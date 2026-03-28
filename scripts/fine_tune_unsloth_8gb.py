#!/usr/bin/env python3
"""
Unsloth LoRA微调脚本 - 8GB显存优化版

针对RTX 4060/3060 8GB显存优化:
- 使用4-bit量化
- 梯度检查点
- 小batch size + 梯度累积
- 序列长度2048

使用方法:
    python scripts/fine_tune_unsloth_8gb.py

显存需求:
    - 基础模型(Q4): ~5GB
    - LoRA适配器: ~1GB
    - 优化器状态: ~1.5GB
    - 激活值: ~0.5GB
    总计: ~8GB
"""

import torch
import json
from pathlib import Path
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer


def check_gpu():
    """检查GPU环境"""
    print("="*60)
    print("🔍 GPU环境检查")
    print("="*60)
    
    if not torch.cuda.is_available():
        print("❌ 未检测到CUDA GPU")
        return False
    
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    
    print(f"✅ GPU: {gpu_name}")
    print(f"✅ 显存: {gpu_memory:.1f} GB")
    
    if gpu_memory < 6:
        print("⚠️  警告: 显存不足6GB，可能无法运行")
        return False
    
    # 清理显存
    torch.cuda.empty_cache()
    print(f"✅ 可用显存: {torch.cuda.memory_allocated() / 1024**3:.1f} GB 已分配")
    
    return True


def install_unsloth():
    """安装Unsloth (如果未安装)"""
    try:
        import unsloth
        print("✅ Unsloth已安装")
        return True
    except ImportError:
        print("📦 正在安装Unsloth...")
        print("这可能需要几分钟时间...")
        
        import subprocess
        import sys
        
        # 安装unsloth
        packages = [
            "unsloth",
            "trl",
            "peft",
            "accelerate",
            "bitsandbytes",
        ]
        
        for pkg in packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])
        
        print("✅ 安装完成")
        return True


def load_model_for_8gb():
    """加载适合8GB显存的模型"""
    from unsloth import FastLanguageModel
    
    print("\n" + "="*60)
    print("📥 加载模型 (4-bit量化)")
    print("="*60)
    
    # 模型选择 (适合8GB的模型)
    models = {
        "1": ("unsloth/llama-3-8b-Instruct", "Llama-3-8B (推荐)"),
        "2": ("unsloth/mistral-7b-Instruct-v0.3", "Mistral-7B"),
        "3": ("unsloth/Qwen2.5-7B-Instruct", "Qwen2.5-7B (中文友好)"),
        "4": ("unsloth/gemma-2-9b-it", "Gemma-2-9B"),
    }
    
    print("\n可用模型:")
    for k, (_, name) in models.items():
        print(f"  {k}. {name}")
    
    choice = input("\n选择模型 (默认1): ").strip() or "1"
    model_name, model_desc = models.get(choice, models["1"])
    
    print(f"\n加载: {model_desc}")
    print("  使用4-bit量化减少显存占用...")
    
    max_seq_length = 2048
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=torch.float16,  # 使用FP16
        load_in_4bit=True,    # 4-bit量化
        token=None,  # 如果需要HuggingFace token
    )
    
    print(f"✅ 模型加载完成")
    print(f"   序列长度: {max_seq_length}")
    print(f"   量化: 4-bit")
    
    return model, tokenizer, max_seq_length


def setup_lora(model):
    """配置LoRA适配器"""
    print("\n" + "="*60)
    print("🔧 配置LoRA适配器")
    print("="*60)
    
    model = FastLanguageModel.get_peft_model(
        model,
        r=32,  # LoRA rank，8GB用32平衡效果和显存
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=64,  # alpha = 2 * r
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",  # 节省显存
        random_state=3407,
        use_rslora=False,  # 使用标准LoRA
    )
    
    print("✅ LoRA配置完成")
    print("   Rank: 32")
    print("   Alpha: 64")
    print("   目标模块: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj")
    
    # 打印可训练参数
    model.print_trainable_parameters()
    
    return model


def load_and_format_data(tokenizer, max_seq_length: int):
    """加载并格式化训练数据"""
    print("\n" + "="*60)
    print("📊 加载训练数据")
    print("="*60)
    
    train_file = "data/training/finetune/train.jsonl"
    val_file = "data/training/finetune/val.jsonl"
    
    # 检查文件
    if not Path(train_file).exists():
        print(f"❌ 训练文件不存在: {train_file}")
        return None, None
    
    # 加载数据集
    dataset = load_dataset("json", data_files={"train": train_file, "validation": val_file})
    
    print(f"✅ 加载完成")
    print(f"   训练样本: {len(dataset['train'])}")
    print(f"   验证样本: {len(dataset['validation'])}")
    
    # 格式化函数 - 使用对话模板
    def format_prompt(examples):
        messages = examples["messages"]
        
        # 使用模型的chat template
        if hasattr(tokenizer, 'apply_chat_template'):
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        else:
            # 手动格式化
            text = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    text += f"<|system|>\n{content}\n"
                elif role == "user":
                    text += f"<|user|>\n{content}\n"
                elif role == "assistant":
                    text += f"<|assistant|>\n{content}\n"
            text += "<|endoftext|>"
        
        return {"text": text}
    
    # 应用格式化
    dataset = dataset.map(format_prompt, batched=False)
    
    # 显示示例
    print("\n数据示例:")
    print("-" * 40)
    print(dataset['train'][0]['text'][:500] + "...")
    print("-" * 40)
    
    return dataset['train'], dataset['validation']


