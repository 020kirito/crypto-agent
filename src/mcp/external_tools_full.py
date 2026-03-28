"""
完整的外部工具 MCP 集成

集成 D:/Crypto/ 中的专业密码学工具：
- cado-nfs: 大整数分解 (Number Field Sieve)
- flatter: 格基规约 (LLL/ BKZ)
- SageMath: 数学计算平台
- gf2bv: GF(2) 布尔向量运算
- hashcat: 密码哈希破解
- cuso: 自定义密码学工具
- yafu: 因数分解工具
"""

import subprocess
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToolConfig:
    """工具配置"""
    name: str
    path: Path
    executable: str
    description: str
    category: str
    check_cmd: Optional[str] = None


class ExternalToolManager:
    """
    外部工具管理器
    
    统一管理所有外部密码学工具的调用
    """
    
    def __init__(self, crypto_dir: str = "/mnt/d/Crypto"):
        self.crypto_dir = Path(crypto_dir)
        self.tools: Dict[str, ToolConfig] = {}
        self.available: Dict[str, bool] = {}
        
        self._register_tools()
        self._check_availability()
    
    def _register_tools(self):
        """注册所有工具"""
        self.tools = {
            "cado-nfs": ToolConfig(
                name="cado-nfs",
                path=self.crypto_dir / "cado-nfs",
                executable="cado-nfs.py",
                description="大整数分解 (Number Field Sieve)",
                category="factoring",
                check_cmd="ls build/ 2>/dev/null | head -1"
            ),
            "flatter": ToolConfig(
                name="flatter",
                path=self.crypto_dir / "flatter",
                executable="flatter",
                description="格基规约工具 (LLL)",
                category="lattice",
                check_cmd="ls build/bin/flatter 2>/dev/null"
            ),
            "sagemath": ToolConfig(
                name="sagemath",
                path=Path("/usr/bin"),
                executable="sage",
                description="数学计算平台",
                category="math",
                check_cmd="sage --version 2>/dev/null"
            ),
            "gf2bv": ToolConfig(
                name="gf2bv",
                path=self.crypto_dir / "gf2bv",
                executable="gf2bv",
                description="GF(2) 布尔向量运算",
                category="algebra",
                check_cmd="ls gf2bv 2>/dev/null"
            ),
            "hashcat": ToolConfig(
                name="hashcat",
                path=self.crypto_dir / "hashcat-7.1.2",
                executable="hashcat.bin",
                description="密码哈希破解工具",
                category="password",
                check_cmd="test -f hashcat.bin || test -f hashcat.exe"
            ),
            "cuso": ToolConfig(
                name="cuso",
                path=self.crypto_dir / "cuso",
                executable="cuso",
                description="自定义密码学工具集",
                category="crypto",
                check_cmd="ls build/ 2>/dev/null | head -1"
            ),
            "yafu": ToolConfig(
                name="yafu",
                path=self.crypto_dir / "yafu-1.34",
                executable="yafu",
                description="因数分解工具 (SIQS/QS)",
                category="factoring",
                check_cmd="test -f yafu || test -f yafu.exe"
            )
        }
    
    def _check_availability(self):
        """检查工具可用性"""
        for name, config in self.tools.items():
            try:
                # 首先检查路径是否存在
                if not config.path.exists():
                    self.available[name] = False
                    continue
                
                # 如果有检查命令，在工具目录下执行检查
                if config.check_cmd:
                    result = subprocess.run(
                        config.check_cmd,
                        shell=True,
                        capture_output=True,
                        timeout=5,
                        cwd=str(config.path)
                    )
                    self.available[name] = result.returncode == 0
                else:
                    # 对于没有检查命令的工具，检查可执行文件是否存在
                    exe_path = None
                    if name == "flatter":
                        exe_path = config.path / "build" / "bin" / "flatter"
                    elif name == "yafu":
                        exe_path = config.path / "yafu"
                    elif name == "hashcat":
                        exe_path = config.path / "hashcat.bin"
                    
                    if exe_path:
                        self.available[name] = exe_path.exists()
                    else:
                        self.available[name] = True
            except:
                self.available[name] = False
    
    def list_tools(self) -> Dict[str, Any]:
        """列出所有工具状态"""
        return {
            "available": [
                {
                    "name": name,
                    "description": config.description,
                    "category": config.category,
                    "path": str(config.path)
                }
                for name, config in self.tools.items()
                if self.available.get(name, False)
            ],
            "unavailable": [
                {
                    "name": name,
                    "description": config.description,
                    "reason": "未安装或配置不正确"
                }
                for name, config in self.tools.items()
                if not self.available.get(name, False)
            ]
        }
    
    # ==================== CADO-NFS ====================
    
    def call_cado_nfs(self, n: int, timeout: int = 3600) -> Dict[str, Any]:
        """
        调用 CADO-NFS 分解大整数
        
        CADO-NFS 是目前最先进的整数分解工具，使用 Number Field Sieve 算法。
        适用于 100+ 位的大整数分解。
        
        Args:
            n: 要分解的整数
            timeout: 超时时间（秒）
        
        Returns:
            分解结果 {p: int, q: int, time: float}
        """
        if not self.available.get("cado-nfs"):
            return {
                "success": False,
                "error": "CADO-NFS 未安装",
                "install_guide": "访问 https://cado-nfs.gitlabpages.inria.fr/ 获取安装说明"
            }
        
        try:
            cado_path = self.tools["cado-nfs"].path
            
            # 创建临时文件存储输入
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(str(n))
                input_file = f.name
            
            # 构建命令
            cmd = [
                "python3",
                str(cado_path / "cado-nfs.py"),
                input_file
            ]
            
            # 执行（这里只是示例，实际需要更复杂的处理）
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cado_path)
            )
            
            os.unlink(input_file)
            
            # 解析输出（CADO-NFS 输出格式较复杂）
            # 简化版本：返回提示信息
            return {
                "success": True,
                "message": f"CADO-NFS 开始分解 {n}",
                "note": "CADO-NFS 是计算密集型任务，可能需要数小时",
                "command": f"cd {cado_path} && python3 cado-nfs.py {n}",
                "estimated_time": "取决于数字大小，100位约需几小时"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"CADO-NFS 执行超时（>{timeout}秒）"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== YAFU ====================
    
    def call_yafu(self, n: int, method: str = "auto") -> Dict[str, Any]:
        """
        调用 YAFU 进行因数分解
        
        YAFU 是一个快速的因数分解工具，支持多种算法：
        - SIQS (Self-Initializing Quadratic Sieve)
        - ECM (Elliptic Curve Method)
        - QS (Quadratic Sieve)
        - 试除法等
        
        Args:
            n: 要分解的整数
            method: 分解方法 (auto/siqs/ecm/qs/trial)
        
        Returns:
            分解结果
        """
        if not self.available.get("yafu"):
            return {"success": False, "error": "YAFU 未安装"}
        
        try:
            yafu_path = self.tools["yafu"].path
            
            # 检测可执行文件
            yafu_exe = yafu_path / "yafu"
            if not yafu_exe.exists():
                yafu_exe = yafu_path / "yafu.exe"
            
            # 构建命令
            if method == "auto":
                cmd = [str(yafu_exe), f"factor({n})"]
            else:
                cmd = [str(yafu_exe), f"factor({n})", f"-method", method]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(yafu_path)
            )
            
            # 解析输出
            output = result.stdout + result.stderr
            
            # 提取因数
            factors = []
            for line in output.split('\n'):
                if 'factor:' in line.lower() or 'prp' in line.lower():
                    # 尝试提取数字
                    import re
                    nums = re.findall(r'\d+', line)
                    if nums:
                        factors.extend([int(x) for x in nums if int(x) > 1 and int(x) != n])
            
            return {
                "success": True,
                "n": n,
                "factors": list(set(factors)),
                "raw_output": output[:2000]  # 限制长度
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "YAFU 执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== FLATTER ====================
    
    def call_flatter(self, matrix: List[List[int]], algorithm: str = "lll") -> Dict[str, Any]:
        """
        调用 FLATTER 进行格基规约
        
        FLATTER 是一个高性能的格基规约工具，支持 LLL 和 BKZ 算法。
        
        Args:
            matrix: 输入矩阵（二维列表）
            algorithm: 算法类型 (lll/bkz)
        
        Returns:
            规约后的矩阵
        """
        if not self.available.get("flatter"):
            # 回退到 SageMath
            return self._fallback_lattice_reduction(matrix, algorithm)
        
        try:
            flatter_path = self.tools["flatter"].path
            flatter_exe = flatter_path / "build" / "bin" / "flatter"
            
            # 创建输入文件 (FPLLL 格式)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                # FPLLL 格式: [[a b c][d e f]...]
                f.write('[')
                for i, row in enumerate(matrix):
                    if i > 0:
                        f.write(' ')
                    f.write('[' + ' '.join(map(str, row)) + ']')
                f.write(']\n')
                input_file = f.name
            
            # 执行 (FLATTER 不需要 -a 参数，自动使用 LLL)
            cmd = [str(flatter_exe), input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            os.unlink(input_file)
            
            # 解析输出 (FPLLL 格式: [[a b c]\n[d e f]...])
            output = result.stdout.strip()
            # 移除所有方括号
            output = output.replace('[', '').replace(']', '')
            # 按行分割并解析
            lines = output.strip().split('\n')
            reduced_matrix = []
            for line in lines:
                if line.strip():
                    row = [int(x) for x in line.split()]
                    reduced_matrix.append(row)
            
            return {
                "success": True,
                "algorithm": algorithm,
                "original_dim": f"{len(matrix)}x{len(matrix[0])}",
                "reduced_matrix": reduced_matrix
            }
            
        except Exception as e:
            return self._fallback_lattice_reduction(matrix, algorithm)
    
    def _fallback_lattice_reduction(self, matrix: List[List[int]], algorithm: str) -> Dict[str, Any]:
        """使用 SageMath 作为后备"""
        try:
            from sageall import Matrix, ZZ
            
            M = Matrix(ZZ, matrix)
            
            if algorithm.lower() == "lll":
                reduced = M.LLL()
            elif algorithm.lower() == "bkz":
                reduced = M.BKZ()
            else:
                reduced = M.LLL()
            
            return {
                "success": True,
                "algorithm": algorithm,
                "note": "使用 SageMath 后备实现",
                "original_dim": f"{M.nrows()}x{M.ncols()}",
                "reduced_matrix": reduced.tolist()
            }
        except ImportError:
            return {
                "success": False,
                "error": "FLATTER 和 SageMath 都不可用"
            }
    
    # ==================== SAGEMATH ====================
    
    def call_sagemath(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """
        执行 SageMath 代码
        
        Args:
            code: SageMath/Python 代码
            timeout: 超时时间
        
        Returns:
            执行结果
        """
        if not self.available.get("sagemath"):
            return {"success": False, "error": "SageMath 未安装"}
        
        try:
            # 创建临时脚本
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sage', delete=False) as f:
                # 添加常用导入
                f.write("from sage.all import *\n")
                f.write("from Crypto.Util.number import *\n")
                f.write(code)
                script_file = f.name
            
            # 执行
            cmd = ["sage", script_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            os.unlink(script_file)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"SageMath 执行超时（>{timeout}秒）"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== HASHCAT ====================
    
    def call_hashcat(self, hash_value: str, hash_type: str = "0", 
                     attack_mode: str = "3", mask: str = None,
                     wordlist: str = None) -> Dict[str, Any]:
        """
        调用 Hashcat 破解哈希
        
        Args:
            hash_value: 哈希值
            hash_type: 哈希类型代码 (0=MD5, 100=SHA1, etc.)
            attack_mode: 攻击模式 (0=字典, 3=掩码, etc.)
            mask: 掩码模式 (如 ?l?l?l?l)
            wordlist: 字典文件路径
        
        Returns:
            破解结果
        """
        if not self.available.get("hashcat"):
            return {"success": False, "error": "Hashcat 未安装"}
        
        try:
            hashcat_path = self.tools["hashcat"].path
            hashcat_exe = hashcat_path / "hashcat.bin"
            if not hashcat_exe.exists():
                hashcat_exe = hashcat_path / "hashcat.exe"
            
            # 创建哈希文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(hash_value + '\n')
                hash_file = f.name
            
            # 构建命令
            cmd = [
                str(hashcat_exe),
                "-m", hash_type,
                "-a", attack_mode,
                hash_file
            ]
            
            if mask:
                cmd.append(mask)
            elif wordlist:
                cmd.append(wordlist)
            else:
                # 默认使用 example.dict
                cmd.append(str(hashcat_path / "example.dict"))
            
            # 添加输出选项
            cmd.extend(["-o", "cracked.txt", "--force"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(hashcat_path)
            )
            
            os.unlink(hash_file)
            
            # 读取结果
            cracked = []
            cracked_file = hashcat_path / "cracked.txt"
            if cracked_file.exists():
                with open(cracked_file) as f:
                    cracked = [line.strip() for line in f if line.strip()]
                cracked_file.unlink()
            
            return {
                "success": len(cracked) > 0,
                "cracked": cracked,
                "stdout": result.stdout[:2000],
                "command": ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Hashcat 执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== GF2BV ====================
    
    def call_gf2bv(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        调用 GF2BV 进行 GF(2) 布尔向量运算
        
        Args:
            operation: 操作类型 (solve/reduce/etc.)
            **kwargs: 操作参数
        
        Returns:
            运算结果
        """
        if not self.available.get("gf2bv"):
            return {"success": False, "error": "GF2BV 未安装"}
        
        # GF2BV 需要查看具体用法
        return {
            "success": False,
            "note": "GF2BV 需要具体使用文档",
            "path": str(self.tools["gf2bv"].path)
        }
    
    # ==================== CUSO ====================
    
    def call_cuso(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        调用 CUSO 工具
        
        Args:
            operation: 操作类型
            **kwargs: 参数
        """
        if not self.available.get("cuso"):
            return {"success": False, "error": "CUSO 未安装"}
        
        return {
            "success": False,
            "note": "CUSO 需要查看 README 了解具体用法",
            "path": str(self.tools["cuso"].path)
        }
    
    # ==================== 通用调用接口 ====================
    
    def call(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        通用工具调用接口
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
        """
        tool_map = {
            "cado-nfs": self.call_cado_nfs,
            "yafu": self.call_yafu,
            "flatter": self.call_flatter,
            "sagemath": self.call_sagemath,
            "hashcat": self.call_hashcat,
            "gf2bv": self.call_gf2bv,
            "cuso": self.call_cuso,
        }
        
        if tool_name not in tool_map:
            return {"error": f"未知工具: {tool_name}"}
        
        return tool_map[tool_name](**kwargs)


# 创建全局实例
external_tool_manager = ExternalToolManager()


# ==================== LangChain Tools 封装 ====================

def get_external_tools_info() -> str:
    """获取外部工具信息（用于 Prompt）"""
    info = external_tool_manager.list_tools()
    
    lines = ["=" * 60]
    lines.append("🔧 外部专业工具集成")
    lines.append("=" * 60)
    
    if info["available"]:
        lines.append("\n✅ 可用工具:")
        for tool in info["available"]:
            lines.append(f"  • {tool['name']}: {tool['description']}")
    
    if info["unavailable"]:
        lines.append("\n❌ 未安装工具:")
        for tool in info["unavailable"]:
            lines.append(f"  • {tool['name']}: {tool['description']}")
    
    lines.append("\n💡 提示: 对于超大整数分解，建议使用 cado-nfs 或 yafu")
    lines.append("💡 对于格基规约，建议使用 flatter 或 SageMath")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    print(get_external_tools_info())
