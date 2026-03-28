"""
CTF Writeup爬虫

自动从以下来源爬取CTF解题报告:
- CTFTime (ctfwriteups)
- GitHub CTF repositories
- 个人博客 (RSS/Atom)
- CTF Wiki

功能:
- 自动爬取writeup内容
- 提取题目描述、解题思路、flag
- 转换为训练数据格式
- 去重和清洗
"""

import re
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import tempfile


@dataclass
class Writeup:
    """Writeup数据结构"""
    title: str
    source: str  # 来源URL
    challenge_name: Optional[str] = None
    category: Optional[str] = None  # crypto, web, pwn, etc.
    difficulty: Optional[str] = None
    tags: List[str] = None
    description: str = ""
    solution: str = ""  # 解题思路
    code_snippets: List[str] = None  # 代码片段
    flag: Optional[str] = None
    author: Optional[str] = None
    ctf_name: Optional[str] = None  # CTF比赛名称
    posted_date: Optional[str] = None
    content_hash: str = ""  # 用于去重
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.code_snippets is None:
            self.code_snippets = []
        # 计算内容哈希用于去重
        content = f"{self.title}{self.description}{self.solution}"
        self.content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_training_example(self) -> Dict[str, Any]:
        """转换为训练数据格式"""
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a CTF crypto expert. Analyze the challenge and provide step-by-step solution."
                },
                {
                    "role": "user",
                    "content": f"【{self.category or 'CTF'} Challenge】\n{self.description}"
                },
                {
                    "role": "assistant",
                    "content": f"解题思路：\n{self.solution}\n\nFlag: {self.flag or '未提供'}"
                }
            ],
            "metadata": {
                "source": self.source,
                "category": self.category,
                "ctf_name": self.ctf_name,
                "content_hash": self.content_hash
            }
        }


class BaseCrawler:
    """爬虫基类"""
    
    def __init__(self, delay: float = 1.0, timeout: int = 30):
        self.delay = delay  # 请求间隔
        self.timeout = timeout
        self.session = None
    
    def _get_session(self):
        """获取HTTP会话"""
        if self.session is None:
            try:
                import requests
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry
                
                self.session = requests.Session()
                retry = Retry(total=3, backoff_factor=1)
                adapter = HTTPAdapter(max_retries=retry)
                self.session.mount('http://', adapter)
                self.session.mount('https://', adapter)
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
            except ImportError:
                print("⚠️  requests未安装，使用urllib")
                return None
        return self.session
    
    def fetch(self, url: str) -> Optional[str]:
        """获取页面内容"""
        session = self._get_session()
        if session:
            try:
                time.sleep(self.delay)
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"❌ 请求失败 {url}: {e}")
                return None
        else:
            # 使用urllib作为备选
            try:
                from urllib.request import urlopen, Request
                time.sleep(self.delay)
                req = Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                with urlopen(req, timeout=self.timeout) as response:
                    return response.read().decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"❌ 请求失败 {url}: {e}")
                return None


