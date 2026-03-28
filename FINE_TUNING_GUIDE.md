# 模型微调指南

## 当前状态

**Kimi API限制**: Kimi的OpenAI兼容API目前不支持`fine-tune`文件用途。这意味着无法直接通过API提交微调任务。

**替代方案**:
1. 使用OpenAI GPT进行微调
2. 使用本地开源模型(如Llama、Mistral)进行微调
3. 使用vLLM + LoRA进行本地微调
4. 使用Axolotl训练框架

---

## 方案1: OpenAI GPT微调 (推荐)

如果你有OpenAI API Key，可以将数据用于GPT-3.5或GPT-4微调。

```bash
# 设置OpenAI API Key
export OPENAI_API_KEY="sk-..."

# 使用OpenAI CLI
pip install openai

# 上传数据
openai api fine_tunes.create -t data/training/finetune/train.jsonl -v data/training/finetune/val.jsonl -m gpt-3.5-turbo
```

---

## 方案2: 本地开源模型微调 (Llama/Mistral)

### 使用Axolotl训练框架

```bash
# 安装Axolotl
pip install axolotl[flash-attn,deepspeed]

# 创建配置文件 axolotl_config.yaml
```

**axolotl_config.yaml**:
```yaml
base_model: unsloth/llama-3-8b-Instruct
model_type: LlamaForCausalLM

load_in_4bit: true
adapter: lora
lora_r: 64
lora_alpha: 32
lora_dropout: 0.05
lora_target_linear: true
lora_fan_in_fan_out: false

sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true

wandb_project: ctf-crypto-agent
wandb_entity: your-username

datasets:
  - path: data/training/finetune/train.jsonl
    type: chat_template
    field_messages: messages
    message_field_role: role
    message_field_content: content

val_set_size: 0.1
output_dir: ./outputs/ctf-crypto-agent

num_epochs: 3
micro_batch_size: 1
gradient_accumulation_steps: 4
optimizer: paged_adamw_8bit
lr_scheduler: cosine
learning_rate: 2e-4

bf16: auto
fsdp:
  - full_shard
  - auto_wrap
fsdp_config:
  fsdp_limit_all_gathers: true
  fsdp_offload_params: false
```

**开始训练**:
```bash
axolotl train axolotl_config.yaml
```

---

## 方案3: 使用Unsloth快速微调

```python
# install_unsloth.py
from unsloth import FastLanguageModel
import torch

# 加载模型
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-Instruct",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

# 添加LoRA适配器
model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                   "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
    random_state=3407,
)

# 加载数据
from datasets import load_dataset
dataset = load_dataset("json", data_files="data/training/finetune/train.jsonl", split="train")

# 格式化数据
def format_prompt(examples):
    messages = examples["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False)
    return {"text": text}

dataset = dataset.map(format_prompt)

# 训练
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

trainer.train()

# 保存模型
model.save_pretrained("ctf-crypto-agent-lora")
tokenizer.save_pretrained("ctf-crypto-agent-lora")
```

---

## 方案4: 使用Ollama本地部署

对于快速原型验证，可以使用Ollama:

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 创建Modelfile
```

**Modelfile**:
```dockerfile
FROM llama3.1:8b

SYSTEM """You are a CTF crypto expert. You have deep knowledge of cryptography, including RSA, ECC, lattice-based cryptography, and various attack methods. Provide detailed step-by-step solutions to CTF crypto challenges."""

PARAMETER temperature 0.7
PARAMETER num_ctx 8192
```

**创建模型**:
```bash
ollama create ctf-crypto-agent -f Modelfile
ollama run ctf-crypto-agent
```

---

## 训练数据格式

当前训练数据已准备完毕:

```
data/training/finetune/
├── train.jsonl      # 667 条训练数据
├── val.jsonl        # 167 条验证数据
└── stats.json       # 数据统计
```

**数据来源**:
- 本地Markdown: 498条
- 糖醋小鸡块博客writeups: 121条
- 博客工具使用: 216条
- **总计**: 834条 (去重后833条)

---

## 推荐的微调流程

### 1. 快速验证 (使用OpenAI)

如果你有OpenAI API Key，先用小数据量测试:

```python
import openai

# 上传训练文件
with open("data/training/finetune/train.jsonl", "rb") as f:
    file = openai.files.create(file=f, purpose='fine-tune')

# 创建微调任务
job = openai.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-3.5-turbo",
    suffix="ctf-crypto-agent"
)

print(f"Job ID: {job.id}")
```

### 2. 生产环境 (使用开源模型)

使用Llama-3-8B或Mistral-7B进行完整微调。

### 3. 模型合并与部署

```python
from peft import AutoPeftModelForCausalLM

# 加载微调后的模型
model = AutoPeftModelForCausalLM.from_pretrained(
    "ctf-crypto-agent-lora",
    torch_dtype=torch.float16,
)

# 合并权重
merged_model = model.merge_and_unload()
merged_model.save_pretrained("ctf-crypto-agent-merged", safe_serialization=True)
```

---

## 评估微调效果

使用以下指标评估:

1. **解题成功率**: 在测试集上的成功率
2. **工具选择准确率**: 选择正确工具的准确率
3. **代码生成质量**: 生成代码的可执行性
4. **推理步数**: 到达正确答案所需的步骤数

```bash
# 测试微调后的模型
python scripts/evaluate_agent.py --model ft-xxxxxxxx --output results_finetuned.json

# 对比基线
python scripts/evaluate_agent.py --compare results_baseline.json results_finetuned.json
```

---

## 持续学习 (Continuous Learning)

建立一个反馈循环:

```
Agent解题 → 人工审核 → 保存正确轨迹 → 增量训练 → 更新模型
```

```bash
# 每周收集新数据
python scripts/collect_training_data.py --trajectories

# 增量微调
python scripts/fine_tune_incremental.py --base-model ctf-crypto-agent --new-data data/new_trajectories.jsonl
```

---

## 资源需求

| 方案 | GPU显存 | 时间 | 成本 |
|------|---------|------|------|
| OpenAI GPT-3.5 | 无需 | ~30分钟 | ~$5-10 |
| Llama-3-8B LoRA | 16GB | ~2小时 | $0 (自有GPU) |
| Llama-3-8B Full | 80GB | ~8小时 | ~$50 (云GPU) |
| Mistral-7B LoRA | 24GB | ~3小时 | $0 (自有GPU) |

---

## 下一步行动

请选择你想使用的方案:

1. **OpenAI微调** (最快，需要API Key)
2. **本地LoRA微调** (最经济，需要GPU)
3. **使用vLLM部署** (生产环境)

我可以帮你配置任何这些方案！
