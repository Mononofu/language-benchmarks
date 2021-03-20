"""Go board implementation, based on the OpenSpiel implementation.

This file is a straight translation of
open_spiel/open_spiel/games/go/go_board.h, implementing the same
algorithm and using the same datastructures.
"""
import enum
import random
from typing import Iterable, Text, Tuple

import dataclasses

Point = int


class Color(enum.IntEnum):
  """Color of a point on the board - etiher a stone or empty."""
  BLACK = 0
  WHITE = 1
  EMPTY = 2
  GUARD = 3

  def opponent(self) -> 'Color':
    if self == self.BLACK:
      return self.WHITE
    elif self == self.WHITE:
      return self.BLACK
    else:
      return self

  def char(self) -> Text:
    if self == self.BLACK:
      return 'X'
    elif self == self.WHITE:
      return 'O'
    elif self == self.EMPTY:
      return ' '
    elif self == self.GUARD:
      return 'G'
    return '?'


VIRTUAL_BOARD_SIZE = 21
VIRTUAL_BOARD_POINTS = VIRTUAL_BOARD_SIZE * VIRTUAL_BOARD_SIZE

INVALID_POINT: Point = -1
PASS: Point = 20 * VIRTUAL_BOARD_SIZE


class Points:
  _HAS_DYNAMIC_ATTRIBUTES = True

  def __getattr__(self, name: Text) -> Point:
    return parse_point(name)


POINTS = Points()


@dataclasses.dataclass
class Vertex:
  chain_head: Point
  chain_next: Point
  color: Color


@dataclasses.dataclass
class Chain:
  """A directly connected group of stones."""
  # Initialized to border values.
  num_stones: int = 0
  # Need to have values big enough that they can never go below 0 even if
  # all liberties are removed.
  num_pseudo_liberties: int = 4
  liberty_vertex_sum: int = 32768
  liberty_vertex_sum_squared: int = 2147483648

  def in_atari(self) -> bool:
    return (self.num_pseudo_liberties *
            self.liberty_vertex_sum_squared == self.liberty_vertex_sum *
            self.liberty_vertex_sum)

  def reset(self):
    self.num_stones = 0
    self.num_pseudo_liberties = 0
    self.liberty_vertex_sum = 0
    self.liberty_vertex_sum_squared = 0

  def merge(self, other: 'Chain'):
    self.num_stones += other.num_stones
    self.num_pseudo_liberties += other.num_pseudo_liberties
    self.liberty_vertex_sum += other.liberty_vertex_sum
    self.liberty_vertex_sum_squared += other.liberty_vertex_sum_squared

  def add_liberty(self, p: Point):
    self.num_pseudo_liberties += 1
    self.liberty_vertex_sum += p
    self.liberty_vertex_sum_squared += p * p

  def remove_liberty(self, p: Point):
    self.num_pseudo_liberties -= 1
    self.liberty_vertex_sum -= p
    self.liberty_vertex_sum_squared -= p * p

  def single_liberty(self) -> Point:
    assert self.in_atari()
    assert self.liberty_vertex_sum % self.num_pseudo_liberties == 0
    return self.liberty_vertex_sum // self.num_pseudo_liberties


def board_points(board_size: int) -> Iterable[Point]:
  for row in range(board_size):
    for col in range(board_size):
      yield point_from_2d(row, col)


def parse_point(s: str) -> Point:
  """Parse a board point from a string such as 'D4' or 'Q16'."""
  s = s.lower()

  if s == 'pass':
    return PASS

  if len(s) < 2 or len(s) > 3:
    return INVALID_POINT

  col = ord(s[0]) - ord('a') + (1 if s[0] <= 'i' else 0)
  row = int(s[1:])
  return row * VIRTUAL_BOARD_SIZE + col


def point_to_2d(p: Point) -> Tuple[int, int]:
  if p == INVALID_POINT or p == PASS:
    return (-1, -1)

  row = p // VIRTUAL_BOARD_SIZE
  col = p % VIRTUAL_BOARD_SIZE
  return (row - 1, col - 1)


def point_from_2d(row: int, col: int) -> Point:
  return (row + 1) * VIRTUAL_BOARD_SIZE + col + 1


_COLS = 'ABCDEFGHJKLMNOPQRST'


def format_point(p: Point) -> Text:
  row, col = point_to_2d(p)
  return _COLS[col] + str(row + 1)


def neighbours(p: Point) -> Iterable[Point]:
  yield p + VIRTUAL_BOARD_SIZE
  yield p - 1
  yield p + 1
  yield p - VIRTUAL_BOARD_SIZE


# 2D array of zobrist values, indexed by point and color.
_ZOBRIST_VALUES = [[random.randint(0, 2**64)
                    for _ in range(4)]
                   for _ in range(VIRTUAL_BOARD_POINTS)]


