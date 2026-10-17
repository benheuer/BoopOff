"""Tactical and runner integration tests; no third-party dependencies."""

import copy
import unittest

from bot import BoopBot
from main import BOTS
from CatGPTBOT import CatGPT
from rules import Board


def position(pieces=(), hands=None):
    cells = [[0] * 6 for _ in range(6)]
    for row, col, piece in pieces:
        cells[row][col] = piece
    return Board(cells, hands if hands is not None else [[8, 0], [8, 0]])


def can_win_next(board, player):
    """Independent one-turn oracle using the actual rules engine.

    Growth cannot create a terminal position: it only removes kittens and
    returns cats to hand, and the runner checks for a win before growing.
    """
    for move in board.get_legals(player):
        state = copy.deepcopy(board)
        state.play(move)
        if state.is_terminal() == player:
            return True
    return False


def can_grow_next(board, player):
    """Check whether any legal move can grow our kittens on the next turn."""
    kitten = -1 if player == 1 else 1
    for move in board.get_legals(player):
        next_board = copy.deepcopy(board)
        next_board.play(move)
        for grow in next_board.get_grows():
            row, column = divmod(grow[0], 6)
            if next_board.board[row][column] == kitten:
                return True
    return False


class CatGPTTests(unittest.TestCase):
    def setUp(self):
        self.bot = CatGPT()

    def test_registered_as_a_boop_bot(self):
        self.assertIsInstance(self.bot, BoopBot)
        self.assertIs(BOTS["CatGPT"], CatGPT)

    def test_opening_is_legal_deterministic_and_does_not_mutate_inputs(self):
        for player in (1, 2):
            with self.subTest(player=player):
                board = position()
                moves = board.get_legals(player)
                before = copy.deepcopy((board.board, board.hands, moves))
                move = self.bot.give_move(moves, board, player)
                self.assertIn(move, moves)
                self.assertEqual(move, self.bot.give_move(moves, board, player))
                self.assertEqual((board.board, board.hands, moves), before)

    def test_takes_immediate_cat_line_win_for_both_colors(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[8, 0], [8, 0]]
                hands[player - 1] = [4, 1]
                board = position([
                    (2, 0, sign), (2, 1, 2 * sign), (2, 2, 2 * sign)
                ], hands)
                move = self.bot.give_move(board.get_legals(player), board, player)
                board.play(move)
                self.assertEqual(board.is_terminal(), player)

    def test_blocks_an_opponent_win_for_both_colors(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                opponent = 3 - player
                hands = [[7, 1], [7, 1]]
                hands[opponent - 1] = [4, 1]
                board = position([
                    (2, 0, -sign), (2, 1, -2 * sign), (2, 2, -2 * sign)
                ], hands)
                self.assertTrue(can_win_next(board, opponent))
                move = self.bot.give_move(board.get_legals(player), board, player)
                board.play(move)
                self.assertFalse(can_win_next(board, opponent))

    def test_wins_by_deploying_eighth_cat(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[8, 0], [8, 0]]
                hands[player - 1] = [0, 1]
                coords = [(0, 0), (0, 2), (0, 4), (2, 0),
                          (2, 2), (2, 4), (4, 1)]
                board = position([(r, c, 2 * sign) for r, c in coords], hands)
                self.assertEqual(board.is_terminal(), 0)
                move = self.bot.give_move(board.get_legals(player), board, player)
                board.play(move)
                self.assertEqual(board.is_terminal(), player)

    def test_growth_keeps_the_kitten_blocking_an_opponent_cat_line(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[4, 1], [4, 1]]
                hands[player - 1] = [4, 0]
                board = position(
                    [(2, col, sign) for col in range(4)] +
                    [(3, 3, -2 * sign), (4, 3, -2 * sign), (5, 3, -sign)],
                    hands,
                )
                grows = board.get_grows()
                self.assertEqual(len(grows), 2)
                before = copy.deepcopy((board.board, board.hands, grows))
                grow = self.bot.give_grow(grows, board, player)
                self.assertIn(grow, grows)
                self.assertEqual(grow, (12, 13, 14))
                self.assertEqual((board.board, board.hands, grows), before)
                board.grow(grow)
                self.assertFalse(can_win_next(board, 3 - player))

    def test_empty_hand_returns_a_legal_removal(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[8, 0], [8, 0]]
                hands[player - 1] = [0, 0]
                coords = [(0, 0), (0, 2), (0, 4), (2, 0),
                          (2, 2), (2, 4), (4, 1), (4, 4)]
                board = position([(r, c, sign) for r, c in coords], hands)
                moves = board.get_legals(player)
                before = copy.deepcopy((board.board, board.hands))
                move = self.bot.give_move(moves, board, player)
                self.assertIn(move, moves)
                self.assertEqual(move[2], "remove")
                self.assertEqual((board.board, board.hands), before)
                board.play(move)
                self.assertEqual(board.hands[player - 1], [0, 1])

    def test_constructor_accepts_positive_integer_depths(self):
        self.assertEqual(CatGPT().search_depth, 2)
        self.assertEqual(CatGPT(1).search_depth, 1)
        self.assertEqual(CatGPT(search_depth=3).search_depth, 3)

    def test_constructor_rejects_invalid_depths(self):
        for depth in (0, -1, 1.5, 2.0, "3", None, True, False):
            with self.subTest(depth=depth):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    CatGPT(search_depth=depth)

    def test_depth_one_returns_a_legal_move_without_changing_inputs(self):
        for player in (1, 2):
            with self.subTest(player=player):
                board = position()
                moves = board.get_legals(player)
                before = copy.deepcopy((board.board, board.hands, moves))
                move = CatGPT(search_depth=1).give_move(moves, board, player)
                self.assertIn(move, moves)
                self.assertEqual((board.board, board.hands, moves), before)

    def test_depth_three_finds_growth_on_our_following_turn(self):
        # Both hands are empty, so each player must remove a piece first.
        # Removing one particular cat now lets us grow kittens when that
        # cat is played again on our next turn, whatever the opponent removes.
        cells = [
            [0, 1, 0, 2, 1, 0],
            [-1, 0, -1, -2, 0, 0],
            [1, 0, 0, 0, -1, 0],
            [2, 0, 0, 0, 1, -1],
            [-1, 0, 0, -1, 0, 1],
            [0, 0, -2, 1, 0, 0],
        ]

        for player in (1, 2):
            with self.subTest(player=player):
                board = Board(copy.deepcopy(cells), [[0, 0], [0, 0]])
                if player == 2:
                    for row in range(6):
                        for column in range(6):
                            board.board[row][column] *= -1

                moves = board.get_legals(player)
                before = copy.deepcopy((board.board, board.hands, moves))
                shallow_move = CatGPT(2).give_move(moves, board, player)
                deep_move = CatGPT(3).give_move(moves, board, player)

                self.assertIn(deep_move, moves)
                self.assertNotEqual(deep_move, shallow_move)
                self.assertEqual((board.board, board.hands, moves), before)

                for move, should_guarantee_growth in (
                    (shallow_move, False), (deep_move, True)
                ):
                    after_move = copy.deepcopy(board)
                    after_move.play(move)
                    growth_is_guaranteed = True

                    for reply in after_move.get_legals(3 - player):
                        after_reply = copy.deepcopy(after_move)
                        after_reply.play(reply)
                        if not can_grow_next(after_reply, player):
                            growth_is_guaranteed = False

                    self.assertEqual(growth_is_guaranteed, should_guarantee_growth)

    def test_growth_choices_work_at_depth_one_and_three(self):
        for depth in (1, 3):
            for player, sign in ((1, -1), (2, 1)):
                with self.subTest(depth=depth, player=player):
                    hands = [[4, 1], [4, 1]]
                    hands[player - 1] = [4, 0]
                    board = position(
                        [(2, column, sign) for column in range(4)] +
                        [(3, 3, -2 * sign), (4, 3, -2 * sign), (5, 3, -sign)],
                        hands,
                    )
                    grows = board.get_grows()
                    before = copy.deepcopy((board.board, board.hands, grows))
                    grow = CatGPT(depth).give_grow(grows, board, player)
                    self.assertIn(grow, grows)
                    self.assertEqual((board.board, board.hands, grows), before)
                    board.grow(grow)
                    self.assertFalse(can_win_next(board, 3 - player))

    def test_empty_choices_have_clear_errors(self):
        board = position()
        with self.assertRaises(ValueError):
            self.bot.give_move([], board, 1)
        with self.assertRaises(ValueError):
            self.bot.give_grow([], board, 1)


if __name__ == "__main__":
    unittest.main()
