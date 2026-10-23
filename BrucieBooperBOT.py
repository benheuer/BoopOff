import random
import time
from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class BrucieBooper(BoopBot):

    #board is a 6x6 array with 0 for basic, -1 and -2 for player == 1, and 1 and 2 for player == 2
    #player == 1 or 2
    def give_move(self, moves, board, player): # Searches its next turn for partial lines
        print(str(self))
        lines = get_lines()
        results = []

        for move in moves:
            board1 = deepcopy(board)
            board1.play(move)
            value = 0
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
                elif (a == c and a != 0):
                    if a > 0 and player == 2:
                        value += 1
                    elif a < 0 and player == 1:
                        value += 1
                    else:
                        value -= 1
                else:
                    pass
                for i in board:
                    for j in board:
                        if board[i][j] != 0:
                            if player == 1:
                                if board[i][j] == -1:
                                    value += 0.1
                                if board[i][j] == 1:
                                    value -= .01
                            if player == 2:
                                if board[i][j] == -1:
                                    value -= 0.1
                                if board[i][j] == 1:
                                    value += .01

            
            results.append((value, move))
        
        best = max(v for v, _ in results)
        dialogue = ["Take this!", "Clever phrase here!", "I coded a knockoff of your bot!", "Its final... brucieBooper WINS!!!", "WAHAHA", "You aren't ready for my specail attack."]
        print(random.choice(dialogue))
        print("")
        time.sleep(.2)
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
