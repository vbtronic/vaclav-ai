#!/usr/bin/env python3
"""
RAG HTTP server na portu 8081 — obaluje browse.py funkce pro web chatbot.
"""
import sys, json
from http.server import HTTPServer, BaseHTTPRequestHandler
sys.path.insert(0, "/Users/viki/vaclav-ai")
import browse

db = browse.get_db()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, data: dict, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._send({"error": "bad json"}, 400); return

        if self.path == "/fetch":
            url = body.get("url", "").strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            result = browse.fetch(url, db, skip_prompt=True)
            if result:
                self._send({"ok": True, "title": result.get("title", url),
                            "url": result["url"], "summary": result.get("summary", "")})
            else:
                self._send({"ok": False, "error": "Nepodařilo se načíst stránku."})

        elif self.path == "/rag":
            question = body.get("question", "").strip()
            url = body.get("url")
            if not question:
                self._send({"error": "prazdna otazka"}, 400); return
            answer = browse.rag_answer(question, db, url)
            self._send({"answer": answer})

        elif self.path == "/pages":
            rows = db.execute(
                "SELECT url, title FROM pages ORDER BY fetched_at DESC LIMIT 30"
            ).fetchall()
            self._send({"pages": [{"url": r[0], "title": r[1] or r[0]} for r in rows]})

        else:
            self._send({"error": "not found"}, 404)

if __name__ == "__main__":
    print("[rag_server] Spusten na http://localhost:8081")
    HTTPServer(("localhost", 8081), Handler).serve_forever()
