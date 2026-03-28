#!/usr/bin/env python3
"""
运行 CTF Crypto Agent

使用示例:
    python scripts/run_agent.py
    python scripts/run_agent.py --challenge challenges/crypto_easy/rsa.txt
"""

import argparse
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import load_env
load_env()  # 先加载环境变量

from agent import create_crypto_agent


def interactive_mode(agent):
    """交互模式"""
    print("\n" + "="*60)
    print("🤖 CTF Crypto Agent 交互模式")
    print("="*60)
    print("输入题目描述 (或 'quit' 退出)\n")
    
    while True:
        print("\n" + "-"*60)
        # 多行输入
        lines = []
        print("请输入题目描述 (空行结束):")
        while True:
            try:
                line = input("> ")
                if line == "":
                    break
                lines.append(line)
            except EOFError:
                return
        
        description = "\n".join(lines)
        
        if description.lower() in ['quit', 'exit', 'q']:
            break
        
        if not description.strip():
            continue
        
        # 解题
        result = agent.solve(description, challenge_name="interactive")


def solve_file(agent, filepath: str):
    """从文件解题"""
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ 文件不存在: {filepath}")
        return
    
    # 读取题目
    description = path.read_text(encoding="utf-8")
    
    # 解题
    result = agent.solve(description, challenge_name=path.stem)
    
    return result


def demo_mode(agent):
    """演示模式 - 使用内置示例题目"""
    demo_challenge = """
题目: Simple Caesar

我们截获了一段密文，看起来像是凯撒密码:
密文: Khoor Zruog

提示: 凯撒密码是将每个字母向后移动固定位数。
请找出 flag。
"""
    
    result = agent.solve(demo_challenge, challenge_name="demo_caesar")
    return result


def main():
    parser = argparse.ArgumentParser(description="CTF Crypto Agent")
    parser.add_argument(
        "--challenge", "-c",
        help="题目文件路径"
    )
    parser.add_argument(
        "--model", "-m",
        default="moonshot-v1-8k",
        help="使用的模型 (默认: moonshot-v1-8k)"
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="运行演示题目"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="温度参数 (0-1)"
    )
    
    args = parser.parse_args()
    
    # 加载环境变量
    load_env()
    
    # 创建 Agent
    print("🚀 初始化 Agent...")
    agent = create_crypto_agent(
        model_name=args.model,
        temperature=args.temperature
    )
    
    # 运行模式
    if args.challenge:
        solve_file(agent, args.challenge)
    elif args.demo:
        demo_mode(agent)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
