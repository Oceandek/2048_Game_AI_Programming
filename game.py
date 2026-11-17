import random

SIZE = 4


def new_board():
    """Leeg bord van 4x4, 0 = leeg vak."""
    return [[0] * SIZE for _ in range(SIZE)]


def add_tile(board):
    """Zet een 2 (90%) of een 4 (10%) op een willekeurig leeg vak."""
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    if empty:
        r, c = random.choice(empty)
        board[r][c] = 4 if random.random() < 0.1 else 2


def merge_row(row):
    """Schuift een rij naar links en voegt gelijke tegels samen.
    Elke tegel versmelt maar 1 keer: [2, 2, 2, 2] -> [4, 4, 0, 0]"""
    tiles = [v for v in row if v != 0]
    result = []
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            result.append(tiles[i] * 2)
            i += 2
        else:
            result.append(tiles[i])
            i += 1
    return result + [0] * (SIZE - len(result))


def move_left(board):
    """Geeft een nieuw bord terug waarbij alles naar links geschoven is."""
    return [merge_row(row) for row in board]


def reverse(board):
    """Spiegelt elke rij: links wordt rechts."""
    return [row[::-1] for row in board]


def transpose(board):
    """Rijen worden kolommen: boven wordt links."""
    return [list(row) for row in zip(*board)]


def move(board, direction):
    """Schuift het bord in een richting: "left", "right", "up" of "down".
    Truc: draai het bord zodat het een zet naar links wordt, en draai terug."""
    if direction == "left":
        return move_left(board)
    if direction == "right":
        return reverse(move_left(reverse(board)))
    if direction == "up":
        return transpose(move_left(transpose(board)))
    if direction == "down":
        return transpose(reverse(move_left(reverse(transpose(board)))))
    raise ValueError("Onbekende richting: " + direction)


def print_board(board):
    for row in board:
        print(" ".join(str(v).rjust(4) if v else "   ." for v in row))


if __name__ == "__main__":
    board = new_board()
    add_tile(board)
    add_tile(board)
    print_board(board)
    for direction in ["left", "right", "up", "down"]:
        print("\nNa " + direction + ":")
        print_board(move(board, direction))
