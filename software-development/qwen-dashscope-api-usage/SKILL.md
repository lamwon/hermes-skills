---
name: qwen-dashscope-api-usage
description: Using Alibaba Cloud DashScope/百炼 workspace APIs (OpenAI-compatible) for text, image analysis (VL), OCR, and image generation — with DeepSeek+Qwen collaborative workflows
---

# Qwen/DashScope Workspace API Usage

## Overview

Alibaba Cloud 百炼 (DashScope) workspace APIs provide a proxy to multiple models via the `ws-*.cn-beijing.maas.aliyuncs.com` domain. They support both OpenAI-compatible endpoints (`/compatible-mode/v1`) and native DashScope endpoints (`/api/v1`).

## Endpoints

- **OpenAI-compatible**: `https://{workspace}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions`
- **DashScope native**: `https://{workspace}.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/...`
- **Model listing**: `GET {base}/compatible-mode/v1/models` (with Bearer token)

All endpoints require `Authorization: Bearer {api_key}` header.

## Working Models & Call Formats

### Text Chat (works with plain content string)

```json
{
  "model": "qwen3.7-max",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 4096
}
```

Working text models: `qwen3.7-max`, `qwen3.6-flash`, `qwen3.5-flash`, `qwen-plus`, `qwen-turbo`, `qwen3.6-plus`, `deepseek-v4-flash`, `deepseek-v4-pro`

### Image Analysis (VL models — content must be list of items)

```json
{
  "model": "qwen-vl-plus",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "Describe this image"},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]
  }],
  "max_tokens": 2000
}
```

Working VL models: `qwen-vl-plus`, `qwen-vl-max`, `qwen2.5-vl-32b-instruct`
- **Base64 images work** reliably; external URLs may time out (API server connectivity issue)
- Format: `data:image/{format};base64,{base64_data}`

### OCR (image text extraction)

Same format as VL, use model `qwen-vl-ocr`.

### Image Generation (wan2.7-image-pro / qwen-image-2.0-pro)

```json
{
  "model": "wan2.7-image-pro",
  "messages": [{"role":"user","content":[{"type":"text","text":"prompt"}]}],
  "max_tokens": 8192
}
```

**Caveat**: This format is accepted by the API (returns 200 with proper fields) but **workspace APIs often return empty content** (2 completion tokens) because the workspace requires a callback URL for async image generation that isn't typically configured. The API accepts the request but the image data never comes back.

### Omni Models (qwen3.5-omni-plus, qwen-omni-turbo)

These work via chat completions with plain text content but only output **text**, not actual images. They can describe images via text input but can't generate image output.

## NOT Working

- `POST /compatible-mode/v1/images/generations` → 404 (not implemented)
- `POST /api/v1/services/aigc/text2image/image-synthesis` → "url error" (needs callback URL)
- `POST /api/v1/services/aigc/text2image` → "task can not be null"

## DeepSeek + Qwen Collaborative Image Workflow

A practical workflow when the workspace can't directly output images:

1. **DeepSeek V4 Flash** → Creative planning, writes detailed JSON prompt (short/detailed/tags)
2. **Qwen text model** (qwen3.7-max/qwen-plus) → Refines/translates the prompt into production-quality English with composition, lighting, style, color, mood
3. **Final prompt** → Used with any actual image generation tool (Flux, SD, DALL-E, Midjourney, SiliconFlow)

### SiliconFlow as Image Generation Fallback

When the Qwen workspace can't output images directly, **SiliconFlow (硅基流动)** is the most practical alternative from China:

- **Domain**: `https://api.siliconflow.cn/v1`
- **API format**: OpenAI-compatible `images/generations` endpoint
- **Working image models**: `Tongyi-MAI/Z-Image-Turbo`, `Kwai-Kolors/Kolors`, `baidu/ERNIE-Image-Turbo`, `Qwen/Qwen-Image`
- **Cost**: ~0.02-0.05 yuan per image (cheap)
- **Free credits**: ~13 yuan on signup as bonus balance

```python
def gen_image_siliconflow(prompt, api_key, output_path,
                           model="Tongyi-MAI/Z-Image-Turbo"):
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }).encode()
    req = urllib.request.Request("https://api.siliconflow.cn/v1/images/generations",
        data=data, headers={"Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, context=ctx, timeout=120)
    result = json.loads(resp.read().decode())
    img_url = result["data"][0]["url"]
    img_data = urllib.request.urlopen(urllib.request.Request(img_url)).read()
    with open(output_path, "wb") as f:
        f.write(img_data)
```

**⚠️ Balance issue**: Signup bonus credits often can't be used for image generation models. Error `"Sorry, your account balance is insufficient"` (code 30001) means image models require real topped-up balance (`chargeBalance`), not gift credits. Solution: top up a small amount (10 yuan = ~$1.40) at https://cloud.siliconflow.cn.

**Check balance**:
```python
req = urllib.request.Request("https://api.siliconflow.cn/v1/user/info",
    headers={"Authorization": f"Bearer {key}"})
resp = urllib.request.urlopen(req, context=ctx, timeout=10)
info = json.loads(resp.read().decode())
b = info["data"]
print(f"Total: {b['totalBalance']} yuan, ChargeBalance: {b['chargeBalance']} yuan")
```

### Complete Workflow Script

Save as `ds-qwen-image-workflow.py` with these modes:

