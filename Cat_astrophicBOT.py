import random
from bot import BoopBot
from rules import Board, IllegalMove, to_coord, get_lines



# change these weights to adjust the playstyle
CENTER_W = 3.0      # reward for pieces near the middle of the board
CLUSTER_W = 2.0     # reward for each pair of my pieces touching each other
EXPOSURE_W = 1.5    # penalty for each way one of my pieces could be booped
LINE_W = 1.0        # reward for lines (of 3) completeable
CAT_WEIGHT = 2.0    # cats count this much in every term above
KITTEN_WEIGHT = 1.0 # kittens count this much in every term above

BOARD_CENTER = 2.5  # the middle of a 6x6 board sits between squares 2 and 3

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

LINE_COORDS = [[to_coord(i) for i in line] for line in get_lines()]


def in_bounds(r, c):
    return 0 <= r <= 5 and 0 <= c <= 5


def fast_copy(board):
    """A quicker stand-in for copy.deepcopy(board)."""
    return Board([row[:] for row in board.board], [h[:] for h in board.hands])


def dist_from_center(index):
    """Straight-line distance from a square index to the middle of the board."""
    r, c = to_coord(index)
    return ((r - BOARD_CENTER) ** 2 + (c - BOARD_CENTER) ** 2) ** 0.5


class Cat_astrophic(BoopBot):

    # This chooses a placement for kittens/cats
    def give_move(self, moves, board, player):
        try:
            return self._choose_move(moves, board, player)
        except Exception:
            # Never crash, bot. This will ensure you don't MWAHAHAHAHAHAHA
            return random.choice(moves)

    def _choose_move(self, moves, board, player):
        opponent = 3 - player
        winning = []     # moves that win right now
        entries = []     # (move, board after move) where nobody has won

        for move in moves:
            after = fast_copy(board)
            after.play(move)
            result = after.is_terminal()
            if result == player:
                winning.append(move)
            elif result == 0:
                entries.append((move, after))
        

        # Here's the top priority for the bot:
        if winning:
            return random.choice(winning)
        # That's right: you'll never believe this, but the bot always wants to win.

        # Avoiding opponent wins:
        safe = [(m, a) for (m, a) in entries if not self._opponent_can_win(a, opponent)]

        # (If nothing is safe, it then just picks what it can do in sad defeat.)
        pool = safe or entries
        if not pool:
            return random.choice(moves)

        # Then it judges the board after its move and takes the highest score:
        scored = [(self._score(a, player), m) for (m, a) in pool]
        best = max(s for s, _ in scored)
        return random.choice([m for s, m in scored if s == best])

    def _opponent_can_win(self, board, opponent):
        """True if the opponent has any reply that wins immediately."""
        try:
            replies = board.get_legals(opponent)
        except IllegalMove:
            return False
        for reply in replies:
            if abs(reply[0]) != 2:
                continue
            after = fast_copy(board)
            after.play(reply)
            if after.is_terminal() == opponent:
                return True
        return False

    # Scoring a board position from our point of view (higher is better):
    def _score(self, board, player):
        sign = -1 if player == 1 else 1
        b = board.board
        total = 0.0

        for r in range(6):
            for c in range(6):
                value = b[r][c]
                if value * sign <= 0:
                    continue  # empty or not mine

                w = CAT_WEIGHT if abs(value) == 2 else KITTEN_WEIGHT

                # Centrality: 2.5 for the four middle squares, 1.5 next ring, 0.5 on the edge
                ring = max(abs(r - BOARD_CENTER), abs(c - BOARD_CENTER))
                total += CENTER_W * w * (3 - ring)

                for dr, dc in DIRECTIONS:
                    # The bot's main strategy: clustering: reward touching my own pieces (halved, since each pair is seen twice)
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and b[nr][nc] * sign > 0:
                        total += CLUSTER_W * 0.5

                    # Exposure: a piece can be booped if an empty square next to it lets
                    # something be placed there AND the square on the far side is empty
                    # (pushed along) or off the board (sent back to hand).
                    if in_bounds(nr, nc) and b[nr][nc] == 0:
                        orr, oc = r - dr, c - dc
                        if (not in_bounds(orr, oc)) or b[orr][oc] == 0:
                            total -= EXPOSURE_W * w

        # Line potential: lines of three with none of the opponent's pieces in them
        for line in LINE_COORDS:
            mine = 0
            blocked = False
            for (r, c) in line:
                v = b[r][c]
                if v * sign > 0:
                    mine += 1
                elif v != 0:
                    blocked = True
                    break
            if not blocked:
                total += LINE_W * {0: 0, 1: 0, 2: 1, 3: 3}[mine]

        return total

    # Choosing a graduation / removal
    def give_grow(self, grows, board, player):
        try:
            scored = [(self._grow_distance(g), g) for g in grows]
            best = max(s for s, _ in scored)
            return random.choice([g for s, g in scored if s == best])
        except Exception:
            return random.choice(grows)

    def _grow_distance(self, grow):
        """How far a grow choice is from the center (bigger = further away)."""
        kind, where = grow
        if kind == "grow":
            return sum(dist_from_center(i) for i in where) / len(where)
        return dist_from_center(where)  # "remove": a single square
