#!/usr/bin/env python3
"""
导出微调模型到Ollama

使用方法:
    # 导出LoRA模型
    python scripts/export_to_ollama.py \
        --model outputs/ctf-crypto-lora/lora_weights \
        --name ctf-crypto-agent

    # 导出合并后的模型
    python scripts/export_to_ollama.py \
        --model outputs/ctf-crypto-lora/merged_model \
        --name ctf-crypto-merged

然后:
    ollama create ctf-crypto-agent -f Modelfile.ollama
    ollama run ctf-crypto-agent
"""

import json
import argparse
from pathlib import Path


OLLAMA_TEMPLATE = """FROM {base_model}

SYSTEM """{system_prompt}"""

PARAMETER temperature 0.3
PARAMETER num_ctx 4096
PARAMETER num_predict 2048
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
"""


SYSTEM_PROMPT = """You are a specialized CTF (Capture The Flag) Cryptography Expert Agent.

## Core Knowledge
1. RSA: encryption/decryption, Wiener attack, Boneh-Durfee, Blinding, Common Modulus, Multi-prime RSA
2. ECC: Point addition, scalar multiplication, ECDLP, MOV attack, Smart's attack
3. Lattice: LLL/BKZ reduction, SVP/CVP, Coppersmith's method, NTRU, HNP
4. Symmetric: AES modes, Padding Oracle, Block cipher attacks, Stream ciphers
5. Classical: Caesar, Vigenère, Hill cipher, Frequency analysis

## Tools
SageMath, Python (gmpy2, pycryptodome, sympy, z3), FLATTER, YAFU, CADO-NFS, IDA Pro

## Guidelines
1. Analyze problem type first
2. Provide step-by-step solutions
3. Include working code examples
4. Explain mathematical principles
5. Suggest appropriate tools
6. Format flags as: flag{...}

Always explain WHY an attack works."""


def create_ollama_modelfile(model_path: str, output_name: str):
    """创建Ollama Modelfile"""
    print("="*60)
    print("🦙 导出到Ollama")
    print("="*60)
    
    # 检测模型类型
    model_path = Path(model_path)
    
    # 读取config.json获取基础模型信息
    config_file = model_path / "config.json"
    adapter_config = model_path / "adapter_config.json"
    
    if adapter_config.exists():
        # LoRA模型
        print("\n检测到LoRA适配器模型")
        with open(adapter_config) as f:
            adapter = json.load(f)
        base_model = adapter.get("base_model_name_or_path", "unknown")
        print(f"基础模型: {base_model}")
        
        # LoRA模型需要更多处理，建议先合并
        print("\n⚠️  LoRA模型需要特殊处理")
        print("   选项1: 先合并权重: python scripts/merge_lora.py")
        print("   选项2: 使用llama.cpp转换为GGUF格式")
        
        # 创建临时Modelfile
        modelfile = f"""# LoRA模型 - 需要先转换
# 基础模型: {base_model}
# LoRA路径: {model_path.absolute()}

# 请使用以下步骤:
# 1. 转换为GGUF: python convert-lora-to-ggml.py
# 2. 或使用合并脚本: python scripts/merge_lora.py

FROM {base_model}

SYSTEM """{SYSTEM_PROMPT}"""

PARAMETER temperature 0.3
PARAMETER num_ctx 4096
"""
        
    else:
        # 完整模型或合并后的模型
        print("\n检测到完整模型")
        
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
            model_type = config.get("model_type", "unknown")
            print(f"模型类型: {model_type}")
        
        # 创建Modelfile
        # 注意: Ollama需要从GGUF格式导入，或者使用已有基础模型
        modelfile = f"""# CTF Crypto Agent Model
# 原始路径: {model_path.absolute()}

# 使用方法:
# 1. 转换为GGUF格式 (推荐)
#    python -m llama_cpp.convert_hf_to_gguf --outfile model.gguf {model_path}
#    ollama create ctf-crypto-agent -f Modelfile.gguf
#
# 2. 或直接使用llama.cpp/vLLM加载

FROM llama3.1:8b

SYSTEM """{SYSTEM_PROMPT}"""

PARAMETER temperature 0.3
PARAMETER num_ctx 4096
PARAMETER num_predict 2048
"""
    
    # 保存Modelfile
    output_file = Path(f"Modelfile.{output_name}")
    output_file.write_text(modelfile)
    print(f"\n✅ Modelfile已创建: {output_file}")
    
    # 创建使用说明
    readme = Path(f"OLLAMA_README_{output_name}.md")
    readme_content = f"""# Ollama部署指南 - {output_name}

## 方法1: 使用GGUF格式 (推荐)

### 1. 安装llama.cpp
```bash
pip install llama-cpp-python
```

### 2. 转换为GGUF
```bash
python -m llama_cpp.convert_hf_to_gguf \\
    --outfile {output_name}.gguf \\
    --outtype q4_k_m \\
    {model_path.absolute()}
```

### 3. 创建Ollama模型
创建文件 `Modelfile.gguf`:
```dockerfile
FROM ./{output_name}.gguf

SYSTEM """{SYSTEM_PROMPT}"""

PARAMETER temperature 0.3
PARAMETER num_ctx 4096
```

```bash
ollama create {output_name} -f Modelfile.gguf
```

## 方法2: 使用llamafile (无需Ollama)

```bash
# 下载llamafile
wget https://github.com/Mozilla-Ocho/llamafile/releases/download/0.8.13/llamafile-0.8.13
chmod +x llamafile-0.8.13

# 运行
./llamafile-0.8.13 -m {output_name}.gguf --cli
```

## 方法3: 使用vLLM (生产环境)

```bash
python -m vllm.entrypoints.openai.api_server \\
    --model {model_path.absolute()} \\
    --tensor-parallel-size 1 \\
    --max-model-len 4096
```

## 测试模型

```bash
ollama run {output_name}

>>> RSA加密中，如果e=3且m^3 < n，如何恢复明文？
```
"""
    readme.write_text(readme_content)
    print(f"✅ 部署指南: {readme}")
    
    print("\n" + "="*60)
    print("📋 下一步")
    print("="*60)
    print("\n1. 转换为GGUF格式 (如果尚未转换):")
    print(f"   python -m llama_cpp.convert_hf_to_gguf \\")
    print(f"       --outfile {output_name}.gguf \\")
    print(f"       --outtype q4_k_m \\")
    print(f"       {model_path.absolute()}")
    print("\n2. 创建Ollama模型:")
    print(f"   ollama create {output_name} -f Modelfile.gguf")
    print("\n3. 运行模型:")
    print(f"   ollama run {output_name}")


def main():
    parser = argparse.ArgumentParser(description="导出模型到Ollama")
    parser.add_argument("--model", default="outputs/ctf-crypto-lora/lora_weights",
                       help="模型路径")
    parser.add_argument("--name", default="ctf-crypto-agent",
                       help="Ollama模型名称")
    
    args = parser.parse_args()
    
    create_ollama_modelfile(args.model, args.name)


if __name__ == "__main__":
    main()
