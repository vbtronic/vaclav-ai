#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vaclav Browser - terminálový prohlížeč s LLM + SQLite
Spuštění: python3 browse.py [url]
"""
import sys, sqlite3, json, re, time, textwrap
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

console = Console(width=100)

LLM_URL = "http://localhost:8080/v1/chat/completions"
DB_PATH  = "/Users/viki/ucitel/browser/browser.db"

BLOCKED_DOMAINS = {
    "malware.testing.google.test", "eicar.org",
}

SUSPICIOUS_KEYWORDS = [
    "download free crack", "virus total", "keylogger", "ransomware",
    "enter your password", "verify your account immediately",
    "you have won", "click here to claim",
]

# ── Databáze ──────────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            title TEXT, text TEXT, summary TEXT,
            safe INTEGER DEFAULT 1, fetched_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT, title TEXT, visited_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS blocklist (
            domain TEXT PRIMARY KEY, reason TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT, role TEXT, content TEXT, ts TEXT
        )
    """)
    db.commit()
    return db

# ── Bezpečnost ────────────────────────────────────────────────────────────────

def is_safe_url(url: str, db) -> tuple[bool, str]:
    domain = urlparse(url).netloc.lower()
    if domain in BLOCKED_DOMAINS:
        return False, f"Doména {domain} je v blocklist."
    row = db.execute("SELECT reason FROM blocklist WHERE domain=?", (domain,)).fetchone()
    if row:
        return False, f"Zablokováno: {row[0]}"
    return True, ""

def llm_safety_check(text: str) -> tuple[bool, str]:
    hits = [kw for kw in SUSPICIOUS_KEYWORDS if kw.lower() in text.lower()]
    if not hits:
        return True, ""
    prompt = (
        f"Stránka obsahuje tato podezřelá slova: {hits}. "
        "Je tato stránka bezpečná? Odpověz POUZE: BEZPECNA nebo NEBEZPECNA a jeden řádek důvodu."
    )
    reply = llm_ask(prompt, context="", system="Jsi bezpečnostní analyzátor webových stránek.")
    safe = "NEBEZPECNA" not in reply.upper()
    return safe, reply

# ── LLM ──────────────────────────────────────────────────────────────────────

def llm_ask(question: str, context: str, system: str = "") -> str:
    if not system:
        system = "Jsi Václav, chytrý asistent. Odpovídej česky, stručně a přesně."
    messages = [{"role": "system", "content": system}]
    if context:
        messages.append({"role": "user", "content": f"Obsah stránky:\n{context[:3000]}"})
        messages.append({"role": "assistant", "content": "Rozumím obsahu stránky."})
    messages.append({"role": "user", "content": question})
    try:
        r = httpx.post(LLM_URL, json={
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.4,
        }, timeout=30)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LLM nedostupný: {e}]"

def llm_summarize(title: str, text: str) -> str:
    return llm_ask(
        f"Shrň tuto stránku '{title}' v 2 větách česky.",
        context=text,
        system="Jsi stručný asistent. Shrnutí max 2 věty."
    )

def llm_search(query: str, pages: list) -> str:
    if not pages:
        return "Žádné stránky v historii."
    index = "\n".join(f"[{i+1}] {p[0]} — {p[1]}: {p[2][:100]}" for i, p in enumerate(pages))
    return llm_ask(
        f"Které stránky jsou nejrelevantnější pro dotaz: '{query}'? Uveď čísla a důvody.",
        context=index,
        system="Jsi vyhledávací asistent. Odpovídej česky."
    )

# ── Fetch + parse ─────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "VaclavBrowser/1.0 (terminal; educational)"}

