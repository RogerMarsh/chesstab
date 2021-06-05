# chessrecord.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definitions for chess game database.

The ...Game... classes differ in the PGN parser used as a superclass of the
...valueGame... class.  These generate different combinations of the available
data structures from the game score for the various display and update uses.
The ...Update classes allow editing of a, possibly incomplete, game score.

"""
from ast import literal_eval
import re

from solentware_base.core.record import KeyData, Value, ValueText, Record
from solentware_base.core.segmentsize import SegmentSize

from pgn_read.core.parser import PGN
from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
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
)
from .cqlstatement import CQLStatement
from .filespec import (
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
)
from .analysis import Analysis
from .querystatement import QueryStatement, re_normalize_player_name
from .engine import Engine

PLAYER_NAME_TAGS = frozenset((TAG_WHITE, TAG_BLACK))


class ChessRecordError(Exception):
    pass


class ChessDBkeyGame(KeyData):

    """Primary key of chess game."""

    def __eq__(self, other):
        """Return (self == other).  Attributes are compared explicitly."""
        try:
            return self.recno == other.recno
        except:
            return False

    def __ne__(self, other):
        """Return (self != other).  Attributes are compared explicitly."""
        try:
            return self.recno != other.recno
        except:
            return True


class ChessDBvaluePGN(Value):

    """Methods common to all chess PGN data classes."""

    def __init__(self):
        super().__init__()
        self.collected_game = None

    @staticmethod
    def encode_move_number(key):
        """Return base 256 string for integer with left-end most significant."""
        return key.to_bytes(2, byteorder="big")

    def load(self, value):
        """Get game from value."""
        self.collected_game = next(self.read_games(literal_eval(value)))

    def pack_value(self):
        """Return PGN text for game."""
        return repr("".join(self.collected_game._text))


class ChessDBvalueGame(PGN, ChessDBvaluePGN):

    """Chess game data.

    Data is indexed by PGN Seven Tag Roster tags.

    """

    def __init__(self, game_class=GameDisplayMoves):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=game_class)

    def pack(self):
        """Return PGN text and indexes for game."""
        v = super(ChessDBvalueGame, self).pack()
        index = v[1]
        tags = self.collected_game._tags
        for field in tags:
            if field in PLAYER_NAME_TAGS:

                # PGN specification states colon is used to separate player
                # names in consultation games.
                index[field] = [
                    " ".join(re_normalize_player_name.findall(tf))
                    for tf in tags[field].split(":")
                ]

            elif field in SEVEN_TAG_ROSTER:
                index[field] = [tags[field]]
        if TAG_DATE in tags:
            index[PGN_DATE_FIELD_DEF] = [
                tags[TAG_DATE].replace(*SPECIAL_TAG_DATE)
            ]
        return v


class ChessDBrecordGame(Record):

    """Chess game record customised for displaying the game score and tags."""

    def __init__(self):
        """Extend with move number encode and decode methods"""
        super(ChessDBrecordGame, self).__init__(
            ChessDBkeyGame, ChessDBvalueGame
        )

    def clone(self):
        """Return copy of ChessDBrecordGame instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGame.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super(ChessDBrecordGame, self).clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string with left-end most significant."""
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

        The keys for the secondary databases in a ChessDatabase instance are
        embedded in, or derived from, the PGN string for the game.  All
        except the positions are held in self.value.collected_game._tags.
        Multiple position keys can arise becuse all repetitions of a
        position are of interest.  The partial argument is used to select
        the relevant keys.  The position is in partial and the keys will
        differ in the move number.

        """
        dbname = datasource.dbname
        if dbname != POSITIONS_FIELD_DEF:
            if dbname == GAMES_FILE_DEF:
                return [(self.key.recno, self.srvalue)]
            elif dbname in self.value.collected_game._tags:
                return [
                    (self.value.collected_game._tags[dbname], self.key.pack())
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
        """Extend with move number encode and decode methods"""
        super(ChessDBrecordGameText, self).__init__(ChessDBkeyGame, ValueText)

    def clone(self):
        """Return copy of ChessDBrecordGameText instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGameText.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super(ChessDBrecordGameText, self).clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string with left-end most significant."""
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
        return self.collected_game._tags.get(fieldname, None)

    # def get_field_values(self, fieldname):
    #    """Return tuple of field values for fieldname.

    #    Added to support Find and Where classes.

    #    """
    #    return self.get_field_value(fieldname),

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
            self.collected_game = next(
                self.read_games("{" + literal_eval(value) + "}*")
            )


class ChessDBrecordGameTags(Record):

    """Chess game record customised for displaying tag information for a game."""

    def __init__(self):
        """Extend with move number encode and decode methods"""
        super(ChessDBrecordGameTags, self).__init__(
            ChessDBkeyGame, ChessDBvalueGameTags
        )


class ChessDBrecordGamePosition(Record):

    """Chess game record customised for displaying the game score only.

    Much of the game structure to be represented in the row display is held
    in the Tkinter.Text object created for display.  Thus the processing of
    the record data is delegated to a PositionScore instance created when
    filling the grid.

    """

    def __init__(self):
        """Extend with move number encode and decode methods"""
        super(ChessDBrecordGamePosition, self).__init__(
            ChessDBkeyGame, ValueText
        )

    def clone(self):
        """Return copy of ChessDBrecordGamePosition instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGamePosition.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super(ChessDBrecordGamePosition, self).clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string with left-end most significant."""
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


# An alternative is to put this in .core.pgn as 'class _Game(Game) and base
# the other classes on _Game rather than Game.  Done here because the only
# place errors which need hiding should occur is when importing games to, or
# updating games on, the database.
class _GameUpdate(GameUpdate):
    """Override the PGN error notification and recovery methods.

    Errors detected in PGN movetext are hidden by wrapping all tokens to end
    of variation, which may be rest of game if error is in main line, in a
    comment which starts and ends with a presumed unlikely character sequence.
    The '}' in any '{}' comments which happen to get wrapped a changed to a
    distinct presumed unlikely character sequence so the wrapped '}' tokens do
    not terminate the wrapping comment.

    """

    def pgn_error_notification(self):
        """Insert error '{' before movetext token which causes PGN error."""
        if self._movetext_offset is not None:
            self._text.append(START_COMMENT + ERROR_START_COMMENT)

    def pgn_error_recovery(self):
        """Insert error '}' before token which ends the scope of a PGN error.

        This token will be a ')' or one of the game termination markers.

        """
        if self._movetext_offset is not None:
            self._text.append(ESCAPE_END_COMMENT + END_COMMENT)

    def pgn_mark_comment_in_error(self, comment):
        """Return comment with '}' replaced by a presumed unlikely sequence.

        One possibility is to wrap the error in a '{...}' comment.  The '}'
        token in any wrapped commment would end the comment wrapping the error
        prematurely, so replace with HIDE_END_COMMENT.

        """
        return comment.replace(END_COMMENT, HIDE_END_COMMENT)


class ChessDBvaluePGNUpdate(PGN, ChessDBvaluePGN):

    """Chess game data with position, piece location, and PGN Tag, indexes."""

    # Replaces ChessDBvaluePGNUpdate and ChessDBvalueGameImport which had been
    # identical for a considerable time.
    # Decided that PGNUpdate should remain in pgn.core.parser because that code
    # generates data while this code updates a database.
    # Now moved to .core.pgn.GameUpdate.
    # ChessDBvalueGameImport had this comment:
    # Implication of original is encode_move_number not supported and load in
    # ChessDBvaluePGN superclass is used.

    def __init__(self):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=_GameUpdate)
        self.gamesource = None

    # Perhaps ChessDBvaluePGNUpdate should follow example of ChessDBvalueGame
    # in handling Seven Tag Roster, and just use 'try ... except ...' for
    # bulk imports in ChessDBrecordGameImport, where Seven Tag Roster should
    # be present.  This would need a subclass of ChessDBvaluePGNUpdate to hold
    # the version of pack() below.
    def pack(self):
        """Return PGN text and indexes for game."""
        v = super().pack()
        index = v[1]
        cg = self.collected_game
        if self.do_full_indexing():
            tags = cg._tags
            for field in SEVEN_TAG_ROSTER:
                if field in PLAYER_NAME_TAGS:

                    # PGN specification states colon is used to separate player
                    # names in consultation games.
                    try:
                        index[field] = [
                            " ".join(re_normalize_player_name.findall(tf))
                            for tf in tags[field].split(":")
                        ]
                    except KeyError:
                        if field in tags:
                            raise

                else:
                    try:
                        index[field] = [tags[field]]
                    except KeyError:
                        if field in tags:
                            raise
            index[POSITIONS_FIELD_DEF] = cg.positionkeys
            index[PIECESQUAREMOVE_FIELD_DEF] = cg.piecesquaremovekeys
            index[PIECEMOVE_FIELD_DEF] = cg.piecemovekeys
            index[SQUAREMOVE_FIELD_DEF] = cg.squaremovekeys
            try:
                index[PGN_DATE_FIELD_DEF] = [
                    tags[TAG_DATE].replace(*SPECIAL_TAG_DATE)
                ]
            except KeyError:
                if TAG_DATE in tags:
                    raise
        else:
            index[SOURCE_FIELD_DEF] = [self.gamesource]
        return v

    def set_game_source(self, source):
        """Set the index value to use if full indexing is not to be done."""
        self.gamesource = source

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
            self.collected_game._text
        )


