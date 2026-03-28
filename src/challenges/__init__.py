"""
CTF挑战题目加载器

用于加载和管理CTF密码学挑战题目
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class ChallengeLoader:
    """CTF挑战题目加载器"""
    
    def __init__(self, challenges_dir: str = "challenges"):
        self.challenges_dir = Path(challenges_dir)
        self.challenges: Dict[str, Dict[str, Any]] = {}
        self._load_all()
    
    def _load_all(self):
        """加载所有挑战题目"""
        if not self.challenges_dir.exists():
            return
        
        for json_file in self.challenges_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    challenge = json.load(f)
                    challenge['_file'] = str(json_file)
                    self.challenges[challenge['name']] = challenge
            except Exception as e:
                print(f"⚠️  加载 {json_file} 失败: {e}")
    
    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定名称的挑战"""
        return self.challenges.get(name)
    
    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有挑战"""
        return list(self.challenges.values())
    
    def filter_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别筛选"""
        return [c for c in self.challenges.values() 
                if c.get('category') == category]
    
    def filter_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """按难度筛选"""
        return [c for c in self.challenges.values() 
                if c.get('difficulty') == difficulty]
    
    def get_categories(self) -> List[str]:
        """获取所有类别"""
        return sorted(set(c.get('category', 'unknown') 
                         for c in self.challenges.values()))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total': len(self.challenges),
            'by_category': {},
            'by_difficulty': {}
        }
        
        for c in self.challenges.values():
            cat = c.get('category', 'unknown')
            diff = c.get('difficulty', 'unknown')
            
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            stats['by_difficulty'][diff] = stats['by_difficulty'].get(diff, 0) + 1
        
        return stats


def load_challenge(name: str) -> Optional[Dict[str, Any]]:
    """便捷函数：加载指定挑战"""
    loader = ChallengeLoader()
    return loader.get(name)


def list_challenges(category: Optional[str] = None, 
                   difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """便捷函数：列挑战"""
    loader = ChallengeLoader()
    
    challenges = loader.list_all()
    
    if category:
        challenges = [c for c in challenges if c.get('category') == category]
    if difficulty:
        challenges = [c for c in challenges if c.get('difficulty') == difficulty]
    
    return challenges


if __name__ == "__main__":
    # 测试
    loader = ChallengeLoader()
    stats = loader.get_statistics()
    
    print("=" * 50)
    print("CTF 挑战题目库")
    print("=" * 50)
    print(f"总计: {stats['total']} 题")
    print("\n按类别:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"  {cat}: {count} 题")
    print("\n按难度:")
    for diff, count in sorted(stats['by_difficulty'].items()):
        print(f"  {diff}: {count} 题")
