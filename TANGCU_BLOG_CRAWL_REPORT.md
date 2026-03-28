# 糖醋小鸡块博客爬取报告

**博客URL**: https://tangcuxiaojikuai.xyz/  
**爬取时间**: 2026-03-28  
**Writeup数量**: 121 篇

---

## 📊 数据概览

### 基础统计

| 指标 | 数值 |
|------|------|
| Writeup总数 | 121 篇 |
| Crypto类别 | 111 篇 (91.7%) |
| 代码片段 | 1,094 个 |
| 资源链接 | 372 条 |
| 独特工具 | 19 个 |
| 工具使用记录 | 216 条 |

### 内容分类

| 分类 | 数量 | 占比 |
|------|------|------|
| wp-crypto | 111 | 91.7% |
| 研究 | 4 | 3.3% |
| 游记 | 3 | 2.5% |
| other | 3 | 2.5% |

---

## 🛠️ 工具使用分析

### 最常用工具 TOP 15

| 排名 | 工具 | 使用次数 | 类别 |
|------|------|----------|------|
| 1 | RSA相关工具 | 44 | rsa |
| 2 | SageMath | 41 | math |
| 3 | gmpy2 | 31 | python |
| 4 | PARI/GP | 19 | math |
| 5 | SymPy | 17 | python |
| 6 | BKZ | 9 | lattice |
| 7 | IDA Pro | 9 | reverse |
| 8 | Boneh-Durfee | 8 | rsa |
| 9 | FactorDB | 8 | factoring |
| 10 | Wiener Attack | 7 | rsa |
| 11 | Z3 | 7 | python |
| 12 | CADO-NFS | 3 | factoring |
| 13 | pwntools | 3 | python |
| 14 | YAFU | 2 | factoring |
| 15 | FLATTER | 2 | lattice |

### 工具类别分布

| 类别 | 使用次数 | 说明 |
|------|----------|------|
| Python库 | 62 | gmpy2, SymPy, Z3, pwntools |
| 数学工具 | 60 | SageMath, PARI/GP |
| RSA工具 | 59 | RSA攻击相关 |
| 因式分解 | 13 | FactorDB, CADO-NFS, YAFU |
| 格密码 | 12 | BKZ, FLATTER, fplll |
| 逆向工具 | 9 | IDA Pro |

---

## 📁 生成文件清单

### 原始数据

| 文件 | 大小 | 说明 |
|------|------|------|
| `writeups_raw.json` | 7.5 MB | 121篇writeup原始数据 |
| `writeups_training.jsonl` | 521 KB | OpenAI训练格式 |

### 工具和资源提取

| 文件 | 大小 | 说明 |
|------|------|------|
| `extracted_tools.json` | 175 KB | 216条工具使用记录 |
| `extracted_resources.json` | 11 KB | 53条资源链接 |
| `extracted_code.json` | 152 KB | 188个代码片段 |
| `tools_summary.json` | 74 KB | 13个工具汇总 |
| `resources_summary.json` | 95 KB | 372条资料链接 |

### 分析和知识库

| 文件 | 大小 | 说明 |
|------|------|------|
| `analysis_report.json` | 1.8 KB | 数据分析报告 |
| `tool_guides.json` | 30 KB | 7个类别工具指南 |
| `tool_knowledge_base.json` | 49 KB | 19个工具知识库 |
| **TOOL_GUIDE.md** | 23 KB | **Markdown格式工具指南** |

### 训练数据

| 文件 | 大小 | 说明 |
|------|------|------|
| `training_tools.jsonl` | 217 KB | 工具使用训练数据 |
| `tools_training.jsonl` | 193 KB | 工具训练数据(旧版) |

---

## 📚 核心内容亮点

### 1. RSA攻击方法
- Wiener攻击
- Boneh-Durfee攻击
- 多素数RSA
- 共模攻击
- Blinding攻击

### 2. 格密码攻击
- LLL/BKZ格基约减
- Coppersmith方法
- HNP (Hidden Number Problem)
- NTRU攻击

### 3. 因式分解工具
- FactorDB在线分解
- CADO-NFS数域筛
- YAFU本地分解
- Alpertron ECM

### 4. 数学计算工具
- SageMath (Python数学系统)
- PARI/GP (数论计算)
- SymPy (符号计算)
- gmpy2 (高精度计算)

---

## 🎯 训练数据用途

### 1. 增强Agent工具使用能力
```python
# 使用 tool_knowledge_base.json
# 训练Agent如何使用各种密码学工具
```

### 2. 扩展攻击方法库
```python
# 从 writeups_raw.json 提取攻击方法
# 转换为Agent可用的工具
```

### 3. 生成代码示例
```python
# 从 extracted_code.json 获取代码片段
# 作为Agent生成代码的参考
```

### 4. 构建知识图谱
```python
# 结合 tools_summary.json 和 resources_summary.json
# 构建密码学工具知识图谱
```

---

## 🚀 快速使用

### 查看工具指南
```bash
cat data/tangcu_blog/TOOL_GUIDE.md
```

### 加载训练数据
```python
import json

# 加载writeup训练数据
with open('data/tangcu_blog/writeups_training.jsonl') as f:
    examples = [json.loads(line) for line in f]

# 加载工具使用数据
with open('data/tangcu_blog/training_tools.jsonl') as f:
    tool_examples = [json.loads(line) for line in f]
```

### 分析工具使用
```python
import json

with open('data/tangcu_blog/extracted_tools.json') as f:
    tools = json.load(f)

# 筛选特定工具
sage_tools = [t for t in tools if t['name'] == 'SageMath']
```

---

## 📈 与其他数据集的对比

| 数据集 | 数量 | 来源 | 特点 |
|--------|------|------|------|
| 本地Markdown | 501条 | D:/Crypto/做题笔记 | 详细解题过程 |
| **糖醋小鸡块博客** | **121篇** | **在线爬取** | **实战CTF经验，丰富代码** |
| CTF Writeups | 待爬取 | CTFTime/GitHub | 多样化来源 |
| 论文攻击方法 | 待提取 | arXiv | 理论深度 |

**总计**: 121篇高质量writeup + 1,094个代码片段 + 19个工具的216条使用记录

---

## 🔄 持续更新

要更新数据，运行:

```bash
# 爬取最新writeup
python src/crawler/blog_crawler.py --output data/tangcu_blog

# 提取工具和资源
python src/crawler/tools_extractor.py

# 生成分析报告
python scripts/analyze_blog_data.py --kb
```

---

## ✨ 特别感谢

感谢 **糖醋小鸡块** 师傅分享的高质量CTF Crypto Writeup！

博客: https://tangcuxiaojikuai.xyz/

---

## 📞 数据来源

- **博客地址**: https://tangcuxiaojikuai.xyz/
- **爬取工具**: `src/crawler/blog_crawler.py`
- **数据目录**: `data/tangcu_blog/`
- **生成时间**: 2026-03-28
