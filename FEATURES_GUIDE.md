# 新功能使用指南

## 新增功能概览

| 功能 | 路径 | 用途 |
|------|------|------|
| CTF Writeup爬虫 | `src/crawler/` | 自动收集CTF解题报告 |
| 论文解析器 | `src/paper_parser/` | 从学术文献提取攻击方法 |
| 集成数据收集器 | `scripts/collect_training_data.py` | 统一收集所有数据源 |

---

## 功能1: CTF Writeup爬虫

### 快速开始

```bash
# 爬取CTFTime上的writeups
python -c "
from src.crawler import WriteupDatasetBuilder

builder = WriteupDatasetBuilder(output_dir='data/writeups')
builder.crawl_all(crypto_only=True, limit_per_source=10)
builder.save()
"
```

### 支持的来源

1. **CTFTime** (ctfwriteups)
2. **GitHub** CTF仓库
3. **RSS/Atom** 博客feed

### 使用示例

```python
from src.crawler import CTFTimeCrawler, GitHubCrawler

# CTFTime爬虫
ctf_time = CTFTimeCrawler()
writeups = ctf_time.search_writeups(category='crypto', limit=20)

for w in writeups:
    print(f"标题: {w.title}")
    print(f"类别: {w.category}")
    print(f"Flag: {w.flag}")
    print(f"代码片段: {len(w.code_snippets)} 个")
    
    # 转换为训练数据
    training_example = w.to_training_example()

# GitHub爬虫
github = GitHubCrawler()
repos = github.search_repos("ctf crypto writeup", limit=5)
```

### 输出格式

```json
{
  "title": "RSA Challenge Writeup",
  "source": "https://ctftime.org/writeup/12345",
  "category": "crypto",
  "description": "题目描述...",
  "solution": "解题思路...",
  "code_snippets": ["代码1", "代码2"],
  "flag": "flag{...}",
  "content_hash": "abc123..."
}
```

---

## 功能2: 论文解析器

### 快速开始

```bash
# 从arXiv搜索密码学论文
python -c "
from src.paper_parser import PaperDatasetBuilder

builder = PaperDatasetBuilder(output_dir='data/papers')
builder.collect_from_arxiv(limit_per_query=5)
builder.generate_codes()
builder.save()
"
```

### 支持的来源

1. **arXiv** (cs.CR密码学板块)
2. **PDF文件** (本地论文)

### 使用示例

```python
from src.paper_parser import ArxivParser, PDFParser, AttackCodeGenerator

# arXiv搜索
parser = ArxivParser()
methods = parser.search('lattice attack', max_results=5)

for method in methods:
    print(f"攻击名称: {method.name}")
    print(f"类型: {method.attack_type.value}")
    print(f"论文: {method.paper_title}")
    print(f"复杂度: {method.complexity}")
    
    # 生成工具代码
    tool_code = method.generate_tool_code()
    print(tool_code)

# PDF解析
pdf_parser = PDFParser()
methods = pdf_parser.parse_pdf("/path/to/paper.pdf")

# 代码生成
generator = AttackCodeGenerator()
python_code = generator.generate_python_code(method)
sagemath_code = generator.generate_sagemath_code(method)
```

### 支持的攻击类型

- `rsa`: RSA相关攻击
- `lattice`: 格密码攻击
- `ecc`: 椭圆曲线攻击
- `aes`: 对称加密攻击
- `hash`: 哈希函数攻击

### 输出格式

```python
{
  "name": "New Lattice Attack",
  "paper_title": "Faster Lattice Reduction",
  "authors": ["Author A", "Author B"],
  "year": 2024,
  "attack_type": "lattice",
  "description": "攻击描述...",
  "prerequisites": ["条件1", "条件2"],
  "complexity": {"time": "O(n^3)", "space": "O(n^2)"},
  "pseudocode": "算法伪代码",
  "python_code": "Python实现",
  "sagemath_code": "SageMath实现",
  "confidence": 0.8
}
```

