#!/usr/bin/env python3
"""
Kimi模型微调脚本

使用OpenAI兼容API提交微调任务。

使用示例:
    # 提交微调任务
    python scripts/fine_tune_kimi.py --submit --train data/training/finetune/train.jsonl --val data/training/finetune/val.jsonl
    
    # 查看任务状态
    python scripts/fine_tune_kimi.py --status <job_id>
    
    # 列出所有任务
    python scripts/fine_tune_kimi.py --list
    
    # 测试微调后的模型
    python scripts/fine_tune_kimi.py --test --model ft-xxxxxxxx
"""

import argparse
import json
import time
from pathlib import Path
from typing import Optional
import os


def get_openai_client():
    """获取OpenAI客户端 (兼容Kimi API)"""
    try:
        from openai import OpenAI
        
        # 从环境变量读取配置
        api_key = os.getenv('KIMI_API_KEY')
        base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        
        if not api_key:
            raise ValueError("请设置 KIMI_API_KEY 环境变量")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        return client
    except ImportError:
        print("❌ 需要安装openai: pip install openai")
        return None


def validate_data(file_path: str) -> bool:
    """验证训练数据格式"""
    print(f"🔍 验证数据文件: {file_path}")
    
    path = Path(file_path)
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    valid_count = 0
    invalid_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                
                # 检查必要字段
                if 'messages' not in data:
                    print(f"  ⚠️  第{i}行缺少'messages'字段")
                    invalid_count += 1
                    continue
                
                messages = data['messages']
                if not isinstance(messages, list):
                    print(f"  ⚠️  第{i}行'messages'不是列表")
                    invalid_count += 1
                    continue
                
                # 检查角色
                roles = [m.get('role') for m in messages]
                if 'system' not in roles:
                    print(f"  ⚠️  第{i}行缺少'system'消息")
                if 'user' not in roles:
                    print(f"  ⚠️  第{i}行缺少'user'消息")
                if 'assistant' not in roles:
                    print(f"  ⚠️  第{i}行缺少'assistant'消息")
                
                valid_count += 1
                
            except json.JSONDecodeError as e:
                print(f"  ❌ 第{i}行JSON解析错误: {e}")
                invalid_count += 1
            except Exception as e:
                print(f"  ❌ 第{i}行错误: {e}")
                invalid_count += 1
    
    print(f"✅ 验证完成: {valid_count} 条有效, {invalid_count} 条无效")
    return valid_count > 0


def submit_fine_tune_job(
    train_file: str,
    val_file: Optional[str] = None,
    model: str = "moonshot-v1-8k",
    suffix: str = "ctf-crypto"
) -> Optional[str]:
    """
    提交微调任务
    
    Args:
        train_file: 训练数据文件路径
        val_file: 验证数据文件路径 (可选)
        model: 基础模型
        suffix: 模型名称后缀
    """
    client = get_openai_client()
    if not client:
        return None
    
    print("="*60)
    print("🚀 提交微调任务")
    print("="*60)
    
    # 1. 上传训练文件
    print(f"\n📤 上传训练文件: {train_file}")
    try:
        with open(train_file, 'rb') as f:
            train_response = client.files.create(
                file=f,
                purpose='fine-tune'
            )
        train_file_id = train_response.id
        print(f"✅ 训练文件上传成功: {train_file_id}")
    except Exception as e:
        print(f"❌ 训练文件上传失败: {e}")
        return None
    
    # 2. 上传验证文件
    val_file_id = None
    if val_file:
        print(f"\n📤 上传验证文件: {val_file}")
        try:
            with open(val_file, 'rb') as f:
                val_response = client.files.create(
                    file=f,
                    purpose='fine-tune'
                )
            val_file_id = val_response.id
            print(f"✅ 验证文件上传成功: {val_file_id}")
        except Exception as e:
            print(f"⚠️  验证文件上传失败: {e}")
    
    # 3. 创建微调任务
    print(f"\n🎯 创建微调任务...")
    print(f"  基础模型: {model}")
    print(f"  模型后缀: {suffix}")
    
    try:
        hyperparameters = {
            "n_epochs": 3,  # 训练轮数
            "batch_size": "auto",
            "learning_rate_multiplier": "auto"
        }
        
        job_params = {
            "training_file": train_file_id,
            "model": model,
            "suffix": suffix,
            "hyperparameters": hyperparameters
        }
        
        if val_file_id:
            job_params["validation_file"] = val_file_id
        
        job = client.fine_tuning.jobs.create(**job_params)
        
        print(f"✅ 微调任务创建成功!")
        print(f"  任务ID: {job.id}")
        print(f"  状态: {job.status}")
        
        # 保存任务信息
        job_info = {
            "job_id": job.id,
            "base_model": model,
            "suffix": suffix,
            "train_file": train_file,
            "val_file": val_file,
            "train_file_id": train_file_id,
            "val_file_id": val_file_id,
            "status": job.status,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        jobs_dir = Path("data/fine_tuning_jobs")
        jobs_dir.mkdir(parents=True, exist_ok=True)
        
        job_file = jobs_dir / f"{job.id}.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_info, f, indent=2)
        
        print(f"  任务信息已保存: {job_file}")
        
        return job.id
        
    except Exception as e:
        print(f"❌ 微调任务创建失败: {e}")
        return None


def check_job_status(job_id: str):
    """检查微调任务状态"""
    client = get_openai_client()
    if not client:
        return
    
    print("="*60)
    print(f"🔍 检查任务状态: {job_id}")
    print("="*60)
    
    try:
        job = client.fine_tuning.jobs.retrieve(job_id)
        
        print(f"\n任务信息:")
        print(f"  任务ID: {job.id}")
        print(f"  状态: {job.status}")
        print(f"  基础模型: {job.model}")
        print(f"  创建时间: {job.created_at}")
        
        if job.fine_tuned_model:
            print(f"  微调后模型: {job.fine_tuned_model}")
        
        if job.finished_at:
            print(f"  完成时间: {job.finished_at}")
        
        if job.error:
            print(f"  错误信息: {job.error}")
        
        # 显示训练进度
        if hasattr(job, 'trained_tokens') and job.trained_tokens:
            print(f"  已训练token: {job.trained_tokens}")
        
        # 更新本地记录
        jobs_dir = Path("data/fine_tuning_jobs")
        job_file = jobs_dir / f"{job_id}.json"
        
        if job_file.exists():
            with open(job_file, 'r', encoding='utf-8') as f:
                job_info = json.load(f)
            
            job_info['status'] = job.status
            job_info['fine_tuned_model'] = job.fine_tuned_model
            
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job_info, f, indent=2)
        
        return job
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return None


