import random

SIZE = 4
DIRECTIONS = ["left", "right", "up", "down"]


def new_board():
    """Leeg bord van 4x4, 0 = leeg vak."""
    return [[0] * SIZE for _ in range(SIZE)]


def add_tile(board, rng=random):
    """Zet een 2 (90%) of een 4 (10%) op een willekeurig leeg vak.
    `rng` is optioneel een eigen random.Random (bv. met een vaste seed)."""
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    if empty:
        r, c = rng.choice(empty)
        board[r][c] = 4 if rng.random() < 0.1 else 2


def merge_row(row):
    """Schuift een rij naar links en voegt gelijke tegels samen.
    Elke tegel versmelt maar 1 keer: [2, 2, 2, 2] -> [4, 4, 0, 0]
    Geeft (nieuwe_rij, punten) terug."""
    tiles = [v for v in row if v != 0]
    result = []
    points = 0
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            result.append(tiles[i] * 2)
            points += tiles[i] * 2
            i += 2
        else:
            result.append(tiles[i])
            i += 1
    return result + [0] * (SIZE - len(result)), points


def move_left(board):
    """Schuift alles naar links. Geeft (nieuw_bord, punten) terug."""
    new_board = []
    points = 0
    for row in board:
        new_row, row_points = merge_row(row)
        new_board.append(new_row)
        points += row_points
    return new_board, points


def reverse(board):
    """Spiegelt elke rij: links wordt rechts."""
    return [row[::-1] for row in board]


def transpose(board):
    """Rijen worden kolommen: boven wordt links."""
    return [list(row) for row in zip(*board)]


def move(board, direction):
    """Schuift het bord in een richting: "left", "right", "up" of "down".
    Truc: draai het bord zodat het een zet naar links wordt, en draai terug.
    Geeft (nieuw_bord, punten) terug."""
    if direction == "left":
        return move_left(board)
    if direction == "right":
        new, points = move_left(reverse(board))
        return reverse(new), points
    if direction == "up":
        new, points = move_left(transpose(board))
        return transpose(new), points
    if direction == "down":
        new, points = move_left(reverse(transpose(board)))
        return transpose(reverse(new)), points
    raise ValueError("Onbekende richting: " + direction)


def valid_moves(board):
    """Alle richtingen waarbij er echt iets verschuift."""
    return [d for d in DIRECTIONS if move(board, d)[0] != board]


def game_over(board):
    """Gedaan als geen enkele zet nog iets verandert."""
    return len(valid_moves(board)) == 0


def print_board(board):
    for row in board:
        print(" ".join(str(v).rjust(4) if v else "   ." for v in row))


if __name__ == "__main__":
    board = new_board()
    add_tile(board)
    add_tile(board)
    print_board(board)
    print("Geldige zetten:", valid_moves(board))
    for direction in DIRECTIONS:
        new, points = move(board, direction)
        print("\nNa " + direction + " (+" + str(points) + " punten):")
        print_board(new)

    full = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]]
    print("\nVol bord zonder mogelijke zetten, game over:", game_over(full))
