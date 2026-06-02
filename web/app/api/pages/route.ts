import { NextResponse } from "next/server";

export async function GET() {
  try {
    const r = await fetch("http://localhost:8081/pages", { method: "POST", body: "{}" });
    const data = await r.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ pages: [] });
  }
}
