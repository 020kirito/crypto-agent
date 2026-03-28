#!/usr/bin/env python3
"""
测试LoRA微调模型

使用方法:
    # 测试LoRA模型
    python scripts/test_lora_model.py \
        --model outputs/ctf-crypto-lora/lora_weights

    # 测试合并后的模型
    python scripts/test_lora_model.py \
        --model outputs/ctf-crypto-lora/merged_model
"""

import torch
import argparse
from pathlib import Path


def load_model(model_path: str):
    """加载模型"""
    print("="*60)
    print("📥 加载模型")
    print("="*60)
    
    try:
        from unsloth import FastLanguageModel
        
        print(f"路径: {model_path}")
        
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_path,
            max_seq_length=2048,
            dtype=torch.float16,
            load_in_4bit=True,
        )
        
        # 启用推理模式
        FastLanguageModel.for_inference(model)
        
        print("✅ 模型加载完成")
        return model, tokenizer
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None, None


def generate_response(model, tokenizer, messages, max_new_tokens=512):
    """生成回复"""
    try:
        from unsloth import FastLanguageModel
        
        # 应用chat template
        if hasattr(tokenizer, 'apply_chat_template'):
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            # 手动格式化
            prompt = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    prompt += f"<|system|>\n{content}\n"
                elif role == "user":
                    prompt += f"<|user|>\n{content}\n"
            prompt += "<|assistant|>\n"
        
        # 编码
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # 生成
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
        
        # 解码
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 提取assistant的回复
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
        return response
        
    except Exception as e:
        return f"错误: {e}"


def run_tests(model, tokenizer):
    """运行测试用例"""
    print("\n" + "="*60)
    print("🧪 测试模型")
    print("="*60)
    
    test_cases = [
        {
            "name": "RSA基础",
            "messages": [
                {"role": "system", "content": "You are a CTF crypto expert."},
                {"role": "user", "content": "RSA加密中，如果e=3且m^3 < n，如何恢复明文？简要说明攻击原理。"}
            ]
        },
        {
            "name": "格密码",
            "messages": [
                {"role": "system", "content": "You are a CTF crypto expert."},
                {"role": "user", "content": "什么是LLL算法？它在密码学中有哪些应用？"}
            ]
        },
        {
            "name": "ECC",
            "messages": [
                {"role": "system", "content": "You are a CTF crypto expert."},
                {"role": "user", "content": "椭圆曲线点加法的几何意义是什么？"}
            ]
        },
        {
            "name": "具体题目",
            "messages": [
                {"role": "system", "content": "You are a CTF crypto expert."},
                {"role": "user", "content": "RSA题目：n=3233, e=17, c=2790。请给出解题步骤和Python代码。"}
            ]
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['name']}")
        print("-" * 40)
        print(f"问题: {test['messages'][1]['content'][:50]}...")
        
        response = generate_response(model, tokenizer, test['messages'])
        
        print(f"回答: {response[:300]}...")
        print()


def interactive_mode(model, tokenizer):
    """交互模式"""
    print("\n" + "="*60)
    print("💬 交互模式 (输入 'quit' 退出)")
    print("="*60)
    
    system_msg = "You are a CTF crypto expert. Provide detailed step-by-step solutions."
    
    while True:
        user_input = input("\n你: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 再见!")
            break
        
        if not user_input:
            continue
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_input}
        ]
        
        print("\n模型思考中...")
        response = generate_response(model, tokenizer, messages)
        
        print(f"\n助手: {response}")


def main():
    parser = argparse.ArgumentParser(description="测试LoRA模型")
    parser.add_argument("--model", default="outputs/ctf-crypto-lora/lora_weights",
                       help="模型路径")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="交互模式")
    
    args = parser.parse_args()
    
    # 加载模型
    model, tokenizer = load_model(args.model)
    
    if model is None:
        print("❌ 模型加载失败")
        return
    
    # 运行测试或交互
    if args.interactive:
        interactive_mode(model, tokenizer)
    else:
        run_tests(model, tokenizer)
        
        # 询问是否进入交互模式
        choice = input("\n是否进入交互模式? (y/N): ").strip().lower()
        if choice == 'y':
            interactive_mode(model, tokenizer)


if __name__ == "__main__":
    main()
