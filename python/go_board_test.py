"""Tests for go_board."""
import random
import unittest

import go_board
from go_board import Color
from go_board import create_board
from go_board import format_point
from go_board import POINTS


class GoBoardTest(unittest.TestCase):

  def test_board_points(self):
    for board_size in [9, 13, 19]:
      with self.subTest(board_size=board_size):
        points = list(go_board.board_points(board_size))
        self.assertEqual(len(points), board_size * board_size)

  def test_starts_empty(self):
    for board_size in [9, 13, 19]:
      with self.subTest(board_size=board_size):
        board = go_board.GoBoard(board_size)
        for p in go_board.board_points(board_size):
          self.assertEqual(board.point_color(p), Color.EMPTY)

  def test_play_move(self):
    board = go_board.GoBoard(19)
    board.play(POINTS.D4, Color.BLACK)
    self.assertEqual(board.point_color(POINTS.D4), Color.BLACK)

  def test_is_legal_move(self):
    board = go_board.GoBoard(19)

    # Pass is always legal.
    self.assertTrue(board.is_legal_move(go_board.PASS, Color.BLACK))

    # Can play on empty.
    self.assertTrue(board.is_legal_move(POINTS.A1, Color.BLACK))

    # Can't play on top.
    board.play(POINTS.A1, Color.BLACK)
    self.assertFalse(board.is_legal_move(POINTS.A1, Color.WHITE))

  def test_is_legal_move_surrounded(self):
    board = create_board("""+++++
                            ++O++
                            +O+O+
                            ++O++
                            +++++""")

    self.assertTrue(board.is_legal_move(POINTS.C3, Color.WHITE), board)
    self.assertFalse(board.is_legal_move(POINTS.C3, Color.BLACK), board)

  def test_is_legal_move_surrounded_capture(self):
    board = create_board("""++X++
                             +XOX+
                             XO+OX
                             +XOX+
                             ++X++""")

    self.assertFalse(board.is_legal_move(POINTS.C3, Color.WHITE), board)
    self.assertTrue(board.is_legal_move(POINTS.C3, Color.BLACK), board)

  def test_is_legal_move_suicide(self):
    board = create_board("""+++XO+X+X+
                            ++XOOOOX++
                            ++XOOOX+++
                            ++XOOOX+++
                            +++XXXO+++
                            ++++++++++""")

    self.assertFalse(board.is_legal_move(POINTS.F1, Color.WHITE), board)
    self.assertTrue(board.is_legal_move(POINTS.F1, Color.BLACK), board)

  def test_is_legal_move_suicide_after_capture(self):
    board = create_board("""OOO++XO++
                            OXXOOOXX+
                            X+XO+OX++
                            ++XOOOX++
                            ++XXXXX++
                            +++++++++""")

    # Capture the white group in the corner.
    board.play(POINTS.D1, Color.BLACK)
    self.assertEqual(board.pseudo_liberty(POINTS.C1), 1)

    board.play(POINTS.B1, Color.WHITE)
    self.assertEqual(board.pseudo_liberty(POINTS.C1), 0)

    board.play(POINTS.A1, Color.BLACK)
    self.assertEqual(board.pseudo_liberty(POINTS.C1), 0)
    self.assertTrue(board.in_atari(POINTS.B1))
    self.assertFalse(board.in_atari(POINTS.D1))
    self.assertFalse(board.in_atari(POINTS.C2))
    self.assertFalse(board.is_legal_move(POINTS.C1, Color.WHITE), board)

  def test_capture_single_stone(self):
    board = create_board("""+++++
                            +OOO+
                            +OXO+
                            +O+O+
                            +++++""")

    board.play(POINTS.C4, Color.WHITE)
    self.assertEqual(board.point_color(POINTS.C3), Color.EMPTY)

  def test_capture_group(self):
    board = create_board("""OOX
                            OXX
                            OX+
                            +X+""")

    board.play(POINTS.A4, Color.BLACK)
    self.assertEqual(board.point_color(POINTS.A1), Color.EMPTY)
    self.assertEqual(board.point_color(POINTS.A2), Color.EMPTY)
    self.assertEqual(board.point_color(POINTS.A3), Color.EMPTY)

  def test_ko_legality(self):
    board = create_board("""++++++
                            ++XO++
                            +XO+O+
                            ++XO++
                            ++++++""")

    # Capturing the ko the first time is legal.
    self.assertTrue(board.is_legal_move(POINTS.D3, Color.BLACK), board)
    board.play(POINTS.D3, Color.BLACK)
    # .. but immediate recapture is not.
    self.assertFalse(board.is_legal_move(POINTS.C3, Color.WHITE), board)

    # After a move somewhere else, the ko can be retaken.
    board.play(POINTS.F16, Color.WHITE)
    self.assertTrue(board.is_legal_move(POINTS.C3, Color.WHITE), board)

  def test_zobrist_hashing(self):
    layout = """+++++++
                ++XOOX+
                ++XO+OX
                ++XOOOX
                +++XXX+"""
    a = create_board(layout)
    b = create_board(layout)

    # Different instances with the same stones should have the same hash.
    self.assertEqual(hash(a), hash(b))

    # If the stones differ, the hashes should differ.
    a.play(POINTS.Q16, Color.BLACK)
    self.assertNotEqual(hash(a), hash(b))

  def test_pseudo_liberty_count(self):
    board = create_board("""+++++
                            +XX++
                            +O+X+
                            +XX++
                            +++++""")

    # Lone stone starts out with 4 liberties.
    self.assertEqual(board.pseudo_liberty(POINTS.D3), 4)

    #  An adjacent enemy stones remove liberties..
    board.play(POINTS.C3, Color.WHITE)
    self.assertEqual(board.pseudo_liberty(POINTS.D3), 3)

    board.play(POINTS.E3, Color.WHITE)
    self.assertEqual(board.pseudo_liberty(POINTS.D3), 2)
    self.assertFalse(board.in_atari(POINTS.D3))

    #  .. but when the enemey stone is captured the liberties are returned.
    board.play(POINTS.A3, Color.BLACK)
    self.assertEqual(board.pseudo_liberty(POINTS.D3), 3)

    # And they can be taken again.
    board.play(POINTS.D2, Color.WHITE)
    self.assertEqual(board.pseudo_liberty(POINTS.D3), 2)
    self.assertFalse(board.in_atari(POINTS.D3))

  def test_random_play(self):
    for board_size in [9, 13, 19]:
      with self.subTest(board_size=board_size):
        for _ in range(2):
          board = go_board.GoBoard(board_size)
          to_play = Color.BLACK

          while True:
            # Points of the same color that neighbor each other should be in the
            # same chain.
            for p in go_board.board_points(board_size):
              if board.is_empty(p):
                continue
              for n in go_board.neighbours(p):
                if board.point_color(p) == board.point_color(n):
                  self.assertEqual(
                      format_point(board.chain_head(p)),
                      format_point(board.chain_head(n)))

            legal_moves = [
                p for p in go_board.board_points(board_size)
                if board.is_legal_move(p, to_play)
            ]
            if not legal_moves:
              break
            move = random.choice(legal_moves)
            board.play(move, to_play)
            to_play = to_play.opponent()


if __name__ == '__main__':
    unittest.main()