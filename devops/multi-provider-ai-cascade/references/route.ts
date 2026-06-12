import { NextRequest } from "next/server";

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

export async function POST(req: NextRequest) {
  try {
    const { question, philosopher, isMismatch, oppositeName } = await req.json();
    if (!question || !philosopher) {
      return new Response(JSON.stringify({ error: "Missing required fields" }), { status: 400 });
    }

    const prompt = buildPrompt(question, philosopher, isMismatch);

    for (const provider of PROVIDERS) {
      if (!provider.apiKey || provider.apiKey === "***") continue;
      try {
        const result = await tryProvider(provider, prompt);
        if (result) return result;
      } catch (err: any) {
        console.warn(`${provider.name} failed:`, err.message);
      }
    }

    return new Response(JSON.stringify({ error: "AI service unavailable" }), { status: 503 });
  } catch (err) {
    return new Response(JSON.stringify({ error: "Internal server error" }), { status: 500 });
  }
}

function buildPrompt(question: string, philosopher: any, isMismatch: boolean): string {
  return ["## Task", `User's question: "${question}"`,
    `Respond using ${philosopher.name} (${philosopher.school})'s philosophy.`,
    "", "## Philosopher Profile",
    `Name: ${philosopher.name}`, `School: ${philosopher.school}`, `Era: ${philosopher.era}`,
    `Core: ${philosopher.summary}`, `Quote: ${philosopher.famousQuote || ""}`,
    `Works: ${philosopher.keyWorks?.join(", ") || ""}`,
    isMismatch ? `\n## Note\nUser deliberately picked an unrelated philosopher. Acknowledge playfully, then apply their framework anyway.` : "",
    "", "## Hard Rules",
    "1. Rephrase user's core dilemma in your own words (≤2 sentences)",
    "2. Quote user's original words at least 3 times with 「」",
    "3. Advice must stem from philosopher's unique method, not generic tips",
    "4. No 'You think you're asking X, but actually...' openers",
    "5. Alternate views must reference a real philosopher by name",
    "6. Use 'you', conversational tone like a wise friend",
    "", "## Output Structure (5 sections marked with 【】)",
    "【Your Blind Spot】Hidden assumptions in user's question, pierced with philosopher's quote (~100 chars)",
    "【Everyday Analogy】Concrete daily-life scene that embodies the philosophical idea (~150 chars)",
    "【Philosophical Dissection】Quote analysis tied to user's specific situation (200-300 chars)",
    "【Actionable Step】One thing user can do TODAY — not 'write this on your wall', a real executable action (100-150 chars)",
    "【Another Lens】Opposing philosopher's view, explain when each lens is useful (~100 chars)",
  ].filter(Boolean).join("\n");
}

async function tryProvider(provider: any, prompt: string): Promise<Response | null> {
  if (provider.format === "openai") return tryOpenAI(provider, prompt);
  return tryAnthropic(provider, prompt);
}

async function tryOpenAI(provider: any, prompt: string): Promise<Response | null> {
  const res = await fetch(provider.baseUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${provider.apiKey}` },
    body: JSON.stringify({ model: provider.model, max_tokens: 2048, stream: true, messages: [{ role: "user", content: prompt }] }),
  });
  if (res.status === 429 || res.status === 402) { await res.body?.cancel(); return null; }
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          for (const line of buffer.split("\n")) {
            const t = line.trim();
            if (!t || t === "data: [DONE]" || !t.startsWith("data: ")) continue;
            try {
              const text = JSON.parse(t.slice(6)).choices?.[0]?.delta?.content || "";
              if (text) controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
            } catch {}
          }
          buffer = "";
        }
      } finally {
        reader.releaseLock();
        controller.enqueue(encoder.encode('data: {"done":true}\n\n'));
        controller.close();
      }
    },
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" } });
}

async function tryAnthropic(provider: any, prompt: string): Promise<Response | null> {
  const res = await fetch(provider.baseUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": provider.apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model: provider.model, max_tokens: 2048, stream: true, messages: [{ role: "user", content: prompt }] }),
  });
  if (res.status === 429 || res.status === 402) { await res.body?.cancel(); return null; }
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          for (const line of buffer.split("\n")) {
            const t = line.trim();
            if (!t || t === "data: [DONE]" || !t.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(t.slice(6));
              const text = data.delta?.text || (data.type === "content_block_delta" && data.delta?.text) || "";
              if (text) controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
            } catch {}
          }
          buffer = "";
        }
      } finally {
        reader.releaseLock();
        controller.enqueue(encoder.encode('data: {"done":true}\n\n'));
        controller.close();
      }
    },
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" } });
}
