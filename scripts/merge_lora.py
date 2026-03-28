#!/usr/bin/env python3
"""
合并LoRA权重到基础模型

使用方法:
    python scripts/merge_lora.py \
        --lora outputs/ctf-crypto-lora/lora_weights \
        --output outputs/ctf-crypto-lora/merged_model
"""

import torch
import argparse
from pathlib import Path
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer


def merge_lora_weights(lora_path: str, output_path: str):
    """合并LoRA权重"""
    print("="*60)
    print("🔄 合并LoRA权重")
    print("="*60)
    
    print(f"\nLoRA路径: {lora_path}")
    print(f"输出路径: {output_path}")
    
    # 检查显存
    if torch.cuda.is_available():
        free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()
        free_gb = free_memory / 1024**3
        print(f"\n可用显存: {free_gb:.1f} GB")
        
        if free_gb < 10:
            print("⚠️  警告: 可用显存不足10GB，合并可能失败")
            print("   建议关闭其他程序或重启后重试")
            choice = input("是否继续? (y/N): ").strip().lower()
            if choice != 'y':
                return
    
    print("\n📥 加载LoRA模型...")
    try:
        model = AutoPeftModelForCausalLM.from_pretrained(
            lora_path,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        print("✅ 模型加载完成")
        
        print("\n🔧 合并权重...")
        model = model.merge_and_unload()
        print("✅ 合并完成")
        
        print("\n💾 保存合并后的模型...")
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model.save_pretrained(
            output_dir,
            safe_serialization=True,
            max_shard_size="2GB"
        )
        
        # 复制tokenizer
        tokenizer = AutoTokenizer.from_pretrained(lora_path)
        tokenizer.save_pretrained(output_dir)
        
        print(f"✅ 模型已保存到: {output_dir}")
        
        # 计算模型大小
        total_size = sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file())
        print(f"   总大小: {total_size / 1024**3:.2f} GB")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="合并LoRA权重")
    parser.add_argument("--lora", default="outputs/ctf-crypto-lora/lora_weights",
                       help="LoRA权重路径")
    parser.add_argument("--output", default="outputs/ctf-crypto-lora/merged_model",
                       help="输出路径")
    
    args = parser.parse_args()
    
    merge_lora_weights(args.lora, args.output)


if __name__ == "__main__":
    main()
