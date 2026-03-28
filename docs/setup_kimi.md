# 🌙 LangChain + Kimi 配置指南

LangChain 完全支持 Kimi！Kimi 提供 OpenAI 兼容的 API，可以直接使用。

## ✅ 支持的模型

| 模型名 | 说明 |
|--------|------|
| `moonshot-v1-8k` | 8K 上下文 |
| `moonshot-v1-32k` | 32K 上下文 |
| `moonshot-v1-128k` | 128K 上下文 |
| `kimi-latest` | 最新版本 |

## 🔑 配置步骤

### 1. 获取 API Key

1. 访问 https://platform.moonshot.cn/
2. 注册/登录账号
3. 创建 API Key
4. 复制 Key (以 `sk-` 开头)

### 2. 设置环境变量

```bash
# Linux/Mac
export KIMI_API_KEY="sk-your-key-here"

# Windows CMD
set KIMI_API_KEY=sk-your-key-here

# Windows PowerShell
$env:KIMI_API_KEY="sk-your-key-here"
```

### 3. 运行 Agent

```bash
# 使用默认 Kimi 模型
python scripts/run_agent.py

# 指定 Kimi 模型
python scripts/run_agent.py --model moonshot-v1-8k

# 使用 .env 文件
echo "KIMI_API_KEY=sk-your-key" > .env
python scripts/run_agent.py
```

## 📝 代码示例

```python
from langchain_openai import ChatOpenAI

# 创建 Kimi LLM
llm = ChatOpenAI(
    model="moonshot-v1-8k",           # Kimi 模型
    api_key="sk-your-key",            # Kimi API Key
    base_url="https://api.moonshot.cn/v1",  # Kimi API 地址
    temperature=0.7,
)

# 使用
response = llm.invoke("你好!")
print(response.content)
```

## 🔧 项目配置

### .env 文件

```bash
# 选择使用 Kimi
KIMI_API_KEY=sk-your-api-key
DEFAULT_MODEL=kimi

# 或使用 OpenAI
# OPENAI_API_KEY=sk-your-key
```

### config.yaml

```yaml
llm:
  provider: "kimi"  # kimi 或 openai
  model: "moonshot-v1-8k"
  temperature: 0.7
```

## ❓ 常见问题

### Q: 报错 "Module not found: langchain_openai"?

```bash
pip install langchain-openai
```

### Q: 报错 "Authentication Error"?

- 检查 API Key 是否正确
- 检查 Key 是否有余额
- 确保 Key 没有过期

### Q: 想同时使用多个模型?

```python
# Kimi
kimi = ChatOpenAI(
    model="moonshot-v1-8k",
    api_key=os.getenv("KIMI_API_KEY"),
    base_url="https://api.moonshot.cn/v1"
)

# OpenAI
gpt = ChatOpenAI(
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
)

# DeepSeek
deepseek = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)
```

## 🎯 推荐配置

对于 CTF 题目，推荐使用：

```bash
# 简单题目 (省钱)
python scripts/run_agent.py --model moonshot-v1-8k

# 复杂题目 (效果好)
python scripts/run_agent.py --model moonshot-v1-32k
```

## 📚 其他兼容的国产模型

| 厂商 | base_url | 模型名 |
|------|----------|--------|
| Kimi | `https://api.moonshot.cn/v1` | moonshot-v1-8k |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| GLM | `https://open.bigmodel.cn/api/paas/v4` | glm-4 |
| Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-turbo |

LangChain 的 `ChatOpenAI` 类支持所有兼容 OpenAI API 格式的模型！
