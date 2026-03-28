"""
密码学工具集 - LangChain Tools

这里定义所有与密码学相关的工具函数。
每个工具都是一个 @tool 装饰的函数。

关键概念:
- @tool 装饰器: 将普通函数转换为 LangChain Tool
- Tool 需要: name (名称), description (描述), 函数实现
- LLM 通过 description 来决定是否调用该工具
"""

import base64
import binascii
from typing import List, Dict, Any, Optional
from math import gcd, isqrt

# LangChain 工具装饰器
from langchain.tools import tool


# ============== 编码/解码工具 ==============

@tool
def base64_decode(data: str) -> str:
    """
    Base64 解码工具
    
    将 Base64 编码的字符串解码为明文。
    适用于识别出 Base64 编码的密文。
    
    Args:
        data: Base64 编码的字符串
    
    Returns:
        解码后的字符串
    
    Example:
        >>> base64_decode("SGVsbG8=")
        "Hello"
    """
    try:
        decoded = base64.b64decode(data)
        # 尝试作为 UTF-8 解码
        return decoded.decode('utf-8', errors='replace')
    except Exception as e:
        return f"解码失败: {e}"


@tool
def hex_decode(hex_string: str) -> str:
    """
    十六进制解码工具
    
    将十六进制字符串解码为明文。
    
    Args:
        hex_string: 十六进制字符串 (如 "48656c6c6f")
    
    Returns:
        解码后的字符串
    """
    try:
        # 移除可能的空格
        hex_string = hex_string.replace(" ", "").replace("0x", "")
        decoded = binascii.unhexlify(hex_string)
        return decoded.decode('utf-8', errors='replace')
    except Exception as e:
        return f"解码失败: {e}"


@tool
def caesar_cipher_decrypt(ciphertext: str, shift: int = None) -> str:
    """
    凯撒密码解密工具
    
    通过将每个字母移动固定位数来解密。
    如果不指定 shift，会尝试所有 26 种可能。
    
    Args:
        ciphertext: 密文
        shift: 位移数 (0-25)，不指定则尝试所有
    
    Returns:
        解密结果
    """
    def shift_char(c, s):
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            return chr((ord(c) - base - s) % 26 + base)
        return c
    
    if shift is not None:
        # 使用指定 shift
        plaintext = ''.join(shift_char(c, shift) for c in ciphertext)
        return f"Shift {shift}: {plaintext}"
    else:
        # 尝试所有 shift
        results = []
        for s in range(26):
            plaintext = ''.join(shift_char(c, s) for c in ciphertext)
            results.append(f"Shift {s}: {plaintext}")
        return "\n".join(results[:10])  # 返回前10个结果


@tool
def xor_decrypt(data: str, key: str) -> str:
    """
    XOR 解密工具
    
    使用密钥对数据进行 XOR 解密。
    
    Args:
        data: 十六进制编码的密文
        key: XOR 密钥 (字符串或十六进制)
    
    Returns:
        解密结果
    """
    try:
        # 转换数据
        data = data.replace(" ", "")
        if all(c in '0123456789abcdefABCDEF' for c in data):
            data_bytes = binascii.unhexlify(data)
        else:
            data_bytes = data.encode()
        
        # 转换密钥
        if all(c in '0123456789abcdefABCDEF' for c in key):
            key_bytes = binascii.unhexlify(key)
        else:
            key_bytes = key.encode()
        
        # XOR
        result = bytearray()
        for i, b in enumerate(data_bytes):
            result.append(b ^ key_bytes[i % len(key_bytes)])
        
        # 尝试解码
        try:
            return result.decode('utf-8')
        except:
            return f"解密结果 (hex): {result.hex()}"
    except Exception as e:
        return f"解密失败: {e}"


# ============== RSA 工具 ==============

