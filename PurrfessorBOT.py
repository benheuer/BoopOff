from bot import BoopBot
from rules import Board, get_lines, to_coord
from random import choice
from copy import deepcopy

class Purrfessor(BoopBot):

  def give_move(self, moves, board, player): ### Simulates every possible three move outcome - inneficient and SLOW
    min_score = float('-inf')

    for move in moves:
      state = deepcopy(board)
      state.play(move)
      values = []
      for after in state.get_legals(3 - player):
        substate = deepcopy(state)
        substate.play(after)
        subvalues = []
        for last in substate.get_legals(player):
          sub2state = deepcopy(substate)
          sub2state.play(last)
          subvalues.append(evaluate(sub2state,player))
        values.append(min(subvalues))
      if min(values) > min_score:
        min_score = min(values)
        best = move

    return best

  def give_grow(self, grows, board, player):

      return choice(grows) ### Just chooses a random grow right now...

### Value Outputs for Each Situation ###

CATONEDGE = 1
WIN = 1000000000000000000000000
TWOBYTWO = 4
THREEROW = 8

def evaluate(board,player):

  pos = board.board
  value = 0
  play_sign = 1 if player == 2 else -1

  def sign(n):
    return (n > 0) - (n < 0)

  lines  = get_lines()

  for line in lines:
    a = pos[to_coord(line[0])[0]][to_coord(line[0])[1]]
    b = pos[to_coord(line[1])[0]][to_coord(line[1])[1]]
    c = pos[to_coord(line[2])[0]][to_coord(line[2])[1]]

    if (a == b and b == c):
      if play_sign == sign(a):
        value += WIN
      else:
        value -= WIN

  for row in range(6):
    for col in range(6):
      if (row in [1,6] or col in [1,6]) and (pos[row][col] != 0): # Small boosts for pieces on edge
        if play_sign == sign(pos[row][col]):
          value -= CATONEDGE
        else:
          value += CATONEDGE

  return value
