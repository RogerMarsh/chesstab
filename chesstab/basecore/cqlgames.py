# cqlgames.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Evaluate a ChessQL query.

Methods defined on all database interfaces are used exclusively.

"""
from ast import literal_eval

from solentware_base.core.find import Find
from solentware_base.core.where import (
    Where,
    EQ,
    OR,
    NOT,
    AND,
)

from chessql.core import cql
from chessql.core.cql import Token
from chessql.core.constants import (
    ALL_GAMES_MATCH_PIECE_DESIGNATORS,
    ANY_WHITE_PIECE_NAME,
    ANY_BLACK_PIECE_NAME,
    ALL_PIECES,
    WHITE_PIECE_NAMES,
    BLACK_PIECE_NAMES,
    EMPTY_SQUARE_NAME,
)

from pgn_read.core.constants import (
    FEN_WHITE_KING,
)
from pgn_read.core.squares import Squares

from ..core.constants import (
    MOVE_NUMBER_KEYS,
)
from .rayfilter import RayFilter, move_number_str
from ..core.filespec import (
    PIECESQUAREMOVE_FIELD_DEF,
    PIECEMOVE_FIELD_DEF,
    SQUAREMOVE_FIELD_DEF,
    NEWGAMES_FIELD_DEF,
    PARTIAL_FILE_DEF,
    NEWGAMES_FIELD_VALUE,
    PARTIALPOSITION_FIELD_DEF,
)
from ..core.chessrecord import ChessDBrecordGameUpdate

# The immediate children of nodes with the names of these filters have 'and'
# and 'or' applied to evaluate the node's answer.
_AND_FILTERS = frozenset(
    (
        Token.AND,
        cql.LEFTBRACE_NUMBER,
        cql.LEFTBRACE_POSITION,
        cql.LEFTBRACE_SET,
        cql.LEFTBRACE_LOGICAL,
        Token.CQL,
    )
)
_OR_FILTERS = frozenset(
    (
        Token.OR,
        Token.FLIP,
        Token.FLIPHORIZONTAL,
        Token.FLIPVERTICAL,
        Token.FLIPCOLOR,
        Token.ROTATE45,
        Token.ROTATE90,
        Token.SHIFT,
        Token.SHIFTHORIZONTAL,
        Token.SHIFTVERTICAL,
    )
)

_filters = {
    Token.PIECE_DESIGNATOR,
    Token.RAY,
}
_SUPPORTED_FILTERS = frozenset(_AND_FILTERS.union(_OR_FILTERS.union(_filters)))
del _filters


class ChessQLGamesError(Exception):
    pass


class ChessQLGames:

    """Represent subset of games that match a Chess Query Language query."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)

        # recordclass argument must be used to support non-index field finds.
        # Empty square searches can be transformed into equivalent occupied
        # square searches, but it does not work yet.
        # ChessDBrecordGameUpdate is the closest class to that needed.
        # No update capability is needed, and a different set of 'per move'
        # attributes might be better.
        # The 'try ...' statements in .gui.cqldisplay and .gui.cqltext fit the
        # version of Find(...) call with the recordclass argument.
        # self.cqlfinder = Find(
        #    self.dbhome, self.dbset, recordclass=ChessDBrecordGameUpdate)
        self.cqlfinder = Find(self.dbhome, self.dbset)

        self.not_implemented = set()

    def forget_cql_statement_games(self, sourceobject, commit=True):
        """Forget game records matching ChessQL statement.

        sourceobject is partial position record instance for cql query.
        commit indicates if this method should start and commit transaction.

        """
        # Forget the list of games under the query key.
        ppview = self.dbhome.recordlist_record_number(
            PARTIAL_FILE_DEF, key=sourceobject.key.recno
        )
        if commit:
            self.dbhome.start_transaction()
        self.dbhome.unfile_records_under(
            self.dbset,
            PARTIALPOSITION_FIELD_DEF,
            self.dbhome.encode_record_number(sourceobject.key.recno),
        )

        # Remove query from set that needs recalculating.
        changed = self.dbhome.recordlist_key(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        changed.remove_recordset(ppview)

        self.dbhome.file_records_under(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            changed,
            self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        if commit:
            self.dbhome.commit()

    def update_cql_statement_games(
        self, sourceobject, initial_recordset=None, commit=True
    ):
        """Find game records matching ChessQL statement and store on database.

        sourceobject is partial position record instance for cql query.
        initial_recordset is games to which query is applied
        commit indicates if this method should start and commit transaction.

        """
        assert sourceobject is not None
        # Evaluate query.
        if initial_recordset is None:
            initial_recordlist = self.dbhome.recordlist_ebm(self.dbset)
        else:
            initial_recordlist = self.dbhome.recordlist_nil(self.dbset)
            initial_recordlist |= initial_recordset
        query = sourceobject.value
        games = self.get_games_matching_filters(
            query,
            self.get_games_matching_parameters(query, initial_recordlist),
        )

        # File the list of games under the query key.
        ppview = self.dbhome.recordlist_record_number(
            PARTIAL_FILE_DEF, key=sourceobject.key.recno
        )
        if commit:
            self.dbhome.start_transaction()
        self.dbhome.file_records_under(
            self.dbset,
            PARTIALPOSITION_FIELD_DEF,
            games,
            self.dbhome.encode_record_number(sourceobject.key.recno),
        )

        # Remove query from set that needs recalculating.
        changed = self.dbhome.recordlist_key(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        changed.remove_recordset(ppview)

        self.dbhome.file_records_under(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            changed,
            self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        if commit:
            self.dbhome.commit()

        # Hand the list of games over to the user interface.
        self.set_recordset(games)

    def get_cql_statement_games(
        self, query, sourceobject, initial_recordset=None, commit=True
    ):
        """Find game records matching ChessQL statement.

        query is detail extracted from query statement.
        sourceobject is previously calculated answer.  Set to None to force
        recalculation from query (after editing query statement usually).
        initial_recordset is games to which query is applied.

        """
        if query is None:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return

        # Use the previously calculated record set if possible.
        # sourceobject is set to None if query must be recalculated.
        if sourceobject is not None:
            ppview = self.dbhome.recordlist_record_number(
                PARTIAL_FILE_DEF, key=sourceobject.key.recno
            )
            pprecalc = self.dbhome.recordlist_key(
                PARTIAL_FILE_DEF,
                NEWGAMES_FIELD_DEF,
                key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
            )
            pprecalc &= ppview
            if pprecalc.count_records() == 0:
                ppcalc = self.dbhome.recordlist_key_startswith(
                    self.dbset,
                    PARTIALPOSITION_FIELD_DEF,
                    keystart=self.dbhome.encode_record_number(
                        sourceobject.key.recno
                    ),
                )
                if ppcalc.count_records() != 0:
                    games = self.dbhome.recordlist_key(
                        self.dbset,
                        PARTIALPOSITION_FIELD_DEF,
                        key=self.dbhome.encode_record_number(
                            sourceobject.key.recno
                        ),
                    )

                    # Hand the list of games over to the user interface.
                    self.set_recordset(games)

                    return

        # Evaluate query.
        if initial_recordset is None:
            initial_recordlist = self.dbhome.recordlist_ebm(self.dbset)
        else:
            initial_recordlist = self.dbhome.recordlist_nil(self.dbset)
            initial_recordlist |= initial_recordset
        games = self.get_games_matching_filters(
            query,
            self.get_games_matching_parameters(query, initial_recordlist),
        )

        # Hand the list of games over to the user interface.
        self.set_recordset(games)

    # Not called anywhere.
    # Introduced at revision 3755 as part of 'on' filter implementation which
    # has been, at least temporarely, removed.
    # Called _pieces_matching_filter then.
    def pieces_matching_filter(self, filter_, initialpieces):
        """Return squares matching filters in CQL statement.

        It is assumed FSNode.designator_set contains the expanded piece
        designators.

        """
        if filter_.tokendef in _AND_FILTERS:
            pieces = set(initialpieces)
            for n in filter_.children:
                if n.tokendef is Token.PIECE_DESIGNATOR:
                    pieces.intersection_update(
                        self.pieces_matching_piece_designator(n)
                    )
                    if not pieces:
                        return pieces
            for n in filter_.children:
                if self.is_filter_not_implemented(n):
                    continue
                pieces.intersection_update(
                    self.pieces_matching_filter(n, pieces)
                )
                if not pieces:
                    return pieces
            return pieces
        elif filter_.tokendef in _OR_FILTERS:
            pieces = set(ALL_PIECES)
            for n in filter_.children:
                if self.is_filter_not_implemented(n):
                    continue

                # This cannot be correct given pieces initialisation, or
                # more likely pieces initialisation is not correct too.
                # However pieces_matching_filter is not called anywhere!
                pieces.union(self.pieces_matching_filter(n, initialpieces))

            return pieces
        else:
            if filter_.tokendef is Token.PIECE_DESIGNATOR:
                return self.pieces_matching_piece_designator(filter_)
            return initialpieces

    # Not called anywhere.
    # Introduced at revision 3755 as part of 'on' filter implementation which
    # has been, at least temporarely, removed.
    # Called _squares_matching_filter then.
    def squares_matching_filter(self, filter_, initialsquares):
        """Return squares matching filters in CQL statement.

        It is assumed FSNode.designator_set contains the expanded piece
        designators.

        """
        if filter_.tokendef in _AND_FILTERS:
            squares = set(initialsquares)
            for n in filter_.children:
                if n.tokendef is Token.PIECE_DESIGNATOR:
                    squares.intersection_update(
                        self.squares_matching_piece_designator(n)
                    )
                    if not squares:
                        return squares
            for n in filter_.children:
                if self.is_filter_not_implemented(n):
                    continue
                squares.intersection_update(
                    self.squares_matching_filter(n, squares)
                )
                if not squares:
                    return squares
            return squares
        elif filter_.tokendef in _OR_FILTERS:
            squares = set(Squares.squares)
            for n in filter_.children:
                if self.is_filter_not_implemented(n):
                    continue

                # This cannot be correct given squares initialisation, or
                # more likely squares initialisation is not correct too.
                # However squares_matching_filter is not called anywhere!
                squares.union(self.squares_matching_filter(n, initialsquares))

            return squares
        else:
            if filter_.tokendef is Token.PIECE_DESIGNATOR:
                return self.squares_matching_piece_designator(filter_)
            return initialsquares

    def pieces_matching_piece_designator(self, filter_):
        """Return pieces matching a piece designator."""

        if filter_.tokendef is not Token.PIECE_DESIGNATOR:
            raise ChessQLGamesError(
                "".join(
                    (
                        "'",
                        Token.PIECE_DESIGNATOR.name,
                        "' expected but '",
                        str(filter_.name),
                        "'received",
                    )
                )
            )
        pieces = set()
        for ps in filter_.data.designator_set:
            p = ps[0]
            if p == ANY_WHITE_PIECE_NAME:
                pieces.update(WHITE_PIECE_NAMES)
            elif p == ANY_BLACK_PIECE_NAME:
                pieces.update(BLACK_PIECE_NAMES)
            else:
                pieces.add(p)
        return pieces

    def squares_matching_piece_designator(self, filter_):
        """Return squares matching a piece designator."""

        if filter_.tokendef is not Token.PIECE_DESIGNATOR:
            raise ChessQLGamesError(
                "".join(
                    (
                        "'",
                        Token.PIECE_DESIGNATOR.name,
                        "' expected but '",
                        str(filter_.name),
                        "'received",
                    )
                )
            )
        squares = set()
        for ps in filter_.data.designator_set:
            if len(ps) == 1:
                squares.update(Squares.squares)
            else:
                squares.add(ps[1:])
        return squares

    def is_filter_not_implemented(self, filter_):
        """Return True if filter is not implemented, and False otherwise.

        Filters which are not implemented are added to a list reported before
        evaluating the statement to the extent possible.

        """
        if filter_.tokendef not in _SUPPORTED_FILTERS:
            self.not_implemented.add(filter_.tokendef.name)
            return True
        return False

    def _games_matching_piece_designator(
        self, filter_, datasource, movenumber, variation
    ):
        """Return games matching a piece designator."""

        if filter_.tokendef is not Token.PIECE_DESIGNATOR:
            raise ChessQLGamesError(
                "".join(
                    (
                        "'",
                        Token.PIECE_DESIGNATOR.name,
                        "' expected but '",
                        str(filter_.name),
                        "'received",
                    )
                )
            )
        answer = self._evaluate_piece_designator(
            movenumber, variation, filter_.data.designator_set
        )
        return datasource & answer

    def _games_matching_filter(
        self, filter_, initialgames, movenumber, variation
    ):
        """Return games matching filters in CQL statement.

        It is assumed FSNode.designator_set contains the expanded piece
        designators.

        """
        if filter_.tokendef in _AND_FILTERS:
            games = self.dbhome.recordlist_nil(self.dbset)
            games |= initialgames
            for n in filter_.children:
                if n.tokendef is Token.PIECE_DESIGNATOR:
                    games &= self._games_matching_piece_designator(
                        n, games, movenumber, variation
                    )
                    if not games.count_records():
                        return games
            for n in filter_.children:
                if self.is_filter_not_implemented(n):
                    continue
                games &= self._games_matching_filter(
                    n, games, movenumber, variation
                )
                if not games.count_records():
                    return games
            return games
        elif filter_.tokendef in _OR_FILTERS:
            games = self.dbhome.recordlist_nil(self.dbset)
            for n in filter_.children:
                if self.is_filter_not_implemented(n):
                    continue
                e = self._games_matching_filter(
                    n, initialgames, movenumber, variation
                )
                games |= self._games_matching_filter(
                    n, initialgames, movenumber, variation
                )
            return games
        else:
            if filter_.tokendef is Token.PIECE_DESIGNATOR:
                return self._games_matching_piece_designator(
                    filter_, initialgames, movenumber, variation
                )
            if filter_.tokendef is Token.RAY:
                return self._games_matching_ray_filter(
                    filter_, initialgames, movenumber, variation
                )
            games = self.dbhome.recordlist_nil(self.dbset)
            games |= initialgames
            return games

    def _games_matching_ray_filter(
        self, filter_, datasource, movenumber, variation
    ):
        """Return games matching a ray filter."""

        if filter_.tokendef is not Token.RAY:
            raise ChessQLGamesError(
                "".join(
                    (
                        "'",
                        Token.RAY.name,
                        "' expected but '",
                        str(filter_.name),
                        "'received",
                    )
                )
            )
        rf = RayFilter(filter_, movenumber, variation)
        rf.prune_end_squares(self.dbhome)
        rf.find_games_for_end_squares(self.cqlfinder)
        rf.find_games_for_middle_squares(self.cqlfinder)

        # So that downstream methods have a valid object to work with.
        recordset = self.dbhome.recordlist_nil(self.dbset)
        for gs in rf.ray_games.values():
            recordset |= gs
        return recordset

    def _evaluate_piece_designator(
        self, move_number, variation_code, piecesquares
    ):
        """Return foundset calculated for piece designator using where class.

        The fieldname PieceSquareMove is now unavoidably a bit confusing, where
        move refers to a token in the movetext when the piece is on the square.
        Nothing to do with move number in the movetext, which is the ChessQL
        meaning of move in this context.

        """
        w = Where(
            where_eq_piece_designator(
                move_number, variation_code, piecesquares
            )
        )
        w.lex()
        w.parse()
        v = w.validate(self.cqlfinder.db, self.cqlfinder.dbset)
        w.evaluate(self.cqlfinder)
        return w.get_node_result_answer()

    def get_games_matching_filters(self, query, games):
        """Select the games which meet the ChessQL cql() ... filters.

        Walk node tree for every movenumber and combine evaluated game sets.

        """
        found = self.dbhome.recordlist_nil(self.dbset)
        if not query.cql_filters:
            return found
        query.cql_filters.expand_child_piece_designators()
        key = self._get_high_move_number()
        if key is None:
            return found
        self.not_implemented = set()
        for movenumber in move_number_in_key_range(key):
            found |= self._games_matching_filter(
                query.cql_filters, games, movenumber, "0"
            )
        return found

    # Version of get_games_matching_filters() to process CQL parameters.
    def get_games_matching_parameters(self, query, games):
        """Select the games which meet the ChessQL cql(...) parameters

        Walk node tree for cql parameters and combine evaluated game sets.

        """
        found = self.dbhome.recordlist_nil(self.dbset)
        found |= games
        return found

    def _get_high_move_number(self):
        cursor = self.dbhome.database_cursor(
            self.dbset, PIECESQUAREMOVE_FIELD_DEF
        )
        try:
            return cursor.last()[0]
        except TypeError:
            return None
        finally:
            cursor.close()
            del cursor


def where_eq_piece_designator(move_number, variation_code, designator_set):
    """Return list of selection phrases to evaluate a piece designator.

    The fieldname PieceSquareMove is now unavoidably a bit confusing, where
    move refers to a token in the movetext when the piece is on the square.
    Nothing to do with move number in the movetext, which is the ChessQL
    meaning of move in this context.

    """
    anypiece = ANY_WHITE_PIECE_NAME + ANY_BLACK_PIECE_NAME
    psmfield = PIECESQUAREMOVE_FIELD_DEF
    pmfield = PIECEMOVE_FIELD_DEF
    smfield = SQUAREMOVE_FIELD_DEF
    mns = move_number_str(move_number)
    psmds = set()
    pmds = set()
    emptyds = set()
    smds = set()
    for ps in designator_set:
        if len(ps) == 1:

            # Rules of chess imply whole piece designator finds all games if
            # any of 'A', 'a', 'K', 'k', and '_', are in designator set.
            if ps[0] in ALL_GAMES_MATCH_PIECE_DESIGNATORS:
                return " ".join(
                    (
                        pmfield,
                        EQ,
                        "".join((mns, variation_code, FEN_WHITE_KING)),
                    )
                )

            pmds.add("".join((mns, variation_code, ps[0])))
            continue
        if ps[0] == EMPTY_SQUARE_NAME:
            sq = ps[1:]

            # 'not field eq value1 or value2' does not work, it should, but
            # 'not field eq value1 and not field eq value2' does work.
            # emptyds.add(' '.join(
            #    (NOT,
            #     smfield,
            #     EQ,
            #     ''.join((mns, variation_code, sq + ANY_WHITE_PIECE_NAME)),
            #     OR,
            #     ''.join((mns, variation_code, sq + ANY_BLACK_PIECE_NAME)),
            #     )))
            emptyds.add(
                " ".join(
                    (
                        NOT,
                        smfield,
                        EQ,
                        "".join(
                            (mns, variation_code, sq + ANY_WHITE_PIECE_NAME)
                        ),
                        AND,
                        NOT,
                        smfield,
                        EQ,
                        "".join(
                            (mns, variation_code, sq + ANY_BLACK_PIECE_NAME)
                        ),
                    )
                )
            )

            continue
        if ps[0] in anypiece:
            smds.add(
                "".join(
                    (
                        mns,
                        variation_code,
                        ps[1:] + ps[0],
                    )
                )
            )
            continue
        psmds.add(
            "".join(
                (
                    mns,
                    variation_code,
                    ps[1:] + ps[0],
                )
            )
        )

    phrases = []
    if psmds:
        phrases.append(" ".join((psmfield, EQ, OR.join("  ").join(psmds))))
    if pmds:
        phrases.append(" ".join((pmfield, EQ, OR.join("  ").join(pmds))))
    if smds:
        phrases.append(" ".join((smfield, EQ, OR.join("  ").join(smds))))
    if emptyds:
        phrases.append(OR.join("  ").join(emptyds))
    if phrases:
        return OR.join("  ").join(phrases)


# def move_number_str(move_number):
#    """Return hex(move_number) values without leading '0x' but prefixed with
#    string length.
#    """
#    # Adapted from module pgn_read.core.parser method add_move_to_game().
#    try:
#        return MOVE_NUMBER_KEYS[move_number]
#    except IndexError:
#        c = hex(move_number)
#        return str(len(c)-2) + c[2:]


def move_number_in_key_range(key):
    """Yield the move number keys in a range one-by-one."""
    for n in range(1, literal_eval("0x" + key[1 : int(key[0]) + 1])):
        yield n
