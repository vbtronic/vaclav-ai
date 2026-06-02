#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vaclav AI Browser v2 — RAG + SQLite FTS5 + LLM + bezpecnost
Spusteni: python3 browse.py [url]
"""
import sys, sqlite3, re, textwrap
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

console = Console(width=100)

LLM_URL    = "http://localhost:8080/v1/chat/completions"
DB_PATH    = "/Users/viki/vaclav-ai/browser.db"
CHUNK_SIZE = 300
TOP_K      = 5

BLOCKED_DOMAINS = {"malware.testing.google.test", "eicar.org"}
PHISHING_WORDS  = [
    "verify your account", "enter your password", "you have won",
    "click here to claim", "your account will be suspended",
    "free crack download", "keylogger", "ransomware",
]

# ── Databáze + FTS5 ───────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY, title TEXT,
            fetched_at TEXT, safe INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL, chunk_index INTEGER NOT NULL, text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(text, url UNINDEXED, chunk_id UNINDEXED);
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT, title TEXT, visited_at TEXT
        );
        CREATE TABLE IF NOT EXISTS blocklist (
            domain TEXT PRIMARY KEY, reason TEXT
        );
    """)
    db.commit()
    return db

def index_page(db, url, title, chunks):
    db.execute("DELETE FROM chunks WHERE url=?", (url,))
    db.execute("DELETE FROM chunks_fts WHERE url=?", (url,))
    for i, chunk in enumerate(chunks):
        cur = db.execute(
            "INSERT INTO chunks (url, chunk_index, text) VALUES (?,?,?)", (url, i, chunk)
        )
        db.execute(
            "INSERT INTO chunks_fts (text, url, chunk_id) VALUES (?,?,?)",
            (chunk, url, cur.lastrowid)
        )
    db.commit()

