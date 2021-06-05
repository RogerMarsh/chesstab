# filespec.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Files and fields for chess database.

Specification for sqlite3 database, Berkeley DB database and DPT database.

"""

from solentware_base.core.constants import (
    PRIMARY,
    SECONDARY,
    DEFER,
    BTOD_FACTOR,
    DEFAULT_RECORDS,
    DEFAULT_INCREASE_FACTOR,
    BTOD_CONSTANT,
    DDNAME,
    FILE,
    FOLDER,
    FIELDS,
    FILEDESC,
    FLT,
    INV,
    UAE,
    ORD,
    ONM,
    SPT,
    EO,
    RRN,
    BSIZE,
    BRECPPG,
    BRESERVE,
    BREUSE,
    DSIZE,
    DRESERVE,
    DPGSRES,
    FILEORG,
    DPT_PRIMARY_FIELD_LENGTH,
    ACCESS_METHOD,
    HASH,
)
import solentware_base.core.filespec

# Reference profile of a typical game (see FileSpec docstring)
POSITIONS_PER_GAME = 75
PIECES_PER_POSITION = 23

# Names used to refer to file descriptions
# DPT files or Berkeley DB primary databases
GAMES_FILE_DEF = "games"
PARTIAL_FILE_DEF = "partial"
REPERTOIRE_FILE_DEF = "repertoire"
ANALYSIS_FILE_DEF = "analysis"
SELECTION_FILE_DEF = "selection"
ENGINE_FILE_DEF = "engine"

# Names used to refer to field descriptions
# DPT fields or Berkeley DB secondary databases
GAME_FIELD_DEF = "Game"
SOURCE_FIELD_DEF = "source"
EVENT_FIELD_DEF = "Event"
SITE_FIELD_DEF = "Site"
DATE_FIELD_DEF = "Date"
ROUND_FIELD_DEF = "Round"
WHITE_FIELD_DEF = "White"
BLACK_FIELD_DEF = "Black"
RESULT_FIELD_DEF = "Result"
POSITIONS_FIELD_DEF = "positions"
PIECESQUAREMOVE_FIELD_DEF = "piecesquaremove"
PIECEMOVE_FIELD_DEF = "piecemove"
SQUAREMOVE_FIELD_DEF = "squaremove"
PARTIAL_FIELD_DEF = "Partial"
PARTIALPOSITION_FIELD_DEF = "partialposition"
PARTIALPOSITION_NAME_FIELD_DEF = "partialpositionname"
NEWGAMES_FIELD_DEF = "newgames"
REPERTOIRE_FIELD_DEF = "Repertoire"
OPENING_FIELD_DEF = "Opening"
OPENING_ERROR_FIELD_DEF = "openingerror"
PGN_DATE_FIELD_DEF = "pgndate"
ANALYSIS_FIELD_DEF = "Analysis"
VARIATION_FIELD_DEF = "variation"
ENGINE_FIELD_DEF = "engine"
SELECTION_FIELD_DEF = "rulename"
RULE_FIELD_DEF = "rule"
PROGRAM_FIELD_DEF = "program"
COMMAND_FIELD_DEF = "command"

# Non-standard field names. Standard is x_FIELD_DEF.title()
_PIECESQUAREMOVE_FIELD_NAME = "PieceSquareMove"
_PIECEMOVE_FIELD_NAME = "PieceMove"
_SQUAREMOVE_FIELD_NAME = "SquareMove"
_PARTIALPOSITION_FIELD_NAME = "PartialPosition"
_PP_NAME_FIELD_NAME = "PartialPositionName"
_NEWGAMES_FIELD_NAME = "NewGames"
_OPENING_ERROR_FIELD_NAME = "OpeningError"
_PGN_DATE_FIELD_NAME = "PGNdate"

# Berkeley DB environment.
DB_ENVIRONMENT_GIGABYTES = 0
DB_ENVIRONMENT_BYTES = 1024000
DB_ENVIRONMENT_MAXLOCKS = 10000  # OpenBSD only.

# Any partial position indexed by NEWGAMES_FIELD_VALUE on _NEWGAMES_FIELD_NAME
# has not been recalculated since an update to the games file.  The partial
# position's _PARTIALGAMES_FIELD_NAME reference on the games file is out of
# date and may be wrong.
NEWGAMES_FIELD_VALUE = "changed"


class FileSpec(solentware_base.core.filespec.FileSpec):

    """Specify a chess database.

    Parameters for Berkeley DB, DPT, and Sqlite3, are defined.

    Ignore settings irrelevant to the database engine in use.

    Berkeley DB and Sqlite3 look after themselves for sizing purposes when
    increasing the size of a database.

    The sizing parameters for the Games file in DPT were chosen using figures
    from a few game collections: ~25000 games in 4NCL up to 2011, ~4500 games
    in a California collection spanning the 20th century, ~2500 games in a
    collection of Volga Gambit games, ~150000 games from section 00 of
    enormous.pgn, ~500 games from 1997 4NCL divisions one and two separately.

             <            per game              >  <     pages    >
      Games Positions Pieces Data bytes PGN Bytes  Table B  Table D   Ratio
      25572     74      23      493        761       2557     20148     7.9
       4445     75      23      418        682        445      6034    13.6
       2324     76      23      416        683        232      3308    14.3
     156954     75      23      375        637      15803    120932     7.7
        528     77      23      481        757         52       891    17.1
        528     74      23      472        739         52       863    16.6

    There is not enough data to conclude that Table D usage is proportional
    to the index entries per game, but it is reasonable to expect this and
    the Positions and Table D ratios in the two 528 game samples are close
    enough to make the assumption.  Above, say, 20000 games it is assumed
    that typical games, 75 positions per game and 23 pieces per position,
    lead to a Table B to Table D ratio of 8, or 14 when CQL statements are
    supported.  The higher ratios at lower numbers of games are assumed to
    arise from the lower chance of compressed inverted lists.

    It is completely unclear what value to use for records per Table B page
    because games can have comments and variations as well as just the moves
    played.  The samples have few comments or variations. A value of 10 seems
    as good a compromise as any between wasting space and getting all record
    numbers used. 16 average sized records would fit on a Table B page.

    """

    def __init__(
        self, use_specification_items=None, dpt_records=None, **kargs
    ):
        """Define chess database."""
        dptdsn = FileSpec.dpt_dsn
        fn = FileSpec.field_name

        super(FileSpec, self).__init__(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
            **{
                GAMES_FILE_DEF: {
                    DDNAME: "GAMES",
                    FILE: dptdsn(GAMES_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 10,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 14,
                    BTOD_CONSTANT: 800,
                    DEFAULT_RECORDS: 10000,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fn(GAME_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 200,
                    SECONDARY: {
                        SOURCE_FIELD_DEF: SOURCE_FIELD_DEF.title(),
                        EVENT_FIELD_DEF: None,
                        SITE_FIELD_DEF: None,
                        DATE_FIELD_DEF: None,
                        ROUND_FIELD_DEF: None,
                        WHITE_FIELD_DEF: None,
                        BLACK_FIELD_DEF: None,
                        RESULT_FIELD_DEF: None,
                        POSITIONS_FIELD_DEF: POSITIONS_FIELD_DEF.title(),
                        PIECESQUAREMOVE_FIELD_DEF: _PIECESQUAREMOVE_FIELD_NAME,
                        PIECEMOVE_FIELD_DEF: _PIECEMOVE_FIELD_NAME,
                        SQUAREMOVE_FIELD_DEF: _SQUAREMOVE_FIELD_NAME,
                        PARTIALPOSITION_FIELD_DEF: _PARTIALPOSITION_FIELD_NAME,
                        PGN_DATE_FIELD_DEF: _PGN_DATE_FIELD_NAME,
                    },
                    FIELDS: {
                        fn(GAME_FIELD_DEF): None,
                        SOURCE_FIELD_DEF.title(): {INV: True, ORD: True},
                        WHITE_FIELD_DEF: {INV: True, ORD: True},
                        BLACK_FIELD_DEF: {INV: True, ORD: True},
                        EVENT_FIELD_DEF: {INV: True, ORD: True},
                        ROUND_FIELD_DEF: {INV: True, ORD: True},
                        DATE_FIELD_DEF: {INV: True, ORD: True},
                        RESULT_FIELD_DEF: {INV: True, ORD: True},
                        SITE_FIELD_DEF: {INV: True, ORD: True},
                        POSITIONS_FIELD_DEF.title(): {
                            INV: True,
                            ORD: True,
                        },  # , ACCESS_METHOD:HASH},
                        _PIECESQUAREMOVE_FIELD_NAME: {
                            INV: True,
                            ORD: True,
                        },  # , ACCESS_METHOD:HASH},
                        _PIECEMOVE_FIELD_NAME: {
                            INV: True,
                            ORD: True,
                        },  # , ACCESS_METHOD:HASH},
                        _SQUAREMOVE_FIELD_NAME: {
                            INV: True,
                            ORD: True,
                        },  # , ACCESS_METHOD:HASH},
                        _PARTIALPOSITION_FIELD_NAME: {INV: True, ORD: True},
                        _PGN_DATE_FIELD_NAME: {INV: True, ORD: True},
                    },
                },
                PARTIAL_FILE_DEF: {
                    DDNAME: "PARTIAL",
                    FILE: dptdsn(PARTIAL_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 40,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 1,  # a guess
                    BTOD_CONSTANT: 100,  # a guess
                    DEFAULT_RECORDS: 10000,
                    DEFAULT_INCREASE_FACTOR: 0.5,
                    PRIMARY: fn(PARTIAL_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 127,
                    SECONDARY: {
                        PARTIALPOSITION_NAME_FIELD_DEF: _PP_NAME_FIELD_NAME,
                        NEWGAMES_FIELD_DEF: _NEWGAMES_FIELD_NAME,
                    },
                    FIELDS: {
                        fn(PARTIAL_FIELD_DEF): None,
                        _PP_NAME_FIELD_NAME: {INV: True, ORD: True},
                        _NEWGAMES_FIELD_NAME: {INV: True, ORD: True},
                    },
                },
                REPERTOIRE_FILE_DEF: {
                    DDNAME: "REPERT",
                    FILE: dptdsn(REPERTOIRE_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 1,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 0.1,
                    BTOD_CONSTANT: 800,
                    DEFAULT_RECORDS: 100,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fn(REPERTOIRE_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 200,
                    SECONDARY: {
                        OPENING_FIELD_DEF: None,
                        OPENING_ERROR_FIELD_DEF: _OPENING_ERROR_FIELD_NAME,
                    },
                    FIELDS: {
                        fn(REPERTOIRE_FIELD_DEF): None,
                        OPENING_FIELD_DEF: {INV: True, ORD: True},
                        _OPENING_ERROR_FIELD_NAME: {INV: True, ORD: True},
                    },
                },
                ANALYSIS_FILE_DEF: {
                    DDNAME: "ANALYSIS",
                    FILE: dptdsn(ANALYSIS_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 10,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 1,
                    BTOD_CONSTANT: 800,
                    DEFAULT_RECORDS: 100000,
                    DEFAULT_INCREASE_FACTOR: 1.0,
                    PRIMARY: fn(ANALYSIS_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 200,
                    SECONDARY: {
                        ENGINE_FIELD_DEF: ENGINE_FIELD_DEF.title(),
                        VARIATION_FIELD_DEF: VARIATION_FIELD_DEF.title(),
                    },
                    FIELDS: {
                        fn(ANALYSIS_FIELD_DEF): None,
                        ENGINE_FIELD_DEF.title(): {INV: True, ORD: True},
                        VARIATION_FIELD_DEF.title(): {INV: True, ORD: True},
                    },
                },
                SELECTION_FILE_DEF: {
                    DDNAME: "SLCTRULE",
                    FILE: dptdsn(SELECTION_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 20,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 1,  # a guess
                    BTOD_CONSTANT: 100,  # a guess
                    DEFAULT_RECORDS: 10000,
                    DEFAULT_INCREASE_FACTOR: 0.5,
                    PRIMARY: fn(SELECTION_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 127,
                    SECONDARY: {
                        RULE_FIELD_DEF: RULE_FIELD_DEF.title(),
                    },
                    FIELDS: {
                        fn(SELECTION_FIELD_DEF): None,
                        RULE_FIELD_DEF.title(): {INV: True, ORD: True},
                    },
                },
                ENGINE_FILE_DEF: {
                    DDNAME: "ENGINE",
                    FILE: dptdsn(ENGINE_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 150,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 1,  # a guess
                    BTOD_CONSTANT: 100,  # a guess
                    DEFAULT_RECORDS: 1000,
                    DEFAULT_INCREASE_FACTOR: 0.5,
                    PRIMARY: fn(PROGRAM_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 127,
                    SECONDARY: {
                        COMMAND_FIELD_DEF: COMMAND_FIELD_DEF.title(),
                    },
                    FIELDS: {
                        fn(PROGRAM_FIELD_DEF): None,
                        COMMAND_FIELD_DEF.title(): {INV: True, ORD: True},
                    },
                },
            }
        )
