#!/usr/bin/env python3
"""
将 CTF 笔记转换为训练数据

从笔记中提取 (题目, 分析, exp) 转换为 JSONL 格式用于模型训练

使用示例:
    python scripts/convert_notes_to_training.py --input "/mnt/d/Crypto/CryCTF" --output data/training/ctf_crypto.jsonl
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Any


def extract_problem_from_note(content: str) -> List[Dict[str, Any]]:
    """
    从笔记内容中提取题目
    
    格式：
    ## 题目名:
    ### 题面：
    ```python
    # 题目代码
    ```
    ### 分析：
    ### 题解：
    ```python
    # exploit 代码
    ```
    """
    problems = []
    
    # 分割不同的题目 (以 ## 开头)
    sections = re.split(r'\n## ', content)
    
    for section in sections:
        if not section.strip():
            continue
        
        # 提取题目名
        title_match = re.match(r'([^\n]+)', section)
        if not title_match:
            continue
        
        title = title_match.group(1).strip().rstrip(':')
        
        # 提取题面
        problem_match = re.search(r'### 题面[：:]\s*\n```python\n(.*?)```', section, re.DOTALL)
        problem_code = problem_match.group(1).strip() if problem_match else ""
        
        # 如果没有代码块，尝试提取纯文本题面
        if not problem_code:
            problem_text_match = re.search(r'### 题面[：:]\s*\n(.*?)(?=###|##|$)', section, re.DOTALL)
            problem_code = problem_text_match.group(1).strip() if problem_text_match else ""
        
        # 提取分析
        analysis_match = re.search(r'### 分析[：:]\s*\n(.*?)(?=###|##|$)', section, re.DOTALL)
        analysis = analysis_match.group(1).strip() if analysis_match else ""
        
        # 提取题解代码
        solution_match = re.search(r'### 题解[：:]\s*\n```python\n(.*?)```', section, re.DOTALL)
        solution_code = solution_match.group(1).strip() if solution_match else ""
        
        # 只保存有完整信息的题目
        if problem_code and solution_code:
            problems.append({
                "title": title,
                "problem": problem_code,
                "analysis": analysis,
                "solution": solution_code
            })
    
    return problems


def convert_to_openai_format(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换为 OpenAI fine-tuning 格式
    
    格式：
    {
      "messages": [
        {"role": "system", "content": "你是 CTF 密码学专家"},
        {"role": "user", "content": "题目: ..."},
        {"role": "assistant", "content": "分析: ...\n\n解题代码:\n..."}
      ]
    }
    """
    # 构建用户消息 (题目)
    user_content = f"题目: {problem['title']}\n\n{problem['problem'][:2000]}"  # 限制长度
    
    # 构建助手消息 (分析和题解)
    assistant_content = ""
    if problem['analysis']:
        assistant_content += f"分析: {problem['analysis'][:1000]}\n\n"
    assistant_content += f"解题代码:\n```python\n{problem['solution'][:2000]}\n```"
    
    return {
        "messages": [
            {"role": "system", "content": "你是 CTF 密码学解题专家。请分析题目并给出完整的解题代码。"},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ],
        "metadata": {
            "title": problem['title'],
            "has_analysis": bool(problem['analysis'])
        }
    }


def process_notes_directory(input_dir: str, output_file: str):
    """处理笔记目录"""
    input_path = Path(input_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_problems = []
    md_files = list(input_path.rglob("*.md"))
    
    print(f"📁 找到 {len(md_files)} 个 Markdown 文件")
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            problems = extract_problem_from_note(content)
            
            for problem in problems:
                problem['source'] = str(md_file.relative_to(input_path))
                all_problems.append(problem)
                
        except Exception as e:
            print(f"⚠️  处理 {md_file} 失败: {e}")
    
    print(f"📊 共提取 {len(all_problems)} 个题目")
    
    # 去重 (基于题目内容)
    seen = set()
    unique_problems = []
    for p in all_problems:
        key = p['title'] + p['problem'][:100]
        if key not in seen:
            seen.add(key)
            unique_problems.append(p)
    
    print(f"✨ 去重后: {len(unique_problems)} 个唯一题目")
    
    # 保存为 JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for problem in unique_problems:
            sample = convert_to_openai_format(problem)
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"💾 已保存到: {output_path}")
    
    # 统计信息
    categories = {}
    for p in unique_problems:
        # 从标题或源码推断类别
        title_lower = p['title'].lower()
        code_lower = p['problem'].lower()
        
        if 'rsa' in title_lower or 'rsa' in code_lower:
            cat = 'RSA'
        elif 'aes' in title_lower or 'aes' in code_lower:
            cat = 'AES'
        elif 'lfsr' in title_lower or 'lfsr' in code_lower:
            cat = 'LFSR'
        elif 'lwe' in title_lower or 'lattice' in title_lower:
            cat = 'LWE/Lattice'
        elif 'md5' in title_lower or 'hash' in title_lower:
            cat = 'Hash'
        elif 'caesar' in title_lower or 'cipher' in title_lower:
            cat = 'Classical'
        else:
            cat = 'Other'
        
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📈 分类统计:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    return len(unique_problems)


def main():
    parser = argparse.ArgumentParser(description="转换 CTF 笔记为训练数据")
    parser.add_argument(
        "--input", "-i",
        default="/mnt/d/Crypto/CryCTF",
        help="笔记目录 (默认: /mnt/d/Crypto/CryCTF)"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/training/ctf_crypto.jsonl",
        help="输出文件 (默认: data/training/ctf_crypto.jsonl)"
    )
    
    args = parser.parse_args()
    
    print("🚀 开始转换 CTF 笔记...")
    count = process_notes_directory(args.input, args.output)
    print(f"\n✅ 完成! 共转换 {count} 个题目")


if __name__ == "__main__":
    main()
