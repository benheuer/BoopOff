"""Check that bot simulations agree with the updated Boop rules."""

import copy
import unittest

from CatGPTBOT import CatGPT, WIN_SCORE
from main import own_grows
from rules import Board, IllegalMove


def make_board(pieces, player=1, hand=None):
    """Describe our pieces with positive numbers, then choose their color."""
    cells = [[0] * 6 for _ in range(6)]
    sign = -1 if player == 1 else 1
    for row, column, piece in pieces:
        cells[row][column] = sign * piece

    hands = [[8, 0], [8, 0]]
    if hand is not None:
        hands[player - 1] = hand[:]
    return Board(cells, hands)


def snapshot(board):
    """Save the board and hands so we can check that inputs stay unchanged."""
    return copy.deepcopy((board.board, board.hands))


class RuleUpdateTests(unittest.TestCase):
    def test_two_item_moves_work_at_each_search_depth(self):
        for player, sign in ((1, -1), (2, 1)):
            for depth in (1, 2, 3):
                with self.subTest(player=player, depth=depth):
                    board = make_board([], player)
                    move = (sign, 14)
                    moves = [move]
                    before = snapshot(board)
                    self.assertIn(move, board.get_legals(player))
                    self.assertEqual(
                        CatGPT(depth).give_move(moves, board, player), move
                    )
                    self.assertEqual(snapshot(board), before)
                    self.assertEqual(moves, [move])

    def test_search_applies_a_tagged_line_growth(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                board = make_board(
                    [(2, 0, 2), (2, 1, 1), (2, 2, 1)],
                    player, [5, 0],
                )
                before = snapshot(board)
                outcomes = CatGPT()._finish_move(board, (sign, 15), player)
                self.assertEqual(len(outcomes), 1)
                after = outcomes[0]
                self.assertEqual(after.hands[player - 1], [4, 3])
                self.assertEqual(after.board[2], [2 * sign, 0, 0, 0, 0, 0])
                self.assertEqual(after.hands[2 - player], [8, 0])
                self.assertEqual(snapshot(board), before)

    def test_a_line_created_for_the_opponent_does_not_grow(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                # Our placement pushes the opponent's kitten from (1, 3)
                # to (2, 3), completing their line during our turn.
                board = make_board(
                    [(2, 1, -1), (2, 2, -1), (1, 3, -1)], player
                )
                board.hands[2 - player] = [5, 0]
                after = CatGPT()._finish_move(board, (sign, 3), player)[0]
                self.assertEqual(
                    after.board[2][1:4], [-sign, -sign, -sign]
                )
                self.assertEqual(after.hands[2 - player], [5, 0])
                self.assertEqual(own_grows(after, player), [])

    def test_line_growth_has_priority_over_retirement(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                pieces = [(2, 0, 1), (2, 1, 1), (2, 2, 1),
                          (0, 0, 1), (0, 2, 1), (0, 4, 1), (4, 4, 1)]
                board = make_board(pieces, player, [1, 0])
                placed = copy.deepcopy(board)
                placed.play((sign, 15))

                # The raw rules list contains both types. The runner offers
                # only the two lines, and the search must do the same.
                self.assertTrue(
                    any(choice[0] == "remove" for choice in placed.get_grows())
                )
                choices = own_grows(placed, player)
                self.assertEqual(len(choices), 2)
                self.assertTrue(all(choice[0] == "grow" for choice in choices))

                expected = []
                for choice in choices:
                    grown = copy.deepcopy(placed)
                    grown.grow(choice)
                    expected.append(snapshot(grown))

                outcomes = CatGPT()._finish_move(board, (sign, 15), player)
                self.assertEqual(len(outcomes), 2)
                self.assertCountEqual(
                    [snapshot(outcome) for outcome in outcomes], expected
                )
                for outcome in outcomes:
                    self.assertEqual(outcome.hands[player - 1], [0, 3])

    def test_last_kitten_placement_retires_one_kitten_immediately(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                coordinates = [(0, 0), (0, 2), (0, 4), (2, 0),
                               (2, 2), (2, 4), (4, 1)]
                pieces = [(row, column, 1) for row, column in coordinates]
                board = make_board(pieces, player, [1, 0])
                before = snapshot(board)
                outcomes = CatGPT()._finish_move(board, (sign, 28), player)

                self.assertEqual(len(outcomes), 8)
                self.assertEqual(snapshot(board), before)
                for outcome in outcomes:
                    self.assertEqual(outcome.hands[player - 1], [0, 1])
                    kitten_count = sum(row.count(sign) for row in outcome.board)
                    self.assertEqual(kitten_count, 7)
                    self.assertTrue(outcome.get_legals(player))

    def test_retirement_never_removes_a_cat(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                pieces = [(0, 0, 1), (0, 2, 2), (0, 4, 2), (2, 0, 2),
                          (2, 2, 2), (2, 4, 2), (4, 1, 2)]
                board = make_board(pieces, player, [0, 1])
                outcomes = CatGPT()._finish_move(board, (2 * sign, 28), player)
                self.assertEqual(len(outcomes), 1)
                after = outcomes[0]
                self.assertEqual(after.board[0][0], 0)
                self.assertEqual(after.hands[player - 1], [0, 1])
                cat_count = sum(row.count(2 * sign) for row in after.board)
                self.assertEqual(cat_count, 7)

    def test_a_win_ends_the_turn_before_growth(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                pieces = [(0, 0, 1), (0, 1, 1), (0, 2, 1),
                          (3, 0, 1), (3, 1, 2), (3, 2, 2)]
                board = make_board(pieces, player, [1, 1])
                after = CatGPT()._finish_move(board, (2 * sign, 21), player)[0]
                self.assertEqual(after.is_terminal(), player)
                self.assertEqual(after.board[0][0:3], [sign, sign, sign])
                self.assertEqual(after.hands[player - 1], [1, 0])

    def test_eight_cats_win_before_the_empty_hand_draw_check(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                coordinates = [(0, 0), (0, 2), (0, 4), (2, 0),
                               (2, 2), (2, 4), (4, 1)]
                pieces = [(row, column, 2) for row, column in coordinates]
                board = make_board(pieces, player, [0, 1])
                after = CatGPT()._finish_move(board, (2 * sign, 28), player)[0]
                self.assertEqual(after.is_terminal(), player)
                self.assertEqual(after.hands[player - 1], [0, 0])
                score = CatGPT()._search(
                    after, 2, player, player, float("-inf"), float("inf")
                )
                self.assertEqual(score, WIN_SCORE)

    def test_tagged_growth_callback_is_legal_at_each_depth(self):
        for player, sign in ((1, -1), (2, 1)):
            for depth in (1, 2, 3):
                with self.subTest(player=player, depth=depth):
                    board = make_board(
                        [(2, column, 1) for column in range(4)],
                        player, [4, 0],
                    )
                    choices = own_grows(board, player)
                    before = snapshot(board)
                    choices_before = copy.deepcopy(choices)
                    choice = CatGPT(depth).give_grow(choices, board, player)
                    self.assertIn(choice, choices)
                    self.assertEqual(snapshot(board), before)
                    self.assertEqual(choices, choices_before)
                    board.grow(choice)
                    self.assertEqual(board.hands[player - 1], [4, 3])

    def test_tagged_retirement_callback_keeps_its_type(self):
        for player in (1, 2):
            with self.subTest(player=player):
                pieces = [(0, 0, 1), (0, 2, 2), (0, 4, 2), (2, 0, 2),
                          (2, 2, 2), (2, 4, 2), (4, 1, 2), (4, 4, 2)]
                board = make_board(pieces, player, [0, 0])
                choices = own_grows(board, player)
                before = snapshot(board)
                choice = CatGPT(3).give_grow(choices, board, player)
                self.assertEqual(choice, ("remove", 0))
                self.assertEqual(snapshot(board), before)
                board.grow(choice)
                self.assertEqual(board.hands[player - 1], [0, 1])

    def test_an_unplayable_turn_is_a_draw_even_at_the_search_limit(self):
        coordinates = [(0, 0), (0, 2), (0, 4), (2, 0),
                       (2, 2), (2, 4), (4, 1), (4, 4)]
        for player in (1, 2):
            for turns_left in (0, 2):
                with self.subTest(player=player, turns_left=turns_left):
                    pieces = [(row, column, 1) for row, column in coordinates]
                    board = make_board(pieces, player, [0, 0])
                    self.assertEqual(board.is_terminal(), 0)
                    with self.assertRaises(IllegalMove):
                        board.get_legals(player)
                    before = snapshot(board)
                    score = CatGPT()._search(
                        board, turns_left, player, player,
                        float("-inf"), float("inf"),
                    )
                    self.assertEqual(score, 0)
                    self.assertEqual(snapshot(board), before)

if __name__ == "__main__":
    unittest.main()
