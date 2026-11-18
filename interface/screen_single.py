"""screen_single.py - scherm 2: singleplayer."""

from ui_base import *  # noqa: F401,F403  (kleuren, fmt, W, H, ...)


class SingleScreen:
    def show_single(self, board, score, best, highest, can_undo):
        self._clear()
        self._header("Schuif tegels, combineer, haal als eerste 2048", mode="single")
        self._draw_board(203, 137, board, 102, 12, ORANGE)

        x, w = 717, 282
        self._rr(x, 137, x + w, 231, 18, fill=CARD, outline=LINE)
        self._text(x + 20, 152, "SCORE", 12, MUTED, bold=False)
        self._text(x + 20, 172, fmt(score), 38, ORANGE)
        self._stat_card(x, 245, 134, 96, "BESTE", fmt(best))
        self._stat_card(x + 148, 245, 134, 96, "HOOGSTE TEGEL", fmt(highest))
        self._button(x, 355, w, 46, "Nieuw spel", self.h.on_new_game, "light", 16)
        self._button(x, 414, w, 46, "Zet ongedaan maken", self.h.on_undo,
                     "ghost" if can_undo else "disabled", 16)
        self._text(x, 490, "Bediening: pijltjestoetsen of W, A, S, D.", 13, MUTED, bold=False)
