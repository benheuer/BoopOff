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
