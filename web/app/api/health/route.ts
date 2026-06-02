export async function GET() {
  try {
    const res = await fetch("http://localhost:8080/v1/models", { signal: AbortSignal.timeout(2000) });
    return res.ok ? new Response("ok") : new Response("error", { status: 502 });
  } catch {
    return new Response("unreachable", { status: 503 });
  }
}
