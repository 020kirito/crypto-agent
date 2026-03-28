"""
通用工具函数
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv


def load_env():
    """加载环境变量"""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ 已加载 .env 文件")
    else:
        print("⚠️  未找到 .env 文件，使用系统环境变量")


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger()


def save_result(result: dict, filepath: str):
    """保存结果到 JSON 文件"""
    import json
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"💾 结果已保存: {path}")
