"""
工具和资源提取器

专门分析writeup内容，提取:
1. 使用的工具及用法
2. 引用的资料和链接
3. 关键代码片段
4. 数学公式和算法
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


# CTF密码学常用工具库
CRYPTO_TOOLS = {
    # 数学计算
    'sage': {'name': 'SageMath', 'category': 'math', 'description': '数学计算系统，用于数论、代数、椭圆曲线等'},
    'sagemath': {'name': 'SageMath', 'category': 'math'},
    'pari': {'name': 'PARI/GP', 'category': 'math', 'description': '数论计算库'},
    'gp': {'name': 'PARI/GP', 'category': 'math'},
    'magma': {'name': 'Magma', 'category': 'math', 'description': '代数系统'},
    
    # 格密码
    'flatter': {'name': 'FLATTER', 'category': 'lattice', 'description': '高性能LLL格基约减'},
    'fplll': {'name': 'fplll', 'category': 'lattice', 'description': '快速LLL库'},
    'bkz': {'name': 'BKZ', 'category': 'lattice', 'description': 'BKZ格基约减算法'},
    
    # 因式分解
    'yafu': {'name': 'YAFU', 'category': 'factoring', 'description': '因式分解工具'},
    'cado': {'name': 'CADO-NFS', 'category': 'factoring', 'description': '数域筛因式分解'},
    'cado-nfs': {'name': 'CADO-NFS', 'category': 'factoring'},
    'factordb': {'name': 'FactorDB', 'category': 'factoring', 'description': '因数数据库'},
    'alpertron': {'name': 'Alpertron', 'category': 'factoring', 'description': '在线因式分解'},
    
    # 密码破解
    'hashcat': {'name': 'Hashcat', 'category': 'cracking', 'description': 'GPU密码破解'},
    'john': {'name': 'John the Ripper', 'category': 'cracking', 'description': '密码破解工具'},
    'hydra': {'name': 'Hydra', 'category': 'cracking', 'description': '在线破解工具'},
    
    # Python库
    'pwntools': {'name': 'pwntools', 'category': 'python', 'description': 'CTF exploit框架'},
    'gmpy2': {'name': 'gmpy2', 'category': 'python', 'description': '高精度数学库'},
    'pycryptodome': {'name': 'PyCryptodome', 'category': 'python', 'description': '密码学库'},
    'z3': {'name': 'Z3', 'category': 'python', 'description': 'SMT求解器'},
    'sympy': {'name': 'SymPy', 'category': 'python', 'description': '符号计算库'},
    'numpy': {'name': 'NumPy', 'category': 'python', 'description': '数值计算库'},
    'owi': {'name': 'OWI', 'category': 'python', 'description': '在线密码工具接口'},
    
    # RSA专用
    'rsactftool': {'name': 'RsaCtfTool', 'category': 'rsa', 'description': 'RSA攻击工具集'},
    'rsa': {'name': 'RSA相关工具', 'category': 'rsa'},
    'wiener': {'name': 'Wiener Attack', 'category': 'rsa', 'description': 'Wiener攻击'},
    'boneh': {'name': 'Boneh-Durfee', 'category': 'rsa', 'description': 'Boneh-Durfee攻击'},
    
    # 逆向/调试
    'ida': {'name': 'IDA Pro', 'category': 'reverse', 'description': '反汇编器'},
    'ghidra': {'name': 'Ghidra', 'category': 'reverse', 'description': '开源逆向工具'},
    'gdb': {'name': 'GDB', 'category': 'reverse', 'description': '调试器'},
    'pwndbg': {'name': 'pwndbg', 'category': 'reverse', 'description': 'GDB插件'},
    'angr': {'name': 'angr', 'category': 'reverse', 'description': '二进制分析框架'},
    
    # 其他
    'openssl': {'name': 'OpenSSL', 'category': 'crypto', 'description': '密码学工具包'},
    'sagecell': {'name': 'SageCell', 'category': 'web', 'description': '在线SageMath'},
    'cryptohack': {'name': 'CryptoHack', 'category': 'learning', 'description': '密码学学习平台'},
    'cryptopals': {'name': 'Cryptopals', 'category': 'learning', 'description': '密码学挑战'},
}


@dataclass
class ToolUsage:
    """工具使用记录"""
    name: str
    category: str
    context: str  # 使用场景
    code_example: str = ""  # 代码示例
    source_url: str = ""  # 来源文章


@dataclass
class ResourceLink:
    """资源链接"""
    title: str
    url: str
    description: str
    resource_type: str  # tool, paper, blog, github


class ToolsExtractor:
    """工具和资源提取器"""
    
    def __init__(self):
        self.tools_usage: List[ToolUsage] = []
        self.resources: List[ResourceLink] = []
        self.code_snippets: List[Dict] = []
    
    def extract_from_writeup(self, title: str, content: str, code_blocks: List[str], url: str):
        """从writeup提取工具和资源"""
        content_lower = content.lower()
        
        # 1. 提取工具使用
        for keyword, tool_info in CRYPTO_TOOLS.items():
            if keyword in content_lower:
                # 找到使用上下文
                pattern = r'.{0,150}' + re.escape(keyword) + r'.{0,150}'
                matches = re.findall(pattern, content, re.IGNORECASE)
                
                for match in matches[:2]:  # 最多2个上下文
                    # 清理文本
                    context = re.sub(r'\s+', ' ', match).strip()
                    
                    # 找相关代码
                    code_example = ""
                    for code in code_blocks:
                        if keyword.lower() in code.lower():
                            code_example = code[:500]
                            break
                    
                    self.tools_usage.append(ToolUsage(
                        name=tool_info['name'],
                        category=tool_info.get('category', 'other'),
                        context=context,
                        code_example=code_example,
                        source_url=url
                    ))
        
        # 2. 提取链接资源
        url_pattern = r'https?://[^\s\)\"\'\>]+'
        urls = re.findall(url_pattern, content)
        
        for link in set(urls):
            if len(link) < 100:  # 过滤过长URL
                # 推断资源类型
                rtype = 'link'
                if 'github' in link:
                    rtype = 'github'
                elif 'arxiv' in link:
                    rtype = 'paper'
                elif 'pdf' in link:
                    rtype = 'paper'
                elif any(x in link for x in ['tool', 'ctf', 'crypto']):
                    rtype = 'tool'
                
                self.resources.append(ResourceLink(
                    title=f"链接来自: {title[:30]}...",
                    url=link,
                    description="文章中引用的外部资源",
                    resource_type=rtype
                ))
        
        # 3. 提取代码片段
        for i, code in enumerate(code_blocks[:5]):
            # 识别代码类型
            lang = self._detect_language(code)
            
            self.code_snippets.append({
                'language': lang,
                'code': code[:1000],  # 截断
                'source': url,
                'description': f"来自: {title[:50]}"
            })
    
    def _detect_language(self, code: str) -> str:
        """检测代码语言"""
        code_lower = code.lower()[:200]
        
        if any(x in code_lower for x in ['def ', 'import ', 'print(', '# ', 'python']):
            return 'python'
        elif any(x in code_lower for x in ['sage:', 'GF(', 'ZZ[', 'EllipticCurve']):
            return 'sage'
        elif any(x in code_lower for x in ['<?php', 'echo', '$']):
            return 'php'
        elif any(x in code_lower for x in ['#include', 'int main', 'cout']):
            return 'cpp'
        elif any(x in code_lower for x in ['function', 'var ', 'console.log']):
            return 'javascript'
        elif any(x in code_lower for x in ['pip', 'apt', 'git ', 'bash', '$ ']):
            return 'bash'
        else:
            return 'text'
    
    def generate_tool_guides(self) -> Dict[str, List[Dict]]:
        """生成工具使用指南"""
        guides = {}
        
        # 按工具分组
        tools_dict = {}
        for usage in self.tools_usage:
            if usage.name not in tools_dict:
                tools_dict[usage.name] = {
                    'name': usage.name,
                    'category': usage.category,
                    'usages': []
                }
            tools_dict[usage.name]['usages'].append({
                'context': usage.context,
                'code': usage.code_example,
                'source': usage.source_url
            })
        
        # 按类别分组
        for name, info in tools_dict.items():
            cat = info['category']
            if cat not in guides:
                guides[cat] = []
            
            # 合并使用场景
            all_contexts = '\n\n'.join([u['context'] for u in info['usages'][:3]])
            all_codes = '\n\n'.join([u['code'] for u in info['usages'][:3] if u['code']])
            
            guides[cat].append({
                'tool': name,
                'usage_count': len(info['usages']),
                'contexts': all_contexts[:1000],
                'code_examples': all_codes[:1500]
            })
        
        return guides
    
    def save(self, output_dir: str = "data/tangcu_blog"):
        """保存提取结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 工具使用记录
        tools_file = output_path / "extracted_tools.json"
        with open(tools_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(t) for t in self.tools_usage], f, indent=2, ensure_ascii=False)
        print(f"💾 工具使用记录: {tools_file} ({len(self.tools_usage)} 条)")
        
        # 2. 资源链接
        resources_file = output_path / "extracted_resources.json"
        with open(resources_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in self.resources], f, indent=2, ensure_ascii=False)
        print(f"💾 资源链接: {resources_file} ({len(self.resources)} 条)")
        
        # 3. 代码片段
        code_file = output_path / "extracted_code.json"
        with open(code_file, 'w', encoding='utf-8') as f:
            json.dump(self.code_snippets, f, indent=2, ensure_ascii=False)
        print(f"💾 代码片段: {code_file} ({len(self.code_snippets)} 个)")
        
        # 4. 工具指南
        guides = self.generate_tool_guides()
        guides_file = output_path / "tool_guides.json"
        with open(guides_file, 'w', encoding='utf-8') as f:
            json.dump(guides, f, indent=2, ensure_ascii=False)
        print(f"💾 工具指南: {guides_file} ({len(guides)} 个类别)")
        
        # 5. 训练数据 - 工具使用
        train_tools = output_path / "training_tools.jsonl"
        with open(train_tools, 'w', encoding='utf-8') as f:
            for usage in self.tools_usage:
                example = {
                    "messages": [
                        {"role": "system", "content": "You are a CTF crypto expert. Explain how to use cryptographic tools."},
                        {"role": "user", "content": f"如何在CTF题目中使用 {usage.name}?"},
                        {"role": "assistant", "content": f"工具: {usage.name}\n\n使用场景:\n{usage.context[:500]}\n\n代码示例:\n```{usage.code_example[:400] if usage.code_example else '代码见原文'}\n```"}
                    ],
                    "metadata": {"tool": usage.name, "category": usage.category, "source": usage.source_url}
                }
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        print(f"💾 工具训练数据: {train_tools}")
        
        # 6. 统计
        stats = {
            "total_tools": len(set(t.name for t in self.tools_usage)),
            "total_usages": len(self.tools_usage),
            "total_resources": len(self.resources),
            "total_code_snippets": len(self.code_snippets),
            "by_category": {}
        }
        
        for t in self.tools_usage:
            cat = t.category
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        
        stats_file = output_path / "extraction_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"💾 统计信息: {stats_file}")
        
        return stats


def extract_from_blog_writeups(writeups_dir: str = "data/tangcu_blog"):
    """从博客writeup提取工具和资源"""
    writeups_path = Path(writeups_dir)
    
    # 读取writeups
    raw_file = writeups_path / "writeups_raw.json"
    if not raw_file.exists():
        print(f"❌ 找不到文件: {raw_file}")
        return
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        writeups = json.load(f)
    
    print(f"📂 加载了 {len(writeups)} 篇writeup")
    
    extractor = ToolsExtractor()
    
    for w in writeups:
        extractor.extract_from_writeup(
            title=w.get('title', ''),
            content=w.get('content', ''),
            code_blocks=[c.get('code', '') for c in w.get('code_snippets', [])],
            url=w.get('url', '')
        )
    
    stats = extractor.save(writeups_dir)
    
    print("\n" + "="*60)
    print("📊 提取统计")
    print("="*60)
    print(f"独特工具: {stats['total_tools']}")
    print(f"使用记录: {stats['total_usages']}")
    print(f"资源链接: {stats['total_resources']}")
    print(f"代码片段: {stats['total_code_snippets']}")
    print("\n工具类别分布:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        extract_from_blog_writeups(sys.argv[1])
    else:
        extract_from_blog_writeups()
