#!/usr/bin/env python3
"""GitHub setup script for Open Bid Kit Pro.

Run this script to push the plugin to GitHub:
  python setup-github.py

Or follow the manual steps below.
"""

import os, sys, subprocess

PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, cwd=PLUGIN_ROOT):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def main():
    print('=== Open Bid Kit Pro - GitHub Setup ===')
    print()
    print(f'Plugin directory: {PLUGIN_ROOT}')
    print()
    
    # Check git status
    rc, out, err = run('git rev-parse --git-dir')
    if rc != 0 or '.git' not in out:
        print('ERROR: Git repo not found. Run: git init')
        sys.exit(1)
    
    print('Git repository: OK')
    
    # Check remote
    rc, out, err = run('git remote -v')
    if out:
        print(f'Remote configured: {out}')
        push_now = input('Push to existing remote? (y/n): ').lower() == 'y'
        if push_now:
            rc, out, err = run('git push -u origin master')
            if rc == 0:
                print(f'Push successful!')
            else:
                print(f'Push failed: {err}')
        return
    
    # No remote - guide setup
    print()
    print('No GitHub remote configured.')
    print()
    print('Option 1: Automatic setup (requires GitHub CLI)')
    print('  gh auth login')
    print('  gh repo create open-bid-kit --source=. --public --push')
    print()
    print('Option 2: Manual setup')
    username = input('GitHub username: ').strip()
    if not username:
        username = 'YOUR_USERNAME'
    print()
    print('Run these commands:')
    print(f'  cd "{PLUGIN_ROOT}"')
    print(f'  gh repo create open-bid-kit --source=. --public --push')
    print()
    print('Or manually:')
    print(f'  cd "{PLUGIN_ROOT}"')
    print(f'  git remote add origin https://github.com/{username}/open-bid-kit.git')
    print(f'  git push -u origin master')
    print()
    print(f'Repo URL: https://github.com/{username}/open-bid-kit')
    print()
    
    print('=== GitHub setup complete ===')

if __name__ == '__main__':
    main()
