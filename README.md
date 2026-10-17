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

`get_legals(self,player)`: returns placement moves as `(piece, index)`. If the player has no pieces in hand, it raises `IllegalMove`; the runner treats that unplayable turn as a draw.

`play(self,move)`: applies a placement `(piece, index)`, including boops and returning pieces pushed off the board to hand. Growth and retirement happen afterward.

`get_grows(self)` and `grow(self, growth)`: growth choices are `("grow", (a, b, c))` for three kittens, or `("remove", index)` to retire one kitten into a cat when its owner's hand is empty. Only the mover acts, once per turn, after checking for a win. The runner offers that player's line growths first, and retirement choices only when there are no line growths.

### bot.py ###

All bots created for said competition must be subclasses of the simple BoopBot abstract class included here so the competition can be run properly.

### MeowddledBOT.py ###

The random bot.

### ByteSizedBOT.py ###

A search depth one bot with really bad heuristics, baseline non-random bot.

### CatGPTBOT.py ###

`CatGPT` is a bot written by ChatGPT, hence the name. The AI chose the bot to have configurable search depths.

Use `CatGPT(search_depth=3)` to search our move, the opponent's reply, and our following move; `CatGPT()` defaults to depth 2. Growth or retirement stays part of the turn that causes it.
