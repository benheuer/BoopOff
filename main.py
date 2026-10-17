import copy
import time
from rules import Board, to_coord
from ByteSizedBOT import ByteSized
from MeowddledBOT import Meowddled
from CatGPTBOT import CatGPT
from ClawedBOT import Clawed

BOTS = {
    "ByteSized": ByteSized,
    "Meowddled": Meowddled,
    "CatGPT": CatGPT,
    "Clawed": Clawed,
}
DELAY = 1.5        
TURN_CAP = 400

COLORS = {1: "Blue", 2: "Orange"}
PIECES = {-2: "blue cat", -1: "blue kitten", 1: "orange kitten", 2: "orange cat"}

def own_grows(board, player):
    sign = -1 if player == 1 else 1
    return [g for g in board.get_grows() if board.board[g[0] // 6][g[0] % 6] * sign > 0]

def show(board, text):
    print(text)
    print(board)
    print(f"Hands [kittens, cats]   blue: {board.hands[0]}   orange: {board.hands[1]}\n")
    time.sleep(DELAY)

def run_game(blue, orange):
    """Returns 1 (blue wins), 2 (orange wins) or 0 (draw)."""
    board = Board([[0] * 6 for _ in range(6)], [[8, 0], [8, 0]])
    bots = {1: blue, 2: orange}
    show(board, "Start")
    player = 1
    for turn in range(1, TURN_CAP + 1):
        legals = board.get_legals(player)
        try:
            move = bots[player].give_move(legals, copy.deepcopy(board), player)
            if move not in legals:
                print(f"{COLORS[player]} made an illegal move: {move}")
                return 3 - player
            board.play(move)
        except Exception as e:
            print(f"{COLORS[player]} crashed: {e!r}")
            return 3 - player
        piece, index, kind = move
        row, col = to_coord(index)
        show(board, f"Turn {turn}: {COLORS[player]} {kind}s a {PIECES[piece]} at row {row}, col {col}")

        winner = board.is_terminal()
        if winner:
            return winner

        grows = own_grows(board, player)     # only the mover grows, and only once per turn
        if grows:
            try:
                choice = bots[player].give_grow(grows, copy.deepcopy(board), player)
                choice = tuple(sorted(choice))   # accept lists / any index order
                if choice not in grows:
                    print(f"{COLORS[player]} made an illegal grow: {choice}")
                    return 3 - player
                board.grow(choice)
            except Exception as e:
                print(f"{COLORS[player]} crashed while growing: {e!r}")
                return 3 - player
            show(board, f"{COLORS[player]} grows three kittens into cats")
        player = 3 - player
    return 0

def choose_bot(color):
    names = list(BOTS)
    while True:
        answer = input(f"Who plays {color}? (name or number): ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            return names[int(answer) - 1]
        for name in names:
            if name.lower() == answer.lower():
                return name
        print("That's not on the list, try again.")

def main():
    print("Available bots:")
    for i, name in enumerate(BOTS, start=1):
        print(f"  {i}. {name}")
    print()
    blue = choose_bot("Blue")
    orange = choose_bot("Orange")
    print(f"\nBlue: {blue}   vs   Orange: {orange}\n")
    result = run_game(BOTS[blue](), BOTS[orange]())
    print({1: f"{blue.title()} (blue) wins!", 2: f"{orange.title()} (orange) wins!", 0: "Draw (turn cap reached)."}[result])

if __name__ == "__main__":
    main()
