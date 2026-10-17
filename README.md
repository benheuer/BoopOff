## Purrfessor: A Boop-Playing Engine ##

GNU license. Below are laid the tools included within.

This was created for the purposes of hosting a friendly tournament between multiple of the same bot.

### rules.py ###

`class IllegalMove`: a custom class created specifically to handle moves that cannot exist/cannot be made.

The following are included in `class Board`:

A `Board` class object has a `board` property - this is formatted as six lists with six items each, each with a value `-2` to `2`. A zero indicates an absence of a piece. Negative numbers indicate blue pieces while positive numbers indicate orange. Numbers n where `|n| = 2` represent full-fledged cats, while those satisfying `|n| = 1` are kittens.

Coordinates on the board can either be expressed as an index integer `0` through `35` or a coordinate tuple `(row, col)`. Indexes are expressed as `row * 6 + col`. Functions `to_index(coord)` and `to_coord(index)` (outside Board class) convert between these values.

The object also contains a `hands` property - two two-item lists for counting kitten then cat numbers per player [blue, orange].

`__str__(self)`: Allows for printing out the board using emojis! 🟩 for `0`, 🔸 for `1`, 🔹 for `-1`, 🟧 for `2`, and 🟦 for `-2`. Prints in a 6x6 grid.

`get_legals(self,player)`: running this on a Board object will give a list of three-tuple outputs with `(piece, index, type)` for every legal move - piece indicates the played/removed piece, index indicates where on the board it goes, and type is either "place" or "remove" (NOTE: all legal moves will be of the same type).

`play(self,move)`: takes one move tuple `(piece, index, type)` and executes that move, including booping and removing to hand but excluding growth (due to factors laid out below).

`get_grows(self)` and `grow(self, indices)`: called separate from the play() function due to the potential choosing between two grow actions.

### bot.py ###

All bots created for said competition must be subclasses of the simple BoopBot abstract class included here so the competition can be run properly.

### CatGPTBOT.py ###

`CatGPT` is a bot written with descriptive names and comments for programmers
who are learning Python. It uses the existing game rules and needs no extra
packages.

To play against it, run:

```sh
python3 main.py
```

Choose **CatGPT** for either Blue or Orange in the bot menu.

Set the search depth when creating a bot:

```python
from CatGPTBOT import CatGPT

quick_bot = CatGPT(search_depth=1)  # Our move only.
normal_bot = CatGPT()              # Default: our move and their reply.
deeper_bot = CatGPT(search_depth=3) # Our move, their reply, our next move.
```

The depth must be a positive integer. Each level counts one player's turn,
including any growth from that turn. Growing does not use another level.
Higher depths examine many more possibilities and take longer to choose
a move. The game menu creates `CatGPT()`, using the default depth of 2.

With the default depth of 2, CatGPT chooses its moves in three steps:

1. Try each legal move on a copy of the board, including any growth choices.
2. Check what the opponent could do on their next turn. Assume they will
   choose the result that is worst for CatGPT.
3. Pick the move with the best result after that opponent reply.

A win gets a very large score. Other positions earn points for cats,
pieces near the center, and pairs that could become three in a row.
These point values are estimates, so searching more turns does not
guarantee a win.

The bot checks for wins before growth and lets only the moving player
grow once, matching the game runner. It handles both colors and the
removal moves needed when a player's hand is empty. It leaves the
supplied boards and move lists unchanged.

To run the tests:

```sh
python3 -B -m unittest discover -v
```
