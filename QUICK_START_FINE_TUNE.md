# 🚀 8GB显存LoRA微调快速启动指南

针对RTX 4060/3060 8GB显存优化

---

## 📋 前置要求

```bash
# 1. 检查GPU
nvidia-smi

# 2. 确保CUDA可用
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# 3. 确保训练数据已准备
cat data/training/finetune/stats.json
```

---

## ⚡ 快速开始 (3步)

### 步骤1: 运行微调脚本

```bash
cd /mnt/d/llama-fac/toy_ctf
python scripts/fine_tune_unsloth_8gb.py
```

**交互流程**:
1. 选择模型 (推荐 Llama-3-8B)
2. 等待下载和加载 (约5-10分钟)
3. 自动开始训练 (约1-3小时)

### 步骤2: 合并权重 (可选)

```bash
python scripts/merge_lora.py \
    --lora outputs/ctf-crypto-lora/lora_weights \
    --output outputs/ctf-crypto-lora/merged_model
```

### 步骤3: 测试模型

```bash
# 自动测试
python scripts/test_lora_model.py \
    --model outputs/ctf-crypto-lora/lora_weights

# 交互模式
python scripts/test_lora_model.py \
    --model outputs/ctf-crypto-lora/lora_weights \
    --interactive
```

---

## 🔧 手动分步执行

如果自动脚本失败，可以手动执行：

### 1. 安装依赖

```bash
pip install unsloth trl peft accelerate bitsandbytes
```

### 2. 训练脚本

```python
# train.py
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 加载模型 (4-bit)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-Instruct",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

# 添加LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                   "gate_proj", "up_proj", "down_proj"],
    lora_alpha=64,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# 加载数据
dataset = load_dataset("json", data_files={
    "train": "data/training/finetune/train.jsonl",
    "validation": "data/training/finetune/val.jsonl"
})

# 格式化
def format_prompt(examples):
    messages = examples["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False)
    return {"text": text}

dataset = dataset.map(format_prompt)

# 训练参数 (8GB优化)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        output_dir="outputs/ctf-crypto-lora",
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        optim="adamw_8bit",
        learning_rate=2e-4,
        warmup_steps=50,
        logging_steps=10,
        save_steps=200,
        fp16=True,
    ),
)

# 开始训练
trainer.train()

# 保存
trainer.save_model("outputs/ctf-crypto-lora/lora_weights")
```

运行:
```bash
python train.py
```

---

## 📊 显存使用参考

| 阶段 | 显存占用 | 说明 |
|------|----------|------|
| 模型加载 (Q4) | ~5GB | 4-bit量化 |
| LoRA适配器 | ~1GB | Rank=32 |
| 优化器 (8-bit) | ~1.5GB | AdamW 8-bit |
| 激活值 | ~0.5GB | Gradient checkpointing |
| **总计** | **~8GB** | 刚好适合8GB显卡 |

---

## 🎯 训练参数调优

如果OOM (显存不足)，尝试：

```python
# 减少Rank
r=16  # 默认32

# 减少序列长度
max_seq_length=1024  # 默认2048

# 增加梯度累积 (减少batch效果)
gradient_accumulation_steps=16  # 默认8

# 使用更激进的量化
load_in_4bit=True  # 已经是4-bit，无法再降
```

---

## 📁 输出文件

训练完成后会在 `outputs/ctf-crypto-lora/` 下生成:

```
outputs/ctf-crypto-lora/
├── lora_weights/          # LoRA权重 (可加载)
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   └── tokenizer files
├── checkpoint-XXX/        # 训练检查点
├── merged_model/          # 合并后的模型 (如果执行了merge)
└── README.md              # 使用说明
```

---

## 🚀 部署选项

### 选项1: 使用Unsloth直接加载 (开发)

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="outputs/ctf-crypto-lora/lora_weights",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)
```

### 选项2: 转换为GGUF + Ollama (推荐部署)

```bash
# 1. 安装llama.cpp
pip install llama-cpp-python

# 2. 转换为GGUF
python -m llama_cpp.convert_hf_to_gguf \
    --outfile ctf-crypto-agent.gguf \
    --outtype q4_k_m \
    outputs/ctf-crypto-lora/merged_model

# 3. 创建Ollama模型
ollama create ctf-crypto-agent -f Modelfile.gguf

# 4. 运行
ollama run ctf-crypto-agent
```

### 选项3: 使用vLLM (生产环境)

```bash
python -m vllm.entrypoints.openai.api_server \
    --model outputs/ctf-crypto-lora/merged_model \
    --tensor-parallel-size 1 \
    --max-model-len 4096
```

---

## 🔍 常见问题

### Q: 训练中断后如何恢复?
```bash
# 从最新checkpoint恢复
trainer.train(resume_from_checkpoint="outputs/ctf-crypto-lora/checkpoint-200")
```

### Q: 如何评估模型效果?
```bash
python scripts/test_lora_model.py --model outputs/ctf-crypto-lora/lora_weights
```

### Q: 显存还是不够?
- 关闭其他程序 (浏览器、游戏等)
- 使用更小的模型 (gemma-2b, qwen2.5-3b)
- 使用Google Colab的免费T4 GPU

### Q: 训练时间太长?
- 减少epochs (num_train_epochs=2)
- 使用更少的数据
- 使用更快的GPU (RTX 4090, A100)

---

## 📞 获取帮助

```bash
# 查看训练日志
tail -f outputs/ctf-crypto-lora/training.log

# 检查显存使用
watch -n 1 nvidia-smi

# 测试模型加载
python scripts/test_lora_model.py --model outputs/ctf-crypto-lora/lora_weights
```

---

## ✨ 开始训练!

```bash
python scripts/fine_tune_unsloth_8gb.py
```

训练完成后记得测试效果! 🎉
