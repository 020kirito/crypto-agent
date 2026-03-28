#!/bin/bash
# GitHub SSH设置脚本

set -e

echo "========================================"
echo "🔧 GitHub SSH密钥设置"
echo "========================================"
echo ""

# 检查是否已有密钥
if [ -f ~/.ssh/github_crypto_agent ]; then
    echo "⚠️  检测到已有SSH密钥"
    read -p "是否重新生成? (y/N): " regen
    if [ "$regen" != "y" ]; then
        echo "使用现有密钥"
        cat ~/.ssh/github_crypto_agent.pub
        echo ""
        echo "请将此公钥添加到GitHub:"
        echo "https://github.com/settings/ssh/new"
        exit 0
    fi
fi

# 生成SSH密钥
echo "📦 生成SSH密钥..."
read -p "输入你的邮箱: " email
ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/github_crypto_agent -N ""

# 启动ssh-agent
echo "🔑 启动ssh-agent..."
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_crypto_agent

# 配置SSH
echo "⚙️  配置SSH..."
if ! grep -q "Host github-crypto-agent" ~/.ssh/config 2>/dev/null; then
    cat >> ~/.ssh/config << EOF

Host github-crypto-agent
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_crypto_agent
EOF
    chmod 600 ~/.ssh/config
fi

# 显示公钥
echo ""
echo "========================================"
echo "📋 你的SSH公钥:"
echo "========================================"
cat ~/.ssh/github_crypto_agent.pub
echo ""

# 提示
read -p "按Enter复制公钥到剪贴板 (如果支持)..."
if command -v xclip &> /dev/null; then
    cat ~/.ssh/github_crypto_agent.pub | xclip -selection clipboard
    echo "✅ 已复制到剪贴板"
elif command -v pbcopy &> /dev/null; then
    cat ~/.ssh/github_crypto_agent.pub | pbcopy
    echo "✅ 已复制到剪贴板"
else
    echo "⚠️  请手动复制上面的公钥"
fi

echo ""
echo "========================================"
echo "📌 下一步:"
echo "========================================"
echo "1. 打开 https://github.com/settings/ssh/new"
echo "2. 粘贴上面的公钥"
echo "3. Title填写: CTF Crypto Agent"
echo "4. 点击 'Add SSH key'"
echo ""
read -p "完成后按Enter继续..."

echo ""
echo "🧪 测试SSH连接..."
ssh -T github-crypto-agent || true

echo ""
echo "📝 配置Git remote..."
cd /mnt/d/llama-fac/toy_ctf
git remote set-url origin git@github-crypto-agent:020kirito/crypto-agent.git

echo ""
echo "🚀 推送到GitHub..."
git push -u origin main

echo ""
echo "✅ 完成!"
echo "查看仓库: https://github.com/020kirito/crypto-agent"
