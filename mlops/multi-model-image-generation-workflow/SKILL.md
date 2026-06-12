---
name: multi-model-image-generation-workflow
description: Multi-model orchestration workflow for AI image generation using DeepSeek (creative prompt engineering), Qwen (prompt refinement + VL analysis + OCR), and SiliconFlow Flux (free image generation). Designed for China-based users with Alibaba Cloud BaiLian workspace APIs.
tags: [image-generation, deepseek, qwen, flux, siliconflow, multi-model, workflow, china, dashscope, baiLian]
---

# Multi-Model AI Image Generation Workflow

Orchestrate DeepSeek + Qwen + Flux for a complete image generation pipeline.

## Architecture

```
[用户需求] --> DeepSeek V4 Flash (创意策划) --> Qwen 3.7 Max (润色优化) --> [Fine-tuned Prompt]
                                                                                |
                                                                     SiliconFlow Flux (出图)
                                                                                |
                                                                           [PNG图片]
```

## When to Use

- User wants to generate images with better prompts than a single model can produce
- User has multiple API providers (DeepSeek + Alibaba Cloud BaiLian) and wants to combine them
- User needs image analysis (VL) + OCR + text-to-image in one workflow
- User is in China and needs China-accessible services

## Key Findings from API Testing

### Alibaba Cloud BaiLian (百炼) Workspace API Patterns

**Models that work via OpenAI-compatible `chat/completions`:**
- Text models: `qwen3.7-max`, `qwen-plus`, `qwen-turbo`, `qwen3.6-flash` (plain string content)
- VL models: `qwen-vl-plus`, `qwen-vl-max`, `qwen2.5-vl-32b-instruct` (works with base64 images)
- OCR: `qwen-vl-ocr` (works with base64 images)
- Omni models: `qwen3.5-omni-plus`, `qwen-omni-turbo` (text+audio only, NO image output)

**Models that exist but DON'T output images in this workspace:**
- `wan2.7-image-pro`: Returns chat completion with empty content (workspace not configured with callback URL / image hosting)
- `qwen-image-2.0-pro`, `qwen-image-max`, `qwen-image-plus`, `z-image-turbo`: Same issue - no image output

**Why image models fail:** Alibaba Cloud DashScope image generation requires async callback URL configuration (the "url error"). The workspace API doesn't provide this, so it returns empty content.

### Content Format Requirements

