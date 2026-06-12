---
name: custom-image-generation-workflow
description: 定制版图像生成工作流 — DeepSeek V4 Flash 做创意策划 + SiliconFlow Flux 免费出图。专为你的 Hermes + DeepSeek 环境优化，单文件脚本，一键运行。
tags: [image-generation, deepseek, flux, siliconflow, custom, workflow, windows]
---

# Custom Image Generation Workflow

你的专属图像生成方案。利用已有的 DeepSeek API，搭配硅基流动免费 Flux 出图。

## 前置条件

- DeepSeek API Key（已有，在 `~/.hermes/.env` 里）
- SiliconFlow 免费账号：[https://siliconflow.cn](https://siliconflow.cn)（注册即送免费额度）
- 不需要其他 API

## 架构

```
[需求] --> DeepSeek V4 Flash (提示词工程师) --> SiliconFlow Flux (出图)
                                                      |
                                                 output.png
```

## 完整脚本

```python
# -*- coding: utf-8 -*-
# image_workflow.py — DeepSeek + Flux 一键出图
import urllib.request, json, ssl, base64, os, sys
from urllib.error import HTTPError

ctx = ssl._create_unverified_context()

# === 配置 ===
DEEPSEEK_KEY = os.environ.get("OPENAI_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"
SILICONFLOW_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "black-forest-labs/FLUX.1-schnell"
CONFIG_FILE = os.path.expanduser("~/.hermes/.image_workflow.json")

def load_sf_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f).get("siliconflow_key", "")
    return ""

def save_sf_key(key):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"siliconflow_key": key}, f)
    print(f"[OK] SiliconFlow key saved to {CONFIG_FILE}")

def call_deepseek(prompt, max_tokens=2000, temp=0.8):
    data = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": temp
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{DEEPSEEK_URL}/chat/completions", data=data,
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}",
                 "Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, context=ctx, timeout=120)
    return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def generate_flux(prompt, sf_key, output="output.png"):
    data = json.dumps({
        "model": SILICONFLOW_MODEL, "prompt": prompt,
        "n": 1, "size": "1024x1024"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{SILICONFLOW_URL}/images/generations", data=data,
        headers={"Authorization": f"Bearer {sf_key}",
                 "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, context=ctx, timeout=300)
    result = json.loads(resp.read().decode())
    b64 = result["data"][0].get("b64_json")
    if b64:
        with open(output, "wb") as f:
            f.write(base64.b64decode(b64))
        return f"[OK] Saved: {output}"
    url = result["data"][0].get("url")
    if url:
        img_data = urllib.request.urlopen(url, context=ctx).read()
        with open(output, "wb") as f:
            f.write(img_data)
        return f"[OK] Saved: {output}"
    return f"[ERR] No image data: {result}"

def main():
    if not DEEPSEEK_KEY:
        print("[ERR] DeepSeek API key not found. Set OPENAI_API_KEY in env or .env")
        return
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python image_workflow.py --setup                  # 配置 SiliconFlow Key")
        print("  python image_workflow.py <prompt>                 # 只生成提示词")
        print("  python image_workflow.py <prompt> --generate      # 生成提示词+出图")
        print("  python image_workflow.py --generate <prompt>      # 同上")
        return
    if sys.argv[1] == "--setup":
        key = input("SiliconFlow API Key: ").strip()
        if key: save_sf_key(key)
        else: print("[ERR] Key cannot be empty")
        return
    do_gen = "--generate" in sys.argv
    words = [w for w in sys.argv[1:] if w != "--generate"]
    req = " ".join(words)
    print(f"[DeepSeek] 正在构思...")
    prompt = call_deepseek(
        f"You are an expert AI image prompt engineer. User wants: {req}\n"
        f"Write a detailed English prompt for FLUX.1-schnell model. "
        f"Include: subject, environment, lighting, style, color palette, composition, mood. "
        f"Output ONLY the prompt, no explanation."
    )
    print(f"=== FINAL PROMPT ===\n{prompt}\n====================")
    if do_gen:
        sf_key = load_sf_key()
        if not sf_key:
            print("[ERR] SiliconFlow key not configured. Run: python image_workflow.py --setup")
            return
        print(f"[Flux] 正在生成图片...")
        result = generate_flux(prompt, sf_key)
        print(result)

if __name__ == "__main__":
    main()
```

## 使用方法

```bash
# 1. 首次配置 SiliconFlow Key
python image_workflow.py --setup

# 2. 只生成提示词（不出图）
python image_workflow.py "赛博朋克猫，霓虹灯，雨夜"

# 3. 完整流程：出图
python image_workflow.py "橘猫在草地上晒太阳" --generate
```

## 对比原版技能的改进

| 项目 | 原版 | 定制版 |
|------|------|--------|
| 模型数量 | DeepSeek + Qwen + Flux 三个 | DeepSeek + Flux 两个（精简） |
| 依赖 | 需要 DeepSeek + 百炼(Qwen) + 硅基流动三个 Key | 只需要 DeepSeek(已有) + 硅基流动 |
| 配置存储 | 本地 JSON | `~/.hermes/` 目录下统一管理 |
| 脚本 | 单独文件 | 单文件，零依赖 |
| 编码处理 | 有 GBK 兼容问题 | 显式 utf-8 编码 |
| 报错提示 | 较简略 | 完整的错误提示 |

## Pitfalls

1. **SiliconFlow 免费额度有限制** — 每月有配额，用完了会返回 402/429 错误
2. **Flux.1-schnell 出图约 5-10 秒** — 比标准 Flux 快很多，但质量略低
3. **DeepSeek API 超时** — 如果 prompt 太长，设大 `timeout` 参数
4. **图片保存路径** — 默认当前目录的 `output.png`，可以改

## 验证

```bash
python image_workflow.py "a cute orange cat on grass, sunlight, warm colors" --generate
# 应该输出 === FINAL PROMPT === 然后保存 output.png
```
