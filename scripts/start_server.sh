#!/bin/bash
# Spusti Qwen3-4B base model (bez fine-tuningu) na portu 8080
PY=/opt/homebrew/opt/python@3.11/bin/python3.11

echo "[vaclav] Spoustim Qwen3-4B base model na portu 8080..."
$PY -m mlx_lm server \
  --model Qwen/Qwen3-4B \
  --port 8080
