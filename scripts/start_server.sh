#!/bin/bash
# Spusti Qwen3-4B base model (bez fine-tuningu) na portu 8080
PY=/opt/homebrew/opt/python@3.11/bin/python3.11

# Uvolni port 8080 pokud je obsazeny
if lsof -ti :8080 > /dev/null 2>&1; then
  echo "[vaclav] Port 8080 obsazen, zabijim stary proces..."
  kill $(lsof -ti :8080) 2>/dev/null
  sleep 1
fi

echo "[vaclav] Spoustim Qwen3-4B base model na portu 8080..."
$PY -m mlx_lm server \
  --model Qwen/Qwen3-4B \
  --port 8080
