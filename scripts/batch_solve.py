#!/usr/bin/env python3
"""
批量解题脚本

支持批量解决CTF挑战题目，并生成排行榜和详细报告。

使用示例:
    # 解决所有题目
    python scripts/batch_solve.py --all
    
    # 解决特定类别的题目
    python scripts/batch_solve.py --category rsa
    
    # 解决特定难度的题目
    python scripts/batch_solve.py --difficulty easy
    
    # 竞赛模式（限时）
    python scripts/batch_solve.py --all --time-limit 3600
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent import create_crypto_agent
from challenges import ChallengeLoader


class BatchSolver:
    """批量解题器"""
    
    def __init__(self, model_name: str = "moonshot-v1-32k", max_workers: int = 1):
        self.model_name = model_name
        self.max_workers = max_workers
        self.agent = None
        self.results: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def _get_agent(self):
        """获取或创建Agent（线程安全）"""
        if self.agent is None:
            self.agent = create_crypto_agent(model_name=self.model_name)
        return self.agent
    
    def solve_challenge(self, challenge: Dict[str, Any], 
                       timeout: int = 120) -> Dict[str, Any]:
        """解决单个挑战"""
        name = challenge['name']
        category = challenge.get('category', 'unknown')
        difficulty = challenge.get('difficulty', 'unknown')
        description = challenge['description']
        expected_flag = challenge.get('flag')
        
        print(f"\n📝 {name} [{category}/{difficulty}]")
        
        start_time = time.time()
        
        try:
            agent = self._get_agent()
            result = agent.solve(
                challenge_description=description,
                challenge_name=name
            )
            
            elapsed = time.time() - start_time
            
            # 检查是否成功
            success = result.get('success', False)
            found_flag = result.get('flag', '')
            
            # 验证flag是否正确（如果知道预期flag）
            flag_correct = None
            if expected_flag and success:
                flag_correct = (found_flag == expected_flag)
            
            return {
                'name': name,
                'category': category,
                'difficulty': difficulty,
                'success': success,
                'flag_found': found_flag,
                'flag_expected': expected_flag,
                'flag_correct': flag_correct,
                'elapsed_time': elapsed,
                'steps': result.get('steps', 0),
                'tools_used': result.get('tools_used', [])
            }
            
        except Exception as e:
            return {
                'name': name,
                'category': category,
                'difficulty': difficulty,
                'success': False,
                'error': str(e),
                'elapsed_time': time.time() - start_time
            }
    
    def solve_all(self, challenges: List[Dict[str, Any]], 
                  timeout: int = 120) -> List[Dict[str, Any]]:
        """批量解决所有挑战"""
        self.results = []
        
        print(f"\n{'='*60}")
        print(f"🚀 批量解题开始")
        print(f"   模型: {self.model_name}")
        print(f"   题目数: {len(challenges)}")
        print(f"{'='*60}")
        
        if self.max_workers == 1:
            # 串行执行
            for challenge in challenges:
                result = self.solve_challenge(challenge, timeout)
                self.results.append(result)
        else:
            # 并行执行（注意：API可能有速率限制）
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_challenge = {
                    executor.submit(self.solve_challenge, c, timeout): c 
                    for c in challenges
                }
                
                for future in as_completed(future_to_challenge):
                    result = future.result()
                    self.results.append(result)
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成详细报告"""
        if not self.results:
            return {}
        
        total = len(self.results)
        success = sum(1 for r in self.results if r.get('success'))
        
        # 按类别统计
        by_category = {}
        for r in self.results:
            cat = r.get('category', 'unknown')
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'success': 0, 'time': 0}
            by_category[cat]['total'] += 1
            if r.get('success'):
                by_category[cat]['success'] += 1
            by_category[cat]['time'] += r.get('elapsed_time', 0)
        
        # 按难度统计
        by_difficulty = {}
        for r in self.results:
            diff = r.get('difficulty', 'unknown')
            if diff not in by_difficulty:
                by_difficulty[diff] = {'total': 0, 'success': 0, 'time': 0}
            by_difficulty[diff]['total'] += 1
            if r.get('success'):
                by_difficulty[diff]['success'] += 1
            by_difficulty[diff]['time'] += r.get('elapsed_time', 0)
        
        return {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'model': self.model_name,
            'summary': {
                'total': total,
                'success': success,
                'failed': total - success,
                'success_rate': success / total if total > 0 else 0,
                'total_time': sum(r.get('elapsed_time', 0) for r in self.results),
                'avg_time': sum(r.get('elapsed_time', 0) for r in self.results) / total if total > 0 else 0
            },
            'by_category': by_category,
            'by_difficulty': by_difficulty,
            'details': self.results
        }
    
    def print_report(self, report: Dict[str, Any]):
        """打印报告"""
        print("\n" + "="*60)
        print("📊 批量解题报告")
        print("="*60)
        
        summary = report.get('summary', {})
        print(f"\n总体统计:")
        print(f"  总题目数: {summary.get('total', 0)}")
        print(f"  成功: {summary.get('success', 0)}")
        print(f"  失败: {summary.get('failed', 0)}")
        print(f"  成功率: {summary.get('success_rate', 0)*100:.1f}%")
        print(f"  总用时: {summary.get('total_time', 0):.1f}s")
        print(f"  平均用时: {summary.get('avg_time', 0):.1f}s")
        
        print(f"\n按类别:")
        for cat, stats in sorted(report.get('by_category', {}).items()):
            rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
            print(f"  {cat:<15} {stats['success']:>2}/{stats['total']:<2} ({rate*100:>5.1f}%)  {stats['time']:>6.1f}s")
        
        print(f"\n按难度:")
        diff_order = ['easy', 'medium', 'hard', 'expert']
        for diff in diff_order:
            if diff in report.get('by_difficulty', {}):
                stats = report['by_difficulty'][diff]
                rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
                print(f"  {diff:<10} {stats['success']:>2}/{stats['total']:<2} ({rate*100:>5.1f}%)  {stats['time']:>6.1f}s")
        
        print(f"\n详细结果:")
        for r in self.results:
            status = "✅" if r.get('success') else "❌"
            flag_info = ""
            if r.get('flag_correct') is not None:
                flag_info = " (flag正确)" if r['flag_correct'] else " (flag错误)"
            print(f"  {status} {r['name']:<30} {r['elapsed_time']:>6.1f}s{flag_info}")


