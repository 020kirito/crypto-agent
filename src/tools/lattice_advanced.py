"""
高级格密码工具

提供 lattice-based cryptography 的高级攻击工具:
- BDD (Bounded Distance Decoding) 攻击
- SVP (Shortest Vector Problem) 求解
- CVP (Closest Vector Problem) 求解
- NTRU攻击
- LWE攻击
- Coppersmith方法实现
"""

from typing import List, Tuple, Optional, Union
from langchain.tools import tool
import json


def _sagemath_execute(code: str) -> str:
    """执行SageMath代码"""
    try:
        from ..mcp.external_tools_full import external_tool_manager
        return external_tool_manager.call_sagemath(code)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def lattice_bdd_attack(basis: str, target: str, radius: float = None) -> str:
    """
    BDD (Bounded Distance Decoding) 攻击
    
    当目标向量距离格点很近时，恢复原始格点。
    常用于攻击GGH、NTRU等密码系统。
    
    Args:
        basis: 格基矩阵（JSON格式列表的列表）
        target: 目标向量（JSON格式列表）
        radius: 搜索半径（可选，自动计算）
    
    Returns:
        解码后的格点向量
    
    示例:
        basis: "[[4, 0], [0, 4]]"
        target: "[3.9, 0.1]"
    """
    sage_code = f"""
import json

# 解析输入
basis = json.loads('{basis}')
target = json.loads('{target}')

# 构造格
n = len(basis)
M = Matrix(ZZ, basis)
L = M.LLL()

# 使用Babai最近平面算法
v = vector(RR, target)

# 计算CVP近似解
w = v
coeffs = []
for i in reversed(range(n)):
    b = L[i]
    c = (w.dot_product(b)) / (b.dot_product(b))
    c_rounded = round(c)
    coeffs.append(c_rounded)
    w = w - c_rounded * vector(RR, b)

# 重构格点
coeffs.reverse()
result = sum(c * vector(M[i]) for i, c in enumerate(coeffs))

print(json.dumps({{
    "lattice_point": list(result),
    "coefficients": coeffs,
    "distance": float((vector(target) - result).norm())
}}))
"""
    return _sagemath_execute(sage_code)


@tool
def lattice_cvp_solver(basis: str, target: str, method: str = "babai") -> str:
    """
    CVP (Closest Vector Problem) 求解器
    
    在格中找到距离目标向量最近的格点。
    
    Args:
        basis: 格基矩阵（JSON格式）
        target: 目标向量（JSON格式）
        method: 算法 (babai/round_off/enumeration)
    
    Returns:
        最近格点和距离
    
    示例:
        basis: "[[10, 0], [0, 10]]"
        target: "[12.3, 7.8]"
        method: "babai"
    """
    sage_code = f"""
import json

basis = json.loads('{basis}')
target = json.loads('{target}')
method = "{method}"

M = Matrix(ZZ, basis)
L = M.LLL()
t = vector(RR, target)
n = len(target)

if method == "babai":
    # Babai最近平面算法
    result = vector(ZZ, [0] * n)
    remaining = t
    
    for i in reversed(range(n)):
        b_i = vector(RR, L[i])
        c = remaining.dot_product(b_i) / b_i.dot_product(b_i)
        c_rounded = round(c)
        result += c_rounded * vector(ZZ, M[i])
        remaining -= c_rounded * b_i
    
elif method == "round_off":
    # Round-off算法
    L_float = Matrix(RR, L)
    t_float = vector(RR, t)
    coeffs = L_float.solve_left(t_float)
    coeffs_rounded = [round(c) for c in coeffs]
    result = sum(c * vector(ZZ, M[i]) for i, c in enumerate(coeffs_rounded))

else:
    # 默认使用Babai
    result = vector(ZZ, [0] * n)
    remaining = t
    for i in reversed(range(n)):
        b_i = vector(RR, L[i])
        c = remaining.dot_product(b_i) / b_i.dot_product(b_i)
        result += round(c) * vector(ZZ, M[i])
        remaining -= round(c) * b_i

distance = float((t - result).norm())

print(json.dumps({{
    "closest_vector": list(result),
    "distance": distance,
    "method": method
}}))
"""
    return _sagemath_execute(sage_code)


