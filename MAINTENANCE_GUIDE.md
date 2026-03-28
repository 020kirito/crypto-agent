# CTF Crypto Agent - 维护指南

除了模型训练外，项目需要定期维护以确保稳定运行和持续改进。

---

## 📋 维护清单概览

| 类别 | 频率 | 优先级 | 耗时 |
|------|------|--------|------|
| [依赖更新](#1-依赖更新) | 每周 | ⭐⭐⭐⭐⭐ | 30分钟 |
| [数据更新](#2-数据更新) | 每月 | ⭐⭐⭐⭐⭐ | 2小时 |
| [模型监控](#3-模型监控) | 每周 | ⭐⭐⭐⭐ | 30分钟 |
| [工具维护](#4-工具维护) | 每月 | ⭐⭐⭐⭐ | 1小时 |
| [安全维护](#5-安全维护) | 每季度 | ⭐⭐⭐⭐⭐ | 1小时 |
| [性能优化](#6-性能优化) | 每季度 | ⭐⭐⭐ | 3小时 |
| [文档维护](#7-文档维护) | 每月 | ⭐⭐⭐ | 1小时 |
| [社区维护](#8-社区维护) | 持续 | ⭐⭐ | 2小时/周 |

---

## 1. 依赖更新

### 1.1 Python依赖更新

```bash
# 检查过时依赖
pip list --outdated

# 安全更新 (仅补丁版本)
pip install --upgrade <package>

# 或者批量更新
pip-review --auto  # 需要: pip install pip-review
```

### 1.2 关键依赖监控

需要重点关注的依赖：
- `langchain` - Agent核心框架
- `unsloth` - 微调框架
- `transformers` - 模型加载
- `torch` - 深度学习框架
- `openai` - API客户端

### 1.3 依赖安全扫描

```bash
# 安装安全扫描工具
pip install safety bandit

# 扫描已知漏洞
safety check

# 代码安全分析
bandit -r src/
```

### 1.4 创建依赖更新脚本

```bash
#!/bin/bash
# scripts/update_dependencies.sh

echo "🔍 检查依赖更新..."

# 生成当前依赖快照
pip freeze > requirements.lock

# 检查过时依赖
echo "📋 过时依赖列表:"
pip list --outdated

# 安全扫描
echo "🔒 安全扫描:"
safety check

echo "✅ 检查完成"
echo "⚠️  请手动测试后再提交更新"
```

---

## 2. 数据更新

### 2.1 增量爬取新Writeup

```bash
# 增量爬取 (只获取新的)
python scripts/collect_training_data.py --writeups --limit 50

# 合并到现有数据集
python scripts/merge_training_data.py
```

### 2.2 数据质量检查

```python
# scripts/check_data_quality.py
import json
from pathlib import Path

def check_data_quality(data_file: str):
    """检查训练数据质量"""
    issues = []
    
    with open(data_file, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                
                # 检查必要字段
                if 'messages' not in data:
                    issues.append(f"Line {i}: missing 'messages'")
                    continue
                
                messages = data['messages']
                
                # 检查消息格式
                for msg in messages:
                    if 'role' not in msg or 'content' not in msg:
                        issues.append(f"Line {i}: invalid message format")
                        break
                
                # 检查内容长度
                total_length = sum(len(m.get('content', '')) for m in messages)
                if total_length < 50:
                    issues.append(f"Line {i}: content too short")
                if total_length > 10000:
                    issues.append(f"Line {i}: content too long")
                    
            except json.JSONDecodeError:
                issues.append(f"Line {i}: invalid JSON")
    
    return issues

# 使用
issues = check_data_quality("data/training/finetune/train.jsonl")
print(f"Found {len(issues)} issues")
```

### 2.3 数据去重

```bash
# 定期去重
python scripts/deduplicate_training_data.py \
    --input data/training/finetune/train.jsonl \
    --output data/training/finetune/train_deduped.jsonl
```

### 2.4 数据备份

```bash
# 创建数据备份脚本
#!/bin/bash
# scripts/backup_data.sh

BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 备份训练数据
cp data/training/finetune/*.jsonl "$BACKUP_DIR/"

# 备份爬取的数据
cp -r data/tangcu_blog "$BACKUP_DIR/"

# 压缩
tar czvf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✅ 备份完成: ${BACKUP_DIR}.tar.gz"
```

---

## 3. 模型监控

### 3.1 性能监控

```python
# scripts/monitor_model_performance.py
import json
from datetime import datetime
from pathlib import Path

def evaluate_and_log(model_name: str, test_challenges: list):
    """评估模型并记录性能"""
    
    # 运行评估
    results = run_evaluation(model_name, test_challenges)
    
    # 记录到日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "success_rate": results['success_rate'],
        "avg_time": results['avg_time'],
        "by_category": results['by_category']
    }
    
    # 追加到日志文件
    log_file = Path("logs/model_performance.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    # 检查性能下降
    if log_entry['success_rate'] < 0.7:
        send_alert(f"Model performance dropped: {log_entry['success_rate']:.2%}")

# 每周运行一次
evaluate_and_log("moonshot-v1-32k", get_test_challenges())
```

### 3.2 模型版本管理

```bash
# 记录模型版本
python scripts/log_model_version.py \
    --model outputs/ctf-crypto-lora/lora_weights \
    --metrics logs/model_performance.jsonl \
    --notes "After 3 epochs fine-tuning"
```

### 3.3 模型 drift 检测

```python
# 检测模型性能是否随时间下降
def detect_model_drift(log_file: str, window: int = 5):
    """检测模型性能漂移"""
    with open(log_file, 'r') as f:
        logs = [json.loads(line) for line in f]
    
    if len(logs) < window * 2:
        return False, "Not enough data"
    
    recent = logs[-window:]
    previous = logs[-window*2:-window]
    
    recent_rate = sum(l['success_rate'] for l in recent) / window
    previous_rate = sum(l['success_rate'] for l in previous) / window
    
    drop = previous_rate - recent_rate
    
    if drop > 0.1:  # 下降超过10%
        return True, f"Performance dropped by {drop:.1%}"
    
    return False, "No significant drift"
```

---

## 4. 工具维护

### 4.1 外部工具更新检查

```bash
# scripts/check_external_tools.sh

echo "🔍 检查外部工具状态..."

# SageMath
echo "  SageMath: $(sage --version 2>/dev/null || echo 'Not installed')"

# FLATTER
if [ -f "tools/flatter/build/bin/flatter" ]; then
    echo "  FLATTER: Installed"
else
    echo "  FLATTER: Not installed"
fi

# YAFU
if command -v yafu &> /dev/null; then
    echo "  YAFU: $(yafu -v 2>&1 | head -1)"
else
    echo "  YAFU: Not installed"
fi

# CADO-NFS
if [ -d "tools/cado-nfs" ]; then
    echo "  CADO-NFS: Installed"
else
    echo "  CADO-NFS: Not installed"
fi

echo "✅ 检查完成"
```

### 4.2 工具可用性测试

```bash
# 定期测试所有工具
python scripts/test_external_tools.py
```

### 4.3 添加新工具流程

1. **实现工具**: 在 `src/tools/` 添加新工具
2. **添加测试**: 在 `tests/tools/` 添加单元测试
3. **更新文档**: 更新 README.md 和 FEATURES_GUIDE.md
4. **注册工具**: 在 `src/tools/__init__.py` 注册

---

## 5. 安全维护

### 5.1 API密钥轮换

```bash
# 定期轮换API Key (建议每3个月)
# 1. 在Kimi平台生成新Key
# 2. 更新 .env 文件
# 3. 测试新Key
# 4. 删除旧Key
```

### 5.2 敏感信息扫描

```bash
# 确保没有意外提交敏感信息
git-secrets --scan  # 需要: brew install git-secrets

# 或者手动检查
grep -r "sk-" --include="*.py" --include="*.json" .
grep -r "api_key" --include="*.py" --include="*.json" .
```

### 5.3 依赖安全审计

```bash
# 每月运行
safety check --json > security_report.json

# 检查报告
if [ $(jq '.vulnerabilities | length' security_report.json) -gt 0 ]; then
    echo "⚠️  发现安全漏洞，请查看 security_report.json"
fi
```

---

## 6. 性能优化

### 6.1 性能分析

```python
# 分析Agent性能瓶颈
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 运行Agent
agent.solve(challenge_description, "test")

profiler.disable()

# 输出统计
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20
```

### 6.2 缓存优化

```python
# 实现工具结果缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_factorization(n: int):
    """缓存因式分解结果"""
    return factor(n)
```

### 6.3 内存优化

```python
# 定期清理缓存
import gc
import torch

def cleanup_memory():
    """清理内存"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```

---

## 7. 文档维护

### 7.1 更新CHANGELOG

```markdown
# CHANGELOG.md

## [1.1.0] - 2024-XX-XX
### Added
- 新增5个RSA攻击工具
- 支持批量解题模式

### Fixed
- 修复YAFU输出解析问题
- 优化Token使用效率

### Changed
- 升级LangChain到1.3.x
```

### 7.2 API文档自动生成

```bash
# 使用pdoc3生成API文档
pip install pdoc3
pdoc --html src/ -o docs/api/
```

### 7.3 示例更新

确保所有示例代码可运行：

```bash
# 测试所有示例
python scripts/test_examples.py
```

---

## 8. 社区维护

### 8.1 Issue管理

```markdown
## Issue标签
- `bug`: Bug报告
- `enhancement`: 功能请求
- `documentation`: 文档问题
- `good first issue`: 新手友好
- `help wanted`: 需要帮助
```

### 8.2 PR审查清单

- [ ] 代码通过测试
- [ ] 添加新工具时包含测试
- [ ] 更新相关文档
- [ ] 遵循代码风格
- [ ] 没有安全漏洞

### 8.3 版本发布流程

```bash
# 1. 更新版本号
# 2. 更新CHANGELOG
# 3. 打标签
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 4. 创建Release
# 在GitHub上创建Release，添加说明
```

---

## 9. 自动化维护

### 9.1 GitHub Actions工作流

```yaml
# .github/workflows/maintenance.yml
name: Weekly Maintenance

on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日运行

jobs:
  maintenance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check dependencies
        run: |
          pip install safety
          safety check
      
      - name: Test tools
        run: python scripts/test_external_tools.py
      
      - name: Check data quality
        run: python scripts/check_data_quality.py
```

### 9.2 维护提醒脚本

```python
#!/usr/bin/env python3
# scripts/maintenance_reminder.py

from datetime import datetime, timedelta

def check_maintenance_schedule():
    """检查维护计划"""
    now = datetime.now()
    
    # 每周任务
    last_weekly = get_last_run("weekly")
    if now - last_weekly > timedelta(days=7):
        print("⚠️  需要执行每周维护:")
        print("  - 更新依赖")
        print("  - 监控模型性能")
    
    # 每月任务
    last_monthly = get_last_run("monthly")
    if now - last_monthly > timedelta(days=30):
        print("⚠️  需要执行每月维护:")
        print("  - 更新训练数据")
        print("  - 检查工具可用性")
    
    # 每季度任务
    last_quarterly = get_last_run("quarterly")
    if now - last_quarterly > timedelta(days=90):
        print("⚠️  需要执行每季度维护:")
        print("  - 安全审计")
        print("  - 性能优化")

if __name__ == "__main__":
    check_maintenance_schedule()
```

---

## 10. 监控仪表板

### 10.1 创建监控脚本

```bash
#!/bin/bash
# scripts/dashboard.sh

clear
echo "========================================"
echo "   CTF Crypto Agent - 维护仪表板"
echo "========================================"
echo ""

# 系统状态
echo "💻 系统状态:"
echo "  Python: $(python --version)"
echo "  CUDA: $(nvidia-smi --query-gpu=name,memory.used --format=csv,noheader 2>/dev/null || echo 'Not available')"
echo ""

# 依赖状态
echo "📦 依赖状态:"
pip list --outdated 2>/dev/null | wc -l | xargs echo "  过时依赖:"
echo ""

# 数据状态
echo "📊 数据状态:"
wc -l data/training/finetune/*.jsonl 2>/dev/null
echo ""

# 模型状态
echo "🤖 模型状态:"
ls -lh outputs/ctf-crypto-lora/ 2>/dev/null | grep -E "lora_weights|merged_model" || echo "  无本地模型"
echo ""

# 最近日志
echo "📝 最近活动:"
tail -5 logs/model_performance.jsonl 2>/dev/null || echo "  无日志"
echo ""
```

---

## 📅 维护日历

```
每周日:
  - [ ] 运行依赖更新检查
  - [ ] 评估模型性能
  - [ ] 备份数据

每月1日:
  - [ ] 爬取新Writeup
  - [ ] 检查数据质量
  - [ ] 测试所有外部工具
  - [ ] 更新文档

每季度:
  - [ ] 安全审计
  - [ ] API密钥轮换
  - [ ] 性能优化
  - [ ] 大版本发布
```

---

## 🎯 总结

**最关键的日常维护**:
1. ⭐⭐⭐⭐⭐ 依赖安全更新
2. ⭐⭐⭐⭐⭐ 模型性能监控
3. ⭐⭐⭐⭐ 数据增量更新
4. ⭐⭐⭐ API密钥安全
5. ⭐⭐ 社区Issue响应

建议将这些任务添加到日历提醒中！
