"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { SYSTEM_PROMPT } from "@/lib/prompt";

interface Message { role: "user" | "assistant"; content: string; }

const STORAGE_KEY = "vaclav-history";
const WELCOME = "Ahoj! Jsem Václav, tvůj AI učitel. Na co se dnes učíš?";

function md(text: string) {
  return text
    .replace(/^### (.+)$/gm, "<h3>$1</h3>").replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>").replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>").replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^- (.+)$/gm, "<li>$1</li>").replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/\n\n/g, "</p><p>").replace(/^(?!<[hul])(.+)$/gm, m => m.trim() ? `<p>${m}</p>` : "")
    .replace(/<p><\/p>/g, "");
}

function load(): Message[] {
  if (typeof window === "undefined") return [{ role: "assistant", content: WELCOME }];
  try { const s = localStorage.getItem(STORAGE_KEY); if (s) { const p = JSON.parse(s); if (p.length) return p; } } catch {}
  return [{ role: "assistant", content: WELCOME }];
}

export default function Chat() {
  const [ready, setReady] = useState(false);
  const [offline, setOffline] = useState(false);
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: WELCOME }]);
  const [input, setInput] = useState("");
  const [generating, setGenerating] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setMessages(load());
    fetch("/api/health").then(r => r.ok ? setReady(true) : setOffline(true)).catch(() => setOffline(true));
  }, []);

  useEffect(() => {
    if (messages.length > 1) localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-100)));
  }, [messages]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = useCallback(async () => {
    if (!input.trim() || generating) return;
    const userMsg = input.trim();
    setInput("");
    setGenerating(true);
    const history: Message[] = [...messages, { role: "user", content: userMsg }];
    setMessages([...history, { role: "assistant", content: "" }]);
    try {
      const res = await fetch("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history] }),
      });
      const reader = res.body!.getReader();
      const dec = new TextDecoder();
      let full = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of dec.decode(value).split("\n")) {
          if (!line.startsWith("data: ") || line.includes("[DONE]")) continue;
          try { full += JSON.parse(line.slice(6)).choices?.[0]?.delta?.content ?? ""; } catch {}
          setMessages([...history, { role: "assistant", content: full }]);
        }
      }
    } catch { setMessages([...history, { role: "assistant", content: "Chyba spojení." }]); }
    setGenerating(false);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [input, messages, generating]);

  function handleKey(e: React.KeyboardEvent) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }

  if (offline) return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-center px-6">
      <div className="text-5xl">⚠️</div>
      <h1 className="text-xl font-bold text-white">Model server neběží</h1>
      <div className="bg-[#1c1c20] rounded-xl px-5 py-4 font-mono text-sm text-green-400 text-left max-w-lg w-full">
        <p className="text-gray-500 text-xs mb-2"># Spusť v terminálu:</p>
        <p>/opt/homebrew/opt/python@3.11/bin/python3.11 \</p>
        <p>&nbsp;&nbsp;-m mlx_lm server --model ~/vaclav-ai/models --port 8080</p>
      </div>
      <button onClick={() => { setOffline(false); fetch("/api/health").then(r => r.ok && setReady(true)).catch(() => setOffline(true)); }}
        className="text-sm text-violet-400 underline">Zkusit znovu</button>
    </div>
  );

  if (!ready) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center"><div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" /><p className="text-gray-400 text-sm">Připojuji se…</p></div>
    </div>
  );

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center gap-3 px-5 py-3 border-b border-white/8 bg-[#111114]">
        <div className="w-8 h-8 rounded-full bg-violet-600 flex items-center justify-center text-sm font-bold select-none">V</div>
        <div><p className="text-sm font-semibold text-white leading-tight">Václav</p><p className="text-xs text-gray-500">Qwen3-4B fine-tuned · lokální</p></div>
        <button onClick={() => { localStorage.removeItem(STORAGE_KEY); setMessages([{ role: "assistant", content: WELCOME }]); }}
          className="ml-auto text-xs text-gray-600 hover:text-gray-400 transition">Nová konverzace</button>
      </header>
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && <div className="w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 select-none">V</div>}
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${msg.role === "user" ? "bg-violet-600 text-white rounded-br-sm" : "bg-[#1c1c20] text-gray-100 rounded-bl-sm"}`}>
              {msg.role === "assistant"
                ? <div className="prose-chat" dangerouslySetInnerHTML={{ __html: msg.content ? md(msg.content) : generating && i === messages.length - 1 ? '<span class="inline-block w-2 h-4 bg-violet-400 animate-pulse rounded-sm"></span>' : "" }} />
                : msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-white/8 bg-[#111114] px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
            disabled={generating} placeholder="Napiš otázku nebo téma…" rows={1}
            className="flex-1 bg-[#1c1c20] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-violet-500 transition disabled:opacity-50"
            style={{ maxHeight: "120px" }}
            onInput={e => { const t = e.target as HTMLTextAreaElement; t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 120) + "px"; }} />
          <button onClick={send} disabled={generating || !input.trim()}
            className="bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white rounded-xl px-4 py-3 text-sm font-medium transition flex-shrink-0">
            {generating ? <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin block" /> : "→"}
          </button>
        </div>
        <p className="text-center text-xs text-gray-700 mt-2">Enter · Shift+Enter pro nový řádek</p>
      </div>
    </div>
  );
}
