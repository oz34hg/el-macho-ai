# EL MACHO AI

A CPU-only terminal AI with a lightweight local model and a nice TUI chat interface.

## Why this is fast on CPU

- Uses **TinyLlama 1.1B Chat** in a quantized **Q4_K_M GGUF** format.
- Typical RAM use stays below ~2GB in normal chat usage.
- Uses multiple CPU threads automatically.
- Downloads the model **only on first startup**.

## Requirements

- Python 3.10+
- Linux/macOS terminal (works in most modern terminals)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python terminal_ai.py
```

On first run, the app downloads the model to:

```text
~/.cache/el-macho-ai/
```

## Controls

- `Enter` send message
- `Ctrl+L` clear conversation
- `F1` show/hide help
- `Ctrl+C` quit

## Notes

- This app is **CPU-only** (`n_gpu_layers=0`).
- If you want even lower memory use, reduce `n_ctx` inside `terminal_ai.py`.
