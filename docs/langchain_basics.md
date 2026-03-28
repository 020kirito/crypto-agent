# 🦜 LangChain 基础入门

本指南为初学者介绍 LangChain 的核心概念，帮助你快速上手。

## 📚 什么是 LangChain?

LangChain 是一个用于开发大语言模型 (LLM) 应用的框架。它提供了：

- **Components (组件)**: 可复用的模块
- **Chains (链)**: 组合多个组件的流水线
- **Agents (代理)**: 让 LLM 决定使用哪些工具
- **Memory (记忆)**: 保存对话历史

## 🔑 核心概念

### 1. Model (模型)

LangChain 支持多种 LLM：

```python
from langchain_openai import ChatOpenAI

# 创建模型
llm = ChatOpenAI(
    model="gpt-4",
    api_key="your-key"
)

# 调用模型
response = llm.invoke("你好!")
print(response.content)
```

### 2. Prompt (提示词)

Prompt 是告诉 LLM 做什么的指令：

```python
from langchain_core.prompts import ChatPromptTemplate

# 创建 Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 {role}"),
    ("human", "请帮我 {task}")
])

# 填充模板
messages = prompt.format_messages(
    role="密码学专家",
    task="解密凯撒密码 Khoor"
)
```

### 3. Tools (工具)

工具是让 LLM 可以执行外部函数的方式：

```python
from langchain.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

# 使用工具
result = add.invoke({"a": 2, "b": 3})
print(result)  # 5
```

### 4. Agent (代理)

Agent 是 LangChain 最强大的功能之一，它让 LLM 自主决定：
- **是否**使用工具
- 使用**哪个**工具
- 如何**组合**多个工具

```python
from langchain.agents import create_openai_tools_agent, AgentExecutor

# 创建 Agent
agent = create_openai_tools_agent(llm, tools, prompt)

# 创建执行器
agent_executor = AgentExecutor(agent=agent, tools=tools)

# 运行
result = agent_executor.invoke({"input": "计算 2+3 然后乘以 4"})
```

## 🏗️ 工作流程

```
用户输入
    ↓
Prompt 模板
    ↓
LLM 思考
    ↓
决定调用工具? ──否──→ 直接回答
    ↓ 是
执行工具
    ↓
返回结果给 LLM
    ↓
继续思考或给出最终答案
```

## 📝 完整示例

```python
# 1. 导入
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 2. 定义工具
@tool
def caesar_decrypt(cipher: str, shift: int) -> str:
    """解密凯撒密码"""
    result = ""
    for c in cipher:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result += chr((ord(c) - base - shift) % 26 + base)
        else:
            result += c
    return result

# 3. 创建模型
llm = ChatOpenAI(model="gpt-4")

# 4. 创建 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个密码学专家，帮助解密信息"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 5. 创建 Agent
tools = [caesar_decrypt]
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. 运行
result = agent_executor.invoke({
    "input": "密文是 Khoor，看起来是凯撒密码，请解密",
    "chat_history": []
})

print(result["output"])
```

## 🎯 关键要点

1. **@tool 装饰器**: 将函数转换为 LangChain Tool
2. **文档字符串**: LLM 通过文档字符串了解工具功能
3. **类型注解**: 帮助 LLM 正确传递参数
4. **AgentExecutor**: 管理 Agent 的执行循环

## 📖 下一步

- [创建第一个 Tool](create_tool.md)
- [构建完整 Agent](build_agent.md)
- [数据收集与 Scaling](scaling_data.md)
