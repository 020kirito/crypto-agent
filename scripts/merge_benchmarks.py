#!/usr/bin/env python3
"""
合并多个基准测试结果

使用示例:
    python scripts/merge_benchmarks.py \
        data/evaluation/batch_easy.json \
        data/evaluation/batch_medium.json \
        --output full_report.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def merge_benchmarks(files, output_file):
    """合并多个基准测试文件"""
    
    all_results = []
    all_details = []
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.append(data)
                all_details.extend(data.get('details', []))
                print(f"✅ 加载: {file_path} ({len(data.get('details', []))} 题)")
        except Exception as e:
            print(f"❌ 加载失败 {file_path}: {e}")
    
    if not all_results:
        print("没有有效的数据文件")
        return
    
    # 合并统计
    total = len(all_details)
    success = sum(1 for d in all_details if d.get('success'))
    
    # 按类别统计
    by_category = {}
    for d in all_details:
        cat = d.get('category', 'unknown')
        if cat not in by_category:
            by_category[cat] = {'total': 0, 'success': 0, 'time': 0}
        by_category[cat]['total'] += 1
        if d.get('success'):
            by_category[cat]['success'] += 1
        by_category[cat]['time'] += d.get('elapsed_time', 0)
    
    # 按难度统计
    by_difficulty = {}
    for d in all_details:
        diff = d.get('difficulty', 'unknown')
        if diff not in by_difficulty:
            by_difficulty[diff] = {'total': 0, 'success': 0, 'time': 0}
        by_difficulty[diff]['total'] += 1
        if d.get('success'):
            by_difficulty[diff]['success'] += 1
        by_difficulty[diff]['time'] += d.get('elapsed_time', 0)
    
    # 构建合并报告
    merged = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model': all_results[0].get('model', 'unknown'),
        'summary': {
            'total': total,
            'success': success,
            'failed': total - success,
            'success_rate': success / total if total > 0 else 0,
            'total_time': sum(d.get('elapsed_time', 0) for d in all_details),
            'avg_time': sum(d.get('elapsed_time', 0) for d in all_details) / total if total > 0 else 0
        },
        'by_category': by_category,
        'by_difficulty': by_difficulty,
        'details': all_details,
        'source_files': [str(f) for f in files]
    }
    
    # 保存
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 合并报告已保存: {output_file}")
    
    # 打印摘要
    print_summary(merged)
    
    return merged


def print_summary(report):
    """打印摘要"""
    print("\n" + "="*60)
    print("📊 合并基准测试报告")
    print("="*60)
    
    s = report['summary']
    print(f"\n总体统计:")
    print(f"  总题目数: {s['total']}")
    print(f"  成功: {s['success']}")
    print(f"  失败: {s['failed']}")
    print(f"  成功率: {s['success_rate']*100:.1f}%")
    print(f"  总用时: {s['total_time']:.1f}s")
    print(f"  平均用时: {s['avg_time']:.1f}s")
    
    print(f"\n按类别:")
    for cat, stats in sorted(report['by_category'].items()):
        rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
        print(f"  {cat:<15} {stats['success']:>2}/{stats['total']:<2} ({rate*100:>5.1f}%)  {stats['time']:>7.1f}s")
    
    print(f"\n按难度:")
    diff_order = ['easy', 'medium', 'hard', 'expert']
    for diff in diff_order:
        if diff in report.get('by_difficulty', {}):
            stats = report['by_difficulty'][diff]
            rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
            print(f"  {diff:<10} {stats['success']:>2}/{stats['total']:<2} ({rate*100:>5.1f}%)  {stats['time']:>7.1f}s")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='合并基准测试结果')
    parser.add_argument('files', nargs='+', help='要合并的JSON文件')
    parser.add_argument('--output', '-o', default='data/evaluation/merged_benchmark.json', 
                       help='输出文件')
    
    args = parser.parse_args()
    
    merge_benchmarks(args.files, args.output)


if __name__ == '__main__':
    main()
