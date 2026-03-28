# GitHub推送指南

## 当前状态

代码已经提交到本地git仓库，现在需要推送到GitHub。

## 方法1: 使用SSH密钥 (推荐)

### 步骤1: 生成SSH密钥

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/github_crypto_agent
```

### 步骤2: 添加SSH密钥到GitHub

1. 复制公钥:
```bash
cat ~/.ssh/github_crypto_agent.pub
```

2. 打开GitHub → Settings → SSH and GPG keys → New SSH key
3. 粘贴公钥内容，Title填写 "CTF Crypto Agent"
4. 点击 "Add SSH key"

### 步骤3: 配置SSH

```bash
# 添加SSH配置
cat >> ~/.ssh/config << EOF
Host github-crypto-agent
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_crypto_agent
EOF

# 设置权限
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/github_crypto_agent
```

### 步骤4: 测试连接

```bash
ssh -T github-crypto-agent
# 应该看到: Hi 020kirito! You've successfully authenticated...
```

### 步骤5: 修改remote并推送

```bash
cd /mnt/d/llama-fac/toy_ctf

# 修改remote为SSH方式
git remote set-url origin git@github-crypto-agent:020kirito/crypto-agent.git

# 推送
git push -u origin main
```

---

## 方法2: 使用GitHub Token

### 步骤1: 创建GitHub Token

1. 打开 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限:
   - ✅ repo (完整仓库访问)
4. 点击 "Generate token"
5. **复制token** (只显示一次!)

### 步骤2: 配置Git使用Token

```bash
# 方式1: 直接修改remote URL
git remote set-url origin https://TOKEN@github.com/020kirito/crypto-agent.git

# 方式2: 使用credential helper
git config --global credential.helper store
echo "https://020kirito:TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

### 步骤3: 推送

```bash
git push -u origin main
```

---

## 方法3: 手动上传 (最简单)

如果以上方法都失败，可以手动上传：

### 步骤1: 创建打包文件

```bash
cd /mnt/d/llama-fac/toy_ctf
tar czvf ../crypto-agent.tar.gz --exclude='.git' --exclude='data/training/*.jsonl' --exclude='outputs/' .
```

### 步骤2: 解压到GitHub Desktop

1. 在Windows上安装 [GitHub Desktop](https://desktop.github.com/)
2. 克隆仓库到本地: `https://github.com/020kirito/crypto-agent`
3. 解压 `crypto-agent.tar.gz` 到仓库目录
4. 使用GitHub Desktop提交并推送

---

## 快速命令参考

### 检查当前状态
```bash
cd /mnt/d/llama-fac/toy_ctf
git status
git log --oneline -3
git remote -v
```

### 重新配置remote
```bash
# HTTPS方式 (使用token)
git remote set-url origin https://TOKEN@github.com/020kirito/crypto-agent.git

# SSH方式
git remote set-url origin git@github.com:020kirito/crypto-agent.git
```

### 强制推送 (如果远程有冲突)
```bash
# 注意: 这会覆盖远程内容!
git push -u origin main --force
```

---

## 验证推送成功

推送后访问:
https://github.com/020kirito/crypto-agent

应该能看到:
- README.md
- 项目代码
- 最近提交记录

---

## 常见问题

### Q: "Repository not found"
**原因**: 仓库不存在或没有权限  
**解决**: 确保在GitHub上创建了同名仓库

### Q: "Permission denied"
**原因**: 身份验证失败  
**解决**: 检查token/ssh key是否正确配置

### Q: "failed to push some refs"
**原因**: 远程仓库有本地没有的提交  
**解决**: 
```bash
git pull origin main --rebase
git push origin main
```

### Q: 大文件推送失败
**原因**: GitHub限制单个文件100MB  
**解决**: 已配置.gitignore排除大文件，检查是否有遗漏:
```bash
git lfs track "*.gguf"
git lfs track "*.bin"
```

---

## 推送后操作

推送成功后，建议:

1. **设置仓库为Public** (如果想分享)
   - Settings → Danger Zone → Change visibility

2. **添加Topics** (便于搜索)
   - ctf, cryptography, llm, agent, rsa, ecc, lattice

3. **启用GitHub Pages** (可选)
   - Settings → Pages → Source: main branch

4. **创建Release** (标记版本)
   - Tags → v1.0 → Create release

---

## 下一步

推送完成后，可以开始模型微调：

```bash
python scripts/fine_tune_unsloth_8gb.py
```

祝训练顺利! 🚀
