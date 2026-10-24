import random
import time
from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class BrucieBooper(BoopBot):

    def give_move(self, moves, board, player):
        lines = get_lines()
        results = []

        EW = 1.5
        edgeVal = .003
        kittenVal = .01
        catVal = .028
        depth_limit = 3

        enemy = 3 - player

        # Stronger tactical values
        enemyLineVal = 1
        ownLineVal = 1.5
        catLineBonus = 5
        immediateWinVal = 10

        def evaluate(board1):
            value = 0

            # Evaluate lines
            for line in lines:
                a = board1.board[to_coord(line[0])[0]][to_coord(line[0])[1]]
                b = board1.board[to_coord(line[1])[0]][to_coord(line[1])[1]]
                c = board1.board[to_coord(line[2])[0]][to_coord(line[2])[1]]

                # A complete line of three
                if a == b == c and a != 0:
                    if (b > 1 and player == 2) or (b < -1 and player == 1):
                        value += ownLineVal
                    elif (b < -1 and player == 2) or (b > 1 and player == 1):
                        value -= enemyLineVal

                    elif (b > 0 and player == 2) or (b < 0 and player == 1):
                        value += 4
                    else:
                        value -= 4

                # Two pieces in a line: reward our threats,
                # heavily penalize enemy threats.
                elif (a == b or b == c) and b != 0:
                    if (a == b and a != 0) or (b == c and b != 0):
                        # Only score a pair if the third square is empty.
                        if (a == b and c == 0) or (b == c and a == 0):
                            if (b > 0 and player == 2) or (b < 0 and player == 1):
                                value += 2
                            elif (b < 0 and player == 2) or (b > 0 and player == 1):
                                value -= enemyLineVal

                elif a == c and a != 0 and b == 0:
                    if (a > 0 and player == 2) or (a < 0 and player == 1):
                        value += 1
                    elif (a < 0 and player == 2) or (a > 0 and player == 1):
                        value -= enemyLineVal

            # Evaluate pieces and edge positions
            for i in range(len(board1.board)):
                for j in range(len(board1.board[i])):
                    piece = board1.board[i][j]

                    if piece == 0:
                        continue

                    edge = (
                        i == 0
                        or i == len(board1.board) - 1
                        or j == 0
                        or j == len(board1.board[i]) - 1
                    )

                    if player == 1:
                        if piece == -1:
                            value += kittenVal / 2
                            if edge:
                                value -= edgeVal

                        if piece == 1:
                            value -= kittenVal * EW

                        if piece == -2:
                            value += catVal
                            if edge:
                                value -= edgeVal * .75

                        if piece == 2:
                            value -= catVal * 1.2 * EW
                            if edge:
                                value += edgeVal / 2

                    elif player == 2:
                        if piece == -1:
                            value -= kittenVal * EW

                        if piece == 1:
                            value += kittenVal / 2
                            if edge:
                                value -= edgeVal

                        if piece == -2:
                            value -= catVal * 1.2 * EW
                            if edge:
                                value += edgeVal / 2

                        if piece == 2:
                            value += catVal
                            if edge:
                                value -= edgeVal * .75

            return value

        def has_line_of_three(board1, who):
            for line in lines:
                pieces = [
                    board1.board[to_coord(pos)[0]][to_coord(pos)[1]]
                    for pos in line
                ]

                if all(p != 0 for p in pieces):
                    if all(
                        (p < 0 if who == 1 else p > 0)
                        for p in pieces
                    ):
                        return True

            return False

        def makes_cat_line(board1, who):
            """Check for a completed line containing three cats."""
            for line in lines:
                pieces = [
                    board1.board[to_coord(pos)[0]][to_coord(pos)[1]]
                    for pos in line
                ]

                if all(
                    (p < -1 if who == 1 else p > 1)
                    for p in pieces
                ):
                    return True

            return False

        def minimax(board1, depth, current_player, alpha, beta):
            legals = board1.get_legals(current_player)

            # A completed line is a major tactical event.
            if has_line_of_three(board1, player):
                return immediateWinVal + depth

            if has_line_of_three(board1, enemy):
                return -immediateWinVal - depth

            if depth == 0 or not legals:
                return evaluate(board1)

            if current_player == player:
                value = float("-inf")

                for move1 in legals:
                    board2 = deepcopy(board1)
                    board2.play(move1)

                    score = minimax(
                        board2,
                        depth - 1,
                        3 - current_player,
                        alpha,
                        beta
                    )

                    value = max(value, score)
                    alpha = max(alpha, value)

                    if alpha >= beta:
                        break

                return value

            else:
                value = float("inf")

                for move1 in legals:
                    board2 = deepcopy(board1)
                    board2.play(move1)

                    score = minimax(
                        board2,
                        depth - 1,
                        3 - current_player,
                        alpha,
                        beta
                    )

                    value = min(value, score)
                    beta = min(beta, value)

                    if alpha >= beta:
                        break

                return value

        # Only consider legal moves supplied by the game.
        legal_moves = board.get_legals(player)
        moves = [move for move in moves if move in legal_moves]

        if not moves:
            if legal_moves:
                return random.choice(legal_moves)
            return None

        # Evaluate every possible first move.
        for move in moves:
            board1 = deepcopy(board)
            board1.play(move)

            # Strongly prioritize making a line immediately.
            if has_line_of_three(board1, player):
                value = immediateWinVal
                if makes_cat_line(board1, player):
                    value += catLineBonus
                results.append((value, move))
                continue

            # Check whether the opponent has an immediate line threat.
            enemy_can_make_line = False

            enemy_moves = board1.get_legals(enemy)
            for enemy_move in enemy_moves:
                board2 = deepcopy(board1)
                board2.play(enemy_move)

                if has_line_of_three(board2, enemy):
                    enemy_can_make_line = True
                    break

            # Reject moves that allow an immediate enemy line whenever
            # another move avoids it.
            value = minimax(
                board1,
                depth_limit - 1,
                enemy,
                float("-inf"),
                float("inf")
            )

            if enemy_can_make_line:
                value -= immediateWinVal

            results.append((value, move))

        if not results:
            return random.choice(legal_moves)

        # Prefer the highest-scoring move, randomly breaking ties.
        best = max(v for v, _ in results)
        chosen = random.choice([m for v, m in results if v == best])

        # safety
        if chosen not in legal_moves:
            return random.choice(legal_moves)
        #more safety
        if chosen not in board.get_legals(player):
            return random.choice(board.get_legals(player))
            
        return chosen

    def give_grow(self, grows, board, player):
        # Finds first eligible grow
        for grow in grows:
            kind, locale = grow
            r, c = to_coord(locale[0] if kind == "grow" else locale)

            if board.board[r][c] > 0 and player == 2:
                return grow

            elif board.board[r][c] < 0 and player == 1:
                return grow

        return grows[0]

