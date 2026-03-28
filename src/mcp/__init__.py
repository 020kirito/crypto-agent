"""MCP (Model Context Protocol) 模块

将外部工具封装为 MCP 服务，供 Agent 调用
"""

from .external_tools import ExternalToolServer, get_external_tools_info

__all__ = ["ExternalToolServer", "get_external_tools_info"]
