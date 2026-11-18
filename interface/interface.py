"""interface.py - zet de losse schermen samen tot één Interface.

De interface kent GEEN spelregels. Ze krijgt van main.py het bord (4x4-lijst,
0 = leeg vak) en de score en tekent die alleen. Alles wat de speler doet
(klikken, toetsen) wordt doorgegeven aan het `handler`-object (de Controller
in main.py). Deze methodes verwacht de interface op de handler:

    on_start(mode, difficulty, target)   on_switch_mode(mode)
    on_set_difficulty(diff)              on_set_target(target)
    on_key(direction)                    on_new_game()
    on_undo()                            on_menu()
    on_rematch()                         on_continue()
    on_join_room(tekst)                  on_start_friend()
    on_cancel_join()

Schermen: show_menu, show_single, show_versus, show_friend_lobby, show_result.
"""

from screen_friend import FriendScreen
from screen_result import ResultScreen
from screen_single import SingleScreen
from screen_start import StartScreen
from screen_versus import VersusScreen
from ui_base import *  # noqa: F401,F403  (main.py importeert kleuren en fmt hiervandaan)
from ui_base import UIBase


class Interface(UIBase, StartScreen, SingleScreen, VersusScreen, FriendScreen, ResultScreen):
    pass
