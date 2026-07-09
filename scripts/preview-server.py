# Preview Server - serves bid document previews via HTTP for Codex in-app browser
# Usage: python preview-server.py [--port 8899]

import os, sys, json, http.server, socketserver, threading, webbrowser, argparse
from urllib.parse import urlparse, unquote

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PLUGIN_ROOT, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_mime(path):
    if path.endswith('.html'): return 'text/html; charset=utf-8'
    if path.endswith('.css'):  return 'text/css; charset=utf-8'
    if path.endswith('.js'):   return 'application/javascript'
    if path.endswith('.json'): return 'application/json'
    if path.endswith('.png'):  return 'image/png'
    if path.endswith('.svg'):  return 'image/svg+xml'
    return 'text/plain; charset=utf-8'

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=PLUGIN_ROOT, **kw)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self._index_page().encode('utf-8'))
        elif path == '/api/status':
            self.send_json({'status': 'ok', 'plugin': 'open-bid-kit', 'outputs': os.listdir(OUTPUT_DIR) if os.path.exists(OUTPUT_DIR) else []})
        elif path.startswith('/preview/'):
            fname = path[9:]
            fpath = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                from markdown import markdown as md
                body = md(content, extensions=['tables', 'fenced_code'])
                html = self._doc_template(os.path.basename(fpath), body)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_error(404, 'File not found')
        else:
            super().do_GET()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _index_page(self):
        files = []
        if os.path.exists(OUTPUT_DIR):
            for f in sorted(os.listdir(OUTPUT_DIR)):
                if f.endswith('.md') and not f.startswith('_'):
                    fsize = os.path.getsize(os.path.join(OUTPUT_DIR, f))
                    files.append((f, fsize))
        rows = ''.join(f'<tr><td><a href="/preview/{f}">{f}</a></td><td>{s} bytes</td></tr>' for f, s in files)
        return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>Open Bid Kit - Preview Server</title>
<style>
  body {{ font-family: 'Microsoft YaHei', sans-serif; background: #f0f2f5; margin: 0; padding: 40px; }}
  .card {{ background: #fff; max-width: 800px; margin: 0 auto; padding: 32px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
  h1 {{ font-size: 20px; color: #1a1a2e; margin: 0 0 8px; }}
  p {{ color: #666; margin: 0 0 24px; font-size: 14px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; padding: 8px 12px; background: #f8f9fa; border-bottom: 2px solid #eee; font-size: 13px; color: #666; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
  td a {{ color: #1a73e8; text-decoration: none; }}
  td a:hover {{ text-decoration: underline; }}
  .empty {{ text-align: center; color: #999; padding: 40px; }}
  .badge {{ display: inline-block; background: #1a1a2e; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
</style></head><body>
<div class="card">
  <h1>Open Bid Kit Pro - Preview Server</h1>
  <p>Generated bid document previews <span class="badge">{len(files)} documents</span></p>
  <table><tr><th>Document</th><th>Size</th></tr>
  {rows or '<tr><td colspan="2" class="empty">No documents yet. Generate some bid documents first.</td></tr>'}
  </table>
</div></body></html>'''
    
    def _doc_template(self, title, body):
        return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>{title} - Open Bid Kit</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Microsoft YaHei', 'SimSun', serif; background: #f0f2f5; color: #333; }}
  .toolbar {{ background: #1a1a2e; color: #fff; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; }}
  .toolbar h1 {{ font-size: 16px; font-weight: 500; }}
  .toolbar .back {{ color: rgba(255,255,255,0.7); text-decoration: none; font-size: 14px; }}
  .toolbar .back:hover {{ color: #fff; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 40px 24px; }}
  .doc-card {{ background: #fff; padding: 60px 80px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-radius: 4px; min-height: 800px; line-height: 1.8; }}
  .doc-card h2 {{ font-size: 18px; margin: 24px 0 12px; color: #1a1a2e; border-left: 4px solid #e94560; padding-left: 12px; }}
  .doc-card h3 {{ font-size: 16px; margin: 16px 0 8px; color: #444; }}
  .doc-card p {{ margin: 8px 0; text-indent: 2em; }}
  .doc-card table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  .doc-card th, .doc-card td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  .doc-card th {{ background: #f8f9fa; font-weight: 600; }}
  .doc-card pre {{ background: #f5f5f5; padding: 16px; border-radius: 4px; overflow-x: auto; font-size: 14px; }}
  .doc-card code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 14px; }}
  .info {{ background: #fff; padding: 16px 24px; margin: 0 0 16px; border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); display: flex; gap: 24px; font-size: 13px; color: #666; }}
</style></head><body>
<div class="toolbar">
  <a href="/" class="back">&larr; Back</a>
  <h1>Open Bid Kit Pro</h1>
</div>
<div class="container">
  <div class="info"><span>{title}</span></div>
  <div class="doc-card">{body}</div>
</div></body></html>'''

def main():
    p = argparse.ArgumentParser(description='Bid document preview server')
    p.add_argument('--port', type=int, default=8899, help='Server port')
    p.add_argument('--open', action='store_true', help='Open browser')
    args = p.parse_args()
    
    server = http.server.HTTPServer(('127.0.0.1', args.port), PreviewHandler)
    print(f'Preview server: http://127.0.0.1:{args.port}')
    print(f'Open in Codex browser to preview bid documents.')
    print('Press Ctrl+C to stop.')
    
    if args.open:
        webbrowser.open(f'http://127.0.0.1:{args.port}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        server.server_close()

if __name__ == '__main__':
    main()
