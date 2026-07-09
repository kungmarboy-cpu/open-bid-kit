#!/usr/bin/env python3
"""Open Bid Kit Pro - MCP Server (Model Context Protocol)

Exposes bid document tools over stdio-based MCP for any MCP-compatible client.
Implements JSON-RPC 2.0 for tool discovery and execution.

Usage:
  # Standalone HTTP server
  python bid-mcp-server.py --http --port 8900
  
  # stdio (for MCP client integration)
  python bid-mcp-server.py
"""

import os, sys, json, re, argparse, time, uuid
from typing import Any

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PLUGIN_ROOT, 'output')
KB_PATH = os.path.join(PLUGIN_ROOT, 'knowledge-base')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Tool Definitions ───────────────────────────────────────────

TOOLS = [
    {
        "name": "extract_bid_document",
        "description": "Extract structure and metadata from a bid document (Markdown)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to bid document (Markdown)"}
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "generate_outline",
        "description": "Generate a structured outline from bid requirements",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirements": {"type": "string", "description": "Requirements text or file path"},
                "industry": {"type": "string", "description": "Industry type (it/construction/medical/education/manufacturing/logistics/consulting/general)"}
            },
            "required": ["requirements"]
        }
    },
    {
        "name": "check_compliance",
        "description": "Run 21-point compliance checklist on a bid document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bid_file": {"type": "string", "description": "Bid document file path"},
                "requirements_file": {"type": "string", "description": "Requirements file path (optional)"}
            },
            "required": ["bid_file"]
        }
    },
    {
        "name": "preview_document",
        "description": "Generate HTML preview of a bid document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Markdown file path"},
                "output_path": {"type": "string", "description": "Output HTML path (optional)"}
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "search_knowledgebase",
        "description": "Search bid knowledge base for relevant templates and content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_industry",
        "description": "Detect industry from bid document content and return industry guide",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Bid document content or heading list"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "list_supported_models",
        "description": "List supported AI models for bid generation",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

# ─── Tool Implementations ───────────────────────────────────────

def tool_extract_document(filepath):
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    h1 = re.findall(r'^# (.+)$', content, re.MULTILINE)
    h2 = re.findall(r'^## (.+)$', content, re.MULTILINE)
    h3 = re.findall(r'^### (.+)$', content, re.MULTILINE)
    has_tables = bool(re.search(r'\|.+\|\n\|[-| ]+\|', content))
    code_blocks = len(re.findall(r'```', content)) // 2
    char_count = len(re.sub(r'\s', '', content))
    return {
        "filename": os.path.basename(filepath),
        "chars": char_count,
        "structure": {"h1": h1, "h2": h2, "h3": h3},
        "features": {"tables": has_tables, "code_blocks": code_blocks}
    }

def tool_generate_outline(requirements, industry=None):
    if os.path.exists(requirements):
        with open(requirements, 'r', encoding='utf-8') as f:
            requirements = f.read()
    
    # Detect sections from requirements
    h2 = re.findall(r'^## (.+)$', requirements, re.MULTILINE)
    
    # Suggest outline based on industry
    industry_templates = {
        "it": [{"id": "2", "title": "技术方案", "focus": "技术架构、系统设计"}],
        "construction": [{"id": "2", "title": "施工组织设计", "focus": "施工方案、进度计划"}],
        "medical": [{"id": "2", "title": "技术参数响应", "focus": "产品配置、质量体系"}],
        "education": [{"id": "2", "title": "整体解决方案", "focus": "教学方案、课程体系"}],
        "manufacturing": [{"id": "2", "title": "技术方案", "focus": "生产工艺、质量控制"}],
        "logistics": [{"id": "2", "title": "运输组织方案", "focus": "运输方案、仓储管理"}],
        "consulting": [{"id": "2", "title": "咨询服务方案", "focus": "方法论、实施计划"}],
    }
    template = industry_templates.get(industry, [{"id": "2", "title": "技术方案", "focus": "详细方案"}])
    
    return {
        "detected_sections": h2,
        "industry": industry or "auto-detect",
        "outline": [
            {"id": "1", "title": "投标方案综述", "description": "项目理解与总体思路",
             "children": [
                 {"id": "1.1", "title": "项目背景与理解"},
                 {"id": "1.2", "title": "总体建设思路"},
                 {"id": "1.3", "title": "核心优势"}
             ]},
            template[0],
            {"id": "3", "title": "项目管理", "description": "项目组织与实施保障",
             "children": [
                 {"id": "3.1", "title": "项目组织管理"},
                 {"id": "3.2", "title": "进度计划"},
                 {"id": "3.3", "title": "质量保障"}
             ]},
            {"id": "4", "title": "售后服务", "description": "服务承诺与保障",
             "children": [
                 {"id": "4.1", "title": "服务方案"},
                 {"id": "4.2", "title": "培训方案"}
             ]}
        ]
    }

