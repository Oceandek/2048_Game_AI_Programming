
import random
import time

from game import DIRECTIONS, move, valid_moves


class _Timeout(Exception):
    """Wordt opgegooid als een diepere zoektocht over het tijdsbudget gaat."""


#interne bordvorm
def _to_ranks(board):
    """Bord uit game.py (4 lijsten met 0, 2, 4, 8, ...) -> tuple van 16 rangen."""
    return tuple(v.bit_length() - 1 if v else 0 for row in board for v in row)


# Voor elke richting: de indexen van de 4 lijnen, telkens in de volgorde
# waarin de tegels naar voren schuiven.
_LINES = {
    "left": [(r * 4, r * 4 + 1, r * 4 + 2, r * 4 + 3) for r in range(4)],
    "right": [(r * 4 + 3, r * 4 + 2, r * 4 + 1, r * 4) for r in range(4)],
    "up": [(c, c + 4, c + 8, c + 12) for c in range(4)],
    "down": [(c + 12, c + 8, c + 4, c) for c in range(4)],
}

_slide_cache = {}


def _slide(row):
    """Schuift een lijn van 4 rangen naar voren en voegt gelijke tegels samen
    (zelfde regels als game.merge_row). Resultaat wordt onthouden."""
    res = _slide_cache.get(row)
    if res is not None:
        return res
    tiles = [v for v in row if v]
    out = []
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            out.append(tiles[i] + 1)  # rang + 1 = waarde x 2
            i += 2
        else:
            out.append(tiles[i])
            i += 1
    res = tuple(out + [0] * (4 - len(out)))
    _slide_cache[row] = res
    return res


def _move(b, direction):
    """Snelle zet op de interne bordvorm. Geeft (nieuw_bord, verschoven?)."""
    nb = list(b)
    for i0, i1, i2, i3 in _LINES[direction]:
        nb[i0], nb[i1], nb[i2], nb[i3] = _slide((b[i0], b[i1], b[i2], b[i3]))
    nb = tuple(nb)
    return nb, nb != b


# heuristiek
LOST_PENALTY = 200000.0
MONO_POWER = 4.0
MONO_WEIGHT = 47.0
SUM_POWER = 3.5
SUM_WEIGHT = 11.0
MERGE_WEIGHT = 700.0
EMPTY_WEIGHT = 270.0

_heur_cache = {}


def _row_heuristic(row):
    h = _heur_cache.get(row)
    if h is not None:
        return h
    total = empty = merges = 0
    prev = counter = 0
    for rank in row:
        total += rank ** SUM_POWER
        if rank == 0:
            empty += 1
        else:
            if prev == rank:
                counter += 1
            elif counter > 0:
                merges += 1 + counter
                counter = 0
            prev = rank
    if counter > 0:
        merges += 1 + counter

    mono_left = mono_right = 0.0
    for i in range(1, 4):
        a, b = row[i - 1], row[i]
        if a > b:
            mono_left += a ** MONO_POWER - b ** MONO_POWER
        else:
            mono_right += b ** MONO_POWER - a ** MONO_POWER

    h = (LOST_PENALTY + EMPTY_WEIGHT * empty + MERGE_WEIGHT * merges
         - MONO_WEIGHT * min(mono_left, mono_right) - SUM_WEIGHT * total)
    _heur_cache[row] = h
    return h


def _evaluate(b):
    """Hoe goed is dit (interne) bord? Hoger = beter."""
    s = 0.0
    for r in range(4):
        s += _row_heuristic(b[r * 4:r * 4 + 4])
    for c in range(4):
        s += _row_heuristic(b[c::4])
    return s


def evaluate(board):
    """Heuristische waarde van een bord uit game.py. Hoger = beter."""
    return _evaluate(_to_ranks(board))


# AI-spelers
class AIPlayer:
    """Basisklasse: `mistake_rate` = kans dat de AI een willekeurige zet doet."""

    name = "AI"

    def __init__(self, mistake_rate=0.0, seed=None):
        self.mistake_rate = mistake_rate
        self.rng = random.Random(seed)

    def choose_move(self, board):
        """Krijgt het bord uit game.py en geeft een richting terug
        ("left", "right", "up" of "down"), of None als er geen zet meer is.
        Het bord zelf wordt niet aangepast."""
        moves = valid_moves(board)
        if not moves:
            return None
        if self.rng.random() < self.mistake_rate:
            return self.rng.choice(moves)
        return self.best_move(board, moves)

    def best_move(self, board, moves):
        raise NotImplementedError