class ChessDBrecordGameUpdate(Record):

    """Chess game record customized for editing database records.

    Used to edit or insert a single record by typing in a widget.

    """

    def __init__(self):
        """Extend with move number encode and decode methods"""
        super(ChessDBrecordGameUpdate, self).__init__(
            ChessDBkeyGame, ChessDBvaluePGNUpdate
        )

    def clone(self):
        """Return copy of ChessDBrecordGameUpdate instance.

        The bound method attributes are dealt with explicitly and the rest
        are handled by super(...).clone().  (Hope that DPT CR LF restrictions
        will be removed at which point the bound method attributes will not
        be needed.  Then ChessDBrecordGameUpdate.clone() can be deleted.)

        """
        # are conditions for deleting this method in place?
        clone = super(ChessDBrecordGameUpdate, self).clone()
        return clone

    @staticmethod
    def decode_move_number(skey):
        """Return integer from base 256 string with left-end most significant."""
        return int.from_bytes(skey, byteorder="big")

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The keys for the secondary databases in a ChessDatabase instance are
        embedded in, or derived from, the PGN string for the game.  All
        except the positions are held in self.value.collected_game._tags.
        Multiple position keys can arise becuse all repetitions of a
        position are of interest.  The partial argument is used to select
        the relevant keys.  The position is in partial and the keys will
        differ in the move number.

        """
        dbname = datasource.dbname
        if dbname != POSITIONS_FIELD_DEF:
            if dbname == GAMES_FILE_DEF:
                return [(self.key.recno, self.srvalue)]
            elif dbname in self.value.collected_game._tags:
                return [
                    (self.value.collected_game._tags[dbname], self.key.pack())
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
        """Extend to set source for game if necessary."""
        super(ChessDBrecordGameUpdate, self).load_instance(
            database, dbset, dbname, record
        )

        # Never called because attribute is not bound anywhere and no
        # exceptions are seen ever.
        # Until ..tools.chesstab-4-1-1_castling-option-correction written, and
        # following code commented.  I assume the idea made sense once!
        # Might as well let superclass method be used directly.
        # if self.value.callbacktried:
        #    pass
        # elif self.value.callbacktried == None:
        #    pass
        # elif not self.value.callbacktried:
        #    self.value.set_game_source(record[0])


class ChessDBrecordGameImport(Record):

    """Chess game record customised for importing games from PGN files.

    Used to import multiple records from a PGN file.

    """

    def __init__(self):
        """Customise Record with chess database import key and value classes"""
        super(ChessDBrecordGameImport, self).__init__(
            ChessDBkeyGame, ChessDBvaluePGNUpdate
        )

    def import_pgn(self, database, source, sourcename, reporter=None):
        """Update database with games read from source."""
        self.set_database(database)
        # self.value.set_game_source(sourcename)
        if reporter is not None:
            reporter("Extracting games from " + sourcename)
        ddup = database.deferred_update_points
        db_segment_size = SegmentSize.db_segment_size
        value = self.value
        count = 0
        for collected_game in value.read_games(source):
            value.set_game_source(
                sourcename if not collected_game.is_pgn_valid() else None
            )
            self.key.recno = None
            value.collected_game = collected_game
            self.put_record(self.database, GAMES_FILE_DEF)
            if reporter is not None:
                if not count:
                    base = self.key.recno - self.key.recno % db_segment_size
                count += 1
                if self.key.recno % db_segment_size in ddup:
                    reporter(
                        " ".join(
                            (
                                "Game",
                                str(count),
                                "stored as record",
                                str(self.key.recno),
                                "offset",
                                str(self.key.recno - base),
                            )
                        )
                    )
                    database.deferred_update_housekeeping()
        if reporter is not None:
            reporter("Extraction from " + sourcename + " done")
            reporter("", timestamp=False)


class ChessDBkeyPartial(KeyData):

    """Primary key of partial position record."""


class ChessDBvaluePartial(CQLStatement, Value):

    """Partial position data."""

    def __init__(self):
        super(ChessDBvaluePartial, self).__init__()

    def __eq__(self, other):
        """Return (self == other).  Attributes are compared explicitly."""
        try:
            if (
                self.get_name_statement_text()
                != other.get_name_statement_text()
            ):
                return False
            else:
                return True
        except:
            return False

    def __ne__(self, other):
        """Return (self != other).  Attributes are compared explicitly."""
        try:
            if (
                self.get_name_statement_text()
                == other.get_name_statement_text()
            ):
                return False
            else:
                return True
        except:
            return True

    def load(self, value):
        """Set partial position from value"""
        self.process_statement(literal_eval(value))

    def pack_value(self):
        """Return partial position value"""
        return repr(self.get_name_statement_text())

    def pack(self):
        """Extend, return partial position record and index data."""
        v = super().pack()
        index = v[1]
        index[PARTIALPOSITION_NAME_FIELD_DEF] = [self.get_name_text()]
        return v


class ChessDBrecordPartial(Record):

    """Partial position record."""

    def __init__(self):
        """Extend as a partial position record."""
        super(ChessDBrecordPartial, self).__init__(
            ChessDBkeyPartial, ChessDBvaluePartial
        )

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The partial position name is held in an attribute which is not named
        for the field where it exists in the database.

        """
        if datasource.dbname == PARTIALPOSITION_NAME_FIELD_DEF:
            return [(self.value.get_name_text(), self.key.pack())]
        else:
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
        """Get game from value."""
        self.collected_game = next(self.read_games(literal_eval(value)))


