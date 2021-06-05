# chesstab-4-1-1_castling-option-correction.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Read games from a ChessTab database and report games with FENs where the
castling options are not consistent with the piece placement, and attempt
correction on request.

The database must be compatible with ChessTab-4.1.

"""
import tkinter
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox
import os
from ast import literal_eval
import time

# This module must have the PGN class from pgn-read-1.3.1 and the PGNUpdate
# class from ChessTab-4.1 so both are copied here, rather than imported, as
# PGN131 along with PGNError131.
# The fitting pgn_read constants module is copied too.
# The two chessql constants are declared here too.
# All docstrings removed from the copied classes and modules.
# The names are modified to indicate their reliance on pgn-read-1.3.1.
# One constant is copied from chesstab.core.chessrecord.
# A regular expession is copied from chesstab.core.querystatement.

# The PGN class from pgn-read-1.3.2 is used to verify any corrected FENs are
# valid so it is copied here, rather than imported, as PGN132 along with
# PGNError132.
# PGN131 and PGN132 use the same version of .constants module

import re

from solentware_base import modulequery
from solentware_base.core.record import KeyData, Value, Record

from pgn_read.core import parser

from .. import (
    APPLICATION_DATABASE_MODULE,
    FULL_POSITION_MODULE,
    ANALYSIS_MODULE,
)
from ..core.chessrecord import ChessDBrecordGameUpdate, ChessDBrecordAnalysis

# These have to be same at both versions of ChessTab so use the current ones.
from ..core.filespec import (
    FileSpec,
    POSITIONS_FIELD_DEF,
    SOURCE_FIELD_DEF,
    PIECESQUAREMOVE_FIELD_DEF,
    PIECEMOVE_FIELD_DEF,
    SQUAREMOVE_FIELD_DEF,
    GAMES_FILE_DEF,
    REPERTOIRE_FILE_DEF,
    OPENING_ERROR_FIELD_DEF,
    PGN_DATE_FIELD_DEF,
    VARIATION_FIELD_DEF,
    ENGINE_FIELD_DEF,
    PARTIALPOSITION_NAME_FIELD_DEF,
    RULE_FIELD_DEF,
    COMMAND_FIELD_DEF,
    ANALYSIS_FILE_DEF,
)

# start of attributes copied from pgn_read.core.constants at version 1.3.1
# pgn specification values
TAG_EVENT = "Event"
TAG_SITE = "Site"
TAG_DATE = "Date"
TAG_ROUND = "Round"
TAG_WHITE = "White"
TAG_BLACK = "Black"
TAG_RESULT = "Result"
TAG_FEN = "FEN"
SEVEN_TAG_ROSTER = {
    TAG_EVENT: "?",
    TAG_SITE: "?",
    TAG_DATE: "????.??.??",
    TAG_ROUND: "?",
    TAG_WHITE: "?",
    TAG_BLACK: "?",
    TAG_RESULT: "*",
}
SEVEN_TAG_ROSTER_DISPLAY_ORDER = (
    TAG_SITE,
    TAG_ROUND,
    TAG_EVENT,
    TAG_DATE,
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
)
SEVEN_TAG_ROSTER_EXPORT_ORDER = (
    TAG_EVENT,
    TAG_SITE,
    TAG_DATE,
    TAG_ROUND,
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
)
# Allow for decorators to do special cases for Date and Round sorting
SPECIAL_TAG_DATE = ("?", "0")
SPECIAL_TAG_ROUND = {"?": 1, "-": 2}
NORMAL_TAG_ROUND = 3
SEVEN_TAG_ROSTER_ARCHIVE_SORT1 = (
    TAG_EVENT,
    TAG_SITE,
    TAG_DATE,
)
SEVEN_TAG_ROSTER_ARCHIVE_SORT2 = (
    TAG_ROUND,
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
)

WHITE_WIN = "1-0"
BLACK_WIN = "0-1"
DRAW = "1/2-1/2"
UNKNOWN_RESULT = "*"
RESULT_SET = {WHITE_WIN, BLACK_WIN, DRAW, UNKNOWN_RESULT}

# Repertoire Tags (non-standard)
TAG_OPENING = "Opening"
REPERTOIRE_TAG_ORDER = (TAG_OPENING, TAG_RESULT)
REPERTOIRE_GAME_TAGS = {
    TAG_OPENING: "?",
    TAG_RESULT: UNKNOWN_RESULT,
}

PGN_PAWN = ""
PGN_KING = "K"
PGN_QUEEN = "Q"
PGN_ROOK = "R"
PGN_BISHOP = "B"
PGN_KNIGHT = "N"
PGN_FROM_SQUARE_DISAMBIGUATION = frozenset((PGN_QUEEN, PGN_BISHOP, PGN_KNIGHT))

# Refugees from old PGN regular expression pattern matching strings.
O_O_O = "O-O-O"
O_O = "O-O"
PLAIN_MOVE = ""
CAPTURE_MOVE = "x"
LINEFEED = "\n"
CARRIAGE_RETURN = "\r"
NEWLINE = "".join((LINEFEED, CARRIAGE_RETURN))
SPACE = " "
HORIZONTAL_TAB = "\t"
FORMFEED = "\f"
VERTICAL_TAB = "\v"

# PGN regular expression pattern matching strings

# Building blocks
ANYTHING_ELSE = "."
WHITESPACE = "\s+"
FULLSTOP = "."
PERIOD = "\\" + FULLSTOP
INTEGER = "[1-9][0-9]*"
TERMINATION = "|".join((WHITE_WIN, BLACK_WIN, DRAW, "\\" + UNKNOWN_RESULT))
START_TAG = "["
END_TAG = "]"
SYMBOL = "([A-Za-z0-9][A-Za-z0-9_+#=:-]*)"
STRING = r'"((?:[^\\"]|\\.)*)"'
TAG_PAIR = "".join(
    (
        "(\\",
        START_TAG,
        ")\s*",
        SYMBOL,
        "\s*",
        STRING,
        "\s*",
        "(\\",
        END_TAG,
        ")",
    )
)
START_COMMENT = "{"
END_COMMENT = "}"
COMMENT = "".join(
    ("\\", START_COMMENT, "[^", END_COMMENT, "]*\\", END_COMMENT)
)
LEFT_ANGLE_BRACE = "<"
RIGHT_ANGLE_BRACE = ">"
RESERVED = "".join(
    (LEFT_ANGLE_BRACE, "[^", RIGHT_ANGLE_BRACE, "]*", RIGHT_ANGLE_BRACE)
)
COMMENT_TO_EOL = ";(?:[^\n]*)\n"
PERCENT = "%"
ESCAPE_LINE = PERCENT.join(("(?:\A|(?<=\n))", "(?:[^\n]*)\n"))
NAG = "\$[0-9]+(?!/|-)"
START_RAV = "("
END_RAV = ")"

# KQRBN are replaced by PGN_KING, ..., constants; not WKING, ..., constants.
FNR = "a-h"
RNR = "1-8"
PAWN_PROMOTE = "".join(
    (
        "(?:([" + FNR + "])(x))?([" + FNR + "][18])(=[",
        PGN_BISHOP,
        PGN_KNIGHT,
        PGN_QUEEN,
        PGN_ROOK,
        "])",
    )
)
PAWN_CAPTURE = "([" + FNR + "])(x)([" + FNR + "][2-7])"
PIECE_CAPTURE = "".join(
    (
        "(?:(",
        PGN_KING,
        ")|(?:([",
        PGN_BISHOP,
        PGN_KNIGHT,
        PGN_QUEEN,
        PGN_ROOK,
        "])([" + FNR + "]?[" + RNR + "]?)))",
        "(x)([" + FNR + "][" + RNR + "])",
    )
)
PIECE_CHOICE_MOVE = "".join(
    (
        "([",
        PGN_BISHOP,
        PGN_KNIGHT,
        PGN_QUEEN,
        PGN_ROOK,
        "])([",
        FNR + RNR + "])([" + FNR + "][" + RNR + "])",
    )
)
PIECE_MOVE = "".join(
    (
        "([",
        PGN_KING,
        PGN_BISHOP,
        PGN_KNIGHT,
        PGN_QUEEN,
        PGN_ROOK,
        "])([" + FNR + "][" + RNR + "])",
    )
)
PAWN_MOVE = "([" + FNR + "][" + RNR + "])"
CASTLES = "(O-O(?:-O)?)"
CHECK = "([+#]?)"
ANNOTATION = "([!?][!?]?)?"

# Regular expression to detect full games in import format; export format is a
# subset of import format.  The text stored on database is captured.
IMPORT_FORMAT = "".join(
    (
        "(?:",
        TAG_PAIR,
        ")",
        "|",
        "(?:",
        "(?:",
        "(?:",
        PAWN_PROMOTE,
        ")",
        "|",
        "(?:",
        PAWN_CAPTURE,
        ")",
        "|",
        "(?:",
        PIECE_CAPTURE,
        ")",
        "|",
        "(?:",
        PIECE_CHOICE_MOVE,
        ")",
        "|",
        "(?:",
        PIECE_MOVE,
        ")",
        "|",
        "(?:",
        PAWN_MOVE,
        ")",
        "|",
        "(?:",
        CASTLES,
        ")",
        ")",
        "(?:",
        CHECK,
        ")",
        "(?:",
        ANNOTATION,
        ")",
        ")",
        "|",
        "(",
        COMMENT,
        ")",
        "|",
        "(",
        NAG,
        ")",
        "|",
        "(",
        COMMENT_TO_EOL,
        ")",
        "|",
        "(",
        TERMINATION,
        ")",
        "|",
        INTEGER,
        "|",
        PERIOD,
        "|",
        WHITESPACE,
        "|",
        "(\\",
        START_RAV,
        ")",
        "|",
        "(\\",
        END_RAV,
        ")",
        "|",
        RESERVED,
        "|",
        ESCAPE_LINE,
        "|",
        "(",
        ANYTHING_ELSE,
        ")",
    )
)

# Regular expressions to disambiguate moves: move text like 'Bc4d5' is the only
# kind which could need to be interpreted as one move rather than two.
DISAMBIGUATE_FORMAT = "".join(
    (
        "[" + PGN_BISHOP + PGN_KNIGHT + PGN_QUEEN + "]",
        "[" + FNR + "][" + RNR + "]",
        "[" + FNR + "][" + RNR + "]",
    )
)
UNAMBIGUOUS_FORMAT = ".*"

# Regular expression to detect possible beginning of move in an error sequence,
# "Bxa" for example while typing "Bxa6".
# No constants for partial castling moves.
POSSIBLE_MOVE = "".join(
    (
        "[O",
        PGN_KING,
        PGN_BISHOP,
        PGN_KNIGHT,
        PGN_ROOK,
        PGN_QUEEN,
        FNR,
        "][-O",
        FNR,
        RNR,
        "+#?!=]* *",
    )
)

#
# Group offsets for IMPORT_FORMAT matches
#
IFG_START_TAG = 1
IFG_TAG_SYMBOL = 2
# IFG_TAG_STRING = 3
IFG_TAG_STRING_VALUE = 3
# IFG_TAG_END = 4
IFG_PAWN_PROMOTE_FROM_FILE = 5
IFG_PAWN_TAKES_PROMOTE = 6
IFG_PAWN_PROMOTE_SQUARE = 7
IFG_PAWN_PROMOTE_PIECE = 8
IFG_PAWN_CAPTURE_FROM_FILE = 9
IFG_PAWN_TAKES = 10
IFG_PAWN_CAPTURE_SQUARE = 11
IFG_KING_CAPTURE = 12
IFG_PIECE_CAPTURE = 13
IFG_PIECE_CAPTURE_FROM = 14
IFG_PIECE_TAKES = 15
IFG_PIECE_CAPTURE_SQUARE = 16
IFG_PIECE_CHOICE = 17
IFG_PIECE_CHOICE_FILE_OR_RANK = 18
IFG_PIECE_CHOICE_SQUARE = 19
IFG_PIECE_MOVE = 20
IFG_PIECE_SQUARE = 21
IFG_PAWN_SQUARE = 22
IFG_CASTLES = 23
IFG_CHECK = 24
IFG_ANNOTATION = 25
IFG_COMMENT = 26
IFG_NAG = 27
IFG_COMMENT_TO_EOL = 28
IFG_TERMINATION = 29
IFG_START_RAV = 30
IFG_END_RAV = 31
IFG_ANYTHING_ELSE = 32

#
# Parser states
#
PGN_SEARCHING = 0
PGN_SEARCHING_AFTER_ERROR_IN_RAV = 1
PGN_SEARCHING_AFTER_ERROR_IN_GAME = 2
PGN_COLLECTING_TAG_PAIRS = 3
PGN_COLLECTING_MOVETEXT = 4
PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING = 5
PGN_DISAMBIGUATE_MOVE = 6

#
# numeric annotation glyphs (just validation for now)
#
NAG_TRANSLATION = {"$" + str(o): None for o in range(1, 499)}

#
# Square constants and flags
#
BOARDSIDE = 8
BOARDSQUARES = BOARDSIDE * BOARDSIDE
SQUARE_BITS = [1 << i for i in range(BOARDSQUARES)]
ALL_SQUARES = sum(SQUARE_BITS)
EN_PASSANT_TO_SQUARES = sum([SQUARE_BITS[s] for s in range(24, 40)])
EN_PASSANT_FROM_SQUARES = sum([SQUARE_BITS[s] for s in range(8, 16)]) | sum(
    [SQUARE_BITS[s] for s in range(48, 56)]
)

# Pieces
# Encoding positions is more efficient (key length) if pawns are encoded with
# a value less than 4 with either the white or the black pawn encoded as 0 and
# the squares that cannot host a pawn include 0..3 as their encodings (bytes
# \x01..\x03 which arises naturally as the second byte of the 2-byte encodings
# ), typically the squares b1 c1 and d1.  The other two values less than 4 are
# best used for the kings which are always present.  Absence of a piece is best
# encoded with the highest value, which will be 12 if using lists, wherever
# possible, rather than dictionaries for mappings.
NOPIECE = ""
WKING = "K"
WQUEEN = "Q"
WROOK = "R"
WBISHOP = "B"
WKNIGHT = "N"
WPAWN = "P"
BKING = "k"
BQUEEN = "q"
BROOK = "r"
BBISHOP = "b"
BKNIGHT = "n"
BPAWN = "p"
PIECES = frozenset(
    (
        WKING,
        WQUEEN,
        WROOK,
        WBISHOP,
        WKNIGHT,
        WPAWN,
        BKING,
        BQUEEN,
        BROOK,
        BBISHOP,
        BKNIGHT,
        BPAWN,
    )
)

# Define white and black pieces and map to values used in database records
WPIECES = frozenset((WKING, WQUEEN, WROOK, WBISHOP, WKNIGHT, WPAWN))
BPIECES = frozenset((BKING, BQUEEN, BROOK, BBISHOP, BKNIGHT, BPAWN))

# The default initial board, internal representation.
INITIAL_BOARD = (
    BROOK,
    BKNIGHT,
    BBISHOP,
    BQUEEN,
    BKING,
    BBISHOP,
    BKNIGHT,
    BROOK,
    BPAWN,
    BPAWN,
    BPAWN,
    BPAWN,
    BPAWN,
    BPAWN,
    BPAWN,
    BPAWN,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    NOPIECE,
    WPAWN,
    WPAWN,
    WPAWN,
    WPAWN,
    WPAWN,
    WPAWN,
    WPAWN,
    WPAWN,
    WROOK,
    WKNIGHT,
    WBISHOP,
    WQUEEN,
    WKING,
    WBISHOP,
    WKNIGHT,
    WROOK,
)
INITIAL_OCCUPIED_SQUARES = (
    frozenset(
        (48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63)
    ),
    frozenset((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)),
)
INITIAL_BOARD_BITMAP = sum(
    [sum([SQUARE_BITS[o] for o in s]) for s in INITIAL_OCCUPIED_SQUARES]
)
INITIAL_PIECE_LOCATIONS = {
    k: v
    for k, v in (
        (WKING, (60,)),
        (WQUEEN, (59,)),
        (WROOK, (56, 63)),
        (WBISHOP, (58, 61)),
        (WKNIGHT, (57, 62)),
        (WPAWN, (48, 49, 50, 51, 52, 53, 54, 55)),
        (BKING, (4,)),
        (BQUEEN, (3,)),
        (BROOK, (0, 7)),
        (BBISHOP, (2, 5)),
        (BKNIGHT, (1, 6)),
        (BPAWN, (8, 9, 10, 11, 12, 13, 14, 15)),
    )
}

# White and black side
WHITE_SIDE = 0
BLACK_SIDE = 1
OTHER_SIDE = BLACK_SIDE, WHITE_SIDE
SIDE_KING = WKING, BKING

# Map PGN piece file and rank names to internal representation
MAPPIECE = (
    {
        PGN_PAWN: WPAWN,
        PGN_KING: WKING,
        PGN_QUEEN: WQUEEN,
        PGN_ROOK: WROOK,
        PGN_BISHOP: WBISHOP,
        PGN_KNIGHT: WKNIGHT,
    },
    {
        PGN_PAWN: BPAWN,
        PGN_KING: BKING,
        PGN_QUEEN: BQUEEN,
        PGN_ROOK: BROOK,
        PGN_BISHOP: BBISHOP,
        PGN_KNIGHT: BKNIGHT,
    },
)  # not sure if this should be set or tuple or dict

MAPFILE = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
MAPRANK = {
    "8": 0,
    "7": 8,
    "6": 16,
    "5": 24,
    "4": 32,
    "3": 40,
    "2": 48,
    "1": 56,
}
MAPROW = {"8": 0, "7": 1, "6": 2, "5": 3, "4": 4, "3": 5, "2": 6, "1": 7}

# {'a8':0, 'b8':1, ..., 'g1':62, 'h1':63}, the order squares are listed in
# Forsyth-Edwards Notation and the square numbers used internally.
MAP_PGN_SQUARE_NAME_TO_FEN_ORDER = {
    "".join((f, r)): fn + rn
    for f, fn in MAPFILE.items()
    for r, rn in MAPRANK.items()
}

# FEN constants
FEN_WHITE = "w"
FEN_BLACK = "b"
FEN_FIELD_DELIM = " "
FEN_RANK_DELIM = "/"
FEN_NULL = "-"
FEN_INITIAL_HALFMOVE_COUNT = 0
FEN_INITIAL_FULLMOVE_NUMBER = 1
FEN_INITIAL_CASTLING = WKING + WQUEEN + BKING + BQUEEN
FEN_STARTPOSITION = FEN_FIELD_DELIM.join(
    (
        FEN_RANK_DELIM.join(
            (
                "".join(
                    (
                        BROOK,
                        BKNIGHT,
                        BBISHOP,
                        BQUEEN,
                        BKING,
                        BBISHOP,
                        BKNIGHT,
                        BROOK,
                    )
                ),
                "".join(
                    (BPAWN, BPAWN, BPAWN, BPAWN, BPAWN, BPAWN, BPAWN, BPAWN)
                ),
                str(len(MAPFILE)),
                str(len(MAPFILE)),
                str(len(MAPFILE)),
                str(len(MAPFILE)),
                "".join(
                    (WPAWN, WPAWN, WPAWN, WPAWN, WPAWN, WPAWN, WPAWN, WPAWN)
                ),
                "".join(
                    (
                        WROOK,
                        WKNIGHT,
                        WBISHOP,
                        WQUEEN,
                        WKING,
                        WBISHOP,
                        WKNIGHT,
                        WROOK,
                    )
                ),
            )
        ),
        FEN_WHITE,
        FEN_INITIAL_CASTLING,
        FEN_NULL,
        str(FEN_INITIAL_HALFMOVE_COUNT),
        str(FEN_INITIAL_FULLMOVE_NUMBER),
    )
)
FEN_FIELD_COUNT = 6
FEN_SIDES = {FEN_WHITE: WHITE_SIDE, FEN_BLACK: BLACK_SIDE}
FEN_TOMOVE = FEN_WHITE, FEN_BLACK

# Map FEN square names to board square numbers for en passant move and capture
FEN_WHITE_MOVE_TO_EN_PASSANT = {
    "a6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["a6"],
    "b6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["b6"],
    "c6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["c6"],
    "d6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["d6"],
    "e6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["e6"],
    "f6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["f6"],
    "g6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["g6"],
    "h6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["h6"],
}
FEN_BLACK_MOVE_TO_EN_PASSANT = {
    "a3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["a3"],
    "b3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["b3"],
    "c3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["c3"],
    "d3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["d3"],
    "e3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["e3"],
    "f3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["f3"],
    "g3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["g3"],
    "h3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["h3"],
}
FEN_WHITE_CAPTURE_EN_PASSANT = {
    "a6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["a5"],
    "b6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["b5"],
    "c6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["c5"],
    "d6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["d5"],
    "e6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["e5"],
    "f6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["f5"],
    "g6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["g5"],
    "h6": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["h5"],
}
FEN_BLACK_CAPTURE_EN_PASSANT = {
    "a3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["a4"],
    "b3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["b4"],
    "c3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["c4"],
    "d3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["d4"],
    "e3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["e4"],
    "f3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["f4"],
    "g3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["g4"],
    "h3": MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["h4"],
}
FEN_EN_PASSANT_TARGET_RANK = {"5": "6", "4": "3"}

# Specification of conditions to be met to permit castling and changes to make
# to board to display move in internal representation.
# The square to which the king moves is not included in the set of squares
# that must not be under attack because this condition is checked for all moves
# after being played provisionally on the board.  The special additional thing
# about castling is that the king cannot move out of or through check; for all
# types of move the king must not be under attack after playing the move.  But
# as currently implemented there is no harm except waste in including the test.
CASTLING_W = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["e1"]
CASTLING_WK = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["h1"]
CASTLING_WQ = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["a1"]
CASTLING_B = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["e8"]
CASTLING_BK = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["h8"]
CASTLING_BQ = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["a8"]
CASTLING_AVAILABITY_SQUARES = (
    SQUARE_BITS[CASTLING_WQ]
    | SQUARE_BITS[CASTLING_W]
    | SQUARE_BITS[CASTLING_WK]
    | SQUARE_BITS[CASTLING_BQ]
    | SQUARE_BITS[CASTLING_B]
    | SQUARE_BITS[CASTLING_BK]
)
CASTLING_SQUARES = {
    WKING: (
        CASTLING_W,
        CASTLING_WK,
        (
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["f1"],
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["g1"],
        ),
        (),
        WROOK,
        WKING,
    ),
    WQUEEN: (
        CASTLING_W,
        CASTLING_WQ,
        (
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["d1"],
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["c1"],
        ),
        (MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["b1"],),
        WROOK,
        WKING,
    ),
    BKING: (
        CASTLING_B,
        CASTLING_BK,
        (
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["f8"],
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["g8"],
        ),
        (),
        BROOK,
        BKING,
    ),
    BQUEEN: (
        CASTLING_B,
        CASTLING_BQ,
        (
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["d8"],
            MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["c8"],
        ),
        (MAP_PGN_SQUARE_NAME_TO_FEN_ORDER["b8"],),
        BROOK,
        BKING,
    ),
}

# FEN validation
FEN_CASTLING_OPTION_REPEAT_MAX = 1
FEN_PIECE_COUNT_PER_SIDE_MAX = 16
FEN_KING_COUNT = 1
FEN_PAWN_COUNT_MAX = 8
FEN_QUEEN_COUNT_INITIAL = 1
FEN_ROOK_COUNT_INITIAL = 2
FEN_BISHOP_COUNT_INITIAL = 2
FEN_KNIGHT_COUNT_INITIAL = 2
FEN_MAXIMUM_PIECES_GIVING_CHECK = 2

# variation markers and non-move placeholders
NON_MOVE = None
MOVE_ERROR = False
MOVE_AFTER_ERROR = 0
MOVE_TEXT = True

# Maximum line length in PGN file for movetext excluding EOL ('\n')
# Some PGN Tags are allowed to exceed this
# The rule may not be enforcable for comments, especially any re-exported,
# without disturbing any formatting attempts with EOL and spaces.
PGN_MAX_LINE_LEN = 79

# Piece moves and line definitions

_RANKS = [
    sum([SQUARE_BITS[s + r * BOARDSIDE] for s in range(BOARDSIDE)])
    for r in range(BOARDSIDE)
    for f in range(BOARDSIDE)
]
_FILES = [
    sum([SQUARE_BITS[s * BOARDSIDE + f] for s in range(BOARDSIDE)])
    for r in range(BOARDSIDE)
    for f in range(BOARDSIDE)
]
_TOPLEFT_TO_BOTTOMRIGHT = [
    sum(
        [
            SQUARE_BITS[
                ((f + c) % BOARDSIDE) + ((r + c) % BOARDSIDE) * BOARDSIDE
            ]
            for c in range(BOARDSIDE)
            if (
                f + c < BOARDSIDE
                and r + c < BOARDSIDE
                or f + c >= BOARDSIDE
                and r + c >= BOARDSIDE
            )
        ]
    )
    for r in range(BOARDSIDE)
    for f in range(BOARDSIDE)
]
_BOTTOMLEFT_TO_TOPRIGHT = [
    sum(
        [
            SQUARE_BITS[
                ((f - c) % BOARDSIDE) + ((r + c) % BOARDSIDE) * BOARDSIDE
            ]
            for c in range(BOARDSIDE)
            if f >= c and r + c < BOARDSIDE or c > f and r + c >= BOARDSIDE
        ]
    )
    for r in range(BOARDSIDE)
    for f in range(BOARDSIDE)
]

RANKS = [_RANKS[r * BOARDSIDE] for r in range(BOARDSIDE)]

FILES = _FILES[:BOARDSIDE]

ROOK_MOVES = [(_RANKS[k] | _FILES[k]) - s for k, s in enumerate(SQUARE_BITS)]

BISHOP_MOVES = [
    (_TOPLEFT_TO_BOTTOMRIGHT[k] | _BOTTOMLEFT_TO_TOPRIGHT[k]) - s
    for k, s in enumerate(SQUARE_BITS)
]

QUEEN_MOVES = [(BISHOP_MOVES[s] | ROOK_MOVES[s]) for s in range(BOARDSQUARES)]

KNIGHT_MOVES = [
    (
        (
            sum(
                _FILES[kf + r * BOARDSIDE]
                for kf in range(f - 2, f + 3)
                if kf >= 0 and kf < BOARDSIDE
            )
            & sum(
                _RANKS[f + kr * 8]
                for kr in range(r - 2, r + 3)
                if kr >= 0 and kr < BOARDSIDE
            )
        )
        & ~(
            _RANKS[f + r * BOARDSIDE]
            | _FILES[f + r * BOARDSIDE]
            | _TOPLEFT_TO_BOTTOMRIGHT[f + r * BOARDSIDE]
            | _BOTTOMLEFT_TO_TOPRIGHT[f + r * BOARDSIDE]
        )
    )
    for r in range(BOARDSIDE)
    for f in range(BOARDSIDE)
]

KING_MOVES = [
    (
        QUEEN_MOVES[f + r * BOARDSIDE]
        & (
            sum(
                _FILES[kf + r * BOARDSIDE]
                for kf in range(f - 1, f + 2)
                if kf >= 0 and kf < BOARDSIDE
            )
            & sum(
                _RANKS[f + kr * 8]
                for kr in range(r - 1, r + 2)
                if kr >= 0 and kr < BOARDSIDE
            )
        )
    )
    for r in range(BOARDSIDE)
    for f in range(BOARDSIDE)
]

WHITE_PAWN_MOVES_TO_SQUARE = []
for s in range(BOARDSQUARES):
    if s < BOARDSQUARES - BOARDSIDE * 2:
        WHITE_PAWN_MOVES_TO_SQUARE.append(SQUARE_BITS[s + BOARDSIDE])
    else:
        WHITE_PAWN_MOVES_TO_SQUARE.append(0)
for s in range(BOARDSQUARES - BOARDSIDE * 4, BOARDSQUARES - BOARDSIDE * 3):
    WHITE_PAWN_MOVES_TO_SQUARE[s] |= SQUARE_BITS[s + BOARDSIDE * 2]

BLACK_PAWN_MOVES_TO_SQUARE = []
for s in range(BOARDSQUARES):
    if s < BOARDSIDE * 2:
        BLACK_PAWN_MOVES_TO_SQUARE.append(0)
    else:
        BLACK_PAWN_MOVES_TO_SQUARE.append(SQUARE_BITS[s - BOARDSIDE])
for s in range(BOARDSIDE * 3, BOARDSIDE * 4):
    BLACK_PAWN_MOVES_TO_SQUARE[s] |= SQUARE_BITS[s - BOARDSIDE * 2]

# 'b1' for black, and 'b8' for white, are allowed as pawn move specifications
# to disambiguate queen moves like 'Qd1f1'.
# PAWN_MOVE_DESITINATION filters them out.
PAWN_MOVE_DESITINATION = [0, 0]
for s in range(BOARDSQUARES):
    if s < BOARDSIDE:
        pass
    elif s < BOARDSIDE * 2:
        PAWN_MOVE_DESITINATION[0] |= SQUARE_BITS[s]
    elif s < BOARDSQUARES - BOARDSIDE * 2:
        PAWN_MOVE_DESITINATION[0] |= SQUARE_BITS[s]
        PAWN_MOVE_DESITINATION[1] |= SQUARE_BITS[s]
    elif s < BOARDSQUARES - BOARDSIDE:
        PAWN_MOVE_DESITINATION[1] |= SQUARE_BITS[s]

WHITE_PAWN_CAPTURES_TO_SQUARE = []
for s in range(BOARDSQUARES):
    if s > BOARDSQUARES - BOARDSIDE * 2 - 1:
        WHITE_PAWN_CAPTURES_TO_SQUARE.append(0)
    elif s % BOARDSIDE == 0:
        WHITE_PAWN_CAPTURES_TO_SQUARE.append(SQUARE_BITS[s + BOARDSIDE + 1])
    elif s % BOARDSIDE == BOARDSIDE - 1:
        WHITE_PAWN_CAPTURES_TO_SQUARE.append(SQUARE_BITS[s + BOARDSIDE - 1])
    else:
        WHITE_PAWN_CAPTURES_TO_SQUARE.append(
            SQUARE_BITS[s + BOARDSIDE - 1] | SQUARE_BITS[s + BOARDSIDE + 1]
        )

BLACK_PAWN_CAPTURES_TO_SQUARE = []
for s in range(BOARDSQUARES):
    if s < BOARDSIDE * 2:
        BLACK_PAWN_CAPTURES_TO_SQUARE.append(0)
    elif s % BOARDSIDE == 0:
        BLACK_PAWN_CAPTURES_TO_SQUARE.append(SQUARE_BITS[s - BOARDSIDE + 1])
    elif s % BOARDSIDE == BOARDSIDE - 1:
        BLACK_PAWN_CAPTURES_TO_SQUARE.append(SQUARE_BITS[s - BOARDSIDE - 1])
    else:
        BLACK_PAWN_CAPTURES_TO_SQUARE.append(
            SQUARE_BITS[s - BOARDSIDE - 1] | SQUARE_BITS[s - BOARDSIDE + 1]
        )

GAPS = []
for f in range(BOARDSQUARES):
    GAPS.append(list())
    for t in range(BOARDSQUARES):
        aligned = (
            (_RANKS[f] & _RANKS[t])
            | (_FILES[f] & _FILES[t])
            | (_TOPLEFT_TO_BOTTOMRIGHT[f] & _TOPLEFT_TO_BOTTOMRIGHT[t])
            | (_BOTTOMLEFT_TO_TOPRIGHT[f] & _BOTTOMLEFT_TO_TOPRIGHT[t])
        )
        if not aligned:
            if SQUARE_BITS[t] & KNIGHT_MOVES[f]:
                GAPS[f].append(0)
            else:
                GAPS[f].append(ALL_SQUARES)
        else:
            gap = (
                aligned
                & sum(SQUARE_BITS[min(f, t) : max(f, t) + 1])
                & ~(SQUARE_BITS[f] | SQUARE_BITS[t])
            )
            if gap:
                GAPS[f].append(gap)
            elif f == t:
                GAPS[f].append(ALL_SQUARES)
            else:
                GAPS[f].append(0)

del _TOPLEFT_TO_BOTTOMRIGHT
del _BOTTOMLEFT_TO_TOPRIGHT
del _FILES
del _RANKS
del f, t, gap, aligned

PIECE_CAPTURE_MAP = {
    k: v
    for k, v in (
        (WKING, KING_MOVES),
        (WQUEEN, QUEEN_MOVES),
        (WROOK, ROOK_MOVES),
        (WBISHOP, BISHOP_MOVES),
        (WKNIGHT, KNIGHT_MOVES),
        (WPAWN, WHITE_PAWN_CAPTURES_TO_SQUARE),
        (BKING, KING_MOVES),
        (BQUEEN, QUEEN_MOVES),
        (BROOK, ROOK_MOVES),
        (BBISHOP, BISHOP_MOVES),
        (BKNIGHT, KNIGHT_MOVES),
        (BPAWN, BLACK_PAWN_CAPTURES_TO_SQUARE),
    )
}

PIECE_MOVE_MAP = {
    k: v
    for k, v in (
        (WKING, KING_MOVES),
        (WQUEEN, QUEEN_MOVES),
        (WROOK, ROOK_MOVES),
        (WBISHOP, BISHOP_MOVES),
        (WKNIGHT, KNIGHT_MOVES),
        (WPAWN, WHITE_PAWN_MOVES_TO_SQUARE),
        (BKING, KING_MOVES),
        (BQUEEN, QUEEN_MOVES),
        (BROOK, ROOK_MOVES),
        (BBISHOP, BISHOP_MOVES),
        (BKNIGHT, KNIGHT_MOVES),
        (BPAWN, BLACK_PAWN_MOVES_TO_SQUARE),
    )
}

# Lookup tables for string representation of square and move numbers.
MAP_FEN_ORDER_TO_PGN_SQUARE_NAME = [
    t[-1]
    for t in sorted(
        (v, k) for k, v in MAP_PGN_SQUARE_NAME_TO_FEN_ORDER.items()
    )
]
MOVE_NUMBER_KEYS = tuple(
    ["0"] + [str(len(hex(i)) - 2) + hex(i)[2:] for i in range(1, 256)]
)

# Error markers for PGN display.
ERROR_START_COMMENT = START_COMMENT + "Error: "
ESCAPE_END_COMMENT = "::" + START_COMMENT + START_COMMENT + "::"
# end of attributes copied from pgn_read.core.constants

# Defined in chesstab.core.chessrecord.
PLAYER_NAME_TAGS = frozenset((TAG_WHITE, TAG_BLACK))

# Imported from chesstab.core.querystatement.
re_normalize_player_name = re.compile("([^,\.\s]+)(?:[,\.\s]*)")

# The two chessql.core.constants attributes needed.
ANY_WHITE_PIECE_NAME = r"A"
ANY_BLACK_PIECE_NAME = r"a"

MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE = {
    WKING: ANY_WHITE_PIECE_NAME,
    WQUEEN: ANY_WHITE_PIECE_NAME,
    WROOK: ANY_WHITE_PIECE_NAME,
    WBISHOP: ANY_WHITE_PIECE_NAME,
    WKNIGHT: ANY_WHITE_PIECE_NAME,
    WPAWN: ANY_WHITE_PIECE_NAME,
    BKING: ANY_BLACK_PIECE_NAME,
    BQUEEN: ANY_BLACK_PIECE_NAME,
    BROOK: ANY_BLACK_PIECE_NAME,
    BBISHOP: ANY_BLACK_PIECE_NAME,
    BKNIGHT: ANY_BLACK_PIECE_NAME,
    BPAWN: ANY_BLACK_PIECE_NAME,
}

re_tokens = re.compile(IMPORT_FORMAT)

# Avoid re.fullmatch() method while compatibility with Python 3.3 is important.
re_disambiguate_error = re.compile(DISAMBIGUATE_FORMAT.join(("^", "$")))
re_disambiguate_non_move = re.compile(UNAMBIGUOUS_FORMAT.join(("^", "$")))
re_possible_move = re.compile(POSSIBLE_MOVE.join(("(^", "$)")))

# for runtime "from <db|dpt>results import ChessDatabase" and similar
_ChessDB = "ChessDatabase"
_FullPositionDS = "FullPositionDS"
_AnalysisDS = "AnalysisDS"


class PGN131Error(Exception):
    pass


class PGN131(object):
    def __init__(self):
        super().__init__()

        # data generated from PGN text for game while checking moves are legal
        self.tokens = []
        self.error_tokens = []
        self.tags_in_order = []

        # data generated from PGN text for game after checking moves are legal
        self.collected_game = None
        self.board_bitmap = None
        self.occupied_squares = []
        self.board = []
        self.piece_locations = {}
        self.fullmove_number = None
        self.halfmove_count = None
        self.en_passant = None
        self.castling = None
        self.active_side = None

        # ravstack keeps track of the position at start of game or variation
        # and the position after application of a valid move.  Thus the value
        # in ravstack[-1] is (None, <position start>) at start of game or line
        # and (<position start>, <position after move>) after application of a
        # valid move from gametokens.
        self.ravstack = []

        # data used while parsing PGN text to split into tag and move tokens
        self._initial_fen = None
        self._state = None
        self._move_error_state = None
        self._rewind_state = None

        self._despatch_table = [
            self._searching,
            self._searching_after_error_in_rav,
            self._searching_after_error_in_game,
            self._collecting_tag_pairs,
            self._collecting_movetext,
            self._collecting_non_whitespace_while_searching,
            self._disambiguate_move,
        ]

    @staticmethod
    def _read_pgn(string, length):
        pgntext = string.read(length)
        while len(pgntext):
            yield pgntext
            pgntext = string.read(length)
        yield pgntext

    def read_games(self, source, size=10000000, housekeepinghook=lambda: None):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        for pgntext in self._read_pgn(source, size):
            if len(self.error_tokens):
                self._state = self._rewind_state
                pgntext = "".join(self.error_tokens) + pgntext
                self.error_tokens.clear()
            for t in re_tokens.finditer(pgntext):
                self._despatch_table[self._state](t)
                if t.group(IFG_TERMINATION):
                    yield t
            housekeepinghook()

    def read_pgn_tokens(
        self, source, size=10000000, housekeepinghook=lambda: None
    ):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        for pgntext in self._read_pgn(source, size):
            if len(self.error_tokens):
                self._state = self._rewind_state
                pgntext = "".join(self.error_tokens) + pgntext
                self.error_tokens.clear()
            for t in re_tokens.finditer(pgntext):
                self._despatch_table[self._state](t)
                yield t.group(IFG_TERMINATION)

    def get_games(self, source):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        for t in re_tokens.finditer(source):
            self._despatch_table[self._state](t)
            if t.group(IFG_TERMINATION):
                yield t

    def get_first_pgn_token(self, source):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        try:
            t = next(re_tokens.finditer(source))
            self._despatch_table[self._state](t)
            return False if t.group(IFG_TERMINATION) else True
        except StopIteration:
            return

    def read_first_game(
        self, source, size=10000000, housekeepinghook=lambda: None
    ):
        return next(
            self.read_games(
                source, size=size, housekeepinghook=housekeepinghook
            )
        )

    def get_first_game(self, source):
        return next(self.get_games(source))

    def is_movetext_valid(self):
        return not self.collected_game[3]

    def is_pgn_valid(self):
        return self.is_movetext_valid() and self.is_tag_roster_valid()

    def is_tag_roster_valid(self):
        tags_in_order = self.collected_game[0]
        tags = self.collected_game[1]
        if len(tags) != len(tags_in_order):
            # Tag must appear no more than once
            return False
        for v in tags.values():
            if len(v) == 0:
                # Tag value must not be null
                return False
        for t in SEVEN_TAG_ROSTER:
            if t not in tags:
                # A mandatory tag is missing
                return False
        return True

    def set_position_fen(self, fen=None):
        # fen is standard start position by default
        if fen is None:
            self.board_bitmap = INITIAL_BOARD_BITMAP
            self.board = list(INITIAL_BOARD)
            self.occupied_squares[:] = [
                set(s) for s in INITIAL_OCCUPIED_SQUARES
            ]
            self.piece_locations = {
                k: set(v) for k, v in INITIAL_PIECE_LOCATIONS.items()
            }
            self.ravstack[:] = [
                (
                    None,
                    (
                        INITIAL_BOARD,
                        WHITE_SIDE,
                        FEN_INITIAL_CASTLING,
                        FEN_NULL,
                        FEN_INITIAL_HALFMOVE_COUNT,
                        FEN_INITIAL_FULLMOVE_NUMBER,
                    ),
                )
            ]
            self.active_side = WHITE_SIDE
            self.castling = FEN_INITIAL_CASTLING
            self.en_passant = FEN_NULL
            self.halfmove_count = FEN_INITIAL_HALFMOVE_COUNT
            self.fullmove_number = FEN_INITIAL_FULLMOVE_NUMBER
            self._initial_fen = True
            return

        # fen specifies an arbitrary position.

        # fen has six space delimited fields.
        fs = fen.split(FEN_FIELD_DELIM)
        if len(fs) != FEN_FIELD_COUNT:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        (
            piece_placement,
            active_side,
            castling,
            en_passant,
            halfmove_count,
            fullmove_number,
        ) = fs
        del fs

        # fen side to move field.
        if active_side not in FEN_SIDES:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen castling field.
        if castling != FEN_NULL:
            for c in FEN_INITIAL_CASTLING:
                if castling.count(c) > FEN_CASTLING_OPTION_REPEAT_MAX:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
            for c in castling:
                if c not in FEN_INITIAL_CASTLING:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return

        # fen square to which a pawn can move when capturing en passant.
        if active_side == FEN_WHITE:
            if en_passant not in FEN_WHITE_MOVE_TO_EN_PASSANT:
                if en_passant != FEN_NULL:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
        elif active_side == FEN_BLACK:
            if en_passant not in FEN_BLACK_MOVE_TO_EN_PASSANT:
                if en_passant != FEN_NULL:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return

        # Earlier 'fen side to move field' test makes this unreachable.
        else:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen halfmove count since pawn move or capture.
        if not halfmove_count.isdigit():
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen fullmove number.
        if not fullmove_number.isdigit():
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen piece placement field has eight ranks delimited by '/'.
        ranks = piece_placement.split(FEN_RANK_DELIM)
        if len(ranks) != BOARDSIDE:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen piece placement field has pieces and empty squares only.
        for r in ranks:
            for c in r:
                if c not in PIECES:
                    if not c.isdigit():
                        self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                        return

        # Exactly 64 squares: equivalent to exactly 8 squares per rank.
        for r in ranks:
            if sum([1 if not s.isdigit() else int(s) for s in r]) != BOARDSIDE:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # No pawns on first or eighth ranks.
        if (
            ranks[0].count(WPAWN)
            + ranks[0].count(BPAWN)
            + ranks[BOARDSIDE - 1].count(WPAWN)
            + ranks[BOARDSIDE - 1].count(BPAWN)
        ):
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # No more than 16 pieces per side.
        for s in WPIECES, BPIECES:
            for p in s:
                if (
                    sum([piece_placement.count(p) for p in s])
                    > FEN_PIECE_COUNT_PER_SIDE_MAX
                ):
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return

        # Exactly one king per side.
        for p in WKING, BKING:
            if piece_placement.count(p) != FEN_KING_COUNT:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # No more than eight pawns per side.
        for p in WPAWN, BPAWN:
            if piece_placement.count(p) > FEN_PAWN_COUNT_MAX:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # Piece counts within initial position and pawn promotion bounds.
        if (
            piece_placement.count(WPAWN)
            - FEN_PAWN_COUNT_MAX
            + max(piece_placement.count(WQUEEN) - FEN_QUEEN_COUNT_INITIAL, 0)
            + max(piece_placement.count(WROOK) - FEN_ROOK_COUNT_INITIAL, 0)
            + max(piece_placement.count(WBISHOP) - FEN_BISHOP_COUNT_INITIAL, 0)
            + max(piece_placement.count(WKNIGHT) - FEN_KNIGHT_COUNT_INITIAL, 0)
        ) > 0:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if (
            piece_placement.count(BPAWN)
            - FEN_PAWN_COUNT_MAX
            + max(piece_placement.count(BQUEEN) - FEN_QUEEN_COUNT_INITIAL, 0)
            + max(piece_placement.count(BROOK) - FEN_ROOK_COUNT_INITIAL, 0)
            + max(piece_placement.count(BBISHOP) - FEN_BISHOP_COUNT_INITIAL, 0)
            + max(piece_placement.count(BKNIGHT) - FEN_KNIGHT_COUNT_INITIAL, 0)
        ) > 0:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # Position is legal apart from checks, actual and deduced, and deduced
        # move that sets up en passant capture possibility.
        board = []
        for r in ranks:
            for c in r:
                if c in PIECES:
                    board.append(c)
                else:
                    board.extend([NOPIECE] * int(c))

        # Castling availability must fit the board position.
        if board[CASTLING_W] != WKING:
            if WKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
            if WQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_B] != BKING:
            if BKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
            if BQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_WK] != WROOK:
            if WKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_WQ] != WROOK:
            if WQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_BK] != BROOK:
            if BKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_BQ] != BROOK:
            if BQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # the two squares behind the pawn that can be captured en passant
        # must be empty. FEN quotes en passant capture square if latest move
        # is a two square pawn move,there does not need to be a pawn able to
        # make the capture. The side with the move must not be in check
        # diagonally through the square containing a pawn that can be captured
        # en passant, treating that square as empty.
        if en_passant != FEN_NULL:
            if en_passant in FEN_WHITE_MOVE_TO_EN_PASSANT:
                s = FEN_WHITE_MOVE_TO_EN_PASSANT[en_passant]
                if (
                    board[s] != NOPIECE
                    or board[s - 8] != NOPIECE
                    or board[s + 8] != BPAWN
                ):
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
            elif en_passant in FEN_BLACK_MOVE_TO_EN_PASSANT:
                s = FEN_BLACK_MOVE_TO_EN_PASSANT[en_passant]
                if (
                    board[s] != NOPIECE
                    or board[s + 8] != NOPIECE
                    or board[s - 8] != WPAWN
                ):
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
            else:

                # Should not happen, caught earlier.
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # FEN is legal, except for restrictions on kings in check, so set
        # instance attributes to fit description of position.
        piece_locations = {k: set() for k in INITIAL_PIECE_LOCATIONS}
        active_side_squares = set()
        inactive_side_squares = set()
        board_bitmap = []
        if active_side == FEN_WHITE:
            active_side_pieces = WPIECES
        else:
            active_side_pieces = BPIECES
        for s, p in enumerate(board):
            if p in PIECES:
                piece_locations[p].add(s)
                board_bitmap.append(SQUARE_BITS[s])
                if p in active_side_pieces:
                    active_side_squares.add(s)
                else:
                    inactive_side_squares.add(s)
        for active_side_king_square in piece_locations[
            SIDE_KING[FEN_SIDES[active_side]]
        ]:
            pass  # set active_side_king_square without pop() and add().
        for inactive_side_king_square in piece_locations[
            SIDE_KING[OTHER_SIDE[FEN_SIDES[active_side]]]
        ]:
            pass  # set active_side_king_square without pop() and add().

        # Side without the move must not be in check.
        # Cannot use is_active_king_attacked method because attributes are
        # not set until the position is ok.
        gap = GAPS[inactive_side_king_square]
        board_bitmap = sum(board_bitmap)
        for s in active_side_squares:
            if (
                not board_bitmap & gap[s]
                and SQUARE_BITS[s]
                & PIECE_CAPTURE_MAP[board[s]][inactive_side_king_square]
            ):
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # Side with the move must not be in check from more than two squares.
        # Cannot use count_attacks_on_square_by_side method because attributes
        # are not set until the position is ok.
        gap = GAPS[active_side_king_square]
        if (
            len(
                [
                    s
                    for s in inactive_side_squares
                    if (
                        not board_bitmap & gap[s]
                        and SQUARE_BITS[s]
                        & PIECE_CAPTURE_MAP[board[s]][active_side_king_square]
                    )
                ]
            )
            > FEN_MAXIMUM_PIECES_GIVING_CHECK
        ):
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        self.board_bitmap = board_bitmap
        self.board = board
        if active_side == FEN_WHITE:
            self.occupied_squares[:] = (
                active_side_squares,
                inactive_side_squares,
            )
        else:
            self.occupied_squares[:] = (
                inactive_side_squares,
                active_side_squares,
            )
        self.piece_locations = piece_locations
        self.ravstack[:] = [
            (
                None,
                (
                    tuple(board),
                    FEN_SIDES[active_side],
                    castling,
                    en_passant,
                    int(halfmove_count),
                    int(fullmove_number),
                ),
            )
        ]
        self.active_side = FEN_SIDES[active_side]
        self.castling = castling
        self.en_passant = en_passant
        self.halfmove_count = int(halfmove_count)
        self.fullmove_number = int(fullmove_number)
        self._initial_fen = fen

    def _play_move(
        self, pgn_piece, pgn_from, pgn_capture, pgn_tosquare, pgn_promote
    ):
        tosquare = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[pgn_tosquare]
        piece = MAPPIECE[self.active_side][pgn_piece]
        g = GAPS[tosquare]
        b = self.board
        bb = self.board_bitmap
        if pgn_capture == CAPTURE_MOVE:
            pts = PIECE_CAPTURE_MAP[piece][tosquare]
        else:
            pts = PIECE_MOVE_MAP[piece][tosquare]
        from_squares = [
            s
            for s in self.piece_locations[piece]
            if (SQUARE_BITS[s] & pts and not bb & g[s])
        ]
        if len(from_squares) > 1:
            if pgn_from:
                fm = MAPFILE.get(pgn_from[0])
                if fm is not None:
                    fm = FILES[fm]
                    from_squares = [
                        s for s in from_squares if SQUARE_BITS[s] & fm
                    ]
                if len(from_squares) > 1:
                    fm = MAPROW.get(pgn_from[-1])
                    if fm is not None:
                        fm = RANKS[fm]
                        from_squares = [
                            s for s in from_squares if SQUARE_BITS[s] & fm
                        ]
            if len(from_squares) > 1:
                inactive_side_squares = self.occupied_squares[
                    OTHER_SIDE[self.active_side]
                ]
                for active_side_king_square in self.piece_locations[
                    SIDE_KING[self.active_side]
                ]:
                    pass  # set active_side_king_square without pop() and add().
                gk = GAPS[active_side_king_square]
                pinned_to_king = set()
                for si in inactive_side_squares:
                    if (
                        PIECE_CAPTURE_MAP[b[si]][active_side_king_square]
                        & SQUARE_BITS[si]
                    ):
                        for s in from_squares:
                            if gk[si] & SQUARE_BITS[s]:
                                if not (
                                    (
                                        bb ^ SQUARE_BITS[s]
                                        | SQUARE_BITS[tosquare]
                                    )
                                    & gk[si]
                                ):
                                    if si != tosquare:
                                        pinned_to_king.add(s)
                from_squares = [
                    s for s in from_squares if s not in pinned_to_king
                ]
        if pgn_capture == PLAIN_MOVE and b[tosquare] == piece:

            # If moving piece is on tosquare and the next token is a square
            # identity try tosquare as fromsquare and next token as tosquare
            # for the piece move.
            # Only applies to Q B N non-capture moves where the moving side
            # has more than 2 of the moving piece so it is possible there
            # are two pieces of the moving kind on the same rank and the
            # same file at the same time which can reach the tosquare.
            # Check that there are at least three pieces of one kind which
            # can move to the same square and note the possibilities for
            # evaluation in two subsequent states where the next tokens are
            # readily available for comparison.  The next two tokens must be
            # '' and a square identity and the square identity must be one
            # of the possibilities.
            if b.count(piece) > 2:
                if pgn_piece in PGN_FROM_SQUARE_DISAMBIGUATION:
                    self._state = PGN_DISAMBIGUATE_MOVE
                    self._rewind_state = self._state
                    return

            self._illegal_play_move()
            return

        # After the disambiguation test, plain move to square containing piece
        # which is moving, because queen moves like both rook and bishop.
        if len(from_squares) != 1:
            self._illegal_play_move()
            return

        piece_locations = self.piece_locations
        fromsquare = from_squares.pop()

        # pgn_from is null, a file name, a rank name, or a square name.  If not
        # null it must be part of, or equal, the square name of fromsquare.
        if pgn_from is not None:
            if pgn_from not in MAP_FEN_ORDER_TO_PGN_SQUARE_NAME[fromsquare]:
                self._illegal_play_move()
                return

        if pgn_capture == CAPTURE_MOVE:
            inactive_side_squares = self.occupied_squares[
                OTHER_SIDE[self.active_side]
            ]
            if tosquare not in inactive_side_squares:
                if pgn_piece != PGN_PAWN:
                    self._illegal_play_move()
                    return
                elif pgn_tosquare != self.en_passant:
                    self._illegal_play_move()
                    return

                # Remove pawn captured en passant.
                elif self.en_passant in FEN_WHITE_CAPTURE_EN_PASSANT:
                    eps = FEN_WHITE_CAPTURE_EN_PASSANT[self.en_passant]
                    b[eps] = NOPIECE
                    inactive_side_squares.remove(eps)
                    piece_locations[BPAWN].remove(eps)
                    self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[eps]
                elif self.en_passant in FEN_BLACK_CAPTURE_EN_PASSANT:
                    eps = FEN_BLACK_CAPTURE_EN_PASSANT[self.en_passant]
                    b[eps] = NOPIECE
                    inactive_side_squares.remove(eps)
                    piece_locations[WPAWN].remove(eps)
                    self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[eps]

                else:
                    self._illegal_play_move()
                    return

            else:
                inactive_side_squares.remove(tosquare)
                piece_locations[b[tosquare]].remove(tosquare)
            self.en_passant = FEN_NULL
            self.halfmove_count = 0
        elif SQUARE_BITS[tosquare] & bb:
            self._illegal_play_move()
            return
        elif pgn_piece == PGN_PAWN:

            # Moves like 'b1' for black, and 'b8' for white, are passed earlier
            # to cope with disambiguating queen moves like 'Qd1f1'.
            if not (
                SQUARE_BITS[tosquare]
                & PAWN_MOVE_DESITINATION[self.active_side]
            ):
                if not pgn_promote:
                    self._illegal_play_move()
                    return

            self.halfmove_count = 0
            if (
                SQUARE_BITS[fromsquare] & EN_PASSANT_FROM_SQUARES
                and SQUARE_BITS[tosquare] & EN_PASSANT_TO_SQUARES
            ):
                self.en_passant = (
                    pgn_tosquare[0]
                    + FEN_EN_PASSANT_TARGET_RANK[pgn_tosquare[1]]
                )
            else:
                self.en_passant = FEN_NULL
        else:
            self.en_passant = FEN_NULL
            self.halfmove_count = self.halfmove_count + 1
        active_side_squares = self.occupied_squares[self.active_side]

        # Remove moving piece from current square.
        b[fromsquare] = NOPIECE
        active_side_squares.remove(fromsquare)
        piece_locations[piece].remove(fromsquare)
        self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[fromsquare]

        # Put moving piece on new square.
        b[tosquare] = piece
        active_side_squares.add(tosquare)
        piece_locations[piece].add(tosquare)
        self.board_bitmap |= SQUARE_BITS[tosquare]

        # Replace moving pawn on promotion and update inactive king square.
        if pgn_promote:
            piece_locations[b[tosquare]].remove(tosquare)
            b[tosquare] = MAPPIECE[self.active_side][pgn_promote]
            piece_locations[b[tosquare]].add(tosquare)

        # Undo move if it leaves king in check.
        if self.is_active_king_attacked():
            self.reset_position(self.ravstack[-1][-1])
            self._illegal_play_move()
            return

        # Castling availabity.
        # tosquare tests deal with capture of rooks which have not moved.
        # For real games the top condition is false for more than half the game
        # and the next condition is usually false.
        if self.castling != FEN_NULL:
            if (
                SQUARE_BITS[fromsquare] | SQUARE_BITS[tosquare]
            ) & CASTLING_AVAILABITY_SQUARES:
                if fromsquare == CASTLING_W:
                    self.castling = self.castling.replace(WKING, NOPIECE)
                    self.castling = self.castling.replace(WQUEEN, NOPIECE)
                elif fromsquare == CASTLING_WK:
                    self.castling = self.castling.replace(WKING, NOPIECE)
                elif fromsquare == CASTLING_WQ:
                    self.castling = self.castling.replace(WQUEEN, NOPIECE)
                elif fromsquare == CASTLING_B:
                    self.castling = self.castling.replace(BKING, NOPIECE)
                    self.castling = self.castling.replace(BQUEEN, NOPIECE)
                elif fromsquare == CASTLING_BK:
                    self.castling = self.castling.replace(BKING, NOPIECE)
                elif fromsquare == CASTLING_BQ:
                    self.castling = self.castling.replace(BQUEEN, NOPIECE)
                elif tosquare == CASTLING_WK:
                    self.castling = self.castling.replace(WKING, NOPIECE)
                elif tosquare == CASTLING_WQ:
                    self.castling = self.castling.replace(WQUEEN, NOPIECE)
                elif tosquare == CASTLING_BK:
                    self.castling = self.castling.replace(BKING, NOPIECE)
                elif tosquare == CASTLING_BQ:
                    self.castling = self.castling.replace(BQUEEN, NOPIECE)
                if self.castling == NOPIECE:
                    self.castling = FEN_NULL

        self.add_move_to_game()

    def _play_castles(self, token):

        # Verify castling availability and pick castling rules.
        if token.startswith(O_O_O):
            if self.active_side == WHITE_SIDE:
                if WQUEEN not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[WQUEEN]
            else:
                if BQUEEN not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[BQUEEN]
        elif token.startswith(O_O):
            if self.active_side == WHITE_SIDE:
                if WKING not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[WKING]
            else:
                if BKING not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[BKING]
        else:
            self._illegal_play_castles()
            return

        bb = self.board_bitmap
        board = self.board
        piece_locations = self.piece_locations
        active_side_squares = self.occupied_squares[self.active_side]
        active_side_king_locations = piece_locations[
            SIDE_KING[self.active_side]
        ]
        if self.active_side == WHITE_SIDE:
            active_side_rook_locations = piece_locations[WROOK]
        else:
            active_side_rook_locations = piece_locations[BROOK]
        for active_side_king_square in active_side_king_locations:
            pass  # set active_side_king_square without pop() and add().

        # Confirm board position is consistent with castling availability.
        if (
            active_side_king_square != castling_squares[0]
            or board[castling_squares[0]] != castling_squares[5]
            or board[castling_squares[1]] != castling_squares[4]
        ):
            self._illegal_play_castles()
            return

        # Squares between king and castling rook must be empty.
        for squares in castling_squares[2:4]:
            for s in squares:
                if SQUARE_BITS[s] & bb:
                    self._illegal_play_castles()
                    return

        # Castling king must not be in check.
        if self.is_square_attacked_by_side(
            castling_squares[0], OTHER_SIDE[self.active_side]
        ):
            self._illegal_play_castles()
            return

        # Castling king's destination square, and the one between, must not be
        # attacked by the other side.
        for square in castling_squares[2]:
            if self.is_square_attacked_by_side(
                square, OTHER_SIDE[self.active_side]
            ):
                self._illegal_play_castles()
                return

        king_square = castling_squares[0]
        new_king_square = castling_squares[2][1]
        rook_square = castling_squares[1]
        new_rook_square = castling_squares[2][0]

        # Put moving pieces on new squares.
        board[new_king_square] = board[king_square]
        board[new_rook_square] = board[rook_square]
        active_side_squares.add(new_king_square)
        active_side_king_locations.add(new_king_square)
        active_side_squares.add(new_rook_square)
        active_side_rook_locations.add(new_rook_square)
        self.board_bitmap |= (
            SQUARE_BITS[new_king_square] | SQUARE_BITS[new_rook_square]
        )

        # Remove moving pieces from current squares.
        board[king_square] = NOPIECE
        board[rook_square] = NOPIECE
        active_side_squares.remove(king_square)
        active_side_king_locations.remove(king_square)
        active_side_squares.remove(rook_square)
        active_side_rook_locations.remove(rook_square)
        self.board_bitmap &= self.board_bitmap ^ (
            SQUARE_BITS[king_square] | SQUARE_BITS[rook_square]
        )

        # Castling availabity.
        if self.active_side == WHITE_SIDE:
            self.castling = self.castling.replace(WKING, NOPIECE)
            self.castling = self.castling.replace(WQUEEN, NOPIECE)
        else:
            self.castling = self.castling.replace(BKING, NOPIECE)
            self.castling = self.castling.replace(BQUEEN, NOPIECE)
        if self.castling == NOPIECE:
            self.castling = FEN_NULL

        # Cannot be en-passant
        self.en_passant = FEN_NULL

        self.halfmove_count = self.halfmove_count + 1
        self.add_move_to_game()

    def is_active_king_attacked(self):
        b = self.board
        bb = self.board_bitmap

        # Only one element in this container.
        for ks in self.piece_locations[SIDE_KING[self.active_side]]:
            g = GAPS[ks]
            for s in self.occupied_squares[OTHER_SIDE[self.active_side]]:
                if (
                    not bb & g[s]
                    and SQUARE_BITS[s] & PIECE_CAPTURE_MAP[b[s]][ks]
                ):
                    return True
        return False

    def is_square_attacked_by_side(self, square, side):
        g = GAPS[square]
        b = self.board
        bb = self.board_bitmap
        for s in self.occupied_squares[side]:
            if (
                not bb & g[s]
                and SQUARE_BITS[s] & PIECE_CAPTURE_MAP[b[s]][square]
            ):
                return True
        return False

    def count_attacks_on_square_by_side(self, square, side):
        g = GAPS[square]
        b = self.board
        bb = self.board_bitmap
        return len(
            [
                s
                for s in self.occupied_squares[side]
                if (
                    not bb & g[s]
                    and SQUARE_BITS[s] & PIECE_CAPTURE_MAP[b[s]][square]
                )
            ]
        )

    def add_move_to_game(self):
        self.active_side = OTHER_SIDE[self.active_side]
        if self.active_side == WHITE_SIDE:
            self.fullmove_number += 1
        self.ravstack[-1] = (
            self.ravstack[-1][-1],
            (
                tuple(self.board),
                self.active_side,
                self.castling,
                self.en_passant,
                self.halfmove_count,
                self.fullmove_number,
            ),
        )

    def collect_token(self, match):
        self.tokens.append(match)

    def collect_game_tokens(self):
        self.collected_game = (
            self.tags_in_order,
            {
                m.group(IFG_TAG_SYMBOL): m.group(IFG_TAG_STRING_VALUE)
                for m in self.tags_in_order
            },
            self.tokens,
            self.error_tokens,
        )

    def _play_disambiguated_move(
        self, pgn_piece, pgn_fromsquare, pgn_tosquare
    ):
        fromsquare = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[pgn_fromsquare]
        tosquare = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[pgn_tosquare]
        piece = MAPPIECE[self.active_side][pgn_piece]
        if fromsquare not in self.piece_locations[piece]:
            self._illegal_play_disambiguated_move()
            return
        if not (
            SQUARE_BITS[fromsquare] & PIECE_MOVE_MAP[piece][tosquare]
            and not self.board_bitmap & GAPS[tosquare][fromsquare]
        ):
            self._illegal_play_disambiguated_move()
            return
        if SQUARE_BITS[tosquare] & self.board_bitmap:
            self._illegal_play_disambiguated_move()
            return
        else:
            self.halfmove_count = self.halfmove_count + 1
        b = self.board
        piece_locations = self.piece_locations
        active_side_squares = self.occupied_squares[self.active_side]

        # Remove moving piece from current square.
        b[fromsquare] = NOPIECE
        active_side_squares.remove(fromsquare)
        piece_locations[piece].remove(fromsquare)
        self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[fromsquare]

        # Put moving piece on new square.
        b[tosquare] = piece
        active_side_squares.add(tosquare)
        piece_locations[piece].add(tosquare)
        self.board_bitmap |= SQUARE_BITS[tosquare]

        # Undo move if it leaves king in check.
        if self.is_active_king_attacked():
            self.reset_position(self.ravstack[-1][-1])
            self._illegal_play_disambiguated_move()
            return

        # Castling availabity is not affected because rooks cannot be involved
        # in moves which need disambiguation.

        # Cannot be en-passant
        self.en_passant = FEN_NULL

        self.add_move_to_game()

    # Maybe should not be a method now, but retain shape of pre-FEN class code
    # for ease of comparison until sure everything works.
    # Just say self._fen = ... where method is called.
    def reset_position(self, position):
        (
            board,
            self.active_side,
            self.castling,
            self.en_passant,
            self.halfmove_count,
            self.fullmove_number,
        ) = position
        self.board[:] = list(board)
        occupied_squares = self.occupied_squares
        for side in occupied_squares:
            side.clear()
        piece_locations = self.piece_locations
        for piece in piece_locations.values():
            piece.clear()
        board_bitmap = 0
        for square, piece in enumerate(board):
            if piece in WPIECES:
                occupied_squares[0].add(square)
                piece_locations[piece].add(square)
                board_bitmap |= SQUARE_BITS[square]
            elif piece in BPIECES:
                occupied_squares[1].add(square)
                piece_locations[piece].add(square)
                board_bitmap |= SQUARE_BITS[square]
        self.board_bitmap = board_bitmap

    def _start_variation(self):
        self.ravstack.append((None, self.ravstack[-1][0]))
        self.reset_position(self.ravstack[-1][-1])

    def _end_variation(self):
        try:
            del self.ravstack[-1]
            try:
                self.reset_position(self.ravstack[-1][-1])
            except:
                pass
        except:
            pass

    def _searching(self, match):
        mg = match.group
        if mg(IFG_START_TAG):
            self.tags_in_order.append(match)
            if mg(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(mg(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if mg(IFG_PIECE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_MOVE), "", "", mg(IFG_PIECE_SQUARE), ""
            )
            return
        if mg(IFG_PAWN_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move("", "", "", mg(IFG_PAWN_SQUARE), "")
            return
        if mg(IFG_PIECE_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CAPTURE) or mg(IFG_KING_CAPTURE),
                mg(IFG_PIECE_CAPTURE_FROM),
                mg(IFG_PIECE_TAKES),
                mg(IFG_PIECE_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PAWN_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_CAPTURE_FROM_FILE),
                mg(IFG_PAWN_TAKES),
                mg(IFG_PAWN_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PIECE_CHOICE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CHOICE),
                mg(IFG_PIECE_CHOICE_FILE_OR_RANK),
                "",
                mg(IFG_PIECE_CHOICE_SQUARE),
                "",
            )
            return
        if mg(IFG_CASTLES):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_castles(mg(IFG_CASTLES))
            return
        if mg(IFG_PAWN_PROMOTE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_PROMOTE_FROM_FILE),
                mg(IFG_PAWN_TAKES_PROMOTE),
                mg(IFG_PAWN_PROMOTE_SQUARE),
                mg(IFG_PAWN_PROMOTE_PIECE)[1],
            )
            return
        if mg(IFG_COMMENT):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_NAG):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_COMMENT_TO_EOL):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return

        # The captured tokens not accepted when searching for start of game.
        if mg(IFG_START_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
            return
        if mg(IFG_END_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
            return
        if mg(IFG_TERMINATION):
            self._termination_while_searching(match)
            return

        # Action for non-captured groups is decided by looking at whole token.
        string = mg()

        if not string.strip():
            return
        if string.isdigit():
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return
        if string == FULLSTOP:
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return

        # Only other groups with length > 1:
        # '<reserved>'
        # '%escaped\n'
        # are not captured and are ignored.
        if len(string) > 1:
            return

        self.error_tokens.append(string)
        self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        return

    def _searching_after_error_in_rav(self, match):
        if match.group(IFG_START_RAV):
            self.error_tokens.append(match.group())
            self._ravstack_length += 1
            return
        if match.group(IFG_END_RAV):
            if self._ravstack_length == len(self.ravstack):
                self._convert_error_tokens_to_token()
                self.collect_token(match)
                self._end_variation()
                self.error_tokens = []
                self._state = PGN_COLLECTING_MOVETEXT
                self._rewind_state = self._state
                if self._ravstack_length > 2:
                    self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_RAV
                else:
                    self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                del self._ravstack_length
            else:
                self.error_tokens.append(match.group())
                self._ravstack_length -= 1
            return
        if match.group(IFG_TERMINATION):
            self._convert_error_tokens_to_token()
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            del self._ravstack_length
            return
        if match.group(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if match.group(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(match.group(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            del self._ravstack_length
            return
        self.error_tokens.append(match.group())

    def _searching_after_error_in_game(self, match):
        if match.group(IFG_TERMINATION):
            self._convert_error_tokens_to_token()
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            return
        if match.group(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if match.group(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(match.group(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        self.error_tokens.append(match.group())

    def _collecting_tag_pairs(self, match):
        mg = match.group
        if mg(IFG_START_TAG):
            self.tags_in_order.append(match)
            if mg(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(mg(IFG_TAG_STRING_VALUE))
            return
        if mg(IFG_PIECE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_MOVE), "", "", mg(IFG_PIECE_SQUARE), ""
            )
            return
        if mg(IFG_PAWN_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move("", "", "", mg(IFG_PAWN_SQUARE), "")
            return
        if mg(IFG_PIECE_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CAPTURE) or mg(IFG_KING_CAPTURE),
                mg(IFG_PIECE_CAPTURE_FROM),
                mg(IFG_PIECE_TAKES),
                mg(IFG_PIECE_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PAWN_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_CAPTURE_FROM_FILE),
                mg(IFG_PAWN_TAKES),
                mg(IFG_PAWN_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PIECE_CHOICE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CHOICE),
                mg(IFG_PIECE_CHOICE_FILE_OR_RANK),
                "",
                mg(IFG_PIECE_CHOICE_SQUARE),
                "",
            )
            return
        if mg(IFG_CASTLES):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_castles(mg(IFG_CASTLES))
            return
        if mg(IFG_PAWN_PROMOTE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_PROMOTE_FROM_FILE),
                mg(IFG_PAWN_TAKES_PROMOTE),
                mg(IFG_PAWN_PROMOTE_SQUARE),
                mg(IFG_PAWN_PROMOTE_PIECE)[1],
            )
            return
        if mg(IFG_TERMINATION):
            if not self._initial_fen:
                self.set_position_fen()
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            return
        if mg(IFG_COMMENT):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_NAG):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_COMMENT_TO_EOL):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return

        # The captured tokens not accepted when searching for tag pairs.
        if mg(IFG_START_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if mg(IFG_END_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # Action for non-captured groups is decided by looking at whole token.
        string = mg()

        if not string.strip():
            return
        if string.isdigit():
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return
        if string == FULLSTOP:
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return

        # Only other groups with length > 1:
        # '<reserved>'
        # '%escaped\n'
        # are not captured and are ignored.
        if len(string) > 1:
            return

        self.error_tokens.append(string)
        self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
        return

    def _collecting_movetext(self, match):
        mg = match.group
        if mg(IFG_PIECE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_MOVE), "", "", mg(IFG_PIECE_SQUARE), ""
            )
            return
        if mg(IFG_PAWN_SQUARE):
            self.tokens.append(match)
            self._play_move("", "", "", mg(IFG_PAWN_SQUARE), "")
            return
        if mg(IFG_PIECE_CAPTURE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CAPTURE) or mg(IFG_KING_CAPTURE),
                mg(IFG_PIECE_CAPTURE_FROM),
                mg(IFG_PIECE_TAKES),
                mg(IFG_PIECE_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PAWN_CAPTURE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_CAPTURE_FROM_FILE),
                mg(IFG_PAWN_TAKES),
                mg(IFG_PAWN_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PIECE_CHOICE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CHOICE),
                mg(IFG_PIECE_CHOICE_FILE_OR_RANK),
                "",
                mg(IFG_PIECE_CHOICE_SQUARE),
                "",
            )
            return
        if mg(IFG_CASTLES):
            self.tokens.append(match)
            self._play_castles(mg(IFG_CASTLES))
            return
        if mg(IFG_PAWN_PROMOTE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_PROMOTE_FROM_FILE),
                mg(IFG_PAWN_TAKES_PROMOTE),
                mg(IFG_PAWN_PROMOTE_SQUARE),
                mg(IFG_PAWN_PROMOTE_PIECE)[1],
            )
            return
        if mg(IFG_START_RAV):
            self._start_variation()
            self.collect_token(match)
            return
        if mg(IFG_END_RAV):
            if len(self.ravstack) > 1:
                self._end_variation()
                self.collect_token(match)
            else:
                self.error_tokens.append(mg())
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if mg(IFG_TERMINATION):
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            return
        if mg(IFG_COMMENT):
            self.collect_token(match)
            return
        if mg(IFG_NAG):
            self.collect_token(match)
            return
        if mg(IFG_COMMENT_TO_EOL):
            self.collect_token(match)
            return

        # Other groups are not put on self.tokens because they are not shown in
        # game displays and do not need to the associated with a position on
        # the board.

        # The non-captured groups which are accepted without action.
        string = mg()

        if not string.strip():
            return
        if string.isdigit():
            return
        if string == FULLSTOP:
            return

        # Current movetext finishes in error, no termination, assume start of
        # new game.
        if mg(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if mg(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(mg(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # Only other groups with length > 1:
        # '<reserved>'
        # '%escaped\n'
        # are not captured and are ignored.
        if len(string) > 1:
            return

        # The non-captured groups which cause an error condition.
        self.error_tokens.append(string)
        self._ravstack_length = len(self.ravstack)
        if self._ravstack_length > 1:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_RAV
        else:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME

    def _collecting_non_whitespace_while_searching(self, match):
        if match.group(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if match.group(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(match.group(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if not match.group().split():
            self.error_tokens.append(match.group())
            return
        self.error_tokens.append(match.group())

    def _disambiguate_move(self, match):
        mg = match.group
        if mg(IFG_PAWN_SQUARE):
            start = self.tokens.pop()
            match = re_disambiguate_error.match(start.group() + mg())
            if match is None:
                match = re_disambiguate_non_move.match(start.group() + mg())
                self.tokens.append(match)
                self._illegal_play_disambiguated_move()
                return
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_disambiguated_move(
                start.group(IFG_PIECE_MOVE),
                start.group(IFG_PIECE_SQUARE),
                mg(IFG_PAWN_SQUARE),
            )
            return
        self.error_tokens.append(self.tokens.pop().group() + mg())
        self._ravstack_length = len(self.ravstack)
        if self._ravstack_length > 1:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_RAV
        else:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME

    def _illegal_play_move(self):
        self._state = self._move_error_state
        et = self.tokens.pop()
        self.error_tokens.append(et.group())

    def _illegal_play_castles(self):
        self._illegal_play_move()

    def _illegal_play_disambiguated_move(self):
        self._illegal_play_move()

    def _convert_error_tokens_to_token(self):
        self.collect_token(
            re_tokens.match(
                "".join(
                    (
                        ERROR_START_COMMENT,
                        "".join(self.error_tokens).replace(
                            END_COMMENT, ESCAPE_END_COMMENT
                        ),
                        END_COMMENT,
                    )
                )
            )
        )
        # Should this method clear self.error_tokens too?

    def _termination_while_searching(self, match):
        self.error_tokens.append(match.group())
        self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING

    def __eq__(self, other):
        if len(self.collected_game[2]) != len(other.collected_game[2]):
            return False
        if self.collected_game[3] or other.collected_game[3]:
            return False
        for ta, tb in zip(self.collected_game[2], other.collected_game[2]):
            if ta.group() != tb.group():
                return False
        return True

    def __ne__(self, other):
        return not self == other


def get_fen_string(description):
    (
        board,
        side_to_move,
        castle_options,
        ep_square,
        halfmoves,
        fullmoves,
    ) = description
    fenboard = []
    fenrank = []
    gap_length = 0
    for e, r in enumerate(board):
        if not e % BOARDSIDE:
            if gap_length:
                fenrank.append(str(gap_length))
                gap_length = 0
            if len(fenrank):
                fenboard.append("".join(fenrank))
                fenrank = []
        if r == NOPIECE:
            gap_length += 1
            continue
        if gap_length:
            fenrank.append(str(gap_length))
            gap_length = 0
        fenrank.append(r)
    if gap_length:
        fenrank.append(str(gap_length))
    fenboard.append("".join(fenrank))
    return " ".join(
        (
            "/".join(fenboard),
            FEN_TOMOVE[side_to_move],
            castle_options,
            ep_square,
            str(halfmoves),
            str(fullmoves),
        )
    )


# Subclass PGN131 to collect inconsistent FENs.
class PGN131Fen(PGN131):
    def __init__(self):
        super().__init__()
        self.position_fens = []
        self.position_strings = []
        self.board_fens = []

    def add_move_to_game(self):
        super().add_move_to_game()
        board = self.board
        castling = self.castling
        if (
            (board[0] != BROOK and BQUEEN in castling)
            or (board[7] != BROOK and BKING in castling)
            or (board[56] != WROOK and WQUEEN in castling)
            or (board[63] != WROOK and WKING in castling)
        ):
            self.position_fens.append(
                get_fen_string(
                    (
                        board,
                        self.active_side,
                        castling,
                        self.en_passant,
                        self.halfmove_count,
                        self.fullmove_number,
                    )
                )
            )
            self.position_strings.append(
                get_position_string(
                    (
                        board,
                        self.active_side,
                        castling,
                        self.en_passant,
                        self.halfmove_count,
                        self.fullmove_number,
                    )
                )
            )
            corrected_castling = castling
            if board[0] != BROOK:
                corrected_castling = corrected_castling.replace(BQUEEN, "")
            if board[7] != BROOK:
                corrected_castling = corrected_castling.replace(BKING, "")
            if board[56] != WROOK:
                corrected_castling = corrected_castling.replace(WQUEEN, "")
            if board[63] != WROOK:
                corrected_castling = corrected_castling.replace(WKING, "")
            self.board_fens.append(
                (
                    tuple(board),
                    self.active_side,
                    corrected_castling,
                    self.en_passant,
                    self.halfmove_count,
                    self.fullmove_number,
                )
            )


class PGNUpdate131(PGN131):
    def __init__(self):
        super().__init__()
        self.positions = []
        self.piecesquaremoves = []
        self.piecemoves = []
        self.squaremoves = []
        self.movenumber = None
        self.variationnumber = None
        self.currentvariation = None
        self._variation = None

    def set_position_fen(self, fen=None):
        super().set_position_fen(fen=fen)
        if self._initial_fen:
            self.positions = []
            self.piecesquaremoves = []

            # It is assumed better to have these indicies, missing square and
            # piece components, than to process the piecesquaremoves index to
            # deduce them when required.
            self.piecemoves = []
            self.squaremoves = []

            if self.active_side == WHITE_SIDE:
                self.movenumber = [(self.fullmove_number - 1) * 2]
            else:
                self.movenumber = [self.fullmove_number * 2 - 1]
            self.variationnumber = [0]
            self._variation = "".join(
                _convert_integer_to_length_hex(i) for i in self.variationnumber
            )

    def add_move_to_game(self):
        super().add_move_to_game()

        # Move numbers must be n, n+1, n+2, ... with repeats for Recursive
        # Annotation Variations for a move.
        # Variation numbers must be unique for each Recursive Annotation
        # Variation, where all moves at the same level within a '()' get the
        # same unique number.
        if len(self.ravstack) != len(self.movenumber):
            while len(self.ravstack) < len(self.movenumber):
                self.movenumber.pop()
                self.variationnumber.pop()
            while len(self.ravstack) > len(self.movenumber):
                self.movenumber.append(self.movenumber[-1])
            self._variation = "".join(
                _convert_integer_to_length_hex(i) for i in self.variationnumber
            )
        self.movenumber[-1] += 1

        movenumber = _convert_integer_to_length_hex(self.movenumber[-1])
        board = self.board
        piecesquaremoves = self.piecesquaremoves
        piecemoves = self.piecemoves
        squaremoves = self.squaremoves
        mfotpsn = MAP_FEN_ORDER_TO_PGN_SQUARE_NAME
        mp = MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE
        pieces = []
        mv = movenumber + self._variation
        for square, piece in enumerate(board):
            if piece:
                pieces.append(piece)
                # piecesquaremoves.append(mv + piece + mfotpsn[square])
                # squaremoves.append(mv + mp[piece] + mfotpsn[square])

                # If 'square piece' is better order than 'piece square'
                piecesquaremoves.append(mv + mfotpsn[square] + piece)
                squaremoves.append(mv + mfotpsn[square] + mp[piece])

        for piece in set(pieces):
            piecemoves.append(mv + piece)
        self.positions.append(
            "".join(
                (
                    self.board_bitmap.to_bytes(8, "big").decode("iso-8859-1"),
                    "".join(pieces),
                    FEN_TOMOVE[self.active_side],
                    self.en_passant,
                    self.castling,
                )
            )
        )

    def collect_game_tokens(self):
        self.collected_game = (
            self.tags_in_order,
            {
                m.group(IFG_TAG_SYMBOL): m.group(IFG_TAG_STRING_VALUE)
                for m in self.tags_in_order
            },
            self.tokens,
            self.error_tokens,
            self.positions,
            self.piecesquaremoves,
            self.piecemoves,
            self.squaremoves,
        )

    def _start_variation(self):
        super()._start_variation()
        if len(self.ravstack) > len(self.variationnumber):
            self.variationnumber.append(0)

    def _end_variation(self):
        super()._end_variation()
        self.variationnumber[len(self.ravstack)] += 1
        self._variation = "".join(
            _convert_integer_to_length_hex(i) for i in self.variationnumber
        )


def get_position_string(description):
    board, side_to_move, castle_options, ep_square = description[:4]
    return (
        sum(SQUARE_BITS[e] for e, p in enumerate(board) if p)
        .to_bytes(8, "big")
        .decode("iso-8859-1")
        + "".join(p for p in board)
        + FEN_TOMOVE[side_to_move]
        + ep_square
        + castle_options
    )


def _convert_integer_to_length_hex(i):
    try:
        return MOVE_NUMBER_KEYS[i]
    except IndexError:
        c = hex(i)
        return str(len(c) - 2) + c[2:]


class PGNError132(Exception):
    pass


class PGN132(object):
    def __init__(self):
        super().__init__()

        # data generated from PGN text for game while checking moves are legal
        self.tokens = []
        self.error_tokens = []
        self.tags_in_order = []

        # data generated from PGN text for game after checking moves are legal
        self.collected_game = None
        self.board_bitmap = None
        self.occupied_squares = []
        self.board = []
        self.piece_locations = {}
        self.fullmove_number = None
        self.halfmove_count = None
        self.en_passant = None
        self.castling = None
        self.active_side = None

        # ravstack keeps track of the position at start of game or variation
        # and the position after application of a valid move.  Thus the value
        # in ravstack[-1] is (None, <position start>) at start of game or line
        # and (<position start>, <position after move>) after application of a
        # valid move from gametokens.
        self.ravstack = []

        # data used while parsing PGN text to split into tag and move tokens
        self._initial_fen = None
        self._state = None
        self._move_error_state = None
        self._rewind_state = None

        self._despatch_table = [
            self._searching,
            self._searching_after_error_in_rav,
            self._searching_after_error_in_game,
            self._collecting_tag_pairs,
            self._collecting_movetext,
            self._collecting_non_whitespace_while_searching,
            self._disambiguate_move,
        ]

    @staticmethod
    def _read_pgn(string, length):
        pgntext = string.read(length)
        while len(pgntext):
            yield pgntext
            pgntext = string.read(length)
        yield pgntext

    def read_games(self, source, size=10000000, housekeepinghook=lambda: None):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        for pgntext in self._read_pgn(source, size):
            if len(self.error_tokens):
                self._state = self._rewind_state
                pgntext = "".join(self.error_tokens) + pgntext
                self.error_tokens.clear()
            for t in re_tokens.finditer(pgntext):
                self._despatch_table[self._state](t)
                if t.group(IFG_TERMINATION):
                    yield t
            housekeepinghook()

    def read_pgn_tokens(
        self, source, size=10000000, housekeepinghook=lambda: None
    ):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        for pgntext in self._read_pgn(source, size):
            if len(self.error_tokens):
                self._state = self._rewind_state
                pgntext = "".join(self.error_tokens) + pgntext
                self.error_tokens.clear()
            for t in re_tokens.finditer(pgntext):
                self._despatch_table[self._state](t)
                yield t.group(IFG_TERMINATION)

    def get_games(self, source):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        for t in re_tokens.finditer(source):
            self._despatch_table[self._state](t)
            if t.group(IFG_TERMINATION):
                yield t

    def get_first_pgn_token(self, source):
        self._state = PGN_SEARCHING
        self._move_error_state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        try:
            t = next(re_tokens.finditer(source))
            self._despatch_table[self._state](t)
            return False if t.group(IFG_TERMINATION) else True
        except StopIteration:
            return

    def read_first_game(
        self, source, size=10000000, housekeepinghook=lambda: None
    ):
        return next(
            self.read_games(
                source, size=size, housekeepinghook=housekeepinghook
            )
        )

    def get_first_game(self, source):
        return next(self.get_games(source))

    def is_movetext_valid(self):
        return not self.collected_game[3]

    def is_pgn_valid(self):
        return self.is_movetext_valid() and self.is_tag_roster_valid()

    def is_tag_roster_valid(self):
        tags_in_order = self.collected_game[0]
        tags = self.collected_game[1]
        if len(tags) != len(tags_in_order):
            # Tag must appear no more than once
            return False
        for v in tags.values():
            if len(v) == 0:
                # Tag value must not be null
                return False
        for t in SEVEN_TAG_ROSTER:
            if t not in tags:
                # A mandatory tag is missing
                return False
        return True

    def set_position_fen(self, fen=None):
        # fen is standard start position by default
        if fen is None:
            self.board_bitmap = INITIAL_BOARD_BITMAP
            self.board = list(INITIAL_BOARD)
            self.occupied_squares[:] = [
                set(s) for s in INITIAL_OCCUPIED_SQUARES
            ]
            self.piece_locations = {
                k: set(v) for k, v in INITIAL_PIECE_LOCATIONS.items()
            }
            self.ravstack[:] = [
                (
                    None,
                    (
                        INITIAL_BOARD,
                        WHITE_SIDE,
                        FEN_INITIAL_CASTLING,
                        FEN_NULL,
                        FEN_INITIAL_HALFMOVE_COUNT,
                        FEN_INITIAL_FULLMOVE_NUMBER,
                    ),
                )
            ]
            self.active_side = WHITE_SIDE
            self.castling = FEN_INITIAL_CASTLING
            self.en_passant = FEN_NULL
            self.halfmove_count = FEN_INITIAL_HALFMOVE_COUNT
            self.fullmove_number = FEN_INITIAL_FULLMOVE_NUMBER
            self._initial_fen = True
            return

        # fen specifies an arbitrary position.

        # fen has six space delimited fields.
        fs = fen.split(FEN_FIELD_DELIM)
        if len(fs) != FEN_FIELD_COUNT:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        (
            piece_placement,
            active_side,
            castling,
            en_passant,
            halfmove_count,
            fullmove_number,
        ) = fs
        del fs

        # fen side to move field.
        if active_side not in FEN_SIDES:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen castling field.
        if castling != FEN_NULL:
            for c in FEN_INITIAL_CASTLING:
                if castling.count(c) > FEN_CASTLING_OPTION_REPEAT_MAX:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
            for c in castling:
                if c not in FEN_INITIAL_CASTLING:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return

        # fen square to which a pawn can move when capturing en passant.
        if active_side == FEN_WHITE:
            if en_passant not in FEN_WHITE_MOVE_TO_EN_PASSANT:
                if en_passant != FEN_NULL:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
        elif active_side == FEN_BLACK:
            if en_passant not in FEN_BLACK_MOVE_TO_EN_PASSANT:
                if en_passant != FEN_NULL:
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return

        # Earlier 'fen side to move field' test makes this unreachable.
        else:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen halfmove count since pawn move or capture.
        if not halfmove_count.isdigit():
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen fullmove number.
        if not fullmove_number.isdigit():
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen piece placement field has eight ranks delimited by '/'.
        ranks = piece_placement.split(FEN_RANK_DELIM)
        if len(ranks) != BOARDSIDE:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # fen piece placement field has pieces and empty squares only.
        for r in ranks:
            for c in r:
                if c not in PIECES:
                    if not c.isdigit():
                        self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                        return

        # Exactly 64 squares: equivalent to exactly 8 squares per rank.
        for r in ranks:
            if sum([1 if not s.isdigit() else int(s) for s in r]) != BOARDSIDE:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # No pawns on first or eighth ranks.
        if (
            ranks[0].count(WPAWN)
            + ranks[0].count(BPAWN)
            + ranks[BOARDSIDE - 1].count(WPAWN)
            + ranks[BOARDSIDE - 1].count(BPAWN)
        ):
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # No more than 16 pieces per side.
        for s in WPIECES, BPIECES:
            for p in s:
                if (
                    sum([piece_placement.count(p) for p in s])
                    > FEN_PIECE_COUNT_PER_SIDE_MAX
                ):
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return

        # Exactly one king per side.
        for p in WKING, BKING:
            if piece_placement.count(p) != FEN_KING_COUNT:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # No more than eight pawns per side.
        for p in WPAWN, BPAWN:
            if piece_placement.count(p) > FEN_PAWN_COUNT_MAX:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # Piece counts within initial position and pawn promotion bounds.
        if (
            piece_placement.count(WPAWN)
            - FEN_PAWN_COUNT_MAX
            + max(piece_placement.count(WQUEEN) - FEN_QUEEN_COUNT_INITIAL, 0)
            + max(piece_placement.count(WROOK) - FEN_ROOK_COUNT_INITIAL, 0)
            + max(piece_placement.count(WBISHOP) - FEN_BISHOP_COUNT_INITIAL, 0)
            + max(piece_placement.count(WKNIGHT) - FEN_KNIGHT_COUNT_INITIAL, 0)
        ) > 0:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if (
            piece_placement.count(BPAWN)
            - FEN_PAWN_COUNT_MAX
            + max(piece_placement.count(BQUEEN) - FEN_QUEEN_COUNT_INITIAL, 0)
            + max(piece_placement.count(BROOK) - FEN_ROOK_COUNT_INITIAL, 0)
            + max(piece_placement.count(BBISHOP) - FEN_BISHOP_COUNT_INITIAL, 0)
            + max(piece_placement.count(BKNIGHT) - FEN_KNIGHT_COUNT_INITIAL, 0)
        ) > 0:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # Position is legal apart from checks, actual and deduced, and deduced
        # move that sets up en passant capture possibility.
        board = []
        for r in ranks:
            for c in r:
                if c in PIECES:
                    board.append(c)
                else:
                    board.extend([NOPIECE] * int(c))

        # Castling availability must fit the board position.
        if board[CASTLING_W] != WKING:
            if WKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
            if WQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_B] != BKING:
            if BKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
            if BQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_WK] != WROOK:
            if WKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_WQ] != WROOK:
            if WQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_BK] != BROOK:
            if BKING in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return
        if board[CASTLING_BQ] != BROOK:
            if BQUEEN in castling:
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # the two squares behind the pawn that can be captured en passant
        # must be empty. FEN quotes en passant capture square if latest move
        # is a two square pawn move,there does not need to be a pawn able to
        # make the capture. The side with the move must not be in check
        # diagonally through the square containing a pawn that can be captured
        # en passant, treating that square as empty.
        if en_passant != FEN_NULL:
            if en_passant in FEN_WHITE_MOVE_TO_EN_PASSANT:
                s = FEN_WHITE_MOVE_TO_EN_PASSANT[en_passant]
                if (
                    board[s] != NOPIECE
                    or board[s - 8] != NOPIECE
                    or board[s + 8] != BPAWN
                ):
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
            elif en_passant in FEN_BLACK_MOVE_TO_EN_PASSANT:
                s = FEN_BLACK_MOVE_TO_EN_PASSANT[en_passant]
                if (
                    board[s] != NOPIECE
                    or board[s + 8] != NOPIECE
                    or board[s - 8] != WPAWN
                ):
                    self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                    return
            else:

                # Should not happen, caught earlier.
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # FEN is legal, except for restrictions on kings in check, so set
        # instance attributes to fit description of position.
        piece_locations = {k: set() for k in INITIAL_PIECE_LOCATIONS}
        active_side_squares = set()
        inactive_side_squares = set()
        board_bitmap = []
        if active_side == FEN_WHITE:
            active_side_pieces = WPIECES
        else:
            active_side_pieces = BPIECES
        for s, p in enumerate(board):
            if p in PIECES:
                piece_locations[p].add(s)
                board_bitmap.append(SQUARE_BITS[s])
                if p in active_side_pieces:
                    active_side_squares.add(s)
                else:
                    inactive_side_squares.add(s)
        for active_side_king_square in piece_locations[
            SIDE_KING[FEN_SIDES[active_side]]
        ]:
            pass  # set active_side_king_square without pop() and add().
        for inactive_side_king_square in piece_locations[
            SIDE_KING[OTHER_SIDE[FEN_SIDES[active_side]]]
        ]:
            pass  # set active_side_king_square without pop() and add().

        # Side without the move must not be in check.
        # Cannot use is_active_king_attacked method because attributes are
        # not set until the position is ok.
        gap = GAPS[inactive_side_king_square]
        board_bitmap = sum(board_bitmap)
        for s in active_side_squares:
            if (
                not board_bitmap & gap[s]
                and SQUARE_BITS[s]
                & PIECE_CAPTURE_MAP[board[s]][inactive_side_king_square]
            ):
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                return

        # Side with the move must not be in check from more than two squares.
        # Cannot use count_attacks_on_square_by_side method because attributes
        # are not set until the position is ok.
        gap = GAPS[active_side_king_square]
        if (
            len(
                [
                    s
                    for s in inactive_side_squares
                    if (
                        not board_bitmap & gap[s]
                        and SQUARE_BITS[s]
                        & PIECE_CAPTURE_MAP[board[s]][active_side_king_square]
                    )
                ]
            )
            > FEN_MAXIMUM_PIECES_GIVING_CHECK
        ):
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        self.board_bitmap = board_bitmap
        self.board = board
        if active_side == FEN_WHITE:
            self.occupied_squares[:] = (
                active_side_squares,
                inactive_side_squares,
            )
        else:
            self.occupied_squares[:] = (
                inactive_side_squares,
                active_side_squares,
            )
        self.piece_locations = piece_locations
        self.ravstack[:] = [
            (
                None,
                (
                    tuple(board),
                    FEN_SIDES[active_side],
                    castling,
                    en_passant,
                    int(halfmove_count),
                    int(fullmove_number),
                ),
            )
        ]
        self.active_side = FEN_SIDES[active_side]
        self.castling = castling
        self.en_passant = en_passant
        self.halfmove_count = int(halfmove_count)
        self.fullmove_number = int(fullmove_number)
        self._initial_fen = fen

    def _play_move(
        self, pgn_piece, pgn_from, pgn_capture, pgn_tosquare, pgn_promote
    ):
        tosquare = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[pgn_tosquare]
        piece = MAPPIECE[self.active_side][pgn_piece]
        g = GAPS[tosquare]
        b = self.board
        bb = self.board_bitmap
        if pgn_capture == CAPTURE_MOVE:
            pts = PIECE_CAPTURE_MAP[piece][tosquare]
        else:
            pts = PIECE_MOVE_MAP[piece][tosquare]
        from_squares = [
            s
            for s in self.piece_locations[piece]
            if (SQUARE_BITS[s] & pts and not bb & g[s])
        ]
        if len(from_squares) > 1:
            if pgn_from:
                fm = MAPFILE.get(pgn_from[0])
                if fm is not None:
                    fm = FILES[fm]
                    from_squares = [
                        s for s in from_squares if SQUARE_BITS[s] & fm
                    ]
                if len(from_squares) > 1:
                    fm = MAPROW.get(pgn_from[-1])
                    if fm is not None:
                        fm = RANKS[fm]
                        from_squares = [
                            s for s in from_squares if SQUARE_BITS[s] & fm
                        ]
            if len(from_squares) > 1:
                inactive_side_squares = self.occupied_squares[
                    OTHER_SIDE[self.active_side]
                ]
                for active_side_king_square in self.piece_locations[
                    SIDE_KING[self.active_side]
                ]:
                    pass  # set active_side_king_square without pop() and add().
                gk = GAPS[active_side_king_square]
                pinned_to_king = set()
                for si in inactive_side_squares:
                    if (
                        PIECE_CAPTURE_MAP[b[si]][active_side_king_square]
                        & SQUARE_BITS[si]
                    ):
                        for s in from_squares:
                            if gk[si] & SQUARE_BITS[s]:
                                if not (
                                    (
                                        bb ^ SQUARE_BITS[s]
                                        | SQUARE_BITS[tosquare]
                                    )
                                    & gk[si]
                                ):
                                    if si != tosquare:
                                        pinned_to_king.add(s)
                from_squares = [
                    s for s in from_squares if s not in pinned_to_king
                ]
        if pgn_capture == PLAIN_MOVE and b[tosquare] == piece:

            # If moving piece is on tosquare and the next token is a square
            # identity try tosquare as fromsquare and next token as tosquare
            # for the piece move.
            # Only applies to Q B N non-capture moves where the moving side
            # has more than 2 of the moving piece so it is possible there
            # are two pieces of the moving kind on the same rank and the
            # same file at the same time which can reach the tosquare.
            # Check that there are at least three pieces of one kind which
            # can move to the same square and note the possibilities for
            # evaluation in two subsequent states where the next tokens are
            # readily available for comparison.  The next two tokens must be
            # '' and a square identity and the square identity must be one
            # of the possibilities.
            if b.count(piece) > 2:
                if pgn_piece in PGN_FROM_SQUARE_DISAMBIGUATION:
                    self._state = PGN_DISAMBIGUATE_MOVE
                    self._rewind_state = self._state
                    return

            self._illegal_play_move()
            return

        # After the disambiguation test, plain move to square containing piece
        # which is moving, because queen moves like both rook and bishop.
        if len(from_squares) != 1:
            self._illegal_play_move()
            return

        piece_locations = self.piece_locations
        fromsquare = from_squares.pop()

        # pgn_from is null, a file name, a rank name, or a square name.  If not
        # null it must be part of, or equal, the square name of fromsquare.
        if pgn_from is not None:
            if pgn_from not in MAP_FEN_ORDER_TO_PGN_SQUARE_NAME[fromsquare]:
                self._illegal_play_move()
                return

        if pgn_capture == CAPTURE_MOVE:
            inactive_side_squares = self.occupied_squares[
                OTHER_SIDE[self.active_side]
            ]
            if tosquare not in inactive_side_squares:
                if pgn_piece != PGN_PAWN:
                    self._illegal_play_move()
                    return
                elif pgn_tosquare != self.en_passant:
                    self._illegal_play_move()
                    return

                # Remove pawn captured en passant.
                elif self.en_passant in FEN_WHITE_CAPTURE_EN_PASSANT:
                    eps = FEN_WHITE_CAPTURE_EN_PASSANT[self.en_passant]
                    b[eps] = NOPIECE
                    inactive_side_squares.remove(eps)
                    piece_locations[BPAWN].remove(eps)
                    self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[eps]
                elif self.en_passant in FEN_BLACK_CAPTURE_EN_PASSANT:
                    eps = FEN_BLACK_CAPTURE_EN_PASSANT[self.en_passant]
                    b[eps] = NOPIECE
                    inactive_side_squares.remove(eps)
                    piece_locations[WPAWN].remove(eps)
                    self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[eps]

                else:
                    self._illegal_play_move()
                    return

            else:
                inactive_side_squares.remove(tosquare)
                piece_locations[b[tosquare]].remove(tosquare)
            self.en_passant = FEN_NULL
            self.halfmove_count = 0
        elif SQUARE_BITS[tosquare] & bb:
            self._illegal_play_move()
            return
        elif pgn_piece == PGN_PAWN:

            # Moves like 'b1' for black, and 'b8' for white, are passed earlier
            # to cope with disambiguating queen moves like 'Qd1f1'.
            if not (
                SQUARE_BITS[tosquare]
                & PAWN_MOVE_DESITINATION[self.active_side]
            ):
                if not pgn_promote:
                    self._illegal_play_move()
                    return

            self.halfmove_count = 0
            if (
                SQUARE_BITS[fromsquare] & EN_PASSANT_FROM_SQUARES
                and SQUARE_BITS[tosquare] & EN_PASSANT_TO_SQUARES
            ):
                self.en_passant = (
                    pgn_tosquare[0]
                    + FEN_EN_PASSANT_TARGET_RANK[pgn_tosquare[1]]
                )
            else:
                self.en_passant = FEN_NULL
        else:
            self.en_passant = FEN_NULL
            self.halfmove_count = self.halfmove_count + 1
        active_side_squares = self.occupied_squares[self.active_side]

        # Remove moving piece from current square.
        b[fromsquare] = NOPIECE
        active_side_squares.remove(fromsquare)
        piece_locations[piece].remove(fromsquare)
        self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[fromsquare]

        # Put moving piece on new square.
        b[tosquare] = piece
        active_side_squares.add(tosquare)
        piece_locations[piece].add(tosquare)
        self.board_bitmap |= SQUARE_BITS[tosquare]

        # Replace moving pawn on promotion and update inactive king square.
        if pgn_promote:
            piece_locations[b[tosquare]].remove(tosquare)
            b[tosquare] = MAPPIECE[self.active_side][pgn_promote]
            piece_locations[b[tosquare]].add(tosquare)

        # Undo move if it leaves king in check.
        if self.is_active_king_attacked():
            self.reset_position(self.ravstack[-1][-1])
            self._illegal_play_move()
            return

        # Castling availabity.
        # tosquare tests deal with capture of rooks which have not moved.
        # For real games the top condition is false for more than half the game
        # and the next condition is usually false.
        if self.castling != FEN_NULL:
            if (
                SQUARE_BITS[fromsquare] | SQUARE_BITS[tosquare]
            ) & CASTLING_AVAILABITY_SQUARES:
                if fromsquare == CASTLING_W:
                    self.castling = self.castling.replace(WKING, NOPIECE)
                    self.castling = self.castling.replace(WQUEEN, NOPIECE)
                elif fromsquare == CASTLING_WK:
                    self.castling = self.castling.replace(WKING, NOPIECE)
                elif fromsquare == CASTLING_WQ:
                    self.castling = self.castling.replace(WQUEEN, NOPIECE)
                elif fromsquare == CASTLING_B:
                    self.castling = self.castling.replace(BKING, NOPIECE)
                    self.castling = self.castling.replace(BQUEEN, NOPIECE)
                elif fromsquare == CASTLING_BK:
                    self.castling = self.castling.replace(BKING, NOPIECE)
                elif fromsquare == CASTLING_BQ:
                    self.castling = self.castling.replace(BQUEEN, NOPIECE)
                if tosquare == CASTLING_WK:
                    self.castling = self.castling.replace(WKING, NOPIECE)
                elif tosquare == CASTLING_WQ:
                    self.castling = self.castling.replace(WQUEEN, NOPIECE)
                elif tosquare == CASTLING_BK:
                    self.castling = self.castling.replace(BKING, NOPIECE)
                elif tosquare == CASTLING_BQ:
                    self.castling = self.castling.replace(BQUEEN, NOPIECE)
                if self.castling == NOPIECE:
                    self.castling = FEN_NULL

        self.add_move_to_game()

    def _play_castles(self, token):

        # Verify castling availability and pick castling rules.
        if token.startswith(O_O_O):
            if self.active_side == WHITE_SIDE:
                if WQUEEN not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[WQUEEN]
            else:
                if BQUEEN not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[BQUEEN]
        elif token.startswith(O_O):
            if self.active_side == WHITE_SIDE:
                if WKING not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[WKING]
            else:
                if BKING not in self.castling:
                    self._illegal_play_castles()
                    return
                castling_squares = CASTLING_SQUARES[BKING]
        else:
            self._illegal_play_castles()
            return

        bb = self.board_bitmap
        board = self.board
        piece_locations = self.piece_locations
        active_side_squares = self.occupied_squares[self.active_side]
        active_side_king_locations = piece_locations[
            SIDE_KING[self.active_side]
        ]
        if self.active_side == WHITE_SIDE:
            active_side_rook_locations = piece_locations[WROOK]
        else:
            active_side_rook_locations = piece_locations[BROOK]
        for active_side_king_square in active_side_king_locations:
            pass  # set active_side_king_square without pop() and add().

        # Confirm board position is consistent with castling availability.
        if (
            active_side_king_square != castling_squares[0]
            or board[castling_squares[0]] != castling_squares[5]
            or board[castling_squares[1]] != castling_squares[4]
        ):
            self._illegal_play_castles()
            return

        # Squares between king and castling rook must be empty.
        for squares in castling_squares[2:4]:
            for s in squares:
                if SQUARE_BITS[s] & bb:
                    self._illegal_play_castles()
                    return

        # Castling king must not be in check.
        if self.is_square_attacked_by_side(
            castling_squares[0], OTHER_SIDE[self.active_side]
        ):
            self._illegal_play_castles()
            return

        # Castling king's destination square, and the one between, must not be
        # attacked by the other side.
        for square in castling_squares[2]:
            if self.is_square_attacked_by_side(
                square, OTHER_SIDE[self.active_side]
            ):
                self._illegal_play_castles()
                return

        king_square = castling_squares[0]
        new_king_square = castling_squares[2][1]
        rook_square = castling_squares[1]
        new_rook_square = castling_squares[2][0]

        # Put moving pieces on new squares.
        board[new_king_square] = board[king_square]
        board[new_rook_square] = board[rook_square]
        active_side_squares.add(new_king_square)
        active_side_king_locations.add(new_king_square)
        active_side_squares.add(new_rook_square)
        active_side_rook_locations.add(new_rook_square)
        self.board_bitmap |= (
            SQUARE_BITS[new_king_square] | SQUARE_BITS[new_rook_square]
        )

        # Remove moving pieces from current squares.
        board[king_square] = NOPIECE
        board[rook_square] = NOPIECE
        active_side_squares.remove(king_square)
        active_side_king_locations.remove(king_square)
        active_side_squares.remove(rook_square)
        active_side_rook_locations.remove(rook_square)
        self.board_bitmap &= self.board_bitmap ^ (
            SQUARE_BITS[king_square] | SQUARE_BITS[rook_square]
        )

        # Castling availabity.
        if self.active_side == WHITE_SIDE:
            self.castling = self.castling.replace(WKING, NOPIECE)
            self.castling = self.castling.replace(WQUEEN, NOPIECE)
        else:
            self.castling = self.castling.replace(BKING, NOPIECE)
            self.castling = self.castling.replace(BQUEEN, NOPIECE)
        if self.castling == NOPIECE:
            self.castling = FEN_NULL

        # Cannot be en-passant
        self.en_passant = FEN_NULL

        self.halfmove_count = self.halfmove_count + 1
        self.add_move_to_game()

    def is_active_king_attacked(self):
        b = self.board
        bb = self.board_bitmap

        # Only one element in this container.
        for ks in self.piece_locations[SIDE_KING[self.active_side]]:
            g = GAPS[ks]
            for s in self.occupied_squares[OTHER_SIDE[self.active_side]]:
                if (
                    not bb & g[s]
                    and SQUARE_BITS[s] & PIECE_CAPTURE_MAP[b[s]][ks]
                ):
                    return True
        return False

    def is_square_attacked_by_side(self, square, side):
        g = GAPS[square]
        b = self.board
        bb = self.board_bitmap
        for s in self.occupied_squares[side]:
            if (
                not bb & g[s]
                and SQUARE_BITS[s] & PIECE_CAPTURE_MAP[b[s]][square]
            ):
                return True
        return False

    def count_attacks_on_square_by_side(self, square, side):
        g = GAPS[square]
        b = self.board
        bb = self.board_bitmap
        return len(
            [
                s
                for s in self.occupied_squares[side]
                if (
                    not bb & g[s]
                    and SQUARE_BITS[s] & PIECE_CAPTURE_MAP[b[s]][square]
                )
            ]
        )

    def add_move_to_game(self):
        self.active_side = OTHER_SIDE[self.active_side]
        if self.active_side == WHITE_SIDE:
            self.fullmove_number += 1
        self.ravstack[-1] = (
            self.ravstack[-1][-1],
            (
                tuple(self.board),
                self.active_side,
                self.castling,
                self.en_passant,
                self.halfmove_count,
                self.fullmove_number,
            ),
        )

    def collect_token(self, match):
        self.tokens.append(match)

    def collect_game_tokens(self):
        self.collected_game = (
            self.tags_in_order,
            {
                m.group(IFG_TAG_SYMBOL): m.group(IFG_TAG_STRING_VALUE)
                for m in self.tags_in_order
            },
            self.tokens,
            self.error_tokens,
        )

    def _play_disambiguated_move(
        self, pgn_piece, pgn_fromsquare, pgn_tosquare
    ):
        fromsquare = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[pgn_fromsquare]
        tosquare = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[pgn_tosquare]
        piece = MAPPIECE[self.active_side][pgn_piece]
        if fromsquare not in self.piece_locations[piece]:
            self._illegal_play_disambiguated_move()
            return
        if not (
            SQUARE_BITS[fromsquare] & PIECE_MOVE_MAP[piece][tosquare]
            and not self.board_bitmap & GAPS[tosquare][fromsquare]
        ):
            self._illegal_play_disambiguated_move()
            return
        if SQUARE_BITS[tosquare] & self.board_bitmap:
            self._illegal_play_disambiguated_move()
            return
        else:
            self.halfmove_count = self.halfmove_count + 1
        b = self.board
        piece_locations = self.piece_locations
        active_side_squares = self.occupied_squares[self.active_side]

        # Remove moving piece from current square.
        b[fromsquare] = NOPIECE
        active_side_squares.remove(fromsquare)
        piece_locations[piece].remove(fromsquare)
        self.board_bitmap &= self.board_bitmap ^ SQUARE_BITS[fromsquare]

        # Put moving piece on new square.
        b[tosquare] = piece
        active_side_squares.add(tosquare)
        piece_locations[piece].add(tosquare)
        self.board_bitmap |= SQUARE_BITS[tosquare]

        # Undo move if it leaves king in check.
        if self.is_active_king_attacked():
            self.reset_position(self.ravstack[-1][-1])
            self._illegal_play_disambiguated_move()
            return

        # Castling availabity is not affected because rooks cannot be involved
        # in moves which need disambiguation.

        # Cannot be en-passant
        self.en_passant = FEN_NULL

        self.add_move_to_game()

    # Maybe should not be a method now, but retain shape of pre-FEN class code
    # for ease of comparison until sure everything works.
    # Just say self._fen = ... where method is called.
    def reset_position(self, position):
        (
            board,
            self.active_side,
            self.castling,
            self.en_passant,
            self.halfmove_count,
            self.fullmove_number,
        ) = position
        self.board[:] = list(board)
        occupied_squares = self.occupied_squares
        for side in occupied_squares:
            side.clear()
        piece_locations = self.piece_locations
        for piece in piece_locations.values():
            piece.clear()
        board_bitmap = 0
        for square, piece in enumerate(board):
            if piece in WPIECES:
                occupied_squares[0].add(square)
                piece_locations[piece].add(square)
                board_bitmap |= SQUARE_BITS[square]
            elif piece in BPIECES:
                occupied_squares[1].add(square)
                piece_locations[piece].add(square)
                board_bitmap |= SQUARE_BITS[square]
        self.board_bitmap = board_bitmap

    def _start_variation(self):
        self.ravstack.append((None, self.ravstack[-1][0]))
        self.reset_position(self.ravstack[-1][-1])

    def _end_variation(self):
        try:
            del self.ravstack[-1]
            try:
                self.reset_position(self.ravstack[-1][-1])
            except:
                pass
        except:
            pass

    def _searching(self, match):
        mg = match.group
        if mg(IFG_START_TAG):
            self.tags_in_order.append(match)
            if mg(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(mg(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if mg(IFG_PIECE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_MOVE), "", "", mg(IFG_PIECE_SQUARE), ""
            )
            return
        if mg(IFG_PAWN_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move("", "", "", mg(IFG_PAWN_SQUARE), "")
            return
        if mg(IFG_PIECE_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CAPTURE) or mg(IFG_KING_CAPTURE),
                mg(IFG_PIECE_CAPTURE_FROM),
                mg(IFG_PIECE_TAKES),
                mg(IFG_PIECE_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PAWN_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_CAPTURE_FROM_FILE),
                mg(IFG_PAWN_TAKES),
                mg(IFG_PAWN_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PIECE_CHOICE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CHOICE),
                mg(IFG_PIECE_CHOICE_FILE_OR_RANK),
                "",
                mg(IFG_PIECE_CHOICE_SQUARE),
                "",
            )
            return
        if mg(IFG_CASTLES):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_castles(mg(IFG_CASTLES))
            return
        if mg(IFG_PAWN_PROMOTE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_PROMOTE_FROM_FILE),
                mg(IFG_PAWN_TAKES_PROMOTE),
                mg(IFG_PAWN_PROMOTE_SQUARE),
                mg(IFG_PAWN_PROMOTE_PIECE)[1],
            )
            return
        if mg(IFG_COMMENT):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_NAG):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_COMMENT_TO_EOL):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return

        # The captured tokens not accepted when searching for start of game.
        if mg(IFG_START_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
            return
        if mg(IFG_END_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
            return
        if mg(IFG_TERMINATION):
            self._termination_while_searching(match)
            return

        # Action for non-captured groups is decided by looking at whole token.
        string = mg()

        if not string.strip():
            return
        if string.isdigit():
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return
        if string == FULLSTOP:
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return

        # Only other groups with length > 1:
        # '<reserved>'
        # '%escaped\n'
        # are not captured and are ignored.
        if len(string) > 1:
            return

        self.error_tokens.append(string)
        self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING
        return

    def _searching_after_error_in_rav(self, match):
        if match.group(IFG_START_RAV):
            self.error_tokens.append(match.group())
            self._ravstack_length += 1
            return
        if match.group(IFG_END_RAV):
            if self._ravstack_length == len(self.ravstack):
                self._convert_error_tokens_to_token()
                self.collect_token(match)
                self._end_variation()
                self.error_tokens = []
                self._state = PGN_COLLECTING_MOVETEXT
                self._rewind_state = self._state
                if self._ravstack_length > 2:
                    self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_RAV
                else:
                    self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
                del self._ravstack_length
            else:
                self.error_tokens.append(match.group())
                self._ravstack_length -= 1
            return
        if match.group(IFG_TERMINATION):
            self._convert_error_tokens_to_token()
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            del self._ravstack_length
            return
        if match.group(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if match.group(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(match.group(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            del self._ravstack_length
            return
        self.error_tokens.append(match.group())

    def _searching_after_error_in_game(self, match):
        if match.group(IFG_TERMINATION):
            self._convert_error_tokens_to_token()
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            return
        if match.group(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if match.group(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(match.group(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        self.error_tokens.append(match.group())

    def _collecting_tag_pairs(self, match):
        mg = match.group
        if mg(IFG_START_TAG):
            self.tags_in_order.append(match)
            if mg(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(mg(IFG_TAG_STRING_VALUE))
            return
        if mg(IFG_PIECE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_MOVE), "", "", mg(IFG_PIECE_SQUARE), ""
            )
            return
        if mg(IFG_PAWN_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move("", "", "", mg(IFG_PAWN_SQUARE), "")
            return
        if mg(IFG_PIECE_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CAPTURE) or mg(IFG_KING_CAPTURE),
                mg(IFG_PIECE_CAPTURE_FROM),
                mg(IFG_PIECE_TAKES),
                mg(IFG_PIECE_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PAWN_CAPTURE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_CAPTURE_FROM_FILE),
                mg(IFG_PAWN_TAKES),
                mg(IFG_PAWN_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PIECE_CHOICE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CHOICE),
                mg(IFG_PIECE_CHOICE_FILE_OR_RANK),
                "",
                mg(IFG_PIECE_CHOICE_SQUARE),
                "",
            )
            return
        if mg(IFG_CASTLES):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_castles(mg(IFG_CASTLES))
            return
        if mg(IFG_PAWN_PROMOTE_SQUARE):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_PROMOTE_FROM_FILE),
                mg(IFG_PAWN_TAKES_PROMOTE),
                mg(IFG_PAWN_PROMOTE_SQUARE),
                mg(IFG_PAWN_PROMOTE_PIECE)[1],
            )
            return
        if mg(IFG_TERMINATION):
            if not self._initial_fen:
                self.set_position_fen()
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            return
        if mg(IFG_COMMENT):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_NAG):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return
        if mg(IFG_COMMENT_TO_EOL):
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.collect_token(match)
            return

        # The captured tokens not accepted when searching for tag pairs.
        if mg(IFG_START_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if mg(IFG_END_RAV):
            self.error_tokens.append(mg())
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # Action for non-captured groups is decided by looking at whole token.
        string = mg()

        if not string.strip():
            return
        if string.isdigit():
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return
        if string == FULLSTOP:
            if not self._initial_fen:
                self.set_position_fen()
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            return

        # Only other groups with length > 1:
        # '<reserved>'
        # '%escaped\n'
        # are not captured and are ignored.
        if len(string) > 1:
            return

        self.error_tokens.append(string)
        self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
        return

    def _collecting_movetext(self, match):
        mg = match.group
        if mg(IFG_PIECE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_MOVE), "", "", mg(IFG_PIECE_SQUARE), ""
            )
            return
        if mg(IFG_PAWN_SQUARE):
            self.tokens.append(match)
            self._play_move("", "", "", mg(IFG_PAWN_SQUARE), "")
            return
        if mg(IFG_PIECE_CAPTURE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CAPTURE) or mg(IFG_KING_CAPTURE),
                mg(IFG_PIECE_CAPTURE_FROM),
                mg(IFG_PIECE_TAKES),
                mg(IFG_PIECE_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PAWN_CAPTURE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_CAPTURE_FROM_FILE),
                mg(IFG_PAWN_TAKES),
                mg(IFG_PAWN_CAPTURE_SQUARE),
                "",
            )
            return
        if mg(IFG_PIECE_CHOICE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                mg(IFG_PIECE_CHOICE),
                mg(IFG_PIECE_CHOICE_FILE_OR_RANK),
                "",
                mg(IFG_PIECE_CHOICE_SQUARE),
                "",
            )
            return
        if mg(IFG_CASTLES):
            self.tokens.append(match)
            self._play_castles(mg(IFG_CASTLES))
            return
        if mg(IFG_PAWN_PROMOTE_SQUARE):
            self.tokens.append(match)
            self._play_move(
                "",
                mg(IFG_PAWN_PROMOTE_FROM_FILE),
                mg(IFG_PAWN_TAKES_PROMOTE),
                mg(IFG_PAWN_PROMOTE_SQUARE),
                mg(IFG_PAWN_PROMOTE_PIECE)[1],
            )
            return
        if mg(IFG_START_RAV):
            self._start_variation()
            self.collect_token(match)
            return
        if mg(IFG_END_RAV):
            if len(self.ravstack) > 1:
                self._end_variation()
                self.collect_token(match)
            else:
                self.error_tokens.append(mg())
                self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if mg(IFG_TERMINATION):
            self.collect_token(match)
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = []
            self._state = PGN_SEARCHING
            self._rewind_state = self._state
            return
        if mg(IFG_COMMENT):
            self.collect_token(match)
            return
        if mg(IFG_NAG):
            self.collect_token(match)
            return
        if mg(IFG_COMMENT_TO_EOL):
            self.collect_token(match)
            return

        # Other groups are not put on self.tokens because they are not shown in
        # game displays and do not need to the associated with a position on
        # the board.

        # The non-captured groups which are accepted without action.
        string = mg()

        if not string.strip():
            return
        if string.isdigit():
            return
        if string == FULLSTOP:
            return

        # Current movetext finishes in error, no termination, assume start of
        # new game.
        if mg(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if mg(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(mg(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return

        # Only other groups with length > 1:
        # '<reserved>'
        # '%escaped\n'
        # are not captured and are ignored.
        if len(string) > 1:
            return

        # The non-captured groups which cause an error condition.
        self.error_tokens.append(string)
        self._ravstack_length = len(self.ravstack)
        if self._ravstack_length > 1:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_RAV
        else:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME

    def _collecting_non_whitespace_while_searching(self, match):
        if match.group(IFG_START_TAG):
            self._convert_error_tokens_to_token()
            self.collect_game_tokens()
            self._initial_fen = False
            self.tokens = []
            self.error_tokens = []
            self.tags_in_order = [match]
            if match.group(IFG_TAG_SYMBOL) == TAG_FEN:
                self.set_position_fen(match.group(IFG_TAG_STRING_VALUE))
            self._state = PGN_COLLECTING_TAG_PAIRS
            self._rewind_state = self._state
            self._move_error_state = PGN_SEARCHING_AFTER_ERROR_IN_GAME
            return
        if not match.group().split():
            self.error_tokens.append(match.group())
            return
        self.error_tokens.append(match.group())

    def _disambiguate_move(self, match):
        mg = match.group
        if mg(IFG_PAWN_SQUARE):
            start = self.tokens.pop()
            match = re_disambiguate_error.match(start.group() + mg())
            if match is None:
                match = re_disambiguate_non_move.match(start.group() + mg())
                self.tokens.append(match)
                self._illegal_play_disambiguated_move()
                return
            self._state = PGN_COLLECTING_MOVETEXT
            self._rewind_state = self._state
            self.tokens.append(match)
            self._play_disambiguated_move(
                start.group(IFG_PIECE_MOVE),
                start.group(IFG_PIECE_SQUARE),
                mg(IFG_PAWN_SQUARE),
            )
            return
        self.error_tokens.append(self.tokens.pop().group() + mg())
        self._ravstack_length = len(self.ravstack)
        if self._ravstack_length > 1:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_RAV
        else:
            self._state = PGN_SEARCHING_AFTER_ERROR_IN_GAME

    def _illegal_play_move(self):
        self._state = self._move_error_state
        et = self.tokens.pop()
        self.error_tokens.append(et.group())

    def _illegal_play_castles(self):
        self._illegal_play_move()

    def _illegal_play_disambiguated_move(self):
        self._illegal_play_move()

    def _convert_error_tokens_to_token(self):
        """Generate error token '{Error: <original tokens> }'.

        Any '}' in <original tokens> replaced by '::{{::'.  Assume '::{{::' and
        '{Error: ' do not occur naturally in '{}' comments.
        """
        self.collect_token(
            re_tokens.match(
                "".join(
                    (
                        ERROR_START_COMMENT,
                        "".join(self.error_tokens).replace(
                            END_COMMENT, ESCAPE_END_COMMENT
                        ),
                        END_COMMENT,
                    )
                )
            )
        )
        # Should this method clear self.error_tokens too?

    def _termination_while_searching(self, match):
        self.error_tokens.append(match.group())
        self._state = PGN_COLLECTING_NON_WHITESPACE_WHILE_SEARCHING

    def __eq__(self, other):
        if len(self.collected_game[2]) != len(other.collected_game[2]):
            return False
        if self.collected_game[3] or other.collected_game[3]:
            return False
        for ta, tb in zip(self.collected_game[2], other.collected_game[2]):
            if ta.group() != tb.group():
                return False
        return True

    def __ne__(self, other):
        return not self == other


# Subclass PGN132 to collect inconsistent FENs: meaning verify they do not
# exist for PGN copied from pgn_read.core.parser version 1.3.2.
class PGNFen(PGN132):
    def __init__(self):
        super().__init__()
        self.position_fens = []
        self.board_fens = []

    def add_move_to_game(self):
        super().add_move_to_game()
        board = self.board
        castling = self.castling
        if (
            (board[0] != BROOK and BQUEEN in castling)
            or (board[7] != BROOK and BKING in castling)
            or (board[56] != WROOK and WQUEEN in castling)
            or (board[63] != WROOK and WKING in castling)
        ):
            self.position_fens.append(
                get_fen_string(
                    (
                        board,
                        self.active_side,
                        castling,
                        self.en_passant,
                        self.halfmove_count,
                        self.fullmove_number,
                    )
                )
            )


# Versions of the classes in core.chessrecord which use PGNUpdate modified to
# use PGNUpdate131, defined in this module above, so the records which have the
# inconsistent castling options can be deleted in full.
class ChessDBkeyGame131(KeyData):
    def __eq__(self, other):
        try:
            return self.recno == other.recno
        except:
            return False

    def __ne__(self, other):
        try:
            return self.recno != other.recno
        except:
            return True


class ChessDBvaluePGN131(Value):
    @staticmethod
    def encode_move_number(key):
        return key.to_bytes(2, byteorder="big")

    def load(self, value):
        self.get_first_game(literal_eval(value))

    def pack_value(self):
        return repr(
            "".join(
                (
                    "".join(
                        [
                            "".join(
                                (
                                    "[",
                                    t.group(IFG_TAG_SYMBOL),
                                    '"',
                                    t.group(IFG_TAG_STRING_VALUE),
                                    '"]',
                                )
                            )
                            for t in self.collected_game[0]
                        ]
                    ),
                    "".join([t.group() for t in self.collected_game[2]]),
                    "".join([t for t in self.collected_game[3]]),
                )
            )
        )


class ChessDBvaluePGNUpdate131(PGNUpdate131, ChessDBvaluePGN131):

    # Replaces ChessDBvaluePGNUpdate and ChessDBvalueGameImport which had been
    # identical for a considerable time.
    # Decided that PGNUpdate should remain in pgn.core.parser because that code
    # generates data while this code updates a database.
    # ChessDBvalueGameImport had this comment:
    # Implication of original is encode_move_number not supported and load in
    # ChessDBvaluePGN superclass is used.

    def __init__(self):
        super().__init__()
        self.gamesource = None

    def pack(self):
        v = super().pack()
        index = v[1]
        cg = self.collected_game
        if self.do_full_indexing():
            tags = cg[1]
            for field in SEVEN_TAG_ROSTER:
                if field in PLAYER_NAME_TAGS:

                    # PGN specification states colon is used to separate player
                    # names in consultation games.
                    index[field] = [
                        " ".join(re_normalize_player_name.findall(tf))
                        for tf in tags[field].split(":")
                    ]

                else:
                    index[field] = [tags[field]]
            index[POSITIONS_FIELD_DEF] = cg[4]
            index[PIECESQUAREMOVE_FIELD_DEF] = cg[5]
            index[PIECEMOVE_FIELD_DEF] = cg[6]
            index[SQUAREMOVE_FIELD_DEF] = cg[7]
            index[PGN_DATE_FIELD_DEF] = [
                tags[TAG_DATE].replace(*SPECIAL_TAG_DATE)
            ]
        else:
            index[SOURCE_FIELD_DEF] = [self.gamesource]
        return v

    def set_game_source(self, source):
        self.gamesource = source

    def do_full_indexing(self):
        return self.gamesource is None

    def is_error_comment_present(self):
        return ERROR_START_COMMENT in self.collected_game[2][0].string


class ChessDBrecordGameUpdate131(Record):
    def __init__(self):
        super(ChessDBrecordGameUpdate131, self).__init__(
            ChessDBkeyGame131, ChessDBvaluePGNUpdate131
        )

    def clone(self):

        # are conditions for deleting this method in place?
        clone = super(ChessDBrecordGameUpdate131, self).clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        return int.from_bytes(skey, byteorder="big")

    def get_keys(self, datasource=None, partial=None):
        dbname = datasource.dbname
        if dbname != POSITIONS_FIELD_DEF:
            if dbname == GAMES_FILE_DEF:
                return [(self.key.recno, self.srvalue)]
            elif dbname in self.value.collected_game[1]:
                return [
                    (self.value.collected_game[1][dbname], self.key.pack())
                ]
            else:
                return []
        if partial == None:
            return []

        moves = self.value.moves
        gamekey = datasource.dbhome.encode_record_number(self.key.pack())
        rav = 0
        ref = 0
        keys = []
        convert_format = datasource.dbhome.db_compatibility_hack

        p = tuple(partial)
        for mt in moves:
            if mt == START_RAV:
                rav += 1
            elif mt == END_RAV:
                rav -= 1
            elif mt == NON_MOVE:
                pass
            else:
                if mt[-1] == p:
                    record = (partial, None)
                    keys.append(convert_format(record, gamekey))
            ref += 1
        return keys

    def load_instance(self, database, dbset, dbname, record):
        super(ChessDBrecordGameUpdate131, self).load_instance(
            database, dbset, dbname, record
        )

        # Never called because attribute is not bound anywhere and no
        # exceptions are seen ever.
        # if self.value.callbacktried:
        #    pass
        # elif self.value.callbacktried == None:
        #    pass
        # elif not self.value.callbacktried:
        #    self.value.set_game_source(record[0])


class Main:
    def __init__(self):
        root = tkinter.Tk()
        root.wm_title(string="Castling Option Corrections")
        root.wm_resizable(width=tkinter.FALSE, height=tkinter.TRUE)
        tkinter.ttk.Label(
            master=root, text="ChessTab Database Directory"
        ).grid(row=0, column=0)
        tkinter.ttk.Label(master=root, text="Log").grid(
            row=1, column=1, pady=5
        )
        tkinter.ttk.Label(master=root, text="Right-click for menu").grid(
            row=1, column=3, pady=5, sticky="e"
        )
        progress = tkinter.ttk.Label(master=root)
        progress.grid(row=1, column=2, pady=5)
        counter = tkinter.StringVar(root, "")
        progress["textvariable"] = counter
        entry = tkinter.ttk.Entry(master=root)
        entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=5)
        chesstab_directory = tkinter.StringVar(root, "")
        entry["textvariable"] = chesstab_directory
        frame = tkinter.ttk.Frame(master=root)
        frame.grid(row=2, column=0, columnspan=5, sticky="nsew")
        root.rowconfigure(2, weight=1)
        text = tkinter.Text(master=frame, wrap=tkinter.WORD)
        scrollbar = tkinter.ttk.Scrollbar(
            master=frame, orient=tkinter.VERTICAL, command=text.yview
        )
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        text.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.menu = tkinter.Menu(master=frame, tearoff=False)
        self.__menu = self.menu
        self.root = root
        self.text = text
        self.entry = entry
        self.chesstab_directory = chesstab_directory
        self.counter = counter
        self.set_menu_and_entry_events(True)
        entry.bind("<ButtonPress-3>", self.show_menu)
        text.bind("<ButtonPress-3>", self.show_menu)
        entry.focus_set()
        self._database_class = None
        self._fullposition_class = None
        self._engineanalysis_class = None
        self.opendatabase = None
        self._database_enginename = None
        self._database_modulename = None

    def insert_text(self, text):
        self.text.insert(tkinter.END, text)

    def report_action(self, msg):
        self.insert_text("\n")
        self.insert_text(" ".join(msg))
        self.text.see(tkinter.END)
        tkinter.messagebox.showinfo(master=self.root, message="\n".join(msg))

    def report_error(self, msg):
        self.insert_text("\n")
        self.insert_text(" ".join(msg))
        self.text.see(tkinter.END)
        tkinter.messagebox.showerror(master=self.root, message="\n".join(msg))

    def show_menu(self, event=None):
        self.__menu.tk_popup(*event.widget.winfo_pointerxy())
        self.__xy = event.x, event.y
        self.__menu = self.menu

    def select_chesstab_database(self, event=None):
        directoryname = tkinter.filedialog.askdirectory(
            title="Select ChessTab Database", initialdir="~"
        )
        if directoryname:
            self.chesstab_directory.set(directoryname)

    def save_log_as(self, event=None):
        openfile = tkinter.filedialog.asksaveasfile(
            title="Save Log As ...",
            defaultextension=".txt",
            filetypes=(("Log file", "*.txt"),),
        )
        if openfile:
            try:
                openfile.write(self.text.get("1.0", tkinter.END))
            finally:
                openfile.close()

    def report_games_with_inconsistent_castling_options(self, event=None):
        if self.chesstab_directory.get() == "":
            tkinter.messagebox.showerror(
                master=self.root,
                message="Please select a ChessTab Database Directory.",
            )
            return
        path = self.chesstab_directory.get()
        if not os.path.exists(path):
            msg = (
                "Cannot process\n",
                self.chesstab_directory.get(),
                "\nwhich does not exist.",
            )
            self.report_error(msg)
            return
        if not os.path.isdir(path):
            msg = (
                "Cannot process\n",
                self.chesstab_directory.get(),
                "\nbecause it is not a directory.",
            )
            self.report_error(msg)
            return

        # Copied from chesstab.gui.chess.py (start)
        ed = modulequery.modules_for_existing_databases(path, FileSpec())
        if not ed:
            tkinter.messagebox.showinfo(
                message="".join(
                    (
                        "Chess database in ",
                        os.path.basename(path),
                        " cannot be opened, or there isn't one.\n\n",
                        "(Is correct database engine available?)",
                    )
                ),
                title="Open",
            )
            return
        elif len(ed) > 1:
            tkinter.messagebox.showinfo(
                message="".join(
                    (
                        "There is more than one chess database in folder\n\n",
                        os.path.basename(path),
                        "\n\nMove the databases to separate folders and try ",
                        "again.  (Use the platform tools for moving files to ",
                        "relocate the database files.)",
                    )
                ),
                title="Open",
            )
            return
        idm = modulequery.installed_database_modules()
        _enginename = None
        for k, v in idm.items():
            if v in ed[0]:
                if _enginename:
                    tkinter.messagebox.showinfo(
                        message="".join(
                            (
                                "Several modules able to open database in\n\n",
                                os.path.basename(path),
                                "\n\navailable.  Unable to choose.",
                            )
                        ),
                        title="Open",
                    )
                    return
                _enginename = k
        if _enginename is None:
            tkinter.messagebox.showinfo(
                message="".join(
                    (
                        "No modules able to open database in\n\n",
                        os.path.basename(path),
                        "\n\navailable.",
                    )
                ),
                title="Open",
            )
            return
        _modulename = APPLICATION_DATABASE_MODULE[_enginename]
        if self._database_modulename != _modulename:
            if self._database_modulename is not None:
                tkinter.messagebox.showinfo(
                    message="".join(
                        (
                            "The database engine needed for this database ",
                            "is not the one already in use.\n\nYou will ",
                            "have to Quit and start the application again ",
                            "to open this database.",
                        )
                    ),
                    title="Open",
                )
                return
            self._database_enginename = _enginename
            self._database_modulename = _modulename

            def import_name(modulename, name):
                try:
                    module = __import__(
                        modulename, globals(), locals(), [name]
                    )
                except ImportError:
                    return None
                return getattr(module, name)

            self._database_class = import_name(_modulename, _ChessDB)
            self._fullposition_class = import_name(
                FULL_POSITION_MODULE[_enginename], _FullPositionDS
            )
            self._engineanalysis_class = import_name(
                ANALYSIS_MODULE[_enginename], _AnalysisDS
            )
        # Copied from chesstab.gui.chess.py (end)

        # Adapted from chesstab.gui.chess.py but much simpler.
        try:
            self.opendatabase = self._database_class(path, allowcreate=True)
            self.opendatabase.open_database()
        except Exception as exc:
            tkinter.messagebox.showinfo(
                message="".join(
                    (
                        "Unable to open database\n\n",
                        str(path),
                        "\n\nThe reported reason is:\n\n",
                        str(exc),
                    )
                ),
                title="Open",
            )
            if self.opendatabase:
                self.opendatabase.close_database()
            self.opendatabase = None
            return

        not_fixed_count = self.do_verification()

        if self.opendatabase:
            self.opendatabase.close_database()
        self.report_action(
            (
                "PGN file",
                os.path.basename(path),
                "done at",
                time.ctime(),
            )
        )
        self.insert_text("\n")
        self.text.see(tkinter.END)
        self.chesstab_directory.set("")

    def do_verification(self):
        """Report games on database with inconsistent castling options and
        piece placement.

        """
        fullposition = self._fullposition_class(
            self.opendatabase, GAMES_FILE_DEF, POSITIONS_FIELD_DEF
        )
        engineanalysis = self._engineanalysis_class(
            self.opendatabase, ANALYSIS_FILE_DEF, VARIATION_FIELD_DEF
        )
        gc = self.opendatabase.database_cursor(GAMES_FILE_DEF, GAMES_FILE_DEF)
        not_fixed_count = 0
        errors = []
        error_fens = []
        board_fens = []
        while True:
            r = gc.next()
            if r is None:
                break
            game = PGN131Fen()
            game.get_first_game(r[1])
            for ps in game.position_strings:
                fullposition.get_full_position_games(ps)
                if fullposition.recordset.is_record_number_in_record_set(r[0]):
                    break
            else:
                self.counter.set(str(r[0]))
                self.text.see(tkinter.END)
                self.text.update()
                continue
            if game.position_fens:
                errors.append(r)
                error_fens.append([])
                board_fens.append([])
                self.insert_text("\n")
                self.insert_text(
                    "Serial " + str(len(errors)) + "\t\tRecord " + str(r[0])
                )
                self.insert_text("\n")
                gpf = game.position_fens
                gbf = game.board_fens
                for e, p in enumerate(gpf):
                    error_fens[-1].append(p)
                    board_fens[-1].append(gbf[e])
                    self.insert_text(p)
                    self.insert_text("\n")
                self.insert_text(literal_eval(r[1]))
                self.insert_text("\n")
                g = PGNFen()
                g.get_first_game(r[1])
                if g.position_fens:
                    not_fixed_count += 1
                    gpf = g.position_fens
                    for p in gpf:
                        self.insert_text(p)
                        self.insert_text("\n")
            self.counter.set(str(r[0]))
            self.text.see(tkinter.END)
            self.text.update()
        gc.close()
        self.insert_text("\n")
        self.insert_text("\n")
        self.insert_text(
            "Total errors " + str(sum(len(e) for e in error_fens))
        )
        self.insert_text("\n")
        self.insert_text("Total games with errors " + str(len(errors)))
        self.insert_text("\n")
        self.insert_text("Total games " + self.counter.get())
        self.insert_text("\n")
        if not_fixed_count:
            return not_fixed_count
        if not errors:
            return 0
        self.insert_text("\n")
        self.insert_text("Fixing castling options.")
        self.insert_text("\n")

        # If transaction surrounds loop a MemoryError is encountered, at no
        # more than 100 games on OpenBSD with bsddb3, citing 'Lock table is out
        # of available locks'.
        le = len(errors)
        for e, x in enumerate(zip(errors, error_fens, board_fens)):
            r, fens, board = x
            del x
            oldgame = ChessDBrecordGameUpdate131()
            oldgame.load_instance(
                self.opendatabase, GAMES_FILE_DEF, GAMES_FILE_DEF, r
            )
            newgame = ChessDBrecordGameUpdate()
            newgame.load_instance(
                self.opendatabase, GAMES_FILE_DEF, GAMES_FILE_DEF, r
            )
            self.opendatabase.start_transaction()
            self.insert_text("\n")
            self.insert_text("Deleting record " + str(r[0]))
            self.text.see(tkinter.END)
            self.text.update()
            self.opendatabase.delete_instance("games", oldgame)
            self.insert_text("\n")
            self.insert_text("Inserting replacement for record " + str(r[0]))
            self.text.see(tkinter.END)
            self.text.update()
            self.opendatabase.put_instance("games", newgame)
            self.insert_text("\n")
            self.insert_text(
                str(e + 1)
                + " of "
                + str(le)
                + " done. "
                + str(le - e - 1)
                + " to do."
            )
            self.text.see(tkinter.END)
            self.text.update()
            ac = self.opendatabase.database_cursor(
                ANALYSIS_FILE_DEF, VARIATION_FIELD_DEF
            )
            replacements = []
            for f, b in zip(fens, board):
                engineanalysis.find_position_analysis(f)
                ar = ac.nearest(f)
                while True:
                    if ar is None:
                        break
                    if ar[0] != f:
                        break
                    replacements.append((ar, get_fen_string(b)))
                    ar = ac.next()
            ac.close()
            if len(replacements):
                self.insert_text("\n")
                self.insert_text(
                    "Correcting "
                    + str(len(replacements))
                    + " position analysis records."
                )
                self.text.see(tkinter.END)
                self.text.update()
            ac = self.opendatabase.database_cursor(
                ANALYSIS_FILE_DEF, ANALYSIS_FILE_DEF
            )
            for ar, fen in replacements:
                oldanalysis = ChessDBrecordAnalysis()
                newanalysis = ChessDBrecordAnalysis()
                dar = ac.setat((ar[1],))
                if dar is None:
                    self.insert_text("\n")
                    self.insert_text("Unable to apply " + fen + " correction.")
                    self.text.see(tkinter.END)
                    self.text.update()
                    continue
                oldanalysis.load_instance(
                    self.opendatabase,
                    ANALYSIS_FILE_DEF,
                    ANALYSIS_FILE_DEF,
                    dar,
                )
                newanalysis.load_instance(
                    self.opendatabase,
                    ANALYSIS_FILE_DEF,
                    ANALYSIS_FILE_DEF,
                    dar,
                )
                newanalysis.value.position = fen
                oldanalysis.newrecord = newanalysis
                self.opendatabase.edit_instance(ANALYSIS_FILE_DEF, oldanalysis)
            ac.close()
            self.opendatabase.commit()
        self.insert_text("\n")
        self.text.see(tkinter.END)

    def set_menu_and_entry_events(self, active):
        menu = self.menu
        if active:
            menu.add_separator()
            menu.add_command(
                label="Process ChessTab Database",
                command=self.report_games_with_inconsistent_castling_options,
                accelerator="Alt F4",
            )
            menu.add_separator()
            menu.add_command(
                label="Select ChessTab Database Directory",
                command=self.select_chesstab_database,
                accelerator="Alt F5",
            )
            menu.add_separator()
            menu.add_command(
                label="Save Log As ...",
                command=self.save_log_as,
                accelerator="Alt F2",
            )
            menu.add_separator()
        else:
            menu.delete(0, tkinter.END)
        for entry in (self.text,):
            self._bind_for_scrolling_only(entry)
        for entry in self.entry, self.text:
            entry.bind(
                "<Alt-KeyPress-F5>",
                "" if not active else self.select_chesstab_database,
            )
            entry.bind(
                "<Alt-KeyPress-F4>",
                ""
                if not active
                else self.report_games_with_inconsistent_castling_options,
            )
            entry.bind(
                "<KeyPress-Return>",
                ""
                if not active
                else self.report_games_with_inconsistent_castling_options,
            )
            entry.bind(
                "<Alt-KeyPress-F2>", "" if not active else self.save_log_as
            )

    def _bind_for_scrolling_only(self, widget):
        widget.bind("<KeyPress>", "break")
        widget.bind("<Home>", "return")
        widget.bind("<Left>", "return")
        widget.bind("<Up>", "return")
        widget.bind("<Right>", "return")
        widget.bind("<Down>", "return")
        widget.bind("<Prior>", "return")
        widget.bind("<Next>", "return")
        widget.bind("<End>", "return")


if __name__ == "__main__":

    Main().root.mainloop()
