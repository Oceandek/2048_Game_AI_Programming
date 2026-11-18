"""app.py - 2048 Arena als website.

Starten:  python app.py
Er opent vanzelf een tabblad in je browser (http://localhost:8000).

Hoe het werkt
-------------
* Deze Python-code is een kleine webserver (alleen de standaardbibliotheek).
* De spelregels (game.py) en de AI (Algoritme/ai.py) draaien hier in Python.
* De interface staat in de map Web/ (index.html, style.css, app.js).
  De browser stuurt elke zet naar de server (bv. POST /api/move) en krijgt
  het nieuwe bord terug als JSON.
"""

import copy
import json
import random
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from Algoritme.ai import make_ai
from game import DIRECTIONS, add_tile, game_over, move, new_board, valid_moves

WEB = Path(__file__).parent / "Web"
STATIC = {  # bestanden die de browser mag opvragen
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}
DIFFICULTY = {"easy": "Makkelijk", "middel": "Middelmatig", "hard": "Moeilijk"}
TARGETS = (1000, 2500, 5000)

lock = threading.Lock()  # de server beantwoordt verzoeken in meerdere threads
games = {}  # spel-id -> spel (singleplayer of tegen de bot)


class ApiError(Exception):
    """Fout die als nette melding naar de browser gaat."""


