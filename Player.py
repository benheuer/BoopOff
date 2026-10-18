from bot import BoopBot
from rules import IllegalMove, to_index, to_coord

class Player(BoopBot):

  def give_move(self, moves, board, player):

    print("Rows and columns are zero-indexed.")

    while True:
      try:
        row = int(input("Row: "))
        col = int(input("Column: "))
        type = int(input("Kitten (1) or cat (2): "))
        sign = 1 if player == 2 else -1
        my_move = (sign * type, to_index((row,col)))
        if not my_move in moves:
          raise IllegalMove("Attempted to make a move that did not exist.")
        return my_move
      except Exception:
        print("Please input a legal move.")

  def give_grow(self, grows, board, player):

    print("You have the following actions available:")

    choices = []

    for i in range(len(grows)):
      grow = grows[i]
      print(f"{i + 1}. ",end="")
      if grow[0] == "grow":
        a = to_coord(grow[1][0])
        b = to_coord(grow[1][1])
        c = to_coord(grow[1][2])
        print(f"You may graduate the pieces at ({a[0]},{a[1]}), ({b[0]},{b[1]}), and ({c[0]},{c[1]}).")
      elif grow[0] == "remove":
        print(f"You may remove (and graduate, if possible) the piece at {to_coord(grow[1])}.")
      choices.append((i,grow))

    choice = -100000 # Just so choice is already defined.
    
    while not choice in range(len(choices)) + 1:
      choice = int(input("Please put the number of your action: "))
    choices.sort()
    return choices[choice - 1][1]
    
