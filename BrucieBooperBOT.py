import random
import time
from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class BrucieBooper(BoopBot):
    
    #this will crash immediately
    #board is a 6x6 array with 0 for basic, -1 and -2 for player == 1, and 1 and 2 for player == 2
    #player == 1 or 2
    def give_move(self, moves, board, player):
    # Searches ahead using recursive minimax
        lines = get_lines()
        results = []

        EW=10
        edgeVal = .003
        kittenVal = .01
        catVal = .028
        depth_limit = 3

    
            # Precompute line coordinates once
        line_coords = [
            [to_coord(pos) for pos in line]
            for line in lines
        ]
        def is_winning_move(board1):
            winning_piece = -2 if player == 1 else 2
            for coords in line_coords:
                a = board1.board[coords[0][0]][coords[0][1]]
                if a != winning_piece:
                    continue
                b = board1.board[coords[1][0]][coords[1][1]]
                if b != winning_piece:
                    continue
                c = board1.board[coords[2][0]][coords[2][1]]
                if c == winning_piece:
                    return True
            return False

            # Take an immediate winning move before running minimax
            for move in moves:
                test_board = deepcopy(board)
                test_board.play(move)
    
                if is_winning_move(test_board):
                    return move
            
        def evaluate(board1):
            value = 0
    
            # Evaluate lines (original scoring logic preserved)
            for line in lines:
                a = board1.board[to_coord(line[0])[0]][to_coord(line[0])[1]]
                b = board1.board[to_coord(line[1])[0]][to_coord(line[1])[1]]
                c = board1.board[to_coord(line[2])[0]][to_coord(line[2])[1]]
    
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
    
            # Evaluate pieces and edge positions
            # Original piece values and scoring logic preserved
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
                        if piece == -1: #own kit
                            value += kittenVal / 2
                            if edge:
                                value -= edgeVal
    
                        if piece == 1: #enemy kit
                            value -= kittenVal *EW
    
                        if piece == -2: #own cat
                            value += catVal 
                            if edge:
                                value -= edgeVal * .75
    
                        if piece == 2: #enemy cat
                            value -= catVal * 1.2 *EW
                            if edge:
                                value += edgeVal/2
    
                    elif player == 2:
                        if piece == -1: #enemy kit
                            value -= kittenVal *EW
    
                        if piece == 1: #own kit
                            value += kittenVal / 2
                            if edge:
                                value -= edgeVal
    
                        if piece == -2: #enemy cat
                            value -= catVal * 1.2 *EW
                            if edge:
                                value += edgeVal/2
    
                        if piece == 2: #own cat
                            value += catVal 
                            if edge:
                                value -= edgeVal * .75
    
            return value
    
        def minimax(board1, depth, current_player, alpha, beta):
            # Get legal moves for the player whose turn it is
            legals = board1.get_legals(current_player)
    
            # Stop searching at the depth limit or a terminal position
            if depth == 0 or not legals:
                return evaluate(board1)
    
            if current_player == player:
                # Maximize the AI's score
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
                #print("Hmm. This is tough.")
                
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
    
        # Evaluate every possible first move
        for move in moves:
            board1 = deepcopy(board)
            board1.play(move)
    
            value = minimax(
                board1,
                depth_limit - 1,
                3 - player,
                float("-inf"),
                float("inf")
            )
    
            results.append((value, move))
    
        # Choose randomly between equally good moves
        dialogue = ["Take this!", "Clever phrase here!", "I coded a knockoff of your bot!", "Its final... brucieBooper WINS!!!", "WAHAHA", "You aren't ready for my specail attack.", "All options lead to your demise."]
        print(random.choice(dialogue))
        print("")
        time.sleep(.2)
        best = max(v for v, _ in results)
        return random.choice([m for v, m in results if v == best])
            
    def give_grow(self, grows, board, player): #Finds first eligible grow - doesn't really care (its a weak bot for a reason)

        for grow in grows:
            kind, locale = grow
            r, c = to_coord(locale[0] if kind == "grow" else locale)

            if board.board[r][c] > 0 and player == 2:
                print("")
                print("ataktoush")
                time.sleep(.2)
                time.sleep(.1)
                return grow

            elif board.board[r][c] < 0 and player == 1:
                print("")
                print("parryrepostoush")
                time.sleep(.2)
                time.sleep(.1)
                return grow

        return grows[0]


