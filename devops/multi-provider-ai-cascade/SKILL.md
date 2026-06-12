---
name: multi-provider-ai-cascade
description: Implement a multi-provider AI API cascade with automatic failover — free tier first, paid fallback. OpenAI-format and Anthropic-format providers supported simultaneously. Build for Next.js API routes with SSE streaming.
---

# Multi-Provider AI API Cascade

Implement a failover chain for AI API calls: try free tier providers first (DashScope, SiliconFlow, etc.), fall back to paid providers (DeepSeek, OpenAI) when quota runs out.

## Architecture

```
User Request → /api/analyze
  ├─ [1st] DashScope (qwen-turbo, free quota)
  │   ├─ Success → SSE stream to frontend
  │   └─ 429/402/timeout → try next
  ├─ [2nd] DeepSeek V4 Flash (paid fallback)
  │   ├─ Success → SSE stream to frontend
  │   └─ Fail → 503 error
```

## Key Design Decisions

- **Two API formats**: OpenAI-compatible (`/v1/chat/completions`, used by DashScope/SiliconFlow) and Anthropic-compatible (`/v1/messages`, used by DeepSeek proxy). Both get normalized to a **unified SSE format** (`data: {"text":"..."}\n\n` + `data: {"done":true}\n\n`) before being sent to the frontend.
- **Quota detection**: HTTP 429 (rate limit) and 402 (payment required) trigger automatic failover. Network errors also trigger failover.
- **Environment variables**: Each provider gets its own env var. Missing/empty keys are skipped gracefully.

## Implementation

### 1. Provider configuration array

```typescript
const PROVIDERS = [
  {
    name: "DashScope",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    apiKey: process.env.DASHSCOPE_API_KEY || "",
    model: "qwen-turbo",
    format: "openai" as const,
  },
  {
    name: "DeepSeek",
    baseUrl: process.env.DEEPSEEK_PROXY_URL || "http://127.0.0.1:15721/anthropic/v1/messages",
    apiKey: process.env.DEEPSEEK_API_KEY || "",
    model: "deepseek-v4-flash",
    format: "anthropic" as const,
  },
];
```

### 2. Cascade loop

```typescript
for (const provider of PROVIDERS) {
  if (!provider.apiKey || provider.apiKey === "***") continue;
  try {
    const result = await tryProvider(provider, prompt);
    if (result) return result; // SSE stream Response
  } catch {
    // Fall through to next provider
  }
}
// All failed
return new Response(JSON.stringify({ error: "AI service unavailable" }), { status: 503 });
```

### 3. OpenAI format handler

```typescript
async function tryOpenAI(provider, prompt): Promise<Response | null> {
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

  if (res.status === 429 || res.status === 402) {
    await res.body?.cancel();
    return null; // Quota exhausted, try next
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  // Transform OpenAI SSE → unified SSE
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
            if (text) controller.enqueue(encoder.encode(
              `data: ${JSON.stringify({ text })}\n\n`
            ));
          } catch {}
        }
        buffer = "";
      }
      controller.enqueue(encoder.encode('data: {"done":true}\n\n'));
      controller.close();
    },
  });

  return new Response(stream, { headers: { "Content-Type": "text/event-stream", ... } });
}
```

### 4. Anthropic format handler

Same structure but different:
- **Auth header**: `x-api-key` instead of `Authorization: Bearer`
- **Body format**: `{ model, max_tokens, stream, messages: [{ role, content }] }`
- **SSE parsing**: `data.delta?.text` or `data.type === "content_block_delta" && data.delta?.text`

## Environment Variables (.env.local)

```bash
# Free tier first
DASHSCOPE_API_KEY=sk-your-dashscope-key

# Paid fallback
DEEPSEEK_PROXY_URL=http://127.0.0.1:15721/anthropic/v1/messages
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

For Vercel production, set these in the dashboard.

## Where to Register for Free Quota

| Provider | Free Tier | Signup |
|----------|-----------|--------|
| Alibaba Cloud DashScope (百炼) | 1M tokens new user + 1M/month for qwen-turbo | https://bailian.console.aliyun.com |
| SiliconFlow (硅基流动) | 20M tokens on signup | https://cloud.siliconflow.cn |

## Pitfalls

- **Format mismatch**: OpenAI format and Anthropic format have different request bodies AND different SSE response formats. Always handle both in separate functions.
- **Stream cancellation**: When quota is exhausted (`429`/`402`), the stream body must be cancelled with `await res.body?.cancel()` to release the connection before making the next provider call. Failing to do this leaks connections.
- **Frontend must handle unified SSE**: Both providers output `data: {"text":"..."}\n\n` chunks + `data: {"done":true}\n\n` terminator. The frontend reads SSE and accumulates text until `done`.
- **Keep `tryOpenAI`/`tryAnthropic` pure**: Return `null` for quota failure, throw for actual errors, return `Response` for success. The cascade loop distinguishes these three cases.