def list_jobs():
    """列出所有微调任务"""
    client = get_openai_client()
    if not client:
        return
    
    print("="*60)
    print("📋 微调任务列表")
    print("="*60)
    
    try:
        jobs = client.fine_tuning.jobs.list(limit=20)
        
        if not jobs.data:
            print("  暂无微调任务")
            return
        
        print(f"\n共 {len(jobs.data)} 个任务:\n")
        
        for job in jobs.data:
            status_emoji = {
                'succeeded': '✅',
                'failed': '❌',
                'running': '🔄',
                'pending': '⏳',
                'cancelled': '🚫'
            }.get(job.status, '❓')
            
            print(f"{status_emoji} {job.id}")
            print(f"   模型: {job.model}")
            print(f"   状态: {job.status}")
            if job.fine_tuned_model:
                print(f"   微调模型: {job.fine_tuned_model}")
            print()
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")


def test_model(model_id: str, prompt: str = None):
    """测试微调后的模型"""
    client = get_openai_client()
    if not client:
        return
    
    if not prompt:
        prompt = "请解释RSA加密的基本原理"
    
    print("="*60)
    print(f"🧪 测试模型: {model_id}")
    print("="*60)
    
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a CTF crypto expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        print(f"\n输入: {prompt}")
        print(f"\n输出:\n{response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def monitor_job(job_id: str, interval: int = 60):
    """持续监控任务直到完成"""
    print(f"🔍 开始监控任务 {job_id} (每{interval}秒检查一次)")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            job = check_job_status(job_id)
            
            if job and job.status in ['succeeded', 'failed', 'cancelled']:
                print(f"\n✨ 任务已结束，最终状态: {job.status}")
                if job.fine_tuned_model:
                    print(f"🎉 微调后模型ID: {job.fine_tuned_model}")
                break
            
            print(f"\n⏳ {time.strftime('%H:%M:%S')} - 状态: {job.status if job else 'unknown'}")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 停止监控")


def main():
    parser = argparse.ArgumentParser(description="Kimi模型微调工具")
    parser.add_argument("--submit", action="store_true", help="提交微调任务")
    parser.add_argument("--train", default="data/training/finetune/train.jsonl", help="训练数据文件")
    parser.add_argument("--val", default="data/training/finetune/val.jsonl", help="验证数据文件")
    parser.add_argument("--model", default="moonshot-v1-8k", help="基础模型")
    parser.add_argument("--suffix", default="ctf-crypto-v1", help="模型后缀")
    parser.add_argument("--status", help="检查任务状态")
    parser.add_argument("--list", action="store_true", help="列出所有任务")
    parser.add_argument("--monitor", help="持续监控任务")
    parser.add_argument("--test", help="测试微调后的模型")
    parser.add_argument("--prompt", help="测试提示词")
    parser.add_argument("--validate", help="验证数据文件")
    
    args = parser.parse_args()
    
    if args.validate:
        validate_data(args.validate)
    elif args.submit:
        # 先验证数据
        if not validate_data(args.train):
            print("❌ 训练数据验证失败")
            return
        if args.val and not validate_data(args.val):
            print("⚠️  验证数据验证失败，继续提交")
        
        # 提交任务
        job_id = submit_fine_tune_job(
            train_file=args.train,
            val_file=args.val,
            model=args.model,
            suffix=args.suffix
        )
        
        if job_id:
            print(f"\n🎉 微调任务已提交!")
            print(f"使用以下命令监控进度:")
            print(f"  python scripts/fine_tune_kimi.py --monitor {job_id}")
            
    elif args.status:
        check_job_status(args.status)
    elif args.list:
        list_jobs()
    elif args.monitor:
        monitor_job(args.monitor)
    elif args.test:
        test_model(args.test, args.prompt)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
