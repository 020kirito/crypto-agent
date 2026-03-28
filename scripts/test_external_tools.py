#!/usr/bin/env python3
"""
测试外部工具集成

使用示例:
    python scripts/test_external_tools.py --list
    python scripts/test_external_tools.py --test yafu --n 3233
    python scripts/test_external_tools.py --test sagemath --code "print(factor(3233))"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.external_tools_full import external_tool_manager, get_external_tools_info


def list_tools():
    """列出所有工具"""
    print(get_external_tools_info())


def test_yafu(n: int):
    """测试 YAFU"""
    print(f"\n🧪 测试 YAFU 分解 {n}")
    print("-" * 60)
    
    result = external_tool_manager.call_yafu(n)
    
    if result.get("success"):
        print(f"✅ 分解成功!")
        print(f"   因数: {result.get('factors', [])}")
        print(f"\n原始输出 (前 500 字符):")
        print(result.get('raw_output', '')[:500])
    else:
        print(f"❌ 失败: {result.get('error', 'Unknown error')}")


def test_sagemath(code: str):
    """测试 SageMath"""
    print(f"\n🧪 测试 SageMath")
    print(f"代码: {code[:50]}...")
    print("-" * 60)
    
    result = external_tool_manager.call_sagemath(code)
    
    if result.get("success"):
        print(f"✅ 执行成功!")
        print(f"\n输出:")
        print(result.get('stdout', ''))
        if result.get('stderr'):
            print(f"\n错误输出:")
            print(result.get('stderr', ''))
    else:
        print(f"❌ 失败: {result.get('error', 'Unknown error')}")


def test_flatter():
    """测试 FLATTER"""
    print(f"\n🧪 测试 FLATTER (LLL 规约)")
    print("-" * 60)
    
    # 测试矩阵
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 10]
    ]
    
    print(f"输入矩阵: {matrix}")
    
    result = external_tool_manager.call_flatter(matrix, algorithm="lll")
    
    if result.get("success"):
        print(f"✅ 规约成功!")
        print(f"   算法: {result.get('algorithm')}")
        print(f"   维度: {result.get('original_dim')}")
        print(f"   结果矩阵: {result.get('reduced_matrix', [])[:3]}")
    else:
        print(f"❌ 失败: {result.get('error', 'Unknown error')}")


def test_hashcat(hash_value: str, hash_type: str = "0"):
    """测试 Hashcat"""
    print(f"\n🧪 测试 Hashcat")
    print(f"哈希: {hash_value}")
    print(f"类型: {hash_type} (0=MD5)")
    print("-" * 60)
    
    result = external_tool_manager.call_hashcat(
        hash_value=hash_value,
        hash_type=hash_type,
        attack_mode="3",
        mask="?l?l?l?l"  # 4位小写字母
    )
    
    if result.get("success"):
        print(f"✅ 破解成功!")
        print(f"   结果: {result.get('cracked', [])}")
    else:
        print(f"❌ 失败或未找到: {result.get('error', 'No result')}")
        print(f"命令: {result.get('command', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="测试外部工具集成")
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有工具"
    )
    parser.add_argument(
        "--test", "-t",
        choices=["yafu", "sagemath", "flatter", "hashcat", "all"],
        help="测试指定工具"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=3233,
        help="用于测试的整数 (默认 3233)"
    )
    parser.add_argument(
        "--code",
        type=str,
        default="print(factor(3233))",
        help="SageMath 代码"
    )
    parser.add_argument(
        "--hash",
        type=str,
        default="5f4dcc3b5aa765d61d8327deb882cf99",  # "password" 的 MD5
        help="测试哈希值"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_tools()
        return
    
    if args.test == "yafu":
        test_yafu(args.n)
    elif args.test == "sagemath":
        test_sagemath(args.code)
    elif args.test == "flatter":
        test_flatter()
    elif args.test == "hashcat":
        test_hashcat(args.hash)
    elif args.test == "all":
        print("\n" + "=" * 60)
        print("运行所有测试")
        print("=" * 60)
        test_yafu(args.n)
        test_flatter()
        test_sagemath(args.code)
        # Hashcat 测试可能较慢，跳过
        # test_hashcat(args.hash)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
