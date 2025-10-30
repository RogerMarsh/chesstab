# chessrecord.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definitions for chess game database.

The ...Game... classes differ in the PGN parser used as a superclass of the
...valueGame... class.  These generate different combinations of the available
data structures from the game score for the various display and update uses.
The ...Update classes allow editing of a, possibly incomplete, game score.

"""
import os
from ast import literal_eval

from solentware_base.core.record import (
    KeyData,
    Value,
    ValueList,
    ValueText,
    Record,
)
from solentware_base.core.segmentsize import SegmentSize
from solentware_base.core.merge import SortIndiciesToSequentialFiles

from pgn_read.core.parser import PGN
from pgn_read.core.movetext_parser import PGNMoveText
from pgn_read.core.tagpair_parser import PGNTagPair
from pgn_read.core.constants import (
    # SEVEN_TAG_ROSTER,
    TAG_DATE,
    TAG_WHITE,
    TAG_BLACK,
)

from .pgn import (
    GameDisplayMoves,
    GameRepertoireDisplayMoves,
    GameRepertoireTags,
    GameRepertoireUpdate,
    GameTags,
    GameUpdate,
    GameUpdatePosition,
    GameUpdatePieceLocation,
    GameMoveText,
    GameStore,
    GameMergeUpdate,
)
from .constants import (
    START_RAV,
    END_RAV,
    NON_MOVE,
    TAG_OPENING,
    START_COMMENT,
    ERROR_START_COMMENT,
    ESCAPE_END_COMMENT,
    HIDE_END_COMMENT,
    END_COMMENT,
    SPECIAL_TAG_DATE,
    FILE,
    GAME,
    WHITE_WIN,
    BLACK_WIN,
    DRAW,
    UNKNOWN_RESULT,
)
from .cqlstatement import CQLStatement
from .filespec import (
    POSITIONS_FIELD_DEF,
    PGN_ERROR_FIELD_DEF,
    PIECESQUARE_FIELD_DEF,
    GAME_FIELD_DEF,
    GAMES_FILE_DEF,
    CQL_QUERY_FIELD_DEF,
    CQL_EVALUATE_FIELD_DEF,
    REPERTOIRE_FILE_DEF,
    PGN_DATE_FIELD_DEF,
    VARIATION_FIELD_DEF,
    ENGINE_FIELD_DEF,
    QUERY_NAME_FIELD_DEF,
    RULE_FIELD_DEF,
    COMMAND_FIELD_DEF,
    PGNFILE_FIELD_DEF,
    # NUMBER_FIELD_DEF,
    IMPORT_FIELD_DEF,
    # EVENT_FIELD_DEF,
    # SITE_FIELD_DEF,
    # DATE_FIELD_DEF,
    # ROUND_FIELD_DEF,
    # WHITE_FIELD_DEF,
    # BLACK_FIELD_DEF,
    # RESULT_FIELD_DEF,
    PGN_TAG_NAMES,
)
from .analysis import Analysis
from .querystatement import QueryStatement, re_normalize_player_name
from .engine import Engine

PLAYER_NAME_TAGS = frozenset((TAG_WHITE, TAG_BLACK))
GAME_TERMINATION_MARKERS = frozenset(
    (WHITE_WIN, BLACK_WIN, DRAW, UNKNOWN_RESULT)
)


class ChessRecordError(Exception):
    """Exception class for chessrecor module."""


class ChessDBkeyGame(KeyData):
    """Primary key of chess game."""

    def __eq__(self, other):
        """Return (self == other).  Attributes are compared explicitly."""
        return self.recno == other.recno

    def __ne__(self, other):
        """Return (self != other).  Attributes are compared explicitly."""
        return self.recno != other.recno


class _GameLoadPack(ValueList):
    """Attributes and methods common to game value classes."""

    attributes = {
        "reference": None,  # dict of PGN file name and game number in file.
        "pgntext": None,  # repr() of PGN text of game.
    }
    _attribute_order = ("pgntext", "reference")
    assert set(_attribute_order) == set(attributes)

    def load(self, value):
        """Get game from value."""
        super().load(value)
        # pylint attribute-defined-outside-init W0201 occurs because
        # __init__(), which defined self.collected_game, was removed
        # from ChessDBvalueGame when it became a subclass of ValueList
        # rather than Value.
        # pylint no-member E1101 ignored because self.read_games is
        # expected to be in a sibling class in hierarchy.
        self.collected_game = next(self.read_games(literal_eval(self.pgntext)))

    def pack(self):
        """Return PGN text and indexes for game."""
        # pylint attribute-defined-outside-init W0201 occurs because
        # self.pgntext is set by Value.load() or Value._empty() methods
        # which are driven by the attributes dict(), a class attribute.
        # pylint no-member E1101 ignored because self.collected_game is
        # expected to be in a sibling class in hierarchy.
        self.pgntext = repr("".join(self.collected_game.pgn_text))
        value = super().pack()
        self.pack_detail(value[1])
        return value


# Changes are made to ChessDBvalueRepertoireUpdate so ChessDBvaluePGN can
# be subclass of ValueList rather than Value.
class ChessDBvaluePGN(PGN, _GameLoadPack):
    """Methods common to all chess PGN data classes."""

    @staticmethod
    def encode_move_number(key):
        """Return base 256 string for integer, left-end most significant."""
        return key.to_bytes(2, byteorder="big")

    def pack_detail(self, index):
        """Fill index with detail from game's PGN Tags."""
        index[PGNFILE_FIELD_DEF] = [self.reference[FILE]]
        # index[NUMBER_FIELD_DEF] = [self.reference[GAME]]


def _pack_tags_into_index(tags, index):
    """Fill index with detail from game's PGN Tags."""
    for field in PGN_TAG_NAMES.intersection(tags):
        if field in PLAYER_NAME_TAGS:
            # PGN specification states colon is used to separate player
            # names in consultation games.
            index[field] = [
                " ".join(re_normalize_player_name.findall(tf))
                for tf in tags[field].split(":")
            ]

        else:
            index[field] = [tags[field]]
    if TAG_DATE in tags:
        index[PGN_DATE_FIELD_DEF] = [tags[TAG_DATE].replace(*SPECIAL_TAG_DATE)]