def fetch_page(url: str, db) -> dict | None:
    cached = db.execute(
        "SELECT url,title,text,summary,safe FROM pages WHERE url=? AND fetched_at > datetime('now','-1 hour')",
        (url,)
    ).fetchone()
    if cached:
        return {"url": cached[0], "title": cached[1], "text": cached[2],
                "summary": cached[3], "safe": cached[4], "cached": True}

    try:
        with console.status("[cyan]Stahuji stránku…"):
            r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        console.print(f"[red]Chyba při stahování: {e}[/red]")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else url
    text  = re.sub(r"\n{3,}", "\n\n", soup.get_text(separator="\n")).strip()
    links = [(a.get_text(strip=True), urljoin(url, a["href"]))
             for a in soup.find_all("a", href=True)
             if a.get_text(strip=True) and a["href"].startswith(("http", "/"))]

    with console.status("[cyan]LLM analyzuje stránku…"):
        summary = llm_summarize(title, text)
        safe, warn = llm_safety_check(text)

    db.execute(
        "INSERT OR REPLACE INTO pages (url,title,text,summary,safe,fetched_at) VALUES (?,?,?,?,?,datetime('now'))",
        (url, title, text[:20000], summary, int(safe))
    )
    db.execute(
        "INSERT INTO history (url,title,visited_at) VALUES (?,?,?)",
        (url, title, datetime.now().isoformat())
    )
    db.commit()

    if not safe:
        console.print(f"[bold red]VAROVANI: {warn}[/bold red]")

    return {"url": url, "title": title, "text": text, "summary": summary,
            "safe": safe, "links": links, "cached": False}

# ── Zobrazení ─────────────────────────────────────────────────────────────────

def display_page(page: dict):
    safe_icon = "[green]BEZPECNA[/green]" if page["safe"] else "[red]NEBEZPECNA[/red]"
    cached_note = " [dim](z cache)[/dim]" if page.get("cached") else ""
    console.print(Panel(
        f"[bold cyan]{page['title']}[/bold cyan]\n"
        f"[dim]{page['url']}[/dim]{cached_note}\n\n"
        f"[yellow]Shrnutí:[/yellow] {page['summary']}\n\n"
        f"Bezpečnost: {safe_icon}",
        title="Václav Browser", border_style="cyan"
    ))
    wrapped = textwrap.fill(page["text"][:2000], width=98)
    console.print(wrapped)
    console.print(f"\n[dim]... (zobrazeno 2000/{len(page['text'])} znaků)[/dim]")

def display_links(links: list):
    t = Table(title="Odkazy na stránce", show_lines=False)
    t.add_column("#", style="cyan", width=4)
    t.add_column("Text", style="white")
    t.add_column("URL", style="dim")
    for i, (text, url) in enumerate(links[:20], 1):
        t.add_row(str(i), text[:50], url[:60])
    console.print(t)

def display_history(db):
    rows = db.execute(
        "SELECT url, title, visited_at FROM history ORDER BY visited_at DESC LIMIT 20"
    ).fetchall()
    t = Table(title="Historie")
    t.add_column("#", width=4, style="cyan")
    t.add_column("Název")
    t.add_column("URL", style="dim")
    t.add_column("Čas", style="dim")
    for i, (url, title, ts) in enumerate(rows, 1):
        t.add_row(str(i), (title or "")[:40], url[:50], ts[:16])
    console.print(t)

# ── Hlavní smyčka ─────────────────────────────────────────────────────────────

def help_text():
    console.print(Panel(
        "[cyan]Příkazy:[/cyan]\n"
        "  [bold]<url>[/bold]           — otevři stránku\n"
        "  [bold]<číslo>[/bold]         — sleduj odkaz č. X\n"
        "  [bold]ask <otázka>[/bold]    — zeptej se LLM na aktuální stránku\n"
        "  [bold]search <dotaz>[/bold]  — prohledej historii pomocí LLM\n"
        "  [bold]links[/bold]           — zobraz všechny odkazy\n"
        "  [bold]history[/bold]         — zobraz historii\n"
        "  [bold]reload[/bold]          — znovu načti stránku (ignoruj cache)\n"
        "  [bold]back[/bold]            — předchozí stránka\n"
        "  [bold]help[/bold]            — tato nápověda\n"
        "  [bold]quit[/bold]            — konec",
        title="Václav Browser — nápověda"
    ))

