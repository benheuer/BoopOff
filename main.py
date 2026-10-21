import contextlib
import copy
import io
import time
from collections import deque
from rules import Board, IllegalMove, to_coord
from ByteSizedBOT import ByteSized
from MeowddledBOT import Meowddled
from CatGPTBOT import CatGPT
from ClawedBOT import Clawed
from BrucieBooperBOT import BrucieBooper
from Player import Player
from PurrfessorBOT import Purrfessor

BOTS = {
    "ByteSized": ByteSized,
    "Meowddled": Meowddled,
    "CatGPT": CatGPT,
    "Clawed": Clawed,
    "Purrfessor": Purrfessor,
    "brucieBooper": BrucieBooper,
    "Player": Player
}
DELAY = 1            # pause after each board shown (only used when PACE_MOVES is False)
PACE_MOVES = True    # True: every turn takes MOVE_TIME seconds in total (thinking time counts toward it)
MOVE_TIME = 1.5      # seconds per turn when PACE_MOVES is on. Set PACE_MOVES = False to use DELAY instead.
TURN_CAP = 300
# Repetition draw: after each turn, if the position matches the position this many plies back
# (every one of these), the game is stuck in a loop and is called a draw.
# A ply is one player's whole turn (the placement plus any graduation or removal).
REPEAT_PLIES = (2, 4, 6)

COLORS = {1: "Blue", 2: "Orange"}
PIECES = {-2: "blue cat", -1: "blue kitten", 1: "orange kitten", 2: "orange cat"}

def grow_square(grow):
    """The first board index a growth choice refers to."""
    kind, where = grow
    return where[0] if kind == "grow" else where

def own_grows(board, player):
    sign = -1 if player == 1 else 1
    lines, removes = [], []
    for g in board.get_grows():
        row, col = to_coord(grow_square(g))
        if board.board[row][col] * sign <= 0:
            continue
        (lines if g[0] == "grow" else removes).append(g)
    return lines or removes

def clean_grow(choice):
    """Put a bot's answer in the form get_grows() uses so it can be compared.
    Lets a bot return a list, or the three indices in any order."""
    kind, where = choice
    if kind == "grow":
        return (kind, tuple(sorted(where)))
    return (kind, where)

def describe_grow(board, player, grow):
    kind, where = grow
    if kind == "grow":
        squares = ", ".join(str(to_coord(i)) for i in where)
        return f"{COLORS[player]} removes three pieces and graduates any kittens to cats at {squares}"
    row, col = to_coord(where)
    return f"{COLORS[player]} removes the {PIECES[board.board[row][col]]} at row {row}, col {col} back to hand"

def show(board, text, verbose=True):
    if not verbose:          # many-game runs: no board printing and no delay
        return
    print(text)
    print(board)
    print(f"Hands [kittens, cats]   blue: {board.hands[0]}   orange: {board.hands[1]}\n")
    if not PACE_MOVES:
        time.sleep(DELAY)

def pace(turn_start, verbose=True):
    """Waits out whatever is left of MOVE_TIME, counting from the start of the turn."""
    if verbose and PACE_MOVES:
        left = MOVE_TIME - (time.time() - turn_start)
        if left > 0:
            time.sleep(left)

