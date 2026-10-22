from bot import BoopBot
from rules import Board, get_lines, to_coord, IllegalMove
from random import shuffle

class Purrfessor(BoopBot):

    def give_move(self, moves, board, player):
        moves = list(moves)
        shuffle(moves)
        min_score = float('-inf')
        best = moves[0]
    
        for _, move, state in ranked(board, moves, player, player, True):
          winner = state.is_terminal()
          if winner == player:
            return move
          if winner:
            continue
          values = []
    
          try:
            replies = state.get_legals(3 - player)
          except IllegalMove:
            replies = []
    
          for _, after, substate in ranked(state, replies, 3 - player, player, False):
            subvalues = []
            lasts = []
            if not substate.is_terminal():
              try:
                lasts = substate.get_legals(player)
              except IllegalMove:
                lasts = []
    
            for last in lasts:
              sub2state = copy_board(substate)
              sub2state.play(last)
              finish_turn(sub2state, player)
              v = evaluate(sub2state, player)
              subvalues.append(v)
              if values and v >= min(values):   # the cutoff from #1
                break
    
            values.append(max(subvalues) if subvalues else evaluate(substate, player))
            if values[-1] <= min_score:
              break
    
          if not values:
            values.append(evaluate(state, player))
          if min(values) > min_score:
            min_score = min(values)
            best = move
    
        return best

    def give_grow(self, grows, board, player): # mini one-depth search (big search above will handle win lines and such)

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

def own_growths(board, player):
  # get_grows() lists both colors, so keep only this player's.
  # We want to grow 3 over growing 1 (usually, hopefully)
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

def ranked(state, moves, mover, me, best_first): # A little thing that helps my code find the better replies first so it can cut bad ones early. Runs all the necesary updates to the board, so that shortened my code a bit above in give_move()
  scored = []
  for m in moves:
    s = copy_board(state)
    s.play(m)
    finish_turn(s, mover)
    scored.append((evaluate(s, me), m, s))
  scored.sort(key=lambda t: t[0], reverse=best_first)   # key= so boards never get compared
  return scored

def finish_turn(board, player):
  # Applies the mover's graduation or removal after a placement. Returns True if the game is over.
  if board.is_terminal():
    return True

  growths = own_growths(board, player)
  if growths:
    board.grow(growths[0])  # Just takes the first option while searching, to keep it quick

  return False

### Value Outputs for Each Situation ###

WIN = 1000000000000000000000000000000
TWOBYTWO = 15
TWOSEP = 8
THREEROW = 20
CATS = 30
OPPCATSINHAND = 9
KITTENS = 5
OPPPIECEONBOARD = 5

LINES = get_lines()
LINE_IDX = [tuple(l) for l in LINES]   # flat indices (row*6+col), computed once
RING = [min(i // 6, 5 - i // 6, i % 6, 5 - i % 6) for i in range(36)] # Reads the board and assigns values to the different rings
RING_VALUE = {0: -1, 1: 0, 2: 1} # <- point values for the rings

def copy_board(b):
  return Board([row[:] for row in b.board], [h[:] for h in b.hands])

def evaluate(board,player):

  flat = [x for row in board.board for x in row]   # flatten the board once
  value = 0
  play_sign = 1 if player == 2 else -1

  for i, j, k in LINE_IDX:
    a = flat[i]
    b = flat[j]
    c = flat[k]

    if a == b and b == c:
      if a == 0:
        continue
      mine = (a > 0) == (play_sign > 0)
      if abs(a) == 2:
        value += WIN if mine else -WIN
      value += THREEROW if mine else -THREEROW
    elif a == b or b == c:
      if b != 0:
        if (b > 0) == (play_sign > 0):
          value += TWOBYTWO * abs(b)
        else:
          value -= TWOBYTWO * abs(b)
    elif a == c and a != 0 and b == 0:
      if (a > 0) == (play_sign > 0):
        value += TWOSEP * abs(a)
      else:
        value -= TWOSEP * abs(a)

  for index, x in enumerate(flat):
    if x == 0:
      continue
    mine = (x > 0) == (play_sign > 0)
    r = RING_VALUE[RING[index]]
    value += r if mine else -r
    if mine:
      value += CATS if abs(x) == 2 else KITTENS
    else:
      value -= OPPPIECEONBOARD * abs(x)

  value += board.hands[player - 1][1] * CATS
  value -= board.hands[2 - player][1] * OPPCATSINHAND

  return value
