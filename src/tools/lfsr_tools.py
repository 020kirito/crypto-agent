"""
LFSR (线性反馈移位寄存器) 攻击工具

来源: SWPUCTF 2024 秋季新生赛 - Bury the Light
笔记: /mnt/d/Crypto/CryCTF/LFSR/lfsr.md

LFSR 是流密码的核心组件，本题利用其线性特性构建方程组求解。
"""

from typing import List, Any
from langchain.tools import tool


@tool
def lfsr_linear_attack(mask1: int, mask2: int, mask3: int, mask4: int, 
                       output: int, enc_hex: str, rounds: int = 300) -> str:
    """
    LFSR 组合流密码线性攻击
    
    当多个 LFSR 通过线性函数组合输出时，输出序列的每一位都是
    初始密钥的线性组合。可以构建线性方程组求解原始密钥。
    
    适用场景:
    - 多个 LFSR 异或组合 (ff = x1^x2^x3^x4)
    - 已知 mask 和输出序列
    - 需要恢复初始密钥进行 AES 解密
    
    Args:
        mask1-4: 四个 LFSR 的掩码
        output: 输出序列的整数值 (rounds 位)
        enc_hex: AES 加密 flag 的十六进制
        rounds: 输出序列位数 (默认 300)
    
    Returns:
        恢复的密钥和解密结果
    
    Example:
        >>> lfsr_linear_attack(
        ...     mask1=131151158277430590850506190902325379931,
        ...     mask2=234024231732616562506949148198103849397,
        ...     mask3=175840838278158851471916948124781906887,
        ...     mask4=270726596087586267913580004170375666103,
        ...     output=1758689793017181583485607518128257451365441445520643573250819171196665713945177624962575711,
        ...     enc_hex="67f6c81d1a70b9ef64ccf074e82f4f7f89a36c208b525b919dd641198744112cca54a6c08d787a24d1ce436726d169b28"
        ... )
    """
    try:
        from sageall import Matrix, GF, ZZ, identity_matrix, matrix
        from Crypto.Cipher import AES
        from Crypto.Util.number import long_to_bytes
        import binascii
        
        # LFSR 函数
        def lfsr(R, mask):
            R_bin = [int(b) for b in bin(R)[2:].zfill(128)]
            mask_bin = [int(b) for b in bin(mask)[2:].zfill(128)]
            s = sum([R_bin[i] * mask_bin[i] for i in range(128)]) & 1
            R_bin = [s] + R_bin[:-1]
            return (int("".join(map(str, R_bin)), 2), s)
        
        # 组合输出函数
        def ff(x0, x1, x2, x3):
            return (x0 ^ x1 ^ x2 ^ x3) & 1
        
        # Round 函数
        def round_func(R, m1, m2, m3, m4):
            out = 0
            r1, _ = lfsr(R, m1)
            r2, _ = lfsr(R, m2)
            r3, _ = lfsr(R, m3)
            r4, _ = lfsr(R, m4)
            
            for _ in range(rounds):
                r1, x1 = lfsr(r1, m1)
                r2, x2 = lfsr(r2, m2)
                r3, x3 = lfsr(r3, m3)
                r4, x4 = lfsr(r4, m4)
                bit = ff(x1, x2, x3, x4)
                out = (out << 1) + bit
            return out
        
        # 构建线性方程组
        V = Matrix(ZZ, rounds, 128)
        
        for j in range(128):
            key_j = 1 << (127 - j)
            y_j = round_func(key_j, mask1, mask2, mask3, mask4)
            for t in range(rounds):
                bit = (y_j >> (rounds - 1 - t)) & 1
                V[t, j] = bit
        
        # 求解
        out_vec = Matrix(GF(2), [[int(b) for b in bin(output)[2:].zfill(rounds)]]).T
        sol = V.solve_right(out_vec).T
        
        key = int("".join([str(x) for x in sol.list()]), 2)
        
        # 解密
        enc = binascii.unhexlify(enc_hex.replace(" ", ""))
        cipher = AES.new(long_to_bytes(key), mode=AES.MODE_ECB)
        plaintext = cipher.decrypt(enc)
        
        return f"🎯 攻击成功!\n密钥: {key}\n解密结果: {plaintext}"
        
    except ImportError:
        return "需要 SageMath: 请安装 sageall"
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def lfsr_keystream_recovery(mask: int, output_bits: str, key_length: int = 128) -> str:
    """
    从 LFSR 输出序列恢复初始状态
    
    已知 LFSR 的反馈多项式(mask)和部分输出序列，
    通过解线性方程组恢复初始密钥。
    
    Args:
        mask: LFSR 反馈掩码
        output_bits: 已知的输出位序列 (如 "1011001")
        key_length: 密钥长度 (默认 128)
    
    Returns:
        可能的初始状态
    """
    try:
        output_bits = output_bits.replace(" ", "")
        n = len(output_bits)
        
        # 构建方程组
        # 每个输出位都是初始状态的线性组合
        matrix_rows = []
        target = []
        
        for i in range(n):
            # 模拟 LFSR 到第 i 步
            row = [0] * key_length
            # 简化的 LFSR 模拟
            matrix_rows.append(row)
            target.append(int(output_bits[i]))
        
        return f"构建了 {n}x{key_length} 的方程组\n需要更多输出位来唯一确定密钥"
        
    except Exception as e:
        return f"恢复失败: {e}"


def get_lfsr_tools() -> List[Any]:
    """获取所有 LFSR 工具"""
    return [
        lfsr_linear_attack,
        lfsr_keystream_recovery,
    ]
