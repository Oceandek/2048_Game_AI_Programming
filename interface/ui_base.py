"""ui_base.py - gedeelde basis van de interface: kleuren, tekenhulpjes, klikken, toetsen.

Elk scherm staat in een eigen bestand (screen_*.py) en gebruikt de hulpfuncties hieruit.
"""

import tkinter as tk
from tkinter import font as tkfont

W, H = 1200, 760

# kleuren (uit het ontwerp)
BG = "#0e1015"
CARD = "#1a1d26"
CARD_DARK = "#14161d"
LINE = "#2a2e3a"
TEXT = "#f4f5f7"
MUTED = "#9aa0ad"
ORANGE = "#f59e0b"
BLUE = "#60a5fa"
GREEN = "#6ee7b7"
RED = "#f87171"
DARK_TEXT = "#1a1208"

TILE_COLORS = {          # waarde: (achtergrond, tekst)
    0: ("#20232c", "#20232c"),
    2: ("#272a36", "#e5e7eb"),
    4: ("#3a3d4c", "#e5e7eb"),
    8: ("#ffb877", DARK_TEXT),
    16: ("#ff9d42", DARK_TEXT),
    32: ("#ff7a14", DARK_TEXT),
    64: ("#c4400d", "#ffffff"),
    128: ("#fde68a", DARK_TEXT),
    256: ("#fbbf24", DARK_TEXT),
    512: ("#f59e0b", DARK_TEXT),
    1024: ("#d97706", "#ffffff"),
    2048: ("#b45309", "#ffffff"),
}
TILE_DEFAULT = ("#7c2d12", "#ffffff")

MODE_LABELS = (("single", "Singleplayer"), ("bot", "Tegen bot"), ("friend", "Tegen vriend"))
DIFF_LABELS = (("easy", "Easy"), ("middel", "Middel"), ("hard", "Hard"))
DIFF_HELP = {
    "easy": "Easy: de bot kijkt één zet vooruit en maakt soms een foutje.",
    "middel": "Middel: de bot kijkt twee zetten vooruit.",
    "hard": "Hard: de bot kijkt drie zetten vooruit.",
}
TARGETS = (1000, 2500, 5000)
PLACEHOLDER = "bijv. 4F7K"


def fmt(n):
    """3412 -> '3 412'"""
    return f"{int(n):,}".replace(",", " ")


