"""
CopperSmith 攻击工具

来源: CopperSmith类题目.md

CopperSmith 算法用于求解模多项式方程的小根，是 RSA 攻击中的重要工具。
"""

from typing import List, Any
from langchain.tools import tool


@tool
def coppersmith_univariate(poly_coeffs_str: str, N: int, X: int) -> str:
    """
    CopperSmith 单变量多项式小根求解
    
    求解 f(x) ≡ 0 (mod N) 的小根 x，其中 |x| < X。
    
    常见应用:
    - 部分明文泄露 (m = m_high * 2^k + x)
    - 填充攻击
    - RSA 小指数广播攻击
    
    Args:
        poly_coeffs_str: 多项式系数，从高次到低次，逗号分隔
                         例如 "1,0,-c" 表示 x^2 - c
        N: 模数
        X: 小根的上界
    
    Returns:
        找到的小根
    
    Example:
        >>> coppersmith_univariate(
        ...     poly_coeffs_str="1,0,-15839981826808763964776267977873436471731337128631076275700612690840398443624729172874876360480710625538537297195589823861172967194157178089069085894122332792736238372018533",
        ...     N=97749087693512967475298392505938212553786992324278366480059797686191115697843807880290898619101038956451494676688415439521209032147590786355166133376656995376940929736615752950435760573768036841112780444621323188977728389727851492721114090843246780991492018401178577644965139921998193472409204611839560552023,
        ...     X=2**103
        ... )
    """
    try:
        from sageall import PolynomialRing, Zmod, ZZ, Matrix
        
        # 解析多项式系数
        coeffs = [int(x.strip()) for x in poly_coeffs_str.split(',')]
        
        # 创建多项式环
        R = PolynomialRing(Zmod(N), 'x')
        x = R.gen()
        
        # 构造多项式
        f = 0
        for i, c in enumerate(coeffs):
            power = len(coeffs) - i - 1
            f += c * x**power
        
        # 使用 Sage 的 small_roots 方法
        # 需要转换为整数多项式
        Zx = PolynomialRing(ZZ, 'x')
        f_int = Zx(f.coefficients(sparse=False))
        
        # 尝试求解
        roots = f_int.small_roots(X=X, beta=0.5)
        
        if roots:
            result = ["🎯 CopperSmith 找到小根:"]
            for r in roots:
                result.append(f"  x = {r}")
                # 验证
                if f_int(r) % N == 0:
                    result.append(f"    ✅ 验证通过: f({r}) ≡ 0 (mod N)")
            return "\n".join(result)
        else:
            return f"❌ 未找到小于 X={X} 的根\n尝试增大 X 或使用不同的 beta 参数"
            
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"求解失败: {e}"


@tool
def coppersmith_rsa_padding(m_high: int, c: int, e: int, N: int, kbits: int) -> str:
    """
    CopperSmith RSA 填充攻击
    
    当明文 m 的高 bits 已知，低 kbits 未知时，恢复完整明文。
    
    m = (m_high << kbits) + x，其中 x 是未知的小根
    
    Args:
        m_high: 已知的明文高位
        c: 密文
        e: 公钥指数
        N: 模数
        kbits: 未知的低位位数
    
    Returns:
        恢复的明文
    """
    try:
        from sageall import PolynomialRing, Zmod, ZZ
        
        # 构造多项式: (m_high * 2^k + x)^e - c ≡ 0 (mod N)
        R = PolynomialRing(Zmod(N), 'x')
        x = R.gen()
        
        m_base = m_high << kbits
        f = (m_base + x)**e - c
        
        # 求解小根
        X = 1 << kbits  # 未知位的范围
        roots = f.small_roots(X=X, beta=0.4)
        
        if roots:
            result = ["🎯 RSA 填充攻击成功!"]
            for r in roots:
                m = m_base + int(r)
                # 验证
                if pow(m, e, N) == c:
                    result.append(f"  明文 m = {m}")
                    try:
                        from Crypto.Util.number import long_to_bytes
                        flag = long_to_bytes(m)
                        result.append(f"  解码: {flag}")
                    except:
                        pass
            return "\n".join(result)
        else:
            return f"❌ 攻击失败，尝试调整参数或检查输入"
            
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def coppersmith_related_message(c1: int, c2: int, e: int, N: int, diff: int = None) -> str:
    """
    CopperSmith 相关消息攻击 (Franklin-Reiter)
    
    当两个明文 m1 和 m2 满足线性关系 m2 = a*m1 + b 时，
    可以恢复明文。
    
    Args:
        c1, c2: 两个密文
        e: 公钥指数 (通常 e=3)
        N: 模数
        diff: 明文差值 (如果 m2 = m1 + diff)
    
    Returns:
        恢复的明文
    """
    try:
        from sageall import PolynomialRing, Zmod, ZZ, gcd
        
        if diff is None:
            return "需要提供明文之间的关系 (如 diff 使得 m2 = m1 + diff)"
        
        # 对于 e=3 和 m2 = m1 + diff
        # c1 = m1^3, c2 = (m1 + diff)^3
        # 可以构造多项式求解
        
        R = PolynomialRing(Zmod(N), 'm')
        m = R.gen()
        
        f1 = m**e - c1
        f2 = (m + diff)**e - c2
        
        # 计算 GCD
        g = gcd(f1, f2)
        
        # 求根
        roots = g.roots()
        
        if roots:
            result = ["🎯 相关消息攻击成功!"]
            for r, _ in roots:
                m_val = int(r)
                if pow(m_val, e, N) == c1:
                    result.append(f"  明文 m1 = {m_val}")
                    try:
                        from Crypto.Util.number import long_to_bytes
                        flag = long_to_bytes(m_val)
                        result.append(f"  解码: {flag}")
                    except:
                        pass
            return "\n".join(result)
        else:
            return "❌ 未找到根"
            
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"攻击失败: {e}"


def get_coppersmith_tools() -> List[Any]:
    """获取所有 CopperSmith 工具"""
    return [
        coppersmith_univariate,
        coppersmith_rsa_padding,
        coppersmith_related_message,
    ]