# Not quite sure what customization needed yet
class ChessDBvalueRepertoireTags(ChessDBvalueRepertoire):

    """Repertoire data using custom non-standard tags in PGN format."""

    def __init__(self):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=GameRepertoireTags)


# Not quite sure what customization needed yet
class ChessDBvalueRepertoireUpdate(PGN, ChessDBvaluePGN):

    """Repertoire data using custom non-standard tags in PGN format."""

    def __init__(self):
        """Extend with game source and move number encoder placeholders."""
        super().__init__(game_class=GameRepertoireUpdate)
        self.gamesource = None

    def pack(self):
        """Return PGN text and indexes for game."""
        v = super(ChessDBvalueRepertoireUpdate, self).pack()
        index = v[1]
        tags = self.collected_game._tags
        if self.collected_game.is_pgn_valid():
            index[TAG_OPENING] = [tags[TAG_OPENING]]
        elif tags[TAG_OPENING]:
            index[TAG_OPENING] = [tags[TAG_OPENING]]
        else:
            index[TAG_OPENING] = [self.gamesource]
        return v

    def set_game_source(self, source):
        """Set game source (the PGN file name or '')"""
        self.gamesource = source


# Not quite sure what customization needed yet
class ChessDBrecordRepertoire(ChessDBrecordGame):

    """Repertoire record customised for exporting repertoire information."""

    def __init__(self):
        """Extend with move number encode and decode methods"""
        # Skip the immediate superclass __init__ to fix key and value classes
        super(ChessDBrecordGame, self).__init__(
            ChessDBkeyGame, ChessDBvalueRepertoire
        )