@tool
def lattice_svp_solver(basis: str, block_size: int = 10) -> str:
    """
    SVP (Shortest Vector Problem) 求解器
    
    使用BKZ算法找到格中的短向量。
    
    Args:
        basis: 格基矩阵（JSON格式）
        block_size: BKZ块大小（越大越好但越慢）
    
    Returns:
        找到的最短向量
    
    示例:
        basis: "[[100, 0], [50, 1]]"
        block_size: 10
    """
    sage_code = f"""
import json

basis = json.loads('{basis}')
block_size = {block_size}

M = Matrix(ZZ, basis)

# 先LLL约减
M_lll = M.LLL()

# 使用BKZ
if block_size >= 2 and block_size <= M.nrows():
    M_bkz = M_lll.BKZ(block_size=block_size)
else:
    M_bkz = M_lll

# 找到最短向量
shortest = None
min_norm = float('inf')

for row in M_bkz:
    norm = float(row.norm())
    if norm > 0 and norm < min_norm:
        min_norm = norm
        shortest = row

if shortest is None:
    shortest = M_bkz[0]
    min_norm = float(shortest.norm())

print(json.dumps({{
    "shortest_vector": list(shortest),
    "norm": min_norm,
    "block_size": block_size
}}))
"""
    return _sagemath_execute(sage_code)


@tool
def ntru_attack(N: int, p: int, q: int, h: str, num_samples: int = 5) -> str:
    """
    NTRU格攻击
    
    通过构造NTRU格并使用LLL/BKZ恢复私钥。
    
    Args:
        N: 多项式次数
        p: 小模数
        q: 大模数
        h: 公钥多项式系数（JSON格式列表）
        num_samples: 样本数量
    
    Returns:
        恢复的私钥候选
    
    示例:
        N: 7
        p: 3
        q: 41
        h: "[6, 32, 15, 8, 30, 17, 35]"
    """
    sage_code = f"""
import json

N = {N}
p = {p}
q = {q}
h = json.loads('{h}')

# 构造NTRU格
# 格基: [[I, H], [0, qI]]
# 其中H是h的循环矩阵

R = ZZ

# 构造循环矩阵H
H = Matrix(ZZ, N, N)
for i in range(N):
    for j in range(N):
        H[i, j] = h[(j - i) % N]

# 构造格基
I = Matrix.identity(ZZ, N)
Z = Matrix.zero(ZZ, N, N)
qI = q * I

# 组合格基 [[I, H], [0, qI]]
top = I.augment(H)
bottom = Z.augment(qI)
M = top.stack(bottom)

# LLL约减
L = M.LLL()

# 搜索短向量（私钥候选）
candidates = []
for i in range(min(10, L.nrows())):
    v = L[i]
    # NTRU私钥形式: (f, g) 其中 g = f * h mod q
    f = list(v[:N])
    g = list(v[N:])
    
    # 检查是否是有效的私钥候选
    if all(abs(x) <= p for x in f) and all(abs(x) <= p for x in g):
        candidates.append({{
            "f": f,
            "g": g,
            "norm": float(v.norm())
        }})

print(json.dumps({{
    "N": N,
    "p": p,
    "q": q,
    "candidates": candidates[:{num_samples}],
    "lattice_dimension": M.nrows()
}}))
"""
    return _sagemath_execute(sage_code)


@tool
def coppersmith_univariate(polynomial: str, modulus: str, 
                           known_bits: int, total_bits: int) -> str:
    """
    Coppersmith方法 - 单变量情况
    
    当知道RSA明文的很大一部分时，恢复完整明文。
    
    Args:
        polynomial: 多项式系数列表（从常数项开始）
        modulus: 模数N
        known_bits: 已知比特数
        total_bits: 总比特数
    
    Returns:
        找到的小根
    
    示例:
        polynomial: "[-c, e*n^(e-1), ...]"  # (x + known)^e - c
        modulus: "N"
        known_bits: 400
        total_bits: 1024
    """
    sage_code = f"""
import json

# 构造多项式 f(x) = (x + known)^e - c mod N
# 这里简化实现，实际需要构造正确的多项式

N = {modulus}
X = 2^({total_bits} - {known_bits})  # 未知部分的上界

# 实际实现需要使用coppersmith算法
# 这里提供框架

result = {{
    "method": "Coppersmith",
    "modulus_bits": {total_bits},
    "unknown_bits": {total_bits} - {known_bits},
    "status": "需要使用SageMath的small_roots实现",
    "note": "实际攻击需要构造正确的多项式并调用small_roots()"
}}

print(json.dumps(result))
"""
    return _sagemath_execute(sage_code)


