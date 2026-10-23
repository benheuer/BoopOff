import random
import time
from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class BrucieBooper(BoopBot):

    
    #board is a 6x6 array with 0 for basic, -1 and -2 for player == 1, and 1 and 2 for player == 2
    #player == 1 or 2
    def give_move(self, moves, board, player):  # Searches future turns using minimax
        lines = get_lines()
        results = []

        edgeVal = .2
        kittenVal = .1
        catVal = .28

        depth = 3  # Number of plies to search; increase for stronger play

    def evaluate(board):
        value = 0

        # Evaluate lines — original scoring logic preserved
        for line in lines:
            a = board.board[to_coord(line[0])[0]][to_coord(line[0])[1]]
            b = board.board[to_coord(line[1])[0]][to_coord(line[1])[1]]
            c = board.board[to_coord(line[2])[0]][to_coord(line[2])[1]]

            if (a == b and b == c) and a != 0:
                if b > 1 and player == 2:
                    value += 100
                elif b < -1 and player == 1:
                    value += 100
                elif (b < -1 and player != 1) or (b > 1 and player != 2):
                    value -= 100
                elif b > 0 and player == 2:
                    value += 4
                elif b < 0 and player == 1:
                    value += 4
                else:
                    value -= 4

            elif (a == b or b == c) and b != 0:
                if b > 0 and player == 2:
                    value += 2
                elif b < 0 and player == 1:
                    value += 2
                else:
                    value -= 2

            elif a == c and a != 0:
                if a > 0 and player == 2:
                    value += 1
                elif a < 0 and player == 1:
                    value += 1
                else:
                    value -= 1

        # Evaluate pieces and edge positions — original scoring preserved
        for i in range(len(board.board)):
            for j in range(len(board.board[i])):
                if board.board[i][j] != 0:

                    if player == 1:
                        if board.board[i][j] == -1:
                            value += kittenVal / 2
                            if i == 0 or i == len(board.board) - 1:
                                value -= edgeVal
                            if j == 0 or j == len(board.board[i]) - 1:
                                value -= edgeVal

                        if board.board[i][j] == 1:
                            value -= kittenVal

                        if board.board[i][j] == -2:
                            value += catVal * 1.2
                            if i == 0 or i == len(board.board) - 1:
                                value -= edgeVal * .75
                            if j == 0 or j == len(board.board[i]) - 1:
                                value -= edgeVal * .75

                        if board.board[i][j] == 2:
                            value -= catVal

                    if player == 2:
                        if board.board[i][j] == -1:
                            value -= kittenVal

                        if board.board[i][j] == 1:
                            value += kittenVal / 2
                            if i == 0 or i == len(board.board) - 1:
                                value -= edgeVal
                            if j == 0 or j == len(board.board[i]) - 1:
                                value -= edgeVal

                        if board.board[i][j] == -2:
                            value -= catVal

                        if board.board[i][j] == 2:
                            value += catVal * 1.2
                            if i == 0 or i == len(board.board) - 1:
                                value -= edgeVal * .75
                            if j == 0 or j == len(board.board[i]) - 1:
                                value -= edgeVal * .75

        return value

    def minimax(board, current_player, depth, alpha, beta):
        # Evaluate the position at the search limit
        if depth == 0:
            return evaluate(board)

        legals = board.get_legals(current_player)

        # No legal moves: evaluate the resulting position
        if not legals:
            return evaluate(board)

        if current_player == player:
            best = float("-inf")

            for move1 in legals:
                board2 = deepcopy(board)
                board2.play(move1)

                value = minimax(
                    board2,
                    3 - current_player,
                    depth - 1,
                    alpha,
                    beta
                )

                best = max(best, value)
                alpha = max(alpha, best)

                if beta <= alpha:
                    break  # Alpha-beta pruning

            return best

        else:
            best = float("inf")

            for move1 in legals:
                board2 = deepcopy(board)
                board2.play(move1)

                value = minimax(
                    board2,
                    3 - current_player,
                    depth - 1,
                    alpha,
                    beta
                )

                best = min(best, value)
                beta = min(beta, best)

                if beta <= alpha:
                    break  # Alpha-beta pruning

            return best

    # Evaluate each possible opening move using the recursive search
    for move in moves:
        board1 = deepcopy(board)
        board1.play(move)

        value = minimax(
            board1,
            3 - player,
            depth - 1,
            float("-inf"),
            float("inf")
        )

        results.append((value, move))

    if not results:
        return 

    best = max(v for v, _ in results)
    return choice([m for v, m in results if v == best])
    
    def give_grow(self, grows, board, player): #Finds first eligible grow - doesn't really care (its a weak bot for a reason)

        for grow in grows:
            kind, locale = grow
            r, c = to_coord(locale[0] if kind == "grow" else locale)

            if board.board[r][c] > 0 and player == 2:
                print("ataktoush")
                time.sleep(.2)
                print("")
                time.sleep(.1)
                return grow

            elif board.board[r][c] < 0 and player == 1:
                print("parryrepostoush")
                time.sleep(.2)
                print("")
                time.sleep(.1)
                return grow

        return grows[0]
