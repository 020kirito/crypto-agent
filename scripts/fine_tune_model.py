#!/usr/bin/env python3
"""
模型微调脚本 - Scaling Law 实践

使用收集的 CTF 数据微调模型，提升解题能力。

使用示例:
    # 准备数据
    python scripts/fine_tune_model.py --prepare
    
    # 上传并微调 (使用 OpenAI)
    python scripts/fine_tune_model.py --upload --provider openai
    
    # 使用微调后的模型
    python scripts/fine_tune_model.py --test --model ft-xxx
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import random


def prepare_data(
    input_file: str = "data/training/combined.jsonl",
    output_dir: str = "data/training/prepared",
    train_ratio: float = 0.8
) -> Dict[str, Any]:
    """
    准备训练数据
    
    将原始数据分割为训练集和验证集，并进行质量筛选。
    
    Args:
        input_file: 原始数据文件
        output_dir: 输出目录
        train_ratio: 训练集比例
    
    Returns:
        数据统计信息
    """
    print("=" * 60)
    print("📊 准备训练数据")
    print("=" * 60)
    
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 读取所有数据
    all_data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    all_data.append(data)
                except:
                    continue
    
    print(f"📖 读取数据: {len(all_data)} 条")
    
    # 质量筛选
    quality_data = []
    for item in all_data:
        messages = item.get('messages', [])
        if len(messages) >= 3:  # 至少包含 system, user, assistant
            # 检查 assistant 回复是否有实质内容
            assistant_msg = messages[-1].get('content', '')
            if len(assistant_msg) > 100:  # 至少 100 字符
                quality_data.append(item)
    
    print(f"✨ 质量筛选后: {len(quality_data)} 条")
    
    # 分类统计
    categories = {}
    for item in quality_data:
        metadata = item.get('metadata', {})
        cat = metadata.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📈 数据分布:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    # 分割训练集和验证集
    random.seed(42)
    random.shuffle(quality_data)
    
    split_idx = int(len(quality_data) * train_ratio)
    train_data = quality_data[:split_idx]
    valid_data = quality_data[split_idx:]
    
    # 保存
    train_file = output_path / "train.jsonl"
    valid_file = output_path / "valid.jsonl"
    
    with open(train_file, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(valid_file, 'w', encoding='utf-8') as f:
        for item in valid_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n💾 数据分割:")
    print(f"  训练集: {len(train_data)} 条 -> {train_file}")
    print(f"  验证集: {len(valid_data)} 条 -> {valid_file}")
    
    # 生成统计信息
    stats = {
        "total_raw": len(all_data),
        "total_quality": len(quality_data),
        "train_count": len(train_data),
        "valid_count": len(valid_data),
        "categories": categories,
        "train_file": str(train_file),
        "valid_file": str(valid_file)
    }
    
    with open(output_path / "stats.json", 'w') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats


def upload_to_openai(train_file: str, valid_file: str = None) -> Dict[str, Any]:
    """
    上传数据到 OpenAI 并创建微调任务
    
    需要设置 OPENAI_API_KEY 环境变量
    """
    try:
        import openai
    except ImportError:
        print("❌ 请先安装 openai: pip install openai")
        return {"success": False}
    
    print("\n" + "=" * 60)
    print("☁️  上传到 OpenAI")
    print("=" * 60)
    
    # 检查 API Key
    if not openai.api_key:
        print("❌ 请设置 OPENAI_API_KEY 环境变量")
        return {"success": False}
    
    # 上传训练文件
    print(f"\n📤 上传训练文件: {train_file}")
    with open(train_file, 'rb') as f:
        train_response = openai.File.create(
            file=f,
            purpose='fine-tune'
        )
    
    train_file_id = train_response.id
    print(f"   文件 ID: {train_file_id}")
    
    # 上传验证文件（可选）
    valid_file_id = None
    if valid_file and Path(valid_file).exists():
        print(f"\n📤 上传验证文件: {valid_file}")
        with open(valid_file, 'rb') as f:
            valid_response = openai.File.create(
                file=f,
                purpose='fine-tune'
            )
        valid_file_id = valid_response.id
        print(f"   文件 ID: {valid_file_id}")
    
    # 创建微调任务
    print("\n🚀 创建微调任务...")
    
    # 使用 gpt-3.5-turbo 进行微调（性价比高）
    fine_tune_params = {
        "training_file": train_file_id,
        "model": "gpt-3.5-turbo-1106",  # 或 "gpt-4"（更贵但效果更好）
        "suffix": "ctf-crypto-v1",
        "hyperparameters": {
            "n_epochs": 3,  # 训练轮数
            "batch_size": "auto",
            "learning_rate_multiplier": "auto"
        }
    }
    
    if valid_file_id:
        fine_tune_params["validation_file"] = valid_file_id
    
    response = openai.FineTuningJob.create(**fine_tune_params)
    
    job_id = response.id
    print(f"✅ 微调任务已创建!")
    print(f"   任务 ID: {job_id}")
    print(f"   状态: {response.status}")
    print(f"   模型: {response.model}")
    
    print("\n⏳ 微调通常需要 10-60 分钟完成")
    print(f"   可使用命令查看状态: openai api fine_tunes.get -i {job_id}")
    
    return {
        "success": True,
        "job_id": job_id,
        "train_file_id": train_file_id,
        "valid_file_id": valid_file_id,
        "status": response.status
    }


def list_fine_tuned_models():
    """列出所有微调模型"""
    try:
        import openai
    except ImportError:
        print("❌ 请先安装 openai: pip install openai")
        return
    
    print("=" * 60)
    print("📋 微调模型列表")
    print("=" * 60)
    
    # 获取微调任务列表
    jobs = openai.FineTuningJob.list()
    
    if not jobs.data:
        print("暂无微调任务")
        return
    
    for job in jobs.data:
        status_icon = "✅" if job.status == "succeeded" else "⏳" if job.status == "running" else "❌"
        print(f"\n{status_icon} {job.id}")
        print(f"   模型: {job.model}")
        print(f"   状态: {job.status}")
        if job.fine_tuned_model:
            print(f"   微调后模型名: {job.fine_tuned_model}")
        print(f"   创建时间: {job.created_at}")


def test_fine_tuned_model(model: str, test_prompt: str = None):
    """测试微调后的模型"""
    try:
        import openai
    except ImportError:
        print("❌ 请先安装 openai: pip install openai")
        return
    
    print("=" * 60)
    print(f"🧪 测试微调模型: {model}")
    print("=" * 60)
    
    if not test_prompt:
        test_prompt = """题目: RSA 解密