# Not quite sure what customization needed yet
class ChessDBrecordRepertoireTags(ChessDBrecordGameTags):

    """Repertoire record customised for displaying repertoire tag information."""

    def __init__(self):
        """Extend with move number encode and decode methods"""
        # Skip the immediate superclass __init__ to fix key and value classes
        super(ChessDBrecordGameTags, self).__init__(
            ChessDBkeyGame, ChessDBvalueRepertoireTags
        )


# Not quite sure what customization needed yet
class ChessDBrecordRepertoireUpdate(ChessDBrecordGameUpdate):

    """Repertoire record customized for editing repertoire records."""

    def __init__(self):
        """Extend with move number encode and decode methods"""
        # Skip the immediate superclass __init__ to fix key and value classes
        super(ChessDBrecordGameUpdate, self).__init__(
            ChessDBkeyGame, ChessDBvalueRepertoireUpdate
        )

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The keys for the secondary databases in a ChessDatabase instance are
        embedded in, or derived from, the PGN string for the game.  All
        except the positions are held in self.value.collected_game._tags.
        Multiple position keys can arise becuse all repetitions of a
        position are of interest.  The partial argument is used to select
        the relevant keys.  The position is in partial and the keys will
        differ in the move number.

        """
        dbname = datasource.dbname
        if dbname == REPERTOIRE_FILE_DEF:
            return [(self.key.recno, self.srvalue)]
        elif dbname in self.value.collected_game._tags:
            return [(self.value.collected_game._tags[dbname], self.key.pack())]
        else:
            return []


class ChessDBvalueAnalysis(Analysis, Value):

    """Chess engine analysis data for a position."""

    def __init__(self):
        """ """
        super().__init__()

    def pack(self):
        """Extend, return analysis record and index data."""
        v = super().pack()
        index = v[1]
        index[VARIATION_FIELD_DEF] = [self.position]
        index[ENGINE_FIELD_DEF] = [k for k in self.scale]
        return v


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

    def __init__(self):
        super(ChessDBvalueQuery, self).__init__()

    def __eq__(self, other):
        """Return (self == other).  Attributes are compared explicitly."""
        try:
            if (
                self.get_name_query_statement_text()
                != other.get_name_query_statement_text()
            ):
                return False
            else:
                return True
        except:
            return False

    def __ne__(self, other):
        """Return (self != other).  Attributes are compared explicitly."""
        try:
            if (
                self.get_name_query_statement_text()
                == other.get_name_query_statement_text()
            ):
                return False
            else:
                return True
        except:
            return True

    def load(self, value):
        """Set game selection rule from value"""
        self.process_query_statement(literal_eval(value))

    def pack_value(self):
        """Return gameselection rule value"""
        return repr(self.get_name_query_statement_text())

    def pack(self):
        """Extend, return game selection rule record and index data."""
        v = super().pack()
        index = v[1]
        index[RULE_FIELD_DEF] = [self.get_name_text()]
        return v


class ChessDBrecordQuery(Record):

    """Game selection rule record."""

    def __init__(self):
        """Extend as a game selection rule record."""
        super(ChessDBrecordQuery, self).__init__(
            ChessDBkeyQuery, ChessDBvalueQuery
        )

    def get_keys(self, datasource=None, partial=None):
        """Return list of (key, value) tuples.

        The game selection rule name is held in an attribute which is not named
        for the field where it exists in the database.

        """
        if datasource.dbname == RULE_FIELD_DEF:
            return [(self.value.get_name_text(), self.key.pack())]
        else:
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

    """Game selection rule data."""

    def __init__(self):
        super(ChessDBvalueEngine, self).__init__()

    def pack(self):
        """Extend, return game selection rule record and index data."""
        v = super().pack()
        index = v[1]
        index[COMMAND_FIELD_DEF] = [self.get_name_text()]
        return v


class ChessDBrecordEngine(Record):

    """Chess engine record."""

    def __init__(self):
        """Extend as a game selection rule record."""
        super(ChessDBrecordEngine, self).__init__(
            ChessDBkeyEngine, ChessDBvalueEngine
        )