def run_game(blue, orange, verbose=True, count=False):
    board = Board([[0] * 6 for _ in range(6)], [[8, 0], [8, 0]])
    bots = {1: blue, 2: orange}
    show(board, "Start", verbose)
    player = 1
    TURNCOUNT = 0
    history = deque(maxlen=max(REPEAT_PLIES))     # positions after the last few turns
    for turn in range(1, TURN_CAP + 1):
        turn_start = time.time()
        try:
            legals = board.get_legals(player)
        except IllegalMove:
            print(f"{COLORS[player]} has nothing to play. Ending as a draw.")
            if count:
                return 0, TURNCOUNT
            return 0

        try:
            move = tuple(bots[player].give_move(list(legals), copy.deepcopy(board), player))
        except Exception as e:
            print(f"{COLORS[player]} crashed: {e!r}")
            if count:
                return 3 - player, TURNCOUNT
            return 3 - player
        if move not in legals:
            print(f"{COLORS[player]} made an illegal move: {move}")
            if count:
                return 3 - player, TURNCOUNT
            return 3 - player
        board.play(move)
        TURNCOUNT += 1

        piece, index = move
        row, col = to_coord(index)
        pace(turn_start, verbose)       # show the placement at the end of its MOVE_TIME
        show(board, f"Turn {turn}: {COLORS[player]} places a {PIECES[piece]} at row {row}, col {col}", verbose)

        winner = board.is_terminal()
        if winner:
            if count:
                return winner, TURNCOUNT
            return winner


        grows = own_grows(board, player)
        if grows:
            grow_start = time.time()    # the graduation/removal gets its own MOVE_TIME too
            try:
                choice = clean_grow(bots[player].give_grow(list(grows), copy.deepcopy(board), player))
            except Exception as e:
                print(f"{COLORS[player]} crashed while growing: {e!r}")
                if count:
                    return 3 - player, TURNCOUNT
                return 3 - player
            if choice not in grows:
                print(f"{COLORS[player]} made an illegal grow: {choice}")
                if count:
                    return 3 - player, TURNCOUNT
                return 3 - player
            text = describe_grow(board, player, choice)
            board.grow(choice)
            pace(grow_start, verbose)   # show the graduation at the end of its own MOVE_TIME
            show(board, text, verbose)

        # history[-1] is one ply ago, history[-2] two plies ago, and so on.
        if len(history) == history.maxlen and all(board == history[-k] for k in REPEAT_PLIES):
            print(f"Draw by repetition: the position is the same as {', '.join(str(k) for k in REPEAT_PLIES)} plies ago.")
            if count:
                return 0, TURNCOUNT
            return 0
        history.append(copy.deepcopy(board))
        player = 3 - player
    if count:
        return 0, TURNCOUNT
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

def ask_games(bot1, bot2):
    
    if "Player" in (bot1, bot2):
        return 1
    
    while True:
        answer = input("How many games? (press Enter for 1): ").strip()
        if answer == "":
            return 1
        if answer.isdigit() and int(answer) >= 1:
            return int(answer)
        print("Enter a whole number of 1 or more.")

def run_many(blue, orange, games):
    """Plays `games` silent games (fresh bots each time) and prints the win percentages."""
    results = {0: 0, 1: 0, 2: 0}
    turns = []
    problems = 0
    for _ in range(games):
        log = io.StringIO()
        with contextlib.redirect_stdout(log):      # hides anything a bot or the rules print
            result, count = run_game(BOTS[blue](), BOTS[orange](), verbose=False, count = True)
        results[result] += 1
        turns.append(count)
        # A crash or illegal move is a forfeit, so flag it rather than letting it pass silently.
        problems += any("crashed" in line or "illegal" in line for line in log.getvalue().splitlines())
    turns.sort()
    print(f"{blue} as blue won {results[1]} games ({results[1] / games:.2%})")
    print(f"{orange} as orange won {results[2]} games ({results[2] / games:.2%})")
    print(f"Each game took, on average, {sum(turns) / len(turns):.1f} turns.")
    print(f"The longest game was {turns[-1]} turns, while the shortest was {turns[0]}.")
    if problems:
        print(f"Warning: {problems} game(s) ended because a bot crashed or made an illegal move.")

def main():
    print("Available bots:")
    for i, name in enumerate(BOTS, start=1):
        print(f"  {i}. {name}")
    print()
    blue = choose_bot("Blue")
    orange = choose_bot("Orange")
    games = ask_games(blue, orange)
    if games > 1:
        run_many(blue, orange, games)
        return
    print(f"\nBlue: {blue}   vs   Orange: {orange}\n")
    result = run_game(BOTS[blue](), BOTS[orange]())
    print({1: f"{blue} (blue) wins!", 2: f"{orange} (orange) wins!", 0: "Draw."}[result])

if __name__ == "__main__":
    main()