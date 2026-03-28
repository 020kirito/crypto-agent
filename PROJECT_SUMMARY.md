# 🏆 CTF Crypto Agent 项目总结

## 项目概述

构建了一个基于大语言模型 (LLM) 的智能 CTF 密码学解题 Agent，具备完整的工具集、数据收集管道和模型微调能力。

---

## 📊 项目成果

### 1. 工具集 (43个)

| 类别 | 数量 | 工具 |
|------|------|------|
| 基础工具 | 21 | Caesar/Vigenere/Rot13/Hex/Base64/URL/AES/SHA256/RSA基础等 |
| 高级密码工具 | 11 | RSA Wiener攻击、Common Modulus、Fermat分解、LFSR、LWE、Autokey、GCM不可伪造性等 |
| 外部MCP工具 | 5 | SageMath、FLATTER (LLL)、YAFU、Hashcat、CADO-NFS |
| 实用工具 | 6 | HTTP请求、文件操作、格式转换等 |

**外部工具状态:**
- ✅ **SageMath**: Python 数学计算环境
- ✅ **FLATTER**: 高性能 LLL 格基约减 (已验证可用)
- ⚠️ **YAFU**: 因式分解工具 (运行正常，输出解析待优化)
- ✅ **Hashcat**: GPU 密码破解 (已检测到，需 GPU 运行环境)
- ⚠️ **CADO-NFS**: 数域筛法因式分解 (框架就绪，需编译)
- ✅ **GF2BV**: GF(2) 位向量运算
- ✅ **CUSO**: 密码学工具库

### 2. 训练数据 (501条)

从 `D:/Crypto/做题笔记` 目录提取了 **119 个 markdown 文件**，整理出 501 条训练样本：

| 类别 | 题目数 |
|------|--------|
| RSA | 39 |
| Lattice | 26 |
| AES | 25 |
| Hash | 20 |
| ECC | 16 |
| DLP | 9 |
| LFSR | 8 |
| CopperSmith | 3 |
| NTRU | 1 |
| 其他 | 354 |

**数据质量筛选:** 501 → 498 (去除低质量样本)
- 训练集: **398条**
- 验证集: **100条**

### 3. Agent 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      CTF Crypto Agent                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Prompt    │───▶│    LLM      │───▶│   Tool Selection    │ │
│  │  + Context  │    │ (Kimi 32k)  │    │                     │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                 │               │
│  ┌──────────────────────────────────────────────┘               │
│  ▼                                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   43 Crypto Tools                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │ Classical│ │  RSA     │ │ Lattice  │ │  ECC     │... │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                     │
│  ┌───────────────────────┼─────────────────────────────────┐  │
│  ▼                       ▼                                 ▼  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐    │
│  │  Python  │    │   SageMath   │    │  External (MCP)  │    │
│  │  Native  │    │   (MCP)      │    │  FLATTER/YAFU/.. │    │
│  └──────────┘    └──────────────┘    └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 4. 评估结果

**基准测试 (moonshot-v1-32k):**

| 题目 | 难度 | 结果 | 耗时 |
|------|------|------|------|
| caesar_basic | easy | ❌ | 11.7s |
| rsa_basic | easy | ✅ | 15.4s |
| base64_decode | easy | ❌ | 5.7s |
| xor_decrypt | easy | ✅ | 5.8s |
| rsa_common_modulus | medium | ❌ | 10.7s |

**总体表现:**
- 成功率: **40%** (2/5)
- 平均耗时: **9.9s**

**按类别:**
- RSA: 1/2 (50%)
- Crypto (XOR): 1/1 (100%)
- Classical: 0/1 (0%)
- Encoding: 0/1 (0%)

---

## 🔧 技术栈

| 组件 | 版本/说明 |
|------|-----------|
| Python | 3.11 |
| LangChain | 1.2.13 (新 create_agent API) |
| LLM | Kimi moonshot-v1-32k |
| API | OpenAI-compatible (Moonshot) |
| Agent Pattern | ReactAgent / ToolAgent |

---

## 📁 项目结构