---

## 功能3: 集成训练数据收集器

### 快速开始

```bash
# 收集所有来源的数据
python scripts/collect_training_data.py --all

# 仅从本地收集
python scripts/collect_training_data.py --local --source-dir D:/Crypto/做题笔记

# 仅从writeups收集
python scripts/collect_training_data.py --writeups --limit 20

# 仅从论文收集
python scripts/collect_training_data.py --papers --limit 10

# 从Agent轨迹收集
python scripts/collect_training_data.py --trajectories
```

### 数据源优先级

1. **本地Markdown** (已有498条)
2. **CTF Writeups** (新爬取)
3. **论文攻击方法** (新提取)
4. **Agent解题轨迹** (动态生成)

### 输出文件

```
data/training/
├── train_augmented.jsonl      # 训练集 (80%)
├── val_augmented.jsonl        # 验证集 (20%)
└── collection_stats.json      # 统计信息
```

---

## 完整工作流示例

### 工作流1: 扩充训练数据

```bash
# 1. 收集所有来源
python scripts/collect_training_data.py --all --limit 20

# 2. 查看统计
cat data/training/collection_stats.json

# 3. 合并到现有数据集
cat data/training/train_augmented.jsonl >> data/training/combined.jsonl

# 4. 准备微调数据
python scripts/fine_tune_model.py --prepare
```

### 工作流2: 从论文实现新攻击

```python
# 1. 搜索相关论文
from src.paper_parser import ArxivParser

parser = ArxivParser()
methods = parser.search('NTRU attack', max_results=5)

# 2. 生成代码
for method in methods:
    if method.confidence >= 0.7:
        code = method.generate_tool_code()
        
        # 3. 保存到工具目录
        with open(f"src/tools/generated_{method.name}.py", "w") as f:
            f.write(code)

# 4. 测试新工具
from src.tools.generated_new_attack import new_attack
result = new_attack.invoke({"params": "..."})
```

### 工作流3: 持续学习循环

```python
# 1. Agent解题并保存轨迹
from src.agent import create_crypto_agent

agent = create_crypto_agent()
result = agent.solve(challenge_description, "challenge_name")

# 轨迹自动保存到 data/trajectories/

# 2. 从轨迹提取训练数据
from scripts.collect_training_data import TrainingDataCollector

collector = TrainingDataCollector()
collector.collect_from_trajectories()
collector.save()

# 3. 增量微调模型
# ... 使用新增数据微调 ...
```

---

## 安装依赖

```bash
# Writeup爬虫依赖
pip install beautifulsoup4 requests feedparser

# 论文解析依赖
pip install PyPDF2

# 可选: 使用SageMath进行验证
# conda install -c conda-forge sage
```

---

## 注意事项

### 爬虫礼仪

- 设置适当的请求间隔 (`delay=1.0`)
- 遵守网站的robots.txt
- 不要短时间内大量请求
- 仅用于学习和研究目的

### 数据质量

- 论文解析置信度阈值: 0.6+
- 自动去重基于内容哈希
- 建议人工审核高价值数据

### API限制

- arXiv: 无明确限制，但建议间隔1秒
- CTFTime: 请勿频繁爬取
- GitHub API: 有rate limit，可使用token

---

## 扩展开发

### 添加新的爬虫来源

```python
from src.crawler.writeup_crawler import BaseCrawler

class MyCrawler(BaseCrawler):
    def search(self, query, limit=10):
        # 实现爬取逻辑
        writeups = []
        # ... 爬取代码 ...
        return writeups
```

### 添加新的论文源

```python
from src.paper_parser.paper_analyzer import PaperParser

class MyPaperParser(PaperParser):
    def search(self, query, max_results=10):
        # 实现搜索逻辑
        methods = []
        # ... 解析代码 ...
        return methods
```
