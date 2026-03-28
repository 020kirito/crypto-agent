# 📚 D/Crypto 文件夹分析报告

## 🗂️ 文件夹结构概览

```
D:/Crypto/
├── CryCTF/                    # CTF 比赛笔记 (37个 Markdown 文件)
│   ├── BaseCTF 2024/
│   ├── CPCTF 2025/
│   ├── Cryptopal-learning/
│   ├── DiceCTF 2025/
│   ├── GHCTF 2025/
│   ├── imaginaryCTF/
│   ├── K!nd4SUS CTF 2025/
│   ├── L3HCTF2025/
│   ├── LFSR/                  # LFSR 流密码
│   ├── LitCTF 2025/
│   ├── Matrix_challenges/     # 矩阵/格密码
│   ├── Midnight flag CTF/
│   ├── Mini L-CTF 2025/
│   ├── N1CTF-junior/
│   ├── Nowruz1404/
│   ├── PascalCTF Beginners 2025/
│   ├── SHCTF 2023/
│   ├── TGCTF 2025/
│   ├── UMassCTF 2025/
│   ├── UTCTF2025/
│   ├── XYCTF/
│   ├── 轩辕杯/
│   ├── 中国能源网络大赛 2025/
│   ├── 机器学习/               # ML 相关密码学
│   └── 杂项/                  # LWE、LWE's primal attack等
│
├── Toolsfx/                   # CTF Crypto 工具箱 (Java GUI)
├── cado-nfs/                  # 大整数分解工具
├── RSAwienerHacker/           # Wiener 攻击工具
├── autokey cipher/            # Autokey 密码破解
├── CyberChef/                 # 编码转换神器
├── ECGEN/                     # 椭圆曲线生成
├── flatter/                   # 格基规约工具
├── gf2bv/                     # GF(2) 布尔向量
├── lll_cvp/                   # LLL/CVP 算法
├── msolve-0.9.1/              # 多项式方程求解
├── Pari/                      # PARI/GP 数论库
├── getroot3/                  # 多项式求根
├── MT19937-Symbolic-Execution/ # MT19937 伪随机数分析
├── RLWE and MLWE/             # 格密码学习
├── hashcat-7.1.2/             # 密码哈希破解
├── fastcoll/                  # MD5 碰撞生成
└── 数学教材.pdf                # An Introduction to Mathematical Cryptography
```

---

## 📝 笔记格式分析

### 标准格式 (题目 + 分析 + exp)

```markdown
## 题目名:
### 题面：
```python
# 题目代码和数据
```

### 分析：
详细的解题思路、数学推导、攻击原理

### 题解：
```python
# 完整的 exploit 代码
```
```

### 涵盖的密码学领域

| 类别 | 具体技术 | 笔记示例 |
|------|----------|----------|
| **RSA** | 基础 RSA、Wiener Attack、共模攻击、小指数攻击、公因数攻击 | BaseCTF babyrsa, ez_rsa |
| **AES** | ECB 模式、CBC 模式、密钥恢复 | BaseCTF helloCrypto |
| **流密码** | LFSR、NLFSR | LFSR/Bury the Light |
| **格密码** | LWE、RLWE、MLWE、Primal Attack | 杂项/LWE's primal attack |
| **古典密码** | 凯撒、Autokey、替换密码 | UTCTF2025 |
| **Hash** | MD5 爆破、彩虹表 | BaseCTF 你会算md5吗 |
| **背包问题** | 超递增序列、Merkle-Hellman | BaseCTF babypack |

---

## 🛠️ 可整合的工具

### 1. 已有的 Python 工具脚本

```
autokey cipher/
├── ngram_score.py      # n-gram 频率评分
├── quadgrams.txt       # 四元组频率表
├── solver.py           # Autokey 密码求解器
└── trigrams.txt        # 三元组频率表
```

### 2. 可封装的攻击代码

从笔记中提取的攻击实现：

| 攻击类型 | 来源 | 代码位置 |
|----------|------|----------|
| **LFSR 线性攻击** | SWPUCTF Bury the Light | lfsr.md |
| **LWE Primal Attack** | Matrices Matrices Matrices | 杂项/LWE's primal attack.md |
| **RSA 小指数** | UTCTF2025 | UTCTF2025.md |
| **Autokey 爆破** | UTCTF2025 | UTCTF2025.md |
| **MD5 字符爆破** | BaseCTF | BaseCTF 2024.md |

---

## 🎯 整合建议

### 方案 1: 提取工具到项目

将笔记中的 exploit 代码转换为 LangChain Tools：

```python
# 示例: LFSR 攻击工具
@tool
def lfsr_linear_attack(mask1: int, mask2: int, mask3: int, mask4: int, 
                       output: int, enc: str) -> str:
    """
    LFSR 组合流密码线性攻击
    来源: SWPUCTF 2024 Bury the Light
    """
    # 从 lfsr.md 提取的代码
    ...

# 示例: LWE Primal Attack 工具
@tool
def lwe_primal_attack(A: list, b: list, q: int, n: int, m: int) -> str:
    """
    LWE 问题的 Primal Attack
    来源: Kind4SUS CTF Matrices Matrices Matrices
    """
    # 从 LWE's primal attack.md 提取的代码
    ...
```

### 方案 2: 创建题目数据集

将笔记中的题目提取为标准的挑战格式：

```yaml
challenges/
├── rsa/
│   ├── babyrsa/           # 来自 BaseCTF
│   ├── ez_rsa/            # 来自 BaseCTF
│   └── wiener_attack/     # 来自 UTCTF
├── aes/
│   └── ecb_key_recovery/  # 来自 BaseCTF
├── lfsr/
│   └── bury_the_light/    # 来自 SWPUCTF
├── lwe/
│   └── primal_attack/     # 来自 Kind4SUS
└── classic/
    └── autokey/           # 来自 UTCTF
```

### 方案 3: 数据收集与训练

笔记中的 (题目, 分析, exp) 可以转换为训练数据：

```json
{
  "messages": [
    {"role": "system", "content": "你是 CTF 密码学专家"},
    {"role": "user", "content": "题目: [题面代码]"},
    {"role": "assistant", "content": "分析: [分析内容]\n\n解题代码:\n[exp代码]"}
  ]
}
```

---

## 📊 数据统计

| 指标 | 数量 |
|------|------|
| 总笔记文件 | 37 个 |
| RSA 题目 | ~15+ 道 |
| AES 题目 | ~5+ 道 |
| 流密码题目 | ~5+ 道 |
| 格密码题目 | ~5+ 道 |
| 古典密码题目 | ~10+ 道 |
| 外部工具 | 10+ 个 |

---

## 🚀 下一步行动建议

1. **提取经典题目的 exploit 代码** → 转换为 Tools
2. **整理题目数据集** → 用于 Agent 测试和训练
3. **分析笔记中的攻击模式** → 构建 Skill 模块
4. **使用已有工具** (ToolsFx, cado-nfs) → 作为外部 MCP 工具

要我帮你执行哪个步骤？
