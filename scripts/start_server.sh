#!/bin/bash
PY=/opt/homebrew/opt/python@3.11/bin/python3.11

# Uvolni porty pokud jsou obsazene
for PORT in 8080 8081; do
  if lsof -ti :$PORT > /dev/null 2>&1; then
    echo "[vaclav] Port $PORT obsazen, zabijim stary proces..."
    kill $(lsof -ti :$PORT) 2>/dev/null
    sleep 1
  fi
done

echo "[vaclav] Spoustim RAG server na portu 8081..."
$PY /Users/viki/vaclav-ai/rag_server.py &
RAG_PID=$!

echo "[vaclav] Spoustim Qwen3-4B na portu 8080..."
$PY -m mlx_lm server --model Qwen/Qwen3-4B --port 8080 &
LLM_PID=$!

echo "[vaclav] Oba servery bezí (RAG=$RAG_PID, LLM=$LLM_PID). Ctrl+C pro zastaveni."
wait
