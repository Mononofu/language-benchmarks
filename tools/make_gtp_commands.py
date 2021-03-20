import tarfile

from sgfmill import sgf

columns = 'ABCDEFGHJKLMNOPQRST'

num_moves = 0
max_moves = 2**10

# From https://homepages.cwi.nl/~aeb/go/games/games/
with tarfile.open('go_games.tar.gz') as f:
  for info in f:
    if not info.name.endswith('sgf'):
      continue
    reader = f.extractfile(info)
    
    game = sgf.Sgf_game.from_bytes(reader.read())
    if game.get_size() > 19:
      continue
    print('boardsize', game.get_size())
    print('komi', game.get_komi())
    print('clear_board')
    for node in game.get_main_sequence(): 
      color, point = node.get_move()
      if point is None:
        continue
      col, row = point
      print('play', color.upper(), columns[col] + str(row + 1))
      num_moves += 1
    print('final_score')

    if num_moves > max_moves:
      break