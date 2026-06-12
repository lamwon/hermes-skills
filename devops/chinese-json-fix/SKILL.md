---
name: chinese-json-fix
description: Fix JSON files containing Chinese text with unescaped ASCII double quotes that break json.loads(). Uses regex with CJK Unicode ranges to replace inner quotes with Chinese corner brackets.
---

# Fix Chinese JSON with ASCII Double Quotes

## Problem

LLMs generate JSON where Chinese text contains ASCII double quotes:
```
"summary": "提出"水是万物的本原"，认为一切事物皆源于水"
```

The inner `"` around `水是万物的本原` breaks JSON parsing.

## Fix Script

```python
import re, json

with open("file.json", "r", encoding="utf-8") as f:
    content = f.read()

LQ, RQ = "\u300c", "\u300d"
cjk = "[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]"

while True:
    prev = content
    content = re.sub(
        '(' + cjk + ')"([^"]{1,60})"(' + cjk + ')',
        lambda m: m.group(1) + LQ + m.group(2) + RQ + m.group(3),
        content
    )
    if content == prev:
        break

data = json.loads(content)
with open("file.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## Key Points
- CJK ranges cover: Unicode blocks U+4E00-U+9FFF, U+3400-U+4DBF, U+F900-U+FAFF, plus CJK punct U+3000-U+303F and Fullwidth U+FF00-U+FFEF
- Fullwidth comma U+FF0C（，）is critical — often appears after CJK text with quotes
- Run with Hermes embedded Python on Windows: `/d/Hermes/portable-hermes-agent/python_embedded/python.exe`
- System python3 (Microsoft Store) returns exit code 49 silently — NEVER use it for Chinese text processing
- Loop replaces repeatedly until no more matches (handles cascading patterns)
- Write the fix script with `write_file` tool (not execute_code, which has encoding issues with CJK chars on system python3)
- Save fix scripts to `C:\Users\Windows\AppData\Local\Temp\` for reliability
