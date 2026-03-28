#!/bin/bash
# GitHub推送修复脚本

echo "========================================"
echo "🔧 GitHub推送修复"
echo "========================================"
echo ""

cd /mnt/d/llama-fac/toy_ctf

echo "📊 当前状态:"
echo "  Remote: $(git remote get-url origin)"
echo ""

# 检测当前SSH用户
ssh_user=$(ssh -T git@github.com 2>&1 | grep -oP 'Hi \K[^!]+' || echo "unknown")
echo "  SSH用户: $ssh_user"
echo ""

echo "选择修复方案:"
echo ""
echo "1) 使用Token推送 (最快，推荐)"
echo "2) 显示当前SSH公钥 (添加到GitHub)"
echo "3) 使用Alic3-Myth的仓库"
echo "4) 退出"
echo ""

read -p "选择 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📋 Token方式推送"
        echo "=================="
        echo ""
        echo "步骤:"
        echo "1. 访问 https://github.com/settings/tokens/new"
        echo "2. Note: CTF Crypto Agent Push"
        echo "3. 勾选 'repo' 权限"
        echo "4. 点击 Generate token"
        echo "5. 复制生成的token (只显示一次!)"
        echo ""
        read -p "粘贴Token (输入时不会显示): " -s token
        echo ""
        
        if [ -z "$token" ]; then
            echo "❌ Token为空"
            exit 1
        fi
        
        echo "📝 配置Git..."
        git remote set-url origin "https://${token}@github.com/020kirito/crypto-agent.git"
        
        echo "🚀 推送中..."
        if git push -u origin main; then
            echo ""
            echo "✅ 推送成功!"
            echo ""
            echo "查看仓库: https://github.com/020kirito/crypto-agent"
            
            # 为了安全，恢复remote (移除token)
            git remote set-url origin "https://github.com/020kirito/crypto-agent.git"
            echo ""
            echo "💡 提示: 已恢复remote URL，下次推送需要输入token"
        else
            echo "❌ 推送失败"
        fi
        ;;
    
    2)
        echo ""
        echo "📋 当前SSH公钥"
        echo "=================="
        echo ""
        
        # 查找公钥
        for keyfile in ~/.ssh/id_ed25519.pub ~/.ssh/id_rsa.pub ~/.ssh/github_crypto_agent.pub; do
            if [ -f "$keyfile" ]; then
                echo "文件: $keyfile"
                echo ""
                cat "$keyfile"
                echo ""
                echo "========================================"
                echo "📌 请将此公钥添加到GitHub:"
                echo "https://github.com/settings/ssh/new"
                echo "========================================"
                exit 0
            fi
        done
        
        echo "❌ 未找到SSH公钥"
        echo ""
        echo "生成新密钥:"
        read -p "输入邮箱: " email
        ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/github_crypto_agent -N ""
        echo ""
        cat ~/.ssh/github_crypto_agent.pub
        echo ""
        echo "========================================"
        echo "📌 请将此公钥添加到GitHub:"
        echo "https://github.com/settings/ssh/new"
        echo "========================================"
        ;;
    
    3)
        echo ""
        echo "📋 使用Alic3-Myth的仓库"
        echo "========================"
        echo ""
        echo "需要在Alic3-Myth账号下创建仓库"
        echo ""
        read -p "输入仓库名 (默认: crypto-agent): " repo_name
        repo_name=${repo_name:-crypto-agent}
        
        git remote set-url origin "git@github.com:Alic3-Myth/${repo_name}.git"
        echo "🚀 推送到 Alic3-Myth/${repo_name}..."
        git push -u origin main
        ;;
    
    4)
        echo "👋 退出"
        exit 0
        ;;
    
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac
