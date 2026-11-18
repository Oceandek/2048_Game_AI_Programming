"""screen_start.py - scherm 1: startscherm (modus, moeilijkheid, doelscore kiezen)."""

from ui_base import *  # noqa: F401,F403  (kleuren, fmt, W, H, ...)


class StartScreen:
    def show_menu(self):
        self._clear()
        self._header("Schuif tegels, combineer, haal als eerste 2048")
        self._text(130, 118, "Hoe wil je spelen?", 40, TEXT)
        self._text(130, 170, "Kies een modus. Alles draait lokaal op je computer.", 16, MUTED, bold=False)

        cards = (
            ("single", "ALLEEN", "Singleplayer",
             "Speel alleen en probeer de 2048-tegel te halen. Je score wordt bijgehouden."),
            ("bot", "TEGEN DE COMPUTER", "Tegen de bot",
             "Jij links, de bot rechts. Om de beurt een zet. Wie als eerste de doelscore haalt, wint."),
            ("friend", "MET EEN ANDER", "Tegen een vriend",
             "Maak een kamer en deel de code. Jullie spelen om de beurt op je eigen toestel."),
        )
        x = 130
        for key, tag, title, desc in cards:
            selected = self.sel_mode == key
            self._rr(x, 229, x + 300, 415, 22, fill=CARD, outline=ORANGE if selected else LINE,
                     width=2 if selected else 1)
            self._text(x + 28, 252, "GESELECTEERD" if selected else tag, 12,
                       ORANGE if selected else MUTED, bold=False)
            self._text(x + 28, 277, title, 24, TEXT)
            self._text(x + 28, 322, desc, 14, "#c5c9d3", bold=False, width=246)
            self._region(x, 229, x + 300, 415, lambda k=key: self._pick_mode(k))
            x += 320

        if self.sel_mode == "bot":
            self._text(130, 452, "MOEILIJKHEID VAN DE BOT", 12, MUTED, bold=False)
            self._segment(130, 477, DIFF_LABELS, self.sel_diff, self._pick_diff, "#f4f5f7", BG, h=54)
            self._text(130, 546, DIFF_HELP[self.sel_diff], 14, MUTED, bold=False)
        if self.sel_mode in ("bot", "friend"):
            self._text(427, 452, "DOELSCORE", 12, MUTED, bold=False)
            items = [(t, fmt(t)) for t in TARGETS]
            self._segment(427, 477, items, self.sel_target, self._pick_target, "#f4f5f7", BG, h=54)
            self._text(427, 546, "Wie dit als eerste haalt, wint.", 14, MUTED, bold=False)

        self._button(130, 594, 142, 48, "Start spel", lambda: self.h.on_start(
            self.sel_mode, self.sel_diff, self.sel_target), "primary", 17)

    def _pick_mode(self, key):
        self.sel_mode = key
        self.show_menu()

    def _pick_diff(self, key):
        self.sel_diff = key
        self.show_menu()

    def _pick_target(self, key):
        self.sel_target = key
        self.show_menu()
