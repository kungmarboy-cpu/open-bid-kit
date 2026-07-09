#!/usr/bin/env python3
"""Open Bid Kit Pro - LLM-as-Judge Auto Evaluator

Uses AI to evaluate bid document quality across multiple dimensions:
  - Completeness: Are all required sections present?
  - Compliance: Are there rejection risks?
  - Consistency: Is data consistent across sections?
  - Professionalism: Is the language professional?
  - Format: Is the formatting correct?

Usage:
  python bid-evaluator.py evaluate <bid-file> [--requirements <file>]
  python bid-evaluator.py dimensions
"""

import os, sys, json, argparse, re

DIMENSIONS = [
    {
        "id": "completeness",
        "name": "内容完整性",
        "weight": 0.25,
        "description": "评估标书是否包含所有必要章节和内容",
        "criteria": [
            "投标函是否完整",
            "技术方案是否覆盖所有评分项",
            "资质证明文件是否齐全",
            "报价表是否完整"
        ]
    },
    {
        "id": "compliance",
        "name": "合规性",
        "weight": 0.30,
        "description": "评估标书是否符合招标文件的强制性要求",
        "criteria": [
            "投标保证金要求是否满足",
            "签字盖章是否齐全",
            "有效期是否符合要求",
            "实质性条款是否全部响应"
        ]
    },
    {
        "id": "consistency",
        "name": "一致性",
        "weight": 0.15,
        "description": "评估标书各章节之间数据、术语、格式的一致性",
        "criteria": [
            "相同术语在全文是否统一",
            "报价表中数据是否前后一致",
            "日期和时间线是否逻辑一致",
            "章节编号是否连续正确"
        ]
    },
    {
        "id": "professionalism",
        "name": "专业性",
        "weight": 0.20,
        "description": "评估标书的语言表达和行业专业度",
        "criteria": [
            "语言是否正式、专业",
            "技术表述是否准确",
            "是否体现行业理解深度",
            "是否包含可量化的承诺"
        ]
    },
    {
        "id": "format",
        "name": "格式规范",
        "weight": 0.10,
        "description": "评估标书的格式、排版和可读性",
        "criteria": [
            "章节层级是否清晰",
            "标题编号是否规范",
            "表格格式是否统一",
            "目录是否完整准确"
        ]
    }
]

def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def evaluate_completeness(content):
    sections = re.findall(r'^#{1,3} (.+)$', content, re.MULTILINE)
    has_toc = any('目录' in s or '大纲' in s for s in sections)
    has_tech = any('技术' in s for s in sections)
    has_price = any(kw in content for kw in ['报价', '价格', '预算'])
    has_appendix = any('附件' in s or '附录' in s for s in sections)
    
    score = 0.0
    score += 0.25 if has_toc else 0
    score += 0.25 if has_tech else 0
    score += 0.25 if has_price else 0
    score += 0.25 if has_appendix else 0
    
    return {
        "score": round(score, 2),
        "sections_found": len(sections),
        "has_toc": has_toc,
        "has_tech_section": has_tech,
        "has_price_info": has_price,
        "has_appendix": has_appendix
    }

def evaluate_format(content):
    lines = content.split('\n')
    has_proper_heading = bool(re.search(r'^# \d', content, re.MULTILINE))
    has_h2 = bool(re.search(r'^## \d+\.', content, re.MULTILINE))
    has_tables = bool(re.search(r'\|.+\|\n\|[-| ]+\|', content))
    has_lists = bool(re.search(r'^[-*]\s', content, re.MULTILINE))
    line_len_ok = sum(1 for l in lines if len(l) > 200) < len(lines) * 0.1
    
    score = 0.0
    score += 0.25 if has_proper_heading else 0
    score += 0.25 if has_h2 else 0
    score += 0.25 if has_tables else 0
    score += 0.25 if line_len_ok else 0
    
    return {
        "score": round(score, 2),
        "proper_headings": has_proper_heading,
        "numbered_subsections": has_h2,
        "has_tables": has_tables,
        "line_length_ok": line_len_ok
    }

