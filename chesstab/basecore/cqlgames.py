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
    )

from chessql.core import constants
from chessql.core.constants import (
    ALL_GAMES_MATCH_PIECE_DESIGNATORS,
    ANY_WHITE_PIECE_NAME,
    ANY_BLACK_PIECE_NAME,
    ALL_PIECES,
    WHITE_PIECE_NAMES,
    BLACK_PIECE_NAMES,
    )

from pgn_read.core.constants import (
    MAP_PGN_SQUARE_NAME_TO_FEN_ORDER,
    MOVE_NUMBER_KEYS,
    WKING,
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

AND_FILTERS = frozenset((constants.LEFT_BRACE_FILTER,
                         'cql',
                         ))
OR_FILTERS = frozenset((constants.OR,
                        constants.FLIP,
                        constants.FLIPDIHEDRAL,
                        constants.FLIPHORIZONTAL,
                        constants.FLIPVERTICAL,
                        constants.FLIPCOLOR,
                        constants.NEXT_STAR,
                        constants.PREVIOUS_STAR,
                        constants.ROTATE45,
                        constants.ROTATE90,
                        constants.SHIFT,
                        constants.SHIFTHORIZONTAL,
                        constants.SHIFTVERTICAL,
                        ))
_filters = {constants.PIECE_DESIGNATOR_FILTER,
            constants.ON,
            constants.RAY,
            }
_SUPPORTED_FILTERS = frozenset(AND_FILTERS.union(OR_FILTERS.union(_filters)))
del _filters


class ChessQLGamesError(Exception):
    pass


class ChessQLGames:
    
    """Represent subset of games that match a Chess Query Language query.
    """

    def __init__(self, *a, **k):
        super().__init__(*a, **k)

        # recordclass argument must be used to support non-index field finds.
        self.cqlfinder = Find(self.dbhome, self.dbset)

        self.not_implemented = set()

    def forget_cql_statement_games(
        self, sourceobject, commit=True):
        """Forget game records matching ChessQL statement.

        sourceobject is partial position record instance for cql query.
        commit indicates if this method should start and commit transaction.
        
        """
        # Forget the list of games under the query key.
        ppview = self.dbhome.recordlist_record_number(
            PARTIAL_FILE_DEF,
            key=sourceobject.key.recno)
        if commit:
            self.dbhome.start_transaction()
        self.dbhome.unfile_records_under(
            self.dbset,
            PARTIALPOSITION_FIELD_DEF,
            self.dbhome.encode_record_number(sourceobject.key.recno))

        # Remove query from set that needs recalculating.
        changed = self.dbhome.recordlist_key(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE))
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
        self, sourceobject, initial_recordset=None, commit=True):
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
            self.get_games_matching_parameters(query, initial_recordlist))

        # File the list of games under the query key.
        ppview = self.dbhome.recordlist_record_number(
            PARTIAL_FILE_DEF,
            key=sourceobject.key.recno)
        if commit:
            self.dbhome.start_transaction()
        self.dbhome.file_records_under(
            self.dbset,
            PARTIALPOSITION_FIELD_DEF,
            games,
            self.dbhome.encode_record_number(sourceobject.key.recno))

        # Remove query from set that needs recalculating.
        changed = self.dbhome.recordlist_key(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE))
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
        self, query, sourceobject, initial_recordset=None, commit=True):
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
                PARTIAL_FILE_DEF,
                key=sourceobject.key.recno)
            pprecalc = self.dbhome.recordlist_key(
                PARTIAL_FILE_DEF,
                NEWGAMES_FIELD_DEF,
                key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE))
            pprecalc &= ppview
            if pprecalc.count_records() == 0:
                ppcalc = self.dbhome.recordlist_key_startswith(
                    self.dbset,
                    PARTIALPOSITION_FIELD_DEF,
                    keystart=self.dbhome.encode_record_number(
                        sourceobject.key.recno))
                if ppcalc.count_records() != 0:
                    games = self.dbhome.recordlist_key(
                        self.dbset,
                        PARTIALPOSITION_FIELD_DEF,
                        key=self.dbhome.encode_record_number(
                            sourceobject.key.recno))

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
            self.get_games_matching_parameters(query, initial_recordlist))

        # Hand the list of games over to the user interface.
        self.set_recordset(games)
        
    def pieces_matching_filter(self, filter_, initialpieces):
        """Return squares matching filters in CQL statement.

        It is assumed FSNode.designator_set contains the expanded piece
        designators.

        """
        if filter_.type in AND_FILTERS:
            pieces = set(initialpieces)
            for n in filter_.children:
                if n.type == constants.PIECE_DESIGNATOR_FILTER:
                    pieces.intersection_update(
                        self.pieces_matching_piece_designator(n))
                    if not pieces:
                        return pieces
            for n in filter_.children:
                if self.is_filter_implemented(n):
                    continue
                pieces.intersection_update(
                    self.pieces_matching_filter(n, pieces))
                if not pieces:
                    return pieces
            return pieces
        elif filter_.type in OR_FILTERS:
            pieces = set(ALL_PIECES)
            for n in filter_.children:
                if self.is_filter_implemented(n):
                    continue
                pieces.union(
                    self.pieces_matching_filter(n, initialpieces))
            return pieces
        else:
            if filter_.type == constants.PIECE_DESIGNATOR_FILTER:
                return self.pieces_matching_piece_designator(filter_)
            if filter_.type == constants.ON:
                return self.pieces_matching_on_filter(filter_)
            return initialpieces
        
    def squares_matching_filter(self, filter_, initialsquares):
        """Return squares matching filters in CQL statement.

        It is assumed FSNode.designator_set contains the expanded piece
        designators.

        """
        if filter_.type in AND_FILTERS:
            squares = set(initialsquares)
            for n in filter_.children:
                if n.type == constants.PIECE_DESIGNATOR_FILTER:
                    squares.intersection_update(
                        self.squares_matching_piece_designator(n))
                    if not squares:
                        return squares
            for n in filter_.children:
                if self.is_filter_implemented(n):
                    continue
                squares.intersection_update(
                    self.squares_matching_filter(n, squares))
                if not squares:
                    return squares
            return squares
        elif filter_.type in OR_FILTERS:
            squares = set(MAP_PGN_SQUARE_NAME_TO_FEN_ORDER)
            for n in filter_.children:
                if self.is_filter_implemented(n):
                    continue
                squares.union(
                    self.squares_matching_filter(n, initialsquares))
            return squares
        else:
            if filter_.type == constants.PIECE_DESIGNATOR_FILTER:
                return self.squares_matching_piece_designator(filter_)
            if filter_.type == constants.ON:
                return self.squares_matching_on_filter(filter_)
            return initialsquares
        
    def pieces_matching_piece_designator(self, filter_):
        """Return pieces matching a piece designator."""

        if filter_.type != constants.PIECE_DESIGNATOR_FILTER:
            raise ChessQLGamesError(''.join(("'",
                                             constants.PIECE_DESIGNATOR_FILTER,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
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

        if filter_.type != constants.PIECE_DESIGNATOR_FILTER:
            raise ChessQLGamesError(''.join(("'",
                                             constants.PIECE_DESIGNATOR_FILTER,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
        squares = set()
        for ps in filter_.data.designator_set:
            if len(ps) == 1:
                squares.update(MAP_PGN_SQUARE_NAME_TO_FEN_ORDER)
            else:
                squares.add(ps[1:])
        return squares
        
    def pieces_matching_on_filter(self, filter_):
        """Return pieces matching an on filter."""

        if filter_.type != constants.ON:
            raise ChessQLGamesError(''.join(("'",
                                             constants.ON,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
        left = self.pieces_matching_filter(
            filter_.children[0],
            set(ALL_PIECES))
        right = self.pieces_matching_filter(
            filter_.children[1],
            set(ALL_PIECES))
        return left.intersection(right)
        
    def squares_matching_on_filter(self, filter_):
        """Return squares matching an on filter."""

        if filter_.type != constants.ON:
            raise ChessQLGamesError(''.join(("'",
                                             constants.ON,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
        left = self.squares_matching_filter(
            filter_.children[0],
            set(MAP_PGN_SQUARE_NAME_TO_FEN_ORDER))
        right = self.squares_matching_filter(
            filter_.children[1],
            set(MAP_PGN_SQUARE_NAME_TO_FEN_ORDER))
        return left.intersection(right)

    # Incomprehensible!!!
    def is_filter_implemented(self, filter_):
        if filter_.type == constants.PLAIN_FILTER:
            self.not_implemented.add(filter_.leaf)
            return True
        elif filter_.type not in _SUPPORTED_FILTERS:
            self.not_implemented.add(filter_.type)
            return True
        return False
        
    def _games_matching_piece_designator(
        self, filter_, datasource, movenumber, variation):
        """Return games matching a piece designator."""

        if filter_.type != constants.PIECE_DESIGNATOR_FILTER:
            raise ChessQLGamesError(''.join(("'",
                                             constants.PIECE_DESIGNATOR_FILTER,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
        answer = self._evaluate_piece_designator(
            movenumber,
            variation,
            filter_.data.designator_set)
        return datasource & answer

    def _games_matching_filter(
        self, filter_, initialgames, movenumber, variation):
        """Return games matching filters in CQL statement.

        It is assumed FSNode.designator_set contains the expanded piece
        designators.

        """
        if filter_.type in AND_FILTERS:
            games = self.dbhome.recordlist_nil(self.dbset)
            games |= initialgames
            for n in filter_.children:
                if n.type == constants.PIECE_DESIGNATOR_FILTER:
                    games &= self._games_matching_piece_designator(
                        n, games, movenumber, variation)
                    if not games.count_records():
                        return games
            for n in filter_.children:
                if self.is_filter_implemented(n):
                    continue
                games &= self._games_matching_filter(
                    n, games, movenumber, variation)
                if not games.count_records():
                    return games
            return games
        elif filter_.type in OR_FILTERS:
            games = self.dbhome.recordlist_nil(self.dbset)
            for n in filter_.children:
                if self.is_filter_implemented(n):
                    continue
                e = self._games_matching_filter(
                    n, initialgames, movenumber, variation)
                games |= self._games_matching_filter(
                    n, initialgames, movenumber, variation)
            return games
        else:
            if filter_.type == constants.PIECE_DESIGNATOR_FILTER:
                return self._games_matching_piece_designator(
                    filter_, initialgames, movenumber, variation)
            if filter_.type == constants.ON:
                return self._games_matching_on_filter(
                    filter_, initialgames, movenumber, variation)
            if filter_.type == constants.RAY:
                return self._games_matching_ray_filter(
                    filter_, initialgames, movenumber, variation)
            games = self.dbhome.recordlist_nil(self.dbset)
            games |= initialgames
            return games
        
    def _games_matching_on_filter(
        self, filter_, datasource, movenumber, variation):
        """Return games matching an on filter."""

        if filter_.type != constants.ON:
            raise ChessQLGamesError(''.join(("'",
                                             constants.ON,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
        left = self.squares_matching_filter(
            filter_.children[0],
            set(MAP_PGN_SQUARE_NAME_TO_FEN_ORDER))
        right = self.squares_matching_filter(
            filter_.children[1],
            set(MAP_PGN_SQUARE_NAME_TO_FEN_ORDER))
        squares = left.intersection(right)
        if not squares:
            return self.dbhome.recordlist_nil(self.dbset)
        left = self.pieces_matching_filter(
            filter_.children[0],
            set(constants.ALL_PIECES))
        right = self.pieces_matching_filter(
            filter_.children[1],
            set(constants.ALL_PIECES))
        pieces = left.intersection(right)
        if not pieces:
            return self.dbhome.recordlist_nil(self.dbset)
        answer = self._evaluate_piece_designator(
            movenumber,
            variation,
            {p + s for p in pieces for s in squares})
        leftgames = self._games_matching_filter(
            filter_.children[0], datasource, movenumber, variation)
        rightgames = self._games_matching_filter(
            filter_.children[1], datasource, movenumber, variation)
        return leftgames & rightgames & answer
        
    def _games_matching_ray_filter(
        self, filter_, datasource, movenumber, variation):
        """Return games matching a ray filter."""

        if filter_.type != constants.RAY:
            raise ChessQLGamesError(''.join(("'",
                                             constants.RAY,
                                             "' expected but '",
                                             str(filter_.type),
                                             "'received",
                                             )))
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
        self, move_number, variation_code, piecesquares):
        """Return foundset calculated for piece designator using where class.

        The fieldname PieceSquareMove is now unavoidably a bit confusing, where
        move refers to a token in the movetext when the piece is on the square.
        Nothing to do with move number in the movetext, which is the ChessQL
        meaning of move in this context.

        """
        w = Where(where_eq_piece_designator(
            move_number, variation_code, piecesquares))
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
                query.cql_filters, games, movenumber, '0')
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
        cursor = self.dbhome.database_cursor(self.dbset,
                                             PIECESQUAREMOVE_FIELD_DEF)
        try:
            return cursor.last()[0]
        except TypeError:
            return None
        finally:
            cursor.close()
            del cursor


def where_eq_piece_designator(move_number, variation_code, designator_set):
    """.

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
            # any of 'A', 'a', 'K', 'k', and '.', are in designator set.
            if ps[0] in ALL_GAMES_MATCH_PIECE_DESIGNATORS:
                return ' '.join(
                    (pmfield, EQ, ''.join((mns, variation_code, WKING))))
            
            pmds.add(''.join((mns, variation_code, ps[0])))
            continue
        if ps[0] == constants.EMPTY_SQUARE_NAME:
            sq = ps[1:]
            emptyds.add(' '.join(
                (NOT,
                 psmfield,
                 EQ,
                 ''.join((mns, variation_code, sq + ANY_WHITE_PIECE_NAME)),
                 OR,
                 ''.join((mns, variation_code, sq + ANY_BLACK_PIECE_NAME)),
                 )))
            continue
        if ps[0] in anypiece:
            smds.add(''.join(
                (mns,
                 variation_code,
                 ps[1:] + ps[0],
                 )))
            continue
        psmds.add(''.join(
            (mns,
             variation_code,
             ps[1:] + ps[0],
             )))

    phrases = []
    if psmds:
        phrases.append(' '.join((psmfield, EQ, OR.join('  ').join(psmds))))
    if pmds:
        phrases.append(' '.join((pmfield, EQ, OR.join('  ').join(pmds))))
    if smds:
        phrases.append(' '.join((smfield, EQ, OR.join('  ').join(smds))))
    if emptyds:
        phrases.append(OR.join('  ').join(emptyds))
    if phrases:
        return OR.join('  ').join(phrases)


#def move_number_str(move_number):
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
    for n in range(1, literal_eval('0x' + key[1:int(key[0]) + 1])):
        yield n