class ChessDBvalueGame(ChessDBvaluePGN):
    """Chess game data.

    Data is indexed by PGN Seven Tag Roster tags.

    """

    def __init__(self, game_class=GameDisplayMoves):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)

    def pack_detail(self, index):
        """Fill index with detail from game's PGN Tags."""
        super().pack_detail(index)
        _pack_tags_into_index(self.collected_game.pgn_tags, index)


class ChessDBrecordGame(Record):
    """Chess game record customised for displaying the game score and tags."""

    def __init__(self):
        """Extend with move number encode and decode methods."""
        super().__init__(ChessDBkeyGame, ChessDBvalueGame)

    def clone(self):
        """Return copy of ChessDBrecordGame instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGame.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super().clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string, left-end most significant."""
        return int.from_bytes(skey, byteorder="big")

    def delete_record(self, database, dbset):
        """Delete record not allowed using ChessDBrecordGame class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError

    def edit_record(self, database, dbset, dbname, newrecord):
        """Edit record not allowed using ChessDBrecordGame class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The keys for the secondary databases in a Database instance are
        embedded in, or derived from, the PGN string for the game.  All
        except the positions are held in self.value.collected_game.pgn_tags.
        Multiple position keys can arise becuse all repetitions of a
        position are of interest.  The partial argument is used to select
        the relevant keys.  The position is in partial and the keys will
        differ in the move number.

        """
        dbname = datasource.dbname
        if dbname != POSITIONS_FIELD_DEF:
            if dbname == GAMES_FILE_DEF:
                return [(self.key.recno, self.srvalue)]
            if dbname in self.value.collected_game.pgn_tags:
                return [
                    (
                        self.value.collected_game.pgn_tags[dbname],
                        self.key.pack(),
                    )
                ]
            if dbname in self.value.reference:
                return [
                    (
                        self.value.reference[dbname],
                        self.key.pack(),
                    )
                ]
            return []
        if partial is None:
            return []

        moves = self.value.moves
        gamekey = datasource.dbhome.encode_record_number(self.key.pack())
        rav = 0
        ref = 0
        keys = []
        convert_format = datasource.dbhome.db_compatibility_hack

        elements = tuple(partial)
        for token in moves:
            if token == START_RAV:
                rav += 1
            elif token == END_RAV:
                rav -= 1
            elif token == NON_MOVE:
                pass
            else:
                if token[-1] == elements:
                    record = (partial, None)
                    keys.append(convert_format(record, gamekey))
            ref += 1
        return keys

    def put_record(self, database, dbset):
        """Put record not allowed using ChessDBrecordGame class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError


class ChessDBrecordGameText(Record):
    """Chess game record customised for processing the game score as text.

    Used to export games or repertoires from a database in the 'Import Format',
    see PGN specification 3.1, used to store the games.

    """

    def __init__(self):
        """Extend with move number encode and decode methods."""
        super().__init__(ChessDBkeyGame, ValueText)

    def clone(self):
        """Return copy of ChessDBrecordGameText instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGameText.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super().clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string, left-end most significant."""
        return int.from_bytes(skey, byteorder="big")

    def delete_record(self, database, dbset):
        """Delete record not allowed using ChessDBrecordGameText class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError

    def edit_record(self, database, dbset, dbname, newrecord):
        """Edit record not allowed using ChessDBrecordGameText class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError

    def put_record(self, database, dbset):
        """Put record not allowed using ChessDBrecordGameText class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError


class ChessDBvalueGameTags(ChessDBvalueGame):
    """Chess game data excluding PGN movetext but including PGN Tags."""

    def __init__(self):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=GameTags)

    def get_field_value(self, fieldname, occurrence=0):
        """Return value of a field occurrence, the first by default.

        Added to support Find and Where classes.

        """
        return self.collected_game.pgn_tags.get(fieldname, None)

    def get_field_values(self, fieldname):
        """Return tuple of field values for fieldname.

        Added to support Find and Where classes.

        """
        if fieldname in PLAYER_NAME_TAGS:
            return tuple(
                " ".join(re_normalize_player_name.findall(name))
                for name in self.get_field_value(fieldname).split(":")
            )
        return (self.get_field_value(fieldname),)

    def load(self, value):
        """Get game from value.

        The exception is a hack introduced to cope with a couple of games
        found in TWIC downloads which give the result as '1-0 ff' in the
        Result tag, and append ' ff' to the movetext after the '1-0' Game
        Termination Marker.  The 'ff' gets stored on ChessTab databases as
        the game score for an invalid game score.

        It is assumed other cases will need this trick, which seems to be
        needed only when displaying a list of games and not when displaying
        the full game score.

        """
        try:
            super().load(value)
        except StopIteration:
            # pylint attribute-defined-outside-init W0201 occurs because
            # __init__(), which defined self.collected_game, was removed
            # from ChessDBvalueGame when it became a subclass of ValueList
            # rather than Value.
            game = literal_eval(value)
            # Avoid pycodestyle message: E501 line too long (83 > 79 ...).
            gstrt = self._game_class().get_seven_tag_roster_tags()
            super().load(
                repr([repr("".join((gstrt, "{" + game[0] + "}*"))), game[1]])
            )


class ChessDBrecordGameTags(Record):
    """Chess game record customised to display tag information for a game."""

    def __init__(self):
        """Extend with move number encode and decode methods."""
        super().__init__(ChessDBkeyGame, ChessDBvalueGameTags)


class ChessDBrecordGamePosition(Record):
    """Chess game record customised for displaying the game score only.

    Much of the game structure to be represented in the row display is held
    in the Tkinter.Text object created for display.  Thus the processing of
    the record data is delegated to a PositionScore instance created when
    filling the grid.

    """

    def __init__(self):
        """Extend with move number encode and decode methods."""
        super().__init__(ChessDBkeyGame, ValueText)

    def clone(self):
        """Return copy of ChessDBrecordGamePosition instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGamePosition.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super().clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string, left-end most significant."""
        return int.from_bytes(skey, byteorder="big")

    def delete_record(self, database, dbset):
        """Delete record not allowed using ChessDBrecordGamePosition class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError

    def edit_record(self, database, dbset, dbname, newrecord):
        """Edit record not allowed using ChessDBrecordGamePosition class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError

    def put_record(self, database, dbset):
        """Put record not allowed using ChessDBrecordGamePosition class.

        Process the game using a ChessDBrecordGameUpdate instance

        """
        raise ChessRecordError


class ChessDBvaluePGNIdentity(ChessDBvaluePGN):
    """Chess game data with position, piece location, and PGN Tag, indexes."""

    # ChessDBvaluePGNUpdate is now a subclass of ChessDBvaluePGNIdentity.
    # The comments below were written when ChessDBvaluePGNIdentity did not
    # exist and this class was called ChessDBvaluePGNUpdate.
    # Replaces ChessDBvaluePGNUpdate and ChessDBvalueGameImport which had been
    # identical for a considerable time.
    # Decided that PGNUpdate should remain in pgn.core.parser because that code
    # generates data while this code updates a database.
    # Now moved to .core.pgn.GameUpdate.
    # ChessDBvalueGameImport had this comment:
    # Implication of original is encode_move_number not supported and load in
    # ChessDBvaluePGN superclass is used.

    def __init__(self, game_class=GameUpdate):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)
        self.gamesource = None

    def pack_detail(self, index):
        """Delegate then add as error if indexing not done."""
        super().pack_detail(index)
        if not self.do_full_indexing():
            index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Detected PGN errors are wrapped in a comment starting 'Error: ' so
        method is_pgn_valid() is not used to decide what indexing to do.

        """
        return self.gamesource is None

    # Before ChessTab 4.3 could test the string attribute of any re.match
    # object for PGN text.  The match objects are not available in version
    # 4.3 and later.  At 4.3 the test was done only for the value attribute
    # of a record, so it is possible to test against the srvalue attribute
    # of the record instance.
    def is_error_comment_present(self):
        """Return True if an {Error: ...} comment is in the PGN text."""
        return START_COMMENT + ERROR_START_COMMENT in "".join(
            self.collected_game.pgn_text
        )