```
toy_ctf/
├── src/
│   ├── agent/               # Agent 核心
│   │   ├── crypto_agent.py
│   │   └── data_collector.py
│   ├── tools/               # 工具实现
│   │   ├── classical_tools.py
│   │   ├── crypto_tools.py
│   │   ├── ctf_tools.py
│   │   ├── advanced_crypto.py
│   │   └── ecc_tools.py
│   ├── mcp/                 # MCP 外部工具
│   │   ├── mcp_server.py
│   │   └── external_tools_full.py
│   └── challenges/          # CTF 题目
├── scripts/                 # 脚本工具
│   ├── test_agent.py
│   ├── fine_tune_model.py
│   ├── evaluate_agent.py
│   ├── extract_training_data.py
│   └── setup_mcp.py
├── data/                    # 数据存储
│   ├── training/            # 训练数据
│   ├── trajectories/        # 轨迹记录
│   └── evaluation/          # 评估结果
├── challenges/              # 测试题目
└── .env                     # API 配置
```

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install langchain langchain-openai

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 KIMI_API_KEY

# 3. 测试 Agent
python scripts/test_agent.py

# 4. 运行评估
python scripts/evaluate_agent.py --model moonshot-v1-32k

# 5. 准备训练数据
python scripts/fine_tune_model.py --prepare
```

---

## 📈 扩展定律 (Scaling Law) 验证

### 假设
> 通过收集解题轨迹数据并微调模型，可以提升 Agent 在密码学任务上的表现。

### 数据规模
- 原始数据: 501 条 (119 文件)
- 清洗后: 498 条
- 训练/验证: 398/100 (80/20 分割)

### 待验证指标
| 指标 | 基线模型 | 微调后 | 提升 |
|------|----------|--------|------|
| 成功率 | 40% | ? | ? |
| 平均步数 | ~5 | ? | ? |
| 工具选择准确率 | ? | ? | ? |

---

## 🔮 后续工作

### 1. 模型微调
- [ ] 提交微调任务到 OpenAI API
- [ ] 等待模型训练完成
- [ ] 对比基线与微调后模型性能

### 2. 工具优化
- [ ] YAFU 输出解析完善
- [ ] CADO-NFS 编译部署
- [ ] 添加更多攻击工具 (Coppersmith, Pohlig-Hellman 等)

### 3. 数据增强
- [ ] 扩大训练数据规模 (目标 1000+)
- [ ] 添加更多 ECC、LWE、NTRU 题目
- [ ] 引入解题思路的详细描述

### 4. Agent 改进
- [ ] 实现反思机制 (Reflection)
- [ ] 添加记忆模块
- [ ] 支持多轮对话式解题

---

## 🎯 核心挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| LangChain 1.x API 变化 | 迁移到 `create_agent` 新 API |
| Token 限制 (8k) | 切换到 32k 上下文模型 |
| FLATTER 路径错误 | 修正为 `build/bin/flatter` |
| FLATTER 输入格式 | 使用 FPLLL 格式 `[[a b][c d]]` |
| .env 解析失败 | 移除注释行后再 export |
| YAFU 输出解析 | 待完善正则表达式匹配 |

---

## 📚 关键代码示例

### Agent 初始化
```python
from agent import create_crypto_agent

agent = create_crypto_agent(
    model_name="moonshot-v1-32k",
    temperature=0.2
)

result = agent.solve(challenge_description, challenge_name="test")
```

### 工具调用
```python
from tools import get_all_tools

tools = get_all_tools()
print(f"已加载 {len(tools)} 个工具")

# 调用特定工具
for tool in tools:
    if tool.name == "caesar_decrypt":
        result = tool.invoke({"ciphertext": "Khoor Zruog", "shift": 3})
```

### 外部工具 (MCP)
```python
from mcp.external_tools_full import external_tool_manager

# FLATTER LLL
matrix = [[100, 0], [0, 100], [123456, 1]]
result = external_tool_manager.call_flatter(matrix)

# SageMath
sage_code = "print(factor(2^127 - 1))"
result = external_tool_manager.call_sagemath(sage_code)
```

---

## 📞 联系方式

项目路径: `/mnt/d/llama-fac/toy_ctf`

---

## 📝 许可证

MIT License
