#!/usr/bin/env python3
"""Notion Knowledge Base Sync for Open Bid Kit Pro.

Sync bid templates and knowledge base with Notion databases.
Uses Notion REST API directly (no SDK required).

Setup:
  1. Go to https://www.notion.so/profile/integrations
  2. Create "New Integration" → copy "Internal Integration Secret"
  3. Set NOTION_API_KEY in .env
  4. Create a database in Notion, share with your integration
  5. Set NOTION_KNOWLEDGEBASE_DATABASE_ID in .env

Usage:
  python notion-sync.py info           Show integration status
  python notion-sync.py pull           Pull templates from Notion
  python notion-sync.py push           Push local KB to Notion
  python notion-sync.py search <q>     Search Notion KB
"""

import os, sys, json, argparse

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PLUGIN_ROOT, '.env')
KB_PATH = os.path.join(PLUGIN_ROOT, 'knowledge-base')
OUTPUT_DIR = os.path.join(PLUGIN_ROOT, 'output')
NOTION_API = 'https://api.notion.com/v1'
NOTION_VERSION = '2022-06-28'

def load_config():
    api_key = os.environ.get('NOTION_API_KEY', '')
    db_id = os.environ.get('NOTION_KNOWLEDGEBASE_DATABASE_ID', '')
    if not api_key and os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('NOTION_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip("'\"").strip()
                elif line.startswith('NOTION_KNOWLEDGEBASE_DATABASE_ID='):
                    db_id = line.split('=', 1)[1].strip().strip("'\"").strip()
    return api_key, db_id

def notion_headers(api_key):
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION
    }

def api_get(url, headers):
    import requests
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def api_post(url, headers, data):
    import requests
    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()
    return r.json()

def cmd_info():
    api_key, db_id = load_config()
    status = {
        'notion_api_key': f'***{api_key[-4:]}' if api_key else 'NOT SET',
        'database_id': db_id or 'NOT SET',
        'configured': bool(api_key and db_id),
        'kb_path': KB_PATH if os.path.exists(KB_PATH) else 'NOT CREATED',
        'output_path': OUTPUT_DIR
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    
    if not status['configured']:
        print()
        print('To set up Notion integration:')
        print('  1. Go to https://www.notion.so/profile/integrations')
        print('  2. Create a new integration, copy the Secret')
        print('  3. Add to .env: NOTION_API_KEY=secret_xxx')
        print('  4. Create a Notion database, share with integration')
        print('  5. Add to .env: NOTION_KNOWLEDGEBASE_DATABASE_ID=xxx')
        return
    
    # Test the connection
    try:
        import requests
        headers = notion_headers(api_key)
        me = api_get(f'{NOTION_API}/users/me', headers)
        print()
        print(f'Connected as: {me.get("name", "Notion User")}')
        print(f'Bot ID: {me.get("id", "N/A")}')
        
        # Try to query the database
        if db_id:
            result = api_post(f'{NOTION_API}/databases/{db_id}/query', headers, {})
            pages = result.get('results', [])
            print(f'Database pages: {len(pages)}')
            for p in pages[:5]:
                props = p.get('properties', {})
                title = 'N/A'
                for key, val in props.items():
                    if val.get('type') == 'title':
                        titles = val.get('title', [])
                        if titles:
                            title = titles[0].get('plain_text', 'N/A')
                print(f'  - {title}')
    except ImportError:
        print('Run: pip install requests')
    except Exception as e:
        print(f'Connection failed: {e}')

def cmd_pull():
    api_key, db_id = load_config()
    if not api_key or not db_id:
        print('Notion not configured. Run: python notion-sync.py info')
        return
    
    import requests
    os.makedirs(KB_PATH, exist_ok=True)
    
    headers = notion_headers(api_key)
    try:
        result = api_post(f'{NOTION_API}/databases/{db_id}/query', headers, {'page_size': 100})
        pages = result.get('results', [])
        print(f'Pulled {len(pages)} pages from Notion database')
        
        for page in pages:
            props = page.get('properties', {})
            
            # Extract title
            title = 'untitled'
            for key, val in props.items():
                if val.get('type') == 'title':
                    titles = val.get('title', [])
                    if titles:
                        title = titles[0].get('plain_text', 'untitled')
            
            # Extract content blocks
            blocks = api_get(f'{NOTION_API}/blocks/{page["id"]}/children', headers)
            content_parts = []
            for block in blocks.get('results', []):
                btype = block.get('type', '')
                rich_text = block.get(btype, {}).get('rich_text', [])
                for rt in rich_text:
                    content_parts.append(rt.get('plain_text', ''))
            
            content = '\n'.join(content_parts)
            
            # Save locally
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title)
            filepath = os.path.join(KB_PATH, f'{safe_name}.md')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f'# {title}\n\n{content}')
            print(f'  Saved: {safe_name}.md')
        
        print(f'\nAll pages saved to: {KB_PATH}')
    except Exception as e:
        print(f'Pull failed: {e}')
        print('Make sure the database is shared with your Notion integration.')