class CTFTimeCrawler(BaseCrawler):
    """CTFTime Writeup爬虫"""
    
    BASE_URL = "https://ctftime.org"
    
    def search_writeups(self, category: str = "crypto", limit: int = 10) -> List[Writeup]:
        """
        搜索CTFTime上的writeup
        
        Args:
            category: 题目类别 (crypto, web, pwn, reverse, misc)
            limit: 最大数量
        """
        writeups = []
        
        # CTFTime writeups页面
        url = f"{self.BASE_URL}/writeups"
        print(f"🔍 搜索CTFTime: {url}")
        
        html = self.fetch(url)
        if not html:
            return writeups
        
        # 解析writeup列表
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找writeup链接
            writeup_links = []
            for link in soup.find_all('a', href=re.compile(r'/writeup/\d+')):
                href = link.get('href')
                if href:
                    full_url = urljoin(self.BASE_URL, href)
                    writeup_links.append(full_url)
            
            print(f"📄 找到 {len(writeup_links)} 个writeup链接")
            
            # 爬取每个writeup
            for i, writeup_url in enumerate(writeup_links[:limit]):
                print(f"  [{i+1}/{min(len(writeup_links), limit)}] {writeup_url}")
                writeup = self._parse_writeup(writeup_url)
                if writeup:
                    writeups.append(writeup)
                    
        except ImportError:
            print("⚠️  需要安装beautifulsoup4: pip install beautifulsoup4")
        except Exception as e:
            print(f"❌ 解析失败: {e}")
        
        return writeups
    
    def _parse_writeup(self, url: str) -> Optional[Writeup]:
        """解析单个writeup页面"""
        html = self.fetch(url)
        if not html:
            return None
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取标题
            title_tag = soup.find('h1') or soup.find('h2')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # 提取内容
            content_div = soup.find('div', class_='writeup')
            if not content_div:
                content_div = soup.find('article') or soup.find('main')
            
            content = content_div.get_text(separator='\n', strip=True) if content_div else ""
            
            # 提取代码片段
            code_snippets = []
            for code in soup.find_all(['code', 'pre']):
                code_text = code.get_text(strip=True)
                if len(code_text) > 20:  # 过滤短片段
                    code_snippets.append(code_text)
            
            # 尝试提取flag
            flag = self._extract_flag(content)
            
            # 尝试识别类别
            category = self._detect_category(content, title)
            
            return Writeup(
                title=title,
                source=url,
                description=content[:1000],  # 截断
                solution=content,
                code_snippets=code_snippets[:5],
                flag=flag,
                category=category
            )
            
        except Exception as e:
            print(f"❌ 解析writeup失败 {url}: {e}")
            return None
    
    def _extract_flag(self, content: str) -> Optional[str]:
        """从内容中提取flag"""
        # 常见flag格式
        patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _detect_category(self, content: str, title: str) -> Optional[str]:
        """检测题目类别"""
        text = (content + title).lower()
        
        keywords = {
            'crypto': ['crypto', 'cipher', 'rsa', 'aes', 'encrypt', '解密', '密码'],
            'web': ['web', 'xss', 'sql', 'injection', 'http'],
            'pwn': ['pwn', 'exploit', 'buffer', 'overflow', 'shell'],
            'reverse': ['reverse', '逆向', 'ida', 'ghidra', 'binary'],
            'misc': ['misc', 'forensics', '隐写', 'steganography']
        }
        
        for cat, words in keywords.items():
            if any(word in text for word in words):
                return cat
        
        return None


class GitHubCrawler(BaseCrawler):
    """GitHub CTF仓库爬虫"""
    
    def search_repos(self, query: str = "ctf writeup crypto", limit: int = 5) -> List[Writeup]:
        """
        搜索GitHub上的CTF仓库
        
        Args:
            query: 搜索关键词
            limit: 最大仓库数
        """
        writeups = []
        
        # GitHub API搜索
        api_url = f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}&sort=updated&order=desc"
        
        print(f"🔍 搜索GitHub: {query}")
        
        session = self._get_session()
        if not session:
            return writeups
        
        try:
            response = session.get(api_url, timeout=self.timeout)
            data = response.json()
            
            repos = data.get('items', [])[:limit]
            print(f"📦 找到 {len(repos)} 个仓库")
            
            for i, repo in enumerate(repos):
                repo_name = repo['full_name']
                print(f"  [{i+1}/{len(repos)}] {repo_name}")
                
                # 获取README内容
                readme_url = f"https://raw.githubusercontent.com/{repo_name}/main/README.md"
                readme = self.fetch(readme_url)
                
                if readme:
                    writeup = self._parse_readme(readme, repo)
                    if writeup:
                        writeups.append(writeup)
                        
        except Exception as e:
            print(f"❌ GitHub API错误: {e}")
        
        return writeups
    
    def _parse_readme(self, readme: str, repo: Dict) -> Writeup:
        """解析README内容"""
        # 提取标题
        title = repo.get('name', 'Unknown')
        
        # 提取描述
        description = repo.get('description', '')
        
        # 提取代码块
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', readme, re.DOTALL)
        
        return Writeup(
            title=title,
            source=repo.get('html_url', ''),
            description=description or readme[:500],
            solution=readme,
            code_snippets=code_blocks[:10],
            category='crypto' if 'crypto' in readme.lower() else None
        )


