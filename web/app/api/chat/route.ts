import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const upstream = await fetch("http://localhost:8080/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, stream: true, temperature: 0.7, max_tokens: 1024 }),
  });
  if (!upstream.ok) return new Response("Model server error", { status: 502 });
  return new Response(upstream.body, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
  });
}
