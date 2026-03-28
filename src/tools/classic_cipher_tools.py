"""
古典密码破解工具

来源: 
- UTCTF2025 Autokey 攻击
- BaseCTF 2024 MD5 爆破
- BaseCTF 2024 背包问题
"""

import itertools
import string
from typing import List, Any
from collections import Counter
from langchain.tools import tool


@tool
def autokey_crack(ciphertext: str, max_key_length: int = 6, use_ngram: bool = True) -> str:
    """
    Autokey 密码自动破解
    
    Autokey 密码是 Vigenère 的变种，密钥由初始密钥 + 明文本身组成。
    通过频率分析(n-gram评分)找到最可能的密钥。
    
    Args:
        ciphertext: 密文 (只包含小写字母和符号)
        max_key_length: 最大密钥长度尝试
        use_ngram: 是否使用 n-gram 评分
    
    Returns:
        破解结果
    
    Example:
        >>> autokey_crack("lpqwma{rws_ywpqaauad_rrqfcfkq_wuey_ifwo_xlkvxawjh_pkbgrzf}")
    """
    try:
        # 预处理：分离字母和符号
        def preprocess(text):
            letters = []
            symbols = []
            for c in text:
                if c in string.ascii_lowercase:
                    letters.append(ord(c) - ord('a'))
                    symbols.append(None)
                else:
                    symbols.append(c)
            return letters, symbols
        
        # 解密函数
        def decrypt(cipher_nums, key):
            plain = []
            key_stream = list(key)
            for i in range(len(cipher_nums)):
                if i < len(key_stream):
                    k = key_stream[i]
                else:
                    k = plain[i - len(key)]
                p = (cipher_nums[i] - k) % 26
                plain.append(p)
                if i >= len(key):
                    key_stream.append(p)
            return plain
        
        # 频率评分
        def score_text(plain_nums):
            text = ''.join([chr(p + ord('a')) for p in plain_nums])
            
            # 简单的英语频率评分
            english_freq = {
                'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
                'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3
            }
            
            counter = Counter(text)
            total = len(text)
            score = 0
            
            for char, count in counter.items():
                freq = (count / total) * 100
                expected = english_freq.get(char, 1)
                score += abs(freq - expected)
            
            return score
        
        # 破解
        cipher_nums, symbol_pos = preprocess(ciphertext)
        best = {'score': float('inf'), 'key': None, 'plain': None}
        
        results = []
        
        for key_len in range(1, max_key_length + 1):
            # 尝试所有可能的密钥
            for key in itertools.product(range(26), repeat=key_len):
                plain_nums = decrypt(cipher_nums, key)
                current_score = score_text(plain_nums)
                
                if current_score < best['score']:
                    best['score'] = current_score
                    best['key'] = key
                    best['plain'] = plain_nums
                    
                    key_str = ''.join([chr(k + ord('a')) for k in key])
                    plain_str = ''.join([chr(p + ord('a')) for p in plain_nums])
                    results.append(f"Key={key_str} (len={key_len}): {plain_str[:50]}... (score={current_score:.2f})")
                
                # 限制尝试次数
                if len(results) > 100:
                    break
            
            if len(results) > 100:
                break
        
        # 重建结果
        plain_str = ''.join([chr(p + ord('a')) for p in best['plain']])
        key_str = ''.join([chr(k + ord('a')) for k in best['key']])
        
        return f"🎯 Autokey 破解成功!\n最佳密钥: {key_str}\n明文: {plain_str}\n\n其他可能结果:\n" + "\n".join(results[:5])
        
    except Exception as e:
        return f"破解失败: {e}"


@tool
def knapsack_decrypt(a_str: str, c: int, method: str = "superincreasing") -> str:
    """
    背包密码解密
    
    解决超递增背包问题。
    超递增序列：每个元素大于之前所有元素之和。
    
    Args:
        a_str: 背包序列 a，逗号分隔的整数
        c: 目标和
        method: 方法 (superincreasing/一般)
    
    Returns:
        解密结果 (二进制表示)
    """
    try:
        a = [int(x.strip()) for x in a_str.split(',')]
        
        if method == "superincreasing":
            # 超递增背包解密
            flag = ''
            remaining = c
            
            # 从大到小遍历
            for num in reversed(a):
                if remaining >= num:
                    flag = '1' + flag
                    remaining -= num
                else:
                    flag = '0' + flag
            
            if remaining == 0:
                # 转换为字节
                flag_int = int(flag, 2)
                try:
                    byte_len = (len(flag) + 7) // 8
                    plaintext = flag_int.to_bytes(byte_len, 'big').decode('utf-8', errors='replace')
                    return f"🎯 超递增背包解密成功!\n二进制: {flag}\n整数值: {flag_int}\n明文: {plaintext}"
                except:
                    return f"🎯 解密成功!\n二进制: {flag}\n整数值: {flag_int}"
            else:
                return f"❌ 无法精确表示，剩余: {remaining}"
        else:
            return "一般背包问题需要更复杂的算法 (如 LLL)"
            
    except Exception as e:
        return f"解密失败: {e}"


@tool
def md5_character_bruteforce(md5_list_str: str, charset: str = string.printable) -> str:
    """
    MD5 逐字符爆破
    
    当 flag 的每个字符的 MD5 被分别给出时，可以逐个爆破。
    
    Args:
        md5_list_str: MD5 值列表，逗号分隔
        charset: 字符集 (默认所有可打印字符)
    
    Returns:
        恢复的字符串
    """
    try:
        import hashlib
        
        md5_list = [x.strip().strip("'\"") for x in md5_list_str.split(',')]
        
        result = ''
        for target_md5 in md5_list:
            found = False
            for char in charset:
                if hashlib.md5(char.encode()).hexdigest() == target_md5:
                    result += char
                    found = True
                    break
            
            if not found:
                result += '?'
        
        return f"🎯 MD5 爆破结果: {result}"
        
    except Exception as e:
        return f"爆破失败: {e}"


@tool
def frequency_analysis(text: str, top_n: int = 10) -> str:
    """
    频率分析工具
    
    分析文本中各字符/字母的频率，帮助破解替换密码。
    
    Args:
        text: 要分析的文本
        top_n: 显示前 N 个高频字符
    
    Returns:
        频率分析结果
    """
    try:
        # 统计字母
        letters = [c.lower() for c in text if c.isalpha()]
        letter_freq = Counter(letters)
        
        # 统计所有字符
        all_chars = Counter(text)
        
        result = []
        result.append("📊 字母频率分析:")
        result.append("-" * 40)
        
        for char, count in letter_freq.most_common(top_n):
            bar = "█" * (count * 50 // len(letters))
            result.append(f"  {char}: {count:3d} ({count/len(letters)*100:5.1f}%) {bar}")
        
        result.append("\n📊 所有字符频率:")
        result.append("-" * 40)
        
        for char, count in all_chars.most_common(top_n):
            display = char if char.isprintable() else f"\\x{ord(char):02x}"
            result.append(f"  '{display}': {count}")
        
        result.append("\n💡 提示: 英语字母频率 e>t>a>o>i>n>s>h>r")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"分析失败: {e}"


def get_classic_cipher_tools() -> List[Any]:
    """获取所有古典密码工具"""
    return [
        autokey_crack,
        knapsack_decrypt,
        md5_character_bruteforce,
        frequency_analysis,
    ]