def main():
    parser = argparse.ArgumentParser(description="批量解题")
    parser.add_argument("--model", "-m", default="moonshot-v1-32k", help="模型名称")
    parser.add_argument("--all", action="store_true", help="解决所有题目")
    parser.add_argument("--category", "-c", help="按类别筛选")
    parser.add_argument("--difficulty", "-d", help="按难度筛选")
    parser.add_argument("--challenge", help="解决特定题目")
    parser.add_argument("--timeout", "-t", type=int, default=120, help="每题超时时间")
    parser.add_argument("--output", "-o", help="输出报告文件")
    parser.add_argument("--workers", "-w", type=int, default=1, help="并行 workers")
    
    args = parser.parse_args()
    
    # 加载挑战
    loader = ChallengeLoader()
    
    if args.challenge:
        challenges = [loader.get(args.challenge)] if loader.get(args.challenge) else []
    elif args.category:
        challenges = loader.filter_by_category(args.category)
    elif args.difficulty:
        challenges = loader.filter_by_difficulty(args.difficulty)
    elif args.all:
        challenges = loader.list_all()
    else:
        print("请指定：--all, --category, --difficulty 或 --challenge")
        parser.print_help()
        return
    
    if not challenges:
        print("没有找到符合条件的挑战题目")
        return
    
    # 批量解题
    solver = BatchSolver(model_name=args.model, max_workers=args.workers)
    solver.solve_all(challenges, timeout=args.timeout)
    
    # 生成报告
    report = solver.generate_report()
    solver.print_report(report)
    
    # 保存报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 报告已保存: {args.output}")
    
    # 也保存到默认位置
    default_output = f"data/evaluation/batch_{time.strftime('%Y%m%d_%H%M%S')}.json"
    Path(default_output).parent.mkdir(parents=True, exist_ok=True)
    with open(default_output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 报告已保存: {default_output}")


if __name__ == "__main__":
    main()
