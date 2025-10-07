#!/usr/bin/env python3
"""
相似度分析脚本使用示例
"""

import subprocess
import sys
import os

def run_analysis(keyword, article_ids, output_file=None):
    """运行相似度分析"""
    cmd = [
        sys.executable, 
        "scripts/analyze_similarity.py", 
        keyword, 
        article_ids
    ]
    
    if output_file:
        cmd.extend(["--output", output_file])
    
    print(f"🔍 运行分析: {keyword} -> {article_ids}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 分析成功")
        print(result.stdout)
    else:
        print("❌ 分析失败")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """主函数"""
    print("📊 相似度分析示例")
    print("=" * 50)
    
    # 示例1: 分析爱因斯坦相关文章
    print("\n1. 分析爱因斯坦相关文章")
    einstein_articles = "{298,688,1611,1994,3022,6853,6876,7350,7899,8119,8282}"
    run_analysis("爱因斯坦", einstein_articles, "einstein_analysis.json")
    
    # 示例2: 分析亚历山大相关文章
    print("\n2. 分析亚历山大相关文章")
    alexander_articles = "{8282}"
    run_analysis("亚历山大", alexander_articles, "alexander_analysis.json")
    
    # 示例3: 分析编程相关文章
    print("\n3. 分析编程相关文章")
    programming_articles = "{99,165,197,212}"
    run_analysis("编程", programming_articles, "programming_analysis.json")
    
    print("\n✅ 所有分析完成！")

if __name__ == "__main__":
    main()