已知 n = 3233, e = 17, c = 2790
请解密密文获取明文。"""
    
    print(f"\n输入:\n{test_prompt}\n")
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是 CTF 密码学解题专家"},
                {"role": "user", "content": test_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        output = response.choices[0].message.content
        print(f"输出:\n{output}")
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="模型微调工具")
    parser.add_argument(
        "--prepare", "-p",
        action="store_true",
        help="准备训练数据"
    )
    parser.add_argument(
        "--upload", "-u",
        action="store_true",
        help="上传数据并创建微调任务"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "local"],
        default="openai",
        help="微调服务提供商"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有微调模型"
    )
    parser.add_argument(
        "--test", "-t",
        metavar="MODEL",
        help="测试指定的微调模型 (如 ft-xxxxxxxx)"
    )
    
    args = parser.parse_args()
    
    if args.prepare:
        stats = prepare_data()
        print(f"\n{'='*60}")
        print("✅ 数据准备完成!")
        print(f"{'='*60}")
        print(f"训练集: {stats['train_count']} 条")
        print(f"验证集: {stats['valid_count']} 条")
        print(f"数据保存在: data/training/prepared/")
    
    elif args.upload:
        if args.provider == "openai":
            train_file = "data/training/prepared/train.jsonl"
            valid_file = "data/training/prepared/valid.jsonl"
            
            if not Path(train_file).exists():
                print("❌ 训练数据不存在，请先运行 --prepare")
                return
            
            result = upload_to_openai(train_file, valid_file)
            if result.get("success"):
                print(f"\n✅ 微调任务已启动!")
                print(f"   任务 ID: {result['job_id']}")
        else:
            print("本地微调功能待实现")
    
    elif args.list:
        list_fine_tuned_models()
    
    elif args.test:
        test_fine_tuned_model(args.test)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
