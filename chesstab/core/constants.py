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
    FEN_WHITE_PAWN,
    FEN_BLACK_PAWN,
    TAG_RESULT,
    DEFAULT_TAG_RESULT_VALUE,
    DEFAULT_TAG_VALUE,
    TAG_FEN,
    TAG_SETUP,
    SETUP_VALUE_FEN_PRESENT,
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

NAME_DELIMITER = "\n"
BOARDSIDE = 8
BOARDSQUARES = BOARDSIDE * BOARDSIDE
PIECE_SQUARE_NOT_ALLOWED = set()
for _piece in FEN_WHITE_PAWN, FEN_BLACK_PAWN:
    for _square in range(BOARDSIDE):
        PIECE_SQUARE_NOT_ALLOWED.add((_piece, _square))
        PIECE_SQUARE_NOT_ALLOWED.add((_piece, BOARDSQUARES - _square - 1))
PIECE_SQUARE_NOT_ALLOWED = frozenset(PIECE_SQUARE_NOT_ALLOWED)

# PGN constants for repertoires.
TAG_OPENING = "Opening"
REPERTOIRE_TAG_ORDER = (TAG_OPENING, TAG_RESULT)
REPERTOIRE_GAME_TAGS = {
    TAG_OPENING: DEFAULT_TAG_VALUE,
    TAG_RESULT: DEFAULT_TAG_RESULT_VALUE,
}

# Lookup for move number component of key values in game indicies: covers the
# likely values for typical game PGN without recursive annotation variations.
MOVE_NUMBER_KEYS = tuple(
    ["0"] + [str(len(hex(i)) - 2) + hex(i)[2:] for i in range(1, 256)]
)

# Character representation of empty square on displayed board.
NOPIECE = ""

# PGN results.  pgn_read.core.constants has '*' as DEFAULT_TAG_RESULT_VALUE
# but does not have constants for the other three results.
WHITE_WIN = "1-0"
BLACK_WIN = "0-1"
DRAW = "1/2-1/2"
UNKNOWN_RESULT = "*"

# Start and end tag characters.
END_TAG = "]"
START_TAG = "["

# Start and end RAV characters.
END_RAV = ")"
START_RAV = "("

# Start and end comment characters.
END_COMMENT = "}"
START_COMMENT = "{"
START_EOL_COMMENT = ";"

# Decorators to do special cases for Date and Round sorting.
SPECIAL_TAG_DATE = ("?", "0")

# Variation markers and non-move placeholders.
NON_MOVE = None

# Error markers for PGN display.
ERROR_START_COMMENT = "Error::"
ESCAPE_END_COMMENT = "::" + START_COMMENT + START_COMMENT + "::"
HIDE_END_COMMENT = "::::" + START_COMMENT + START_COMMENT

FEN_CONTEXT = (
    "".join((START_TAG, TAG_FEN, '"')),
    "".join(
        (
            '"',
            END_TAG,
            START_TAG,
            TAG_SETUP,
            '"',
            SETUP_VALUE_FEN_PRESENT,
            END_TAG.join('"\n'),
        )
    ),
)

del _piece, _square
del FEN_WHITE_PAWN, FEN_BLACK_PAWN, BOARDSQUARES
del ANY_WHITE_PIECE_NAME, ANY_BLACK_PIECE_NAME, EMPTY_SQUARE_NAME
del WHITE_PIECE_NAMES, BLACK_PIECE_NAMES
del TAG_FEN, TAG_SETUP, SETUP_VALUE_FEN_PRESENT
