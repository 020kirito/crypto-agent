#!/usr/bin/env python3
"""
分析博客爬取数据

分析从糖醋小鸡块博客爬取的writeup，生成:
1. 工具使用频率统计
2. 攻击类型分布
3. 代码片段库
4. 学习路径推荐
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List


def analyze_blog_data(data_dir: str = "data/tangcu_blog"):
    """分析博客数据"""
    data_path = Path(data_dir)
    
    # 读取数据文件
    files = {
        'writeups': data_path / "writeups_raw.json",
        'tools': data_path / "extracted_tools.json",
        'resources': data_path / "extracted_resources.json",
        'stats': data_path / "collection_stats.json"
    }
    
    results = {}
    
    # 1. 基础统计
    if files['stats'].exists():
        with open(files['stats'], 'r', encoding='utf-8') as f:
            stats = json.load(f)
        results['stats'] = stats
        print("="*60)
        print("📊 基础统计")
        print("="*60)
        print(f"Writeup数量: {stats.get('total_writeups', 0)}")
        print(f"代码片段: {stats.get('code_snippets_total', 0)}")
        print(f"数学公式: {stats.get('math_formulas_total', 0)}")
        print(f"独特工具: {stats.get('unique_tools', 0)}")
        print(f"资源链接: {stats.get('resources_total', 0)}")
    
    # 2. 工具分析
    if files['tools'].exists():
        with open(files['tools'], 'r', encoding='utf-8') as f:
            tools = json.load(f)
        
        print("\n" + "="*60)
        print("🛠️ 工具使用分析")
        print("="*60)
        
        # 按名称统计
        tool_names = [t['name'] for t in tools]
        name_counter = Counter(tool_names)
        print("\n最常用工具 TOP 15:")
        for name, count in name_counter.most_common(15):
            print(f"  {name:<25} {count:>3} 次")
        
        # 按类别统计
        categories = [t['category'] for t in tools]
        cat_counter = Counter(categories)
        print("\n工具类别分布:")
        for cat, count in cat_counter.most_common():
            print(f"  {cat:<15} {count:>3} 次")
        
        results['tools'] = {
            'total': len(tools),
            'unique': len(name_counter),
            'top_tools': name_counter.most_common(15),
            'by_category': dict(cat_counter)
        }
    
    # 3. Writeup分析
    if files['writeups'].exists():
        with open(files['writeups'], 'r', encoding='utf-8') as f:
            writeups = json.load(f)
        
        print("\n" + "="*60)
        print("📝 Writeup分析")
        print("="*60)
        
        # 分类统计
        categories = [w.get('category', 'unknown') for w in writeups]
        cat_counter = Counter(categories)
        print("\n分类分布:")
        for cat, count in cat_counter.most_common():
            print(f"  {cat:<15} {count:>3} 篇")
        
        # 标签统计
        all_tags = []
        for w in writeups:
            all_tags.extend(w.get('tags', []))
        tag_counter = Counter(all_tags)
        print("\n热门标签 TOP 10:")
        for tag, count in tag_counter.most_common(10):
            print(f"  {tag:<20} {count:>3} 次")
        
        # 代码最多的文章
        code_counts = [(w['title'], len(w.get('code_snippets', []))) 
                       for w in writeups]
        code_counts.sort(key=lambda x: -x[1])
        print("\n代码最丰富的文章 TOP 5:")
        for title, count in code_counts[:5]:
            print(f"  {title[:40]:<40} {count:>2} 个代码块")
        
        results['writeups'] = {
            'total': len(writeups),
            'by_category': dict(cat_counter),
            'top_tags': tag_counter.most_common(10),
            'most_code': code_counts[:5]
        }
    
    # 4. 资源分析
    if files['resources'].exists():
        with open(files['resources'], 'r', encoding='utf-8') as f:
            resources = json.load(f)
        
        print("\n" + "="*60)
        print("🔗 资源链接分析")
        print("="*60)
        
        # 按类型统计
        types = [r.get('resource_type', 'unknown') for r in resources]
        type_counter = Counter(types)
        print("\n资源类型分布:")
        for rtype, count in type_counter.most_common():
            print(f"  {rtype:<15} {count:>3} 个")
        
        results['resources'] = {
            'total': len(resources),
            'by_type': dict(type_counter)
        }
    
    # 5. 生成学习建议
    print("\n" + "="*60)
    print("📚 学习路径建议")
    print("="*60)
    
    if 'tools' in results:
        print("\n🎯 核心工具学习顺序:")
        for i, (tool, count) in enumerate(results['tools']['top_tools'][:5], 1):
            print(f"  {i}. {tool} ({count} 次使用)")
    
    if 'writeups' in results:
        print("\n📖 推荐阅读:")
        for i, (title, count) in enumerate(results['writeups'].get('most_code', [])[:3], 1):
            print(f"  {i}. {title} ({count} 个代码示例)")
    
    # 6. 保存分析报告
    report_file = data_path / "analysis_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 分析报告已保存: {report_file}")
    
    return results


def generate_tool_knowledge_base(data_dir: str = "data/tangcu_blog"):
    """生成工具知识库"""
    data_path = Path(data_dir)
    tools_file = data_path / "extracted_tools.json"
    
    if not tools_file.exists():
        print(f"❌ 找不到文件: {tools_file}")
        return
    
    with open(tools_file, 'r', encoding='utf-8') as f:
        tools = json.load(f)
    
    # 按工具分组
    tools_dict = defaultdict(list)
    for t in tools:
        tools_dict[t['name']].append(t)
    
    # 生成知识库
    knowledge_base = []
    for tool_name, usages in tools_dict.items():
        # 收集所有使用场景
        contexts = [u['context'] for u in usages if u['context']]
        codes = [u['code_example'] for u in usages if u['code_example']]
        
        knowledge_base.append({
            'tool': tool_name,
            'category': usages[0]['category'],
            'usage_count': len(usages),
            'contexts': contexts[:5],  # 最多5个场景
            'code_examples': codes[:3]  # 最多3个代码示例
        })
    
    # 保存知识库
    kb_file = data_path / "tool_knowledge_base.json"
    with open(kb_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    
    print(f"💾 工具知识库已保存: {kb_file} ({len(knowledge_base)} 个工具)")
    
    # 生成Markdown文档
    md_file = data_path / "TOOL_GUIDE.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# CTF Crypto 工具使用指南\n\n")
        f.write("> 从糖醋小鸡块博客提取的工具使用经验\n\n")
        
        # 按类别分组
        by_category = defaultdict(list)
        for kb in knowledge_base:
            by_category[kb['category']].append(kb)
        
        for category, tools in sorted(by_category.items()):
            f.write(f"## {category.upper()}\n\n")
            
            for tool in sorted(tools, key=lambda x: -x['usage_count']):
                f.write(f"### {tool['tool']}\n\n")
                f.write(f"**使用次数**: {tool['usage_count']}\n\n")
                
                if tool['contexts']:
                    f.write("**使用场景**:\n\n")
                    for i, ctx in enumerate(tool['contexts'][:3], 1):
                        f.write(f"{i}. {ctx[:200]}...\n\n")
                
                if tool['code_examples']:
                    f.write("**代码示例**:\n\n```python\n")
                    f.write(tool['code_examples'][0][:500])
                    f.write("\n```\n\n")
                
                f.write("---\n\n")
    
    print(f"💾 Markdown指南: {md_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="分析博客数据")
    parser.add_argument("--data-dir", "-d", default="data/tangcu_blog", help="数据目录")
    parser.add_argument("--kb", action="store_true", help="生成知识库")
    
    args = parser.parse_args()
    
    # 分析数据
    analyze_blog_data(args.data_dir)
    
    # 生成知识库
    if args.kb:
        print("\n" + "="*60)
        generate_tool_knowledge_base(args.data_dir)


if __name__ == "__main__":
    main()
