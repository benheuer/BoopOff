from bot import BoopBot
from random import choice

class Random(BoopBot):

    def give_move(moves, board, player):

        return choice(moves)
    
    def give_grow(grows, board, player):

        return choice(grows)