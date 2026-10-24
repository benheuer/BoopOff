import random
import time
from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class BrucieBooper(BoopBot):

    def give_move(self, moves, board, player):
        """
        Minimax bot with alpha-beta pruning.

        Priorities:
        1. Take a winning move with three cats.
        2. Make a line of three whenever possible.
        3. Prevent the opponent from winning on their next turn.
        4. Disrupt dangerous enemy lines.
        5. Never return a move that is not legal.
        """

        if player not in (1, 2):
            raise ValueError("player must be 1 or 2")

        lines = get_lines()

        # The board encoding:
        # Player 1: -1 = kitten, -2 = cat
        # Player 2:  1 = kitten,  2 = cat
        MY_KITTEN = -player if player == 1 else 1
        MY_CAT = -2 if player == 1 else 2
        ENEMY_KITTEN = 1 if player == 1 else -1
        ENEMY_CAT = 2 if player == 2 else -2

        WIN_SCORE = 1_000_000
        CAT_LINE_SCORE = 100_000
        KITTEN_LINE_SCORE = 25_000
        TWO_CAT_SCORE = 180
        TWO_KITTEN_SCORE = 35

        EDGE_PENALTY = 0.5
        KITTEN_VALUE = 2.0
        CAT_VALUE = 6.0

        DEPTH_LIMIT = 3

        def piece_owner(piece):
            if piece < 0:
                return 1
            if piece > 0:
                return 2
            return 0

        def line_pieces(board1, line):
            return [
                board1.board[to_coord(pos)[0]][to_coord(pos)[1]]
                for pos in line
            ]

        def winning_cat_line(board1, who):
            """True if who has a line of three cats."""
            target = -2 if who == 1 else 2

            for line in lines:
                pieces = line_pieces(board1, line)
                if all(piece == target for piece in pieces):
                    return True

            return False

        def completed_lines(board1, who):
            """Count completed lines of three matching pieces."""
            kitten = -1 if who == 1 else 1
            cat = -2 if who == 1 else 2

            kitten_lines = 0
            cat_lines = 0

            for line in lines:
                pieces = line_pieces(board1, line)

                if all(piece == cat for piece in pieces):
                    cat_lines += 1
                elif all(piece == kitten for piece in pieces):
                    kitten_lines += 1

            return kitten_lines, cat_lines

        def evaluate(board1):
            """
            Scores positions from the original player's perspective.
            Winning cat lines dominate every positional consideration.
            """

            # Terminal wins must always outweigh ordinary positional scores.
            if winning_cat_line(board1, player):
                return WIN_SCORE

            opponent = 3 - player

            if winning_cat_line(board1, opponent):
                return -WIN_SCORE

            value = 0.0

            # Count and score every completed line.
            my_kittens, my_cats = completed_lines(board1, player)
            enemy_kittens, enemy_cats = completed_lines(
                board1, opponent
            )

            # Cat lines are winning threats; kitten lines are valuable too.
            value += my_cats * CAT_LINE_SCORE
            value -= enemy_cats * CAT_LINE_SCORE

            value += my_kittens * KITTEN_LINE_SCORE
            value -= enemy_kittens * KITTEN_LINE_SCORE

            # Evaluate incomplete lines and threats.
            for line in lines:
                pieces = line_pieces(board1, line)

                for who, kitten, cat, sign in (
                    (player, MY_KITTEN, MY_CAT, 1),
                    (
                        opponent,
                        ENEMY_KITTEN,
                        ENEMY_CAT,
                        -1,
                    ),
                ):
                    del who

                    # A line is dangerous when two matching pieces
                    # have an empty third square.
                    for piece, score in (
                        (cat, TWO_CAT_SCORE),
                        (kitten, TWO_KITTEN_SCORE),
                    ):
                        if pieces.count(piece) == 2 and pieces.count(0) == 1:
                            value += sign * score

            # Positional and material evaluation.
            for r, row in enumerate(board1.board):
                for c, piece in enumerate(row):
                    if piece == 0:
                        continue

                    owner = piece_owner(piece)

                    edge = (
                        r == 0
                        or r == len(board1.board) - 1
                        or c == 0
                        or c == len(row) - 1
                    )

                    if abs(piece) == 1:
                        piece_value = KITTEN_VALUE
                    else:
                        piece_value = CAT_VALUE

                    if owner == player:
                        value += piece_value

                        if edge:
                            value -= EDGE_PENALTY
                    else:
                        value -= piece_value * 1.2

                        # Edge pieces are more likely to be booped off.
                        if edge:
                            value += EDGE_PENALTY

            return value

        def legal_moves(board1, who):
            """Always get the legal moves for the player to move."""
            return list(board1.get_legals(who))

        def minimax(board1, depth, current_player, alpha, beta):
            # A completed cat line ends the game immediately.
            if winning_cat_line(board1, player):
                return WIN_SCORE + depth

            if winning_cat_line(board1, 3 - player):
                return -WIN_SCORE - depth

            legals = legal_moves(board1, current_player)

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
                        beta,
                    )

                    value = max(value, score)
                    alpha = max(alpha, value)

                    if alpha >= beta:
                        break

                return value

            value = float("inf")

            for move1 in legals:
                board2 = deepcopy(board1)
                board2.play(move1)

                score = minimax(
                    board2,
                    depth - 1,
                    3 - current_player,
                    alpha,
                    beta,
                )

                value = min(value, score)
                beta = min(beta, value)

                if alpha >= beta:
                    break

            return value

        # ---------------------------------------------------------
        # 1. Verify the available moves before considering anything.
        # ---------------------------------------------------------
        actual_legals = legal_moves(board, player)

        if not actual_legals:
            # No move can be returned if the game supplies no legal moves.
            return None

        # Use the intersection of the supplied moves and the board's
        # own legal moves, so we never search an illegal root move.
        candidates = [
            move for move in moves
            if move in actual_legals
        ]

        if not candidates:
            # Emergency fallback: choose only from verified legal moves.
            return random.choice(actual_legals)

        # ---------------------------------------------------------
        # 2. Detect an immediate win before ordinary minimax.
        # ---------------------------------------------------------
        winning_moves = []

        for move in candidates:
            test_board = deepcopy(board)
            test_board.play(move)

            if winning_cat_line(test_board, player):
                winning_moves.append(move)

        if winning_moves:
            return random.choice(winning_moves)

        # ---------------------------------------------------------
        # 3. Look for moves that complete a line of three.
        #    Prefer cats over kittens.
        # ---------------------------------------------------------
        line_completing_moves = []

        for move in candidates:
            test_board = deepcopy(board)
            test_board.play(move)

            my_kittens, my_cats = completed_lines(test_board, player)
            old_kittens, old_cats = completed_lines(board, player)

            new_cats = my_cats - old_cats
            new_kittens = my_kittens - old_kittens

            if new_cats > 0:
                line_completing_moves.append(
                    (3, random.random(), move)
                )
            elif new_kittens > 0:
                line_completing_moves.append(
                    (2, random.random(), move)
                )

        if line_completing_moves:
            best_priority = max(item[0] for item in line_completing_moves)

            best_moves = [
                item[2]
                for item in line_completing_moves
                if item[0] == best_priority
            ]

            # Choose the strongest immediate line-making opportunity.
            # Still check whether the opponent can win immediately.
            safe_moves = []

            for move in best_moves:
                test_board = deepcopy(board)
                test_board.play(move)

                enemy_moves = legal_moves(test_board, 3 - player)
                enemy_can_win = False

                for enemy_move in enemy_moves:
                    enemy_board = deepcopy(test_board)
                    enemy_board.play(enemy_move)

                    if winning_cat_line(enemy_board, 3 - player):
                        enemy_can_win = True
                        break

                if not enemy_can_win:
                    safe_moves.append(move)

            if safe_moves:
                return random.choice(safe_moves)

            # If every line-making move allows a win, minimax will
            # compare them against other defensive options below.

        # ---------------------------------------------------------
        # 4. Search all candidate moves.
        #    Opponent wins are scored as enormous negative values.
        # ---------------------------------------------------------
        results = []

        for move in candidates:
            board1 = deepcopy(board)
            board1.play(move)

            # If the opponent has an immediate winning reply, heavily
            # discourage this move unless there is no better choice.
            enemy_moves = legal_moves(board1, 3 - player)
            opponent_has_winning_reply = False

            for enemy_move in enemy_moves:
                enemy_board = deepcopy(board1)
                enemy_board.play(enemy_move)

                if winning_cat_line(enemy_board, 3 - player):
                    opponent_has_winning_reply = True
                    break

            if opponent_has_winning_reply:
                value = -WIN_SCORE * 2
            else:
                value = minimax(
                    board1,
                    DEPTH_LIMIT - 1,
                    3 - player,
                    float("-inf"),
                    float("inf"),
                )

            results.append((value, move))

        best_value = max(value for value, _ in results)

        best_moves = [
            move for value, move in results
            if value == best_value
        ]

        selected_move = random.choice(best_moves)

        # ---------------------------------------------------------
        # 5. FINAL SAFETY CHECK: never return an illegal move.
        # ---------------------------------------------------------
        if selected_move not in legal_moves(board, player):
            return random.choice(legal_moves(board, player))

        return selected_move

    def give_grow(self, grows, board, player):
        """
        Choose an eligible grow move, preserving the original behavior.
        """

        if not grows:
            return None

        for grow in grows:
            kind, locale = grow

            r, c = to_coord(
                locale[0] if kind == "grow" else locale
            )

            piece = board.board[r][c]

            if player == 2 and piece > 0:
                return grow

            if player == 1 and piece < 0:
                return grow

        return random.choice(grows)

