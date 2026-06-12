---
name: multi-provider-cascade-fallback
description: Chain multiple AI API providers with automatic fallback when free tier quotas run out. Supports OpenAI-format and Anthropic-format providers simultaneously.
---

# Multi-Provider Cascade Fallback Pattern

Chain multiple AI API providers in priority order. If one returns 429 (rate limited) or 402 (quota exhausted), automatically try the next. Both OpenAI-format and Anthropic-format supported.

## Architecture

```
Request → Provider 1 (free tier) → success → return
                    ↓ 429/402/fail
              Provider 2 (cheap tier) → success → return
                    ↓ fail
              Provider 3 (paid fallback) → return
                    ↓ fail
              503 error
```

## Implementation (Next.js API Route)

### 1. Define providers array

```typescript
const PROVIDERS = [
  {
    name: "DashScope",                          // 阿里云百炼
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    apiKey: process.env.DASHSCOPE_API_KEY || "",
    model: "qwen-turbo",
    format: "openai" as const,                  // OpenAI 兼容格式
  },
  {
    name: "DeepSeek",
    baseUrl: process.env.DEEPSEEK_PROXY_URL || "http://127.0.0.1:15721/anthropic/v1/messages",
    apiKey: process.env.DEEPSEEK_API_KEY || "",
    model: "deepseek-v4-flash",
    format: "anthropic" as const,               // Anthropic 格式
  },
];
```

### 2. Cascade loop

```typescript
export async function POST(req: NextRequest) {
  // ... parse body, build prompt ...
  
  let lastError = "";
  for (const provider of PROVIDERS) {
    if (!provider.apiKey || provider.apiKey === "***") continue;
    try {
      const result = await tryProvider(provider, prompt);
      if (result) return result;
    } catch (err: any) {
      lastError = `${provider.name}: ${err.message}`;
      continue;
    }
  }
  return new Response(JSON.stringify({ error: "All providers failed" }), { status: 503 });
}
```

### 3. Provider dispatch

```typescript
async function tryProvider(provider, prompt) {
  if (provider.format === "openai") return tryOpenAI(provider, prompt);
  else return tryAnthropic(provider, prompt);
}
```

### 4. OpenAI-format handler (DashScope, SiliconFlow, etc.)

```typescript
async function tryOpenAI(provider, prompt) {
  const res = await fetch(provider.baseUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${provider.apiKey}`,
    },
    body: JSON.stringify({
      model: provider.model,
      max_tokens: 2048,
      stream: true,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  // Quota exhausted → return null to trigger next provider
  if (res.status === 429 || res.status === 402) {
    await res.body?.cancel();
    return null;
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  // Transform OpenAI SSE → unified SSE format
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        for (const line of buffer.split("\n")) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === "data: [DONE]") continue;
          if (!trimmed.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(trimmed.slice(6));
            const text = data.choices?.[0]?.delta?.content || "";
            if (text) controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
          } catch {}
        }
        buffer = "";
      }
      reader.releaseLock();
      controller.enqueue(encoder.encode('data: {"done":true}\n\n'));
      controller.close();
    },
  });
  return new Response(stream, { headers: SSE_HEADERS });
}
```

### 5. Anthropic-format handler (DeepSeek / cc-switch)

```typescript
async function tryAnthropic(provider, prompt) {
  const res = await fetch(provider.baseUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": provider.apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: provider.model,
      max_tokens: 2048,
      stream: true,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  if (res.status === 429 || res.status === 402) {
    await res.body?.cancel();
    return null;
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  // Transform Anthropic SSE → unified SSE format
  // ... same pattern, but parse: data.delta?.text || (data.type === "content_block_delta" && data.delta?.text)
}
```

## Unified SSE output format (frontend receives this from all providers)

```typescript
// Each chunk:
data: {"text":"..."}\n\n

// End signal:
data: {"done":true}\n\n
```

## Frontend consumer (TypeScript)

```typescript
const res = await fetch("/api/analyze", { method: "POST", body: JSON.stringify({...}) });
const reader = res.body.getReader();
const decoder = new TextDecoder();
let fullText = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value, { stream: true });
  for (const line of chunk.split("\n")) {
    const trimmed = line.trim();
    if (trimmed.startsWith("data: ") && !trimmed.includes('"done"')) {
      try {
        const data = JSON.parse(trimmed.slice(6));
        if (data.text) fullText += data.text;
      } catch {}
    }
  }
}
```

## Known Providers with Free Tiers

| Provider | Free Quota | API Format | Signup |
|----------|-----------|------------|--------|
| 阿里云百炼 DashScope | 新用户100万tokens, qwen-turbo每月100万免费 | OpenAI | bailian.console.aliyun.com |
| 硅基流动 SiliconFlow | 注册送2000万tokens | OpenAI | cloud.siliconflow.cn |
| DeepSeek (paid) | ¥1/百万tokens | Anthropic | platform.deepseek.com |

## Key Points

- **`429` (rate limit) and `402` (quota exhausted)** trigger cascade — any other HTTP error skips to next provider
- `await res.body?.cancel()` is critical to release connection before trying next provider
- Empty API key (`""` or `"***"`) skips that provider silently
- Both format handlers output **the same unified SSE format** — frontend doesn't know which provider served
- The cascade adds ~1-3s latency per failed provider (network timeout), so keep timeouts reasonable
