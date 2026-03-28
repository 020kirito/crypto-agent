#!/bin/bash
# 快速安装脚本

echo "🚀 安装 CTF Crypto Agent 依赖..."

# 使用清华镜像加速
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 先安装核心依赖
echo "📦 安装核心依赖..."
pip install langchain langchain-core langchain-openai openai -q

# 安装密码学库
echo "🔐 安装密码学库..."
pip install pycryptodome sympy gmpy2 -q

# 安装其他工具
echo "🛠️ 安装工具库..."
pip install pyyaml python-dotenv rich -q

echo "✅ 安装完成！"
echo ""
echo "下一步:"
echo "1. 配置 API Key: 编辑 .env 文件"
echo "2. 运行 Agent: python scripts/run_agent.py --demo"
