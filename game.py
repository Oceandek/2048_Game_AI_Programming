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


def print_board(board):
    for row in board:
        print(" ".join(str(v).rjust(4) if v else "   ." for v in row))


if __name__ == "__main__":
    board = new_board()
    add_tile(board)
    add_tile(board)
    print_board(board)
