from bot import BoopBot
from rules import Board, get_lines, to_coord, IllegalMove
from random import choice

class Purrfessor(BoopBot):

  def give_move(self, moves, board, player): ### Simulates every possible three move outcome
    min_score = float('-inf')

    for move in moves:
      state = copy_board(board)
      state.play(move)
      values = []

      try:
        replies = state.get_legals(3 - player)
      except IllegalMove: # The opponent has no piece left to play
        replies = []

      for after in replies:
        substate = copy_board(state)
        substate.play(after)
        subvalues = []

        try:
          lasts = substate.get_legals(player)
        except IllegalMove: # We have no piece left to play (we have not simulated the removal yet)
          lasts = []

        for last in lasts:
          sub2state = copy_board(substate)
          sub2state.play(last)
          subvalues.append(evaluate(sub2state,player))

        if subvalues:
          values.append(max(subvalues))
        else:
          values.append(evaluate(substate,player))

        if values[-1] <= min_score:
          break

      if not values:
        values.append(evaluate(state,player))

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

LINES = get_lines()

def copy_board(b):
  return Board([row[:] for row in b.board], [h[:] for h in b.hands])

def evaluate(board,player):

  pos = board.board
  value = 0
  play_sign = 1 if player == 2 else -1

  def sign(n):
    return (n > 0) - (n < 0)

  for line in LINES:
    a = pos[to_coord(line[0])[0]][to_coord(line[0])[1]]
    b = pos[to_coord(line[1])[0]][to_coord(line[1])[1]]
    c = pos[to_coord(line[2])[0]][to_coord(line[2])[1]]

    if (a == b and b == c) and abs(a) == 2:
      if play_sign == sign(a):
        value += WIN
      else:
        value -= WIN

  for row in range(6):
    for col in range(6):
      if (row in [0,5] or col in [0,5]) and (pos[row][col] != 0): # Small boosts for pieces on edge
        if play_sign == sign(pos[row][col]):
          value -= CATONEDGE
        else:
          value += CATONEDGE

  return value
