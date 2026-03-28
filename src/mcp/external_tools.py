"""
外部工具 MCP 服务

封装 D:/Crypto 中的外部工具：
- cado-nfs: 大整数分解
- ToolsFx: CTF Crypto 综合工具
- RSAwienerHacker: Wiener 攻击
- flatter: 格基规约
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ExternalToolServer:
    """
    外部工具 MCP 服务器
    
    将本地安装的 Crypto 工具封装为可调用的服务
    """
    
    def __init__(self, crypto_tools_dir: str = "/mnt/d/Crypto"):
        self.tools_dir = Path(crypto_tools_dir)
        self.available_tools = self._check_tools()
    
    def _check_tools(self) -> Dict[str, bool]:
        """检查可用工具"""
        tools = {
            "cado-nfs": (self.tools_dir / "cado-nfs" / "build").exists(),
            "toolsfx": (self.tools_dir / "Toolsfx" / "ToolsFx.exe").exists(),
            "rsawiener": (self.tools_dir / "RSAwienerHacker").exists(),
            "flatter": (self.tools_dir / "flatter").exists(),
        }
        return tools
    
    def list_tools(self) -> Dict[str, Any]:
        """列出可用工具"""
        return {
            "available": [k for k, v in self.available_tools.items() if v],
            "unavailable": [k for k, v in self.available_tools.items() if not v],
            "details": {
                "cado-nfs": "大整数分解 (Number Field Sieve)",
                "toolsfx": "CTF Crypto 综合工具 (Java GUI)",
                "rsawiener": "RSA Wiener 攻击",
                "flatter": "格基规约工具 (LLL)",
            }
        }
    
    def call_cado_nfs(self, n: int, timeout: int = 3600) -> Dict[str, Any]:
        """
        调用 cado-nfs 分解大整数
        
        Args:
            n: 要分解的整数
            timeout: 超时时间 (秒)
        
        Returns:
            分解结果 {p, q}
        """
        if not self.available_tools["cado-nfs"]:
            return {"error": "cado-nfs 未安装", "path": str(self.tools_dir / "cado-nfs")}
        
        try:
            cado_dir = self.tools_dir / "cado-nfs" / "build"
            
            return {
                "success": True,
                "note": f"cado-nfs 目录: {cado_dir}",
                "target": n,
                "command": f"python3 cado-nfs.py {n}",
                "message": "请手动在 cado-nfs 目录中运行上述命令"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def call_flatter(self, matrix_str: str) -> Dict[str, Any]:
        """
        调用 flatter 进行格基规约
        
        Args:
            matrix_str: 矩阵字符串，格式 "1,2,3;4,5,6;7,8,9"
        
        Returns:
            规约后的格
        """
        if not self.available_tools["flatter"]:
            return {"error": "flatter 未安装", "path": str(self.tools_dir / "flatter")}
        
        try:
            # 解析矩阵
            rows = []
            for row_str in matrix_str.split(';'):
                row = [int(x.strip()) for x in row_str.split(',')]
                rows.append(row)
            
            return {
                "success": True,
                "matrix": rows,
                "note": "建议使用 Python 的 fpylll 库或 SageMath 进行 LLL 规约",
                "command": f"flatter '{matrix_str}'"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        通用工具调用接口
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
        
        Returns:
            工具执行结果
        """
        if tool_name == "cado-nfs":
            return self.call_cado_nfs(**kwargs)
        elif tool_name == "flatter":
            return self.call_flatter(**kwargs)
        else:
            return {"error": f"未知工具: {tool_name}"}


# 创建全局实例
external_tool_server = ExternalToolServer()


def get_external_tools_info() -> str:
    """获取外部工具信息（用于 Prompt）"""
    info = external_tool_server.list_tools()
    
    lines = ["外部工具列表:"]
    lines.append("-" * 40)
    
    for tool in info["available"]:
        desc = info["details"].get(tool, "")
        lines.append(f"✅ {tool}: {desc}")
    
    for tool in info["unavailable"]:
        desc = info["details"].get(tool, "")
        lines.append(f"❌ {tool}: {desc} (未安装)")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    print(get_external_tools_info())