def fts_search(db, query, limit=TOP_K):
    safe_q = re.sub(r"[^\w\s]", " ", query).strip()
    if not safe_q:
        return []
    try:
        rows = db.execute("""
            SELECT c.text, c.url, p.title
            FROM chunks_fts f
            JOIN chunks c ON c.id = f.chunk_id
            JOIN pages  p ON p.url = c.url
            WHERE chunks_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (safe_q, limit)).fetchall()
        return [{"text": r[0], "url": r[1], "title": r[2]} for r in rows]
    except Exception:
        return []

# ── Chunking ──────────────────────────────────────────────────────────────────

def split_chunks(text, size=CHUNK_SIZE):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)
            if len(" ".join(words[i:i+size])) > 50]

# ── Bezpečnost ────────────────────────────────────────────────────────────────

def safety_check(url, text, db):
    domain = urlparse(url).netloc.lower()
    if domain in BLOCKED_DOMAINS:
        return False, f"Domena {domain} v blocklist"
    row = db.execute("SELECT reason FROM blocklist WHERE domain=?", (domain,)).fetchone()
    if row:
        return False, f"Zablokovano: {row[0]}"
    hits = [w for w in PHISHING_WORDS if w in text.lower()]
    if len(hits) >= 2:
        return False, f"Podezrela slova: {hits}"
    return True, ""

# ── LLM ──────────────────────────────────────────────────────────────────────

def llm(messages, max_tokens=512):
    try:
        r = httpx.post(LLM_URL, json={
            "messages": messages, "max_tokens": max_tokens, "temperature": 0.4,
        }, timeout=60)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LLM nedostupny: {e}]"

def rag_answer(question, db, current_url=None):
    """
    Klicova funkce RAG:
    1. FTS5 najde nejrelevantnější chunky ze vsech stranck v DB
    2. LLM dostane jen tyto chunky jako kontext
    3. Odpovida pouze z toho, co je v DB — zadne halucinace
    """
    chunks = fts_search(db, question)

    # Doplnit chunky z aktualni stranky pokud jich je malo
    if current_url and len(chunks) < TOP_K:
        extra = db.execute(
            "SELECT text FROM chunks WHERE url=? LIMIT ?",
            (current_url, TOP_K - len(chunks))
        ).fetchall()
        existing = {c["text"] for c in chunks}
        for (t,) in extra:
            if t not in existing:
                chunks.append({"text": t, "url": current_url, "title": ""})

    if not chunks:
        # Zadne stranky v DB — LLM odpovida ze sve znalosti
        return llm([
            {"role": "system", "content": "Jsi Vaclav, cesky AI asistent. Odpovidas cesky."},
            {"role": "user",   "content": question},
        ])

    context = "\n\n---\n\n".join(
        f"[{c['title'] or c['url']}]\n{c['text']}" for c in chunks
    )
    return llm([
        {"role": "system", "content":
            "Jsi Vaclav. Odpovidas POUZE na zaklade poskytnutych zdrojovych textu. "
            "Kdyz informace neni ve zdrojich, rikej to. Odpovidas cesky, strukturovane."},
        {"role": "user", "content":
            f"Zdrojove texty z navstivenych stranek:\n\n{context}\n\n---\n\nOtazka: {question}"},
    ], max_tokens=700)

def llm_summarize(title, chunks):
    sample = " ".join(chunks[:2])[:1500]
    return llm([
        {"role": "system", "content": "Shrnuj kratce v 1-2 vetach cesky."},
        {"role": "user",   "content": f"{title}\n\n{sample}"},
    ], max_tokens=100)

# ── Fetch + indexace ──────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "VaclavBrowser/2.0 (RAG; educational)"}

def fetch(url, db):
    # Cache: pokud stranka je v DB a neni stara > 1h, pouzij ji
    cached = db.execute(
        "SELECT url, title FROM pages WHERE url=? AND fetched_at > datetime('now','-1 hour')",
        (url,)
    ).fetchone()
    if cached:
        n = db.execute("SELECT COUNT(*) FROM chunks WHERE url=?", (url,)).fetchone()[0]
        console.print(f"[dim]Z cache — {n} chunku indexovano[/dim]")
        return {"url": cached[0], "title": cached[1], "cached": True, "links": [], "summary": ""}

    try:
        with console.status("[cyan]Stahuji stranku…"):
            r = httpx.get(url, headers=HEADERS, timeout=12, follow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        console.print(f"[red]Chyba: {e}[/red]")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script","style","nav","footer","aside","header","noscript"]):
        tag.decompose()

    title = (soup.title.string or url).strip()
    text  = re.sub(r"\n{3,}", "\n\n", soup.get_text(separator=" ")).strip()
    links = [
        (a.get_text(strip=True), urljoin(url, a["href"]))
        for a in soup.find_all("a", href=True)
        if a.get_text(strip=True) and a["href"].startswith(("http", "/"))
    ]

    safe, warn = safety_check(url, text, db)
    if not safe:
        console.print(f"[bold red]VAROVANI: {warn}[/bold red]")
        if Prompt.ask("Presto otevrit?", choices=["ano","ne"], default="ne") != "ano":
            return None

    chunks = split_chunks(text)
    with console.status(f"[cyan]Indexuji {len(chunks)} chunku do SQLite FTS5…"):
        index_page(db, url, title, chunks)
        summary = llm_summarize(title, chunks)
        db.execute(
            "INSERT OR REPLACE INTO pages (url,title,fetched_at,safe) VALUES (?,?,datetime('now'),?)",
            (url, title, int(safe))
        )
        db.execute(
            "INSERT INTO history (url,title,visited_at) VALUES (?,?,?)",
            (url, title, datetime.now().isoformat())
        )
        db.commit()

    return {"url": url, "title": title, "summary": summary,
            "links": links, "cached": False, "text_preview": text[:1500]}

# ── Zobrazení ─────────────────────────────────────────────────────────────────

def show_page(page, db):
    n = db.execute("SELECT COUNT(*) FROM chunks WHERE url=?", (page["url"],)).fetchone()[0]
    console.print(Panel(
        f"[bold cyan]{page['title']}[/bold cyan]\n"
        f"[dim]{page['url']}[/dim]  [dim]({n} chunku v DB)[/dim]\n\n"
        + (f"[yellow]Shrnuti:[/yellow] {page['summary']}" if page.get("summary") else ""),
        title="Vaclav AI Browser", border_style="cyan"
    ))
    if page.get("text_preview"):
        console.print(textwrap.fill(page["text_preview"], 98))
        console.print("[dim]... (zobrazeno 1500 znaku)[/dim]")

def show_links(links):
    t = Table(show_lines=False)
    t.add_column("#", style="cyan", width=4)
    t.add_column("Text")
    t.add_column("URL", style="dim")
    for i, (text, url) in enumerate(links[:25], 1):
        t.add_row(str(i), text[:55], url[:60])
    console.print(t)

def show_history(db):
    rows = db.execute(
        "SELECT url, title, visited_at FROM history ORDER BY visited_at DESC LIMIT 20"
    ).fetchall()
    t = Table(title="Historie navstev")
    t.add_column("#", width=4, style="cyan")
    t.add_column("Nazev")
    t.add_column("URL", style="dim")
    t.add_column("Cas", style="dim", width=16)
    for i, (url, title, ts) in enumerate(rows, 1):
        t.add_row(str(i), (title or "")[:45], url[:52], ts[:16])
    console.print(t)

def show_help():
    console.print(Panel(
        "[cyan]Prikazy:[/cyan]\n"
        "  [bold]<url>[/bold]           otevri stranku + indexuj do DB\n"
        "  [bold]ask <otazka>[/bold]    RAG: FTS5 najde chunky → LLM odpovi\n"
        "  [bold]search <dotaz>[/bold]  prohledej celou DB + RAG odpoved\n"
        "  [bold]<cislo>[/bold]         sleduj odkaz c. X\n"
        "  [bold]links[/bold]           zobraz odkazy\n"
        "  [bold]history[/bold]         historie navstev\n"
        "  [bold]back[/bold]            predchozi stranka\n"
        "  [bold]reload[/bold]          znovu nacti (smaz cache)\n"
        "  [bold]block <domena>[/bold]  pridej do blacklistu\n"
        "  [bold]quit[/bold]            konec",
        title="Napoveda"
    ))

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    db    = get_db()
    page  = None
    stack = []

    console.print(Panel(
        "[bold violet]Vaclav AI Browser v2[/bold violet]\n"
        "[dim]RAG · SQLite FTS5 · Qwen3-4B lokalne · bezpecnostni analyza[/dim]\n"
        "Napiš URL nebo [cyan]help[/cyan].",
        border_style="violet"
    ))

    cmd = sys.argv[1] if len(sys.argv) > 1 else Prompt.ask("\n[cyan]>[/cyan]")

    while True:
        cmd = cmd.strip()

        if cmd in ("quit", "exit", "q"):
            console.print("[dim]Na shledanou.[/dim]")
            break
        elif cmd == "help":
            show_help()
        elif cmd == "links":
            if page and page.get("links"):
                show_links(page["links"])
            else:
                console.print("[yellow]Zadna stranka.[/yellow]")
        elif cmd == "history":
            show_history(db)
        elif cmd == "back":
            if stack:
                page = stack.pop()
                show_page(page, db)
            else:
                console.print("[yellow]Zadna predchozi stranka.[/yellow]")
        elif cmd == "reload" and page:
            db.execute("DELETE FROM pages WHERE url=?", (page["url"],))
            db.execute("DELETE FROM chunks WHERE url=?", (page["url"],))
            db.execute("DELETE FROM chunks_fts WHERE url=?", (page["url"],))
            db.commit()
            new = fetch(page["url"], db)
            if new:
                page = new
                show_page(page, db)
        elif cmd.startswith("ask "):
            q = cmd[4:].strip()
            with console.status("[cyan]RAG: FTS5 hleda relevantni chunky…"):
                answer = rag_answer(q, db, page["url"] if page else None)
            console.print(Panel(Markdown(answer), title="Vaclav (RAG)", border_style="violet"))
        elif cmd.startswith("search "):
            q = cmd[7:].strip()
            with console.status("[cyan]FTS5 + LLM hleda…"):
                chunks = fts_search(db, q, limit=8)
                answer = rag_answer(q, db, None)
            if chunks:
                seen = set()
                t = Table(title=f"Nalezene zdroje: {q}")
                t.add_column("Zdroj", style="cyan")
                t.add_column("Ukazka")
                for c in chunks:
                    if c["url"] not in seen:
                        seen.add(c["url"])
                        t.add_row(c["title"] or c["url"][:50], c["text"][:80] + "…")
                console.print(t)
            console.print(Panel(Markdown(answer), title="RAG odpoved", border_style="yellow"))
        elif cmd.startswith("block "):
            domain = cmd[6:].strip()
            db.execute("INSERT OR REPLACE INTO blocklist (domain,reason) VALUES (?,?)",
                       (domain, "manualne zablokovano"))
            db.commit()
            console.print(f"[red]Zablokovano: {domain}[/red]")
        elif cmd.isdigit() and page and page.get("links"):
            idx = int(cmd) - 1
            if 0 <= idx < len(page["links"]):
                new = fetch(page["links"][idx][1], db)
                if new:
                    stack.append(page)
                    page = new
                    show_page(page, db)
        elif cmd.startswith(("http://", "https://")):
            new = fetch(cmd, db)
            if new:
                if page:
                    stack.append(page)
                page = new
                show_page(page, db)
        elif cmd:
            console.print(f"[dim]Neznam '{cmd}'. Zkus 'help'.[/dim]")

        cmd = Prompt.ask("\n[cyan]>[/cyan]")

if __name__ == "__main__":
    main()