class RSSCrawler(BaseCrawler):
    """RSS/Atom博客爬虫"""
    
    COMMON_BLOGS = [
        "https://ctftime.org/writeups/rss",  # CTFTime RSS
        # 可以添加更多CTF博客的RSS
    ]
    
    def crawl_feeds(self, feeds: List[str] = None, limit: int = 20) -> List[Writeup]:
        """
        爬取RSS/Atom feed
        
        Args:
            feeds: RSS feed URL列表
            limit: 每feed最大条目数
        """
        if feeds is None:
            feeds = self.COMMON_BLOGS
        
        writeups = []
        
        for feed_url in feeds:
            print(f"📡 爬取RSS: {feed_url}")
            
            try:
                import feedparser
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit]:
                    writeup = self._parse_entry(entry)
                    if writeup:
                        writeups.append(writeup)
                        
            except ImportError:
                print("⚠️  需要安装feedparser: pip install feedparser")
                break
            except Exception as e:
                print(f"❌ RSS解析失败: {e}")
        
        return writeups
    
    def _parse_entry(self, entry) -> Optional[Writeup]:
        """解析RSS条目"""
        try:
            title = entry.get('title', 'Unknown')
            link = entry.get('link', '')
            content = entry.get('summary', entry.get('description', ''))
            
            # 获取完整内容
            if link:
                full_content = self.fetch(link)
                if full_content:
                    content = full_content
            
            return Writeup(
                title=title,
                source=link,
                description=content[:1000],
                solution=content,
                posted_date=entry.get('published', ''),
                author=entry.get('author', '')
            )
        except Exception as e:
            print(f"❌ 解析条目失败: {e}")
            return None


class WriteupDatasetBuilder:
    """Writeup数据集构建器"""
    
    def __init__(self, output_dir: str = "data/writeups"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.writeups: List[Writeup] = []
        self.seen_hashes: set = set()
    
    def add_writeup(self, writeup: Writeup) -> bool:
        """添加writeup（自动去重）"""
        if writeup.content_hash in self.seen_hashes:
            print(f"  ⚠️  重复内容，跳过: {writeup.title[:50]}")
            return False
        
        self.seen_hashes.add(writeup.content_hash)
        self.writeups.append(writeup)
        return True
    
    def crawl_all(self, crypto_only: bool = True, limit_per_source: int = 10):
        """爬取所有来源"""
        print("="*60)
        print("🚀 开始爬取CTF Writeups")
        print("="*60)
        
        # 1. CTFTime
        print("\n📍 来源1: CTFTime")
        ctf_time = CTFTimeCrawler()
        for writeup in ctf_time.search_writeups(category="crypto", limit=limit_per_source):
            if not crypto_only or writeup.category == 'crypto':
                self.add_writeup(writeup)
        
        # 2. GitHub
        print("\n📍 来源2: GitHub")
        github = GitHubCrawler()
        for writeup in github.search_repos("ctf writeup crypto", limit=limit_per_source//2):
            self.add_writeup(writeup)
        
        # 3. RSS Feeds
        print("\n📍 来源3: RSS Feeds")
        rss = RSSCrawler()
        for writeup in rss.crawl_feeds(limit=limit_per_source):
            if not crypto_only or writeup.category == 'crypto':
                self.add_writeup(writeup)
        
        print(f"\n✅ 爬取完成，共 {len(self.writeups)} 条writeup")
    
    def save(self):
        """保存数据集"""
        # 保存原始writeups
        raw_file = self.output_dir / "writeups_raw.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(w) for w in self.writeups], f, indent=2, ensure_ascii=False)
        print(f"💾 原始数据已保存: {raw_file}")
        
        # 保存训练数据格式
        training_file = self.output_dir / "writeups_training.jsonl"
        with open(training_file, 'w', encoding='utf-8') as f:
            for writeup in self.writeups:
                example = writeup.to_training_example()
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        print(f"💾 训练数据已保存: {training_file}")
        
        # 保存统计信息
        stats = {
            "total_writeups": len(self.writeups),
            "by_category": {},
            "by_source": {}
        }
        for w in self.writeups:
            cat = w.category or 'unknown'
            src = urlparse(w.source).netloc
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
        
        stats_file = self.output_dir / "writeups_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"💾 统计信息已保存: {stats_file}")


def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description="CTF Writeup爬虫")
    parser.add_argument("--output", "-o", default="data/writeups", help="输出目录")
    parser.add_argument("--limit", "-l", type=int, default=10, help="每来源最大数量")
    parser.add_argument("--all", action="store_true", help="爬取所有类别")
    
    args = parser.parse_args()
    
    builder = WriteupDatasetBuilder(output_dir=args.output)
    builder.crawl_all(crypto_only=not args.all, limit_per_source=args.limit)
    builder.save()


if __name__ == "__main__":
    main()
