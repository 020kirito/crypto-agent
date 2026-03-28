# 🤖 构建完整的 Agent

本指南教你如何使用 LangChain 构建一个完整的 CTF Crypto Agent。

## 🏗️ Agent 架构

```
┌─────────────────────────────────────────┐
│           Agent Executor                 │
│  ┌───────────────────────────────────┐  │
│  │            Agent                   │  │
│  │  ┌─────────┐    ┌──────────────┐  │  │
│  │  │   LLM   │───►│  Tool Router │  │  │
│  │  └─────────┘    └──────────────┘  │  │
│  └───────────────────────────────────┘  │
│              │                           │
│              ▼                           │
│  ┌───────────────────────────────────┐  │
│  │            Tools                   │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────┐  │  │
│  │  │crypto_1 │ │crypto_2 │ │ctf_1│  │  │
│  │  └─────────┘ └─────────┘ └─────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 📝 完整代码

### 1. 基础配置

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    model_name: str = "kimi-latest"
    temperature: float = 0.7
    max_iterations: int = 50
    api_key: str = None
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("KIMI_API_KEY")
```

### 2. 创建 Agent

```python
# agent_builder.py

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

def build_agent(tools, config):
    """构建 Agent"""
    
    # 1. 创建 LLM
    llm = ChatOpenAI(
        model=config.model_name,
        api_key=config.api_key,
        base_url="https://api.moonshot.cn/v1",
        temperature=config.temperature,
    )
    
    # 2. 创建 Prompt
    system_prompt = """你是一个专业的 CTF 密码学解题专家。

你的任务：
1. 分析题目类型（RSA、AES、古典密码等）
2. 提取关键参数（n, e, c, 密文等）
3. 选择合适的工具进行解密
4. 验证结果是否符合 flag 格式

工具使用指南：
{tools}

重要提示：
- 如果一种方法失败，尝试其他方法
- flag 通常格式为 flag{{...}}
- 仔细分析工具返回的结果
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 3. 创建 Agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # 4. 创建执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=config.max_iterations,
        handle_parsing_errors=True,
    )
    
    return agent_executor
```

### 3. 任务特定 Agent

#### RSA Agent

```python
# specialized_agents.py

def create_rsa_agent(llm):
    """创建专门解决 RSA 题目的 Agent"""
    
    rsa_tools = [
        rsa_factor_small_n,
        rsa_calculate_private_key,
        rsa_decrypt,
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是 RSA 专家。

解题步骤：
1. 首先尝试分解 n 得到 p 和 q
2. 计算 phi(n) = (p-1)(q-1)
3. 计算私钥 d
4. 解密 c 得到明文

可用的分解方法：
- 小 n: 试除法
- p≈q: Fermat 分解
"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, rsa_tools, prompt)
    return AgentExecutor(agent=agent, tools=rsa_tools, verbose=True)
```

### 4. 主控制器

```python
# main_controller.py

class CryptoController:
    """CTF 解题主控制器"""
    
    def __init__(self, config):
        self.config = config
        self.llm = self._create_llm()
        
        # 创建专门的 Agents
        self.rsa_agent = create_rsa_agent(self.llm)
        self.classic_agent = create_classic_agent(self.llm)
        
        # 通用 Agent
        self.general_agent = self._create_general_agent()
    
    async def solve(self, challenge):
        """解题主入口"""
        
        # 1. 分析题目类型
        challenge_type = await self._classify_challenge(challenge)
        
        # 2. 路由到专门的 Agent
        if challenge_type == "rsa":
            return await self.rsa_agent.ainvoke({"input": challenge})
        elif challenge_type == "classic":
            return await self.classic_agent.ainvoke({"input": challenge})
        else:
            return await self.general_agent.ainvoke({"input": challenge})
    
    async def _classify_challenge(self, challenge):
        """分类题目类型"""
        prompt = f"""分析以下 CTF 题目，判断类型：

{challenge}

只输出一种类型: rsa / aes / classic / other"""
        
        response = await self.llm.ainvoke(prompt)
        return response.content.strip().lower()
```

## 🔄 执行流程

```python
# 完整使用示例

async def main():
    # 1. 配置
    config = Config()
    
    # 2. 创建控制器
    controller = CryptoController(config)
    
    # 3. 题目
    challenge = """
    题目: RSA Challenge
    n = 3233
    e = 17
    c = 2790
    """
    
    # 4. 解题
    result = await controller.solve(challenge)
    print(f"结果: {result['output']}")

# 运行
import asyncio
asyncio.run(main())
```

## 🎯 高级技巧

### 1. 添加记忆

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,  # 添加记忆
    verbose=True
)
```

### 2. 回调函数

```python
from langchain.callbacks.base import BaseCallbackHandler

class LoggingCallback(BaseCallbackHandler):
    """自定义回调，记录 Agent 行为"""
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"🔧 调用工具: {serialized['name']}")
    
    def on_tool_end(self, output, **kwargs):
        print(f"📤 工具返回: {output}")

# 使用回调
result = agent_executor.invoke(
    {"input": "..."},
    callbacks=[LoggingCallback()]
)
```

### 3. 并行执行

```python
async def solve_multiple(challenges):
    """并行解决多个题目"""
    tasks = [controller.solve(c) for c in challenges]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## 📊 调试技巧

### 1. 启用详细日志

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 打印详细执行过程
    max_iterations=50,
)
```

### 2. 查看 Tool 调用

```python
# 在 Tool 中添加日志
@tool
def my_tool(x: str) -> str:
    """My tool"""
    print(f"[DEBUG] Tool called with: {x}")  # 调试输出
    result = process(x)
    print(f"[DEBUG] Tool result: {result}")
    return result
```

### 3. 保存执行轨迹

```python
class TrajectorySaver:
    def __init__(self):
        self.steps = []
    
    def add_step(self, thought, action, observation):
        self.steps.append({
            "thought": thought,
            "action": action,
            "observation": observation
        })
    
    def save(self, filepath):
        import json
        with open(filepath, "w") as f:
            json.dump(self.steps, f, indent=2)
```

## 🚀 下一步

- [数据收集与 Scaling](scaling_data.md)
- 添加更多专业 Tools
- 实现 Agent 协作
