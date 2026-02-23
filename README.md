# EL MACHO AI

A CPU-only terminal AI with a lightweight local model and a nice TUI chat interface.

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
