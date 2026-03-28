#!/usr/bin/env python3
"""
OpenAI微调脚本

用于在OpenAI平台上微调GPT模型。

前置条件:
1. 设置 OPENAI_API_KEY 环境变量
2. 安装openai: pip install openai

使用示例:
    export OPENAI_API_KEY="sk-..."
    
    # 提交微调任务
    python scripts/fine_tune_openai.py --submit
    
    # 查看任务状态
    python scripts/fine_tune_openai.py --status <job_id>
    
    # 列出所有任务
    python scripts/fine_tune_openai.py --list
"""

import argparse
import json
import time
import os
from pathlib import Path


def get_client():
    """获取OpenAI客户端"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        return OpenAI(api_key=api_key)
    except ImportError:
        print("❌ 需要安装openai: pip install openai")
        return None


def validate_jsonl(file_path: str) -> tuple:
    """验证JSONL文件格式"""
    print(f"🔍 验证文件: {file_path}")
    
    path = Path(file_path)
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False, 0
    
    valid = 0
    invalid = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                if 'messages' in data and isinstance(data['messages'], list):
                    valid += 1
                else:
                    invalid += 1
            except:
                invalid += 1
    
    print(f"✅ 有效: {valid}, 无效: {invalid}")
    return invalid == 0, valid


def submit_job(train_file: str, val_file: str = None, model: str = "gpt-3.5-turbo", suffix: str = "ctf-crypto"):
    """提交微调任务"""
    client = get_client()
    if not client:
        return None
    
    print("="*60)
    print("🚀 提交OpenAI微调任务")
    print("="*60)
    
    # 验证数据
    ok, count = validate_jsonl(train_file)
    if not ok:
        print("❌ 训练数据验证失败")
        return None
    
    print(f"📊 训练样本数: {count}")
    
    # 上传训练文件
    print(f"\n📤 上传训练文件...")
    try:
        with open(train_file, 'rb') as f:
            train_resp = client.files.create(file=f, purpose='fine-tune')
        print(f"✅ 训练文件ID: {train_resp.id}")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return None
    
    # 上传验证文件
    val_file_id = None
    if val_file and Path(val_file).exists():
        print(f"\n📤 上传验证文件...")
        try:
            with open(val_file, 'rb') as f:
                val_resp = client.files.create(file=f, purpose='fine-tune')
            val_file_id = val_resp.id
            print(f"✅ 验证文件ID: {val_file_id}")
        except Exception as e:
            print(f"⚠️  验证文件上传失败: {e}")
    
    # 创建微调任务
    print(f"\n🎯 创建微调任务...")
    print(f"  基础模型: {model}")
    print(f"  后缀: {suffix}")
    
    try:
        job = client.fine_tuning.jobs.create(
            training_file=train_resp.id,
            validation_file=val_file_id,
            model=model,
            suffix=suffix,
            hyperparameters={
                "n_epochs": 3
            }
        )
        
        print(f"\n✅ 微调任务已创建!")
        print(f"  任务ID: {job.id}")
        print(f"  状态: {job.status}")
        print(f"  预计时间: 10-30分钟")
        
        # 保存任务信息
        job_info = {
            "job_id": job.id,
            "base_model": model,
            "suffix": suffix,
            "train_file_id": train_resp.id,
            "val_file_id": val_file_id,
            "status": job.status,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        jobs_dir = Path("data/fine_tuning_jobs")
        jobs_dir.mkdir(parents=True, exist_ok=True)
        
        with open(jobs_dir / f"openai_{job.id}.json", 'w') as f:
            json.dump(job_info, f, indent=2)
        
        return job.id
        
    except Exception as e:
        print(f"❌ 创建任务失败: {e}")
        return None


def check_status(job_id: str):
    """检查任务状态"""
    client = get_client()
    if not client:
        return
    
    print(f"🔍 检查任务状态: {job_id}")
    
    try:
        job = client.fine_tuning.jobs.retrieve(job_id)
        
        print(f"\n状态: {job.status}")
        print(f"模型: {job.model}")
        
        if job.fine_tuned_model:
            print(f"✅ 微调后模型: {job.fine_tuned_model}")
        
        if job.status == "succeeded":
            print(f"\n🎉 微调完成!")
            print(f"模型名称: {job.fine_tuned_model}")
            print(f"\n使用方式:")
            print(f'  model="{job.fine_tuned_model}"')
        elif job.status == "failed":
            print(f"\n❌ 微调失败")
            if hasattr(job, 'error'):
                print(f"错误: {job.error}")
        
        # 显示训练进度
        if hasattr(job, 'trained_tokens'):
            print(f"已训练token: {job.trained_tokens}")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")


def list_jobs():
    """列出所有微调任务"""
    client = get_client()
    if not client:
        return
    
    print("📋 OpenAI微调任务列表\n")
    
    try:
        jobs = client.fine_tuning.jobs.list(limit=10)
        
        for job in jobs.data:
            status_icon = {
                'succeeded': '✅',
                'failed': '❌',
                'running': '🔄',
                'pending': '⏳'
            }.get(job.status, '❓')
            
            print(f"{status_icon} {job.id}")
            print(f"   模型: {job.model}")
            print(f"   状态: {job.status}")
            if job.fine_tuned_model:
                print(f"   结果: {job.fine_tuned_model}")
            print()
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")


def monitor_job(job_id: str, interval: int = 30):
    """持续监控任务"""
    print(f"🔍 监控任务 {job_id} (每{interval}秒更新)\n")
    print("按 Ctrl+C 停止\n")
    
    try:
        while True:
            client = get_client()
            if not client:
                break
            
            job = client.fine_tuning.jobs.retrieve(job_id)
            
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] 状态: {job.status}", end="")
            
            if job.status == "succeeded":
                print(f"\n\n🎉 微调完成! 模型: {job.fine_tuned_model}")
                break
            elif job.status == "failed":
                print(f"\n\n❌ 微调失败")
                break
            
            print("" if job.status == "running" else f" ({job.status})")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 停止监控")


def test_model(model_id: str):
    """测试微调后的模型"""
    client = get_client()
    if not client:
        return
    
    print(f"🧪 测试模型: {model_id}\n")
    
    test_prompts = [
        "RSA加密中，如果e=3且m^e < n，如何恢复明文？",
        "解释格密码中的LLL算法原理",
        "给定椭圆曲线E: y^2 = x^3 + ax + b mod p，如何计算点加？"
    ]
    
    for prompt in test_prompts:
        print(f"问题: {prompt}")
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a CTF crypto expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            print(f"回答: {resp.choices[0].message.content[:200]}...\n")
        except Exception as e:
            print(f"❌ 错误: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="OpenAI微调工具")
    parser.add_argument("--submit", action="store_true", help="提交微调任务")
    parser.add_argument("--train", default="data/training/finetune/train.jsonl")
    parser.add_argument("--val", default="data/training/finetune/val.jsonl")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="基础模型")
    parser.add_argument("--suffix", default="ctf-crypto-agent")
    parser.add_argument("--status", help="检查任务状态")
    parser.add_argument("--list", action="store_true", help="列出任务")
    parser.add_argument("--monitor", help="持续监控任务")
    parser.add_argument("--test", help="测试模型")
    
    args = parser.parse_args()
    
    if args.submit:
        job_id = submit_job(args.train, args.val, args.model, args.suffix)
        if job_id:
            print(f"\n监控命令: python scripts/fine_tune_openai.py --monitor {job_id}")
    elif args.status:
        check_status(args.status)
    elif args.list:
        list_jobs()
    elif args.monitor:
        monitor_job(args.monitor)
    elif args.test:
        test_model(args.test)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