class ChessDBvaluePGNIndex(ChessDBvaluePGNIdentity):
    """Chess game data with references to indicies to be applied."""

    def pack_detail(self, index):
        """Delegate then add index names to IMPORT_FIELD_DEF index."""
        super().pack_detail(index)
        if self.do_full_indexing():
            index[IMPORT_FIELD_DEF] = [
                IMPORT_FIELD_DEF,
                # POSITIONS_FIELD_DEF,
                # PIECESQUARE_FIELD_DEF,
                # PGN_DATE_FIELD_DEF,
                # EVENT_FIELD_DEF,
                # SITE_FIELD_DEF,
                # DATE_FIELD_DEF,
                # ROUND_FIELD_DEF,
                # WHITE_FIELD_DEF,
                # BLACK_FIELD_DEF,
                # RESULT_FIELD_DEF,
            ]


class ChessDBvaluePGNUpdate(ChessDBvaluePGNIdentity):
    """Chess game data with position, piece location, and PGN Tag, indexes."""

    def pack_detail(self, index):
        """Delegate then add position and piece location detail to index."""
        super().pack_detail(index)
        if self.do_full_indexing():
            game = self.collected_game
            _pack_tags_into_index(game.pgn_tags, index)
            index[POSITIONS_FIELD_DEF] = game.positionkeys
            index[PIECESQUARE_FIELD_DEF] = game.piecesquarekeys
            try:
                index[PGN_DATE_FIELD_DEF] = [
                    game.pgn_tags[TAG_DATE].replace(*SPECIAL_TAG_DATE)
                ]
            except KeyError:
                index[PGN_DATE_FIELD_DEF] = []


class ChessDBvaluePGNDelete(ChessDBvaluePGNUpdate):
    """Chess game data with position, piece location, and PGN Tag, indexes."""

    def pack_detail(self, index):
        """Delegate then add position and piece location detail to index."""
        super().pack_detail(index)
        index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Game is being deleted so full indexing is always done to remove
        all index references.

        """
        return True


class ChessDBvaluePGNEdit(ChessDBvaluePGNUpdate):
    """Chess game data with position, piece location, and PGN Tag, indexes."""

    def pack_detail(self, index):
        """Delegate then add position and piece location detail to index."""
        super().pack_detail(index)
        game = self.collected_game
        if game.errors_hidden_in_comments or not game.is_tag_roster_valid():
            index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Detected PGN errors are wrapped in a comment starting 'Error: ' so
        method is_pgn_valid() is not used to decide what indexing to do.

        """
        return self.collected_game.is_tag_roster_valid()


class ChessDBrecordGameUpdate(Record):
    """Chess game record customized for editing database records.

    Used to edit or insert a single record by typing in a widget.

    """

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvaluePGNUpdate
    ):
        """Extend with move number encode and decode methods."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)

    def clone(self):
        """Return copy of ChessDBrecordGameUpdate instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGameUpdate.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super().clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string, left-end most significant."""
        return int.from_bytes(skey, byteorder="big")

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The keys for the secondary databases in a Database instance are
        embedded in, or derived from, the PGN string for the game.  All
        except the positions are held in self.value.collected_game.pgn_tags.
        Multiple position keys can arise becuse all repetitions of a
        position are of interest.  The partial argument is used to select
        the relevant keys.  The position is in partial and the keys will
        differ in the move number.

        """
        dbname = datasource.dbname
        if dbname != POSITIONS_FIELD_DEF:
            if dbname == GAMES_FILE_DEF:
                return [(self.key.recno, self.srvalue)]
            if dbname in self.value.collected_game.pgn_tags:
                return [
                    (
                        self.value.collected_game.pgn_tags[dbname],
                        self.key.pack(),
                    )
                ]
            if dbname in self.value.reference:
                return [
                    (
                        self.value.reference[dbname],
                        self.key.pack(),
                    )
                ]
            return []
        if partial is None:
            return []

        moves = self.value.moves
        gamekey = datasource.dbhome.encode_record_number(self.key.pack())
        rav = 0
        ref = 0
        keys = []
        convert_format = datasource.dbhome.db_compatibility_hack

        elements = tuple(partial)
        for token in moves:
            if token == START_RAV:
                rav += 1
            elif token == END_RAV:
                rav -= 1
            elif token == NON_MOVE:
                pass
            else:
                if token[-1] == elements:
                    record = (partial, None)
                    keys.append(convert_format(record, gamekey))
            ref += 1
        return keys


