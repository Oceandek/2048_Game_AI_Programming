"""screen_result.py - scherm 5: einde van de ronde."""

from ui_base import *  # noqa: F401,F403  (kleuren, fmt, W, H, ...)


class ResultScreen:
    def show_result(self, title, subtitle, cards, winner, buttons, tag="EINDE VAN DE RONDE"):
        """cards: lijst van (label, score, hoogste_tegel, kleur). winner: index of None.
        buttons: lijst van (tekst, handler-methode, stijl)."""
        self._clear()
        self._header("")
        self._rr(300, 170, 900, 610, 26, fill=CARD, outline=ORANGE, width=2)
        self._text(600, 214, tag, 13, ORANGE, bold=False, anchor="center")
        self._text(600, 266, title, 40, TEXT, anchor="center")
        self._text(600, 318, subtitle, 15, MUTED, bold=False, anchor="center", width=520)

        cw, ch = 245, 120
        total = len(cards) * cw + (len(cards) - 1) * 20
        x = 600 - total / 2
        for i, (label, score, high, color) in enumerate(cards):
            win = winner == i
            self._rr(x, 356, x + cw, 356 + ch, 18, fill=CARD_DARK, outline=ORANGE if win else LINE,
                     width=2 if win else 1)
            self._text(x + cw / 2, 380, label, 14, "#c5c9d3", bold=False, anchor="center")
            self._text(x + cw / 2, 420, fmt(score), 36, color, anchor="center")
            self._text(x + cw / 2, 458, f"Hoogste tegel {fmt(high)}", 13, MUTED, bold=False, anchor="center")
            x += cw + 20

        widths = [len(t) * 10 + 56 for t, _, _ in buttons]
        bx = 600 - (sum(widths) + 12 * (len(buttons) - 1)) / 2
        for (text, method, style), bw in zip(buttons, widths):
            self._button(bx, 520, bw, 52, text, getattr(self.h, method), style, 16)
            bx += bw + 12
