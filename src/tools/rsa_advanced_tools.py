"""
高级 RSA 攻击工具

包含更多 RSA 攻击方法，用于处理各种 CTF 场景。
"""

from typing import List, Any, Tuple
from math import gcd, isqrt
from langchain.tools import tool


@tool
def rsa_common_modulus_attack(c1: int, c2: int, e1: int, e2: int, n: int) -> str:
    """
    RSA 共模攻击
    
    当同一个 n 被两个不同的公钥 e1, e2 加密时，
    如果 gcd(e1, e2) = 1，可以通过扩展欧几里得算法恢复明文。
    
    Args:
        c1: 密文1
        c2: 密文2
        e1: 公钥指数1
        e2: 公钥指数2
        n: 共同模数
    
    Returns:
        解密结果
    
    Example:
        >>> rsa_common_modulus_attack(123, 456, 3, 5, 100000)
        "解密结果: flag{...}"
    """
    try:
        def extended_gcd(a, b):
            if a == 0:
                return b, 0, 1
            gcd_val, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd_val, x, y
        
        # 检查 e1, e2 是否互质
        g, s, t = extended_gcd(e1, e2)
        
        if g != 1:
            return f"e1={e1} 和 e2={e2} 不互质 (gcd={g})，无法使用共模攻击"
        
        # 确保 s 为正数
        if s < 0:
            s = -s
            c1 = pow(c1, -1, n)
        if t < 0:
            t = -t
            c2 = pow(c2, -1, n)
        
        # 计算明文: m = c1^s * c2^t mod n
        m = (pow(c1, s, n) * pow(c2, t, n)) % n
        
        # 尝试转换为字符串
        try:
            byte_len = (m.bit_length() + 7) // 8
            plaintext = m.to_bytes(byte_len, 'big').decode('utf-8', errors='replace')
            return f"解密成功! m = {m}\n明文: {plaintext}"
        except:
            return f"解密成功! m = {m}"
            
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def rsa_low_exponent_attack(c: int, e: int, n: int = None) -> str:
    """
    RSA 小指数攻击 (e=3)
    
    当公钥指数 e 很小（如 3）且明文较小时，
    可以直接对密文开 e 次方得到明文。
    
    Args:
        c: 密文
        e: 公钥指数 (通常是 3)
        n: 模数 (可选，如果 c < n 则不需要)
    
    Returns:
        解密结果
    """
    try:
        import gmpy2
        
        # 开 e 次方
        m, exact = gmpy2.iroot(c, e)
        
        if exact:
            m = int(m)
            try:
                byte_len = (m.bit_length() + 7) // 8
                plaintext = m.to_bytes(byte_len, 'big').decode('utf-8', errors='replace')
                return f"🎯 小指数攻击成功!\nm = {m}\n明文: {plaintext}"
            except:
                return f"🎯 小指数攻击成功! m = {m}"
        else:
            return f"❌ 无法精确开 {e} 次方，可能不适用小指数攻击"
            
    except ImportError:
        return "需要安装 gmpy2: pip install gmpy2"
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def rsa_wiener_attack(n: int, e: int) -> str:
    """
    RSA Wiener 攻击
    
    当私钥 d 较小时 (d < n^0.25/3)，可以通过连分数算法恢复 d。
    常见于 e 很大而 d 很小的情况。
    
    Args:
        n: RSA 模数
        e: 公钥指数
    
    Returns:
        攻击结果
    """
    try:
        def continued_fraction(n, d):
            """计算连分数展开"""
            cf = []
            while d:
                q = n // d
                cf.append(q)
                n, d = d, n - q * d
            return cf
        
        def convergents(cf):
            """计算渐近分数"""
            numerators = [0, 1]
            denominators = [1, 0]
            
            for q in cf:
                numerators.append(q * numerators[-1] + numerators[-2])
                denominators.append(q * denominators[-1] + denominators[-2])
            
            return list(zip(numerators[2:], denominators[2:]))
        
        # 计算 e/n 的连分数
        cf = continued_fraction(e, n)
        
        # 遍历渐近分数
        for k, d in convergents(cf):
            if k == 0:
                continue
            
            # 检查是否满足 RSA 条件
            if (e * d - 1) % k == 0:
                phi = (e * d - 1) // k
                
                # 求解 p + q = n - phi + 1
                s = n - phi + 1
                
                # 判别式
                discriminant = s * s - 4 * n
                
                if discriminant >= 0:
                    sqrt_disc = isqrt(discriminant)
                    if sqrt_disc * sqrt_disc == discriminant:
                        p = (s + sqrt_disc) // 2
                        q = (s - sqrt_disc) // 2
                        
                        if p * q == n:
                            return f"🎯 Wiener 攻击成功!\nd = {d}\np = {p}\nq = {q}"
        
        return "❌ Wiener 攻击失败，d 可能不够小"
        
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def rsa_common_factor_attack(n1: int, n2: int) -> str:
    """
    RSA 公因数攻击
    
    当两个不同的 n 共享一个质因数时，可以直接计算 gcd 得到该质因数。
    
    Args:
        n1: 第一个模数
        n2: 第二个模数
    
    Returns:
        攻击结果
    """
    try:
        p = gcd(n1, n2)
        
        if p == 1:
            return "❌ n1 和 n2 没有公因数，无法攻击"
        elif p == n1 or p == n2:
            return f"⚠️  n1 = n2，公因数为 {p}"
        else:
            q1 = n1 // p
            q2 = n2 // p
            return f"🎯 找到公因数!\np = {p}\nn1 = p * {q1}\nn2 = p * {q2}"
            
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def rsa_modulus_factorization(n: int, method: str = "auto") -> str:
    """
    RSA 模数分解工具
    
    尝试使用各种方法分解 n。
    
    Args:
        n: 要分解的模数
        method: 分解方法 (auto/trial/fermat/pollard)
    
    Returns:
        分解结果
    """
    try:
        n = int(n)
        
        if method == "auto":
            methods = ["trial", "fermat", "pollard"]
        else:
            methods = [method]
        
        for m in methods:
            if m == "trial":
                # 试除法
                limit = min(100000, isqrt(n) + 1)
                for p in range(2, limit):
                    if n % p == 0:
                        q = n // p
                        return f"🎯 试除法成功!\nn = {p} * {q}"
            
            elif m == "fermat":
                # Fermat 分解
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
                        return f"🎯 Fermat 分解成功!\nn = {p} * {q}"
                    a += 1
            
            elif m == "pollard":
                # Pollard's p-1 简单版本
                from math import gcd
                import random
                
                a = 2
                for i in range(2, 10000):
                    a = pow(a, i, n)
                    p = gcd(a - 1, n)
                    if 1 < p < n:
                        q = n // p
                        return f"🎯 Pollard p-1 成功!\nn = {p} * {q}"
        
        return f"❌ 无法分解 n={n}，可能需要更高级的分解方法或更大的计算资源"
        
    except Exception as e:
        return f"分解失败: {e}"


def get_rsa_advanced_tools() -> List[Any]:
    """获取高级 RSA 攻击工具"""
    return [
        rsa_common_modulus_attack,
        rsa_low_exponent_attack,
        rsa_wiener_attack,
        rsa_common_factor_attack,
        rsa_modulus_factorization,
    ]
