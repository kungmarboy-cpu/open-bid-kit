import sys, os, json, re

def extract_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return {
        'file': os.path.basename(filepath),
        'chars': len(content),
        'sections': re.findall(r'^# (.+)$', content, re.MULTILINE)
    }

def make_preview(filepath, html_path=None):
    import markdown
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    body = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    html = '<html><head><meta charset="UTF-8"><title>Bid Preview</title>'
    html += '<style>body{font-family:Microsoft YaHei,sans-serif;background:#f0f2f5;margin:0}'
    html += '.toolbar{background:#1a1a2e;color:#fff;padding:12px 24px;position:sticky;top:0}'
    html += '.container{max-width:900px;margin:0 auto;padding:40px 24px}'
    html += '.doc-card{background:#fff;padding:60px 80px;box-shadow:0 2px 12px rgba(0,0,0,0.08);line-height:1.8;min-height:800px}'
    html += '.doc-card h2{font-size:18px;margin:24px 0 12px;color:#1a1a2e;border-left:4px solid #e94560;padding-left:12px}'
    html += '.doc-card h3{font-size:16px;margin:16px 0 8px;color:#444}'
    html += '.doc-card p{margin:8px 0;text-indent:2em}'
    html += '.doc-card table{width:100%;border-collapse:collapse;margin:16px 0}'
    html += '.doc-card th,.doc-card td{border:1px solid #ddd;padding:8px 12px}'
    html += '.doc-card th{background:#f8f9fa;font-weight:600}'
    html += '.doc-card pre{background:#f5f5f5;padding:16px;border-radius:4px;overflow-x:auto}'
    html += '</style></head><body>'
    html += '<div class="toolbar"><h1>Open Bid Kit Pro - Bid Preview</h1></div>'
    html += '<div class="container"><div class="doc-card">' + body + '</div></div></body></html>'
    if not html_path:
        html_path = filepath.replace('.md', '_preview.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return os.path.abspath(html_path).replace(os.sep, '/')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd')
    e = sp.add_parser('extract')
    e.add_argument('file')
    v = sp.add_parser('preview')
    v.add_argument('file')
    args = p.parse_args()
    if args.cmd == 'extract':
        print(json.dumps(extract_content(args.file), ensure_ascii=False, indent=2))
    elif args.cmd == 'preview':
        print('Preview: file:///' + make_preview(args.file))
