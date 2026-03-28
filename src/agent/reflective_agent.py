"""
自我反思Agent (Reflective Agent)

实现带反思机制的Agent，能够在失败后：
1. 分析失败原因
2. 调整解题策略
3. 重试直到成功或达到最大尝试次数

核心特性:
- 错误分析
- 策略调整
- 记忆机制
- 渐进式提示增强
"""

import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class ReflectionType(Enum):
    """反思类型"""
    TOOL_SELECTION_ERROR = "tool_selection_error"
    PARAMETER_ERROR = "parameter_error"
    WRONG_APPROACH = "wrong_approach"
    INSUFFICIENT_ANALYSIS = "insufficient_analysis"
    EXTERNAL_TOOL_FAILURE = "external_tool_failure"
    UNKNOWN = "unknown"


@dataclass
class Attempt:
    """单次尝试记录"""
    attempt_number: int
    prompt: str
    response: str
    success: bool
    flag: Optional[str] = None
    error: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)
    reflection: Optional[str] = None
    reflection_type: Optional[ReflectionType] = None
    

class ReflectiveCryptoAgent:
    """
    带自我反思能力的Crypto Agent
    
    工作流程:
    1. 初始尝试解题
    2. 如果失败，分析失败原因
    3. 根据反思调整策略
    4. 重试（最多max_retries次）
    5. 记录完整的反思过程
    """
    
    def __init__(self, base_agent, max_retries: int = 3, enable_reflection: bool = True):
        """
        Args:
            base_agent: 基础Agent实例
            max_retries: 最大重试次数
            enable_reflection: 是否启用反思机制
        """
        self.base_agent = base_agent
        self.max_retries = max_retries
        self.enable_reflection = enable_reflection
        self.attempts: List[Attempt] = []
        self.reflection_memory: List[Dict[str, Any]] = []
    
    def _analyze_failure(self, challenge_desc: str, 
                        last_attempt: Attempt) -> Dict[str, Any]:
        """
        分析失败原因
        
        Returns:
            包含反思类型和建议的字典
        """
        response = last_attempt.response.lower()
        error = (last_attempt.error or "").lower()
        
        # 分析失败类型
        reflection_type = ReflectionType.UNKNOWN
        suggestions = []
        
        # 检查工具选择问题
        if "no such tool" in error or "tool not found" in error:
            reflection_type = ReflectionType.TOOL_SELECTION_ERROR
            suggestions.append("检查工具名称是否正确")
            suggestions.append("使用 list_tools 查看可用工具")
        
        # 检查参数错误
        elif "parameter" in error or "argument" in error or "missing" in error:
            reflection_type = ReflectionType.PARAMETER_ERROR
            suggestions.append("仔细检查工具的参数要求")
            suggestions.append("确认所有必需参数都已提供")
        
        # 检查外部工具失败
        elif "external tool failed" in error or "sagemath" in error or "flatter" in error:
            reflection_type = ReflectionType.EXTERNAL_TOOL_FAILURE
            suggestions.append("检查外部工具输入格式")
            suggestions.append("尝试简化输入或分步处理")
        
        # 检查方法错误
        elif "wrong approach" in response or "not work" in response or "failed" in response:
            reflection_type = ReflectionType.WRONG_APPROACH
            suggestions.append("重新分析题目类型")
            suggestions.append("考虑其他攻击方法")
            suggestions.append("检查是否有遗漏的信息")
        
        # 分析不足
        elif "don't know" in response or "unclear" in response or "need more" in response:
            reflection_type = ReflectionType.INSUFFICIENT_ANALYSIS
            suggestions.append("更仔细地分析题目描述")
            suggestions.append("识别关键密码学参数")
            suggestions.append("回顾相关攻击方法")
        
        # 默认建议
        if not suggestions:
            suggestions.append("尝试不同的解题思路")
            suggestions.append("检查输入数据是否正确")
            suggestions.append("考虑题目可能需要多步攻击")
        
        return {
            "type": reflection_type,
            "description": self._get_reflection_description(reflection_type),
            "suggestions": suggestions,
            "previous_tools": last_attempt.tools_used
        }
    
    def _get_reflection_description(self, reflection_type: ReflectionType) -> str:
        """获取反思类型描述"""
        descriptions = {
            ReflectionType.TOOL_SELECTION_ERROR: "工具选择错误：使用了不存在或错误的工具",
            ReflectionType.PARAMETER_ERROR: "参数错误：工具参数缺失或格式不正确",
            ReflectionType.WRONG_APPROACH: "方法错误：使用了错误的攻击方法",
            ReflectionType.INSUFFICIENT_ANALYSIS: "分析不足：对题目理解不够深入",
            ReflectionType.EXTERNAL_TOOL_FAILURE: "外部工具失败：SageMath/FLATTER等工具调用失败",
            ReflectionType.UNKNOWN: "未知错误：需要进一步分析"
        }
        return descriptions.get(reflection_type, "未知错误")
    
    def _build_enhanced_prompt(self, challenge_desc: str, 
                              reflection: Dict[str, Any],
                              attempt_number: int) -> str:
        """构建增强的提示"""
        
        base_prompt = challenge_desc
        
        # 添加反思信息
        reflection_text = f"""
【反思与调整 - 尝试 #{attempt_number}】

上一次尝试的问题分析:
- 问题类型: {reflection['type'].value}
- 详细说明: {reflection['description']}

改进建议:
"""
        for i, suggestion in enumerate(reflection['suggestions'], 1):
            reflection_text += f"{i}. {suggestion}\n"
        
        # 添加之前使用的工具（避免重复）
        if reflection['previous_tools']:
            reflection_text += f"\n之前已尝试的工具: {', '.join(reflection['previous_tools'])}\n"
            reflection_text += "建议尝试不同的工具或方法。\n"
        
        # 添加策略提示
        reflection_text += """
请根据以上反思调整你的解题策略:
1. 重新分析题目类型和关键参数
2. 选择合适的工具（检查工具列表）
3. 仔细构造工具参数
4. 如果一种方法失败，尝试其他方法
5. 必要时将问题分解为多个步骤

现在重新开始解题:
"""
        
        return base_prompt + reflection_text
    
    def solve(self, challenge_description: str, challenge_name: str = None,
              verbose: bool = True) -> Dict[str, Any]:
        """
        带反思的解题
        
        Returns:
            包含最终结果和完整尝试历史的字典
        """
        self.attempts = []
        challenge_name = challenge_name or f"challenge_{time.time()}"
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"🤔 反思式解题开始: {challenge_name}")
            print(f"   最大重试次数: {self.max_retries}")
            print(f"{'='*60}")
        
        current_prompt = challenge_description
        
        for attempt_num in range(self.max_retries + 1):
            if verbose:
                print(f"\n📍 尝试 #{attempt_num + 1}")
            
            # 执行解题
            start_time = time.time()
            
            try:
                result = self.base_agent.solve(
                    challenge_description=current_prompt,
                    challenge_name=f"{challenge_name}_attempt{attempt_num + 1}"
                )
                
                elapsed = time.time() - start_time
                
                # 记录尝试
                attempt = Attempt(
                    attempt_number=attempt_num + 1,
                    prompt=current_prompt[:500],  # 截断存储
                    response=result.get('output', '')[:1000],
                    success=result.get('success', False),
                    flag=result.get('flag'),
                    tools_used=result.get('tools_used', [])
                )
                self.attempts.append(attempt)
                
                if verbose:
                    status = "✅ 成功" if attempt.success else "❌ 失败"
                    print(f"   结果: {status} ({elapsed:.1f}s)")
                    if attempt.flag:
                        print(f"   Flag: {attempt.flag}")
                
                # 如果成功，返回结果
                if attempt.success:
                    if verbose:
                        print(f"\n✨ 解题成功！共尝试 {attempt_num + 1} 次")
                    return self._build_final_result(success=True)
                
                # 如果启用反思且还有重试机会
                if self.enable_reflection and attempt_num < self.max_retries:
                    reflection = self._analyze_failure(challenge_description, attempt)
                    attempt.reflection = reflection['description']
                    attempt.reflection_type = reflection['type']
                    
                    if verbose:
                        print(f"   反思: {reflection['description']}")
                        print(f"   建议: {', '.join(reflection['suggestions'][:2])}")
                    
                    # 构建增强提示
                    current_prompt = self._build_enhanced_prompt(
                        challenge_description, reflection, attempt_num + 2
                    )
                
            except Exception as e:
                elapsed = time.time() - start_time
                attempt = Attempt(
                    attempt_number=attempt_num + 1,
                    prompt=current_prompt[:500],
                    response="",
                    success=False,
                    error=str(e)
                )
                self.attempts.append(attempt)
                
                if verbose:
                    print(f"   错误: {e} ({elapsed:.1f}s)")
        
        # 所有尝试都失败
        if verbose:
            print(f"\n💔 解题失败，已尝试 {len(self.attempts)} 次")
        
        return self._build_final_result(success=False)
    
    def _build_final_result(self, success: bool) -> Dict[str, Any]:
        """构建最终结果"""
        last_attempt = self.attempts[-1] if self.attempts else None
        
        return {
            'success': success,
            'flag': last_attempt.flag if last_attempt else None,
            'total_attempts': len(self.attempts),
            'attempts': [
                {
                    'number': a.attempt_number,
                    'success': a.success,
                    'flag': a.flag,
                    'tools_used': a.tools_used,
                    'reflection': a.reflection,
                    'reflection_type': a.reflection_type.value if a.reflection_type else None,
                    'error': a.error
                }
                for a in self.attempts
            ],
            'reflection_summary': self._generate_reflection_summary()
        }
    
    def _generate_reflection_summary(self) -> str:
        """生成反思总结"""
        if not self.attempts:
            return "无尝试记录"
        
        reflection_types = [a.reflection_type for a in self.attempts if a.reflection_type]
        if not reflection_types:
            return "无需反思（首次成功或无明确错误）"
        
        type_counts = {}
        for rt in reflection_types:
            type_counts[rt.value] = type_counts.get(rt.value, 0) + 1
        
        summary = "遇到的问题类型:\n"
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            summary += f"  - {t}: {count}次\n"
        
        return summary
    
    def get_reflection_memory(self) -> List[Dict[str, Any]]:
        """获取反思记忆（可用于持续学习）"""
        return [
            {
                'attempt_number': a.attempt_number,
                'reflection_type': a.reflection_type.value if a.reflection_type else None,
                'reflection': a.reflection,
                'tools_used': a.tools_used,
                'success': a.success
            }
            for a in self.attempts
        ]


def create_reflective_agent(model_name: str = "moonshot-v1-32k", 
                           max_retries: int = 3,
                           **kwargs) -> ReflectiveCryptoAgent:
    """
    创建带反思能力的Agent
    
    使用示例:
        agent = create_reflective_agent(max_retries=3)
        result = agent.solve(challenge_description, "challenge_name")
        
        print(f"成功: {result['success']}")
        print(f"尝试次数: {result['total_attempts']}")
        print(f"反思总结: {result['reflection_summary']}")
    """
    from .crypto_agent import create_crypto_agent
    
    base_agent = create_crypto_agent(model_name=model_name, **kwargs)
    return ReflectiveCryptoAgent(base_agent, max_retries=max_retries)


# 便捷函数
def solve_with_reflection(challenge_description: str, 
                         challenge_name: str = None,
                         max_retries: int = 3,
                         model_name: str = "moonshot-v1-32k") -> Dict[str, Any]:
    """
    使用反思机制解题的便捷函数
    """
    agent = create_reflective_agent(model_name=model_name, max_retries=max_retries)
    return agent.solve(challenge_description, challenge_name)
