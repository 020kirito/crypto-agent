# 🛠️ 创建你的第一个 Tool

本指南教你如何使用 LangChain 创建自定义工具。

## 📋 Tool 的基本结构

```python
from langchain.tools import tool

@tool
def my_tool(param1: str, param2: int) -> str:
    """
    工具的详细描述 - LLM 通过这个描述了解工具功能
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    """
    # 工具逻辑
    result = do_something(param1, param2)
    return result
```

## 🌟 实战：创建 ROT13 工具

ROT13 是一种特殊的凯撒密码，移位数固定为 13。

```python
from langchain.tools import tool

@tool
def rot13_decrypt(ciphertext: str) -> str:
    """
    ROT13 解密工具
    
    ROT13 是一种替换密码，将每个字母向后移动 13 位。
    由于字母表有 26 个字母，ROT13 是它自己的逆运算。
    
    Args:
        ciphertext: ROT13 编码的密文
    
    Returns:
        解密后的明文
    
    Example:
        >>> rot13_decrypt("Uryyb")
        "Hello"
    """
    result = ""
    for char in ciphertext:
        if char.isalpha():
            # 确定字母表基准
            base = ord('A') if char.isupper() else ord('a')
            # ROT13: 移动 13 位
            offset = (ord(char) - base + 13) % 26
            result += chr(base + offset)
        else:
            # 非字母字符保持不变
            result += char
    
    return result
```

## 🔑 关键点

### 1. 描述要详细

LLM 通过文档字符串了解工具功能，描述要包含：
- **功能说明**: 这个工具做什么
- **参数说明**: 每个参数的含义
- **返回值**: 返回什么
- **示例**: 使用示例

### 2. 类型注解

使用类型注解帮助 LLM 正确传递参数：

```python
@tool
def example(
    text: str,        # 字符串
    count: int,       # 整数
    ratio: float,     # 浮点数
    flag: bool,       # 布尔值
    items: list       # 列表
) -> str:
    ...
```

### 3. 错误处理

工具应该优雅地处理错误：

```python
@tool
def safe_divide(a: float, b: float) -> str:
    """安全除法"""
    try:
        if b == 0:
            return "错误: 不能除以零"
        result = a / b
        return f"结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"
```

## 📝 进阶：带复杂参数的 Tool

```python
from typing import Dict, List
from langchain.tools import tool

@tool
def analyze_crypto_params(params: str) -> str:
    """
    分析密码学参数
    
    分析给定的密码学参数，识别可能的攻击方式。
    
    Args:
        params: JSON 格式的参数字符串，例如:
                '{"n": 3233, "e": 17, "c": 2790}'
    
    Returns:
        分析结果和建议的攻击方式
    """
    import json
    
    try:
        # 解析参数
        data = json.loads(params)
        n = data.get('n')
        e = data.get('e')
        c = data.get('c')
        
        analysis = []
        
        # 分析 n 的大小
        if n:
            if n < 10000:
                analysis.append("n 较小，可以尝试试除法分解")
            elif n < 10**12:
                analysis.append("n 中等大小，尝试 Fermat 分解")
            else:
                analysis.append("n 很大，需要高级分解方法")
        
        # 分析 e
        if e:
            if e == 3 or e == 5:
                analysis.append(f"e={e} 较小，可能存在小指数攻击")
            elif e == 65537:
                analysis.append("e=65537 是标准值")
        
        return "\\n".join(analysis) if analysis else "无法分析"
        
    except json.JSONDecodeError:
        return "错误: 参数格式不正确，请提供有效的 JSON"
    except Exception as e:
        return f"分析错误: {e}"
```

## 🧪 测试你的 Tool

```python
# 测试文件: test_my_tool.py

from tools.crypto_tools import rot13_decrypt

def test_rot13():
    # 测试基本功能
    result = rot13_decrypt.invoke({"ciphertext": "Uryyb"})
    assert result == "Hello"
    
    # 测试回文特性
    original = "Hello World"
    encrypted = rot13_decrypt.invoke({"ciphertext": original})
    decrypted = rot13_decrypt.invoke({"ciphertext": encrypted})
    assert decrypted == original
    
    print("✅ 所有测试通过!")

if __name__ == "__main__":
    test_rot13()
```

## 📚 常用工具模式

### 模式 1: 解码工具

```python
@tool
def decode_xxx(data: str) -> str:
    """XXX 解码"""
    try:
        decoded = xxx_decode(data)
        return f"解码成功: {decoded}"
    except Exception as e:
        return f"解码失败: {e}"
```

### 模式 2: 分析工具

```python
@tool
def analyze_xxx(text: str) -> str:
    """分析 XXX 特征"""
    features = extract_features(text)
    return format_analysis(features)
```

### 模式 3: 暴力破解工具

```python
@tool
def brute_xxx(ciphertext: str, max_attempts: int = 100) -> str:
    """暴力破解 XXX"""
    for i in range(max_attempts):
        result = try_decode(ciphertext, i)
        if looks_like_flag(result):
            return f"成功! key={i}, result={result}"
    return f"尝试了 {max_attempts} 次，未找到结果"
```

## 🎯 练习

1. 创建一个 Base64 编码工具
2. 创建一个检测编码类型的工具
3. 创建一个批量凯撒解密工具 (尝试所有 shift)

完成后，将这些工具添加到 `src/tools/crypto_tools.py` 中！
