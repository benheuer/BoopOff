from bot import BoopBot
from random import choice

class Meowddled(BoopBot):

    def give_move(self, moves, board, player):

        return choice(moves)
    
    def give_grow(self, grows, board, player):

        return choice(grows)