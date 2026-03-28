"""
CTF 通用工具 - LangChain Tools

这里定义 CTF 通用的辅助工具。
"""

from typing import List, Any
from pathlib import Path

from langchain.tools import tool


@tool
def read_challenge_file(filepath: str) -> str:
    """
    读取题目文件
    
    读取 CTF 题目文件的内容。
    
    Args:
        filepath: 文件路径
    
    Returns:
        文件内容
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {e}"


@tool
def search_flag_pattern(text: str) -> str:
    """
    搜索 flag 模式
    
    在文本中搜索常见的 flag 格式。
    
    Args:
        text: 要搜索的文本
    
    Returns:
        找到的 flag 或提示
    """
    import re
    
    patterns = [
        r'flag\{[^}]+\}',
        r'FLAG\{[^}]+\}',
        r'ctf\{[^}]+\}',
        r'CTF\{[^}]+\}',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    
    if found:
        return f"找到 {len(found)} 个可能的 flag:\n" + "\n".join(found)
    else:
        return "未找到常见的 flag 格式"


@tool
def extract_numbers(text: str) -> str:
    """
    提取文本中的数字
    
    从题目描述中提取所有数字，常用于获取 RSA 参数。
    
    Args:
        text: 题目文本
    
    Returns:
        提取到的数字列表
    """
    import re
    
    # 匹配整数
    numbers = re.findall(r'\b\d+\b', text)
    
    if numbers:
        return f"提取到的数字 ({len(numbers)} 个):\n" + ", ".join(numbers[:20])
    else:
        return "未找到数字"


@tool
def try_common_passwords(hint: str = "") -> str:
    """
    尝试常见密码
    
    返回 CTF 中常见的密码/密钥列表。
    
    Args:
        hint: 密码提示 (可选)
    
    Returns:
        常见密码列表
    """
    common_passwords = [
        "password", "123456", "admin",
        "ctf", "flag", "root",
        "qwerty", "password123",
        "secret", "key", "crypto",
    ]
    
    result = ["常见密码列表:", "-" * 20]
    for pwd in common_passwords[:10]:
        result.append(f"  - {pwd}")
    
    return "\n".join(result)


def get_ctf_tools() -> List[Any]:
    """获取所有 CTF 通用工具"""
    return [
        read_challenge_file,
        search_flag_pattern,
        extract_numbers,
        try_common_passwords,
    ]
