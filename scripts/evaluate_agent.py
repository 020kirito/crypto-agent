#!/usr/bin/env python3
"""
Agent 评估系统

评估 Agent 在不同模型配置下的解题能力。

使用示例:
    # 评估基础模型
    python scripts/evaluate_agent.py --model gpt-3.5-turbo --output results_baseline.json
    
    # 评估微调模型
    python scripts/evaluate_agent.py --model ft-xxxxxxxx --output results_finetuned.json
    
    # 对比结果
    python scripts/evaluate_agent.py --compare results_baseline.json results_finetuned.json
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent import create_crypto_agent


TEST_CHALLENGES = [
    {
        "name": "caesar_basic",
        "category": "classical",
        "difficulty": "easy",
        "description": """
密文: Khoor Zruog
这是一个凯撒密码，请解密。
提示: 每个字母向后移动固定位数。
"""
    },
    {
        "name": "rsa_basic",
        "category": "rsa",
        "difficulty": "easy",
        "description": """
RSA 解密:
n = 3233
e = 17
c = 2790
请解密密文 c 获取明文。
"""
    },
    {
        "name": "base64_decode",
        "category": "encoding",
        "difficulty": "easy",
        "description": """
密文: SGVsbG8gV29ybGQ=
这是什么编码？请解码。
"""
    },
    {
        "name": "xor_decrypt",
        "category": "crypto",
        "difficulty": "easy",
        "description": """
密文 (hex): 0a0c1e1e08
密钥: key
加密方式: XOR
请解密。
"""
    },
    {
        "name": "rsa_common_modulus",
        "category": "rsa",
        "difficulty": "medium",
        "description": """
共模攻击:
同一个 n，不同的 e1=3, e2=5
密文 c1, c2
请恢复明文。
"""
    },
]


def evaluate_challenge(agent, challenge: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    """
    评估单个题目
    
    Returns:
        评估结果
    """
    print(f"\n  📝 {challenge['name']} ({challenge['difficulty']})")
    
    start_time = time.time()
    
    try:
        result = agent.solve(
            challenge_description=challenge['description'],
            challenge_name=challenge['name']
        )
        
        elapsed = time.time() - start_time
        
        # 判断是否成功
        success = result.get('success', False)
        flag = result.get('flag', None)
        
        return {
            "name": challenge['name'],
            "category": challenge['category'],
            "difficulty": challenge['difficulty'],
            "success": success,
            "flag": flag,
            "elapsed_time": elapsed,
            "output": result.get('output', '')[:500]  # 限制长度
        }
        
    except Exception as e:
        return {
            "name": challenge['name'],
            "category": challenge['category'],
            "difficulty": challenge['difficulty'],
            "success": False,
            "error": str(e),
            "elapsed_time": time.time() - start_time
        }


def run_evaluation(model: str, output_file: str):
    """
    运行完整评估
    """
    print("=" * 60)
    print(f"🧪 Agent 评估: {model}")
    print("=" * 60)
    
    # 创建 Agent
    print(f"\n🔧 创建 Agent (模型: {model})...")
    agent = create_crypto_agent(model_name=model)
    
    results = []
    
    print(f"\n📋 测试题目 ({len(TEST_CHALLENGES)} 个):")
    
    for challenge in TEST_CHALLENGES:
        result = evaluate_challenge(agent, challenge)
        results.append(result)
        
        status = "✅" if result['success'] else "❌"
        print(f"     {status} {result['name']}: {result['elapsed_time']:.1f}s")
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r['success'])
    
    by_category = {}
    for r in results:
        cat = r['category']
        if cat not in by_category:
            by_category[cat] = {"total": 0, "success": 0}
        by_category[cat]["total"] += 1
        if r['success']:
            by_category[cat]["success"] += 1
    
    summary = {
        "model": model,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_challenges": total,
        "success_count": success,
        "success_rate": success / total if total > 0 else 0,
        "avg_time": sum(r['elapsed_time'] for r in results) / total if total > 0 else 0,
        "by_category": {
            cat: {
                "total": stats["total"],
                "success": stats["success"],
                "rate": stats["success"] / stats["total"] if stats["total"] > 0 else 0
            }
            for cat, stats in by_category.items()
        },
        "details": results
    }
    
    # 保存结果
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("📊 评估结果")
    print("=" * 60)
    print(f"总题目数: {total}")
    print(f"成功数: {success} ({summary['success_rate']*100:.1f}%)")
    print(f"平均用时: {summary['avg_time']:.1f}s")
    print("\n分类统计:")
    for cat, stats in summary['by_category'].items():
        print(f"  {cat}: {stats['success']}/{stats['total']} ({stats['rate']*100:.1f}%)")
    print(f"\n💾 结果已保存: {output_file}")
    
    return summary


def compare_results(file1: str, file2: str):
    """
    对比两个评估结果
    """
    print("=" * 60)
    print("📊 结果对比")
    print("=" * 60)
    
    with open(file1) as f:
        result1 = json.load(f)
    with open(file2) as f:
        result2 = json.load(f)
    
    print(f"\n模型 A: {result1['model']}")
    print(f"模型 B: {result2['model']}")
    
    print("\n" + "-" * 60)
    print(f"{'指标':<20} {'模型 A':<15} {'模型 B':<15} {'提升':<10}")
    print("-" * 60)
    
    # 成功率
    r1, r2 = result1['success_rate'], result2['success_rate']
    improvement = (r2 - r1) * 100
    print(f"{'成功率':<20} {r1*100:>6.1f}%{'':<8} {r2*100:>6.1f}%{'':<8} {improvement:+.1f}%")
    
    # 平均用时
    t1, t2 = result1['avg_time'], result2['avg_time']
    time_change = ((t2 - t1) / t1 * 100) if t1 > 0 else 0
    print(f"{'平均用时':<20} {t1:>6.1f}s{'':<7} {t2:>6.1f}s{'':<7} {time_change:+.1f}%")
    
    # 逐个题目对比
    print("\n" + "=" * 60)
    print("📋 逐题对比")
    print("=" * 60)
    
    details1 = {d['name']: d for d in result1['details']}
    details2 = {d['name']: d for d in result2['details']}
    
    for name in details1:
        d1, d2 = details1[name], details2[name]
        s1 = "✅" if d1['success'] else "❌"
        s2 = "✅" if d2['success'] else "❌"
        
        if d1['success'] != d2['success']:
            change = "🆙 提升" if d2['success'] else "⬇️  下降"
        else:
            change = "➡️  持平"
        
        print(f"  {name:<25} {s1} -> {s2}  {change}")


def main():
    parser = argparse.ArgumentParser(description="Agent 评估系统")
    parser.add_argument(
        "--model", "-m",
        default="moonshot-v1-8k",
        help="评估的模型名称 (默认: moonshot-v1-8k)"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/evaluation/results.json",
        help="输出文件路径"
    )
    parser.add_argument(
        "--compare", "-c",
        nargs=2,
        metavar=("FILE1", "FILE2"),
        help="对比两个结果文件"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_results(args.compare[0], args.compare[1])
    else:
        run_evaluation(args.model, args.output)


if __name__ == "__main__":
    main()
