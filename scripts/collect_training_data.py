#!/usr/bin/env python3
"""
训练数据收集器 - 集成版

整合多个数据源，构建完整的训练数据集:
1. 本地Markdown文件 (已有)
2. CTF Writeup爬虫
3. 论文解析器
4. Agent解题轨迹

使用示例:
    # 收集所有来源
    python scripts/collect_training_data.py --all
    
    # 仅从本地收集
    python scripts/collect_training_data.py --local --source-dir D:/Crypto/做题笔记
    
    # 爬取CTF writeups
    python scripts/collect_training_data.py --writeups --limit 20
    
    # 从论文提取
    python scripts/collect_training_data.py --papers --limit 10
    
    # 合并所有数据
    python scripts/collect_training_data.py --merge-only
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TrainingDataCollector:
    """训练数据收集器"""
    
    def __init__(self, output_dir: str = "data/training"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.examples: List[Dict[str, Any]] = []
        self.source_stats = {}
    
    def collect_from_local(self, source_dir: str):
        """从本地Markdown收集"""
        print("\n" + "="*60)
        print("📁 从本地Markdown收集")
        print("="*60)
        
        from data_collector import CTFDataCollector
        
        collector = CTFDataCollector(source_dir)
        collector.process_directory()
        
        # 读取生成的文件
        combined_file = Path(source_dir).parent / "combined.jsonl"
        if combined_file.exists():
            with open(combined_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        self.examples.append(json.loads(line))
                    except:
                        pass
        
        count = len(self.examples) - sum(self.source_stats.values())
        self.source_stats['local_markdown'] = count
        print(f"✅ 从本地收集: {count} 条")
    
    def collect_from_writeups(self, limit: int = 10):
        """从CTF Writeup收集"""
        print("\n" + "="*60)
        print("🌐 从CTF Writeup收集")
        print("="*60)
        
        try:
            from crawler.writeup_crawler import WriteupDatasetBuilder
            
            builder = WriteupDatasetBuilder(output_dir="data/writeups")
            builder.crawl_all(crypto_only=True, limit_per_source=limit)
            builder.save()
            
            # 读取生成的训练数据
            training_file = Path("data/writeups/writeups_training.jsonl")
            if training_file.exists():
                count = 0
                with open(training_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            self.examples.append(json.loads(line))
                            count += 1
                        except:
                            pass
                self.source_stats['ctf_writeups'] = count
                print(f"✅ 从Writeup收集: {count} 条")
            
        except Exception as e:
            print(f"❌ Writeup收集失败: {e}")
    
    def collect_from_papers(self, limit: int = 5):
        """从论文收集"""
        print("\n" + "="*60)
        print("📚 从论文收集攻击方法")
        print("="*60)
        
        try:
            from paper_parser.paper_analyzer import PaperDatasetBuilder
            
            builder = PaperDatasetBuilder(output_dir="data/papers")
            builder.collect_from_arxiv(limit_per_query=limit)
            builder.generate_codes()
            builder.save()
            
            # 转换攻击方法为训练数据
            for method in builder.methods:
                if method.confidence >= 0.6:
                    example = {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a cryptography expert. Explain attack methods and generate implementation code."
                            },
                            {
                                "role": "user",
                                "content": f"Explain the {method.name} attack from the paper '{method.paper_title}'."
                            },
                            {
                                "role": "assistant",
                                "content": f"""# {method.name}

## Description
{method.description}

## Prerequisites
{chr(10).join('- ' + p for p in method.prerequisites)}

## Complexity
- Time: {method.complexity.get('time', 'Unknown')}
- Space: {method.complexity.get('space', 'Unknown')}

## Implementation
```python
{method.python_code[:500]}
```