class GoBoard:
  """GoBoard implementation optimized for speed, at least in the C++ version."""

  def __init__(self, board_size: int):
    self._board_size = board_size
    self._last_ko_point = INVALID_POINT

    self._board = [
        Vertex(chain_head=i, chain_next=i, color=Color.GUARD)
        for i in range(VIRTUAL_BOARD_POINTS)
    ]
    self._chains = [Chain() for _ in range(VIRTUAL_BOARD_POINTS)]
    self._last_captures = [INVALID_POINT for _ in range(4)]

    for p in board_points(board_size):
      self._board[p].color = Color.EMPTY
      self._chains[p].reset()

    for p in board_points(board_size):
      for n in neighbours(p):
        if self.is_empty(n):
          self._chains[p].add_liberty(n)

    self._zobrist_hash = 0

  def clone(self) -> 'GoBoard':
    """Returns a deep copy of this GoBoard instance."""
    # Manually write out a copy constructor.. deepcopy is 3x slower than even
    # this terribly slow implementation.
    other = GoBoard(self._board_size)
    # pylint: disable=protected-access
    other._last_ko_point = self._last_ko_point

    for i in range(VIRTUAL_BOARD_POINTS):
      other._board[i].chain_head = self._board[i].chain_head
      other._board[i].chain_next = self._board[i].chain_next
      other._board[i].color = self._board[i].color

      other._chains[i].num_stones = self._chains[i].num_stones
      other._chains[i].num_pseudo_liberties = self._chains[
          i].num_pseudo_liberties
      other._chains[i].liberty_vertex_sum = self._chains[i].liberty_vertex_sum
      other._chains[i].liberty_vertex_sum_squared = self._chains[
          i].liberty_vertex_sum_squared

    for i in range(len(self._last_captures)):
      other._last_captures[i] = self._last_captures[i]

    other._zobrist_hash = self._zobrist_hash
    # pylint: enable=protected-access

    return other

  def point_color(self, p: Point) -> Color:
    return self._board[p].color

  def is_empty(self, p: Point) -> bool:
    return self._board[p].color == Color.EMPTY

  def in_board_area(self, p: Point) -> bool:
    row, col = point_to_2d(p)
    return (row >= 0 and row < self._board_size and col >= 0 and
            col < self._board_size)

  def pseudo_liberty(self, p: Point) -> int:
    chain = self._chain(p)
    if chain.num_pseudo_liberties == 0:
      return 0
    elif chain.in_atari():
      return 1
    else:
      return chain.num_pseudo_liberties

  def in_atari(self, p: Point) -> bool:
    return self._chain(p).in_atari()

  def single_liberty(self, p: Point) -> Point:
    """If the chain this point is part of has a single liberty, return it."""
    head = self.chain_head(p)
    liberty = self._chain(p).single_liberty()

    # Check it is really a liberty.
    assert self.in_board_area(liberty)
    assert self.is_empty(liberty)

    # Make sure the liberty actually borders the group.
    for n in neighbours(liberty):
      if self.chain_head(n) == head:
        return liberty

    raise ValueError(f'liberty {liberty} does not actually border {p}')

  def __hash__(self) -> int:
    return self._zobrist_hash

  def is_legal_move(self, p: Point, c: Color) -> bool:
    """Return whether this move is legal."""
    if p == PASS:
      return True
    if not self.in_board_area(p):
      return False
    if not self.is_empty(p) or p == self._last_ko_point:
      return False
    if self._chain(p).num_pseudo_liberties > 0:
      return True

    # For all checks below, the newly placed stone is completely surrounded by
    # enemy and friendly stones.

    # Allow to play if the placed stones connects to a group that still has at
    # least one other liberty after connecting.
    for n in neighbours(p):
      if self.point_color(n) == c and not self._chain(n).in_atari():
        return True

    # Allow to play if the placed stone will kill at least one group.
    for n in neighbours(p):
      if self.point_color(n) == c.opponent() and self._chain(n).in_atari():
        return True

    return False

  def play(self, p: Point, c: Color):
    """Applies the move to the board."""
    if p == PASS:
      self._last_ko_point = INVALID_POINT
      return

    assert self._board[p].color == Color.EMPTY

    # Preparation for ko checking.
    played_in_enemy_eye = True
    for n in neighbours(p):
      nc = self.point_color(n)
      if nc == c or nc == Color.EMPTY:
        played_in_enemy_eye = False
        break

    self._join_chains_around(p, c)
    self._set_stone(p, c)
    self._remove_liberty_from_neighbouring_chains(p)
    stones_captured = self._capture_dead_chains(p, c)

    if played_in_enemy_eye and stones_captured == 1:
      self._last_ko_point = self._last_captures[0]
    else:
      self._last_ko_point = INVALID_POINT

    assert self._chain(
        p).num_pseudo_liberties > 0, f'suicide: {c} {format_point(p)} on {self}'

  def _set_stone(self, p: Point, c: Color):
    if c == Color.EMPTY:
      self._zobrist_hash ^= _ZOBRIST_VALUES[p][self.point_color(p)]
    else:
      self._zobrist_hash ^= _ZOBRIST_VALUES[p][c]

    self._board[p].color = c

  def _join_chains_around(self, p: Point, c: Color):
    """Connects any chains connected by a newly placed stone."""
    # Combines the groups around the newly placed stone at vertex. If no groups
    # are available for joining, the new stone is placed as a new group.
    largest_chain_head = INVALID_POINT
    largest_chain_size = 0
    for n in neighbours(p):
      if self.point_color(n) == c:
        chain = self._chain(n)
        if chain.num_stones > largest_chain_size:
          largest_chain_size = chain.num_stones
          largest_chain_head = self.chain_head(n)

    if largest_chain_size == 0:
      self._init_new_chain(p)
      return

    for n in neighbours(p):
      if self.point_color(n) == c:
        chain_head = self.chain_head(n)
        if chain_head != largest_chain_head:
          self._chain(largest_chain_head).merge(self._chain(n))

          # Set all stones in the smaller string to be part of the larger chain.
          cur = n
          while True:
            self._board[cur].chain_head = largest_chain_head
            cur = self._board[cur].chain_next
            if cur == n:
              break

          # Connect the 2 linked lists representing the stones in the 2 chains.
          self._board[largest_chain_head].chain_next, self._board[
              n].chain_next = (self._board[n].chain_next,
                               self._board[largest_chain_head].chain_next)

    self._board[p].chain_next = self._board[largest_chain_head].chain_next
    self._board[largest_chain_head].chain_next = p
    self._board[p].chain_head = largest_chain_head
    self._chain(largest_chain_head).num_stones += 1

    for n in neighbours(p):
      if self.is_empty(n):
        self._chain(largest_chain_head).add_liberty(n)

  def _remove_liberty_from_neighbouring_chains(self, p: Point):
    for n in neighbours(p):
      self._chain(n).remove_liberty(p)

  def __str__(self) -> Text:
    s = f'GoBoard(size={self._board_size})\n'
    for row in reversed(range(self._board_size)):
      s += '%2d ' % (row + 1)
      for col in range(self._board_size):
        s += self.point_color(point_from_2d(row, col)).char()
      s += '\n'
    s += '   ' + 'ABCDEFGHJKLMNOPQRST'[0:self._board_size]
    s += '\n'
    return s

  def _capture_dead_chains(self, p: Point, c: Color) -> int:
    """Remove any dead stones from the board."""
    stones_captured = 0
    capture_index = 0
    for n in neighbours(p):
      if self.point_color(n) == c.opponent() and self._chain(
          n).num_pseudo_liberties == 0:
        self._last_captures[capture_index] = self.chain_head(n)
        capture_index += 1
        stones_captured += self._chain(n).num_stones
        self._remove_chain(n)

    for i in range(capture_index, len(self._last_captures)):
      self._last_captures[i] = INVALID_POINT

    return stones_captured

  def _remove_chain(self, p: Point):
    """Remove and reset all stones in the chain that this stone is part of."""
    this_chain_head = self.chain_head(p)
    cur = p
    while True:
      next_p = self._board[cur].chain_next

      self._set_stone(cur, Color.EMPTY)
      self._init_new_chain(cur)

      for n in neighbours(cur):
        if self.chain_head(n) != this_chain_head or self.is_empty(n):
          self._chain(n).add_liberty(cur)

      cur = next_p
      if cur == p:
        break

  def _init_new_chain(self, p: Point):
    """Initialize this point to a new chain."""
    self._board[p].chain_head = p
    self._board[p].chain_next = p

    c = self._chain(p)
    c.reset()
    c.num_stones += 1

    for n in neighbours(p):
      if self.is_empty(n):
        c.add_liberty(n)

  # Head of a chain; each chain has exactly one head that can be used to
  # uniquely identify it. Chain heads may change over successive play() calls.
  def chain_head(self, p: Point) -> Point:
    return self._board[p].chain_head

  # Number of stones in a chain.
  def chain_size(self, p: Point) -> int:
    return self._chain(p).num_stones

  def _chain(self, p: Point) -> Chain:
    return self._chains[self.chain_head(p)]


def create_board(s: Text) -> GoBoard:
  """Generates a go board from the given string.

  Sets X to black stones and O to white stones. The first character of the first
  line is mapped to A1, the second character to B1, etc, as below:
     ABCDEFGH
   1 ++++XO++
   2 XXXXXO++
   3 OOOOOO++
   4 ++++++++

  Args:
    s: The string representing the board to create.

  Returns:
    A go board of size 19x19 with the specified stones played.
  """
  board = GoBoard(19)
  row = 0
  for line in s.split('\n'):
    col = 0
    stones_started = False
    for c in line:
      if c == ' ':
        assert not stones_started
        continue
      elif c == 'X':
        stones_started = True
        board.play(point_from_2d(row, col), Color.BLACK)
      elif c == 'O':
        stones_started = True
        board.play(point_from_2d(row, col), Color.WHITE)
      col += 1
    row += 1

  return board
