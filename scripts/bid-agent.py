#!/usr/bin/env python3
"""Open Bid Kit Pro - CLI tool for bid document workflows.

Usage:
  python bid-agent.py extract <file>      Extract headings and structure
  python bid-agent.py preview <file>      Generate HTML preview  
  python bid-agent.py outline <file>      Generate outline from requirements
  python bid-agent.py check <bid> <reqs>  Run compliance check
  python bid-agent.py models              List supported AI models
"""

import os, sys, json, re, argparse

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PLUGIN_ROOT, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_file(path):
    if not os.path.exists(path):
        print(f'Error: File not found: {path}', file=sys.stderr)
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def cmd_extract(filepath):
    """Extract structure from a bid document (markdown)."""
    content = read_file(filepath)
    
    # Detect all heading levels
    h1 = re.findall(r'^# (.+)$', content, re.MULTILINE)
    h2 = re.findall(r'^## (.+)$', content, re.MULTILINE)
    h3 = re.findall(r'^### (.+)$', content, re.MULTILINE)
    
    # Detect tables
    has_tables = bool(re.search(r'\|.+\|\n\|[-| ]+\|', content))
    
    # Detect code blocks
    code_blocks = len(re.findall(r'```', content)) // 2
    
    # Count words (Chinese + English)
    char_count = len(re.sub(r'\s', '', content))
    en_words = len(re.findall(r'[a-zA-Z]+', content))
    
    result = {
        'file': os.path.basename(filepath),
        'chars': char_count,
        'en_words': en_words,
        'structure': {
            'h1': h1,
            'h2': h2,
            'h3': h3,
        },
        'features': {
            'tables': has_tables,
            'code_blocks': code_blocks,
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_preview(filepath):
    """Generate a browser-ready HTML preview."""
    content = read_file(filepath)
    try:
        import markdown
    except ImportError:
        print('Run: pip install markdown', file=sys.stderr)
        sys.exit(1)
    
    body = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Bid Preview - {os.path.basename(filepath)}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Microsoft YaHei','SimSun',serif;background:#f0f2f5;color:#333}}
.toolbar{{background:#1a1a2e;color:#fff;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}}
.toolbar h1{{font-size:16px;font-weight:500}}
.toolbar .meta{{color:rgba(255,255,255,0.6);font-size:13px}}
.container{{max-width:900px;margin:0 auto;padding:40px 24px 80px}}
.doc-card{{background:#fff;padding:60px 80px;box-shadow:0 2px 12px rgba(0,0,0,0.08);border-radius:4px;line-height:1.8;min-height:800px}}
.doc-card h1{{font-size:22px;text-align:center;margin-bottom:32px;padding-bottom:16px;border-bottom:2px solid #1a1a2e}}
.doc-card h2{{font-size:18px;margin:24px 0 12px;color:#1a1a2e;border-left:4px solid #e94560;padding-left:12px}}
.doc-card h3{{font-size:16px;margin:16px 0 8px;color:#444}}
.doc-card p{{margin:8px 0;text-indent:2em}}
.doc-card table{{width:100%;border-collapse:collapse;margin:16px 0}}
.doc-card th,.doc-card td{{border:1px solid #ddd;padding:8px 12px;text-align:left}}
.doc-card th{{background:#f8f9fa;font-weight:600}}
.doc-card pre{{background:#f5f5f5;padding:16px;border-radius:4px;overflow-x:auto;font-size:14px}}
.doc-card code{{background:#f5f5f5;padding:2px 6px;border-radius:3px;font-size:14px}}
.doc-card ul,.doc-card ol{{margin:8px 0 8px 24px}}
@media print{{.toolbar{{display:none}}.container{{padding:0}}.doc-card{{box-shadow:none;padding:40px}}}}
</style></head>
<body>
<div class="toolbar"><h1>Open Bid Kit Pro</h1><span class="meta">{os.path.basename(filepath)}</span></div>
<div class="container"><div class="doc-card">{body}</div></div>
</body></html>'''
    
    out = os.path.join(os.path.dirname(filepath) or OUTPUT_DIR, '_preview.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Preview: file:///{os.path.abspath(out).replace(os.sep, "/")}')

def cmd_outline(filepath):
    """Generate outline structure from requirements file."""
    content = read_file(filepath)
    
    # Extract key requirements to suggest outline structure
    h2_sections = re.findall(r'^## (.+)$', content, re.MULTILINE)
    
    template = {
        'status': 'outline_ready',
        'source_sections': h2_sections,
        'outline_schema': {
            'outline': [
                {
                    'id': '1', 'title': '投标方案综述',
                    'description': '综合阐述对项目的理解、总体思路和核心优势',
                    'children': [
                        {'id': '1.1', 'title': '项目背景与理解', 'description': '对项目需求的深入分析和理解'},
                        {'id': '1.2', 'title': '总体建设思路', 'description': '项目的总体设计理念'},
                        {'id': '1.3', 'title': '核心优势', 'description': '投标人的核心竞争力'}
                    ]
                },
                {
                    'id': '2', 'title': '技术方案',
                    'description': '详细技术方案设计',
                    'children': []
                }
            ]
        },
        'next': 'Review outline, fill children arrays, then generate content with AI'
    }
    print(json.dumps(template, ensure_ascii=False, indent=2))

def cmd_check(bid_file, reqs_file):
    """Run compliance check checklist."""
    bid_content = read_file(bid_file)
    reqs = read_file(reqs_file) if os.path.exists(reqs_file) else reqs_file
    
    checks = [
        ('保证金', '投标保证金金额、提交方式、提交时间'),
        ('签字盖章', '法定代表人签字、公司盖章'),
        ('有效期', '投标有效期'),
        ('格式一致性', '文档格式符合招标要求'),
        ('内容一致性', '前后文数据、金额、日期一致'),
        ('重复率', '内容重复或抄袭'),
        ('价格合理性', '报价逻辑和竞争性'),
        ('资质完整性', '所需资质证书'),
        ('人员配置', '项目人员资历和数量'),
        ('业绩要求', '类似项目业绩'),
        ('技术参数', '关键技术参数响应'),
        ('实质性条款', '标注*的实质性条款'),
        ('偏离表', '商务/技术偏离表'),
        ('授权委托', '授权委托书'),
        ('财务报表', '财务状况资料'),
        ('社保纳税', '社保缴纳和纳税记录'),
        ('联合体协议', '联合体协议书'),
        ('分包说明', '分包方案'),
        ('页码目录', '页码和目录'),
        ('密封要求', '投标文件密封'),
        ('递交时间', '投标截止时间'),
    ]
    
    result = {
        'bid_file': os.path.basename(bid_file),
        'bid_chars': len(bid_content),
        'checklist': [
            {'id': i+1, 'item': name, 'description': desc}
            for i, (name, desc) in enumerate(checks)
        ],
        'action': 'Review each check item against the bid document using AI analysis',
        'templates': {
            'pass': {'status': 'passed', 'evidence': '...', 'suggestion': ''},
            'fail': {'status': 'failed', 'risk': 'high', 'evidence': '...', 'suggestion': '...'},
            'confirm': {'status': 'needs_confirmation', 'reason': 'requires offline verification'}
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_models():
    """List supported AI models."""
    models = {
        'providers': [
            {'name': 'DeepSeek', 'models': ['deepseek-chat', 'deepseek-reasoner'], 'best_for': 'Cost-effective, Chinese content'},
            {'name': 'OpenAI', 'models': ['gpt-4o', 'gpt-4o-mini'], 'best_for': 'Quality, international'},
            {'name': 'Volcano Engine (火山引擎)', 'models': ['doubao'], 'best_for': 'Speed in China'},
            {'name': 'SiliconFlow (硅基流动)', 'models': ['Qwen2.5-72B', 'DeepSeek-V3'], 'best_for': 'Flexibility'},
            {'name': 'Ollama (Local)', 'models': ['llama3', 'qwen2.5'], 'best_for': 'Data security'},
            {'name': 'OpenRouter', 'models': ['gemini-2.0-flash'], 'best_for': 'International free tier'},
        ],
        'tips': [
            'Chinese users: DeepSeek V3 via Volcano Engine API for best speed',
            'International: OpenRouter + Gemini Free for cost-effective option',
            'Always test API before generating final documents'
        ]
    }
    print(json.dumps(models, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Open Bid Kit Pro - CLI Agent')
    sp = p.add_subparsers(dest='cmd')
    
    e = sp.add_parser('extract', help='Extract document structure')
    e.add_argument('file', help='Markdown file path')
    
    v = sp.add_parser('preview', help='Generate HTML preview')
    v.add_argument('file', help='Markdown file path')
    
    o = sp.add_parser('outline', help='Generate outline from requirements')
    o.add_argument('file', help='Requirements markdown file')
    
    c = sp.add_parser('check', help='Run compliance checklist')
    c.add_argument('bid_file', help='Bid document file')
    c.add_argument('reqs_file', nargs='?', default='', help='Requirements file (optional)')
    
    sp.add_parser('models', help='List supported AI models')
    
    args = p.parse_args()
    
    if args.cmd == 'extract':
        cmd_extract(args.file)
    elif args.cmd == 'preview':
        cmd_preview(args.file)
    elif args.cmd == 'outline':
        cmd_outline(args.file)
    elif args.cmd == 'check':
        cmd_check(args.bid_file, args.reqs_file or args.bid_file)
    elif args.cmd == 'models':
        cmd_models()
    else:
        p.print_help()