class ChessDBvaluePGNMergeUpdate(ChessDBvaluePGNUpdate):
    """Chess game data with position, piece location, and PGN Tag, indexes.

    Alternative valueclass argument for ChessDBrecordGameSequential if the
    PGN movetext can be trusted to not have moves which leave the mover's
    king in check.
    """

    def __init__(self, game_class=GameMergeUpdate):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)


class ChessDBrecordGameSequential(Record):
    """Customise Record to index games by dump, merge, and load."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvaluePGNUpdate
    ):
        """Customise Record with chess database key and value classes."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)

    def write_index_entries_to_sequential_files(
        self, database, index_games, reporter=None, quit_event=None
    ):
        """Write index entries for imported games to sequential file."""
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Writing index entries to sorted files.")
        sorter = SortIndiciesToSequentialFiles(
            database,
            GAMES_FILE_DEF,
            ignore=set(
                (
                    IMPORT_FIELD_DEF,
                    PGNFILE_FIELD_DEF,
                    CQL_QUERY_FIELD_DEF,
                    CQL_EVALUATE_FIELD_DEF,
                    PGN_ERROR_FIELD_DEF,
                )
            ),
        )
        # Not sure this is not needed yet: the sorter uses database though.
        # self.set_database(database)
        database.set_int_to_bytes_lookup(lookup=True)
        cursor = index_games.create_recordsetbase_cursor(internalcursor=True)
        while True:
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Merge index stopped.")
                database.set_int_to_bytes_lookup(lookup=False)
                return False
            current_record = cursor.next()
            if current_record is None:
                break
            self.load_record(current_record)
            try:
                count = sorter.add_instance(self)
                if count is not None and reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Games before ",
                                format(count, ","),
                                " written to sorted files.",
                            )
                        )
                    )
            except FileExistsError:
                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Unable to dump '",
                                sorter.file,
                                "' indicies because ",
                                os.path.dirname(sorter.dump_file),
                                " is not a directory.",
                            )
                        )
                    )
                raise
        try:
            sorter.write_final_segments_to_sequential_file()
        except FileExistsError:
            if reporter is not None:
                reporter.append_text(
                    "".join(
                        (
                            "Unable to dump '",
                            sorter.file,
                            "' indicies because ",
                            os.path.dirname(sorter.dump_file),
                            " is not a directory.",
                        )
                    )
                )
            raise
        database.set_int_to_bytes_lookup(lookup=False)
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Writing index entries to sorted files done.")
        return True