@tool
def rsa_factor_small_n(n: int) -> str:
    """
    RSA 小因数分解工具
    
    尝试分解较小的 RSA 模数 n (通常 n < 10^12)。
    使用试除法和 Fermat 分解。
    
    Args:
        n: RSA 模数
    
    Returns:
        分解结果 p 和 q
    """
    try:
        n = int(n)
        
        # 试除法
        limit = min(1000000, isqrt(n) + 1)
        for p in range(2, limit):
            if n % p == 0:
                q = n // p
                return f"分解成功! n = {p} * {q}"
        
        # Fermat 分解 (适用于 p, q 接近)
        a = isqrt(n)
        if a * a < n:
            a += 1
        
        max_iter = 100000
        for _ in range(max_iter):
            b2 = a * a - n
            b = isqrt(b2)
            if b * b == b2:
                p = a - b
                q = a + b
                return f"Fermat 分解成功! n = {p} * {q}"
            a += 1
        
        return f"无法在合理时间内分解 n={n}，可能需要更高级的分解方法"
        
    except Exception as e:
        return f"分解失败: {e}"


@tool
def rsa_calculate_private_key(p: int, q: int, e: int = 65537) -> str:
    """
    RSA 私钥计算工具
    
    已知 p, q, e 时计算私钥 d。
    
    Args:
        p: 质数 p
        q: 质数 q
        e: 公钥指数 (默认 65537)
    
    Returns:
        私钥信息
    """
    try:
        p, q, e = int(p), int(q), int(e)
        
        n = p * q
        phi = (p - 1) * (q - 1)
        
        # 检查 e 和 phi 是否互质
        if gcd(e, phi) != 1:
            return f"错误: e={e} 和 phi={phi} 不互质"
        
        # 计算 d
        d = pow(e, -1, phi)
        
        return f"""RSA 私钥计算结果:
n = {n}
phi(n) = {phi}
e = {e}
d = {d}

私钥: (n={n}, d={d})
"""
    except Exception as e:
        return f"计算失败: {e}"


@tool
def rsa_decrypt(c: int, d: int, n: int) -> str:
    """
    RSA 解密工具
    
    使用私钥解密密文。
    
    Args:
        c: 密文
        d: 私钥指数
        n: 模数
    
    Returns:
        解密结果
    """
    try:
        c, d, n = int(c), int(d), int(n)
        
        # RSA 解密: m = c^d mod n
        m = pow(c, d, n)
        
        # 尝试转换为字符串
        try:
            byte_length = (m.bit_length() + 7) // 8
            plaintext = m.to_bytes(byte_length, 'big').decode('utf-8', errors='replace')
            return f"解密结果 (数字): {m}\n解密结果 (字符串): {plaintext}"
        except:
            return f"解密结果: {m}"
            
    except Exception as e:
        return f"解密失败: {e}"


@tool
def analyze_text_frequency(text: str) -> str:
    """
    文本频率分析工具
    
    分析文本中字母的出现频率，有助于破解替换密码。
    
    Args:
        text: 待分析的文本
    
    Returns:
        频率分析结果
    """
    from collections import Counter
    
    # 统计字母频率
    letters = [c.lower() for c in text if c.isalpha()]
    freq = Counter(letters)
    total = len(letters)
    
    if total == 0:
        return "没有检测到字母"
    
    # 排序并格式化
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    result = ["字母频率分析 (从高到低):"]
    result.append("-" * 30)
    
    for char, count in sorted_freq[:10]:
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        result.append(f"{char}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    result.append("\n提示: 英语中最常见的字母是 e, t, a, o, i, n")
    
    return "\n".join(result)


# ============== 工具集合 ==============

def get_crypto_tools() -> List[Any]:
    """
    获取所有密码学工具
    
    Returns:
        工具列表，用于传递给 Agent
    """
    return [
        # 编码解码
        base64_decode,
        hex_decode,
        caesar_cipher_decrypt,
        xor_decrypt,
        
        # RSA
        rsa_factor_small_n,
        rsa_calculate_private_key,
        rsa_decrypt,
        
        # 分析
        analyze_text_frequency,
    ]
