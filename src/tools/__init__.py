"""工具模块 - LangChain Tools"""

from .crypto_tools import get_crypto_tools
from .ctf_tools import get_ctf_tools
from .aes_tools import get_aes_tools
from .rsa_advanced_tools import get_rsa_advanced_tools
from .lattice_advanced import LATTICE_ADVANCED_TOOLS

def get_all_tools():
    """获取所有工具"""
    tools = []
    tools.extend(get_crypto_tools())
    tools.extend(get_ctf_tools())
    tools.extend(get_aes_tools())
    tools.extend(get_rsa_advanced_tools())
    tools.extend(LATTICE_ADVANCED_TOOLS)
    return tools

__all__ = [
    "get_crypto_tools", 
    "get_ctf_tools", 
    "get_aes_tools", 
    "get_rsa_advanced_tools",
    "get_all_tools",
    "LATTICE_ADVANCED_TOOLS"
]