class ChessDBvaluePGNStore(PGN, _GameLoadPack):
    """Chess game data with references to indicies to be applied."""

    def __init__(self, game_class=GameStore):
        """Delegate to superclass with game_class argument."""
        super().__init__(game_class=game_class)
        self.gamesource = None

    def pack_detail(self, index):
        """Add PGN file reference and indexing flag for game to index.

        Replace indexing flag by an error flag if errors are found.

        """
        index[PGNFILE_FIELD_DEF] = [self.reference[FILE]]
        if self.do_full_indexing():
            index[IMPORT_FIELD_DEF] = [IMPORT_FIELD_DEF]
        else:
            index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Detected PGN errors are wrapped in a comment starting 'Error: ' so
        method is_pgn_valid() is not used to decide what indexing to do.

        """
        return self.collected_game.is_pgn_valid()

    # Copied from core.pgn._Game class.
    def pgn_mark_comment_in_error(self, comment):
        """Return comment with '}' replaced by a presumed unlikely sequence.

        One possibility is to wrap the error in a '{...}' comment.  The '}'
        token in any wrapped commment would end the comment wrapping the error
        prematurely, so replace with HIDE_END_COMMENT.

        """
        return comment.replace(END_COMMENT, HIDE_END_COMMENT)


class ChessDBrecordGameStore(Record):
    """Customise chess game record to store games from PGN files."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvaluePGNStore
    ):
        """Customise Record with chess database key and value classes."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)

    def import_pgn(
        self, database, source, sourcename, reporter=None, quit_event=None
    ):
        """Update database with games read from source."""
        self.set_database(database)
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Extracting games from " + sourcename)
        db_segment_size = SegmentSize.db_segment_size
        value = self.value
        value.reference = {}
        reference = value.reference
        reference[FILE] = sourcename
        game_number = 0
        # game_number_str = lambda number: str(len(number)) + number
        copy_number = 0
        collected_game = None
        file_games = database.recordlist_key(
            GAMES_FILE_DEF,
            PGNFILE_FIELD_DEF,
            key=database.encode_record_selector(sourcename),
        )
        cursor = file_games.create_recordsetbase_cursor(internalcursor=True)
        file_game_numbers = set()
        present_game = cursor.first()
        if present_game is not None:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "Noting games to ignore by position in file."
                )
                reporter.append_text_only(
                    " ".join(
                        (
                            "This takes about two minutes per million",
                            "games from file already on database.",
                        )
                    )
                )
            file_game_numbers.add(literal_eval(present_game[1])[1][GAME])
        while True:
            present_game = cursor.next()
            if present_game is None:
                break
            file_game_numbers.add(literal_eval(present_game[1])[1][GAME])
        file_games.close()
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Extract started.")
            reporter.append_text_only("")
        for collected_game in value.read_games(source):
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Import stopped.")
                return False
            game_number += 1
            reference[GAME] = str(game_number)
            if file_game_numbers:
                if reference[GAME] in file_game_numbers:
                    if game_number % db_segment_size == 0:
                        if reporter is not None:
                            reporter.append_text(
                                "".join(
                                    (
                                        "Game ",
                                        format(game_number, ","),
                                        " in PGN is one of ignored games",
                                    )
                                )
                            )
                    continue
            # Do a full parse of the game score if an error is found, to
            # consume the rest of game and wrap it in a '{ ... }' comment,
            # so later display of the stored record will succeed.
            # Later import stages, which do the full parse so the position
            # and piece location indicies can be generated, will ignore
            # this record.
            # Attribute collected_game is re-bound so note anything needed
            # from the original object.
            game_offset = collected_game.game_offset
            if collected_game.is_tag_roster_valid():
                value.gamesource = None
            else:
                value.gamesource = sourcename
                pgn_text = [
                    value.pgn_mark_comment_in_error(text)
                    for text in collected_game.pgn_text
                ]
                pgn_text.insert(
                    len(collected_game.pgn_tags),
                    START_COMMENT + ERROR_START_COMMENT,
                )
                if pgn_text[-1].strip() not in GAME_TERMINATION_MARKERS:
                    pgn_text.append(ESCAPE_END_COMMENT + END_COMMENT)
                    pgn_text.append(
                        "\n{'*' added to mitigate effect of earlier error}"
                    )
                    pgn_text.append(" *")
                else:
                    pgn_text.insert(-1, ESCAPE_END_COMMENT + END_COMMENT)
                collected_game = next(
                    ChessDBvaluePGNIdentity().read_games("".join(pgn_text))
                )
            copy_number += 1
            self.key.recno = None
            value.collected_game = collected_game
            self.put_record(self.database, GAMES_FILE_DEF)
            if copy_number % db_segment_size == 0:
                database.commit()
                database.deferred_update_housekeeping()
                database.start_transaction()
                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Game ",
                                format(game_number, ","),
                                " to character ",
                                format(game_offset, ","),
                                " in PGN is record ",
                                format(self.key.recno, ","),
                            )
                        )
                    )
        if reporter is not None:
            reporter.append_text_only("")
            if file_game_numbers:
                reporter.append_text(
                    "".join(
                        (
                            format(copy_number, ","),
                            " games, missing from database, read from ",
                            sourcename,
                        )
                    )
                )
            elif copy_number and collected_game is not None:
                reporter.append_text(
                    "".join(
                        (
                            format(copy_number, ","),
                            " games, to character ",
                            format(game_offset, ","),
                            " in PGN, read from ",
                            sourcename,
                        )
                    )
                )
            else:
                reporter.append_text(
                    "".join(
                        (
                            format(copy_number, ","),
                            " games read from ",
                            sourcename,
                        )
                    )
                )
            reporter.append_text_only("")
        return True


class ChessDBvaluePosition(PGN, _GameLoadPack):
    """Chess game data with references to indicies to be applied."""

    def __init__(self, game_class=GameUpdatePosition):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)
        self.gamesource = None

    def pack_detail(self, index):
        """Add position detail to index or mark as error."""
        if self.do_full_indexing():
            index[POSITIONS_FIELD_DEF] = self.collected_game.positionkeys
        else:
            index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Detected PGN errors are wrapped in a comment starting 'Error: ' so
        method is_pgn_valid() is not used to decide what indexing to do.

        """
        return self.gamesource is None

    # Copied from core.pgn._Game class.
    def pgn_mark_comment_in_error(self, comment):
        """Return comment with '}' replaced by a presumed unlikely sequence.

        One possibility is to wrap the error in a '{...}' comment.  The '}'
        token in any wrapped commment would end the comment wrapping the error
        prematurely, so replace with HIDE_END_COMMENT.

        """
        return comment.replace(END_COMMENT, HIDE_END_COMMENT)


class ChessDBrecordGameTransposition(Record):
    """Customise chess game record to index games by positions."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvaluePosition
    ):
        """Customise Record with chess database key and value classes."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)

    def index_positions(
        self, database, index_games, reporter=None, quit_event=None
    ):
        """Update database games with position indicies."""
        self.set_database(database)
        db_segment_size = SegmentSize.db_segment_size
        index_key = database.encode_record_selector(POSITIONS_FIELD_DEF)
        value = self.value
        old_segment = None
        cursor = index_games.create_recordsetbase_cursor(internalcursor=True)
        while True:
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Index positions stopped.")
                return False
            current_record = cursor.next()
            if current_record is None:
                # At this point do the final segement index updates.
                # self.srindex has the indicies to update because these do
                # not change from one record to another.
                if self.srindex is not None and self.key.recno is not None:
                    current_segment = self.key.recno // db_segment_size
                    for secondary in self.srindex:
                        database.sort_and_write(
                            GAMES_FILE_DEF, secondary, current_segment
                        )
                        database.merge(GAMES_FILE_DEF, secondary)
                if old_segment is not None:
                    database.unfile_records_under(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        index_key,
                    )
                break
            self.load_record(current_record)
            current_segment = self.key.recno // db_segment_size
            if current_segment != old_segment:
                if old_segment is not None:
                    old_records = database.recordlist_record_number_range(
                        GAMES_FILE_DEF,
                        keystart=old_segment * db_segment_size,
                        keyend=(old_segment + 1) * db_segment_size - 1,
                    )
                    not_indexed_yet = database.recordlist_key(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        key=index_key,
                    )
                    not_indexed_yet.remove_recordset(old_records)
                    database.file_records_under(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        not_indexed_yet,
                        index_key,
                    )
                    del not_indexed_yet
                    del old_records
                    database.commit()
                    database.deferred_update_housekeeping()
                    database.start_transaction()
                    reporter.append_text(
                        "".join(
                            (
                                "Games before ",
                                format(current_segment * db_segment_size, ","),
                                " indexed by positions.",
                            )
                        )
                    )
                old_segment = current_segment
            value.gamesource = None
            # Earlier import stages verified the syntax of movetext but did
            # not verify the movetext represented legal moves on the board.
            # The absence of movetext is fine, as is movetext which is just
            # comments or other stuff which does not signify a move to be
            # applied to the board.
            # If movetext which signifies a move to be applied to the board
            # is present, the first such element must signify a legal move.
            # Problems occur later when displaying games if this is not so.
            if value.collected_game.state is not None:
                # Re-index as an error.
                pgn_text = [
                    value.pgn_mark_comment_in_error(text)
                    for text in value.collected_game.pgn_text
                ]
                pgn_text.insert(
                    len(value.collected_game.pgn_tags),
                    START_COMMENT + ERROR_START_COMMENT,
                )
                if pgn_text[-1].strip() not in GAME_TERMINATION_MARKERS:
                    pgn_text.append(ESCAPE_END_COMMENT + END_COMMENT)
                    pgn_text.append(
                        "\n{'*' added to mitigate effect of earlier error}"
                    )
                    pgn_text.append(" *")
                else:
                    pgn_text.insert(-1, ESCAPE_END_COMMENT + END_COMMENT)
                new_instance = self.__class__(
                    keyclass=self.key.__class__,
                    valueclass=ChessDBvaluePGNIdentity,
                )
                new_instance.load_record(current_record)
                new_instance.set_database(database)
                new_instance.value.gamesource = value.reference[FILE]
                collected_game = next(
                    new_instance.value.read_games("".join(pgn_text))
                )
                new_instance.value.collected_game = collected_game
                new_instance.value.collected_game.pgn_tags.clear()
                new_instance.value.collected_game.positionkeys.clear()
                self.srkey = None
                self.edit_record(
                    database, GAMES_FILE_DEF, GAME_FIELD_DEF, new_instance
                )
                continue
            database.index_instance(GAMES_FILE_DEF, self)
        return True


