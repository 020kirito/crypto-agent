#!/usr/bin/env python3
"""
批量提取所有做题笔记为训练数据

使用示例:
    python scripts/extract_all_notes.py
"""

import json
import re
from pathlib import Path


def extract_from_note(content: str, source_file: str):
    """从单个笔记提取题目"""
    problems = []
    
    # 分割题目 (多种格式)
    # 格式1: ## 题目名
    # 格式2: ### [比赛名]题目名
    sections = re.split(r'\n##\s+|\n###\s+', content)
    
    for section in sections:
        if not section.strip() or len(section) < 100:
            continue
        
        # 提取标题
        title_match = re.match(r'([^\n]+)', section)
        if not title_match:
            continue
        
        title = title_match.group(1).strip()
        
        # 跳过非题目部分
        if any(skip in title.lower() for skip in ['总结', '参考', '前言', '介绍', '目录']):
            continue
        
        # 提取题面
        problem = ""
        problem_patterns = [
            r'(?:题面|题目)[：:]\s*```python\n(.*?)```',
            r'```python\n(.*?)```',
        ]
        for pattern in problem_patterns:
            match = re.search(pattern, section, re.DOTALL)
            if match:
                problem = match.group(1).strip()
                break
        
        # 提取题解
        solution = ""
        solution_patterns = [
            r'(?:题解|exp|解决)[：:]\s*```python\n(.*?)```',
            r'```python\n(.*?)```(?!.*```)',  # 最后一个python代码块
        ]
        for pattern in solution_patterns:
            match = re.search(pattern, section, re.DOTALL)
            if match:
                solution = match.group(1).strip()
                break
        
        # 提取分析
        analysis = ""
        analysis_match = re.search(r'(?:分析|思路)[：:]\s*(.*?)(?=###|##|$)', section, re.DOTALL)
        if analysis_match:
            analysis = analysis_match.group(1).strip()[:500]
        
        if problem and solution and len(solution) > 50:
            problems.append({
                'title': title,
                'problem': problem[:2000],
                'solution': solution[:2000],
                'analysis': analysis,
                'source': source_file
            })
    
    return problems


def main():
    notes_dir = Path("/mnt/d/Crypto/做题笔记")
    output_file = Path("data/training/all_notes.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    all_problems = []
    md_files = list(notes_dir.rglob("*.md"))
    
    print(f"📁 扫描到 {len(md_files)} 个 Markdown 文件")
    
    for i, md_file in enumerate(md_files, 1):
        if i % 10 == 0:
            print(f"  处理中... {i}/{len(md_files)}")
        
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            problems = extract_from_note(content, md_file.name)
            all_problems.extend(problems)
        except Exception as e:
            print(f"  ⚠️  {md_file.name}: {e}")
    
    print(f"\n📊 共提取 {len(all_problems)} 个题目")
    
    # 去重
    seen = set()
    unique = []
    for p in all_problems:
        key = p['title'] + p['problem'][:100]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    print(f"✨ 去重后: {len(unique)} 个唯一题目")
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        for p in unique:
            sample = {
                "messages": [
                    {"role": "system", "content": "你是 CTF 密码学解题专家"},
                    {"role": "user", "content": f"题目: {p['title']}\n\n{p['problem']}"},
                    {"role": "assistant", "content": f"分析: {p['analysis']}\n\n解题代码:\n```python\n{p['solution']}\n```"}
                ],
                "metadata": {
                    "source": p['source'],
                    "title": p['title']
                }
            }
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"💾 已保存到: {output_file}")
    
    # 分类统计
    categories = {}
    for p in unique:
        text = (p['title'] + p['problem']).lower()
        if 'rsa' in text:
            cat = 'RSA'
        elif 'ecc' in text or '椭圆' in text:
            cat = 'ECC'
        elif 'lattice' in text or 'lll' in text or 'hnp' in text:
            cat = 'Lattice'
        elif 'lfsr' in text:
            cat = 'LFSR'
        elif 'aes' in text:
            cat = 'AES'
        elif 'md5' in text or 'hash' in text:
            cat = 'Hash'
        elif 'copper' in text:
            cat = 'CopperSmith'
        elif 'ntru' in text:
            cat = 'NTRU'
        elif 'dlp' in text or 'discrete' in text:
            cat = 'DLP'
        else:
            cat = 'Other'
        
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📈 分类统计:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