def cmd_push():
    api_key, db_id = load_config()
    if not api_key or not db_id:
        print('Notion not configured. Run: python notion-sync.py info')
        return
    
    if not os.path.exists(KB_PATH):
        print(f'No knowledge base found at {KB_PATH}')
        print('Create markdown files in that directory to push.')
        return
    
    import requests, re
    headers = notion_headers(api_key)
    
    files = [f for f in os.listdir(KB_PATH) if f.endswith('.md')]
    print(f'Pushing {len(files)} files to Notion...')
    
    for fname in files:
        filepath = os.path.join(KB_PATH, fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first # heading
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else fname.replace('.md', '')
        
        # Parse content into blocks
        lines = content.split('\n')
        children = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            
            # Heading detection
            if line.startswith('### '):
                children.append({'object': 'block', 'type': 'heading_3', 'heading_3': {'rich_text': [{'type': 'text', 'text': {'content': line[4:]}}]}})
            elif line.startswith('## '):
                children.append({'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': [{'type': 'text', 'text': {'content': line[3:]}}]}})
            elif line.startswith('# '):
                children.append({'object': 'block', 'type': 'heading_1', 'heading_1': {'rich_text': [{'type': 'text', 'text': {'content': line[2:]}}]}})
            elif line.startswith('- '):
                children.append({'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [{'type': 'text', 'text': {'content': line[2:]}}]}})
            elif line.strip():
                children.append({'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': line}}]}})
            i += 1
        
        # Create Notion page
        page_data = {
            'parent': {'database_id': db_id},
            'properties': {
                'title': {'title': [{'type': 'text', 'text': {'content': title}}]}
            },
            'children': children
        }
        
        try:
            result = api_post(f'{NOTION_API}/pages', headers, page_data)
            print(f'  Created: {title}')
        except Exception as e:
            print(f'  Failed {title}: {e}')
    
    print('Push complete.')

def cmd_search(query):
    api_key, db_id = load_config()
    if not api_key or not db_id:
        print('Notion not configured. Run: python notion-sync.py info')
        return
    
    import requests
    headers = notion_headers(api_key)
    
    data = {
        'filter': {
            'property': 'title',
            'rich_text': {'contains': query}
        }
    }
    
    try:
        result = api_post(f'{NOTION_API}/databases/{db_id}/query', headers, data)
        pages = result.get('results', [])
        print(f'Found {len(pages)} pages matching "{query}":')
        for p in pages:
            props = p.get('properties', {})
            for key, val in props.items():
                if val.get('type') == 'title':
                    titles = val.get('title', [])
                    if titles:
                        print(f'  - {titles[0].get("plain_text", "")}')
    except Exception as e:
        print(f'Search failed: {e}')

if __name__ == '__main__':
    import re  # for cmd_push and cmd_pull
    p = argparse.ArgumentParser(description='Notion KB Sync for Open Bid Kit Pro')
    sp = p.add_subparsers(dest='cmd')
    sp.add_parser('info', help='Show config and connection status')
    sp.add_parser('pull', help='Pull templates from Notion')
    sp.add_parser('push', help='Push local KB to Notion')
    s = sp.add_parser('search', help='Search Notion KB')
    s.add_argument('query')
    args = p.parse_args()
    
    if args.cmd == 'info': cmd_info()
    elif args.cmd == 'pull': cmd_pull()
    elif args.cmd == 'push': cmd_push()
    elif args.cmd == 'search': cmd_search(args.query)
    else: p.print_help()
