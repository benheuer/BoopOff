import rules, bot
from random import choice

class ByteSized(BoopBot):

    def give_move(moves, board):

        return choice(moves)
    
    def give_grow(grows, board):

        return choice(grows)