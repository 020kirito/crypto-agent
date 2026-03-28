"""
糖醋小鸡块博客爬虫

专门爬取 https://tangcuxiaojikuai.xyz/ 的CTF Crypto Writeup
自动提取:
- 题目描述和解题思路
- 代码片段
- 提到的工具和资料
- 数学公式和算法
"""

import re
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin, urlparse
import urllib.request
from urllib.error import HTTPError


@dataclass
class ToolReference:
    """工具引用"""
    name: str
    context: str  # 上下文描述
    link: Optional[str] = None
    usage: Optional[str] = None  # 使用方法


@dataclass
class ResourceReference:
    """资料引用"""
    title: str
    link: Optional[str] = None
    description: str = ""
    resource_type: str = ""  # paper, blog, tool, etc.


@dataclass
class BlogWriteup:
    """博客Writeup"""
    title: str
    url: str
    category: str  # wp-crypto, 游记, etc.
    tags: List[str] = field(default_factory=list)
    
    # 内容
    description: str = ""  # 摘要
    content: str = ""  # 全文
    
    # 提取的元素
    code_snippets: List[Dict[str, str]] = field(default_factory=list)  # [{'lang': 'python', 'code': '...'}]
    math_formulas: List[str] = field(default_factory=list)  # LaTeX公式
    tools: List[ToolReference] = field(default_factory=list)
    resources: List[ResourceReference] = field(default_factory=list)
    
    # 元数据
    posted_date: Optional[str] = None
    author: str = "糖醋小鸡块"
    content_hash: str = ""
    
    def __post_init__(self):
        # 计算内容哈希用于去重
        content = f"{self.title}{self.content[:500]}"
        self.content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_training_example(self) -> Dict[str, Any]:
        """转换为训练数据格式"""
        # 构建工具和资源描述
        tools_desc = ""
        if self.tools:
            tools_desc = "\n使用的工具:\n" + "\n".join([
                f"- {t.name}: {t.context[:100]}"
                for t in self.tools[:5]
            ])
        
        resources_desc = ""
        if self.resources:
            resources_desc = "\n参考资料:\n" + "\n".join([
                f"- {r.title}: {r.description[:80]}"
                for r in self.resources[:5]
            ])
        
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a CTF crypto expert. Analyze the challenge and provide step-by-step solution."
                },
                {
                    "role": "user",
                    "content": f"【CTF Crypto Writeup】\n{self.title}\n\n{self.description[:500]}{tools_desc}{resources_desc}"
                },
                {
                    "role": "assistant",
                    "content": f"解题思路：\n{self.content[:1500]}\n\n关键代码片段:\n" + 
                              "\n\n".join([
                                  f"```{c.get('lang', '')}\n{c['code'][:300]}\n```"
                                  for c in self.code_snippets[:3]
                              ])
                }
            ],
            "metadata": {
                "source": self.url,
                "category": self.category,
                "tags": self.tags,
                "tools_used": [t.name for t in self.tools],
                "resources": [r.title for r in self.resources],
                "content_hash": self.content_hash
            }
        }
    
    def to_tools_dataset(self) -> List[Dict[str, Any]]:
        """生成工具使用训练数据"""
        examples = []
        
        for tool in self.tools:
            example = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a CTF crypto expert. Explain how to use cryptographic tools."
                    },
                    {
                        "role": "user",
                        "content": f"如何使用 {tool.name} 解决CTF题目?\n场景: {self.title}"
                    },
                    {
                        "role": "assistant",
                        "content": f"工具: {tool.name}\n\n使用场景:\n{tool.context[:500]}\n\n使用方法:\n{tool.usage or '详见代码示例'}"
                    }
                ],
                "metadata": {
                    "tool": tool.name,
                    "source": self.url,
                    "type": "tool_usage"
                }
            }
            examples.append(example)
        
        return examples