class UIBase:
    def __init__(self, root, handler):
        self.root = root
        self.h = handler
        self.regions = []              # klikbare gebieden: (x0, y0, x1, y1, functie)

        # keuzes op het startscherm
        self.sel_mode = "bot"
        self.sel_diff = "middel"
        self.sel_target = 5000

        root.title("2048 Arena")
        root.geometry(f"{W}x{H}")
        root.resizable(False, False)
        root.configure(bg=BG)

        families = set(tkfont.families())
        self.family = next((f for f in ("Inter", "Segoe UI", "SF Pro Display", "Helvetica Neue",
                                        "Helvetica", "DejaVu Sans") if f in families), "TkDefaultFont")

        self.canvas = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._hover)
        root.bind("<Key>", self._key)

        # invoerveld voor de kamercode (blijft bestaan tussen hertekeningen)
        self.entry = tk.Entry(root, font=(self.family, -20, "bold"), bg=CARD_DARK, fg=MUTED,
                              insertbackground=TEXT, relief="flat", highlightthickness=1,
                              highlightbackground=LINE, highlightcolor=ORANGE, bd=8)
        self.entry.insert(0, PLACEHOLDER)
        self.entry.bind("<FocusIn>", self._entry_focus_in)
        self.entry.bind("<FocusOut>", self._entry_focus_out)

    # ======================================================== hulpfuncties

    def _f(self, px, bold=True):
        return (self.family, -px, "bold" if bold else "normal")

    def _clear(self):
        self.canvas.delete("all")
        self.regions = []
        self.canvas.focus_set()

    def _rr(self, x0, y0, x1, y1, r=14, fill="", outline="", width=1, dash=None):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
               x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.canvas.create_polygon(pts, smooth=True, fill=fill, outline=outline,
                                          width=width, dash=dash)

    def _text(self, x, y, text, size=14, color=TEXT, bold=True, anchor="nw", width=None):
        return self.canvas.create_text(x, y, text=text, fill=color, font=self._f(size, bold),
                                       anchor=anchor, width=width)

    def _region(self, x0, y0, x1, y1, fn):
        self.regions.append((x0, y0, x1, y1, fn))

    def _click(self, e):
        self.canvas.focus_set()
        for x0, y0, x1, y1, fn in reversed(self.regions):
            if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                fn()
                return

    def _hover(self, e):
        over = any(x0 <= e.x <= x1 and y0 <= e.y <= y1 for x0, y0, x1, y1, _ in self.regions)
        self.canvas.config(cursor="hand2" if over else "")

    def _button(self, x, y, w, h, text, fn, style="primary", size=16):
        styles = {
            "primary": (ORANGE, "", DARK_TEXT),
            "light": ("#f4f5f7", "", BG),
            "blue": (BLUE, "", DARK_TEXT),
            "ghost": (BG, LINE, TEXT),
            "ghost_card": (CARD, "#3a3d4c", TEXT),
            "disabled": ("#3a3d4c", "", MUTED),
        }
        fill, outline, color = styles[style]
        self._rr(x, y, x + w, y + h, 12, fill=fill, outline=outline, width=1)
        self._text(x + w / 2, y + h / 2, text, size, color, anchor="center")
        if style != "disabled":
            self._region(x, y, x + w, y + h, fn)

    def _segment(self, x, y, items, selected, on_pick, sel_fill, sel_text, h=48, size=15):
        """Keuzebalk (zoals Easy | Middel | Hard). Geeft de breedte terug."""
        widths = [len(label) * 9 + 40 for _, label in items]
        total = sum(widths) + 12
        self._rr(x, y, x + total, y + h, 14, fill=CARD, outline=LINE)
        cx = x + 6
        for (key, label), bw in zip(items, widths):
            if key == selected:
                self._rr(cx, y + 6, cx + bw, y + h - 6, 10, fill=sel_fill)
                self._text(cx + bw / 2, y + h / 2, label, size, sel_text, anchor="center")
            else:
                self._text(cx + bw / 2, y + h / 2, label, size, "#c5c9d3", bold=False, anchor="center")
                self._region(cx, y + 6, cx + bw, y + h - 6, lambda k=key: on_pick(k))
            cx += bw
        return total

    def _header(self, subtitle, mode=None, difficulty=None):
        """Logo + titel links, optioneel de modus-tabs (en bot-niveau) rechts."""
        self._rr(45, 32, 90, 77, 12, fill=ORANGE)
        self._text(67, 55, "2048", 14, DARK_TEXT, anchor="center")
        self._text(103, 31, "2048 Arena", 24, TEXT)
        if subtitle:
            self._text(103, 62, subtitle, 13, MUTED, bold=False)
        if mode is None:
            return
        tabs_w = sum(len(l) * 9 + 40 for _, l in MODE_LABELS) + 12
        x = W - 45 - tabs_w
        self._segment(x, 28, MODE_LABELS, mode, self.h.on_switch_mode, ORANGE, DARK_TEXT, h=54)
        if difficulty is not None:
            diff_w = sum(len(l) * 9 + 40 for _, l in DIFF_LABELS) + 12
            self._segment(x - 22 - diff_w, 28, DIFF_LABELS, difficulty, self.h.on_set_difficulty,
                          "#f4f5f7", BG, h=54)

    def _draw_board(self, x, y, board, tile, gap, outline):
        size = 4 * tile + 5 * gap
        self._rr(x, y, x + size, y + size, 22, fill=CARD_DARK, outline=outline, width=2)
        for r in range(4):
            for c in range(4):
                v = board[r][c]
                bg, fg = TILE_COLORS.get(v, TILE_DEFAULT)
                tx = x + gap + c * (tile + gap)
                ty = y + gap + r * (tile + gap)
                self._rr(tx, ty, tx + tile, ty + tile, 12, fill=bg)
                if v:
                    digits = len(str(v))
                    factor = {1: 0.40, 2: 0.40, 3: 0.34, 4: 0.28}.get(digits, 0.22)
                    self._text(tx + tile / 2, ty + tile / 2, str(v), int(tile * factor), fg,
                               anchor="center")
        return size

    def _stat_card(self, x, y, w, h, label, value, value_color=TEXT, value_size=28):
        self._rr(x, y, x + w, y + h, 16, fill=CARD, outline=LINE)
        self._text(x + 18, y + 14, label, 11, MUTED, bold=False, width=w - 30)
        self._text(x + 18, y + h - 16, value, value_size, value_color, anchor="sw")

    # ======================================================= toetsen / invoer

    def _key(self, e):
        if self.root.focus_get() is self.entry:
            if e.keysym in ("Return", "KP_Enter"):
                self.h.on_join_room(self.get_join_text())
            return
        direction = {"Left": "left", "Right": "right", "Up": "up", "Down": "down"}.get(e.keysym)
        if direction is None and e.char:
            direction = {"a": "left", "d": "right", "w": "up", "s": "down"}.get(e.char.lower())
        if direction:
            self.h.on_key(direction)

    def _entry_focus_in(self, _):
        if str(self.entry.cget("fg")) == MUTED:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT)

    def _entry_focus_out(self, _):
        if not self.entry.get().strip():
            self.entry.delete(0, "end")
            self.entry.insert(0, PLACEHOLDER)
            self.entry.config(fg=MUTED)

    def get_join_text(self):
        return "" if str(self.entry.cget("fg")) == MUTED else self.entry.get().strip()

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
