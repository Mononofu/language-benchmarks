"""Benchmarks for GoBoard."""
import random
import timeit
from typing import Sequence, Text, Tuple

import go_board
from go_board import Color

def random_board(
    fill_fraction: float,
    board_size: int) -> Tuple[go_board.GoBoard, Sequence[go_board.Point]]:
  """Creates a randomly filled board."""
  assert fill_fraction >= 0 and fill_fraction <= 1

  board = go_board.GoBoard(board_size)
  move_history = []
  to_play = go_board.Color.BLACK

  for _ in range(int(board_size**2 * fill_fraction)):
    legal_moves = [
        p for p in go_board.board_points(board_size)
        if board.is_legal_move(p, to_play)
    ]
    if not legal_moves:
      return (board, move_history)

    move = random.choice(legal_moves)
    board.play(move, to_play)
    to_play = to_play.opponent()
    move_history.append(move)

  return (board, move_history)


def format_duration(seconds: float) -> Text:
  if seconds > 1:
    return f'{seconds:.2f}s'
  elif seconds > 1e-3:
    return f'{seconds * 1e3:.2f}ms'
  elif seconds > 1e-6:
    return f'{seconds * 1e6:.2f}us'
  else:
    return f'{seconds * 1e9:.2f}ns'


_BOARD_SIZE = 19


class PlayUndo:
  """Plays a single move on a freshly copied board."""

  def __init__(self):
    self._board = random_board(0.8, _BOARD_SIZE)[0]

    for p in go_board.board_points(_BOARD_SIZE):
      if self._board.is_legal_move(p, Color.BLACK):
        self._move = p
        break

  def __call__(self):
    scratch = self._board.clone()
    scratch.play(self._move, Color.BLACK)
    assert scratch.point_color(self._move) == Color.BLACK


class PlayUndoLargeCapture:
  """Plays a single move on a freshly copied board."""

  def __init__(self):
    self._board = go_board.create_board("""OOOXX+XOOOOX+
                                           OOOOXXXOOOOX+
                                           OOXO+OOOOOOX+
                                           OXXXXXXOOOOX+
                                           X+++++XOOOOX+
                                           ++++++XXXXXX+
                                           +++++++++++++""")

  def __call__(self):
    scratch = self._board.clone()
    scratch.play(go_board.POINTS.E3, Color.BLACK)
    assert scratch.point_color(go_board.POINTS.E3) == Color.BLACK


class Play:
  """Plays out an entire game."""

  def __init__(self):
    self._history = random_board(1, _BOARD_SIZE)[1]
    self._i = 0
    self._board = go_board.GoBoard(_BOARD_SIZE)

  def __call__(self):
    if self._i >= len(self._history):
      self._i = 0
      self._board = go_board.GoBoard(_BOARD_SIZE)

    self._board.play(self._history[self._i],
                     Color.BLACK if self._i % 2 == 0 else Color.WHITE)
    self._i += 1


class Copy:

  def __init__(self):
    self._board = random_board(1, _BOARD_SIZE)[0]

  def __call__(self):
    scratch = self._board.clone()
    assert hash(scratch) == hash(self._board)


class NoOp:
  """No-op benchmark to check the measurement overhead."""

  def __init__(self):
    pass

  def __call__(self):
    pass


def main():
  benchmarks = [NoOp(), PlayUndo(), PlayUndoLargeCapture(), Play(), Copy()]
  for benchmark in benchmarks:
    print(benchmark.__class__.__name__)

    timer = timeit.Timer(benchmark)
    n, n_time = timer.autorange()
    # Aim for 1s per repetition.
    n = int(n / n_time)
    print('running for', n, 'iterations')

    durations = timer.repeat(repeat=10, number=n)

    time_per_op = [d / n for d in durations]
    min_t, max_t = min(time_per_op), max(time_per_op)
    mean_t = sum(time_per_op) / len(time_per_op)

    print(f'min {format_duration(min_t)} -- mean {format_duration(mean_t)} '
          f'-- max {format_duration(max_t)}')
    print()


if __name__ == '__main__':
  main()
