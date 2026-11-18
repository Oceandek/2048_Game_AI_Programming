from game import new_board, add_tile, move, valid_moves, game_over, print_board

KEYS = {"z": "up", "q": "left", "s": "down", "d": "right"}  # AZERTY


def play():
    """Zelf spelen in de terminal met z/q/s/d."""
    board = new_board()
    add_tile(board)
    add_tile(board)
    score = 0

    while not game_over(board):
        print("\nScore:", score)
        print_board(board)
        key = input("Zet (z/q/s/d, x = stoppen): ").lower()

        if key == "x":
            break
        if key not in KEYS:
            continue

        direction = KEYS[key]
        if direction not in valid_moves(board):
            print("Die zet doet niets.")
            continue

        board, points = move(board, direction)
        score += points
        add_tile(board)

    print("\nGame over! Eindscore:", score)
    print_board(board)


if __name__ == "__main__":
    play()