@tool
def hnp_solver(p: str, samples: str, bound: int) -> str:
    """
    隐藏数问题 (HNP) 求解器
    
    用于攻击DSA/ECDSA的nonce泄露。
    
    Args:
        p: 素数模数
        samples: 样本列表 [(a_i, b_i)] 其中 b_i ≡ a_i*x + e_i (mod p)
        bound: 误差上界 |e_i| < bound
    
    Returns:
        恢复的秘密x
    
    示例:
        p: "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF..."
        samples: "[[a1, b1], [a2, b2], ...]"
        bound: 2^64
    """
    sage_code = f"""
import json

p = {p}
samples = json.loads('{samples}')
B = {bound}

n = len(samples)

# 构造HNP格
# [p, 0, ..., 0, 0]
# [0, p, ..., 0, 0]
# [...       ...  ]
# [a1, a2, ..., an, B/p]
# [b1, b2, ..., bn, B/p]

# 实际构造矩阵
M = Matrix(ZZ, n + 1, n + 1)

# 对角线放p
for i in range(n):
    M[i, i] = p

# 最后一行
for i, (a, b) in enumerate(samples):
    M[n, i] = a

M[n, n] = B

# LLL约减
L = M.LLL()

# 从短向量恢复x
# 最后一列应该是 B*x/p
recovered = None
for row in L:
    if row[-1] != 0:
        # 尝试恢复x
        candidate = (row[-1] * p) // B
        # 验证
        valid = True
        for a, b in samples:
            error = (b - a * candidate) % p
            if error > p//2:
                error = p - error
            if error >= B:
                valid = False
                break
        if valid:
            recovered = candidate % p
            break

print(json.dumps({{
    "p": str(p),
    "samples": n,
    "bound": B,
    "recovered_x": str(recovered) if recovered else None,
    "success": recovered is not None
}}))
"""
    return _sagemath_execute(sage_code)


@tool
def lattice_ghsv_estimator(dimension: int, log_determinant: float) -> str:
    """
    GHSV格困难度估计器
    
    估计格的Hermite因子和SVP困难度。
    
    Args:
        dimension: 格维度
        log_determinant: log(det(L))
    
    Returns:
        安全估计
    
    示例:
        dimension: 512
        log_determinant: 5120.0
    """
    import math
    
    n = dimension
    ld = log_determinant
    
    # Hermite因子 δ^n = ||b1|| / det(L)^(1/n)
    # 对于随机格，预期最短向量长度 ≈ GH(L) = sqrt(n/(2πe)) * det(L)^(1/n)
    
    # 高斯启发式
    gh_constant = math.sqrt(n / (2 * math.pi * math.e))
    det_root = math.exp(ld / n)
    expected_svp = gh_constant * det_root
    
    # BKZ复杂度估计
    # log(BKZ_cost) ≈ 0.292 * β * log(β) for Core-SVP
    
    estimates = {
        "dimension": n,
        "log_determinant": ld,
        "gaussian_heuristic": expected_svp,
        "security_estimates": {
            "svp_classical": f"需要约 {n} 维BKZ",
            "svp_quantum": f"需要约 {n//2} 维BKZ（量子加速）",
            "note": "实际安全性还依赖于具体应用"
        }
    }
    
    return json.dumps(estimates, indent=2)


# 工具列表
LATTICE_ADVANCED_TOOLS = [
    lattice_bdd_attack,
    lattice_cvp_solver,
    lattice_svp_solver,
    ntru_attack,
    coppersmith_univariate,
    hnp_solver,
    lattice_ghsv_estimator,
]
