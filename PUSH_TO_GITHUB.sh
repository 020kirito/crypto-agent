#!/bin/bash
# GitHub推送脚本 - Token方式

echo "========================================"
echo "🚀 GitHub Token推送脚本"
echo "========================================"
echo ""

# 检查是否在正确目录
if [ ! -f "README.md" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    echo "   cd /mnt/d/llama-fac/toy_ctf"
    exit 1
fi

echo "📋 步骤说明:"
echo "1. 访问 https://github.com/settings/tokens/new"
echo "2. Note: CTF Crypto Agent"
echo "3. 勾选 'repo' 权限"
echo "4. 点击 Generate token"
echo "5. 复制token (ghp_xxxxxxxx...)"
echo ""

# 获取Token
read -s -p "请输入GitHub Token: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ Token不能为空"
    exit 1
fi

echo "📝 配置remote..."
git remote set-url origin "https://${TOKEN}@github.com/020kirito/crypto-agent.git"

echo "🚀 推送到GitHub..."
if git push -u origin main; then
    echo ""
    echo "========================================"
    echo "✅ 推送成功!"
    echo "========================================"
    echo ""
    echo "查看仓库: https://github.com/020kirito/crypto-agent"
    echo ""
    echo "💡 安全提示:"
    echo "   - 建议删除刚才生成的Token"
    echo "   - 或设置token过期时间为7天"
    echo ""
    
    # 恢复remote (移除token)
    git remote set-url origin "https://github.com/020kirito/crypto-agent.git"
    echo "✅ 已恢复remote URL"
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能原因:"
    echo "   - Token无效"
    echo "   - Token没有repo权限"
    echo "   - 仓库不存在"
    echo ""
    echo "请检查并重试"
fi