class ChessDBvaluePieceLocation(PGN, _GameLoadPack):
    """Chess game data with references to indicies to be applied."""

    def __init__(self, game_class=GameUpdatePieceLocation):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)
        self.gamesource = None

    def pack_detail(self, index):
        """Add piece square detail to index or mark as error."""
        if self.do_full_indexing():
            game = self.collected_game
            index[PIECESQUARE_FIELD_DEF] = game.piecesquarekeys
        else:
            index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Detected PGN errors are wrapped in a comment starting 'Error: ' so
        method is_pgn_valid() is not used to decide what indexing to do.

        """
        return self.gamesource is None


class ChessDBrecordGamePieceLocation(Record):
    """Customise chess game record to index games by piece locations."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvaluePieceLocation
    ):
        """Customise Record with chess database key and value classes."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)

    def index_piece_locations(
        self, database, index_games, reporter=None, quit_event=None
    ):
        """Update database games with piece location indicies."""
        self.set_database(database)
        db_segment_size = SegmentSize.db_segment_size
        index_key = database.encode_record_selector(PIECESQUARE_FIELD_DEF)
        value = self.value
        old_segment = None
        cursor = index_games.create_recordsetbase_cursor(internalcursor=True)
        while True:
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Index piece movement stopped.")
                return False
            current_record = cursor.next()
            if current_record is None:
                # At this point do the final segement index updates.
                # self.srindex has the indicies to update because these do
                # not change from one record to another.
                if self.srindex is not None and self.key.recno is not None:
                    current_segment = self.key.recno // db_segment_size
                    for secondary in self.srindex:
                        database.sort_and_write(
                            GAMES_FILE_DEF, secondary, current_segment
                        )
                        database.merge(GAMES_FILE_DEF, secondary)
                if old_segment is not None:
                    database.unfile_records_under(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        index_key,
                    )
                break
            self.load_record(current_record)
            current_segment = self.key.recno // db_segment_size
            if current_segment != old_segment:
                if old_segment is not None:
                    old_records = database.recordlist_record_number_range(
                        GAMES_FILE_DEF,
                        keystart=old_segment * db_segment_size,
                        keyend=(old_segment + 1) * db_segment_size - 1,
                    )
                    not_indexed_yet = database.recordlist_key(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        key=index_key,
                    )
                    not_indexed_yet.remove_recordset(old_records)
                    database.file_records_under(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        not_indexed_yet,
                        index_key,
                    )
                    del not_indexed_yet
                    del old_records
                    database.commit()
                    database.deferred_update_housekeeping()
                    database.start_transaction()
                    reporter.append_text(
                        "".join(
                            (
                                "Games before ",
                                format(current_segment * db_segment_size, ","),
                                " indexed by piece movement.",
                            )
                        )
                    )
                old_segment = current_segment
            value.gamesource = None
            database.index_instance(GAMES_FILE_DEF, self)
        return True


class ChessDBvaluePGNTags(PGNTagPair, _GameLoadPack):
    """Chess game data with references to indicies to be applied."""

    def __init__(self, game_class=GameMoveText):
        """Delegate to superclass with game_class argument."""
        super().__init__(game_class=game_class)
        self.gamesource = None

    def pack_detail(self, index):
        """Add PGN tags to index or mark as error."""
        if self.do_full_indexing():
            # index[PGNFILE_FIELD_DEF] = [self.reference[FILE]]
            # index[NUMBER_FIELD_DEF] = [self.reference[GAME]]
            _pack_tags_into_index(self.collected_game.pgn_tags, index)
            # index[IMPORT_FIELD_DEF] = [
            #    IMPORT_FIELD_DEF,
            # ]
        else:
            index[PGN_ERROR_FIELD_DEF] = [self.reference[FILE]]

    def do_full_indexing(self):
        """Return True if full indexing is to be done.

        Detected PGN errors are wrapped in a comment starting 'Error: ' so
        method is_pgn_valid() is not used to decide what indexing to do.

        """
        return self.gamesource is None


class ChessDBrecordGamePGNTags(Record):
    """Customise chess game record to index games by PGN tags."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvaluePGNTags
    ):
        """Customise Record with chess database key and value classes."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)

    def index_pgn_tags(
        self, database, index_games, reporter=None, quit_event=None
    ):
        """Update database games with PGN tag indicies."""
        self.set_database(database)
        db_segment_size = SegmentSize.db_segment_size
        value = self.value
        old_segment = None
        cursor = index_games.create_recordsetbase_cursor(internalcursor=True)
        while True:
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Index PGN Tags stopped.")
                return False
            current_record = cursor.next()
            if current_record is None:
                # At this point do the final segement index updates.
                # self.srindex has the indicies to update because these do
                # not change from one record to another.
                if self.srindex is not None and self.key.recno is not None:
                    current_segment = self.key.recno // db_segment_size
                    for secondary in self.srindex:
                        database.sort_and_write(
                            GAMES_FILE_DEF, secondary, current_segment
                        )
                        database.merge(GAMES_FILE_DEF, secondary)
                if old_segment is not None:
                    database.unfile_records_under(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        database.encode_record_selector(IMPORT_FIELD_DEF),
                    )
                break
            self.load_record(current_record)
            current_segment = self.key.recno // db_segment_size
            if current_segment != old_segment:
                if old_segment is not None:
                    old_records = database.recordlist_record_number_range(
                        GAMES_FILE_DEF,
                        keystart=old_segment * db_segment_size,
                        keyend=(old_segment + 1) * db_segment_size - 1,
                    )
                    not_indexed_yet = database.recordlist_key(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        key=database.encode_record_selector(IMPORT_FIELD_DEF),
                    )
                    not_indexed_yet.remove_recordset(old_records)
                    database.file_records_under(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        not_indexed_yet,
                        database.encode_record_selector(IMPORT_FIELD_DEF),
                    )
                    del not_indexed_yet
                    del old_records
                    database.commit()
                    database.deferred_update_housekeeping()
                    database.start_transaction()
                    reporter.append_text(
                        "".join(
                            (
                                "Games before ",
                                format(current_segment * db_segment_size, ","),
                                " indexed by selected PGN tags.",
                            )
                        )
                    )
                old_segment = current_segment
            value.gamesource = None
            if not value.collected_game.is_tag_roster_valid():
                # Re-index as an error.
                new_instance = self.__class__(
                    keyclass=self.key.__class__,
                    valueclass=self.value.__class__,
                )
                new_instance.load_record(current_record)
                new_instance.set_database(database)
                new_instance.value.gamesource = value.reference[FILE]
                new_instance.value.collected_game.pgn_tags.clear()
                self.srkey = None
                self.edit_record(
                    database, GAMES_FILE_DEF, GAME_FIELD_DEF, new_instance
                )
                continue
            database.index_instance(GAMES_FILE_DEF, self)
        return True


class ChessDBvalueCQLScan(PGNMoveText, _GameLoadPack):
    """Chess game data with references to indicies to be applied."""

    def __init__(self, game_class=GameMoveText):
        """Delegate to superclass with game_class argument."""
        super().__init__(game_class=game_class)
        self.gamesource = None


class ChessDBrecordGameCQLScan(Record):
    """Customise chess game record to index games by PGN tags."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvalueCQLScan
    ):
        """Customise Record with chess database key and value classes."""
        super().__init__(keyclass=keyclass, valueclass=valueclass)


