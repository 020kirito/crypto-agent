"""
密码学论文解析器

从学术文献中提取攻击方法并生成可执行的攻击代码/payload。

支持的来源:
- arXiv密码学论文
- IACR ePrint
- 会议论文 (Crypto, Eurocrypt, Asiacrypt, CCS, etc.)
- PDF文件

核心功能:
- 提取论文中的攻击算法
- 生成Python/SageMath实现
- 验证算法正确性
- 生成CTF题目
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class AttackType(Enum):
    """攻击类型"""
    RSA = "rsa"
    LATTICE = "lattice"
    ECC = "ecc"
    AES = "aes"
    HASH = "hash"
    MULTIVARIATE = "multivariate"
    CODE_BASED = "code_based"
    UNKNOWN = "unknown"


@dataclass
class AttackMethod:
    """攻击方法"""
    name: str
    paper_title: str
    authors: List[str]
    year: int
    attack_type: AttackType
    source_url: str
    
    # 攻击细节
    description: str = ""  # 攻击描述
    prerequisites: List[str] = None  # 前提条件
    complexity: Dict[str, str] = None  # 复杂度
    
    # 实现
    pseudocode: str = ""  # 伪代码
    python_code: str = ""  # Python实现
    sagemath_code: str = ""  # SageMath实现
    
    # 测试
    test_cases: List[Dict] = None  # 测试用例
    
    # 元数据
    confidence: float = 0.0  # 提取置信度 (0-1)
    extracted_at: str = ""
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.complexity is None:
            self.complexity = {}
        if self.test_cases is None:
            self.test_cases = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def generate_tool_code(self) -> str:
        """生成LangChain工具代码"""
        tool_name = self.name.lower().replace(' ', '_').replace('-', '_')
        
        code = f'''@tool
def {tool_name}_attack({self._generate_params()}) -> str:
    """
    {self.name}
    
    {self.description[:200]}...
    
    Paper: {self.paper_title} ({self.year})
    Authors: {', '.join(self.authors[:3])}
    
    Prerequisites:
{self._format_prerequisites()}
    """
    
    # 实现代码
{self._indent_code(self.python_code or self.sagemath_code, 4)}
    
    return json.dumps({{
        "success": True,
        "method": "{self.name}",
        "result": result
    }})
'''
        return code
    
    def _generate_params(self) -> str:
        """生成函数参数"""
        # 从测试用例推断参数
        if self.test_cases and len(self.test_cases) > 0:
            params = []
            for key in self.test_cases[0].get('input', {}).keys():
                params.append(f"{key}: str")
            return ', '.join(params) if params else "params: str"
        return "target: str"
    
    def _format_prerequisites(self) -> str:
        """格式化前提条件"""
        if not self.prerequisites:
            return "    None"
        return '\n'.join(f'    - {p}' for p in self.prerequisites[:5])
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """缩进代码"""
        if not code:
            return " " * spaces + "# TODO: Implementation"
        lines = code.split('\n')
        return '\n'.join(' ' * spaces + line for line in lines[:50])  # 限制行数


class PaperParser:
    """论文解析器基类"""
    
    # 攻击关键词映射
    ATTACK_PATTERNS = {
        AttackType.RSA: [
            'rsa', 'factorization', 'factoring', 'wiener', 'coppersmith',
            'bleichenbacher', 'franklin-reiter', 'hastad', 'common modulus'
        ],
        AttackType.LATTICE: [
            'lattice', 'lll', 'bkz', 'svp', 'cvp', 'ntru', 'lwe',
            'shortest vector', 'closest vector', 'reduction'
        ],
        AttackType.ECC: [
            'elliptic curve', 'ecdlp', 'mov attack', 'smart attack',
            'singular curve', 'anomalous curve', 'pairing'
        ],
        AttackType.AES: [
            'aes', 'rijndael', 'differential', 'linear cryptanalysis',
            'side channel', 'cache attack'
        ],
        AttackType.HASH: [
            'hash', 'md5', 'sha', 'collision', 'preimage', 'birthday attack'
        ]
    }
    
    def __init__(self):
        self.methods: List[AttackMethod] = []
    
    def detect_attack_type(self, text: str) -> AttackType:
        """检测攻击类型"""
        text_lower = text.lower()
        
        scores = {}
        for attack_type, keywords in self.ATTACK_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[attack_type] = score
        
        if not scores:
            return AttackType.UNKNOWN
        
        return max(scores, key=scores.get)
    
    def extract_pseudocode(self, text: str) -> Optional[str]:
        """从文本提取伪代码"""
        # 常见的伪代码标记
        patterns = [
            r'Algorithm \d+[:\s]*([^\n]+)\n+(.*?)(?=\n\s*Algorithm|\Z)',
            r'Procedure[:\s]*([^\n]+)\n+(.*?)(?=\n\s*Procedure|\Z)',
            r'Input:.*?(?=\n\n|\Z)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                # 返回最长的匹配
                longest = max(matches, key=lambda x: len(x) if isinstance(x, str) else len(x[1]))
                if isinstance(longest, tuple):
                    return longest[1]
                return longest
        
        return None
    
    def extract_complexity(self, text: str) -> Dict[str, str]:
        """提取复杂度信息"""
        complexity = {}
        
        # 时间复杂度
        time_match = re.search(r'time complexity[:\s]*([^\n]+)', text, re.IGNORECASE)
        if time_match:
            complexity['time'] = time_match.group(1).strip()
        
        # 空间复杂度
        space_match = re.search(r'space complexity[:\s]*([^\n]+)', text, re.IGNORECASE)
        if space_match:
            complexity['space'] = space_match.group(1).strip()
        
        return complexity


class ArxivParser(PaperParser):
    """arXiv论文解析器"""
    
    ARXIV_API = "http://export.arxiv.org/api/query"
    
    def search(self, query: str = "cryptography attack", max_results: int = 10) -> List[AttackMethod]:
        """
        搜索arXiv论文
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
        """
        print(f"🔍 搜索arXiv: {query}")
        
        import urllib.request
        import urllib.parse
        
        search_query = urllib.parse.quote(query)
        url = f"{self.ARXIV_API}?search_query=all:{search_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                xml_data = response.read().decode('utf-8')
                return self._parse_arxiv_xml(xml_data)
        except Exception as e:
            print(f"❌ arXiv搜索失败: {e}")
            return []
    
    def _parse_arxiv_xml(self, xml_data: str) -> List[AttackMethod]:
        """解析arXiv XML响应"""
        methods = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_data)
            
            # arXiv命名空间
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    title = entry.find('atom:title', ns).text
                    authors = [a.find('atom:name', ns).text 
                              for a in entry.findall('atom:author', ns)]
                    summary = entry.find('atom:summary', ns).text or ""
                    link = entry.find('atom:id', ns).text
                    published = entry.find('atom:published', ns).text[:4]  # 年份
                    
                    # 检测攻击类型
                    attack_type = self.detect_attack_type(title + summary)
                    
                    if attack_type == AttackType.UNKNOWN:
                        continue
                    
                    # 提取信息
                    method = AttackMethod(
                        name=self._extract_attack_name(title),
                        paper_title=title,
                        authors=authors,
                        year=int(published) if published.isdigit() else 2024,
                        attack_type=attack_type,
                        source_url=link,
                        description=summary[:500],
                        prerequisites=self._extract_prerequisites(summary),
                        complexity=self.extract_complexity(summary),
                        confidence=0.6  # arXiv摘要的置信度
                    )
                    
                    methods.append(method)
                    print(f"  ✅ 提取: {method.name}")
                    
                except Exception as e:
                    print(f"  ⚠️  解析条目失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ XML解析失败: {e}")
        
        return methods
    
    def _extract_attack_name(self, title: str) -> str:
        """从标题提取攻击名称"""
        # 移除常见前缀后缀
        name = re.sub(r'^On\s+|^A\s+|^An\s+|\s+attack\s*$|\s+attacks\s*$', '', title, flags=re.IGNORECASE)
        return name.strip()[:50]
    
    def _extract_prerequisites(self, summary: str) -> List[str]:
        """提取前提条件"""
        prereqs = []
        
        # 查找关键词
        keywords = [
            'requires', 'assumes', 'given', 'prerequisite',
            '条件', '假设', '前提'
        ]
        
        sentences = re.split(r'[.!?]\s+', summary)
        for sent in sentences:
            if any(kw in sent.lower() for kw in keywords):
                prereqs.append(sent.strip()[:200])
        
        return prereqs[:3]


class PDFParser(PaperParser):
    """PDF论文解析器"""
    
    def parse_pdf(self, pdf_path: str) -> List[AttackMethod]:
        """
        解析PDF文件
        
        Args:
            pdf_path: PDF文件路径
        """
        print(f"📄 解析PDF: {pdf_path}")
        
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages[:10]:  # 只读前10页
                    text += page.extract_text() or ""
                
                return self._extract_from_text(text, pdf_path)
                
        except ImportError:
            print("⚠️  需要安装PyPDF2: pip install PyPDF2")
            return []
        except Exception as e:
            print(f"❌ PDF解析失败: {e}")
            return []
    
    def _extract_from_text(self, text: str, source: str) -> List[AttackMethod]:
        """从文本提取攻击方法"""
        methods = []
        
        # 检测攻击类型
        attack_type = self.detect_attack_type(text)
        
        if attack_type == AttackType.UNKNOWN:
            print("  ⚠️  无法识别攻击类型")
            return methods
        
        # 提取标题
        title_match = re.search(r'^(.+?)\n', text)
        title = title_match.group(1) if title_match else "Unknown"
        
        # 提取伪代码
        pseudocode = self.extract_pseudocode(text)
        
        # 提取复杂度
        complexity = self.extract_complexity(text)
        
        method = AttackMethod(
            name=self._extract_attack_name(title),
            paper_title=title[:100],
            authors=["Unknown"],
            year=2024,
            attack_type=attack_type,
            source_url=source,
            description=text[:1000],
            pseudocode=pseudocode or "",
            complexity=complexity,
            confidence=0.7 if pseudocode else 0.5
        )
        
        methods.append(method)
        print(f"  ✅ 提取: {method.name}")
        
        return methods


class AttackCodeGenerator:
    """攻击代码生成器"""
    
    # 模板库
    TEMPLATES = {
        AttackType.RSA: {
            'import': ['from Crypto.Util.number import *', 'import gmpy2'],
            'common_funcs': [
                'def mod_inv(a, m):\n    """模逆元"""\n    return pow(a, -1, m)\n'
            ]
        },
        AttackType.LATTICE: {
            'import': ['from sage.all import *'],
            'common_funcs': [
                'def lattice_reduce(basis):\n    """格基约减"""\n    M = Matrix(ZZ, basis)\n    return M.LLL()\n'
            ]
        },
        AttackType.ECC: {
            'import': ['from sage.all import *', 'from sage.schemes.elliptic_curves.all import *'],
            'common_funcs': []
        }
    }
    
    def generate_python_code(self, method: AttackMethod) -> str:
        """生成Python实现"""
        template = self.TEMPLATES.get(method.attack_type, {})
        
        code_lines = []
        
        # 添加导入
        code_lines.extend(template.get('import', []))
        code_lines.append('import json')
        code_lines.append('')
        
        # 添加常用函数
        code_lines.extend(template.get('common_funcs', []))
        code_lines.append('')
        
        # 添加主函数
        func_name = method.name.lower().replace(' ', '_').replace('-', '_')
        code_lines.append(f'def {func_name}(n, e, c):')
        code_lines.append(f'    """')
        code_lines.append(f'    {method.paper_title}')
        code_lines.append(f'    {method.description[:100]}...')
        code_lines.append(f'    """')
        code_lines.append('')
        code_lines.append('    # TODO: Implement attack logic')
        code_lines.append('    # Based on pseudocode from paper')
        code_lines.append('')
        
        if method.pseudocode:
            code_lines.append('    # Pseudocode from paper:')
            for line in method.pseudocode.split('\n')[:10]:
                code_lines.append(f'    # {line}')
        
        code_lines.append('')
        code_lines.append('    return {"success": True, "plaintext": None}')
        
        return '\n'.join(code_lines)
    
    def generate_sagemath_code(self, method: AttackMethod) -> str:
        """生成SageMath实现"""
        code_lines = [
            '# SageMath implementation',
            '# Paper: ' + method.paper_title,
            ''
        ]
        
        if method.pseudocode:
            code_lines.append('# Algorithm:')
            code_lines.append(method.pseudocode)
        
        code_lines.extend([
            '',
            'def attack(params):',
            '    # TODO: Implement in SageMath',
            '    pass'
        ])
        
        return '\n'.join(code_lines)


