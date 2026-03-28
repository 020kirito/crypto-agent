# 🤖 CTF Crypto Agent

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2-green.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model](https://img.shields.io/badge/Model-LoRA%20Fine--tuned-orange.svg)]()

基于大语言模型(LLM)的智能CTF密码学解题Agent，专注于Crypto方向，支持RSA、ECC、格密码、对称加密等多种密码学攻击方法。

[English Version](#ctf-crypto-agent) | [中文文档](#目录)

---

## 📋 目录

- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [工具列表](#-工具列表)
- [使用示例](#-使用示例)
- [性能基准](#-性能基准)
- [模型微调](#-模型微调)
- [数据收集](#-数据收集)
- [部署方案](#-部署方案)
- [贡献指南](#-贡献指南)

---

## ✨ 核心特性

### 🛠️ 丰富的工具集 (50+)
- **RSA工具**: 基础加密/解密、Wiener攻击、Boneh-Durfee、共模攻击、多素数RSA
- **ECC工具**: 点加法、标量乘、Smart攻击、MOV攻击、奇异曲线攻击
- **格密码工具**: LLL/BKZ约减、Coppersmith方法、NTRU攻击、HNP求解
- **对称加密**: AES模式、Padding Oracle、Bit Flipping、LFSR分析
- **古典密码**: Caesar、Vigenère、Hill、频率分析

### 🧠 智能Agent架构
- **ReAct推理**: 基于LangChain的推理-行动循环
- **工具选择**: 自动识别题目类型并选择合适工具
- **链式调用**: 复杂攻击的多步骤组合
- **自我反思**: 失败重试、错误分析、策略调整

### 📚 高质量训练数据 (833条)
| 来源 | 数量 | 说明 |
|------|------|------|
| 本地笔记 | 498条 | 做题笔记提取 |
| 博客爬取 | 121条 | 博客 |
| 工具教程 | 216条 | 工具使用场景 |
| **总计** | **833条** | 去重后834条 |

### 🔬 外部工具集成
- **数学工具**: SageMath、PARI/GP、SymPy、gmpy2
- **格密码**: FLATTER (LLL)、fplll、BKZ
- **因式分解**: YAFU、CADO-NFS、FactorDB
- **逆向工具**: IDA Pro、Ghidra、pwndbg

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- CUDA 12.0+ (用于本地模型微调)
- 8GB+ 显存 (RTX 4060/3060等)

### 安装

```bash
# 克隆仓库
git clone https://github.com/020kirito/crypto-agent.git
cd crypto-agent

# 创建conda环境
conda create -n crypto python=3.11
conda activate crypto

# 安装依赖
pip install -r requirements.txt
```

### 配置API Key

```bash
cp .env.example .env
# 编辑 .env 文件，填入Kimi API Key
```

### 快速测试

```bash
# 测试Agent
python scripts/test_agent.py

# 批量解题
python scripts/batch_solve.py --category rsa
```

---

## 📁 项目结构

```
crypto-agent/
├── src/
│   ├── agent/                 # Agent核心
│   │   ├── crypto_agent.py    # 主Agent实现
│   │   ├── reflective_agent.py # 反思式Agent
│   │   └── data_collector.py  # 数据收集器
│   ├── tools/                 # 密码学工具 (50+)
│   │   ├── classical_tools.py
│   │   ├── crypto_tools.py
│   │   ├── rsa_advanced_tools.py
│   │   ├── ecc_tools.py
│   │   ├── lattice_advanced.py
│   │   └── ...
│   ├── crawler/               # 数据爬取
│   │   ├── writeup_crawler.py
│   │   └── blog_crawler.py
│   ├── paper_parser/          # 论文解析
│   │   └── paper_analyzer.py
│   └── challenges/            # CTF题目库
├── scripts/                   # 脚本工具
│   ├── fine_tune_unsloth_8gb.py
│   ├── batch_solve.py
│   ├── evaluate_agent.py
│   └── analyze_blog_data.py
├── data/                      # 训练数据
│   ├── training/              # 833条训练样本
│   └── tangcu_blog/           # 博客爬取数据
├── challenges/                # 20道测试题目
└── docs/                      # 文档
```

---

## 🛠️ 工具列表

### RSA攻击工具

| 工具 | 功能 | 复杂度 |
|------|------|--------|
| `rsa_basic` | 基础加密/解密 | Easy |
| `rsa_wiener_attack` | Wiener攻击 (d < n^0.25) | Hard |
| `rsa_blinding_attack` | RSA Blinding | Medium |
| `rsa_common_modulus` | 共模攻击 | Medium |
| `rsa_crt_fault` | CRT故障注入 | Expert |
| `fermat_factor` | Fermat分解 (p≈q) | Medium |
| `pollard_p1` | Pollard's p-1 | Medium |

### ECC工具

| 工具 | 功能 | 复杂度 |
|------|------|--------|
| `ecc_point_addition` | 椭圆曲线点加 | Easy |
| `ecc_scalar_mul` | 标量乘法 | Medium |
| `ecc_smart_attack` | Smart攻击 (异常曲线) | Hard |
| `ecc_mov_attack` | MOV攻击 (ECDLP规约) | Expert |

### 格密码工具

| 工具 | 功能 | 复杂度 |
|------|------|--------|
| `lattice_lll` | LLL格基约减 | Medium |
| `lattice_bkz` | BKZ约减 | Hard |
| `lattice_coppersmith` | Coppersmith方法 | Hard |
| `ntru_attack` | NTRU格攻击 | Expert |
| `hnp_solver` | 隐藏数问题 | Expert |

---

## 💻 使用示例

### 单题解题

```python
from src.agent import create_crypto_agent

# 创建Agent
agent = create_crypto_agent(model_name="moonshot-v1-32k")

# 解题
result = agent.solve(
    challenge_description="""
    RSA解密:
    n = 3233
    e = 17
    c = 2790
    求明文m
    """,
    challenge_name="rsa_basic"
)

print(f"Flag: {result['flag']}")
print(f"解题步骤: {result['steps']}")
```

### 批量解题

```bash
# 解决所有RSA题目
python scripts/batch_solve.py --category rsa --output results.json

# 按难度筛选
python scripts/batch_solve.py --difficulty easy

# 查看统计
python scripts/analyze_results.py results.json
```

### 反思式Agent

```python
from src.agent.reflective_agent import create_reflective_agent

# 创建带反思的Agent (最多重试3次)
agent = create_reflective_agent(max_retries=3)

result = agent.solve(challenge_description, "challenge_name")

print(f"成功: {result['success']}")
print(f"尝试次数: {result['total_attempts']}")
print(f"反思总结: {result['reflection_summary']}")
```

---

## 📊 性能基准

### 测试数据集

20道CTF题目，覆盖6大类别：
- RSA (5题)
- ECC (5题)
- Lattice (4题)
- Stream (2题)
- Block (2题)
- Classical (2题)

### 测试结果

| 模型 | 成功率 | 平均用时 | 备注 |
|------|--------|----------|------|
| moonshot-v1-32k (基线) | 83.3% | 35s | 10/12题 |
| **LoRA微调后** | **90%+** (预计) | **25s** | 待验证 |

### 分类表现

| 类别 | 成功率 | 最佳题目 |
|------|--------|----------|
| Classical | 100% | Vigenère Kasiski |
| ECC | 100% | 点加法、MOV攻击 |
| Lattice | 100% | HNP、NTRU |
| Stream | 100% | LFSR Berlekamp-Massey |
| Block | 100% | AES ECB字节翻转 |
| RSA | 33.3% | 需改进small_e攻击 |

详细报告: [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)

---

## 🎯 模型微调

### 8GB显存LoRA微调

```bash
# 运行微调脚本 (针对RTX 4060/3060优化)
python scripts/fine_tune_unsloth_8gb.py
```

**配置参数**:
- 基础模型: Llama-3-8B-Instruct
- 量化: 4-bit (Q4)
- LoRA Rank: 32
- Batch Size: 1 (有效batch=8)
- 优化器: AdamW 8-bit
- 序列长度: 2048
- 训练轮数: 3 epochs

**显存占用**: ~8GB (刚好适合8GB显卡)

### 训练数据

```
data/training/finetune/
├── train.jsonl      # 667条训练数据
├── val.jsonl        # 167条验证数据
└── stats.json       # 数据统计
```

### 训练后操作

```bash
# 1. 测试模型
python scripts/test_lora_model.py \
    --model outputs/ctf-crypto-lora/lora_weights \
    --interactive

# 2. 合并权重
python scripts/merge_lora.py

# 3. 导出到Ollama
python scripts/export_to_ollama.py
ollama create ctf-crypto-agent -f Modelfile.gguf
```

---

## 🌐 数据收集

### 爬取CTF Writeup

```python
from src.crawler import WriteupDatasetBuilder

builder = WriteupDatasetBuilder()
builder.crawl_all(crypto_only=True, limit_per_source=20)
builder.save()
```

支持来源:
- CTFTime (ctfwriteups)
- GitHub CTF repositories
- RSS/Atom blogs

### 爬取博客数据

成功爬取121篇Writeup:

```bash
python src/crawler/blog_crawler.py
python src/crawler/tools_extractor.py
```

**提取成果**:
- 121篇Writeup
- 1,094个代码片段
- 216条工具使用记录
- 19个密码学工具

### 解析论文攻击方法

```python
from src.paper_parser import PaperDatasetBuilder

builder = PaperDatasetBuilder()
builder.collect_from_arxiv(limit_per_query=5)
builder.generate_codes()  # 自动生成Python实现
builder.save()
```

---

## 🚀 部署方案

### 方案1: Ollama本地部署 (推荐)

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 创建模型
ollama create ctf-crypto-agent -f Modelfile

# 运行
ollama run ctf-crypto-agent
```

### 方案2: vLLM生产部署

```bash
python -m vllm.entrypoints.openai.api_server \
    --model outputs/ctf-crypto-lora/merged_model \
    --tensor-parallel-size 1 \
    --max-model-len 4096
```

### 方案3: 直接使用LoRA权重

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="outputs/ctf-crypto-lora/lora_weights",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)
```

---

## 🤝 贡献指南

欢迎提交Issue和PR！

### 添加新工具

```python
from langchain.tools import tool

@tool
def my_attack(params: str) -> str:
    """
    我的攻击方法
    
    Args:
        params: 参数说明
    
    Returns:
        攻击结果
    """
    # 实现代码
    return result
```

### 添加新题目

在 `challenges/` 目录下创建JSON文件:

```json
{
  "name": "my_challenge",
  "category": "rsa",
  "difficulty": "medium",
  "description": "题目描述...",
  "flag": "flag{...}",
  "hint": "提示信息",
  "solution_type": "attack_name"
}
```

---

## 📝 学习路径

### 核心工具 (按使用频率)

1. **SageMath** (41次) - 数论、代数、椭圆曲线
2. **gmpy2** (31次) - 高精度数学计算
3. **PARI/GP** (19次) - 数论专用
4. **FLATTER** - 高性能LLL格基约减
5. **YAFU/CADO-NFS** - 因式分解

### 推荐阅读

- [TOOL_GUIDE.md](data/tangcu_blog/TOOL_GUIDE.md) - 工具使用指南
- [FEATURES_GUIDE.md](FEATURES_GUIDE.md) - 功能使用说明
- [QUICK_START_FINE_TUNE.md](QUICK_START_FINE_TUNE.md) - 微调快速指南

