"""screen_friend.py - scherm 4: tegen een vriend, kamer maken of meedoen."""

from ui_base import *  # noqa: F401,F403  (kleuren, fmt, W, H, ...)


class FriendScreen:
    def show_friend_lobby(self, lobby):
        """lobby = dict met: role ('host'/'guest'), code, address, connected,
        target, error, status."""
        self._clear()
        self._header("Schuif tegels, combineer, haal als eerste de doelscore", mode="friend")
        role = lobby.get("role", "host")

        if role == "guest":
            self._text(130, 118, "Speel tegen een vriend", 40, TEXT)
            self._rr(130, 200, 770, 400, 22, fill=CARD, outline=BLUE, width=2)
            self._text(160, 228, lobby.get("status", "Verbinden..."), 24, TEXT, width=580)
            self._text(160, 300, "De host kiest de doelscore en start het spel.", 15, MUTED,
                       bold=False, width=580)
            self._button(160, 336, 160, 46, "Annuleren", self.h.on_cancel_join, "ghost_card", 15)
            return

        self._text(130, 118, "Speel tegen een vriend", 40, TEXT)
        self._text(130, 170, "Jullie spelen om de beurt, elk op een eigen toestel in hetzelfde netwerk.",
                   16, MUTED, bold=False)

        # --- linker kaart: kamer maken
        self._rr(130, 216, 590, 726, 24, fill=CARD, outline=ORANGE, width=2)
        self._text(160, 236, "Maak een kamer", 24, TEXT)
        self._text(160, 286, "KAMERCODE", 12, MUTED, bold=False)
        self._rr(160, 308, 330, 376, 14, fill=CARD_DARK, outline=LINE)
        self._text(245, 342, " ".join(lobby.get("code", "----")), 38, "#fbbf24", anchor="center")
        self._button(344, 322, 124, 40, "Kopieer code",
                     lambda: self.copy_to_clipboard(lobby.get("code", "")), "ghost_card", 14)
        self._text(160, 398, "OF DEEL HET ADRES", 12, MUTED, bold=False)
        self._rr(160, 420, 560, 462, 12, fill=CARD_DARK, outline=LINE)
        address = f"{lobby.get('address', '')}/{lobby.get('code', '')}"
        self._text(176, 441, address, 15, "#c5c9d3", bold=False, anchor="w")
        self._region(160, 420, 560, 462, lambda: self.copy_to_clipboard(address))

        self._rr(160, 482, 560, 522, 12, fill=CARD_DARK)
        self.canvas.create_oval(172, 496, 184, 508, fill=ORANGE, outline="")
        self._text(196, 502, "Speler 1 (jij)", 16, TEXT, anchor="w")
        self._text(548, 502, "Klaar", 14, GREEN, bold=False, anchor="e")
        connected = lobby.get("connected", False)
        self._rr(160, 534, 560, 574, 12, fill=CARD_DARK if connected else CARD, outline="" if connected
                 else "#3a3d4c", dash=None if connected else (4, 4))
        self.canvas.create_oval(172, 548, 184, 560, fill=BLUE, outline="")
        self._text(196, 554, "Speler 2 (vriend)" if connected else "Speler 2", 16,
                   TEXT if connected else MUTED, bold=connected, anchor="w")
        self._text(548, 554, "Klaar" if connected else "Wacht op vriend...", 14,
                   GREEN if connected else MUTED, bold=False, anchor="e")

        self._text(160, 592, "DOELSCORE", 12, MUTED, bold=False)
        self._segment(160, 612, [(t, fmt(t)) for t in TARGETS], lobby.get("target", 5000),
                      self.h.on_set_target, "#f4f5f7", BG, h=46, size=14)
        if connected:
            self._button(160, 668, 400, 46, "Start spel", self.h.on_start_friend, "primary", 16)
        else:
            self._button(160, 668, 400, 46, "Start zodra je vriend erbij is", None, "disabled", 16)

        # --- rechter kaart: meedoen
        self._rr(610, 216, 1070, 520, 24, fill=CARD, outline=LINE)
        self._text(640, 236, "Doe mee aan een kamer", 24, TEXT)
        self._text(640, 286, "KAMERCODE VAN JE VRIEND", 12, MUTED, bold=False)
        self.canvas.create_window(640, 308, window=self.entry, anchor="nw", width=400, height=48)
        self._button(640, 372, 400, 48, "Verbinden",
                     lambda: self.h.on_join_room(self.get_join_text()), "blue", 16)
        self._text(640, 436, "Zelfde wifi nodig. Werkt de code niet, vraag je vriend dan om zijn "
                   "adres en plak dat hier, zoals bij 'Of deel het adres'.", 13, MUTED, bold=False, width=400)
        if lobby.get("error"):
            self._text(640, 490, lobby["error"], 13, RED, bold=False, width=400)
