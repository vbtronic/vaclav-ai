#!/bin/bash
PY=/opt/homebrew/opt/python@3.11/bin/python3.11
FINETUNE_DIR=/Users/viki/ucitel/finetune
LOG=$FINETUNE_DIR/deploy.log

echo "[auto_deploy] Cekam na dokonceni fine-tuningu (PID 18586)..." | tee -a $LOG

while kill -0 18586 2>/dev/null; do
  sleep 5
done

echo "[auto_deploy] Fine-tuning dokoncen! Spoustim fuse..." | tee -a $LOG

$PY -m mlx_lm fuse \
  --model Qwen/Qwen3-4B \
  --adapter-path $FINETUNE_DIR/adapters \
  --save-path $FINETUNE_DIR/fused \
  >> $LOG 2>&1

echo "[auto_deploy] Fuse hotov. Spoustim server na portu 8080..." | tee -a $LOG

$PY -m mlx_lm server \
  --model $FINETUNE_DIR/fused \
  --port 8080 \
  >> $LOG 2>&1
