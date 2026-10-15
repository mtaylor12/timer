"""
Clock Timer
A simple countdown timer with alarm beeps.
Runs small on the screen — set any hours/minutes/seconds.

Requirements: Python 3.x (tkinter included with Python)
To build .exe: pyinstaller --onefile --windowed timer.py
"""

import tkinter as tk
from tkinter import font as tkfont
import math
import winsound  # Windows built-in beep — no extra libraries needed


# ── Colours ──────────────────────────────────────────────────────────────────
BG          = "#1a1a1a"
BG_INPUT    = "#2b2b2b"
FG          = "#e8e8e8"
FG_DIM      = "#555555"
FG_RUNNING  = "#7ec8e3"
FG_DONE     = "#f4a261"
BTN_START   = "#3d8b6e"
BTN_PAUSE   = "#5a7fa8"
BTN_RESET   = "#2b2b2b"
BORDER      = "#3a3a3a"

CLOCK_EMOJIS = ["🕐","🕑","🕒","🕓","🕔","🕕","🕖","🕗","🕘","🕙","🕚","🕛"]


class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Timer")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)   # frameless window

        # Window size & centre on screen
        W, H = 200, 260
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        # State
        self.remaining  = 0
        self.running    = False
        self.paused     = False
        self._after_id  = None
        self._emoji_idx = 0
        self._blink_on  = True

        # Drag support
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar (drag handle + close) ───────────────────────────────────
        titlebar = tk.Frame(self.root, bg="#111111", height=22)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        tk.Label(titlebar, text="  ⏱ Timer", bg="#111111", fg="#888888",
                 font=("Helvetica", 9)).pack(side="left")

        close_btn = tk.Label(titlebar, text=" × ", bg="#111111", fg="#888888",
                             font=("Helvetica", 11), cursor="hand2")
        close_btn.pack(side="right", padx=2)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>",    lambda e: close_btn.config(fg="#ff6b6b"))
        close_btn.bind("<Leave>",    lambda e: close_btn.config(fg="#888888"))

        for w in (titlebar,):
            w.bind("<ButtonPress-1>",  self._drag_start)
            w.bind("<B1-Motion>",      self._drag_move)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG, padx=14, pady=8)
        body.pack(fill="both", expand=True)

        # Clock emoji
        self.emoji_lbl = tk.Label(body, text="🕐", bg=BG, font=("Segoe UI Emoji", 26))
        self.emoji_lbl.pack()

        # Big countdown display
        self.display_var = tk.StringVar(value="00:00")
        self.display_lbl = tk.Label(body, textvariable=self.display_var,
                                    bg=BG, fg=FG,
                                    font=("Courier New", 30, "bold"))
        self.display_lbl.pack(pady=(2, 6))

        # ── Input row: HH : MM : SS ────────────────────────────────────────
        input_frame = tk.Frame(body, bg=BG)
        input_frame.pack()

        vcmd = (self.root.register(self._validate_num), '%P')

        self.h_var = tk.StringVar(value="0")
        self.m_var = tk.StringVar(value="5")
        self.s_var = tk.StringVar(value="0")

        def make_input(parent, var):
            e = tk.Entry(parent, textvariable=var, width=3,
                         bg=BG_INPUT, fg="#cccccc", insertbackground="#cccccc",
                         relief="flat", bd=0,
                         font=("Courier New", 13),
                         justify="center",
                         validate="key", validatecommand=vcmd,
                         highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=FG_RUNNING)
            e.bind("<FocusIn>",  lambda ev, w=e: w.select_range(0, "end"))
            e.bind("<Return>",   lambda ev: self._start_pause())
            e.bind("<KeyRelease>", lambda ev: self._preview_display())
            return e

        self.h_entry = make_input(input_frame, self.h_var)
        self.m_entry = make_input(input_frame, self.m_var)
        self.s_entry = make_input(input_frame, self.s_var)

        sep_font = tkfont.Font(family="Courier New", size=14, weight="bold")

        self.h_entry.grid(row=0, column=0)
        tk.Label(input_frame, text=":", bg=BG, fg=FG_DIM,
                 font=sep_font).grid(row=0, column=1, padx=1)
        self.m_entry.grid(row=0, column=2)
        tk.Label(input_frame, text=":", bg=BG, fg=FG_DIM,
                 font=sep_font).grid(row=0, column=3, padx=1)
        self.s_entry.grid(row=0, column=4)

        # Labels below inputs
        lbl_frame = tk.Frame(body, bg=BG)
        lbl_frame.pack(pady=(1, 8))
        lbl_font = tkfont.Font(family="Helvetica", size=8)
        for col, txt in enumerate(["hr", "min", "sec"]):
            tk.Label(lbl_frame, text=txt, bg=BG, fg=FG_DIM,
                     font=lbl_font).grid(row=0, column=col*2, padx=8)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill="x")

        self.main_btn = tk.Button(
            btn_frame, text="Start", command=self._start_pause,
            bg=BTN_START, fg="#ffffff", activebackground="#4fa882",
            relief="flat", bd=0, font=("Helvetica", 10, "bold"),
            cursor="hand2", padx=0, pady=5)
        self.main_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        reset_btn = tk.Button(
            btn_frame, text="↺", command=self._reset,
            bg=BTN_RESET, fg="#888888", activebackground="#3a3a3a",
            relief="flat", bd=0, font=("Helvetica", 12),
            cursor="hand2", padx=8, pady=5,
            highlightthickness=1, highlightbackground=BORDER)
        reset_btn.pack(side="right")

        # Status label
        self.status_var = tk.StringVar(value="Set a time above")
        tk.Label(body, textvariable=self.status_var,
                 bg=BG, fg=FG_DIM,
                 font=("Helvetica", 8)).pack(pady=(6, 0))

        # Preview initial display
        self._preview_display()

    # ── Input validation ──────────────────────────────────────────────────────

    def _validate_num(self, val):
        return val == "" or (val.isdigit() and len(val) <= 3)

    def _get_seconds(self):
        h = int(self.h_var.get() or 0)
        m = int(self.m_var.get() or 0)
        s = int(self.s_var.get() or 0)
        return h * 3600 + m * 60 + s

    def _preview_display(self):
        if not self.running and not self.paused:
            secs = self._get_seconds()
            self.display_var.set(self._fmt(secs))

    # ── Timer logic ───────────────────────────────────────────────────────────

    def _start_pause(self):
        if self.paused:
            self.paused  = False
            self.running = True
            self.main_btn.config(text="Pause", bg=BTN_PAUSE,
                                 activebackground="#6a8fb8")
            self.status_var.set("Running…")
            self.display_lbl.config(fg=FG_RUNNING)
            self._tick()
            return

        if self.running:
            self.running = False
            self.paused  = True
            if self._after_id:
                self.root.after_cancel(self._after_id)
            self.main_btn.config(text="Resume", bg=BTN_START,
                                 activebackground="#4fa882")
            self.status_var.set("Paused")
            self.display_lbl.config(fg=FG)
            return

        # Fresh start
        secs = self._get_seconds()
        if secs <= 0:
            self.status_var.set("Enter a time first!")
            return

        self.remaining  = secs
        self.running    = True
        self.paused     = False
        self._emoji_idx = 0
        self.main_btn.config(text="Pause", bg=BTN_PAUSE,
                             activebackground="#6a8fb8")
        self.status_var.set("Running…")
        self.display_lbl.config(fg=FG_RUNNING)
        self.display_var.set(self._fmt(self.remaining))
        self._tick()

    def _tick(self):
        if not self.running:
            return
        if self.remaining <= 0:
            self._finish()
            return
        self.remaining -= 1
        self.display_var.set(self._fmt(self.remaining))
        # Animate emoji
        self._emoji_idx = (self._emoji_idx + 1) % len(CLOCK_EMOJIS)
        self.emoji_lbl.config(text=CLOCK_EMOJIS[self._emoji_idx])
        self._after_id = self.root.after(1000, self._tick)

    def _finish(self):
        self.running = False
        self.paused  = False
        self.display_var.set("00:00")
        self.display_lbl.config(fg=FG_DONE)
        self.emoji_lbl.config(text="⏰")
        self.main_btn.config(text="Start", bg=BTN_START,
                             activebackground="#4fa882")
        self.status_var.set("Time's up!")
        self._play_alarm()
        self._blink()

    def _blink(self):
        if self.running or self.paused:
            return
        if self.display_lbl.cget("fg") == FG_DONE:
            self._blink_on = not self._blink_on
            self.display_lbl.config(fg=FG_DONE if self._blink_on else BG)
            self._after_id = self.root.after(600, self._blink)

    def _reset(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self.running   = False
        self.paused    = False
        self.remaining = 0
        self.emoji_lbl.config(text="🕐")
        self.display_lbl.config(fg=FG)
        self.main_btn.config(text="Start", bg=BTN_START,
                             activebackground="#4fa882")
        self.status_var.set("Set a time above")
        self._preview_display()

    # ── Alarm ─────────────────────────────────────────────────────────────────

    def _play_alarm(self):
        # Three beeps using Windows built-in winsound (no extra files needed)
        def beeps():
            for _ in range(3):
                winsound.Beep(880, 220)
                self.root.after(100)
        self.root.after(0, beeps)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(secs):
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()