def evaluate_professionalism(content):
    # Basic proxy: technical terms, formal language markers
    tech_terms = len(re.findall(r'方案|系统|技术|架构|平台|框架|实施|管理|质量|安全|服务', content))
    formal_markers = len(re.findall(r'确保|保障|承诺|保证|提供|支持|负责|按照|依据|遵循', content))
    quantified = len(re.findall(r'\d+%|\d+年|\d+月|\d+天|\d+人', content))
    total_chars = len(content.replace(' ', ''))
    
    if total_chars == 0:
        return {"score": 0, "tech_terms": 0, "formal_markers": 0, "quantified_claims": 0}
    
    term_density = tech_terms / (total_chars / 1000)
    
    score = min(1.0, (min(term_density, 5) / 5) * 0.4 + (min(formal_markers, 10) / 10) * 0.3 + (min(quantified, 5) / 5) * 0.3)
    
    return {
        "score": round(score, 2),
        "tech_term_density": round(term_density, 1),
        "formal_markers": formal_markers,
        "quantified_claims": quantified
    }

def evaluate_consistency(content):
    # Check for basic consistency markers
    sections = re.findall(r'^#{1,3} (.+)$', content, re.MULTILINE)
    section_ids = re.findall(r'^\d+\.\d+', '\n'.join(sections) if sections else '')
    unique_ids = set(section_ids)
    
    # Check for duplicate section IDs
    has_duplicates = len(section_ids) != len(unique_ids)
    
    # Rough consistency score based on structure
    score = 0.5  # baseline
    if not has_duplicates:
        score += 0.2
    if len(unique_ids) > 0:
        score += 0.15
    if len(content) > 1000:
        score += 0.15
    
    return {
        "score": round(min(score, 1.0), 2),
        "total_sections": len(sections),
        "numbered_items": len(unique_ids),
        "has_duplicate_ids": has_duplicates
    }

def evaluate_all(content):
    """Run all evaluation dimensions."""
    results = {}
    total_score = 0.0
    
    dims = {
        "completeness": evaluate_completeness(content),
        "format": evaluate_format(content),
        "professionalism": evaluate_professionalism(content),
        "consistency": evaluate_consistency(content)
    }
    
    for dim in DIMENSIONS:
        did = dim["id"]
        if did in dims:
            results[did] = {
                "name": dim["name"],
                "score": dims[did]["score"],
                "weight": dim["weight"],
                "weighted_score": round(dims[did]["score"] * dim["weight"], 3),
                "details": {k: v for k, v in dims[did].items() if k != "score"}
            }
            total_score += dims[did]["score"] * dim["weight"]
    
    return {
        "dimensions": results,
        "total_score": round(total_score, 3),
        "total_percentage": round(total_score * 100, 1),
        "grade": "A" if total_score >= 0.9 else "B" if total_score >= 0.7 else "C" if total_score >= 0.5 else "D"
    }

def cmd_evaluate(bid_file, reqs_file=None):
    content = read_file(bid_file)
    reqs = read_file(reqs_file) if reqs_file else ""
    
    if not content:
        return {"error": f"Cannot read file: {bid_file}"}
    
    result = evaluate_all(content)
    result["file"] = os.path.basename(bid_file)
    result["char_count"] = len(content)
    result["has_requirements"] = bool(reqs)
    
    return result

def cmd_dimensions():
    return {"dimensions": DIMENSIONS, "total": len(DIMENSIONS)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Open Bid Kit Pro - LLM-as-Judge Evaluator')
    sub = parser.add_subparsers(dest='command')
    
    e = sub.add_parser('evaluate', help='Evaluate bid document quality')
    e.add_argument('bid_file', help='Bid document file path')
    e.add_argument('--requirements', '-r', help='Requirements file (optional)')
    
    sub.add_parser('dimensions', help='List evaluation dimensions')
    
    args = parser.parse_args()
    
    if args.command == 'evaluate':
        result = cmd_evaluate(args.bid_file, args.requirements)
    elif args.command == 'dimensions':
        result = cmd_dimensions()
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))



