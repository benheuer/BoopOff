from bot import BoopBot
from rules import Board, get_lines
from random import choice

class ByteSized(BoopBot):

    def give_move(self, moves, board, player): # Searches its next turn for partial lines

        lines = get_lines()
        results = []

        for move in moves:
            state = board.play(move)
            value = 0
            for line in lines:
                a = board.board[to_index(line[0])[0]][to_index(line[0])[1]]
                b = board.board[to_index(line[1])[0]][to_index(line[1])[1]]
                c = board.board[to_index(line[2])[0]][to_index(line[2])[1]]

                if (a == b and b == c) and a != 0:
                    if b > 1 and player == 2:
                        value += 10000000000
                    elif b < -1 and player == 1:
                        value += 10000000000
                    elif b > 0 and player == 2:
                        value += 4
                    elif b < 0 and player == 1:
                        value += 4
                    else:
                        value -= 2

                elif (a == b or b == c) and b != 0:
                    if b > 0 and player == 2:
                        value += 2
                    elif b < 0 and player == 1:
                        value += 2
                    else:
                        value -= 2
                elif (a == c and a != 0):
                    if a > 0 and player == 2:
                        value += 1
                    elif a < 0 and player == 1:
                        value += 1
                    else:
                        value -= 1
                else:
                    pass
            
            result.append((value, move))
        
        return sorted(result)[len(result) - 1][1]

    
    def give_grow(self, grows, board, player): #Finds first eligible grow

        for grow in grows:

            if board.board[to_index(grow[0])[0]][to_index(grow[0])[1]] > 0 and player == 2:
                return grow

            elif board.board[to_index(grow[0])[0]][to_index(grow[0])[1]] < 0 and player == 1:
                return grow
