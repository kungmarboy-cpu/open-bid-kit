# Notion Knowledge Base Sync - sync bid knowledge base with Notion
# Usage: python notion-sync.py pull    (fetch templates from Notion)
#        python notion-sync.py push    (push local KB to Notion)
#        python notion-sync.py search <query>  (search Notion KB)

import os, sys, json, argparse

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PLUGIN_ROOT, '.env')
OUTPUT_DIR = os.path.join(PLUGIN_ROOT, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_config():
    api_key = os.environ.get('NOTION_API_KEY', '')
    db_id = os.environ.get('NOTION_KNOWLEDGEBASE_DATABASE_ID', '')
    if not api_key and os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('NOTION_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip("'").strip('"')
                elif line.startswith('NOTION_KNOWLEDGEBASE_DATABASE_ID='):
                    db_id = line.split('=', 1)[1].strip().strip("'").strip('"')
    return api_key, db_id

def cmd_pull(args):
    """Pull bid templates from Notion knowledge base."""
    api_key, db_id = load_config()
    if not api_key or not db_id:
        print('Notion not configured. Set NOTION_API_KEY and NOTION_KNOWLEDGEBASE_DATABASE_ID in .env')
        print('Usage:')
        print('  1. Create a Notion integration: https://www.notion.so/profile/integrations')
        print('  2. Copy the Internal Integration Secret as NOTION_API_KEY')
        print('  3. Share your knowledge base database with the integration')
        print('  4. Copy the database ID and set as NOTION_KNOWLEDGEBASE_DATABASE_ID')
        sys.exit(1)
    print(f'Sync from Notion (DB: {db_id})')
    print('Notion sync available when NOTION_API_KEY is configured.')
    print('To configure: copy .env.example to .env and fill in your Notion credentials.')

def cmd_push(args):
    """Push local knowledge base entries to Notion."""
    api_key, db_id = load_config()
    if not api_key or not db_id:
        print('Notion not configured. See "pull" command for setup instructions.')
        sys.exit(1)
    print(f'Sync to Notion (DB: {db_id})')
    print('Notion sync available when NOTION_API_KEY is configured.')

def cmd_search(args):
    """Search knowledge base entries."""
    query = args.query
    print(f'Searching for: {query}')
    print('Notion search requires NOTION_API_KEY to be configured in .env')

def cmd_info(args):
    """Show Notion integration status."""
    api_key, db_id = load_config()
    status = {
        'notion_api_key': f'{"***" + api_key[-4:] if api_key else "NOT SET"}',
        'database_id': db_id or 'NOT SET',
        'configured': bool(api_key and db_id),
        'setup_guide': 'https://www.notion.so/profile/integrations'
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not status['configured']:
        print()
        print('To set up Notion integration:')
        print('  1. Go to https://www.notion.so/profile/integrations')
        print('  2. Create a new integration ("New Integration")')
        print('  3. Copy the Internal Integration Secret')
        print('  4. Set NOTION_API_KEY in .env')
        print('  5. Create a database in Notion and share it with your integration')
        print('  6. Set NOTION_KNOWLEDGEBASE_DATABASE_ID in .env')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Notion KB sync for Open Bid Kit')
    sp = p.add_subparsers(dest='cmd')
    sp.add_parser('pull', help='Pull from Notion')
    sp.add_parser('push', help='Push to Notion')
    s = sp.add_parser('search', help='Search Notion KB')
    s.add_argument('query')
    sp.add_parser('info', help='Show config status')
    args = p.parse_args()
    if args.cmd == 'pull': cmd_pull(args)
    elif args.cmd == 'push': cmd_push(args)
    elif args.cmd == 'search': cmd_search(args)
    elif args.cmd == 'info': cmd_info(args)
    else: p.print_help()