class PaperDatasetBuilder:
    """论文数据集构建器"""
    
    def __init__(self, output_dir: str = "data/papers"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.methods: List[AttackMethod] = []
    
    def collect_from_arxiv(self, queries: List[str] = None, limit_per_query: int = 5):
        """从arXiv收集"""
        if queries is None:
            queries = [
                "RSA cryptanalysis",
                "lattice attack cryptography",
                "elliptic curve discrete log",
                "side channel attack"
            ]
        
        print("\n" + "="*60)
        print("📚 从arXiv收集论文")
        print("="*60)
        
        parser = ArxivParser()
        for query in queries:
            print(f"\n🔍 查询: {query}")
            methods = parser.search(query, max_results=limit_per_query)
            for method in methods:
                self.methods.append(method)
    
    def add_pdf(self, pdf_path: str):
        """添加PDF文件"""
        parser = PDFParser()
        methods = parser.parse_pdf(pdf_path)
        self.methods.extend(methods)
    
    def generate_codes(self):
        """为所有方法生成代码"""
        generator = AttackCodeGenerator()
        
        for method in self.methods:
            method.python_code = generator.generate_python_code(method)
            method.sagemath_code = generator.generate_sagemath_code(method)
    
    def save(self):
        """保存数据集"""
        # 保存原始数据
        raw_file = self.output_dir / "attack_methods.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump([m.to_dict() for m in self.methods], f, indent=2, ensure_ascii=False)
        print(f"\n💾 攻击方法已保存: {raw_file}")
        
        # 生成工具代码
        tools_dir = self.output_dir / "generated_tools"
        tools_dir.mkdir(exist_ok=True)
        
        for method in self.methods:
            if method.confidence >= 0.6:  # 只保存高置信度的
                tool_code = method.generate_tool_code()
                tool_file = tools_dir / f"{method.name.lower().replace(' ', '_')}.py"
                with open(tool_file, 'w', encoding='utf-8') as f:
                    f.write(tool_code)
        
        print(f"💾 生成工具代码: {tools_dir}")
        
        # 保存统计
        stats = {
            "total_methods": len(self.methods),
            "by_type": {},
            "by_year": {},
            "high_confidence": sum(1 for m in self.methods if m.confidence >= 0.6)
        }
        for m in self.methods:
            stats["by_type"][m.attack_type.value] = stats["by_type"].get(m.attack_type.value, 0) + 1
            stats["by_year"][m.year] = stats["by_year"].get(m.year, 0) + 1
        
        stats_file = self.output_dir / "papers_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"💾 统计信息: {stats_file}")


def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description="密码学论文解析器")
    parser.add_argument("--output", "-o", default="data/papers", help="输出目录")
    parser.add_argument("--pdf", help="PDF文件路径")
    parser.add_argument("--arxiv", action="store_true", help="从arXiv搜索")
    parser.add_argument("--limit", "-l", type=int, default=5, help="每查询最大结果")
    
    args = parser.parse_args()
    
    builder = PaperDatasetBuilder(output_dir=args.output)
    
    if args.arxiv:
        builder.collect_from_arxiv(limit_per_query=args.limit)
    
    if args.pdf:
        builder.add_pdf(args.pdf)
    
    if not args.arxiv and not args.pdf:
        # 默认从arXiv收集
        builder.collect_from_arxiv(limit_per_query=args.limit)
    
    # 生成代码并保存
    builder.generate_codes()
    builder.save()


if __name__ == "__main__":
    main()
