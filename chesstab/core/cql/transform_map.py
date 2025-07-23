# transform_map.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Transform tables for squares and directions under transform filters.

The rotate45 filter transforms directions.

The flipcolor filter transforms black pieces to white, and white to black,
and adjusts the other color related filters appropriately.

The other transform filters map squares.
"""

from chessql.core.constants import FILE_NAMES as FILE
from chessql.core.constants import CQL_RANK_NAMES as RANK
from chessql.core.constants import PIECE_NAMES as PIECE

color = str.maketrans(PIECE[:7] + PIECE[7:14], PIECE[7:14] + PIECE[:7])
del PIECE
up = {f + str(r): f + str(r + 1) for f in FILE for r in range(1, 8)}
down = {f + str(r): f + str(r - 1) for f in FILE for r in range(2, 9)}
left = {FILE[f] + r: FILE[f - 1] + r for f in range(1, 8) for r in RANK}
right = {FILE[f] + r: FILE[f + 1] + r for f in range(0, 7) for r in RANK}
file_left = {FILE[f]: FILE[f - 1] for f in range(1, 8)}
file_right = {FILE[f]: FILE[f + 1] for f in range(0, 7)}
rank_up = {RANK[r]: RANK[r + 1] for r in range(0, 7)}
rank_down = {RANK[r]: RANK[r - 1] for r in range(1, 8)}
northwest = {
    f + r: file_left[f] + rank_up[r] for f in file_left for r in rank_up
}
northeast = {
    f + r: file_right[f] + rank_up[r] for f in file_right for r in rank_up
}
southwest = {
    f + r: file_left[f] + rank_down[r] for f in file_left for r in rank_down
}
southeast = {
    f + r: file_right[f] + rank_down[r] for f in file_right for r in rank_down
}
del file_left
del file_right
del rank_up
del rank_down
reflect_v = {
    FILE[f] + r: FILE[len(FILE) - f - 1] + r
    for f in range(len(FILE))
    for r in RANK
}
reflect_h = {
    f + RANK[r]: f + RANK[len(RANK) - r - 1]
    for f in FILE
    for r in range(len(RANK))
}
reflect_a1h8 = {
    FILE[f] + RANK[r]: FILE[r] + RANK[f]
    for f in range(len(FILE))
    for r in range(len(RANK))
}
reflect_a8h1 = {
    FILE[f] + RANK[r]: FILE[len(RANK) - r - 1] + RANK[len(FILE) - f - 1]
    for f in range(len(FILE))
    for r in range(len(RANK))
}
rotate_90 = {
    FILE[f] + RANK[r]: FILE[len(RANK) - r - 1] + RANK[f]
    for f in range(len(FILE))
    for r in range(len(RANK))
}
rotate_180 = {
    FILE[f] + RANK[r]: FILE[len(FILE) - f - 1] + RANK[len(RANK) - r - 1]
    for f in range(len(FILE))
    for r in range(len(RANK))
}
rotate_270 = {
    FILE[f] + RANK[r]: FILE[r] + RANK[len(FILE) - f - 1]
    for f in range(len(FILE))
    for r in range(len(RANK))
}
identity = {f + r: f + r for f in FILE for r in RANK}
del FILE
del RANK
