# filespec.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Files and fields for chess database.

Specification for sqlite3 database, Berkeley DB database and DPT database.

"""

from solentware_base.core.constants import (
    PRIMARY,
    SECONDARY,
    BTOD_FACTOR,
    DEFAULT_RECORDS,
    DEFAULT_INCREASE_FACTOR,
    BTOD_CONSTANT,
    DDNAME,
    FILE,
    FIELDS,
    FILEDESC,
    INV,
    ORD,
    RRN,
    BRECPPG,
    FILEORG,
    DPT_PRIMARY_FIELD_LENGTH,
    ACCESS_METHOD,
    HASH,
    BTREE,
)
import solentware_base.core.filespec

# PGN Tag fields.
# These are the names recommended in the PGN specification plus others
# commonly used.
# All are well-known PGN Tags: those which are intentionally not indexed
# are commented in PGN_TAG_NAMES.
PGN_TAG_NAMES = frozenset(
    (
        # These are the Seven Tag Roster in the PGN specification.
        "Event",  # EVENT_FIELD_DEF.
        "Site",  # SITE_FIELD_DEF.
        "Date",  # DATE_FIELD_DEF.
        "Round",  # ROUND_FIELD_DEF.
        "White",  # WHITE_FIELD_DEF.
        "Black",  # BLACK_FIELD_DEF.
        "Result",  # RESULT_FIELD_DEF.
        # These are the other tags in the PGN specification.
        "WhiteTitle",
        "BlackTitle",
        "WhiteElo",
        "BlackElo",
        "WhiteUSCF",  # Example of national rating agency.
        "BlackUSCF",  # Example of national rating agency.
        "WhiteNA",
        "BlackNA",
        "WhiteType",
        "BlackType",
        "EventDate",
        "EventSponsor",
        "Stage",
        "Board",
        "Opening",
        "Variation",
        "SubVariation",
        "ECO",
        "NIC",
        "Time",
        "UTCTime",
        "UTCDate",
        "TimeControl",
        "SetUp",
        "FEN",
        "Termination",
        "Annotator",
        "Mode",
        "PlyCount",
        # These are commonly used, in TWIC or LiChess for example.
        "EventType",
        "EventRounds",
        "EventCountry",
        "SourceTitle",
        "Source",
        "SourceDate",
        "SourceVersion",
        "SourceVersionDate",
        "SourceQuality",
        "WhiteTeam",
        "BlackTeam",
        "WhiteRatingDiff",
        "BlackRatingDiff",
    )
)

# Reference profile of a typical game (see FileSpec docstring)
POSITIONS_PER_GAME = 75
PIECES_PER_POSITION = 23
PIECES_TYPES_PER_POSITION = 10  # Added after introduction of chessql.
BYTES_PER_GAME = 700  # Records per page set to 10 because 700 was good.

# Names used to refer to file descriptions
# DPT files or Berkeley DB primary databases
GAMES_FILE_DEF = "games"
CQL_FILE_DEF = "cql"
REPERTOIRE_FILE_DEF = "repertoire"
ANALYSIS_FILE_DEF = "analysis"
SELECTION_FILE_DEF = "selection"
ENGINE_FILE_DEF = "engine"
IDENTITY_FILE_DEF = "identity"

# Names used to refer to field descriptions
# DPT fields or Berkeley DB secondary databases

# games file fields.
GAME_FIELD_DEF = "Game"
PGN_ERROR_FIELD_DEF = "pgnerror"
PGNFILE_FIELD_DEF = "pgnfile"
# NUMBER_FIELD_DEF = "number"
EVENT_FIELD_DEF = "Event"
SITE_FIELD_DEF = "Site"
DATE_FIELD_DEF = "Date"
ROUND_FIELD_DEF = "Round"
WHITE_FIELD_DEF = "White"
BLACK_FIELD_DEF = "Black"
RESULT_FIELD_DEF = "Result"
POSITIONS_FIELD_DEF = "positions"
assert EVENT_FIELD_DEF in PGN_TAG_NAMES
assert SITE_FIELD_DEF in PGN_TAG_NAMES
assert DATE_FIELD_DEF in PGN_TAG_NAMES
assert ROUND_FIELD_DEF in PGN_TAG_NAMES
assert WHITE_FIELD_DEF in PGN_TAG_NAMES
assert BLACK_FIELD_DEF in PGN_TAG_NAMES
assert RESULT_FIELD_DEF in PGN_TAG_NAMES
PIECESQUARE_FIELD_DEF = "piecesquare"
IMPORT_FIELD_DEF = "import"
CQL_QUERY_FIELD_DEF = "cqlquery"
PGN_DATE_FIELD_DEF = "pgndate"
CQL_EVALUATE_FIELD_DEF = "cqleval"

# CQL query file fields.
QUERY_IDENTITY_FIELD_DEF = "queryid"
QUERY_NAME_FIELD_DEF = "queryname"
QUERY_STATUS_FIELD_DEF = "querystatus"

# repertoire file fields.
REPERTOIRE_FIELD_DEF = "Repertoire"
OPENING_FIELD_DEF = "Opening"
OPENING_ERROR_FIELD_DEF = "openingerror"

# analysis file fields.
ANALYSIS_FIELD_DEF = "Analysis"
VARIATION_FIELD_DEF = "variation"
ENGINE_FIELD_DEF = "engine"

# selection file fields.
RULE_IDENTITY_FIELD_DEF = "ruleid"
RULE_FIELD_DEF = "rule"

# engine file fields.
# (Note 'ENGINE_FIELD_DEF' already taken by analysis file)
PROGRAM_FIELD_DEF = "program"
COMMAND_FIELD_DEF = "command"

# identity file fields.
IDENTITY_FIELD_DEF = IDENTITY_FILE_DEF
IDENTITY_TYPE_FIELD_DEF = "identitytype"

# Non-standard field names. Standard is x_FIELD_DEF.title().
# These are used as values in 'SECONDARY', and keys in 'FIELDS', dicts.
_OPENING_ERROR_FIELD_NAME = "OpeningError"
_PGN_DATE_FIELD_NAME = "PGNdate"

# Berkeley DB environment.
DB_ENVIRONMENT_GIGABYTES = 0
DB_ENVIRONMENT_BYTES = 1024000
DB_ENVIRONMENT_MAXLOCKS = 120000  # OpenBSD only.
DB_ENVIRONMENT_MAXOBJECTS = 120000  # OpenBSD only.

# Symas LMMD environment.
LMMD_MINIMUM_FREE_PAGES_AT_START = 20000

# Any CQL query indexed by STATUS_VALUE_NEWGAMES on CQL_STATUS_FIELD_NAME
# has not been recalculated since an update to the games file.  The CQL
# query's _PARTIALGAMES_FIELD_NAME reference on the games file is out of
# date and may be wrong.
STATUS_VALUE_ERROR = "cqlerror"
STATUS_VALUE_NEWGAMES = "changed"
STATUS_VALUE_PENDING = "pending"  # Is this same as STATUS_VALUE_NEWGAMES?

# Any game which needs to be evaluated against the existing CQL queries.
CQL_EVALUATE_FIELD_VALUE = "changed"


def _specification():
    """Return file specification dict."""
    dptdsn = FileSpec.dpt_dsn
    field_name = FileSpec.field_name
    return {
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
            PRIMARY: field_name(GAME_FIELD_DEF),
            DPT_PRIMARY_FIELD_LENGTH: 200,
            SECONDARY: {
                PGN_ERROR_FIELD_DEF: PGN_ERROR_FIELD_DEF.title(),
                PGNFILE_FIELD_DEF: None,
                # NUMBER_FIELD_DEF: None,
                # EVENT_FIELD_DEF: None,
                # SITE_FIELD_DEF: None,
                # DATE_FIELD_DEF: None,
                # ROUND_FIELD_DEF: None,
                # WHITE_FIELD_DEF: None,
                # BLACK_FIELD_DEF: None,
                # RESULT_FIELD_DEF: None,
                POSITIONS_FIELD_DEF: POSITIONS_FIELD_DEF.title(),
                PIECESQUARE_FIELD_DEF: PIECESQUARE_FIELD_DEF.title(),
                CQL_QUERY_FIELD_DEF: CQL_QUERY_FIELD_DEF.title(),
                CQL_EVALUATE_FIELD_DEF: CQL_EVALUATE_FIELD_DEF.title(),
                PGN_DATE_FIELD_DEF: _PGN_DATE_FIELD_NAME,
                IMPORT_FIELD_DEF: None,
            },
            FIELDS: {
                field_name(GAME_FIELD_DEF): None,
                PGN_ERROR_FIELD_DEF.title(): {INV: True, ORD: True},
                field_name(PGNFILE_FIELD_DEF): {INV: True, ORD: True},
                # field_name(NUMBER_FIELD_DEF): {INV: True, ORD: True},
                # WHITE_FIELD_DEF: {INV: True, ORD: True},
                # BLACK_FIELD_DEF: {INV: True, ORD: True},
                # EVENT_FIELD_DEF: {INV: True, ORD: True},
                # ROUND_FIELD_DEF: {INV: True, ORD: True},
                # DATE_FIELD_DEF: {INV: True, ORD: True},
                # RESULT_FIELD_DEF: {INV: True, ORD: True},
                # SITE_FIELD_DEF: {INV: True, ORD: True},
                POSITIONS_FIELD_DEF.title(): {
                    INV: True,
                    ORD: True,
                },  # , ACCESS_METHOD:HASH},
                PIECESQUARE_FIELD_DEF.title(): {
                    INV: True,
                    ORD: True,
                },  # , ACCESS_METHOD:HASH},
                CQL_QUERY_FIELD_DEF.title(): {INV: True, ORD: True},
                CQL_EVALUATE_FIELD_DEF.title(): {INV: True, ORD: True},
                _PGN_DATE_FIELD_NAME: {INV: True, ORD: True},
                field_name(IMPORT_FIELD_DEF): {INV: True, ORD: True},
            },
        },
        CQL_FILE_DEF: {
            DDNAME: "CQL",
            FILE: dptdsn(CQL_FILE_DEF),
            FILEDESC: {
                BRECPPG: 40,
                FILEORG: RRN,
            },
            BTOD_FACTOR: 1,  # a guess
            BTOD_CONSTANT: 100,  # a guess
            DEFAULT_RECORDS: 10000,
            DEFAULT_INCREASE_FACTOR: 0.5,
            PRIMARY: field_name(QUERY_IDENTITY_FIELD_DEF),
            DPT_PRIMARY_FIELD_LENGTH: 127,
            SECONDARY: {
                QUERY_NAME_FIELD_DEF: QUERY_NAME_FIELD_DEF.title(),
                QUERY_STATUS_FIELD_DEF: QUERY_STATUS_FIELD_DEF.title(),
            },
            FIELDS: {
                field_name(QUERY_IDENTITY_FIELD_DEF): None,
                QUERY_NAME_FIELD_DEF.title(): {INV: True, ORD: True},
                QUERY_STATUS_FIELD_DEF.title(): {INV: True, ORD: True},
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
            PRIMARY: field_name(REPERTOIRE_FIELD_DEF),
            DPT_PRIMARY_FIELD_LENGTH: 200,
            SECONDARY: {
                OPENING_FIELD_DEF: None,
                OPENING_ERROR_FIELD_DEF: _OPENING_ERROR_FIELD_NAME,
            },
            FIELDS: {
                field_name(REPERTOIRE_FIELD_DEF): None,
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
            PRIMARY: field_name(ANALYSIS_FIELD_DEF),
            DPT_PRIMARY_FIELD_LENGTH: 200,
            SECONDARY: {
                ENGINE_FIELD_DEF: ENGINE_FIELD_DEF.title(),
                VARIATION_FIELD_DEF: VARIATION_FIELD_DEF.title(),
            },
            FIELDS: {
                field_name(ANALYSIS_FIELD_DEF): None,
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
            PRIMARY: field_name(RULE_IDENTITY_FIELD_DEF),
            DPT_PRIMARY_FIELD_LENGTH: 127,
            SECONDARY: {
                RULE_FIELD_DEF: RULE_FIELD_DEF.title(),
            },
            FIELDS: {
                field_name(RULE_IDENTITY_FIELD_DEF): None,
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
            PRIMARY: field_name(PROGRAM_FIELD_DEF),
            DPT_PRIMARY_FIELD_LENGTH: 127,
            SECONDARY: {
                COMMAND_FIELD_DEF: COMMAND_FIELD_DEF.title(),
            },
            FIELDS: {
                field_name(PROGRAM_FIELD_DEF): None,
                COMMAND_FIELD_DEF.title(): {INV: True, ORD: True},
            },
        },
        IDENTITY_FILE_DEF: {
            DDNAME: "IDENTITY",
            FILE: dptdsn(IDENTITY_FILE_DEF),
            FILEDESC: {
                BRECPPG: 80,
                FILEORG: RRN,
            },
            BTOD_FACTOR: 2.0,
            BTOD_CONSTANT: 50,
            DEFAULT_RECORDS: 10,
            DEFAULT_INCREASE_FACTOR: 0.01,
            PRIMARY: field_name(IDENTITY_FIELD_DEF),
            SECONDARY: {
                IDENTITY_TYPE_FIELD_DEF: None,
            },
            FIELDS: {
                field_name(IDENTITY_FIELD_DEF): None,
                field_name(IDENTITY_TYPE_FIELD_DEF): {
                    INV: True,
                    ORD: True,
                },
            },
        },
    }


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

    def is_consistent_with(self, stored_specification):
        """Raise FileSpecError if stored_specification is not as expected.

        The stored_specification is expected to be consistent with the one
        in the FileSpec instance (self).  The stored_specification should
        be the one read from the database being opened.

        In particular the access method for fields in the database version is
        allowed to be different from the version in self, by being BTREE rather
        than HASH.

        """
        file_spec_error = solentware_base.core.filespec.FileSpecError
        # Compare specification with reference version in self to allow field
        # access methods to differ.  Specification can say, or imply by
        # default, BTREE while reference version can say HASH instead.
        # (Matters for _db and _nosql modules.)
        if self == stored_specification:
            return
        sdbspec = sorted(stored_specification)
        sfsspec = sorted(self)
        if sdbspec != sfsspec:
            raise file_spec_error(
                "".join(
                    (
                        "Specification does not have same files as ",
                        "defined in this FileSpec",
                    )
                )
            )
        msgdh = "".join(
            (
                "Specification does not have same detail headings for each ",
                "file as defined in this FileSpec",
            )
        )
        msgd = "".join(
            (
                "Specification does not have same detail for each file as ",
                "defined in this FileSpec",
            )
        )
        msgfield = "".join(
            (
                "Specification does not have same fields for each file as ",
                "defined in this FileSpec",
            )
        )
        msgam = "".join(
            (
                "Specification does not have same descriptions for each ",
                "field in each file as defined in this FileSpec",
            )
        )
        for dbs, fss in zip(sdbspec, sfsspec):
            sdbs = sorted(s for s in stored_specification[dbs])
            sfss = sorted(s for s in self[fss])
            if sdbs != sfss:
                raise file_spec_error(msgdh)
            if dbs == GAMES_FILE_DEF:
                if dbsd == FIELDS:
                    continue
                if dbsd == SECONDARY:
                    continue
            for dbsd in sdbs:
                if dbsd != FIELDS:
                    if stored_specification[dbs][dbsd] != self[fss][dbsd]:
                        raise file_spec_error(msgd)
                    continue
                sdbsf = stored_specification[dbs][dbsd]
                sfssf = self[fss][dbsd]
                if sorted(sdbsf) != sorted(sfssf):
                    raise file_spec_error(msgfield)
                for fieldname in sdbsf:
                    if sdbsf[fieldname] == sfssf[fieldname]:
                        continue
                    dbfp = sdbsf[fieldname].copy()
                    fsfp = sfssf[fieldname].copy()
                    if ACCESS_METHOD in dbfp:
                        del dbfp[ACCESS_METHOD]
                    if ACCESS_METHOD in fsfp:
                        del fsfp[ACCESS_METHOD]
                    if dbfp != fsfp:
                        raise file_spec_error(msgam)
                    dbfpam = sdbsf[fieldname].get(ACCESS_METHOD, BTREE)
                    fsfpam = sfssf[fieldname].get(ACCESS_METHOD, BTREE)
                    if dbfpam == fsfpam:
                        continue
                    if dbfpam == BTREE and fsfpam == HASH:
                        continue
                    raise file_spec_error(msgam)


def make_filespec(use_specification_items=None, dpt_records=None):
    """Return FileSpec instance."""
    specification = _specification()
    secondary = specification[GAMES_FILE_DEF][SECONDARY]
    for tag in PGN_TAG_NAMES:
        secondary[tag] = tag
    fields = specification[GAMES_FILE_DEF][FIELDS]
    for tag in PGN_TAG_NAMES:
        fields[tag] = {INV: True, ORD: True}
    return FileSpec(
        use_specification_items=use_specification_items,
        dpt_records=dpt_records,
        **specification,
    )