## Reference
- Paper: {method.paper_title}
- Authors: {', '.join(method.authors[:3])}
- Year: {method.year}
- URL: {method.source_url}
"""
                            }
                        ],
                        "metadata": {
                            "source": "paper",
                            "attack_type": method.attack_type.value,
                            "confidence": method.confidence
                        }
                    }
                    self.examples.append(example)
            
            self.source_stats['papers'] = len([e for e in self.examples if e.get('metadata', {}).get('source') == 'paper'])
            print(f"✅ 从论文收集: {self.source_stats['papers']} 条")
            
        except Exception as e:
            print(f"❌ 论文收集失败: {e}")
    
    def collect_from_trajectories(self, trajectories_dir: str = "data/trajectories"):
        """从Agent解题轨迹收集"""
        print("\n" + "="*60)
        print("🤖 从Agent轨迹收集")
        print("="*60)
        
        traj_dir = Path(trajectories_dir)
        if not traj_dir.exists():
            print(f"⚠️  轨迹目录不存在: {trajectories_dir}")
            return
        
        count = 0
        for traj_file in traj_dir.glob("*.json"):
            try:
                with open(traj_file, 'r', encoding='utf-8') as f:
                    traj = json.load(f)
                
                # 只收集成功的轨迹
                if traj.get('success') and traj.get('flag'):
                    example = {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a CTF crypto expert. Solve the challenge step by step."
                            },
                            {
                                "role": "user",
                                "content": traj.get('challenge_description', '')
                            },
                            {
                                "role": "assistant",
                                "content": f"解题过程:\n{traj.get('output', '')[:1000]}\n\nFlag: {traj.get('flag')}"
                            }
                        ],
                        "metadata": {
                            "source": "agent_trajectory",
                            "challenge_name": traj.get('challenge_name'),
                            "success": True
                        }
                    }
                    self.examples.append(example)
                    count += 1
            except Exception as e:
                pass
        
        self.source_stats['agent_trajectories'] = count
        print(f"✅ 从轨迹收集: {count} 条")
    
    def deduplicate(self):
        """去重"""
        print("\n" + "="*60)
        print("🧹 数据去重")
        print("="*60)
        
        seen = set()
        unique_examples = []
        
        for example in self.examples:
            # 计算内容哈希
            content = json.dumps(example.get('messages', []), sort_keys=True)
            hash_val = hash(content) % (2**32)
            
            if hash_val not in seen:
                seen.add(hash_val)
                unique_examples.append(example)
        
        removed = len(self.examples) - len(unique_examples)
        self.examples = unique_examples
        
        print(f"  去重前: {len(self.examples) + removed}")
        print(f"  去重后: {len(self.examples)}")
        print(f"  移除重复: {removed}")
    
    def split_train_val(self, val_ratio: float = 0.2):
        """分割训练集和验证集"""
        import random
        random.seed(42)
        
        random.shuffle(self.examples)
        
        val_size = int(len(self.examples) * val_ratio)
        train_examples = self.examples[val_size:]
        val_examples = self.examples[:val_size]
        
        return train_examples, val_examples
    
    def save(self):
        """保存数据集"""
        print("\n" + "="*60)
        print("💾 保存数据集")
        print("="*60)
        
        # 去重
        self.deduplicate()
        
        # 分割
        train, val = self.split_train_val(val_ratio=0.2)
        
        # 保存训练集
        train_file = self.output_dir / "train_augmented.jsonl"
        with open(train_file, 'w', encoding='utf-8') as f:
            for ex in train:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
        print(f"✅ 训练集: {train_file} ({len(train)} 条)")
        
        # 保存验证集
        val_file = self.output_dir / "val_augmented.jsonl"
        with open(val_file, 'w', encoding='utf-8') as f:
            for ex in val:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
        print(f"✅ 验证集: {val_file} ({len(val)} 条)")
        
        # 保存统计
        stats = {
            "total": len(self.examples),
            "train": len(train),
            "validation": len(val),
            "by_source": self.source_stats
        }
        
        stats_file = self.output_dir / "collection_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"✅ 统计信息: {stats_file}")
        
        return stats


def main():
    parser = argparse.ArgumentParser(description="训练数据收集器")
    parser.add_argument("--all", action="store_true", help="收集所有来源")
    parser.add_argument("--local", action="store_true", help="从本地Markdown收集")
    parser.add_argument("--source-dir", default="D:/Crypto/做题笔记", help="本地源目录")
    parser.add_argument("--writeups", action="store_true", help="爬取CTF writeups")
    parser.add_argument("--papers", action="store_true", help="从论文提取")
    parser.add_argument("--trajectories", action="store_true", help="从Agent轨迹收集")
    parser.add_argument("--limit", "-l", type=int, default=10, help="每来源最大数量")
    parser.add_argument("--output", "-o", default="data/training", help="输出目录")
    
    args = parser.parse_args()
    
    collector = TrainingDataCollector(output_dir=args.output)
    
    # 如果没有指定任何来源，默认收集全部
    if not any([args.all, args.local, args.writeups, args.papers, args.trajectories]):
        args.all = True
    
    if args.all or args.local:
        collector.collect_from_local(args.source_dir)
    
    if args.all or args.writeups:
        collector.collect_from_writeups(limit=args.limit)
    
    if args.all or args.papers:
        collector.collect_from_papers(limit=args.limit)
    
    if args.all or args.trajectories:
        collector.collect_from_trajectories()
    
    # 保存
    stats = collector.save()
    
    print("\n" + "="*60)
    print("✨ 数据收集完成!")
    print("="*60)
    print(f"总计: {stats['total']} 条")
    print(f"训练集: {stats['train']} 条")
    print(f"验证集: {stats['validation']} 条")
    print("\n来源分布:")
    for source, count in stats['by_source'].items():
        print(f"  {source}: {count} 条")


if __name__ == "__main__":
    main()
