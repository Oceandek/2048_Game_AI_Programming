"""screen_versus.py - scherm 3: tegen de bot (en het spel tegen een vriend): twee borden."""

from ui_base import *  # noqa: F401,F403  (kleuren, fmt, W, H, ...)


class VersusScreen:
    def show_versus(self, mode, difficulty, you, opp, target, turn, move_nr,
                    opp_name, opp_tag, footer=""):
        """you / opp = (bord, score, hoogste_tegel). turn = 'you' of 'opp'."""
        self._clear()
        self._header("Schuif tegels, combineer, haal als eerste de doelscore", mode=mode,
                     difficulty=difficulty if mode == "bot" else None)

        tile, gap = 84, 10
        size = 4 * tile + 5 * gap
        lx, rx = 58, W - 58 - size
        for x, name, tag, data, color in ((lx, "Jij", "W A S D", you, ORANGE),
                                          (rx, opp_name, opp_tag, opp, BLUE)):
            self.canvas.create_oval(x + 4, 146, x + 16, 158, fill=color, outline="")
            self._text(x + 30, 138, name, 22, TEXT)
            tw = len(tag) * 9 + 28
            self._rr(x + size - tw, 138, x + size, 166, 8, fill=BG, outline="#3a3d4c")
            self._text(x + size - tw / 2, 152, tag, 12, MUTED, bold=False, anchor="center")
            board, score, high = data
            half = (size - 12) / 2
            self._stat_card(x, 180, half, 74, "SCORE", fmt(score), color, 26)
            self._stat_card(x + half + 12, 180, half, 74, "HOOGSTE TEGEL", fmt(high), TEXT, 26)
            self._draw_board(x, 268, board, tile, gap, color)

        # midden
        cx = W / 2
        self._text(cx, 225, "VS", 52, "#3a3d4c", anchor="center")
        your_turn = turn == "you"
        pill = ORANGE if your_turn else BLUE
        self._rr(cx - 90, 268, cx + 90, 308, 20, fill="#2a1f0b" if your_turn else "#0f1e33",
                 outline=pill, width=1)
        self.canvas.create_oval(cx - 66, 282, cx - 54, 294, fill=pill, outline="")
        self._text(cx + 6, 288, "Jouw beurt" if your_turn else f"Beurt van {opp_name.lower()}", 16,
                   pill, anchor="center")

        self._rr(cx - 115, 326, cx + 115, 486, 18, fill=CARD, outline=LINE)
        self._text(cx, 346, "EERSTE NAAR", 11, MUTED, bold=False, anchor="center")
        self._text(cx, 378, fmt(target), 32, TEXT, anchor="center")
        for i, (name, score, color) in enumerate((("Jij", you[1], ORANGE), (opp_name, opp[1], BLUE))):
            y = 408 + i * 42
            pct = min(100, int(score * 100 / target))
            self._text(cx - 95, y, name, 13, "#c5c9d3", bold=False)
            self._text(cx + 95, y, f"{pct}%", 13, "#c5c9d3", bold=False, anchor="ne")
            self._rr(cx - 95, y + 22, cx + 95, y + 28, 3, fill="#262a35")
            if pct > 0:
                self._rr(cx - 95, y + 22, cx - 95 + 190 * pct / 100, y + 28, 3, fill=color)

        self._text(cx, 508, f"Zet {move_nr}", 14, MUTED, bold=False, anchor="center")
        self._button(cx - 65, 532, 130, 42, "Nieuw spel", self.h.on_new_game, "light", 15)
        if footer:
            self._text(rx + size, 672, footer, 14, MUTED, bold=False, anchor="ne")
