#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
import re
from threading import Thread
from typing import List, Tuple

from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Static

MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_DIR = Path.home() / ".cache" / "el-macho-ai"
SYSTEM_PROMPT = (
    "You are EL MACHO AI, a concise and friendly terminal assistant. "
    "Give practical, direct answers. Reply as the assistant only, without role labels "
    "(such as 'User:' or 'Assistant:') and never fabricate extra conversation turns."
)

ROLE_MARKER_RE = re.compile(
    r"(?:^|\n)\s*(?:you|user|customer|human|assistant|ai|system)\s*:\s*",
    re.IGNORECASE,
)


class HelpScreen(ModalScreen[None]):
    """Small help modal with keyboard shortcuts."""

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                "[b]EL MACHO AI[/b]\n\n"
                "Ctrl+L  Clear conversation\n"
                "Ctrl+C  Quit\n"
                "F1      Toggle this help\n\n"
                "Press Esc to close.",
                id="help-text",
            ),
            id="help-modal",
        )

    @on(Input.Submitted)
    def _ignore_submit(self) -> None:
        pass


class ChatUI(App[None]):
    """Textual app to chat with a local TinyLlama model."""

    TITLE = "EL MACHO AI"

    CSS = """
    Screen {
        background: #0b1020;
    }

    #root {
        height: 1fr;
        width: 100%;
        padding: 1 2;
    }

    #chat-box {
        height: 1fr;
        border: heavy #4f46e5;
        background: #0f172a;
        padding: 1;
        overflow-y: auto;
    }

    #input-row {
        height: 3;
        margin-top: 1;
    }

    #chat-input {
        border: round #38bdf8;
        background: #111827;
    }

    #status {
        width: 28;
        min-width: 28;
        border: heavy #22c55e;
        background: #0f172a;
        padding: 1;
        margin-left: 1;
    }

    #help-modal {
        width: 52;
        height: 12;
        border: heavy #a855f7;
        background: #111827;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("f1", "toggle_help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.model: Llama | None = None
        self.history: List[Tuple[str, str]] = []
        self.chat_lines: List[str] = []
        self.is_generating = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="root"):
            yield Static(id="chat-box")
            yield Static("[b]Status[/b]\nStarting...", id="status")
        with Container(id="input-row"):
            yield Input(placeholder="Type a message and press Enter...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        self._write_chat("[b cyan]System:[/b cyan] Loading model. First run downloads it automatically.")
        self._set_status("Booting")
        Thread(target=self._load_model, daemon=True).start()

    def action_toggle_help(self) -> None:
        if self.screen_stack and isinstance(self.screen_stack[-1], HelpScreen):
            self.pop_screen()
            return
        self.push_screen(HelpScreen())

    def action_clear_chat(self) -> None:
        self.history.clear()
        self.chat_lines = ["[dim]Conversation cleared.[/dim]"]
        self.query_one("#chat-box", Static).update(self.chat_lines[0])

    def _write_chat(self, text: str) -> None:
        chat_box = self.query_one("#chat-box", Static)
        self.chat_lines.append(text)
        chat_box.update("\n\n".join(self.chat_lines))
        chat_box.scroll_end(animate=False)

    def _set_status(self, state: str) -> None:
        self.query_one("#status", Static).update(f"[b]Status[/b]\n{state}")

    def _load_model(self) -> None:
        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model_path = hf_hub_download(
                repo_id=MODEL_REPO,
                filename=MODEL_FILE,
                local_dir=str(MODEL_DIR),
                local_dir_use_symlinks=False,
            )
            threads = max(2, min(8, (os.cpu_count() or 4) - 1))
            self.model = Llama(
                model_path=model_path,
                n_ctx=1024,
                n_threads=threads,
                n_gpu_layers=0,
                verbose=False,
            )
            self.call_from_thread(self._set_status, "Ready (CPU)")
            self.call_from_thread(
                self._write_chat,
                "[b green]System:[/b green] Ready. This runs fully on CPU with a light quantized model.",
            )
        except Exception as exc:  # pragma: no cover - startup safety
            self.call_from_thread(self._set_status, "Error")
            self.call_from_thread(self._write_chat, f"[b red]Error:[/b red] {exc}")

    @on(Input.Submitted, "#chat-input")
    def on_submitted(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        event.input.value = ""

        if not message:
            return
        if self.is_generating:
            self._write_chat("[yellow]System:[/yellow] Please wait, still generating.")
            return
        if self.model is None:
            self._write_chat("[yellow]System:[/yellow] Model not ready yet, please wait.")
            return

        self.history.append(("user", message))
        self._write_chat(f"[b #38bdf8]You:[/b #38bdf8] {message}")
        self.is_generating = True
        self._set_status("Thinking...")
        Thread(target=self._generate_reply, daemon=True).start()

    def _build_prompt(self) -> str:
        lines = [f"<|system|>\n{SYSTEM_PROMPT}\n</s>\n"]
        for role, text in self.history[-8:]:
            lines.append(f"<|{role}|>\n{text}\n</s>\n")
        lines.append("<|assistant|>\n")
        return "".join(lines)

    def _clean_assistant_reply(self, text: str) -> str:
        """Keep only the first assistant turn and remove chat role prefixes."""
        cleaned = text.strip()
        cleaned = re.sub(r"^\s*(?:assistant|ai)\s*:\s*", "", cleaned, flags=re.IGNORECASE)

        marker = ROLE_MARKER_RE.search(cleaned)
        if marker:
            cleaned = cleaned[: marker.start()].rstrip()

        return cleaned or "(No response generated)"

    def _generate_reply(self) -> None:
        assert self.model is not None
        try:
            prompt = self._build_prompt()
            output = self.model(
                prompt,
                max_tokens=220,
                temperature=0.6,
                top_p=0.9,
                stop=["<|user|>", "<|system|>", "<|assistant|>", "</s>"],
            )
            raw_answer = output["choices"][0]["text"]
            answer = self._clean_assistant_reply(raw_answer)
            self.history.append(("assistant", answer))
            self.call_from_thread(self._write_chat, f"[b #22c55e]AI:[/b #22c55e] {answer}")
            self.call_from_thread(self._set_status, "Ready (CPU)")
        except Exception as exc:  # pragma: no cover - generation safety
            self.call_from_thread(self._write_chat, f"[b red]Error:[/b red] {exc}")
            self.call_from_thread(self._set_status, "Error")
        finally:
            self.is_generating = False


def main() -> None:
    ChatUI().run()


if __name__ == "__main__":
    main()
