"""Kleine tests voor game.py. Run: python test_game.py"""
import game


def test_slide_en_merge():
    assert game.slide_row((2, 2, 2, 2)) == ((4, 4, 0, 0), 8)
    assert game.slide_row((2, 2, 4, 0)) == ((4, 4, 0, 0), 4)
    assert game.slide_row((0, 0, 0, 2)) == ((2, 0, 0, 0), 0)
    assert game.slide_row((4, 2, 2, 0)) == ((4, 4, 0, 0), 4)


def test_vier_richtingen():
    b = [[2, 0, 0, 2],
         [0, 4, 0, 0],
         [0, 0, 0, 0],
         [2, 0, 0, 2]]
    assert game.move(b, "left")[0][0] == [4, 0, 0, 0]
    assert game.move(b, "right")[0][0] == [0, 0, 0, 4]
    nb, pts = game.move(b, "up")
    assert [row[0] for row in nb] == [4, 0, 0, 0] and pts == 8
    nb, pts = game.move(b, "down")
    assert [row[0] for row in nb] == [0, 0, 0, 4]


def test_zet_zonder_effect():
    b = [[2, 4, 2, 4],
         [4, 2, 4, 2],
         [2, 4, 2, 4],
         [4, 2, 4, 2]]
    assert game.move(b, "left") == (b, 0)
    assert game.valid_moves(b) == []
    assert game.game_over(b)


def test_origineel_bord_blijft_heel():
    b = [[2, 2, 0, 0]] + [[0] * 4 for _ in range(3)]
    game.move(b, "left")
    assert b[0] == [2, 2, 0, 0]


def test_nieuw_bord():
    b = game.new_board()
    assert sum(v != 0 for row in b for v in row) == 2
    assert not game.game_over(b)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