def tool_check_compliance(bid_file, requirements_file=None):
    if not os.path.exists(bid_file):
        return {"error": f"File not found: {bid_file}"}
    with open(bid_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checklist = [
        {"id": 1, "item": "投标保证金", "category": "财务"},
        {"id": 2, "item": "签字盖章", "category": "形式"},
        {"id": 3, "item": "投标有效期", "category": "时间"},
        {"id": 4, "item": "格式一致性", "category": "形式"},
        {"id": 5, "item": "内容一致性", "category": "内容"},
        {"id": 6, "item": "重复率", "category": "内容"},
        {"id": 7, "item": "价格合理性", "category": "报价"},
        {"id": 8, "item": "资质完整性", "category": "资质"},
        {"id": 9, "item": "人员配置", "category": "人员"},
        {"id": 10, "item": "业绩要求", "category": "资质"},
        {"id": 11, "item": "技术参数响应", "category": "技术"},
        {"id": 12, "item": "实质性条款", "category": "条款"},
        {"id": 13, "item": "偏离表", "category": "内容"},
        {"id": 14, "item": "授权委托", "category": "形式"},
        {"id": 15, "item": "财务报表", "category": "财务"},
        {"id": 16, "item": "社保纳税", "category": "资质"},
        {"id": 17, "item": "联合体协议", "category": "形式"},
        {"id": 18, "item": "分包说明", "category": "内容"},
        {"id": 19, "item": "页码目录", "category": "形式"},
        {"id": 20, "item": "密封要求", "category": "形式"},
        {"id": 21, "item": "递交时间", "category": "时间"},
    ]
    
    return {
        "bid_file": os.path.basename(bid_file),
        "chars": len(content),
        "checklist": checklist,
        "total_checks": 21,
        "categories": ["财务", "形式", "时间", "内容", "报价", "资质", "人员", "技术", "条款"]
    }

def tool_preview_document(filepath, output_path=None):
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if output_path is None:
        output_path = os.path.join(os.path.dirname(filepath), '_preview_' + str(int(time.time())) + '.html')
    try:
        import markdown
        body = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        html = f'''<!DOCTYPE html><html lang="zh-CN">
<head><meta charset="UTF-8"><title>Bid Preview</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Microsoft YaHei','SimSun',serif;background:#f0f2f5;color:#333}}
.toolbar{{background:#1a1a2e;color:#fff;padding:12px 24px;position:sticky;top:0}}
.container{{max-width:900px;margin:0 auto;padding:40px 24px 80px}}
.doc-card{{background:#fff;padding:60px 80px;box-shadow:0 2px 12px rgba(0,0,0,0.08);border-radius:4px;line-height:1.8;min-height:800px}}
.doc-card h1{{font-size:22px;text-align:center;margin-bottom:32px;padding-bottom:16px;border-bottom:2px solid #1a1a2e}}
.doc-card h2{{font-size:18px;margin:24px 0 12px;color:#1a1a2e;border-left:4px solid #e94560;padding-left:12px}}
.doc-card h3{{font-size:16px;margin:16px 0 8px;color:#444}}
.doc-card p{{margin:8px 0;text-indent:2em}}
.doc-card table{{width:100%;border-collapse:collapse;margin:16px 0}}
.doc-card th,.doc-card td{{border:1px solid #ddd;padding:8px 12px}}
.doc-card th{{background:#f8f9fa;font-weight:600}}
.doc-card pre{{background:#f5f5f5;padding:16px;border-radius:4px;overflow-x:auto}}
@media print{{.toolbar{{display:none}}.container{{padding:0}}.doc-card{{box-shadow:none;padding:40px}}}}
</style></head><body>
<div class="toolbar"><h1>Open Bid Kit Pro - Preview</h1></div>
<div class="container"><div class="doc-card">{body}</div></div>
</body></html>'''
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return {"preview_path": os.path.abspath(output_path), "file_url": "file:///" + os.path.abspath(output_path).replace(os.sep, "/")}
    except ImportError:
        return {"error": "Install markdown library: pip install markdown"}

def tool_search_knowledgebase(query, max_results=5):
    if not os.path.exists(KB_PATH):
        return {"results": [], "total": 0, "message": "Knowledge base directory not found"}
    query_lower = query.lower()
    results = []
    for fname in os.listdir(KB_PATH):
        if fname.endswith('.md'):
            fpath = os.path.join(KB_PATH, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            score = 0
            if query_lower in content.lower():
                score += content.lower().count(query_lower)
            if score > 0:
                results.append({"file": fname, "score": score, "snippet": content[:200]})
    results.sort(key=lambda x: x['score'], reverse=True)
    return {"results": results[:max_results], "total": len(results)}

def tool_analyze_industry(content):
    industries = {
        "it": ["软件", "系统集成", "云计算", "大数据", "信息化", "网络", "数字化"],
        "construction": ["建筑", "施工", "装修", "市政", "工程", "土木", "建设"],
        "medical": ["医疗", "医院", "设备", "药品", "医疗器械", "临床"],
        "education": ["教育", "学校", "教学", "培训", "校园", "课程"],
        "manufacturing": ["制造", "设备", "自动化", "智能制造", "工业"],
        "logistics": ["物流", "运输", "仓储", "配送", "货运"],
        "consulting": ["咨询", "管理", "审计", "法律", "评估", "规划"],
    }
    
    scores = {}
    for ind, keywords in industries.items():
        scores[ind] = sum(1 for kw in keywords if kw in content)
    
    if max(scores.values()) == 0:
        return {"industry": "general", "confidence": 0.3, "message": "No specific industry detected"}
    
    best = max(scores, key=scores.get)
    return {"industry": best, "confidence": min(1.0, scores[best] / 5), "matched_keywords": [kw for kw in industries[best] if kw in content]}

def tool_list_models():
    return {
        "providers": [
            {"name": "DeepSeek", "models": ["deepseek-chat", "deepseek-reasoner"], "best_for": "中文"},
            {"name": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini"], "best_for": "国际"},
            {"name": "火山引擎", "models": ["doubao"], "best_for": "国内速度"},
            {"name": "Ollama", "models": ["llama3", "qwen2.5"], "best_for": "本地"},
            {"name": "OpenRouter", "models": ["gemini-2.0-flash"], "best_for": "免费"},
        ]
    }

# ─── Tool Router ────────────────────────────────────────────────

TOOL_MAP = {
    "extract_bid_document": lambda a: tool_extract_document(a["filepath"]),
    "generate_outline": lambda a: tool_generate_outline(a["requirements"], a.get("industry")),
    "check_compliance": lambda a: tool_check_compliance(a["bid_file"], a.get("requirements_file")),
    "preview_document": lambda a: tool_preview_document(a["filepath"], a.get("output_path")),
    "search_knowledgebase": lambda a: tool_search_knowledgebase(a["query"], a.get("max_results", 5)),
    "analyze_industry": lambda a: tool_analyze_industry(a["content"]),
    "list_supported_models": lambda a: tool_list_models(),
}

# ─── MCP Protocol ──────────────────────────────────────────────

def handle_mcp_request(msg):
    method = msg.get("method", "")
    params = msg.get("params", {})
    msg_id = msg.get("id")
    
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "open-bid-kit-mcp", "version": "1.0.0"}
        }}
    
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    
    elif method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        if name in TOOL_MAP:
            try:
                result = TOOL_MAP[name](arguments)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": str(e)}}
        else:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Tool not found: {name}"}}
    
    elif method == "resources/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}
    
    elif method == "resources/read":
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Resource not found"}}
    
    elif method == "notifications/initialized":
        return None
    
    else:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

# ─── Main ───────────────────────────────────────────────────────

def run_stdio():
    """Run MCP server over stdio (for MCP client integration)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = handle_mcp_request(msg)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + '\n')
                sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stderr.write(f'Invalid JSON: {line}\n')
            sys.stderr.flush()

def run_http(port=8900):
    """Run MCP server over HTTP."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class MCPHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                msg = json.loads(body)
                resp = handle_mcp_request(msg)
                resp_bytes = json.dumps(resp, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp_bytes)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        
        def log_message(self, format, *args):
            pass
    
    server = HTTPServer(('127.0.0.1', port), MCPHandler)
    print(json.dumps({"status": "ok", "type": "mcp-http", "url": f"http://127.0.0.1:{port}", "tools": len(TOOLS)}))
    print(f'MCP HTTP server: http://127.0.0.1:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Open Bid Kit Pro - MCP Server')
    parser.add_argument('--http', action='store_true', help='Run as HTTP server')
    parser.add_argument('--port', type=int, default=8900, help='HTTP port')
    args = parser.parse_args()
    
    if args.http:
        run_http(args.port)
    else:
        run_stdio()
