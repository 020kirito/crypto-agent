# 📊 数据收集与 Scaling

本指南教你收集 Agent 解题轨迹，准备训练数据，实现 Scaling Law。

## 🎯 什么是 Scaling Law?

**Scaling Law** 指模型性能随数据量、模型规模增加而提升的规律。

对于 CTF Agent:
- **数据 Scaling**: 收集更多解题轨迹
- **模型 Scaling**: 微调更大的模型
- **工具 Scaling**: 增加更多专业工具

```
数据量 ↑  →  模型能力 ↑  →  解题成功率 ↑
```

## 📦 数据结构

### 1. 单次解题轨迹

```json
{
  "id": "abc123",
  "challenge": {
    "name": "rsa_basic",
    "type": "rsa",
    "description": "n=3233, e=17, c=2790",
    "difficulty": "easy"
  },
  "result": {
    "success": true,
    "flag": "flag{123}",
    "elapsed_time": 15.3
  },
  "steps": [
    {
      "step": 1,
      "thought": "看起来是 RSA 题目，需要分解 n",
      "action": "call_tool:rsa_factor_small_n",
      "observation": "分解成功! n = 61 * 53",
      "timestamp": "2024-01-01T10:00:00"
    },
    {
      "step": 2,
      "thought": "现在计算私钥 d",
      "action": "call_tool:rsa_calculate_private_key",
      "observation": "d = 2753",
      "timestamp": "2024-01-01T10:00:05"
    }
  ],
  "metadata": {
    "model": "kimi-latest",
    "temperature": 0.7,
    "tools_used": ["rsa_factor_small_n", "rsa_calculate_private_key"]
  }
}
```

### 2. 训练数据格式

#### OpenAI 格式

```jsonl
{"messages": [
  {"role": "system", "content": "你是 CTF 专家"},
  {"role": "user", "content": "题目: n=3233, e=17, c=2790"},
  {"role": "assistant", "content": "思考: 这是 RSA 题目...\n行动: 分解 n"},
  {"role": "tool", "content": "n = 61 * 53"},
  {"role": "assistant", "content": "思考: 计算 d...\n行动: 计算私钥"},
  {"role": "assistant", "content": "FINAL ANSWER: flag{123}"}
]}
```

## 🛠️ 实现数据收集

### 1. 轨迹收集器

```python
# data/collector.py

import json
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class Step:
    step: int
    thought: str
    action: str
    observation: str
    timestamp: str

@dataclass
class Trajectory:
    id: str
    challenge_name: str
    challenge_type: str
    steps: List[Step]
    success: bool
    flag: str = None
    elapsed_time: float = 0.0

class TrajectoryCollector:
    """解题轨迹收集器"""
    
    def __init__(self, save_dir: str = "data/trajectories"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.current: Trajectory = None
    
    def start(self, challenge: Dict[str, Any]):
        """开始收集"""
        self.current = Trajectory(
            id=str(uuid.uuid4())[:8],
            challenge_name=challenge.get("name", "unknown"),
            challenge_type=challenge.get("type", "unknown"),
            steps=[],
            success=False
        )
    
    def add_step(self, thought: str, action: str, observation: str):
        """添加步骤"""
        step = Step(
            step=len(self.current.steps) + 1,
            thought=thought,
            action=action,
            observation=str(observation)[:1000],  # 限制长度
            timestamp=datetime.now().isoformat()
        )
        self.current.steps.append(step)
    
    def finish(self, success: bool, flag: str = None, elapsed: float = 0):
        """完成收集"""
        self.current.success = success
        self.current.flag = flag
        self.current.elapsed_time = elapsed
        
        # 保存
        filepath = self.save_dir / f"{self.current.challenge_name}_{self.current.id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(self.current), f, ensure_ascii=False, indent=2)
        
        return filepath
```

### 2. 集成到 Agent

```python
# agent.py

class CryptoAgent:
    def __init__(self):
        self.collector = TrajectoryCollector()
        # ... 其他初始化
    
    async def solve(self, challenge: dict) -> dict:
        # 开始收集
        self.collector.start(challenge)
        start_time = time.time()
        
        try:
            # 解题过程
            result = await self._run_agent(challenge)
            
            # 完成收集
            elapsed = time.time() - start_time
            self.collector.finish(
                success=result.get("success"),
                flag=result.get("flag"),
                elapsed=elapsed
            )
            
            return result
            
        except Exception as e:
            self.collector.finish(success=False)
            raise
```

### 3. LangChain 回调收集

```python
# callbacks.py

from langchain.callbacks.base import BaseCallbackHandler

class TrajectoryCallback(BaseCallbackHandler):
    """通过回调收集轨迹"""
    
    def __init__(self, collector):
        self.collector = collector
        self.current_thought = ""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM 开始思考"""
        self.current_thought = prompts[0] if prompts else ""
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """开始调用工具"""
        self.current_action = f"{serialized['name']}({input_str})"
    
    def on_tool_end(self, output, **kwargs):
        """工具调用结束"""
        self.collector.add_step(
            thought=self.current_thought,
            action=self.current_action,
            observation=str(output)
        )

# 使用
collector = TrajectoryCollector()
callback = TrajectoryCallback(collector)

result = agent_executor.invoke(
    {"input": "..."},
    callbacks=[callback]
)
```

## 📈 数据分析

### 1. 统计成功率