class ChessDBkeyPartial(KeyData):
    """Primary key of CQL query record."""


class ChessDBvaluePartial(CQLStatement, Value):
    """Partial position data."""

    def __eq__(self, other):
        """Return (self == other).  Attributes are compared explicitly."""
        if self.get_name_statement_text() != other.get_name_statement_text():
            return False
        return True

    def __ne__(self, other):
        """Return (self != other).  Attributes are compared explicitly."""
        if self.get_name_statement_text() == other.get_name_statement_text():
            return False
        return True

    def load(self, value):
        """Set CQL query from value."""
        self.load_statement(literal_eval(value))

    def pack_value(self):
        """Return CQL query value."""
        return repr(self.get_name_statement_text())

    def pack(self):
        """Extend, return CQL query record and index data."""
        value = super().pack()
        index = value[1]
        index[QUERY_NAME_FIELD_DEF] = [self.get_name_text()]
        return value


class ChessDBrecordPartial(Record):
    """Partial position record."""

    def __init__(self):
        """Extend as a CQL query record."""
        super().__init__(ChessDBkeyPartial, ChessDBvaluePartial)

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The CQL query name is held in an attribute which is not named
        for the field where it exists in the database.

        """
        if datasource.dbname == QUERY_NAME_FIELD_DEF:
            return [(self.value.get_name_text(), self.key.pack())]
        return super().get_keys(datasource=datasource, partial=partial)

    def load_value(self, value):
        """Load self.value from value which is repr(<data>).

        Set database in self.value for query processing then delegate value
        processing to superclass.

        """
        self.value.set_database(self.database)
        self.value.dbset = GAMES_FILE_DEF
        super().load_value(value)


# Not quite sure what customization needed yet
class ChessDBvalueRepertoire(PGN, Value):
    """Repertoire data using custom non-standard tags in PGN format."""

    def __init__(self, game_class=GameRepertoireDisplayMoves):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)
        self.collected_game = None

    def load(self, value):
        """Get game from value.

        If value is from a database record it will be a str and is the
        required argument to read_games().

        If value is from a user interface object it will be a list and
        the required argument to read_games() will be
        'literal_eval(<list>[0])'.

        """
        lev = literal_eval(value)
        if isinstance(lev, list):
            lev = literal_eval(lev[0])
        self.collected_game = next(self.read_games(lev))


# Not quite sure what customization needed yet
class ChessDBvalueRepertoireTags(ChessDBvalueRepertoire):
    """Repertoire data using custom non-standard tags in PGN format."""

    def __init__(self):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=GameRepertoireTags)


# Not quite sure what customization needed yet
# Changed superclass from ChessDBvaluePGN to ChessDBvalueRepertoire and
# copied ChessDBvaluePGN methods, pre-ChessDBvaluePGN changes, to
# to ChessDBvalueRepertoireUpdate where missing otherwise.
class ChessDBvalueRepertoireUpdate(ChessDBvalueRepertoire):
    """Repertoire data using custom non-standard tags in PGN format."""

    # Some code, which should no longer be shared between repertoire and
    # game classes, expects value classes to have a reference attribute.
    reference = None

    def __init__(self):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=GameRepertoireUpdate)
        self.gamesource = None

    @staticmethod
    def encode_move_number(key):
        """Return base 256 string for integer, left-end most significant."""
        return key.to_bytes(2, byteorder="big")

    def pack(self):
        """Return PGN text and indexes for game."""
        value = super().pack()
        index = value[1]
        tags = self.collected_game.pgn_tags
        if self.collected_game.is_pgn_valid():
            index[TAG_OPENING] = [tags[TAG_OPENING]]
        elif tags[TAG_OPENING]:
            index[TAG_OPENING] = [tags[TAG_OPENING]]
        else:
            index[TAG_OPENING] = ["/"]
        return value

    def pack_value(self):
        """Return PGN text for game."""
        return repr("".join(self.collected_game.pgn_text))


# Not quite sure what customization needed yet
class ChessDBrecordRepertoire(ChessDBrecordGame):
    """Repertoire record customised for exporting repertoire information."""

    def __init__(self):
        """Extend with move number encode and decode methods."""
        # Skip the immediate superclass __init__ to fix key and value classes
        # pylint bad-super-call message given.
        # pylint super-with-arguments message given.
        super(ChessDBrecordGame, self).__init__(
            ChessDBkeyGame, ChessDBvalueRepertoire
        )


# Not quite sure what customization needed yet
class ChessDBrecordRepertoireTags(ChessDBrecordGameTags):
    """Repertoire record customised to display repertoire tag information."""

    def __init__(self):
        """Extend with move number encode and decode methods."""
        # Skip the immediate superclass __init__ to fix key and value classes
        # pylint bad-super-call message given.
        # pylint super-with-arguments message given.
        super(ChessDBrecordGameTags, self).__init__(
            ChessDBkeyGame, ChessDBvalueRepertoireTags
        )


# Not quite sure what customization needed yet
class ChessDBrecordRepertoireUpdate(ChessDBrecordGameUpdate):
    """Repertoire record customized for editing repertoire records."""

    def __init__(
        self, keyclass=ChessDBkeyGame, valueclass=ChessDBvalueRepertoireUpdate
    ):
        """Extend with move number encode and decode methods."""
        # Skip the immediate superclass __init__ to fix key and value classes
        # pylint bad-super-call message given.
        # pylint super-with-arguments message given.
        # Before introduction of reference to PGN file and game number within
        # file it was reasonable to have Repertoire inherit from Game but
        # that is not reasonable now.  The first actual problem which needs
        # fixing is having to ignore the valueclass argument which may pass
        # in a class relevant to games but wrong for repertoires.  The
        # problem arises from all supported database engines but Symas LMDB
        # supporting zero length bytestring keys.
        valueclass = ChessDBvalueRepertoireUpdate
        super(ChessDBrecordGameUpdate, self).__init__(
            keyclass=keyclass, valueclass=valueclass
        )

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The keys for the secondary databases in a Database instance are
        embedded in, or derived from, the PGN string for the game.  All
        except the positions are held in self.value.collected_game.pgn_tags.
        Multiple position keys can arise becuse all repetitions of a
        position are of interest.  The partial argument is used to select
        the relevant keys.  The position is in partial and the keys will
        differ in the move number.

        """
        dbname = datasource.dbname
        if dbname == REPERTOIRE_FILE_DEF:
            return [(self.key.recno, self.srvalue)]
        if dbname in self.value.collected_game.pgn_tags:
            return [
                (self.value.collected_game.pgn_tags[dbname], self.key.pack())
            ]
        return []