def main():
    db = get_db()
    page = None
    stack = []

    console.print(Panel(
        "[bold violet]Václav Browser[/bold violet]\n"
        "[dim]LLM + databáze · bezpečný · lokální[/dim]\n"
        "Napiš [cyan]help[/cyan] pro seznam příkazů.",
        border_style="violet"
    ))

    start_url = sys.argv[1] if len(sys.argv) > 1 else None
    if start_url:
        cmd = start_url
    else:
        cmd = Prompt.ask("\n[cyan]>[/cyan]")

    while True:
        cmd = cmd.strip()

        if cmd in ("quit", "exit", "q"):
            console.print("[dim]Na shledanou.[/dim]")
            break

        elif cmd == "help":
            help_text()

        elif cmd == "links":
            if page and page.get("links"):
                display_links(page["links"])
            else:
                console.print("[yellow]Žádná stránka otevřena.[/yellow]")

        elif cmd == "history":
            display_history(db)

        elif cmd == "back":
            if stack:
                page = stack.pop()
                display_page(page)
            else:
                console.print("[yellow]Žádná předchozí stránka.[/yellow]")

        elif cmd == "reload" and page:
            db.execute("DELETE FROM pages WHERE url=?", (page["url"],))
            db.commit()
            safe, warn = is_safe_url(page["url"], db)
            if not safe:
                console.print(f"[red]{warn}[/red]")
            else:
                new = fetch_page(page["url"], db)
                if new:
                    if page:
                        stack.append(page)
                    page = new
                    display_page(page)

        elif cmd.startswith("ask "):
            question = cmd[4:].strip()
            if not page:
                console.print("[yellow]Nejprve otevři stránku.[/yellow]")
            else:
                with console.status("[cyan]LLM přemýšlí…"):
                    answer = llm_ask(question, context=page["text"])
                db.execute("INSERT INTO chat (url,role,content,ts) VALUES (?,?,?,?)",
                           (page["url"], "user", question, datetime.now().isoformat()))
                db.execute("INSERT INTO chat (url,role,content,ts) VALUES (?,?,?,?)",
                           (page["url"], "assistant", answer, datetime.now().isoformat()))
                db.commit()
                console.print(Panel(Markdown(answer), title="Václav", border_style="violet"))

        elif cmd.startswith("search "):
            query = cmd[7:].strip()
            pages = db.execute(
                "SELECT url, title, summary FROM pages ORDER BY fetched_at DESC LIMIT 30"
            ).fetchall()
            with console.status("[cyan]LLM hledá…"):
                result = llm_search(query, pages)
            console.print(Panel(result, title=f"Výsledky pro: {query}", border_style="yellow"))

        elif cmd.isdigit() and page and page.get("links"):
            idx = int(cmd) - 1
            links = page["links"]
            if 0 <= idx < len(links):
                target_url = links[idx][1]
                safe, warn = is_safe_url(target_url, db)
                if not safe:
                    console.print(f"[red]ZABLOKOVÁNO: {warn}[/red]")
                else:
                    new = fetch_page(target_url, db)
                    if new:
                        stack.append(page)
                        page = new
                        display_page(page)
            else:
                console.print("[yellow]Neplatné číslo odkazu.[/yellow]")

        elif cmd.startswith("http://") or cmd.startswith("https://"):
            safe, warn = is_safe_url(cmd, db)
            if not safe:
                console.print(f"[red]ZABLOKOVÁNO: {warn}[/red]")
            else:
                new = fetch_page(cmd, db)
                if new:
                    if page:
                        stack.append(page)
                    page = new
                    display_page(page)

        else:
            if cmd:
                console.print(f"[dim]Neznámý příkaz '{cmd}'. Napiš 'help'.[/dim]")

        cmd = Prompt.ask("\n[cyan]>[/cyan]")

if __name__ == "__main__":
    main()
