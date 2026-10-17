class IllegalMove(Exception):
  pass

class Board:
  
  def __init__(self, board, hands):

    # board is a 6x6 nested list
    self.board = board

    # 2 lists with 2 elements, 0-8 -> [[blue_kit,_blue_cat],[orange_kit,orange_cat]]
    self.hands = hands
    
  @property
  def board(self):
    return self._board
  
  @property
  def hands(self):
    return self._hands

  @board.setter
  def board(self,board):
    if len({len(row) for row in board}) != 1:
      raise ValueError("Board must be square.")
    if len(board[0]) != 6:
      raise ValueError("Only 6x6 boards are supported.")
    self._board = board
  
  @hands.setter
  def hands(self,hands):
    if (len(hands[0]) - len(hands[1]) != 0) or (len(hands[0]) != 2) or (len(hands) != 2):
      raise ValueError("There must be two hands with two resource types.")
    if (hands[0][0] + hands[0][1] > 8) or (hands[1][0] + hands[1][1] > 8):
      raise ValueError("Too many resources in hand.")
    self._hands = hands

  def __str__(self):
    result = ""
    
    for i in self.board:
      for j in i:
        if j == 1:
          result += "🔸"
        elif j == -1:
          result += "🔹"
        elif j == 2:
          result += "🟧"
        elif j == -2:
          result += "🟦"
        else:
          result += "🟩"
      result += "\n"
      
    return result
  
  def play(self, move): # Move tuples are expressed as (piece, index) with piece as -2,-1,1,2 and index 0-35
    piece = move[0]
    row, col = to_coord(move[1])
    player = 1 if (piece > 0) - (piece < 0) == -1 else 2

    if self.board[row][col] != 0:
      raise IllegalMove("Cannot place a piece where a piece already exists.")
    
    if not (self.hands[player - 1][abs(piece) - 1] > 0):
      raise IllegalMove("Cannot place a piece that does not exist.")

    self.board[row][col] = piece
    self.hands[player - 1][abs(piece) - 1] -= 1

    #Boop logic

    directions = [-1,0,1]

    for i in directions:
      for j in directions:

        if i == 0 and j == 0:
              continue

        nr, nc = row + i, col + j
        if not (0 <= nr <= 5 and 0 <= nc <= 5):
          continue

        neighbor = self.board[nr][nc]

        if neighbor == 0 or abs(piece) < abs(neighbor):
          continue

        dr, dc = row + 2*i, col + 2*j

        if 0 <= dr <= 5 and 0 <= dc <= 5:
          if self.board[dr][dc] == 0:
            self.board[dr][dc] = neighbor
            self.board[nr][nc] = 0

        else:
          owner = 0 if neighbor < 0 else 1
          self.hands[owner][abs(neighbor) - 1] += 1
          self.board[nr][nc] = 0

  def is_terminal(self):
    lines = get_lines()

    for line in lines:
      check = set()
      for index in line:
        row, col = to_coord(index)
        check.add(self.board[row][col])
      if len(check) == 1 and abs(next(iter(check))) == 2:
        return 1 if next(iter(check)) < 0 else 2

    for player, cat in ((1, -2), (2, 2)):
      if sum(row.count(cat) for row in self.board) == 8:
        return player
    
    return 0

  def get_grows(self):

    lines = get_lines()
    result = []

    for line in lines:
      check = []
      for index in line:
        row, col = to_coord(index)
        check.append(self.board[row][col])
      if (check[0] < 0 and check[1] < 0 and check[2] < 0) or (check[0] > 0 and check[1] > 0 and check[2] > 0):
        result.append(("grow", line))

    for player in [1,2]:
      kitten = -1 if player == 1 else 1
      hand = self.hands[player - 1]

      if hand[0] + hand[1] == 0:
        for row in range(6):
          for col in range(6):
            if self.board[row][col] == kitten:
              result.append(("remove", to_index((row,col))))

    return result

  def grow(self, growth): # takes one of the choices from get_grows(): ("grow", (a,b,c)) or ("remove", index)

    if growth[0] == "grow":
      indices = tuple(sorted(growth[1]))
      if indices not in get_lines():
        raise IllegalMove("The provided growth action is not a line of three.")
      check = []
      for index in indices:
        row, col = to_coord(index)
        check.append(self.board[row][col])
      if not (check[0] < 0 and check[1] < 0 and check[2] < 0) or not (check[0] > 0 and check[1] > 0 and check[2] > 0):
        raise IllegalMove("The chosen pieces are not all of the same player.")
      for index in indices:
        row, col = to_coord(index)
        owner = 0 if self.board[row][col] < 0 else 1
        self.hands[owner][1] += 1
        self.board[row][col] = 0

    elif growth[0] == "remove":

      row, col = to_coord(growth[1])
      removed = self.board[row][col]

      if abs(removed) != 1:
        raise IllegalMove("There is no kitten to remove at that index")

      owner = 0 if removed < 0 else 1
      if self.hands[owner][0] + self.hands[owner][1] != 0:
        raise IllegalMove("A kitten can only be removed when there are no pieces left in hand")

      self.hands[owner][1] += 1

      self.board[row][col] = 0

    else:
      raise IllegalMove("Unknown growth type.")

  def get_legals(self, player):
    if player not in (1, 2):
        raise ValueError("Player must be 1 (blue) or 2 (orange).")

    result = []
    hand = self.hands[player - 1]
    sign = -1 if player == 1 else 1
    
    if self.hands[player - 1][0] + self.hands[player - 1][1] > 0:

      for row in range(6):
          for col in range(6):
              if self.board[row][col] != 0:
                  continue

              for piece_type, count in enumerate(hand, start=1):
                  if count > 0:
                      result.append((sign * piece_type, to_index((row, col))))
    else:
      raise IllegalMove("Cannot play a piece")
    
    return result


# Coord is a tuple of (row, col), index from 0-35 (rows/cols from 0-5)

def to_index(coord): 
  return coord[0] * 6 + coord[1]

def to_coord(index):
  return (index // 6,index % 6)

def get_lines():
  lines = []

  for row in range(6):
      for col in range(4):
          lines.append((to_index((row, col)), to_index((row, col + 1)), to_index((row, col + 2))))
          
  for row in range(4):
      for col in range(6):
          lines.append((to_index((row, col)), to_index((row + 1, col)), to_index((row + 2, col))))
          
  for row in range(4):
      for col in range(4):
          lines.append((to_index((row, col)), to_index((row + 1, col + 1)), to_index((row + 2, col + 2))))
          
  for row in range(4):
      for col in range(2, 6):
          lines.append((to_index((row, col)), to_index((row + 1, col - 1)), to_index((row + 2, col - 2))))

  return lines
