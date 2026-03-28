#!/bin/bash
# CTF Crypto Agent - 维护仪表板

clear
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          🤖 CTF Crypto Agent - 维护仪表板                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 项目路径
PROJECT_DIR="/mnt/d/llama-fac/toy_ctf"
cd "$PROJECT_DIR" 2>/dev/null || cd "$(dirname "$0")/.."

echo "📅 时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📁 路径: $(pwd)"
echo ""

# ============================================
# 💻 系统状态
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💻 系统状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python版本
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
echo "  Python: $PYTHON_VERSION"

# CUDA状态
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1)
    if [ -n "$GPU_INFO" ]; then
        echo "  GPU: $GPU_INFO"
    else
        echo "  GPU: 未检测到"
    fi
else
    echo "  GPU: nvidia-smi 不可用"
fi

# 磁盘空间
echo "  磁盘: $(df -h . | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo ""

# ============================================
# 📦 依赖状态
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 依赖状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查关键包
PACKAGES=("langchain" "openai" "unsloth" "transformers" "torch")
for pkg in "${PACKAGES[@]}"; do
    VERSION=$(pip show "$pkg" 2>/dev/null | grep Version | cut -d' ' -f2)
    if [ -n "$VERSION" ]; then
        echo "  ✅ $pkg: $VERSION"
    else
        echo "  ❌ $pkg: 未安装"
    fi
done

# 检查过时依赖
echo ""
if command -v pip-review &> /dev/null; then
    OUTDATED=$(pip-review --local 2>/dev/null | wc -l)
    if [ "$OUTDATED" -gt 0 ]; then
        echo "  ⚠️  过时依赖: $OUTDATED 个"
        echo "     运行: pip list --outdated"
    else
        echo "  ✅ 所有依赖已最新"
    fi
else
    echo "  ℹ️  pip-review 未安装 (pip install pip-review)"
fi
echo ""

# ============================================
# 📊 数据状态
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 数据状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 训练数据
if [ -f "data/training/finetune/train.jsonl" ]; then
    TRAIN_COUNT=$(wc -l < data/training/finetune/train.jsonl)
    echo "  训练数据: $TRAIN_COUNT 条"
else
    echo "  训练数据: 未找到"
fi

if [ -f "data/training/finetune/val.jsonl" ]; then
    VAL_COUNT=$(wc -l < data/training/finetune/val.jsonl)
    echo "  验证数据: $VAL_COUNT 条"
else
    echo "  验证数据: 未找到"
fi

# 博客数据
if [ -d "data/tangcu_blog" ]; then
    BLOG_FILES=$(find data/tangcu_blog -name "*.json" 2>/dev/null | wc -l)
    echo "  博客数据: $BLOG_FILES 个文件"
else
    echo "  博客数据: 未找到"
fi

# 轨迹数据
TRAJ_COUNT=$(find data/trajectories -name "*.json" 2>/dev/null | wc -l)
echo "  解题轨迹: $TRAJ_COUNT 个"
echo ""

# ============================================
# 🤖 模型状态
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 模型状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "outputs/ctf-crypto-lora" ]; then
    echo "  ✅ 本地模型目录存在"
    
    if [ -d "outputs/ctf-crypto-lora/lora_weights" ]; then
        LORA_SIZE=$(du -sh outputs/ctf-crypto-lora/lora_weights 2>/dev/null | cut -f1)
        echo "  ✅ LoRA权重: $LORA_SIZE"
    fi
    
    if [ -d "outputs/ctf-crypto-lora/merged_model" ]; then
        MERGED_SIZE=$(du -sh outputs/ctf-crypto-lora/merged_model 2>/dev/null | cut -f1)
        echo "  ✅ 合并模型: $MERGED_SIZE"
    fi
else
    echo "  ❌ 未找到本地模型"
    echo "     运行: python scripts/fine_tune_unsloth_8gb.py"
fi
echo ""

# ============================================
# 🛠️ 工具状态
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠️  工具状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查外部工具
if command -v sage &> /dev/null; then
    echo "  ✅ SageMath: $(sage --version 2>&1 | head -1)"
else
    echo "  ❌ SageMath: 未安装"
fi

if [ -f "tools/flatter/build/bin/flatter" ]; then
    echo "  ✅ FLATTER: 已安装"
else
    echo "  ❌ FLATTER: 未安装"
fi

if command -v yafu &> /dev/null; then
    echo "  ✅ YAFU: 已安装"
else
    echo "  ❌ YAFU: 未安装"
fi

if [ -d "tools/cado-nfs" ]; then
    echo "  ✅ CADO-NFS: 已安装"
else
    echo "  ❌ CADO-NFS: 未安装"
fi
echo ""

# ============================================
# 📝 最近活动
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 最近活动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Git状态
echo "  Git分支: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "  最近提交:"
git log --oneline -3 2>/dev/null | sed 's/^/    /' || echo "    N/A"
echo ""

# 最近轨迹
if [ -d "data/trajectories" ]; then
    LATEST_TRAJ=$(ls -t data/trajectories/*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_TRAJ" ]; then
        TRAJ_TIME=$(stat -c %y "$LATEST_TRAJ" 2>/dev/null | cut -d'.' -f1)
        TRAJ_NAME=$(basename "$LATEST_TRAJ")
        echo "  最新轨迹: $TRAJ_NAME ($TRAJ_TIME)"
    fi
fi
echo ""

# ============================================
# ⚠️  维护提醒
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  维护提醒"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查是否需要维护
REMINDERS=()

# 检查依赖更新
if ! pip-review --local &> /dev/null; then
    REMINDERS+=("运行: pip list --outdated (检查依赖更新)")
fi

# 检查数据备份
LATEST_BACKUP=$(find backups -name "*.tar.gz" -mtime -7 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    REMINDERS+=("已超过7天未备份数据")
fi

# 检查模型性能日志
if [ ! -f "logs/model_performance.jsonl" ]; then
    REMINDERS+=("未找到模型性能日志，建议开始监控")
fi

# 显示提醒
if [ ${#REMINDERS[@]} -eq 0 ]; then
    echo "  ✅ 暂无紧急维护事项"
else
    for reminder in "${REMINDERS[@]}"; do
        echo "  ⚠️  $reminder"
    done
fi
echo ""

# ============================================
# 🎯 快速操作
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 快速操作"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  训练模型:     python scripts/fine_tune_unsloth_8gb.py"
echo "  测试Agent:    python scripts/test_agent.py"
echo "  批量解题:     python scripts/batch_solve.py --all"
echo "  更新数据:     python scripts/collect_training_data.py --trajectories"
echo "  备份数据:     bash scripts/backup_data.sh"
echo ""

# ============================================
# 结束
# ============================================
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  详细维护指南: cat MAINTENANCE_GUIDE.md                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
