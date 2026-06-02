# Václav AI

Terminálový prohlížeč s lokálním LLM, SQLite RAG databází a bezpečnostní analýzou.

## Jak to funguje

```
URL → bezpečnostní check → fetch + BeautifulSoup
    → chunky textu → SQLite FTS5 (full-text search)
    → otázka → FTS najde relevantnější chunks
    → LLM (Qwen3-4B fine-tuned) složí odpověď z kontextu
```

Kombinace starých chatbotů (keyword DB, pattern matching) + moderní LLM = rychlé, lokální, bez halucinací.

## Požadavky

- Python 3.11+
- `pip install mlx-lm beautifulsoup4 httpx rich`
- Apple Silicon (M1–M5)

## Spuštění

```bash
# 1. Spustit model server (po fine-tuningu)
mlx_lm.server --model ./models/fused --port 8080

# 2. Spustit browser
python3 browse.py https://mensagymnazium.cz
```

## Příkazy

| Příkaz | Funkce |
|--------|--------|
| `<url>` | Otevři stránku |
| `ask <otázka>` | Zeptej se LLM (RAG z DB) |
| `search <dotaz>` | Prohledej celou historii |
| `links` | Zobraz odkazy |
| `back` | Předchozí stránka |
| `history` | Historie návštěv |
| `quit` | Konec |

## Fine-tuning

```bash
python3 gen_dataset.py          # vygeneruj dataset
mlx_lm.lora --model Qwen/Qwen3-4B --train --data ./data --iters 600
mlx_lm.fuse --model Qwen/Qwen3-4B --adapter-path ./adapters --save-path ./models/fused
```

Model zůstává lokálně (není v repozitáři — příliš velký).