# ================================================================ spelers
class Player:
    """Eén bord met score. Elke speler heeft een eigen toevalsgenerator."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.board = new_board()
        add_tile(self.board, self.rng)
        add_tile(self.board, self.rng)
        self.score = 0
        self.history = []  # voor "zet ongedaan maken"

    def step(self, direction):
        """Doet een zet. Geeft False terug als die zet niets verandert."""
        if direction not in valid_moves(self.board):
            return False
        self.history = (self.history + [(copy.deepcopy(self.board), self.score)])[-50:]
        self.board, points = move(self.board, direction)
        self.score += points
        add_tile(self.board, self.rng)
        return True

    def undo(self):
        if self.history:
            self.board, self.score = self.history.pop()

    def stuck(self):
        return game_over(self.board)

    def view(self):
        return {"board": self.board, "score": self.score,
                "highest": max(max(row) for row in self.board), "stuck": self.stuck()}


class Match:
    """Twee spelers die om de beurt een zet doen. Wie eerst de doelscore haalt, wint.
    Zit iemand vast, dan stopt de ronde en wint de hoogste score."""

    def __init__(self, target, first=0):
        seed = random.randrange(1 << 30)  # beide borden starten met dezelfde seed
        self.players = [Player(seed), Player(seed)]
        self.target = target
        self.turn = first
        self.moves = 0
        self.winner = None  # 0, 1 of "draw"
        self.reason = None  # "target" of "stuck"

    def play(self, idx, direction):
        if self.winner is not None or self.turn != idx:
            return False
        if not self.players[idx].step(direction):
            return False
        self.moves += 1
        self._check_end()
        if self.winner is None:
            self.turn = 1 - idx
        return True

    def _check_end(self):
        a, b = self.players
        for i, p in enumerate(self.players):
            if p.score >= self.target:
                self.winner, self.reason = i, "target"
                return
        if a.stuck() or b.stuck():
            self.reason = "stuck"
            self.winner = 0 if a.score > b.score else 1 if b.score > a.score else "draw"

    def view(self, idx):
        """De ronde gezien vanuit speler `idx` ("you" = die speler zelf)."""
        winner = None
        if self.winner == "draw":
            winner = "draw"
        elif self.winner is not None:
            winner = "you" if self.winner == idx else "opp"
        return {"you": self.players[idx].view(), "opp": self.players[1 - idx].view(),
                "turn": "you" if self.turn == idx else "opp", "moves": self.moves,
                "target": self.target, "winner": winner, "reason": self.reason}


# ============================================================ hulpfuncties
def _target(data):
    target = int(data.get("target", 5000))
    if target not in TARGETS:
        raise ApiError("Onbekende doelscore.")
    return target


def _direction(data):
    direction = data.get("dir")
    if direction not in DIRECTIONS:
        raise ApiError("Onbekende richting.")
    return direction


def _game(data):
    game = games.get(data.get("id"))
    if game is None:
        raise ApiError("Dit spel bestaat niet meer. Start een nieuw spel.")
    return game


def _game_state(game):
    if game["kind"] == "single":
        p = game["player"]
        return {"mode": "single", "you": p.view(), "can_undo": bool(p.history),
                "over": p.stuck()}
    return {"mode": "bot", "diff": game["diff"], "delay": game["delay"],
            **game["match"].view(0)}


# ======================================================= API: solo & bot
def api_start(data):
    mode = data.get("mode")
    if mode == "single":
        game = {"kind": "single", "player": Player(random.randrange(1 << 30))}
    elif mode == "bot":
        diff = data.get("diff", "middel")
        if diff not in DIFFICULTY:
            raise ApiError("Onbekende moeilijkheid.")
        ai, delay = make_ai(DIFFICULTY[diff])
        game = {"kind": "bot", "match": Match(_target(data)), "ai": ai,
                "delay": delay, "diff": diff}
    else:
        raise ApiError("Deze modus komt nog.")
    game_id = secrets.token_hex(8)
    with lock:
        if len(games) > 200:  # oude spellen opruimen
            games.pop(next(iter(games)))
        games[game_id] = game
        return {"id": game_id, **_game_state(game)}


def api_move(data):
    direction = _direction(data)
    with lock:
        game = _game(data)
        if game["kind"] == "single":
            game["player"].step(direction)
        else:
            game["match"].play(0, direction)
        return _game_state(game)


def api_bot(data):
    """De bot doet zijn zet (de browser vraagt dit na een korte pauze)."""
    with lock:
        game = _game(data)
        if game["kind"] != "bot":
            raise ApiError("Dit is geen spel tegen de bot.")
        match = game["match"]
        if match.turn != 1 or match.winner is not None:
            return _game_state(game)
        board = copy.deepcopy(match.players[1].board)
    # nadenken buiten de lock: andere verzoeken moeten niet wachten op de AI
    direction = game["ai"].choose_move(board)
    with lock:
        if direction and match.turn == 1 and match.players[1].board == board:
            match.play(1, direction)
        return _game_state(game)


def api_undo(data):
    with lock:
        game = _game(data)
        if game["kind"] != "single":
            raise ApiError("Ongedaan maken kan alleen in singleplayer.")
        game["player"].undo()
        return _game_state(game)


ACTIONS = {
    "/api/start": api_start,
    "/api/move": api_move,
    "/api/bot": api_bot,
    "/api/undo": api_undo,
}


# =============================================================== webserver
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # geen log-regel per verzoek in de terminal
        pass

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, obj):
        self._send(status, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        path = urlparse(self.path).path
        name = "index.html" if path == "/" else path.lstrip("/")
        if name not in STATIC:
            self._send(404, b"Niet gevonden", "text/plain; charset=utf-8")
            return
        self._send(200, (WEB / name).read_bytes(), STATIC[name])

    def do_POST(self):
        action = ACTIONS.get(urlparse(self.path).path)
        if action is None:
            self._json(404, {"error": "Onbekende actie."})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
            self._json(200, action(data))
        except ApiError as e:
            self._json(400, {"error": str(e)})
        except (ValueError, TypeError, KeyError):
            self._json(400, {"error": "Ongeldige aanvraag."})


class Server(ThreadingHTTPServer):
    allow_reuse_address = False  # op Windows anders 2 servers op dezelfde poort
    daemon_threads = True


def main():
    for port in range(8000, 8011):
        try:
            server = Server(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        print("Geen vrije poort gevonden tussen 8000 en 8010.")
        return
    url = f"http://localhost:{port}"
    print("2048 Arena draait!")
    print(f"  Open: {url}")
    print("Stoppen: Ctrl+C")
    threading.Timer(0.5, webbrowser.open, args=[url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGestopt.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
