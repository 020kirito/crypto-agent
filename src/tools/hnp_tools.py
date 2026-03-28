"""
HNP (Hidden Number Problem) 攻击工具

来源: Lattice刷题笔记.md

HNP 是格密码中的经典问题，常见于泄露部分比特的随机数恢复。
"""

from typing import List, Any
from langchain.tools import tool


@tool
def hnp_solver_high_bits(A_str: str, B_str: str, q: int, bits_leaked: int, total_bits: int = 256) -> str:
    """
    HNP 求解器 - 高位泄露版本
    
    当随机数 x 与已知数 a 相乘后，结果的高 bits_leaked 位泄露时，
    可以通过构造格来恢复完整的 x。
    
    数学模型:
    a_i * x ≡ b_i (mod q)
    其中 b_i = 2^(total_bits-bits_leaked) * b_hi + b_li
    
    Args:
        A_str: a_i 列表，逗号分隔
        B_str: b_i 的高位部分列表，逗号分隔
        q: 模数
        bits_leaked: 泄露的位数
        total_bits: 总位数 (默认256)
    
    Returns:
        恢复的 x
    
    Example:
        >>> hnp_solver_high_bits(
        ...     A_str="3561678147813669042672186969104055553515262226168087322052560790885260761433,...",
        ...     B_str="185,121,74,...",
        ...     q=2**256,
        ...     bits_leaked=8
        ... )
    """
    try:
        from sageall import Matrix, ZZ, QQ, GF
        
        # 解析输入
        A = [int(x.strip()) for x in A_str.split(',')]
        B_hi = [int(x.strip()) for x in B_str.split(',')]
        
        n = len(A)
        if n < 2:
            return "需要至少2组数据"
        
        # 使用第一组作为参考
        a0 = A[0]
        b0_hi = B_hi[0]
        
        # 计算 a0 的逆元
        try:
            a0_inv = ZZ(GF(q)(a0) ** -1)
        except:
            return "a0 在模 q 下不可逆，请选择其他参考"
        
        # 构造 HNP 格
        # L = [[q, 0, ..., 0, 0, 0],
        #      [0, q, ..., 0, 0, 0],
        #      ...
        #      [A_1, A_2, ..., A_n, 1, 0],
        #      [B_1, B_2, ..., B_n, 0, 2^(total_bits-bits_leaked)]]
        
        rows = n - 1  # 使用 n-1 组差分数据
        M = Matrix(ZZ, rows + 2, rows + 2)
        
        # 对角线填充 q
        for i in range(rows):
            M[i, i] = q
        
        # 填充 A 和 B
        shift = total_bits - bits_leaked
        for i in range(1, rows + 1):
            # A_i = a0^{-1} * a_i mod q
            Ai = ZZ(a0_inv * A[i] % q)
            M[rows, i-1] = Ai
            
            # B_i = a0^{-1} * (a_i * 2^shift * b0_hi - a0 * 2^shift * b_i_hi) mod q
            Bi = ZZ(a0_inv * (A[i] * (b0_hi << shift) - a0 * (B_hi[i] << shift)) % q)
            M[rows + 1, i-1] = Bi
        
        # 右下角
        M[rows, rows] = 1
        M[rows + 1, rows + 1] = 1 << shift
        
        # LLL 规约
        L = M.LLL()
        
        # 提取结果
        # 最短向量应该形如 (b_l1, b_l2, ..., b_ln, b_l0, 2^shift)
        v = L[0]
        b_l0 = abs(v[-2])
        
        # 恢复完整的 b0
        b0 = (b0_hi << shift) + b_l0
        
        # 计算 x
        x = ZZ(GF(q)(b0) / GF(q)(a0))
        
        return f"🎯 HNP 求解成功!\nx = {x}\nb0 = {b0}"
        
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"求解失败: {e}"


@tool
def hnp_solver_low_bits(A_str: str, B_str: str, q: int, bits_leaked: int) -> str:
    """
    HNP 求解器 - 低位泄露版本
    
    当随机数 x 与已知数 a 相乘后，结果的低 bits_leaked 位泄露时。
    
    Args:
        A_str: a_i 列表
        B_str: b_i 的低位部分列表
        q: 模数
        bits_leaked: 泄露的位数
    
    Returns:
        恢复的 x
    """
    try:
        from sageall import Matrix, ZZ, GF
        
        A = [int(x.strip()) for x in A_str.split(',')]
        B_lo = [int(x.strip()) for x in B_str.split(',')]
        
        n = len(A)
        mask = (1 << bits_leaked) - 1
        
        # 对于低位泄露，使用不同的格构造
        # b_i = (a_i * x) & mask
        
        # 构造格求解
        # 简化为暴力搜索 (对于小bits_leaked)
        if bits_leaked <= 8:
            for guess in range(1 << (bits_leaked * 2)):
                # 验证猜测
                valid = True
                for i in range(min(5, n)):
                    if (A[i] * guess) & mask != B_lo[i]:
                        valid = False
                        break
                if valid:
                    return f"找到候选解: x = {guess}"
        
        return f"低位泄露求解需要更复杂的格构造，建议参考完整 HNP 论文"
        
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"求解失败: {e}"


def get_hnp_tools() -> List[Any]:
    """获取所有 HNP 工具"""
    return [
        hnp_solver_high_bits,
        hnp_solver_low_bits,
    ]
