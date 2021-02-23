# cqlstatement.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (CQL) statement parser.

Thes extracts from http://www.gadycosteff.com/cql/doc/operation.html for cql5.1
briefly describe CQL and how the cql.exe program operates.

A CQL statement has three parts:

    The word cql
    The cql parameters: a sequence of cql parameters enclosed in parentheses
    The cql body: a sequence of filters

CQL successively reads each game in its input PGN file. For each such game, CQL
plays through each move in the game.

Every time CQL reaches a position, it sets the current position to that
position. Then CQL tries to match each of its filters against that position.
If all the filters in the CQL file match the position, then CQL is said to have
matched the position.

When CQL has finished trying to match all the positions in the game against its
filters, then if any of the positions matched, CQL will output the game to the
output file. The output file can be specified either by default (in which case
its name is the name of the CQL file with -out appended); or as a parameter in
to the cql arguments in the CQL file itself; or on the command line. 


The earlier partial position scheme implemented a sequence of piece designator
filters in CQL terms.  The equivalent of piece designator was limited to the
form 'Ra3', with pieces identified as one of 'KQRBNPkqrbnp?Xx-' where X is
replaced by A, x by a, ? by [Aa], and - by [Aa.], in CQL.  'A' is any white
piece, 'a' is any black piece, and '.' is an empty square. '[Aa.]' means it
does not matter whether the square is occupied because either white piece or
black piece or empty square matches.

"""

from chessql.core.statement import Statement
#from chessql.core.constants import PIECE_DESIGNATOR_FILTER
#from chessql.core.piecedesignator import PieceDesignator

from .cqlnode import CQLNode, FSNode


class CQLStatementError(Exception):
    pass


class CQLStatement(Statement):
    """CQL statement parser.

    Parse text for a CQL statement.

    """
    create_node = CQLNode

    def __init__(self):
        """"""
        super().__init__()

        # Not sure this is needed or wanted.
        # See datasource argument to get_games_matching_filters().
        # dbset not used until a QueryStatement instance evaluates query.
        #self._dbset = None

        # _dbset and __database are passed to QueryStatement instances which
        # evaluate the query: not used directly in this class.

        self._dbset = None

        # Support using where.Where or where_dpt.Where depending on database
        # engine being used.
        # This attribute should not be used for anything else.
        self.__database = None
        #self.root_filter_node = None

    @property
    def dbset(self):
        return self._dbset

    @dbset.setter
    def dbset(self, value):
        if self._dbset is None:
            self._dbset = value
        elif self._dbset != value:
            raise CQLStatementError(
                ''.join(("Database file name already set to ",
                         repr(self._dbset),
                         ", cannot change to ",
                         repr(value),
                         ".")))

    def set_database(self, database=None):
        """Set Database instance to which ChessQL query is applied."""
        self.__database = database

    # Until the naming convention is resolved.
    def get_name_cql_statement_text(self):
        """Return name and statement text."""
        return super().get_name_statement_text()

    # Until the naming convention is resolved.
    def get_cql_statement_text(self):
        """Return statement text."""
        return super().get_statement_text()
        
    # Until the naming convention is resolved.
    def process_cql_statement(self, text):
        """Lex and parse the ChessQL statement."""

        # None or False returned depending on problem.
        result = super().process_statement(text)
        if not result:
            return result

        # self.cql_parameters and self.cql_filters contain a node tree for a
        # valid Chess QL statement.
        if self.cql_filters is None:
            return result
        #self.root_filter_node = FSNode(self.cql_filters)
        r = self.cql_filters.transform_piece_designators(
            FSNode(self.cql_filters))
        if r:
            self.cql_error = r
        return result

    # Until the naming convention is resolved.
    def is_cql_statement(self):
        """Return True if the statement text is valid CQL syntax."""
        return super().is_statement()

    # Not sure this is needed or wanted.
    #@property
    #def dbset(self):
    #    return self._dbset

    # Not sure this is needed or wanted.
    #@dbset.setter
    #def dbset(self, value):
    #    if self._dbset is None:
    #        self._dbset = value
    #    elif self._dbset != value:
    #        raise QueryStatementError(
    #            ''.join(("Database file name already set to ",
    #                     repr(self._dbset),
    #                     ", cannot change to ",
    #                     repr(value),
    #                     ".")))
        
    #def _transform_piece_designators(self, filter_):
    #    """Apply transforms to piece designators in CQL statement."""
    #    children = filter_.children
    #    for n in filter_.node.children:
    #        children.append(FSNode(n))
    #        r = self._transform_piece_designators(children[-1])
    #        if r:
    #            return r
    #    r = filter_.transform_descendant_piece_designators()
    #    if r:
    #        return r
        
    #def expand_piece_designators(self, filter_):
    #    """Expand piece designators in CQL statement.

    #    Expanded piece designators are made available in FSNode.designator_set,
    #    and cache for optimizing index access.

    #    """
    #    for n in filter_.children:
    #        self.expand_piece_designators(n)
    #    if filter_.leaf:
    #        if filter_.type == PIECE_DESIGNATOR_FILTER:
    #            pd = PieceDesignator(filter_.leaf)
    #            pd.parse()
    #            pd.expand_piece_designator()
    #            filter_.data = pd