```python
# analysis/basic_stats.py

import json
from pathlib import Path
from collections import defaultdict

def analyze_trajectories(data_dir: str = "data/trajectories"):
    """分析轨迹数据"""
    
    trajectories = []
    for file in Path(data_dir).glob("*.json"):
        with open(file) as f:
            trajectories.append(json.load(f))
    
    # 基础统计
    total = len(trajectories)
    success = sum(1 for t in trajectories if t["success"])
    
    # 按类型统计
    by_type = defaultdict(lambda: {"total": 0, "success": 0})
    for t in trajectories:
        t_type = t["challenge_type"]
        by_type[t_type]["total"] += 1
        if t["success"]:
            by_type[t_type]["success"] += 1
    
    print(f"总题目数: {total}")
    print(f"成功率: {success/total:.1%}")
    print("\n按类型统计:")
    for t_type, stats in by_type.items():
        rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
        print(f"  {t_type}: {stats['success']}/{stats['total']} ({rate:.1%})")
```

### 2. 工具使用分析

```python
def analyze_tool_usage(trajectories):
    """分析工具使用频率"""
    from collections import Counter
    
    tool_counter = Counter()
    
    for t in trajectories:
        for step in t["steps"]:
            action = step["action"]
            if action.startswith("call_tool:"):
                tool_name = action.replace("call_tool:", "").split("(")[0]
                tool_counter[tool_name] += 1
    
    print("工具使用频率:")
    for tool, count in tool_counter.most_common():
        print(f"  {tool}: {count}")
```

## 🧠 生成训练数据

### 1. 转换为 OpenAI 格式

```python
# data/convert_to_training.py

def convert_to_openai_format(trajectory: dict) -> dict:
    """转换为 OpenAI fine-tuning 格式"""
    
    messages = [
        {"role": "system", "content": "你是 CTF 密码学专家"}
    ]
    
    # 题目
    challenge = trajectory["challenge"]
    messages.append({
        "role": "user",
        "content": f"题目: {challenge['description']}"
    })
    
    # 解题过程
    for step in trajectory["steps"]:
        # Assistant 思考
        messages.append({
            "role": "assistant",
            "content": f"思考: {step['thought']}\\n行动: {step['action']}"
        })
        
        # Tool 返回
        messages.append({
            "role": "tool",
            "content": step["observation"]
        })
    
    # 最终答案
    if trajectory["success"]:
        messages.append({
            "role": "assistant",
            "content": f"FINAL ANSWER: {trajectory['flag']}"
        })
    
    return {"messages": messages}

# 批量转换
def batch_convert(input_dir: str, output_file: str):
    import json
    from pathlib import Path
    
    trajectories = []
    for file in Path(input_dir).glob("*.json"):
        with open(file) as f:
            trajectories.append(json.load(f))
    
    # 只保留成功的
    successful = [t for t in trajectories if t["success"]]
    
    with open(output_file, "w") as f:
        for t in successful:
            sample = convert_to_openai_format(t)
            f.write(json.dumps(sample, ensure_ascii=False) + "\\n")
    
    print(f"转换完成: {len(successful)} 条训练数据 -> {output_file}")
```

## 🚀 Scaling 策略

### 1. 数据收集策略

```python
# scaling/strategies.py

class DataCollectionStrategy:
    """数据收集策略"""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def collect_diverse_data(self, challenges: list):
        """收集多样化数据"""
        results = []
        
        for challenge in challenges:
            # 多次运行同一题目 (temperature 不同)
            for temp in [0.0, 0.5, 1.0]:
                self.agent.set_temperature(temp)
                result = await self.agent.solve(challenge)
                results.append(result)
        
        return results
    
    async def collect_with_variants(self, base_challenge: dict, variants: list):
        """收集变体数据"""
        results = []
        
        for variant in variants:
            challenge = {**base_challenge, **variant}
            result = await self.agent.solve(challenge)
            results.append(result)
        
        return results
```

### 2. 质量过滤

```python
def filter_quality(trajectories: list) -> list:
    """过滤高质量轨迹"""
    
    filtered = []
    
    for t in trajectories:
        # 必须成功
        if not t["success"]:
            continue
        
        # 步骤数合理 (不能太短也不能太长)
        if not (2 <= len(t["steps"]) <= 20):
            continue
        
        # 耗时合理
        if t["elapsed_time"] > 300:  # 5分钟
            continue
        
        # 包含正确的 flag 格式
        if not t["flag"] or "{" not in t["flag"]:
            continue
        
        filtered.append(t)
    
    return filtered
```

## 📊 可视化

```python
# visualization/plots.py

def plot_success_rate_by_type(data_dir: str):
    """按类型绘制成功率"""
    import matplotlib.pyplot as plt
    
    # 收集数据
    stats = analyze_trajectories(data_dir)
    
    # 绘图
    types = list(stats["by_type"].keys())
    rates = [stats["by_type"][t]["success_rate"] for t in types]
    
    plt.figure(figsize=(10, 6))
    plt.bar(types, rates)
    plt.xlabel("题目类型")
    plt.ylabel("成功率")
    plt.title("Agent 成功率按题目类型分布")
    plt.savefig("success_rate.png")
```

## 🎯 下一步

1. **收集数据**: 运行 Agent 解决大量题目
2. **清洗数据**: 过滤低质量轨迹
3. **生成训练集**: 转换为模型训练格式
4. **微调模型**: 使用收集的数据 fine-tune 模型
5. **迭代优化**: 用更好的模型收集更多数据

```
Agent v1 → 收集数据 → Fine-tune → Agent v2 → 收集更多数据 → ...
```
