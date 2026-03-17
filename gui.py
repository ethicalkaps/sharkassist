import threading
import tkinter as tk
from tkinter import font, messagebox, scrolledtext

import ollama_client
import prompt_builder
import session as session_module

# ── Colours ──────────────────────────────────────────────────────────────────
BG = "#1e1e2e"
SURFACE = "#2a2a3e"
ACCENT = "#7aa2f7"
GREEN = "#9ece6a"
YELLOW = "#e0af68"
RED = "#f7768e"
FG = "#cdd6f4"
FG_DIM = "#6c7086"

FONT_MONO = ("Consolas", 10)
FONT_UI = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 12, "bold")


class SharkAssistApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.session = session_module.Session()
        self._setup_window()
        self._build_ui()
        self._check_ollama()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        self.title("SharkAssist")
        self.configure(bg=BG)
        self.geometry("520x700")
        self.minsize(420, 500)
        self.resizable(True, True)
        # Keep the window always-on-top so it floats next to Wireshark
        self.attributes("-topmost", True)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # Title bar
        title_frame = tk.Frame(self, bg=ACCENT)
        title_frame.pack(fill="x")
        tk.Label(
            title_frame,
            text="🦈 SharkAssist",
            bg=ACCENT,
            fg=BG,
            font=FONT_TITLE,
            pady=6,
        ).pack(side="left", padx=12)

        self._status_label = tk.Label(
            title_frame, text="", bg=ACCENT, fg=BG, font=FONT_UI
        )
        self._status_label.pack(side="right", padx=12)

        # Query input
        tk.Label(self, text="Describe what you want to filter:", bg=BG, fg=FG,
                 font=FONT_UI, anchor="w").pack(fill="x", **pad)

        input_frame = tk.Frame(self, bg=SURFACE, bd=0)
        input_frame.pack(fill="x", padx=12)

        self._query_box = tk.Text(
            input_frame, height=3, bg=SURFACE, fg=FG, insertbackground=FG,
            font=FONT_UI, wrap="word", relief="flat", padx=8, pady=6,
        )
        self._query_box.pack(fill="x")
        self._query_box.bind("<Return>", self._on_enter)
        self._query_box.bind("<Shift-Return>", lambda e: None)  # allow newline

        # Buttons row
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=12, pady=(4, 8))

        self._submit_btn = tk.Button(
            btn_frame, text="Generate Filter", bg=ACCENT, fg=BG,
            font=FONT_UI, relief="flat", cursor="hand2",
            activebackground=FG, activeforeground=BG,
            command=self._submit,
        )
        self._submit_btn.pack(side="left")

        tk.Button(
            btn_frame, text="Clear Session", bg=SURFACE, fg=FG_DIM,
            font=FONT_UI, relief="flat", cursor="hand2",
            activebackground=RED, activeforeground=BG,
            command=self._clear_session,
        ).pack(side="left", padx=(8, 0))

        # Result area
        tk.Label(self, text="Result:", bg=BG, fg=FG, font=FONT_UI,
                 anchor="w").pack(fill="x", padx=12)

        result_frame = tk.Frame(self, bg=SURFACE)
        result_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        self._result_box = scrolledtext.ScrolledText(
            result_frame, bg=SURFACE, fg=FG, font=FONT_MONO, relief="flat",
            wrap="word", state="disabled", padx=10, pady=8,
        )
        self._result_box.pack(fill="both", expand=True)

        # Tag colours for result sections
        self._result_box.tag_config("label", foreground=ACCENT, font=(*FONT_MONO[:1], FONT_MONO[1], "bold"))
        self._result_box.tag_config("filter_val", foreground=GREEN, font=FONT_MONO)
        self._result_box.tag_config("expl_val", foreground=FG)
        self._result_box.tag_config("next_val", foreground=YELLOW)
        self._result_box.tag_config("error", foreground=RED)
        self._result_box.tag_config("dim", foreground=FG_DIM)
        self._result_box.tag_config("separator", foreground=FG_DIM)

        # History sidebar label
        tk.Label(self, text="Session history:", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=12)

        self._history_box = tk.Listbox(
            self, bg=SURFACE, fg=FG_DIM, font=("Segoe UI", 9),
            relief="flat", height=5, selectbackground=ACCENT,
            selectforeground=BG, activestyle="none",
        )
        self._history_box.pack(fill="x", padx=12, pady=(0, 12))
        self._history_box.bind("<<ListboxSelect>>", self._on_history_select)

    # ── Ollama health check ───────────────────────────────────────────────────

    def _check_ollama(self):
        if ollama_client.is_available():
            self._status_label.config(text="● mistral ready")
        else:
            self._status_label.config(text="● offline")
            self._append_result(
                "WARNING: Ollama / mistral not detected on localhost:11434.\n"
                "Start Ollama and run:  ollama pull mistral\n",
                tag="error",
            )

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_enter(self, event):
        """Submit on plain Enter; Shift+Enter inserts a newline."""
        if not event.state & 0x1:  # Shift not held
            self._submit()
            return "break"

    def _submit(self):
        query = self._query_box.get("1.0", "end").strip()
        if not query:
            return
        self._query_box.delete("1.0", "end")
        self._set_busy(True)
        self._append_result(f"\n▶ {query}\n", tag="dim")
        threading.Thread(target=self._run_query, args=(query,), daemon=True).start()

    def _run_query(self, query: str):
        try:
            messages = prompt_builder.build_prompt(query, self.session.get_history())
            raw = ollama_client.chat(messages)
            parsed = prompt_builder.parse_response(raw)
            self.session.add_exchange(query, raw, parsed)
            self.after(0, self._show_result, parsed)
        except ollama_client.OllamaError as exc:
            self.after(0, self._show_error, str(exc))
        finally:
            self.after(0, self._set_busy, False)

    def _show_result(self, parsed: dict):
        self._append_result("FILTER:      ", tag="label")
        self._append_result((parsed["filter"] or "(none)") + "\n", tag="filter_val")

        self._append_result("EXPLANATION: ", tag="label")
        self._append_result((parsed["explanation"] or "(none)") + "\n", tag="expl_val")

        self._append_result("NEXT STEPS:  ", tag="label")
        self._append_result((parsed["next_steps"] or "(none)") + "\n", tag="next_val")

        self._append_result("─" * 52 + "\n", tag="separator")
        self._refresh_history()

    def _show_error(self, message: str):
        self._append_result(f"Error: {message}\n", tag="error")

    def _clear_session(self):
        self.session.clear()
        self._history_box.delete(0, "end")
        self._result_box.config(state="normal")
        self._result_box.delete("1.0", "end")
        self._result_box.config(state="disabled")

    def _on_history_select(self, _event):
        idx = self._history_box.curselection()
        if not idx:
            return
        record = self.session.get_filters()[idx[0]]
        self._show_result(record)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_busy(self, busy: bool):
        if busy:
            self._submit_btn.config(state="disabled", text="Thinking…")
        else:
            self._submit_btn.config(state="normal", text="Generate Filter")

    def _append_result(self, text: str, tag: str = ""):
        self._result_box.config(state="normal")
        if tag:
            self._result_box.insert("end", text, tag)
        else:
            self._result_box.insert("end", text)
        self._result_box.see("end")
        self._result_box.config(state="disabled")

    def _refresh_history(self):
        self._history_box.delete(0, "end")
        for i, record in enumerate(self.session.get_filters(), 1):
            label = f"{i}. {record['query'][:55]}{'…' if len(record['query']) > 55 else ''}"
            self._history_box.insert("end", label)
