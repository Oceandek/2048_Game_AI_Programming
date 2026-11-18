"""game.py - de spelregels van 2048 (geen scherm, geen AI).

Het bord is een 4x4-lijst (lijst van 4 rijen). 0 betekent een leeg vak.

Belangrijk voor de AI (Brent):
    move(board, richting) schuift en voegt tegels samen, maar zet GEEN nieuwe
    tegel neer. Zo kan Expectimax zelf het toeval (kansknopen) uitrekenen.
    Het echte spel roept na een geldige zet add_random_tile() aan.
"""

import random
from functools import lru_cache

SIZE = 4
DIRECTIONS = ("left", "right", "up", "down")


# ---------------------------------------------------------------- bord maken

def empty_board():
    return [[0] * SIZE for _ in range(SIZE)]


def copy_board(board):
    return [row[:] for row in board]


def empty_cells(board):
    """Lijst van (rij, kolom) van alle lege vakken."""
    return [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]


def add_random_tile(board, rng=random):
    """Geeft een NIEUW bord terug met een extra tegel (90% een 2, 10% een 4)."""
    new = copy_board(board)
    cells = empty_cells(new)
    if not cells:
        return new
    r, c = rng.choice(cells)
    new[r][c] = 2 if rng.random() < 0.9 else 4
    return new


def new_board(rng=random):
    """Nieuw spel: leeg bord met twee starttegels."""
    return add_random_tile(add_random_tile(empty_board(), rng), rng)


# ------------------------------------------------------------------- schuiven

@lru_cache(maxsize=None)
def slide_row(row):
    """Schuif één rij (tuple) naar links.

    Geeft (nieuwe_rij, punten) terug. Elke tegel mag maar één keer per zet
    samensmelten, bv. [2,2,2,2] -> [4,4,0,0] en [2,2,4,0] -> [4,4,0,0].
    """
    tiles = [v for v in row if v != 0]
    result = []
    points = 0
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged = tiles[i] * 2
            result.append(merged)
            points += merged
            i += 2
        else:
            result.append(tiles[i])
            i += 1
    result += [0] * (SIZE - len(result))
    return tuple(result), points


def move(board, direction):
    """Voer een zet uit. Geeft (nieuw_bord, punten) terug.

    direction is "left", "right", "up" of "down". Bij een zet die niets
    verandert krijg je een kopie van het oude bord en 0 punten terug.
    Er komt GEEN nieuwe tegel bij (zie bovenaan dit bestand).
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"onbekende richting: {direction!r}")

    if direction in ("up", "down"):
        lines = [tuple(board[r][c] for r in range(SIZE)) for c in range(SIZE)]
    else:
        lines = [tuple(row) for row in board]

    reverse = direction in ("right", "down")
    new_lines = []
    points = 0
    for line in lines:
        if reverse:
            slid, pts = slide_row(line[::-1])
            slid = slid[::-1]
        else:
            slid, pts = slide_row(line)
        new_lines.append(list(slid))
        points += pts

    if direction in ("up", "down"):
        new_board = [[new_lines[c][r] for c in range(SIZE)] for r in range(SIZE)]
    else:
        new_board = new_lines
    return new_board, points


# ------------------------------------------------------------- toestand check

def valid_moves(board):
    """Alle richtingen die het bord echt veranderen."""
    return [d for d in DIRECTIONS if move(board, d)[0] != board]


def game_over(board):
    """True als er geen enkele zet meer mogelijk is."""
    return not valid_moves(board)


def highest_tile(board):
    return max(max(row) for row in board)