```python
import urllib.request, json, ssl, sys, base64, os, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# === Config ===
DS_KEY = "sk-..."
DS_URL = "https://api.deepseek.com/v1"
QW_KEY = "sk-..."
QW_URL = "https://ws-{workspace}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
SF_KEY = "sk-..."  # SiliconFlow key (optional)

def llm(base_url, key, model, msgs, max_tokens=4096, temp=0.7, timeout=120):
    data = json.dumps({"model": model, "messages": msgs,
        "max_tokens": max_tokens, "temperature": temp}).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST")
    resp = urllib.request.urlopen(req, context=ctx, timeout=timeout)
    return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

# === Usage patterns ===

# 1. Generate prompt only: DeepSeek -> Qwen
user_req = "cyberpunk cat, neon lights, rainy night"

# Step 1: DeepSeek creates detailed JSON prompt
ds_result = llm(DS_URL, DS_KEY, "deepseek-v4-flash", [{"role": "user", "content":
    f"""You are an AI image prompt engineer. User request: {user_req}
Output JSON: {{"short":"under 100 chars","detailed":"200-500 chars: composition, lighting, style, colors, mood, subject, environment","tags":"keyword1, keyword2, keyword3"}}"""}])

# Step 2: Qwen refines into production prompt
final_prompt = llm(QW_URL, QW_KEY, "qwen3.7-max", [{"role": "user", "content":
    f"""Original request: {user_req}
DeepSeek output: {ds_result}
Refine into one detailed English prompt including: subject, environment, lighting, style, color, composition, mood.
Output only the final English prompt."""}])

print(final_prompt)

# 2. Analyze image with Qwen VL
def analyze_image(api_key, image_path):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    data = json.dumps({"model": "qwen-vl-plus", "messages": [{
        "role": "user", "content": [
            {"type": "text", "text": "Describe this image in detail"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]}], "max_tokens": 2000}).encode()
    req = urllib.request.Request(f"{QW_URL}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST")
    resp = urllib.request.urlopen(req, context=ctx, timeout=60)
    return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

# 3. OCR with qwen-vl-ocr
# Same as analyze_image but with model="qwen-vl-ocr" and prompt "Extract all text from this image"

# 4. Generate image with SiliconFlow (if key configured)
def gen_image(prompt, sf_key, output_path):
    data = json.dumps({"model": "Tongyi-MAI/Z-Image-Turbo", "prompt": prompt,
        "n": 1, "size": "1024x1024"}).encode()
    req = urllib.request.Request("https://api.siliconflow.cn/v1/images/generations",
        data=data, headers={"Authorization": f"Bearer {sf_key}",
        "Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=120)
        result = json.loads(resp.read().decode())
        img_url = result["data"][0]["url"]
        img_data = urllib.request.urlopen(urllib.request.Request(img_url)).read()
        with open(output_path, "wb") as f:
            f.write(img_data)
        return True, f"Saved: {output_path} ({len(img_data)//1024}KB)"
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        if "insufficient" in body:
            return False, "Balance insufficient. Top up at https://cloud.siliconflow.cn"
        return False, f"HTTP {e.code}: {body[:200]}"
```

## VL Image Analysis

For analyzing existing images with Qwen VL:

```python
# Encode image as base64
with open("image.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Call VL model
data = json.dumps({"model": "qwen-vl-plus", "messages": [{
    "role": "user", "content": [
        {"type": "text", "text": "Describe this image in detail"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
    ]}], "max_tokens": 2000}).encode()

# ... send request same as text chat format
```

## Pitfalls

1. **"url error" on image synthesis** → The workspace needs a configured callback URL for async results. This is a workspace-level config issue, not fixable via API calls.
2. **Chinese in f-strings** → In execute_code sandbox, Chinese characters in comments or f-strings cause `SyntaxError: Non-UTF-8 code starting with...`. Use `# -*- coding: utf-8 -*-` header or avoid Chinese in Python code within the sandbox.
3. **`python3` vs `python`** → On Windows/Git Bash, use `python` not `python3`.
4. **SiliconFlow balance types** → The API returns `balance` (total, includes gift credits) and `chargeBalance` (real money paid). Image generation models require `chargeBalance`. Even with 13 yuan bonus balance, you'll get "insufficient balance" (code 30001). Top up a small amount to activate image gen.
5. **SiliconFlow model availability varies by account** → List available models with `GET /v1/models`. Free-tier accounts may not see Flux models. Use `Tongyi-MAI/Z-Image-Turbo` as a reliable fallback.
6. **Qwen workspace image models are non-functional** → `wan2.7-image-pro`, `qwen-image-2.0-pro`, `z-image-turbo` etc. accept requests but return empty content (2 completion tokens). They cannot produce actual images through workspace APIs.
7. **DeepSeek prompt engineering format** → For best image prompts, use the JSON format: `{"short": "under 100 chars", "detailed": "200-500 chars with composition, lighting, style, colors, mood", "tags": "comma, separated"}`. This gives the Qwen refinement model structured content to work with.
4. **Content format matters** → VL/Omni/image models need `content` as a list `[{"type":"text","text":"..."}]`, not a plain string. Text-only models work with both.
5. **Image URL download timeouts** → The workspace API server may fail to download images from external URLs (Wikimedia, Imgur). Always use `data:` URIs with base64 for reliability.
6. **Model IDs are case-sensitive** → Use exact model IDs from the `/v1/models` endpoint listing.
