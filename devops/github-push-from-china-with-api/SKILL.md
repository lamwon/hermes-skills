---
name: github-push-from-china-with-api
description: Push files to GitHub from mainland China when `git push` fails due to network issues. Uses GitHub Contents API as a reliable fallback when the git protocol is blocked or timed out. Handles both new and existing repos.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github, china, network, api, devops, git]
---

# GitHub Push from China via API

When `git push` fails from China (common `Failed to connect to github.com port 443` errors), use the GitHub Contents API or Git Data API as a reliable fallback. The Contents API uses HTTPS and often succeeds when the git protocol is blocked.

## Problem

From mainland China, `git push` frequently fails with:
```
fatal: unable to access 'https://github.com/user/repo.git/':
  Failed to connect to github.com port 443 after 21150 ms: Could not connect to server
```

However, the GitHub REST API (`api.github.com`) often works because it uses a different network path.

## Architecture: Two Approaches

| Approach | When to Use | Pros | Cons |
|----------|-------------|------|------|
| **Contents API** | New or existing repos | Simple, works with `auto_init=True` repos | Each file uploaded individually, no atomic commits |
| **Git Data API** (blobs+tree+commit+ref) | When atomic commit needed | Single commit for all files | 409 Conflict on empty repos; needs existing ref |

## Approach 1: Contents API (Recommended)

### Create repo with auto_init

```python
import urllib.request, json, base64

TOKEN = "ghp_your_token_here"
REPO_NAME = "my-repo"
LOCAL_DIR = "/path/to/files"

# Create repo with auto_init so it has a base commit
data = json.dumps({
    "name": REPO_NAME,
    "description": "Description",
    "private": False,
    "auto_init": True  # CRITICAL: needed for Contents API to work
}).encode()

req = urllib.request.Request(
    "https://api.github.com/user/repos",
    data=data,
    headers={"Authorization": f"token {TOKEN}",
             "Content-Type": "application/json",
             "User-Agent": "my-app"},
    method="POST"
)
urllib.request.urlopen(req, timeout=15)
```

### Upload files

```python
import os, base64, json, urllib.request

FILES = ["README.md", "main.py", ".gitignore"]

for fname in FILES:
    path = os.path.join(LOCAL_DIR, fname)
    if not os.path.exists(path):
        continue
    
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    data = json.dumps({
        "message": f"Add {fname}",
        "content": b64,
        "branch": "main"
    }).encode()
    
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{REPO_NAME}/contents/{fname}",
        data=data,
        headers={"Authorization": f"token {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "my-app"},
        method="PUT"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        print(f"OK: {fname}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"FAIL: {fname} - {e.code} - {body}")
```

### Updating existing files (need SHA)

When a repo already has a file (e.g., auto_generated README.md), you need its SHA to update:

```python
# Get SHA first
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{REPO_NAME}/contents/README.md",
    headers={"Authorization": f"token {TOKEN}", "User-Agent": "my-app"}
)
resp = urllib.request.urlopen(req, timeout=10)
sha = json.loads(resp.read().decode())["sha"]

# Update with SHA
data = json.dumps({
    "message": "Update README",
    "content": b64_content,
    "sha": sha,  # Required for existing files
    "branch": "main"
}).encode()
```

## Approach 2: Git Data API (Atomic Commit)

Use when you need all files in a single commit:

```python
# Step 1: Create blobs for each file
tree_entries = []
for fname, local_path in files:
    with open(local_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    blob_data = json.dumps({"content": b64, "encoding": "base64"}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/git/blobs",
        data=blob_data,
        headers={"Authorization": f"token {TOKEN}", "Content-Type": "application/json", "User-Agent": "my-app"},
        method="POST"
    )
    blob_sha = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["sha"]
    tree_entries.append({"path": fname, "mode": "100644", "type": "blob", "sha": blob_sha})

# Step 2: Create tree
tree_data = json.dumps({"tree": tree_entries}).encode()
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/git/trees", ...
)
tree_sha = json.loads(urllib.request.urlopen(req).read().decode())["sha"]

# Step 3: Create commit (no parents for root commit)
commit_data = json.dumps({
    "message": "Initial commit",
    "tree": tree_sha,
    "parents": []  # Empty for root commit
}).encode()

# Step 4: Create or update branch reference
if is_first_commit:
    ref_data = json.dumps({"ref": "refs/heads/main", "sha": commit_sha}).encode()
    method = "POST"
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
else:
    ref_data = json.dumps({"sha": commit_sha, "force": True}).encode()
    method = "PATCH"
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/main"
```

## Setting Topics

```python
topics = ["tag1", "tag2", "tag3"]
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/topics",
    data=json.dumps({"names": topics}).encode(),
    headers={"Authorization": f"token {TOKEN}",
             "Accept": "application/vnd.github.mercy-preview+json",
             "Content-Type": "application/json",
             "User-Agent": "my-app"},
    method="PUT"
)
urllib.request.urlopen(req, timeout=10)
```

## Pitfalls

1. **Empty repos need auto_init=True** — The Contents API requires at least one commit to exist. Without `auto_init`, you get 409 Conflict on blobs and 404 on contents.
2. **Large files (>1MB)** — The Contents API has a 1MB file limit. For larger files, use the Git Data API with blob creation.
3. **Rate limits** — Unauthenticated: 60 req/hr. Authenticated: 5000 req/hr. Use the token.
4. **Token scope** — Token needs `repo` scope for private repos and `delete_repo` for deletions.
5. **File encoding** — Contents must be base64-encoded. Binary files (images) work fine.
6. **No force push** — The Contents API doesn't support force push semantics. If you get conflicts, you need to get the current SHA first.
7. **GBK encoding on Windows** — When writing Python scripts with Chinese chars on Windows, use `# -*- coding: utf-8 -*-` at the top.

## Extracting Token from Git Remote URL

When the token is embedded in a git remote URL (e.g., `https://user:ghp_token@github.com/...`):

```python
import subprocess
result = subprocess.run(
    ["git", "remote", "get-url", "origin"],
    capture_output=True, text=True, cwd="/path/to/repo"
)
url = result.stdout.strip()
token = url.split(":")[-1].split("@")[0]  # Extract token between ':' and '@'
```
