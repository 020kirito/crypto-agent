"""
CTF Crypto Agent - 基于 LangChain 1.x

这是项目的核心，使用 LangChain 的 Agent 框架来构建 CTF 解题 Agent。
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# LangChain 1.x 导入
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# 导入工具
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.crypto_tools import get_crypto_tools
from tools.ctf_tools import get_ctf_tools
from tools.aes_tools import get_aes_tools
from tools.rsa_advanced_tools import get_rsa_advanced_tools
from tools.lfsr_tools import get_lfsr_tools
from tools.lwe_tools import get_lwe_tools
from tools.classic_cipher_tools import get_classic_cipher_tools
from tools.ecc_tools import get_ecc_tools
from tools.hnp_tools import get_hnp_tools
from tools.ntru_tools import get_ntru_tools
from tools.coppersmith_tools import get_coppersmith_tools
from tools.mcp_tools import get_mcp_tools


class CryptoAgent:
    """CTF 密码学 Agent"""
    
    def __init__(
        self,
        model_name: str = "moonshot-v1-8k",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        trajectory_dir: str = "data/trajectories"
    ):
        self.model_name = model_name
        self.trajectory_dir = Path(trajectory_dir)
        self.trajectory_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 LLM
        self.llm = self._create_llm(api_key, temperature)
        
        # 获取所有工具
        self.tools = self._load_tools()
        
        # 创建 Agent
        self.agent = self._create_agent()
        
        print(f"✅ Agent 初始化完成 (模型: {model_name})")
        print(f"🔧 已加载 {len(self.tools)} 个工具")
    
    def _create_llm(self, api_key: Optional[str], temperature: float):
        """创建 LLM 客户端"""
        
        is_kimi = (
            "kimi" in self.model_name.lower() 
            or "moonshot" in self.model_name.lower()
            or os.getenv("DEFAULT_MODEL", "").lower() == "kimi"
        )
        
        if is_kimi:
            api_key = api_key or os.getenv("KIMI_API_KEY")
            if not api_key:
                raise ValueError(
                    "请设置 KIMI_API_KEY 环境变量\n"
                    "获取方式: https://platform.moonshot.cn/"
                )
            
            print(f"🌙 使用 Kimi API (模型: {self.model_name})")
            
            return ChatOpenAI(
                model=self.model_name or "moonshot-v1-8k",
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1",
                temperature=temperature,
            )
        else:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "请设置 OPENAI_API_KEY 环境变量\n"
                    "获取方式: https://platform.openai.com/"
                )
            
            print(f"🤖 使用 OpenAI API (模型: {self.model_name})")
            
            return ChatOpenAI(
                model=self.model_name or "gpt-3.5-turbo",
                api_key=api_key,
                temperature=temperature,
            )
    
    def _load_tools(self) -> List[Any]:
        """加载所有工具"""
        tools = []
        tools.extend(get_crypto_tools())
        tools.extend(get_ctf_tools())
        tools.extend(get_aes_tools())
        tools.extend(get_rsa_advanced_tools())
        tools.extend(get_lfsr_tools())
        tools.extend(get_lwe_tools())
        tools.extend(get_classic_cipher_tools())
        tools.extend(get_ecc_tools())
        tools.extend(get_hnp_tools())
        tools.extend(get_ntru_tools())
        tools.extend(get_coppersmith_tools())
        tools.extend(get_mcp_tools())
        return tools
    
    def _create_agent(self):
        """创建 LangChain Agent"""
        
        # 构建工具描述
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description[:80]}..."
            for tool in self.tools
        ])
        
        system_prompt = f"""你是一个专业的 CTF 密码学解题专家。

你的任务是根据题目描述，分析题目类型，选择合适的工具来解决问题。

可用工具：
{tools_desc}

解题策略：
1. 分析题目类型（RSA、AES、古典密码等）
2. 识别关键参数（n, e, c, 密文等）
3. 选择合适的工具进行解密
4. 验证结果是否符合 flag 格式（通常包含 flag{{...}}）

重要提示：
- 你可以调用多个工具
- 如果一种方法失败，尝试其他方法
- flag 格式通常为 flag{{...}}
- 仔细分析工具返回的结果
"""
        
        # LangChain 1.x 创建 Agent
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            debug=False,
        )
        
        return agent
    
    def solve(self, challenge_description: str, challenge_name: str = "unknown") -> Dict[str, Any]:
        """解决 CTF 题目"""
        print(f"\n{'='*60}")
        print(f"🎯 开始解题: {challenge_name}")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        
        input_text = f"""请解决以下 CTF 密码学题目：

{challenge_description}

请分析题目，使用合适的工具获取 flag。
如果成功找到 flag，请在最后明确输出：FINAL ANSWER: flag{{...}}
"""
        
        try:
            # LangChain 1.x 调用方式
            result = self.agent.invoke({
                "messages": [{"role": "user", "content": input_text}]
            })
            
            # 提取输出
            output = ""
            if isinstance(result, dict) and "messages" in result:
                # 取最后一条消息
                messages = result["messages"]
                if messages:
                    last_msg = messages[-1]
                    # AIMessage 对象使用 .content 属性
                    if hasattr(last_msg, 'content'):
                        output = last_msg.content
                    else:
                        output = str(last_msg)
            else:
                output = str(result)
            
            flag = self._extract_flag(output)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            solution_result = {
                "success": flag is not None,
                "flag": flag,
                "output": output,
                "challenge_name": challenge_name,
                "elapsed_time": elapsed,
                "timestamp": datetime.now().isoformat(),
            }
            
            self._save_trajectory(solution_result)
            
            # 打印详细输出
            print(f"\n📤 Agent 输出:")
            print("-" * 60)
            print(output)
            print("-" * 60)
            
            if flag:
                print(f"\n✅ 成功! 找到 flag: {flag}")
            else:
                print(f"\n❌ 未能找到 flag")
            print(f"⏱️  耗时: {elapsed:.2f} 秒")
            
            return solution_result
            
        except Exception as e:
            print(f"\n💥 错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "challenge_name": challenge_name,
            }
    
    def _extract_flag(self, output: str) -> Optional[str]:
        """从输出中提取 flag"""
        import re
        
        patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group()
        
        return None
    
    def _save_trajectory(self, result: Dict[str, Any]):
        """保存解题轨迹"""
        import json
        
        filename = f"{result['challenge_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.trajectory_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 轨迹已保存: {filepath}")


def create_crypto_agent(**kwargs) -> CryptoAgent:
    """工厂函数：创建 CryptoAgent"""
    return CryptoAgent(**kwargs)
