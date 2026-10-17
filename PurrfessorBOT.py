from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class Purrfessor(BoopBot):

  def give_move(self, moves, board, player):
    best = moves[0]
    min_score = float('-inf')

    for move in moves:
      state = deepcopy(board)
      state.play(move)
      values = []
      for after in state.get_legals():
        substate = deepcopy(state)
        substate.play(after)
        subvalues = []
        subposition = evaluate(substate,player)
        for last in substate.get_legals():
          sub2state = deepcopy(substate)
          sub2state.play(last)
          sub2position = evaluate(sub2state,player)
          if subvalues[0] > sub2position and len(subvalue) > 0:
            continue
          else:
            subvalue.append(sub2position)
        value.append(min(subvalues))
      if min(values) > min_score:
        min_score = min(values)
        best = move

  def give_grow(self, moves, board, player):
      pass
      #Nothing yet to put here

def evaluate(board,player):
  return 0
  #Will be the base evaluator for my eval system
