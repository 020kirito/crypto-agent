"""
椭圆曲线密码学 (ECC) 攻击工具集

来源:
- ECC's smart attack.md
- ECC解题思路大全.md
"""

from typing import List, Any
from langchain.tools import tool


@tool
def ecc_smart_attack(p: int, a: int, b: int, px: int, py: int, qx: int, qy: int) -> str:
    """
    ECC Smart Attack - 针对异常椭圆曲线的攻击
    
    当椭圆曲线的阶等于素数 p 时 (E.order() == p)，
    可以利用 p-进数域将 ECDLP 问题转化为加法群上的问题。
    
    攻击原理:
    1. 将椭圆曲线从 GF(p) 提升到 Q_p(p-adic 域)
    2. 利用 p-进对数映射 φ(P) = -x_P/y_P
    3. 计算 k = φ(Q)/φ(P)
    
    Args:
        p: 有限域的素数模数
        a: 椭圆曲线参数 a
        b: 椭圆曲线参数 b
        px, py: 点 P 的坐标
        qx, qy: 点 Q = k*P 的坐标
    
    Returns:
        私钥 k
    
    Example:
        >>> ecc_smart_attack(
        ...     p=11093300438765357787693823122068501933326829181518693650897090781749379503427651954028543076247583697669597230934286751428880673539155279232304301123931419,
        ...     a=490963434153515882934487973185142842357175523008183292296815140698999054658777820556076794490414610737654365807063916602037816955706321036900113929329671,
        ...     b=7668542654793784988436499086739239442915170287346121645884096222948338279165302213440060079141960679678526016348025029558335977042712382611197995002316466,
        ...     px=5554022717099360648521077915206867958510713570728935648722513803012487951670103349974914076311463683401346041009548809409633656449393930718778345589173915,
        ...     py=1266078318886560129287459416353113688542197996795961235340234481614474504159805769053978291478602425874624451558101353431723090978689270131228854203647770,
        ...     qx=2758577082514053081281256667519462531364634668223896872592517478354667723237248507295586566258918736939764700935831769480917509906899250634810284495146946,
        ...     qy=511778894973388402517121634149232729267586460552999583843974221520798491852352254441185282292648216492508999730064294835066451755699876682807265675847421
        ... )
    """
    try:
        from sageall import EllipticCurve, GF, Qp, ZZ, RealField, randint
        
        # 创建椭圆曲线
        E = EllipticCurve(GF(p), [a, b])
        P = E(px, py)
        Q = E(qx, qy)
        
        # 检查阶是否等于 p
        if E.order() != p:
            return f"❌ Smart Attack 不适用: E.order() = {E.order()} != p = {p}"
        
        # 提升到 p-进数域
        Eqp = EllipticCurve(Qp(p, 2), [ZZ(t) + randint(0, p) * p for t in E.a_invariants()])
        
        # 提升点 P
        P_Qps = Eqp.lift_x(ZZ(P.xy()[0]), all=True)
        for P_Qp in P_Qps:
            if GF(p)(P_Qp.xy()[1]) == P.xy()[1]:
                break
        
        # 提升点 Q
        Q_Qps = Eqp.lift_x(ZZ(Q.xy()[0]), all=True)
        for Q_Qp in Q_Qps:
            if GF(p)(Q_Qp.xy()[1]) == Q.xy()[1]:
                break
        
        # 计算 p 倍点
        p_times_P = p * P_Qp
        p_times_Q = p * Q_Qp
        
        # 计算 p-进对数
        x_P, y_P = p_times_P.xy()
        x_Q, y_Q = p_times_Q.xy()
        
        phi_P = -(x_P / y_P)
        phi_Q = -(x_Q / y_Q)
        
        # 计算私钥
        k = phi_Q / phi_P
        k_int = ZZ(k)
        
        # 验证
        if k_int * P == Q:
            return f"🎯 Smart Attack 成功!\n私钥 k = {k_int}"
        else:
            return f"⚠️ 计算结果可能不正确: k = {k_int}"
            
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"攻击失败: {e}"


@tool
def ecc_check_order(p: int, a: int, b: int) -> str:
    """
    检查椭圆曲线的阶
    
    判断椭圆曲线是否适合 Smart Attack 或 MOV Attack
    
    Args:
        p: 素数模数
        a, b: 椭圆曲线参数
    
    Returns:
        阶的信息和攻击建议
    """
    try:
        from sageall import EllipticCurve, GF, factor
        
        E = EllipticCurve(GF(p), [a, b])
        order = E.order()
        
        result = [f"椭圆曲线阶: {order}"]
        result.append(f"阶的因数分解: {factor(order)}")
        
        # 检查 Smart Attack 条件
        if order == p:
            result.append("✅ 满足 Smart Attack 条件 (E.order() == p)")
        
        # 检查 MOV Attack 条件
        if order == p + 1:
            result.append("✅ 满足 MOV Attack 条件 (E.order() == p + 1)")
        
        # 检查异常曲线
        if order == p:
            result.append("⚠️  异常曲线 (Anomalous Curve)")
        
        return "\n".join(result)
        
    except ImportError:
        return "需要 SageMath 环境"
    except Exception as e:
        return f"检查失败: {e}"


def get_ecc_tools() -> List[Any]:
    """获取所有 ECC 工具"""
    return [
        ecc_smart_attack,
        ecc_check_order,
    ]
