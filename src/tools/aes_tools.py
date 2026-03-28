"""
AES 加密工具集

AES (Advanced Encryption Standard) 是现代最常用的对称加密算法。
在 CTF 中，常见考点包括：
- ECB 模式攻击
- CBC 模式 IV 问题
- 已知密钥解密
"""

from typing import List, Any
from langchain.tools import tool


@tool
def aes_ecb_decrypt(ciphertext_hex: str, key_hex: str) -> str:
    """
    AES-ECB 模式解密
    
    ECB (Electronic Codebook) 是最简单的 AES 模式，
    每个数据块独立加密。相同的明文块会产生相同的密文块。
    
    Args:
        ciphertext_hex: 十六进制编码的密文
        key_hex: 十六进制编码的密钥 (16/24/32字节对应AES-128/192/256)
    
    Returns:
        解密后的明文
    
    Example:
        >>> aes_ecb_decrypt("ciphertext_hex", "000102030405060708090a0b0c0d0e0f")
        "Hello World"
    """
    try:
        from Crypto.Cipher import AES
        import binascii
        
        # 转换十六进制为字节
        ciphertext = binascii.unhexlify(ciphertext_hex.replace(" ", ""))
        key = binascii.unhexlify(key_hex.replace(" ", ""))
        
        # 创建 AES-ECB 解密器
        cipher = AES.new(key, AES.MODE_ECB)
        
        # 解密
        plaintext = cipher.decrypt(ciphertext)
        
        # 去除 PKCS7 填充
        padding_len = plaintext[-1]
        plaintext = plaintext[:-padding_len]
        
        # 尝试解码为字符串
        try:
            return plaintext.decode('utf-8')
        except:
            return f"解密结果 (hex): {plaintext.hex()}"
            
    except Exception as e:
        return f"解密失败: {e}"


@tool
def aes_cbc_decrypt(ciphertext_hex: str, key_hex: str, iv_hex: str) -> str:
    """
    AES-CBC 模式解密
    
    CBC (Cipher Block Chaining) 是常用的 AES 模式，
    每个数据块与前一个密文块进行 XOR 后再加密。
    
    Args:
        ciphertext_hex: 十六进制编码的密文
        key_hex: 十六进制编码的密钥
        iv_hex: 十六进制编码的初始向量 (IV，16字节)
    
    Returns:
        解密后的明文
    """
    try:
        from Crypto.Cipher import AES
        import binascii
        
        ciphertext = binascii.unhexlify(ciphertext_hex.replace(" ", ""))
        key = binascii.unhexlify(key_hex.replace(" ", ""))
        iv = binascii.unhexlify(iv_hex.replace(" ", ""))
        
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        plaintext = cipher.decrypt(ciphertext)
        
        # 去除填充
        padding_len = plaintext[-1]
        plaintext = plaintext[:-padding_len]
        
        try:
            return plaintext.decode('utf-8')
        except:
            return f"解密结果 (hex): {plaintext.hex()}"
            
    except Exception as e:
        return f"解密失败: {e}"


@tool
def detect_ecb_mode(ciphertext_hex: str, block_size: int = 32) -> str:
    """
    检测是否为 ECB 模式
    
    ECB 模式的特征：相同的明文块会产生相同的密文块。
    通过检测重复块来判断是否为 ECB 模式。
    
    Args:
        ciphertext_hex: 十六进制编码的密文
        block_size: 块大小 (字节)，默认32(16字节*2个字符)
    
    Returns:
        检测结果
    """
    try:
        import binascii
        
        ciphertext = binascii.unhexlify(ciphertext_hex.replace(" ", ""))
        
        # 分块
        blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
        
        # 检测重复块
        unique_blocks = set(blocks)
        
        if len(blocks) != len(unique_blocks):
            repeated = len(blocks) - len(unique_blocks)
            return f"⚠️  检测到 {repeated} 个重复块，很可能是 ECB 模式！\n重复块: {[b.hex() for b in blocks if blocks.count(b) > 1][:3]}"
        else:
            return "✅ 没有检测到重复块，可能不是 ECB 模式"
            
    except Exception as e:
        return f"检测失败: {e}"


@tool
def pkcs7_pad(data: str, block_size: int = 16) -> str:
    """
    PKCS7 填充
    
    将数据填充到块大小的整数倍。
    
    Args:
        data: 原始数据
        block_size: 块大小 (默认16)
    
    Returns:
        填充后的十六进制字符串
    """
    try:
        data_bytes = data.encode('utf-8')
        padding_len = block_size - (len(data_bytes) % block_size)
        padded = data_bytes + bytes([padding_len] * padding_len)
        return padded.hex()
    except Exception as e:
        return f"填充失败: {e}"


def get_aes_tools() -> List[Any]:
    """获取所有 AES 工具"""
    return [
        aes_ecb_decrypt,
        aes_cbc_decrypt,
        detect_ecb_mode,
        pkcs7_pad,
    ]
