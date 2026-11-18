"""app.py - 2048 Arena als website.

Starten:  python app.py
Er opent vanzelf een tabblad in je browser (http://localhost:8000).

Hoe het werkt
-------------
* Deze Python-code is een kleine webserver (alleen de standaardbibliotheek).
* De spelregels (game.py) draaien hier in Python.
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

from game import DIRECTIONS, add_tile, game_over, move, new_board, valid_moves

WEB = Path(__file__).parent / "Web"
STATIC = {  # bestanden die de browser mag opvragen
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}

lock = threading.Lock()  # de server beantwoordt verzoeken in meerdere threads
games = {}  # spel-id -> spel


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


# ============================================================ hulpfuncties
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
    p = game["player"]
    return {"mode": "single", "you": p.view(), "can_undo": bool(p.history),
            "over": p.stuck()}


# ============================================================= API: solo
def api_start(data):
    if data.get("mode") != "single":
        raise ApiError("Deze modus komt nog.")
    game = {"kind": "single", "player": Player(random.randrange(1 << 30))}
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
        game["player"].step(direction)
        return _game_state(game)


def api_undo(data):
    with lock:
        game = _game(data)
        game["player"].undo()
        return _game_state(game)


ACTIONS = {
    "/api/start": api_start,
    "/api/move": api_move,
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
