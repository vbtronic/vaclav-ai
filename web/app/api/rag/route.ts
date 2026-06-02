import { NextRequest, NextResponse } from "next/server";

const RAG_URL = "http://localhost:8081/rag";

export async function POST(req: NextRequest) {
  const body = await req.json();
  try {
    const r = await fetch(RAG_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "RAG server nedostupný (port 8081)" }, { status: 503 });
  }
}
