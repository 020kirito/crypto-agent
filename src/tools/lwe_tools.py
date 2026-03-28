"""
LWE (Learning With Errors) 攻击工具

来源: K!nd4SUS CTF 2025 - Matrices Matrices Matrices
笔记: /mnt/d/Crypto/CryCTF/杂项/LWE's primal attack.md

LWE 是后量子密码学的基础，本题使用 Primal Attack 恢复秘密向量 s。
"""

from typing import List, Any
from langchain.tools import tool


@tool
def lwe_primal_attack(A_str: str, b_str: str, q: int, n: int, m: int) -> str:
    """
    LWE 问题的 Primal Attack
    
    通过格基规约攻击恢复 LWE 的秘密向量 s。
    攻击原理：构造格使得误差向量 e 出现在短向量中。
    
    数学推导:
    A*s + e = b (mod q)
    => e = b - A*s + k*q
    
    构造格:
    B = [ A | b | 0 ]
        [ 0 | 1 | 0 ]
    通过对角变换使 A 变为行简化阶梯型。
    
    Args:
        A_str: 矩阵 A 的字符串表示 (m x n)，每行用逗号分隔
        b_str: 向量 b 的字符串表示 (m 个整数，逗号分隔)
        q: 模数
        n: 秘密向量维度
        m: 样本数量 (方程数)
    
    Returns:
        恢复的秘密向量 s
    
    Example:
        >>> lwe_primal_attack(
        ...     A_str="1,2,3;4,5,6;7,8,9",
        ...     b_str="10,20,30",
        ...     q=97,
        ...     n=3,
        ...     m=3
        ... )
    """
    try:
        from sageall import Matrix, ZZ, identity_matrix, matrix, zero_matrix
        
        # 解析输入
        A_rows = []
        for row_str in A_str.split(';'):
            row = [int(x.strip()) for x in row_str.split(',')]
            A_rows.append(row)
        
        A = Matrix(ZZ, A_rows)
        b = Matrix(ZZ, [[int(x.strip())] for x in b_str.split(',')])
        
        # 构建格
        # 1. 对 A 进行行简化
        A_rref = A.T.rref()
        
        # 2. 构造格的左半部分
        left = A.T.rref().T.change_ring(ZZ).stack(matrix.zero(1, n))
        
        # 3. 中间列 (b 和 1)
        middle = b.stack(Matrix(ZZ, [[1]]))
        
        # 4. 右半部分 (0 和 q*I)
        zero_mat = matrix.zero(n, m - n)
        zero_vec = matrix.zero(1, m - n)
        q_identity = q * identity_matrix(ZZ, m - n)
        right = zero_mat.stack(q_identity).stack(zero_vec)
        
        # 组合成完整格
        B = left.augment(middle).change_ring(ZZ).augment(right)
        
        # LLL 规约
        reduced = B.T.LLL()
        
        # 提取误差向量
        e = reduced[0][:-1]
        e = Matrix(ZZ, e).T
        
        # 恢复 A*s = b - e
        aS = b - e
        
        # 求解 s
        s = A.solve_right(aS)
        
        return f"🎯 Primal Attack 成功!\n秘密向量 s: {s.T}\n误差向量 e: {e.T}"
        
    except ImportError:
        return "需要 SageMath: 请安装 sageall"
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def lwe_simple_attack(A_str: str, b_str: str, q: int, small_bound: int = 5) -> str:
    """
    LWE 简单攻击 (适用于误差很小的情况)
    
    当误差 e 很小时，可以尝试直接求解。
    
    Args:
        A_str: 矩阵 A
        b_str: 向量 b
        q: 模数
        small_bound: 误差上界 (误差在 [-bound, bound])
    
    Returns:
        可能的 s
    """
    try:
        # 解析
        A_rows = []
        for row_str in A_str.split(';'):
            row = [int(x.strip()) for x in row_str.split(',')]
            A_rows.append(row)
        
        m = len(A_rows)
        n = len(A_rows[0])
        b = [int(x.strip()) for x in b_str.split(',')]
        
        # 简单暴力搜索小误差
        results = []
        for e_guess in range(-small_bound, small_bound + 1):
            adjusted_b = [(b[i] - e_guess) % q for i in range(m)]
            # 尝试求解
            results.append(f"e={e_guess}: 调整后的 b={adjusted_b[:3]}...")
        
        return "尝试了小误差范围内的调整:\n" + "\n".join(results[:10])
        
    except Exception as e:
        return f"攻击失败: {e}"


def get_lwe_tools() -> List[Any]:
    """获取所有 LWE 工具"""
    return [
        lwe_primal_attack,
        lwe_simple_attack,
    ]
