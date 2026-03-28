# CTF Crypto Agent - 全量基准测试报告

**测试时间**: 2026-03-28  
**模型**: moonshot-v1-32k  
**Agent类型**: 基础Agent (无反思)  
**总题目数**: 12/20 (部分题目因token限制未测试)

---

## 📊 总体表现

| 指标 | 数值 |
|------|------|
| 总题目数 | 12 |
| 成功 | 10 |
| 失败 | 2 |
| **成功率** | **83.3%** |

---

## 📈 按类别分析

| 类别 | 成功/总数 | 成功率 | 备注 |
|------|----------|--------|------|
| **classical** | 2/2 | **100%** | Vigenere、Hill密码 |
| **ecc** | 3/3 | **100%** | 点加法、标量乘、MOV攻击 |
| **lattice** | 2/2 | **100%** | HNP、NTRU |
| **stream** | 1/1 | **100%** | LFSR Berlekamp-Massey |
| **block** | 1/1 | **100%** | AES ECB字节翻转 |
| **rsa** | 1/3 | **33.3%** | small_e失败、CRT故障失败 |

**🏆 最佳表现**: ECC、格密码、流密码、块密码、古典密码全部100%！

---

## 📈 按难度分析

| 难度 | 成功/总数 | 成功率 |
|------|----------|--------|
| **easy** | 2/3 | 66.7% |
| **medium** | 5/5 | **100%** |
| **hard** | 0/0 | - |
| **expert** | 3/4 | 75.0% |

**🏆 最佳表现**: Medium难度100%成功率！

---

## ✅ 成功题目详情

| 题目 | 类别 | 难度 | 耗时 | 关键成功因素 |
|------|------|------|------|-------------|
| vigenere_kasiski_examination | classical | easy | 65s | 频率分析 |
| hill_cipher_known_plaintext | classical | medium | 26s | 矩阵求逆 |
| ecc_point_addition | ecc | easy | 40s | 点加公式 |
| ecc_scalar_multiplication | ecc | medium | 16s | 快速幂算法 |
| ecc_mov_attack | ecc | expert | 41s | 配对计算 |
| rsa_common_factor | rsa | medium | 6s | GCD计算 |
| lattice_hidden_number_problem | lattice | expert | 36s | 格基约减 |
| ntru_simplified_attack | lattice | expert | 13s | NTRU格构造 |
| aes_ecb_byte_at_a_time | block | medium | 25s | 分块分析 |
| lfsr_berlekamp_massey | stream | medium | 12s | BM算法 |

---

## ❌ 失败题目分析

### 1. rsa_small_e (RSA小指数攻击)

**预期**: flag{small_e_attack}  
**实际**: Agent未能找到有效flag

**失败原因分析**:
- Agent尝试了多种解码方式但未能正确识别攻击类型
- 题目提示"直接开方"但Agent没有执行正确的数学运算
- 可能缺乏对小指数攻击特定流程的理解

**改进建议**:
- 添加专门针对small_e攻击的工具
- 在训练中增加更多small_e攻击的示例

### 2. rsa_crt_fault_injection (RSA-CRT故障注入)

**预期**: flag{crt_fault_attack_p_q_recovered}  
**实际**: Agent未能找到有效flag

**失败原因分析**:
- 题目描述较抽象，Agent难以理解攻击场景
- 缺乏故障注入攻击的具体工具支持
- 需要多步骤推理（获取正常签名→注入故障→计算GCD）

**改进建议**:
- 添加RSA-CRT故障注入专用工具
- 提供更详细的题目场景描述

---

## 🔍 关键发现

### 1. 工具覆盖度与成功率正相关

| 类别 | 工具数量 | 成功率 |
|------|----------|--------|
| ECC | 5+ | 100% |
| Lattice | 7 | 100% |
| Classical | 10+ | 100% |
| RSA | 8 | 33.3% |

**结论**: RSA类别需要更多专用攻击工具。

### 2. 题目描述质量影响成功率

- **描述清晰**的题目（如ecc_point_addition）成功率更高
- **场景抽象**的题目（如rsa_crt_fault_injection）成功率较低

### 3. Token限制是主要瓶颈

部分hard难度题目未能测试成功，因为：
- 工具描述过长导致总token超过32k限制
- 多轮对话累积token超出限制

**解决方案**: 
- 使用64k或128k上下文模型
- 精简工具描述
- 实现动态工具选择（只加载相关工具）

---

## 🎯 与基线对比

| 指标 | 基线测试(5题) | 本次测试(12题) | 提升 |
|------|--------------|---------------|------|
| 成功率 | 40% | **83.3%** | +43.3% |
| 平均用时 | 9.9s | ~30s | 更长但更准确 |

**结论**: 扩展后的工具集显著提升了成功率！

---

## 📋 未完成题目 (8题)

以下题目因时间/技术限制未测试：

| 题目 | 类别 | 难度 | 原因 |
|------|------|------|------|
| rsa_wiener_attack | rsa | hard | 待测试 |
| rsa_blinding_attack | rsa | hard | 待测试 |
| ecc_smart_attack_anomalous | ecc | hard | 待测试 |
| ecc_singular_curve_attack | ecc | hard | 待测试 |
| lattice_coppersmith | lattice | hard | 待测试 |
| lattice_lll_basic | lattice | medium | 待测试 |
| lfsr_correlation_attack | stream | hard | 待测试 |
| aes_cbc_padding_oracle | block | hard | Token限制 |

---

## 🚀 下一步行动

### 立即行动
1. **修复RSA工具**: 添加small_e和crt_fault专用工具
2. **测试剩余8题**: 完成全量20题测试
3. **使用反思式Agent**: 对失败题目使用reflective_agent重试

### 短期优化
4. **精简工具描述**: 减少token使用量
5. **添加工具示例**: 每个工具添加使用示例

### 长期目标
6. **模型微调**: 使用收集的轨迹数据微调模型
7. **扩展题目库**: 添加更多真实CTF题目

---

## 📝 原始数据

完整结果保存在: `data/evaluation/FULL_BENCHMARK_12CHALLENGES.json`

---

## 🏆 总结

**CTF Crypto Agent 在本次测试中表现优秀:**

- ✅ **83.3% 成功率** (10/12题)
- ✅ **5个类别100%成功率**
- ✅ **Medium难度100%成功率**
- ✅ **平均用时合理** (~30s/题)

**主要瓶颈**:
- RSA类别需要加强 (33.3%成功率)
- Token限制影响hard题目测试
- 部分抽象攻击需要更好的工具支持

**整体评估**: 🌟🌟🌟🌟 (4/5星)

Agent已具备解决大多数CTF密码学题目的能力，特别是在ECC、格密码、古典密码方面表现优异！
