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
* Tegen een vriend: de server draait op jouw computer. Je vriend opent op
  hetzelfde wifi-netwerk het adres van jouw computer, bv.
  http://192.168.0.24:8000/kamer/4F7K
"""

import copy
import json
import random
import secrets
import socket
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
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # geen 0/O en 1/I: niet te verwarren

PORT = 8000
LAN_IP = "127.0.0.1"

lock = threading.Lock()  # de server beantwoordt verzoeken in meerdere threads
games = {}  # spel-id -> spel (singleplayer of tegen de bot)
rooms = {}  # kamercode -> kamer (tegen een vriend)


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


def _room(data):
    """Zoekt de kamer en welke speler (0 = host, 1 = gast) dit verzoek stuurt."""
    room = rooms.get(str(data.get("code", "")).strip().upper())
    if room is None:
        raise ApiError("Kamer niet gevonden. Controleer de code.")
    token = data.get("token")
    if not token or token not in room["tokens"]:
        raise ApiError("Je zit niet in deze kamer.")
    return room, room["tokens"].index(token)


def _room_state(room, idx):
    return {"code": room["code"], "role": "host" if idx == 0 else "guest",
            "connected": room["tokens"][1] is not None, "target": room["target"],
            "round": room["round"],
            "match": room["match"].view(idx) if room["match"] else None}


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
        raise ApiError("Onbekende modus.")
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


# ===================================================== API: tegen vriend
def api_room_create(data):
    target = _target(data)
    with lock:
        while True:
            code = "".join(random.choice(CODE_CHARS) for _ in range(4))
            if code not in rooms:
                break
        token = secrets.token_hex(8)
        rooms[code] = {"code": code, "tokens": [token, None], "target": target,
                       "match": None, "round": 0}
    return {"code": code, "token": token, "address": f"http://{LAN_IP}:{PORT}/kamer/{code}"}


def api_room_join(data):
    # ook een volledige link plakken mag: we nemen het laatste stuk
    code = str(data.get("code", "")).strip().rstrip("/").split("/")[-1].upper()
    with lock:
        room = rooms.get(code)
        if room is None:
            raise ApiError("Kamer niet gevonden. Controleer de code.")
        if room["tokens"][1] is not None:
            raise ApiError("Deze kamer is al vol.")
        token = secrets.token_hex(8)
        room["tokens"][1] = token
        return {"code": code, "token": token}


def api_room_state(data):
    with lock:
        room, idx = _room(data)
        return _room_state(room, idx)


def api_room_target(data):
    target = _target(data)
    with lock:
        room, idx = _room(data)
        if idx != 0:
            raise ApiError("Alleen de host kiest de doelscore.")
        room["target"] = target
        return _room_state(room, idx)


def api_room_start(data):
    with lock:
        room, idx = _room(data)
        if room["tokens"][1] is None:
            raise ApiError("Wacht tot je vriend erbij is.")
        room["round"] += 1
        # om de beurt mag de host of de gast de eerste zet doen
        room["match"] = Match(room["target"], first=(room["round"] + 1) % 2)
        return _room_state(room, idx)


def api_room_move(data):
    direction = _direction(data)
    with lock:
        room, idx = _room(data)
        if room["match"] is None:
            raise ApiError("Het spel is nog niet gestart.")
        room["match"].play(idx, direction)
        return room["match"].view(idx)


def api_room_leave(data):
    with lock:
        try:
            room, idx = _room(data)
        except ApiError:
            return {}
        if idx == 0:  # host weg = kamer dicht
            rooms.pop(room["code"], None)
        else:
            room["tokens"][1] = None
            room["match"] = None
        return {}


ACTIONS = {
    "/api/start": api_start,
    "/api/move": api_move,
    "/api/bot": api_bot,
    "/api/undo": api_undo,
    "/api/room/create": api_room_create,
    "/api/room/join": api_room_join,
    "/api/room/state": api_room_state,
    "/api/room/target": api_room_target,
    "/api/room/start": api_room_start,
    "/api/room/move": api_room_move,
    "/api/room/leave": api_room_leave,
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
        name = "index.html" if path == "/" or path.startswith("/kamer/") else path.lstrip("/")
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


def lan_ip():
    """IP-adres van deze computer in het lokale netwerk (voor de kamerlink).
    Een UDP-socket 'verbinden' verstuurt niets, maar kiest wel de juiste netwerkkaart."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    global PORT, LAN_IP
    LAN_IP = lan_ip()
    for port in range(8000, 8011):
        try:
            server = Server(("0.0.0.0", port), Handler)  # 0.0.0.0 = ook bereikbaar via wifi
            break
        except OSError:
            continue
    else:
        print("Geen vrije poort gevonden tussen 8000 en 8010.")
        return
    PORT = port
    url = f"http://localhost:{port}"
    print("2048 Arena draait!")
    print(f"  Op deze computer : {url}")
    print(f"  Voor je vriend   : http://{LAN_IP}:{port}  (zelfde wifi)")
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