class GreedyAI(AIPlayer):
    """Makkelijk: kijkt maar één zet vooruit en wil alleen direct punten."""

    name = "Makkelijk"

    def best_move(self, board, moves):
        points = {d: move(board, d)[1] for d in moves}
        best_score = max(points.values())
        best = [d for d in moves if points[d] == best_score]
        return self.rng.choice(best)


class ExpectimaxAI(AIPlayer):
    """Expectimax-zoekalgoritme.

    depth       : aantal kans-lagen (tegel-plaatsingen) dat vooruit gekeken wordt
    adaptive    : diepte verhogen als het bord ingewikkelder wordt
    """

    name = "Expectimax"
    MIN_PROB = 1e-4  # takken die zeer onwaarschijnlijk zijn, niet verder zoeken

    def __init__(self, depth=2, adaptive=False, max_depth=3, time_budget=0.5,
                 **kw):
        super().__init__(**kw)
        self.depth = depth
        self.adaptive = adaptive
        self.max_depth = max_depth
        self.time_budget = time_budget  # seconden voor de extra diepere zoektocht
        self._tt = {}
        self._deadline = None
        self._nodes = 0

    def _depth_for(self, b):
        if not self.adaptive:
            return self.depth
        # Weinig lege cellen = weinig takken (snel) én gevaarlijk (diep
        # zoeken loont). Veel lege cellen = veel takken (traag) en veilig.
        if b.count(0) <= 3:
            return self.max_depth
        return self.depth

    def best_move(self, board, moves):
        """Iterative deepening: eerst diepte `self.depth`, daarna (indien
        adaptief) dieper zolang het binnen het tijdsbudget lukt."""
        b = _to_ranks(board)
        target = self._depth_for(b)
        best = self._search(b, moves, self.depth, deadline=None)
        for depth in range(self.depth + 1, target + 1):
            try:
                best = self._search(b, moves, depth,
                                    deadline=time.perf_counter() + self.time_budget)
            except _Timeout:
                break  # te traag -> hou het resultaat van de vorige diepte
        return best

    def _search(self, b, moves, depth, deadline):
        self._tt = {}  # transpositietabel: hetzelfde bord niet 2x berekenen
        self._deadline = deadline
        self._nodes = 0
        best, best_val = moves[0], float("-inf")
        for d in moves:
            nb, _ = _move(b, d)
            v = self._chance(nb, depth, 1.0)
            if v > best_val:
                best, best_val = d, v
        return best

    def _chance(self, b, depth, prob):
        """KANS-knoop: verwachtingswaarde over alle mogelijke nieuwe tegels."""
        if depth <= 0 or prob < self.MIN_PROB:
            return _evaluate(b)
        self._nodes += 1
        if (self._deadline is not None and self._nodes % 256 == 0
                and time.perf_counter() > self._deadline):
            raise _Timeout
        key = (b, depth)
        cached = self._tt.get(key)
        if cached is not None:
            return cached

        empties = [i for i in range(16) if b[i] == 0]
        n = len(empties)
        total = 0.0
        for i in empties:
            for rank, p in ((1, 0.9), (2, 0.1)):  # tegel 2 (90%) of 4 (10%)
                nb = b[:i] + (rank,) + b[i + 1:]
                total += p * self._max(nb, depth - 1, prob * p / n)
        result = total / n
        self._tt[key] = result
        return result

    def _max(self, b, depth, prob):
        """MAX-knoop: de beste zet voor de AI."""
        best = 0.0  # geen zetten meer = verloren = slechtste waarde
        for d in DIRECTIONS:
            nb, moved = _move(b, d)
            if moved:
                v = self._chance(nb, depth, prob)
                if v > best:
                    best = v
        return best


# moeilijkheidsgraden
DIFFICULTIES = {
    # naam: (fabriek voor de AI, wachttijd tussen zetten in ms)
    "Makkelijk": (lambda: GreedyAI(mistake_rate=0.30), 700),
    "Middelmatig": (lambda: ExpectimaxAI(depth=1, mistake_rate=0.05), 400),
    "Moeilijk": (lambda: ExpectimaxAI(depth=2, adaptive=True, max_depth=3), 180),
}


def make_ai(difficulty):
    """Geeft (ai, wachttijd_in_ms) terug voor "Makkelijk", "Middelmatig"
    of "Moeilijk"."""
    factory, delay_ms = DIFFICULTIES[difficulty]
    ai = factory()
    ai.name = difficulty
    return ai, delay_ms
