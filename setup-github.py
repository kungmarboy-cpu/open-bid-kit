#!/usr/bin/env python3
"""GitHub setup script for Open Bid Kit Pro.

Run:  python setup-github.py
Repo: https://github.com/kungmarboy-cpu/open-bid-kit
"""

import os, sys, subprocess

PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_URL = "https://github.com/kungmarboy-cpu/open-bid-kit"

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def main():
    print("=== Open Bid Kit Pro - GitHub Setup ===")
    print(f"Plugin: {PLUGIN_ROOT}")
    print(f"Repo:   {REPO_URL}")
    print()
    
    # Check remote
    rc, out, _ = run("git remote -v")
    if "origin" in out:
        print("Remote 'origin' already configured:")
        print(out)
        rc2, out2, _ = run("git push origin master")
        if rc2 == 0:
            print("Push successful!")
        else:
            print("Push failed. This is likely a PAT scope issue.")
            print("See: https://github.com/settings/tokens")
            print("Ensure PAT has 'repo' and 'workflow' scopes.")
        return
    
    # No remote
    print("No remote configured. Run:")
    print(f"  git remote add origin {REPO_URL}")
    print("  git push -u origin master")
    print()
    
    print("To push workflow file:")
    print("  1. Create PAT at https://github.com/settings/tokens")
    print("     Scopes needed: 'repo' + 'workflow'")
    print("  2. git push origin master")

if __name__ == "__main__":
    main()