class ChessDBvalueAnalysis(Analysis, Value):
    """Chess engine analysis data for a position."""

    def __init__(self):
        """Delegate."""
        super().__init__()

    def pack(self):
        """Extend, return analysis record and index data."""
        value = super().pack()
        index = value[1]
        index[VARIATION_FIELD_DEF] = [self.position]
        index[ENGINE_FIELD_DEF] = list(self.scale)
        return value


class ChessDBrecordAnalysis(Record):
    """Chess game record customised for chess engine analysis data.

    No index values are derived from PGN move text, so there is no advantage in
    separate classes for display and update.  The PGN FEN tag provides the only
    PGN related index value used.

    """

    def __init__(self):
        """Delegate using ChessDBkeyGame and ChessDBvalueAnalysis classes."""
        super().__init__(KeyData, ChessDBvalueAnalysis)


class ChessDBkeyQuery(KeyData):
    """Primary key of game selection rule record."""


class ChessDBvalueQuery(QueryStatement, Value):
    """Game selection rule data."""

    def __eq__(self, other):
        """Return (self == other).  Attributes are compared explicitly."""
        if (
            self.get_name_query_statement_text()
            != other.get_name_query_statement_text()
        ):
            return False
        return True

    def __ne__(self, other):
        """Return (self != other).  Attributes are compared explicitly."""
        if (
            self.get_name_query_statement_text()
            == other.get_name_query_statement_text()
        ):
            return False
        return True

    def load(self, value):
        """Set game selection rule from value."""
        self.process_query_statement(literal_eval(value))

    def pack_value(self):
        """Return gameselection rule value."""
        return repr(self.get_name_query_statement_text())

    def pack(self):
        """Extend, return game selection rule record and index data."""
        value = super().pack()
        index = value[1]
        index[RULE_FIELD_DEF] = [self.get_name_text()]
        return value


class ChessDBrecordQuery(Record):
    """Game selection rule record."""

    def __init__(self):
        """Extend as a game selection rule record."""
        super().__init__(ChessDBkeyQuery, ChessDBvalueQuery)

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The game selection rule name is held in an attribute which is not named
        for the field where it exists in the database.

        """
        if datasource.dbname == RULE_FIELD_DEF:
            return [(self.value.get_name_text(), self.key.pack())]
        return super().get_keys(datasource=datasource, partial=partial)

    def load_value(self, value):
        """Load self.value from value which is repr(<data>).

        Set database in self.value for query processing then delegate value
        processing to superclass.

        """
        self.value.set_database(self.database)
        self.value.dbset = GAMES_FILE_DEF
        super().load_value(value)


class ChessDBkeyEngine(KeyData):
    """Primary key of chess engine record."""


class ChessDBvalueEngine(Engine, Value):
    """Game chess engine data."""

    def pack(self):
        """Extend, return chess engine record and index data."""
        value = super().pack()
        index = value[1]
        index[COMMAND_FIELD_DEF] = [self.get_name_text()]
        return value


class ChessDBrecordEngine(Record):
    """Chess engine record."""

    def __init__(self):
        """Extend as a chess engine record."""
        super().__init__(ChessDBkeyEngine, ChessDBvalueEngine)
