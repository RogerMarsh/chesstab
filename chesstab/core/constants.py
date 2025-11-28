# constants.py
# Copyright 2010 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Constants for ChessTab.

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
    SEVEN_TAG_ROSTER_DEFAULTS,
    SEVEN_TAG_ROSTER,
)

# These constants should match values from chessql.constants PIECE_NAMES.
# It is not imported because nothing else is taken from chessql at present,
# and the order in PIECE_NAMES changed at some point.
ANY_WHITE_PIECE_NAME = "A"
ANY_BLACK_PIECE_NAME = "a"
EMPTY_SQUARE_NAME = "_"
WHITE_PIECE_NAMES = "QBRNKP"
BLACK_PIECE_NAMES = "qbrnkp"

ALWAYS_MATCH = "".join(
    (ANY_WHITE_PIECE_NAME, ANY_BLACK_PIECE_NAME, EMPTY_SQUARE_NAME, ".")
)

# Supported encodings of PGN files.
# The PGN standard at 4.1 specifies the use of iso-8859-1 encoding.
# The ascii encoding gets treated as utf-8.  All others get treated as
# iso-8859-1 so utf-16, for example, will probably produce a complete mess
# at best; while others with single-byte encoding will not produce the
# intended character to an unknown extent.
ENCODINGS = ("utf-8", "iso-8859-1")

# File name and game number within file for a PGN file.
# Equivalent to PGN Tag Names for a game's position in the file.
FILE = "file"
GAME = "game"

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
# del ANY_WHITE_PIECE_NAME, ANY_BLACK_PIECE_NAME, EMPTY_SQUARE_NAME
# del WHITE_PIECE_NAMES, BLACK_PIECE_NAMES
del TAG_FEN, TAG_SETUP, SETUP_VALUE_FEN_PRESENT

NULL_GAME_TEXT = "\n".join(
    (
        " ".join(
            [
                " ".join(
                    (
                        t,
                        SEVEN_TAG_ROSTER_DEFAULTS.get(
                            t, DEFAULT_TAG_VALUE
                        ).join('""'),
                    )
                ).join("[]")
                for t in SEVEN_TAG_ROSTER
                if t != TAG_RESULT
            ]
        ),
        " ".join(
            (
                TAG_RESULT,
                SEVEN_TAG_ROSTER_DEFAULTS.get(
                    TAG_RESULT, DEFAULT_TAG_VALUE
                ).join('""'),
            )
        ).join("[]"),
        DEFAULT_TAG_RESULT_VALUE,
        "",
    )
)
del SEVEN_TAG_ROSTER_DEFAULTS, SEVEN_TAG_ROSTER

# Key for sort area path in database control file application control record.
SORT_AREA = b"_sort_area"

# Key for PGN files being imported path in database control file application
# control record.
PGN_FILES = b"_pgn_files"
