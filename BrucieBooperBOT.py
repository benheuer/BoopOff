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

        EW=1.5
        edgeVal = .003
        kittenVal = .01
        catVal = .028
        depth_limit = 3
        

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

        def has_three(board1, current_player, piece_type=None):
            # Check whether current_player has a completed line.
            # piece_type: 1 = kitten, 2 = cat, None = either
            target = current_player
    
            for line in lines:
                pieces = [
                    board1.board[to_coord(pos)[0]][to_coord(pos)[1]]
                    for pos in line
                ]
    
                if all(
                    piece == target * piece_kind
                    for piece, piece_kind in zip(
                        pieces,
                        [piece_type] * 3 if piece_type is not None
                        else [1 if p > 0 else -1 for p in pieces]
                    )
                ):
                    return True

        return False
    
        def has_three_of_type(board1, current_player, piece_type):
            # More direct check for three identical cats or kittens.
            target = current_player * piece_type
    
            for line in lines:
                pieces = [
                    board1.board[to_coord(pos)[0]][to_coord(pos)[1]]
                    for pos in line
                ]
    
                if all(piece == target for piece in pieces):
                    return True
    
            return False
    
        def winning_moves(board1, current_player, legals, piece_type=None):
            # Return legal moves that create a line of three.
            winning = []
    
            for move1 in legals:
                board2 = deepcopy(board1)
                board2.play(move1)
    
                if piece_type is None:
                    won = (
                        has_three_of_type(board2, current_player, 1)
                        or has_three_of_type(board2, current_player, 2)
                    )
                else:
                    won = has_three_of_type(
                        board2, current_player, piece_type
                    )
    
                if won:
                    winning.append(move1)
    
            return winning
        
        def minimax(board1, depth, current_player, alpha, beta):
            # Get legal moves for the player whose turn it is
            legals = board1.get_legals(current_player) or []
    
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
    
            # Check whether the opponent can make three cats in a row
            opponent = 3 - player
            opponent_legals = board.get_legals(opponent) or []
        
            opponent_cat_wins = winning_moves(
                board, opponent, opponent_legals, piece_type=2
            )
        
            # If the opponent threatens a cat line, prioritize disrupting it.
            if opponent_cat_wins:
                results = []
        
                for move in moves:
                    board1 = deepcopy(board)
                    board1.play(move)
        
                    # See whether the opponent still has a winning cat move.
                    remaining_legals = board1.get_legals(opponent) or []
                    remaining_wins = winning_moves(
                        board1, opponent, remaining_legals, piece_type=2
                    )
        
                    # Minimize remaining opponent cat-winning moves,
                    # then use minimax to break ties.
                    value = -1000 * len(remaining_wins)
        
                    value += minimax(
                        board1,
                        depth_limit - 1,
                        opponent,
                        float("-inf"),
                        float("inf")
                    )
        
                    results.append((value, move))
        
                best = max(v for v, _ in results)
                return random.choice([m for v, m in results if v == best])
        
            # No opponent cat threat: take an immediate line win if available.
            immediate_wins = winning_moves(
                board, player, moves
            )
        
            if immediate_wins:
                return random.choice(immediate_wins)
        
            # Otherwise, use ordinary minimax.
            results = []
        
            for move in moves:
                board1 = deepcopy(board)
                board1.play(move)
        
                value = minimax(
                    board1,
                    depth_limit - 1,
                    opponent,
                    float("-inf"),
                    float("inf")
                )
        
                results.append((value, move))
        
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