- **Text models** accept plain string: `"content": "你好"`
- **Image/VL models** require list format: `"content": [{"type": "text", "text": "描述..."}]`
- For VL with images, append: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,${b64}"}}`
- External image URLs may time out from China (API server can't reach foreign hosts)
- Base64 is the reliable approach for VL models

### SiliconFlow (硅基流动) Free Flux

- API base: `https://api.siliconflow.cn/v1`
- Free model: `black-forest-labs/FLUX.1-schnell`
- OpenAI-compatible `/v1/images/generations` endpoint
- Works with standard format: `{"model": "...", "prompt": "...", "n": 1, "size": "1024x1024"}`
- Response: `data[0].url` or `data[0].b64_json`
- Sign up at https://siliconflow.cn for free API key (free tier has monthly quota)

## Complete Workflow Script

Save to a Python file (e.g., `ds-qwen-image-workflow.py`):

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-model image generation workflow.
DeepSeek (creative) -> Qwen (refine) -> SiliconFlow Flux (generate)
Also supports: --analyze (VL image analysis), --ocr (text extraction), --setup (configure Flux key)
"""

import urllib.request, json, ssl, sys, base64, os
from urllib.error import HTTPError

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# --- CONFIGURATION ---
DEEPSEEK_KEY = "sk-..."
DEEPSEEK_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"

QWEN_KEY = "sk-..."
QWEN_URL = "https://ws-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
QWEN_REFINE = "qwen3.7-max"
QWEN_VL = "qwen-vl-plus"
QWEN_OCR = "qwen-vl-ocr"

SILICONFLOW_KEY = ""  # Set via --setup
SILICONFLOW_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "black-forest-labs/FLUX.1-schnell"

# --- CORE FUNCTIONS ---

def call_llm(base_url, api_key, model, messages, max_tokens=4096, temperature=0.7, timeout=120):
    data = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, context=ctx, timeout=timeout)
    return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def call_vl(base_url, api_key, model, text, image_b64):
    content = [{"type": "text", "text": text}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}]
    data = json.dumps({"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 2000}).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, context=ctx, timeout=120)
    return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def generate_flux(prompt, api_key, output_path="output.png"):
    data = json.dumps({"model": SILICONFLOW_MODEL, "prompt": prompt, "n": 1, "size": "1024x1024"}).encode()
    req = urllib.request.Request(f"{SILICONFLOW_URL}/images/generations", data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, context=ctx, timeout=120)
    result = json.loads(resp.read().decode())
    b64 = result["data"][0].get("b64_json")
    if b64:
        with open(output_path, "wb") as f: f.write(base64.b64decode(b64))
        return f"Saved: {output_path}"
    url = result["data"][0].get("url")
    if url:
        img = urllib.request.urlopen(url, context=ctx).read()
        with open(output_path, "wb") as f: f.write(img)
        return f"Saved: {output_path}"
    return f"No image data: {result}"

# --- WORKFLOW ---

def deepseek_creative(user_request):
    prompt = f"""You are an AI image prompt engineer. User request: {user_request}
Output STRICT JSON: {{"short":"under 100 chars","detailed":"200-500 chars with composition, lighting, style, colors, mood, subject, environment","tags":"keyword1, keyword2"}}"""
    return call_llm(DEEPSEEK_URL, DEEPSEEK_KEY, DEEPSEEK_MODEL,
                    [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.8)

def qwen_refine(user_request, ds_output):
    prompt = f"""Original request: {user_request}\n\nDeepSeek output:\n{ds_output}\n\nRefine into accurate English prompt covering: subject, environment, lighting, style, color palette, composition, mood. Output only the final prompt."""
    return call_llm(QWEN_URL, QWEN_KEY, QWEN_REFINE,
                    [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.7)

def analyze_image(image_path):
    with open(image_path, "rb") as f: img_b64 = base64.b64encode(f.read()).decode()
    return call_vl(QWEN_URL, QWEN_KEY, QWEN_VL, "Describe this image in detail. Subject? Style? Colors? Composition? Give an English prompt to recreate it.", img_b64)

def ocr_image(image_path):
    with open(image_path, "rb") as f: img_b64 = base64.b64encode(f.read()).decode()
    return call_vl(QWEN_URL, QWEN_KEY, QWEN_OCR, "Extract all text from this image, preserve original formatting.", img_b64)

# --- CLI ---
def main():
    if len(sys.argv) < 2: print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "--setup":
        key = input("SiliconFlow API Key: ").strip()
        with open(".image_workflow_config.json", "w") as f: json.dump({"siliconflow_key": key}, f)
        print("Saved!")
    elif cmd == "--analyze": print(analyze_image(sys.argv[2]))
    elif cmd == "--ocr": print(ocr_image(sys.argv[2]))
    else:
        req = " ".join(sys.argv[1:]).replace("--generate", "")
        do_gen = "--generate" in " ".join(sys.argv[1:])
        ds = deepseek_creative(req); print("DS:", ds[:500])
        qw = qwen_refine(req, ds); print("QW:", qw[:500])
        print("="*50+"\nFINAL PROMPT:\n"+qw+"\n"+"="*50)
        if do_gen:
            sf_key = SILICONFLOW_KEY
            config_path = ".image_workflow_config.json"
            if os.path.exists(config_path):
                with open(config_path) as f: sf_key = json.load(f).get("siliconflow_key", "")
            if sf_key: print(generate_flux(qw, sf_key))
            else: print("Run --setup first for Flux key")
```

## Usage

```bash
# Generate prompt only
python ds-qwen-image-workflow.py "赛博朋克猫，霓虹灯，雨夜"

# Full pipeline: prompt + Flux image generation
python ds-qwen-image-workflow.py "橘猫在草地上" --generate

# Analyze image with Qwen VL
python ds-qwen-image-workflow.py --analyze photo.jpg

# OCR text from image
python ds-qwen-image-workflow.py --ocr screenshot.png

# Configure SiliconFlow key
python ds-qwen-image-workflow.py --setup
```

## Pitfalls

1. **Chinese comments break the execute_code sandbox**: The sandbox runs in a GBK environment. All Chinese characters in Python code comments cause `SyntaxError: Non-UTF-8 code starting with` errors. Use `# -*- coding: utf-8 -*-` header or avoid Chinese entirely in code that runs through the sandbox.

2. **`python3` vs `python` on Windows Git Bash**: On Windows Git Bash, `python3` returns exit code 49 (no output). Use `python` instead.

3. **Background processes in Git Bash**: Piping `python script.py > file &` and polling the file may not produce output in Windows Git Bash. Use foreground execution with adequate timeout instead.

4. **Image generation API timeout**: The workspace image models may take up to 5 minutes and still return empty. This is a workspace configuration limitation, not a code bug.

5. **External image URLs from China**: VL models may fail to download images from foreign hosts (Wikimedia, Imgur). Use base64-encoded images instead.

6. **SiliconFlow quota**: Free tier has monthly limits. Handle `HTTP 402/429` with clear error messages directing user to the website.