class TangcuBlogCrawler:
    """糖醋小鸡块博客爬虫"""
    
    BASE_URL = "https://tangcuxiaojikuai.xyz"
    
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.writeups: List[BlogWriteup] = []
        self.session = None
    
    def _fetch(self, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            time.sleep(self.delay)
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8', errors='ignore')
        except HTTPError as e:
            print(f"  HTTP Error {e.code}: {url}")
            return None
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            return None
    
    def get_all_article_links(self) -> List[str]:
        """获取所有文章链接"""
        print("🔍 发现文章链接...")
        
        links = set()
        
        # 1. 从首页获取
        home = self._fetch(f"{self.BASE_URL}/")
        if home:
            home_links = re.findall(r'href="(/post/[a-f0-9]+\.html)"', home)
            links.update(home_links)
        
        # 2. 从分类页获取 (wp-crypto是writeup分类)
        for category in ['wp-crypto', '']:
            url = f"{self.BASE_URL}/categories/{category}/" if category else f"{self.BASE_URL}/categories/"
            content = self._fetch(url)
            if content:
                cat_links = re.findall(r'href="(/post/[a-f0-9]+\.html)"', content)
                links.update(cat_links)
        
        # 3. 遍历分页
        for page in range(2, 20):  # 假设最多20页
            url = f"{self.BASE_URL}/page/{page}/"
            content = self._fetch(url)
            if not content:
                break
            page_links = re.findall(r'href="(/post/[a-f0-9]+\.html)"', content)
            if not page_links:
                break
            links.update(page_links)
            print(f"  第{page}页: 发现 {len(page_links)} 篇文章")
        
        full_links = [f"{self.BASE_URL}{link}" for link in links]
        print(f"✅ 共发现 {len(full_links)} 篇文章")
        return full_links
    
    def parse_writeup(self, url: str) -> Optional[BlogWriteup]:
        """解析单篇writeup"""
        print(f"  📄 解析: {url}")
        
        html = self._fetch(url)
        if not html:
            return None
        
        try:
            # 提取标题
            title_match = re.search(r'<h1 class="post-title"[^>]*>(.*?)</h1>', html, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else "Unknown"
            
            # 提取日期
            date_match = re.search(r'<time[^>]*>(.*?)</time>', html)
            posted_date = date_match.group(1).strip() if date_match else None
            
            # 提取分类
            cat_match = re.search(r'wp-crypto|游记|研究', html)
            category = cat_match.group(0) if cat_match else "unknown"
            
            # 提取标签
            tags = re.findall(r'rel="tag">([^<]+)</a>', html)
            
            # 提取正文内容
            content_match = re.search(
                r'<div class="post-body[^"]*"[^>]*>(.*?)</div>\s*<footer',
                html,
                re.DOTALL
            )
            
            if not content_match:
                content_match = re.search(
                    r'<article[^>]*>.*?<div[^>]*>(.*?)</div>.*?</article>',
                    html,
                    re.DOTALL
                )
            
            content_html = content_match.group(1) if content_match else ""
            
            # 提取代码块
            code_snippets = self._extract_code_blocks(content_html)
            
            # 提取数学公式
            math_formulas = self._extract_math_formulas(content_html)
            
            # 提取文本内容
            content_text = re.sub(r'<[^>]+>', ' ', content_html)
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # 提取描述 (前200字符)
            description = content_text[:200]
            
            # 提取工具引用
            tools = self._extract_tools(content_text, content_html)
            
            # 提取资料引用
            resources = self._extract_resources(content_html, content_text)
            
            return BlogWriteup(
                title=title,
                url=url,
                category=category,
                tags=tags,
                description=description,
                content=content_text,
                code_snippets=code_snippets,
                math_formulas=math_formulas,
                tools=tools,
                resources=resources,
                posted_date=posted_date
            )
            
        except Exception as e:
            print(f"    ❌ 解析失败: {e}")
            return None
    
    def _extract_code_blocks(self, html: str) -> List[Dict[str, str]]:
        """提取代码块"""
        snippets = []
        
        # 匹配代码块
        code_patterns = [
            r'<pre><code class="language-([^"]*)">(.*?)</code></pre>',
            r'<pre><code>(.*?)</code></pre>',
            r'<figure class="highlight[^"]*"[^>]*>.*?<td class="code">.*?<pre>(.*?)</pre>.*?</figure>',
        ]
        
        for pattern in code_patterns:
            if 'language-' in pattern:
                matches = re.findall(pattern, html, re.DOTALL)
                for lang, code in matches:
                    code = re.sub(r'<[^>]+>', '', code)
                    code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    if len(code) > 20:
                        snippets.append({'lang': lang, 'code': code.strip()})
            else:
                matches = re.findall(pattern, html, re.DOTALL)
                for code in matches:
                    code = re.sub(r'<[^>]+>', '', code)
                    code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    if len(code) > 20:
                        snippets.append({'lang': '', 'code': code.strip()})
        
        return snippets[:10]  # 限制数量
    
    def _extract_math_formulas(self, html: str) -> List[str]:
        """提取数学公式"""
        formulas = []
        
        # LaTeX公式
        latex_patterns = [
            r'\$\$(.*?)\$\$',
            r'\\[(.*?)\\]',
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
        ]
        
        for pattern in latex_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            formulas.extend([f.strip() for f in matches if len(f.strip()) > 5])
        
        return formulas[:20]
    
    def _extract_tools(self, text: str, html: str) -> List[ToolReference]:
        """提取工具引用"""
        tools = []
        
        # 常见密码学工具
        tool_patterns = [
            (r'sage(math)?', 'SageMath'),
            (r'gp/pari', 'PARI/GP'),
            (r'magma', 'Magma'),
            (r'flatter', 'FLATTER'),
            (r'yafu', 'YAFU'),
            (r'cado', 'CADO-NFS'),
            (r'hashcat', 'Hashcat'),
            (r'pwntools', 'pwntools'),
            (r'z3', 'Z3'),
            (r'angr', 'angr'),
            (r'gdb', 'GDB'),
            (r'ida', 'IDA Pro'),
            (r'ghidra', 'Ghidra'),
            (r'openssl', 'OpenSSL'),
            (r'python[^3]', 'Python'),
            (r'gmpy2?', 'gmpy2'),
            (r'pycryptodome', 'PyCryptodome'),
            (r'owi', 'OWI'),
            (r'RsaCtfTool', 'RsaCtfTool'),
            (r'factordb', 'factordb'),
            (r'alpertron', 'Alpertron'),
        ]
        
        for pattern, tool_name in tool_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # 找到上下文
                context_match = re.search(
                    r'.{0,100}' + pattern + r'.{0,100}',
                    text,
                    re.IGNORECASE
                )
                context = context_match.group(0) if context_match else ""
                
                tools.append(ToolReference(
                    name=tool_name,
                    context=context
                ))
        
        return tools
    
    def _extract_resources(self, html: str, text: str) -> List[ResourceReference]:
        """提取资料引用"""
        resources = []
        
        # 提取链接和标题
        link_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        links = re.findall(link_pattern, html)
        
        for link, title in links:
            if len(title) > 5 and not link.startswith('/'):
                resources.append(ResourceReference(
                    title=title.strip(),
                    link=link,
                    description=f"链接: {link}",
                    resource_type="external"
                ))
        
        # 检测论文引用
        paper_patterns = [
            r'论文[《\[]([^》\]]+)[》\]]',
            r'paper[:\s]*["\']([^"\']+)["\']',
            r'arXiv[:\s]*(\d+\.\d+)',
        ]
        
        for pattern in paper_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                resources.append(ResourceReference(
                    title=match,
                    description="论文引用",
                    resource_type="paper"
                ))
        
        return resources[:10]
    
    def crawl_all(self, max_articles: Optional[int] = None):
        """爬取所有writeup"""
        print("="*60)
        print("🚀 开始爬取糖醋小鸡块博客")
        print("="*60)
        
        links = self.get_all_article_links()
        
        if max_articles:
            links = links[:max_articles]
        
        print(f"\n📥 开始解析 {len(links)} 篇文章...")
        
        for i, link in enumerate(links, 1):
            print(f"\n[{i}/{len(links)}]", end=" ")
            writeup = self.parse_writeup(link)
            if writeup:
                self.writeups.append(writeup)
                print(f"   ✅ {writeup.title[:50]}...")
                print(f"   代码片段: {len(writeup.code_snippets)} 工具: {len(writeup.tools)} 资料: {len(writeup.resources)}")
        
        print(f"\n✅ 爬取完成，共 {len(self.writeups)} 篇writeup")
    
    def save(self, output_dir: str = "data/tangcu_blog"):
        """保存数据"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 原始数据
        raw_file = output_path / "writeups_raw.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(w) for w in self.writeups], f, indent=2, ensure_ascii=False)
        print(f"\n💾 原始数据: {raw_file}")
        
        # 2. 训练数据格式
        train_file = output_path / "writeups_training.jsonl"
        with open(train_file, 'w', encoding='utf-8') as f:
            for w in self.writeups:
                example = w.to_training_example()
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        print(f"💾 训练数据: {train_file}")
        
        # 3. 工具使用数据
        tools_file = output_path / "tools_training.jsonl"
        tool_examples = []
        with open(tools_file, 'w', encoding='utf-8') as f:
            for w in self.writeups:
                examples = w.to_tools_dataset()
                for ex in examples:
                    f.write(json.dumps(ex, ensure_ascii=False) + '\n')
                    tool_examples.append(ex)
        print(f"💾 工具数据: {tools_file} ({len(tool_examples)} 条)")
        
        # 4. 提取所有工具
        all_tools = {}
        for w in self.writeups:
            for t in w.tools:
                if t.name not in all_tools:
                    all_tools[t.name] = {
                        "name": t.name,
                        "count": 0,
                        "contexts": []
                    }
                all_tools[t.name]["count"] += 1
                all_tools[t.name]["contexts"].append(t.context[:200])
        
        tools_summary = output_path / "tools_summary.json"
        with open(tools_summary, 'w', encoding='utf-8') as f:
            json.dump(all_tools, f, indent=2, ensure_ascii=False)
        print(f"💾 工具汇总: {tools_summary} ({len(all_tools)} 个工具)")
        
        # 5. 提取所有资料
        all_resources = []
        for w in self.writeups:
            all_resources.extend([asdict(r) for r in w.resources])
        
        resources_file = output_path / "resources_summary.json"
        with open(resources_file, 'w', encoding='utf-8') as f:
            json.dump(all_resources, f, indent=2, ensure_ascii=False)
        print(f"💾 资料汇总: {resources_file} ({len(all_resources)} 条)")
        
        # 6. 统计信息
        stats = {
            "total_writeups": len(self.writeups),
            "by_category": {},
            "by_tag": {},
            "code_snippets_total": sum(len(w.code_snippets) for w in self.writeups),
            "math_formulas_total": sum(len(w.math_formulas) for w in self.writeups),
            "unique_tools": len(all_tools),
            "resources_total": len(all_resources)
        }
        
        for w in self.writeups:
            stats["by_category"][w.category] = stats["by_category"].get(w.category, 0) + 1
            for tag in w.tags:
                stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1
        
        stats_file = output_path / "collection_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"💾 统计信息: {stats_file}")
        
        return stats


def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description="糖醋小鸡块博客爬虫")
    parser.add_argument("--output", "-o", default="data/tangcu_blog", help="输出目录")
    parser.add_argument("--max", "-m", type=int, help="最大文章数")
    parser.add_argument("--delay", "-d", type=float, default=0.5, help="请求间隔")
    
    args = parser.parse_args()
    
    crawler = TangcuBlogCrawler(delay=args.delay)
    crawler.crawl_all(max_articles=args.max)
    stats = crawler.save(args.output)
    
    print("\n" + "="*60)
    print("📊 爬取统计")
    print("="*60)
    print(f"Writeup数量: {stats['total_writeups']}")
    print(f"代码片段: {stats['code_snippets_total']}")
    print(f"数学公式: {stats['math_formulas_total']}")
    print(f"独特工具: {stats['unique_tools']}")
    print(f"资料链接: {stats['resources_total']}")
    print("\n分类分布:")
    for cat, count in stats['by_category'].items():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
