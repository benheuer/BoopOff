from abc import ABC, abstractmethod

class BoopBot(ABC):

  @abstractmethod
  def give_move(self, moves, board, player):
    '''Will take the list of legal moves with a deepcopy of the boardstate and output a move to make'''
    pass

  @abstractmethod
  def give_grow(self, grows, board, player):
    '''Will take the list of legal grows with a deepcopy of the boardstate and output a grow to make'''
    pass

# Each participant will create a subclass with these functions that can do whatever it wants so long as it gives the right outputs.
