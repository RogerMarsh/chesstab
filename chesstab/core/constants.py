# constants.py
# Copyright 2010 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Constants for Chess Query Language (CQL) parser.

Uses pgn_read.core.constants values plus additional piece encodings for any
piece, any white piece, and so on.

These constants were used by the old partial position scheme, which implemented
a single position list in CQL terms.

"""

from pgn_read.core.constants import (
    WPAWN,
    BPAWN,
    BOARDSIDE,
    BOARDSQUARES,
    )

from chessql.core.constants import (
    ANY_WHITE_PIECE_NAME,
    ANY_BLACK_PIECE_NAME,
    EMPTY_SQUARE_NAME,
    WHITE_PIECE_NAMES,
    BLACK_PIECE_NAMES,
    )

# Composite piece map (CQL) to actual pieces (PGN).
MAP_CQL_PIECE_TO_PIECES = {
    ANY_WHITE_PIECE_NAME: WHITE_PIECE_NAMES,
    ANY_BLACK_PIECE_NAME: BLACK_PIECE_NAMES,
    EMPTY_SQUARE_NAME: WHITE_PIECE_NAMES + BLACK_PIECE_NAMES,
    }

NAME_DELIMITER = '\n'
PIECE_SQUARE_NOT_ALLOWED = set()
for _piece in WPAWN, BPAWN:
    for _square in range(BOARDSIDE):
        PIECE_SQUARE_NOT_ALLOWED.add((_piece, _square))
        PIECE_SQUARE_NOT_ALLOWED.add((_piece, BOARDSQUARES - _square - 1))
PIECE_SQUARE_NOT_ALLOWED = frozenset(PIECE_SQUARE_NOT_ALLOWED)

del _piece, _square
del WPAWN, BPAWN, BOARDSIDE, BOARDSQUARES
del ANY_WHITE_PIECE_NAME, ANY_BLACK_PIECE_NAME, EMPTY_SQUARE_NAME
del WHITE_PIECE_NAMES, BLACK_PIECE_NAMES
    
