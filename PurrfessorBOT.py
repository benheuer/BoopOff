from bot import BoopBot
from rules import Board, get_lines, to_coord, IllegalMove

class Purrfessor(BoopBot):

  def give_move(self, moves, board, player): ### Simulates every possible three move outcome
    min_score = float('-inf')

    for move in moves:
      state = copy_board(board)
      state.play(move)
      over = finish_turn(state, player)
      values = []

      replies = []
      if not over:
        try:
          replies = state.get_legals(3 - player)
        except IllegalMove: # The opponent has no piece left to play
          replies = []

      for after in replies:
        substate = copy_board(state)
        substate.play(after)
        over = finish_turn(substate, 3 - player)
        subvalues = []

        lasts = []
        if not over:
          try:
            lasts = substate.get_legals(player)
          except IllegalMove: # We have no piece left to play
            lasts = []

        for last in lasts:
          sub2state = copy_board(substate)
          sub2state.play(last)
          finish_turn(sub2state, player)

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

    best = grows[0]
    best_score = float('-inf')

    for grow in grows:
      after = copy_board(board)
      after.grow(grow)
      score = evaluate(after, player)
      if score > best_score:
        best_score = score
        best = grow

    return best

### Finishing a turn in the search (same rules as main.py) ###

def own_growths(board, player):
  # get_grows() lists both colours, so keep only this player's.
  # A line to graduate comes first; a removal is only offered when there is no line.
  sign = -1 if player == 1 else 1
  lines, removes = [], []

  for g in board.get_grows():
    index = g[1][0] if g[0] == "grow" else g[1]
    row, col = to_coord(index)
    if board.board[row][col] * sign <= 0:
      continue
    if g[0] == "grow":
      lines.append(g)
    else:
      removes.append(g)

  return lines or removes

def finish_turn(board, player):
  # Applies the mover's graduation or removal after a placement. Returns True if the game is over.
  if board.is_terminal():
    return True

  growths = own_growths(board, player)
  if growths:
    board.grow(growths[0])  # Just takes the first option while searching, to keep it quick

  return False

### Value Outputs for Each Situation ###

CATONEDGE = 1
WIN = 1000000000000000000000000000000
TWOBYTWO = 15
TWOSEP = 10
THREEROW = 25
CATSINHAND = 7
OPPCATSINHAND = 5
MYPIECEONBOARD = 4
OPPPIECEONBOARD = 2

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
    if (a == b and b == c) and abs(a) >= 1:
      if play_sign == sign(a):
        value += THREEROW
      else:
        value -= THREEROW
    elif (a == b) or (b == c):
      if play_sign == sign(b):
        value += TWOBYTWO * abs(b)
      else:
        value -= TWOBYTWO * abs(b)
    elif (a == c) and a != 0 and b == 0:
      if play_sign == sign(a):
        value += TWOSEP * abs(a)
      else:
        value -= TWOSEP * abs(a)
    

  for row in range(6):
    for col in range(6):
      if (row in [0,5] or col in [0,5]) and (pos[row][col] != 0): # Small boosts for pieces on edge
        if play_sign == sign(pos[row][col]):
          value -= CATONEDGE
        else:
          value += CATONEDGE

  value += board.hands[player - 1][1] * CATSINHAND
  value -= board.hands[2 - player][1] * OPPCATSINHAND

  for row in board.board:
    for col in row:
      if col != 0 and sign(col) == play_sign:
        value += MYPIECEONBOARD * abs(col)
      elif col != 0 and sign(col) != play_sign:
        value -= OPPPIECEONBOARD * abs(col)


  return value