def train_model(model, tokenizer, train_dataset, val_dataset, max_seq_length: int):
    """训练模型"""
    print("\n" + "="*60)
    print("🚀 开始训练")
    print("="*60)
    
    # 训练参数 (8GB显存优化)
    training_args = TrainingArguments(
        output_dir="outputs/ctf-crypto-lora",
        
        # 训练设置
        num_train_epochs=3,
        per_device_train_batch_size=1,      # 8GB必须用1
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,       # 模拟batch_size=8
        
        # 优化器
        optim="adamw_8bit",                  # 8-bit优化器节省显存
        learning_rate=2e-4,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        warmup_steps=50,
        
        # 日志和评估
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,
        
        # 精度
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        
        # 其他
        seed=3407,
        report_to="none",  # 不使用wandb
        remove_unused_columns=False,
    )
    
    print("训练配置:")
    print(f"   Epochs: 3")
    print(f"   Batch size: 1 (有效batch size: 8)")
    print(f"   Learning rate: 2e-4")
    print(f"   Sequence length: {max_seq_length}")
    print(f"   预计时间: 1-3小时 (取决于数据量)")
    
    # 创建trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        args=training_args,
    )
    
    # 开始训练
    print("\n⏳ 训练中... (按Ctrl+C可暂停)")
    
    try:
        trainer_stats = trainer.train()
        
        print("\n✅ 训练完成!")
        print(f"   训练时间: {trainer_stats.metrics.get('train_runtime', 0)/60:.1f} 分钟")
        print(f"   最终loss: {trainer_stats.training_loss:.4f}")
        
        return trainer
        
    except KeyboardInterrupt:
        print("\n\n⚠️  训练被中断")
        return trainer


def save_model(model, tokenizer, trainer):
    """保存模型"""
    print("\n" + "="*60)
    print("💾 保存模型")
    print("="*60)
    
    output_dir = Path("outputs/ctf-crypto-lora")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存LoRA权重
    lora_dir = output_dir / "lora_weights"
    trainer.save_model(str(lora_dir))
    print(f"✅ LoRA权重已保存: {lora_dir}")
    
    # 保存tokenizer
    tokenizer.save_pretrained(str(lora_dir))
    
    # 合并权重 (可选，需要更多显存)
    print("\n是否合并LoRA权重到基础模型?")
    print("  注意: 合并需要约10GB显存，可能会OOM")
    choice = input("合并权重? (y/N): ").strip().lower()
    
    if choice == 'y':
        try:
            print("🔄 合并权重...")
            model = model.merge_and_unload()
            
            merged_dir = output_dir / "merged_model"
            model.save_pretrained(str(merged_dir), safe_serialization=True)
            tokenizer.save_pretrained(str(merged_dir))
            
            print(f"✅ 合并模型已保存: {merged_dir}")
        except Exception as e:
            print(f"⚠️  合并失败: {e}")
            print("   你可以稍后使用merge_lora.py脚本合并")
    
    # 保存使用说明
    readme = output_dir / "README.md"
    readme.write_text(f"""# CTF Crypto Agent LoRA Model

## 模型信息
- 基础模型: {model_name}
- 训练数据: {len(train_dataset)} 条
- LoRA Rank: 32
- 训练轮数: 3

## 使用方法

### 1. 加载LoRA模型
```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="outputs/ctf-crypto-lora/lora_weights",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)
```

### 2. 使用Ollama部署 (推荐)
```bash
# 转换格式并部署
python scripts/export_to_ollama.py
ollama create ctf-crypto-agent -f Modelfile.ollama
```

### 3. 使用vLLM部署
```bash
python -m vllm.entrypoints.openai.api_server \\
    --model outputs/ctf-crypto-lora/merged_model \\
    --tensor-parallel-size 1
```

## 测试示例
```python
messages = [
    {{"role": "system", "content": "You are a CTF crypto expert."}},
    {{"role": "user", "content": "RSA中n=3233,e=17,c=2790,求明文m"}}
]
```
""")
    
    print(f"✅ 使用说明: {readme}")
    
    return output_dir


def main():
    """主函数"""
    print("="*60)
    print("🎓 CTF Crypto Agent - LoRA微调 (8GB版)")
    print("="*60)
    
    # 1. 检查GPU
    if not check_gpu():
        print("❌ GPU检查失败，退出")
        return
    
    # 2. 安装依赖
    if not install_unsloth():
        print("❌ 依赖安装失败，退出")
        return
    
    # 导入unsloth (安装后)
    from unsloth import FastLanguageModel
    global FastLanguageModel
    
    # 3. 加载模型
    model, tokenizer, max_seq_length = load_model_for_8gb()
    
    # 4. 设置LoRA
    model = setup_lora(model)
    
    # 5. 加载数据
    result = load_and_format_data(tokenizer, max_seq_length)
    if result is None:
        print("❌ 数据加载失败")
        return
    train_dataset, val_dataset = result
    
    # 6. 训练
    trainer = train_model(model, tokenizer, train_dataset, val_dataset, max_seq_length)
    
    # 7. 保存
    output_dir = save_model(model, tokenizer, trainer)
    
    print("\n" + "="*60)
    print("🎉 全部完成!")
    print("="*60)
    print(f"\n模型保存在: {output_dir}")
    print("\n下一步:")
    print("  1. 测试模型: python scripts/test_lora_model.py")
    print("  2. 导出到Ollama: python scripts/export_to_ollama.py")
    print("  3. 运行Agent: python scripts/test_agent.py --model outputs/ctf-crypto-lora/lora_weights")


if __name__ == "__main__":
    main()
