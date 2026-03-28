"""
MCP 外部工具封装

将 D:/Crypto 中的专业工具封装为 LangChain Tools
供 Agent 直接调用
"""

from typing import List, Any, Optional
from langchain.tools import tool
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp.external_tools_full import external_tool_manager


@tool
def external_factor_n(n: int, tool: str = "auto") -> str:
    """
    使用外部专业工具分解大整数
    
    当内置的 RSA 工具无法分解大整数时，调用外部专业工具：
    - yafu: 适合 50-100 位整数 (SIQS/QS 算法)
    - cado-nfs: 适合 100+ 位整数 (Number Field Sieve)
    - auto: 自动选择
    
    Args:
        n: 要分解的整数
        tool: 使用的工具 (yafu/cado-nfs/auto)
    
    Returns:
        分解结果
    
    Example:
        >>> external_factor_n(3233)
        "3233 = 61 * 53"
        
        >>> external_factor_n(1234567890123456789, tool="yafu")
        "分解结果: [3, 3, 101, 3541, 3607, 3803, 27961]"
    """
    try:
        # 根据大小自动选择工具
        bit_length = n.bit_length()
        
        if tool == "auto":
            if bit_length > 100:
                tool = "cado-nfs"
            else:
                tool = "yafu"
        
        if tool == "yafu":
            result = external_tool_manager.call_yafu(n)
            if result.get("success"):
                factors = result.get("factors", [])
                if factors:
                    return f"🎯 YAFU 分解成功!\nn = {n}\n因数: {factors}\n\n原始输出:\n{result.get('raw_output', '')[:500]}"
                else:
                    return f"⚠️  YAFU 运行完成但未找到因数\n原始输出:\n{result.get('raw_output', '')[:500]}"
            else:
                return f"❌ YAFU 失败: {result.get('error', 'Unknown error')}"
        
        elif tool == "cado-nfs":
            result = external_tool_manager.call_cado_nfs(n)
            return f"📋 CADO-NFS 任务已启动\n{result.get('message', '')}\n命令: {result.get('command', 'N/A')}"
        
        else:
            return f"❌ 未知工具: {tool}"
            
    except Exception as e:
        return f"❌ 调用外部工具失败: {e}"


@tool
def external_lattice_reduction(matrix_str: str, algorithm: str = "lll") -> str:
    """
    使用外部工具进行格基规约
    
    当需要高性能的 LLL/BKZ 规约时，调用 FLATTER 或 SageMath。
    
    Args:
        matrix_str: 矩阵字符串，格式 "1,2,3;4,5,6;7,8,9"
        algorithm: 算法 (lll/bkz)
    
    Returns:
        规约后的矩阵
    
    Example:
        >>> external_lattice_reduction("1,2,3;4,5,6;7,8,9", algorithm="lll")
        "规约成功! 结果矩阵: [...]"
    """
    try:
        # 解析矩阵
        rows = []
        for row_str in matrix_str.split(';'):
            row = [int(x.strip()) for x in row_str.split(',')]
            rows.append(row)
        
        result = external_tool_manager.call_flatter(rows, algorithm)
        
        if result.get("success"):
            reduced = result.get("reduced_matrix", [])
            return f"🎯 格基规约成功!\n算法: {result.get('algorithm')}\n原始维度: {result.get('original_dim')}\n\n规约后矩阵:\n{reduced}"
        else:
            return f"❌ 规约失败: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ 解析矩阵失败: {e}"


@tool
def external_sage_execute(code: str, timeout: int = 60) -> str:
    """
    执行 SageMath 代码
    
    当需要高级数学计算时，调用 SageMath。
    
    Args:
        code: SageMath/Python 代码
        timeout: 超时时间（秒）
    
    Returns:
        执行结果
    
    Example:
        >>> external_sage_execute("print(factor(3233))")
        "61 * 53"
        
        >>> code = "E = EllipticCurve(GF(101), [0, 1]); print(E.order())"
        >>> external_sage_execute(code)
        "102"
    """
    result = external_tool_manager.call_sagemath(code, timeout)
    
    if result.get("success"):
        output = result.get("stdout", "")
        if output.strip():
            return f"✅ SageMath 执行成功!\n\n输出:\n{output}"
        else:
            return f"✅ SageMath 执行成功!\n(无输出)"
    else:
        error = result.get("error", "Unknown error")
        stderr = result.get("stderr", "")
        return f"❌ SageMath 执行失败:\n错误: {error}\n\n错误输出:\n{stderr}"


@tool
def external_hash_crack(hash_value: str, hash_type: str = "0", pattern: str = None) -> str:
    """
    使用 Hashcat 破解密码哈希
    
    支持多种哈希类型和攻击模式。
    
    Args:
        hash_value: 哈希值
        hash_type: 哈希类型代码 (0=MD5, 100=SHA1, 1400=SHA256)
        pattern: 密码模式 (如 "?l?l?l?l" 表示4位小写字母)
    
    Returns:
        破解结果
    
    Example:
        >>> external_hash_crack("5f4dcc3b5aa765d61d8327deb882cf99", hash_type="0")
        "破解成功: password"
    
    哈希类型代码参考:
    - 0: MD5
    - 100: SHA1
    - 1400: SHA256
    - 1700: SHA512
    - 3200: bcrypt
    - 1800: sha512crypt
    """
    if not pattern:
        pattern = "?l?l?l?l?l?l?l?l"  # 默认8位小写字母
    
    result = external_tool_manager.call_hashcat(
        hash_value=hash_value,
        hash_type=hash_type,
        attack_mode="3",
        mask=pattern
    )
    
    if result.get("success"):
        cracked = result.get("cracked", [])
        return f"🎯 Hashcat 破解成功!\n结果: {cracked}"
    else:
        return f"❌ 破解失败或未找到:\n{result.get('error', 'No result')}\n\n提示: 尝试调整 pattern 或使用字典攻击"


@tool
def list_external_tools() -> str:
    """
    列出所有可用的外部工具
    
    返回 D:/Crypto/ 中安装的专业工具的列表和状态。
    """
    info = external_tool_manager.list_tools()
    
    lines = ["=" * 60]
    lines.append("🔧 D:/Crypto 外部工具状态")
    lines.append("=" * 60)
    
    if info["available"]:
        lines.append("\n✅ 可用工具:")
        for tool in info["available"]:
            lines.append(f"  • {tool['name']}")
            lines.append(f"    描述: {tool['description']}")
            lines.append(f"    路径: {tool['path']}")
            lines.append("")
    
    if info["unavailable"]:
        lines.append("\n❌ 未安装工具:")
        for tool in info["unavailable"]:
            lines.append(f"  • {tool['name']}: {tool['description']}")
    
    lines.append("\n💡 使用说明:")
    lines.append("  • 大整数分解: external_factor_n(n, tool='yafu')")
    lines.append("  • 格基规约: external_lattice_reduction(matrix, algorithm='lll')")
    lines.append("  • 数学计算: external_sage_execute(code)")
    lines.append("  • 哈希破解: external_hash_crack(hash, hash_type='0')")
    
    return "\n".join(lines)


def get_mcp_tools() -> List[Any]:
    """获取所有 MCP 外部工具"""
    return [
        external_factor_n,
        external_lattice_reduction,
        external_sage_execute,
        external_hash_crack,
        list_external_tools,
    ]
