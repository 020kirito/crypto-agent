#!/usr/bin/env python3
"""
分析解题结果和收集的数据

使用示例:
    python scripts/analyze_results.py --stats
    python scripts/analyze_results.py --export-train
"""

import argparse
import json
from pathlib import Path
from collections import Counter, defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_trajectories(data_dir: str = "data/trajectories"):
    """加载所有轨迹数据"""
    trajectories = []
    path = Path(data_dir)
    
    if not path.exists():
        return trajectories
    
    for file in path.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                trajectories.append(json.load(f))
        except:
            continue
    
    return trajectories


def show_statistics(trajectories):
    """显示统计数据"""
    if not trajectories:
        print("❌ 没有数据")
        return
    
    total = len(trajectories)
    success = sum(1 for t in trajectories if t.get("success"))
    failed = total - success
    
    print("\n" + "="*60)
    print("📊 解题统计")
    print("="*60)
    print(f"总题目数: {total}")
    print(f"成功: {success} ({success/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    
    # 按挑战名称统计
    by_challenge = defaultdict(lambda: {"total": 0, "success": 0})
    for t in trajectories:
        name = t.get("challenge_name", "unknown")
        by_challenge[name]["total"] += 1
        if t.get("success"):
            by_challenge[name]["success"] += 1
    
    print("\n按题目统计:")
    print("-"*60)
    for name, stats in sorted(by_challenge.items()):
        rate = stats["success"] / stats["total"] * 100
        status = "✅" if stats["success"] == stats["total"] else "❌"
        print(f"{status} {name}: {stats['success']}/{stats['total']} ({rate:.0f}%)")
    
    # 平均耗时
    times = [t.get("elapsed_time", 0) for t in trajectories]
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n平均解题时间: {avg_time:.1f} 秒")


def export_training_data(trajectories, output_file: str):
    """导出训练数据 (OpenAI 格式)"""
    successful = [t for t in trajectories if t.get("success")]
    
    if not successful:
        print("❌ 没有成功的轨迹可用于训练")
        return
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for t in successful:
            # 构建 OpenAI 训练格式
            sample = {
                "messages": [
                    {"role": "system", "content": "你是 CTF 密码学解题专家"},
                    {"role": "user", "content": t.get("output", "")[:500]},
                    {"role": "assistant", "content": f"找到 flag: {t.get('flag', 'unknown')}"}
                ]
            }
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    print(f"✅ 导出 {len(successful)} 条训练数据到 {output_path}")


def show_recent_results(trajectories, n: int = 5):
    """显示最近的解题结果"""
    sorted_trajectories = sorted(
        trajectories,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:n]
    
    print(f"\n🕐 最近 {n} 次解题:")
    print("-"*60)
    
    for t in sorted_trajectories:
        status = "✅" if t.get("success") else "❌"
        name = t.get("challenge_name", "unknown")
        flag = t.get("flag", "N/A")
        time = t.get("elapsed_time", 0)
        
        print(f"{status} {name}")
        if t.get("success"):
            print(f"   flag: {flag}")
        print(f"   耗时: {time:.1f}s")
        print()


def main():
    parser = argparse.ArgumentParser(description="分析解题结果")
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="显示统计信息"
    )
    parser.add_argument(
        "--recent", "-r",
        type=int,
        metavar="N",
        help="显示最近 N 次解题"
    )
    parser.add_argument(
        "--export-train", "-e",
        metavar="FILE",
        help="导出训练数据到文件 (JSONL 格式)"
    )
    parser.add_argument(
        "--data-dir", "-d",
        default="data/trajectories",
        help="数据目录 (默认: data/trajectories)"
    )
    
    args = parser.parse_args()
    
    # 加载数据
    trajectories = load_trajectories(args.data_dir)
    
    if not trajectories:
        print(f"❌ 在 {args.data_dir} 中没有找到数据")
        print("提示: 先运行一些题目来生成数据")
        print("  python scripts/run_agent.py --demo")
        return
    
    # 执行命令
    if args.stats:
        show_statistics(trajectories)
    
    if args.recent:
        show_recent_results(trajectories, args.recent)
    
    if args.export_train:
        export_training_data(trajectories, args.export_train)
    
    # 默认显示统计
    if not any([args.stats, args.recent, args.export_train]):
        show_statistics(trajectories)


if __name__ == "__main__":
    main()
