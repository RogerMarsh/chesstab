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

# from chessql.core.constants import PIECE_DESIGNATOR_FILTER
# from chessql.core.piecedesignator import PieceDesignator

from .cqlnode import CQLNode, FSNode
from .constants import NAME_DELIMITER

_ROTATE45_VALIDATION_TABLE = str.maketrans("12345678", "xxxxxxxx")


class CQLStatementError(Exception):
    pass


class CQLStatement(Statement):
    """CQL statement parser.

    Parse text for a CQL statement.

    """

    create_node = CQLNode

    def __init__(self):
        """ """
        # Error handling is slightly different to .querystatement module.
        # The error information object is held directly here while it is held
        # in the Where instance used to calculate the query there.
        # This module processes instructions used to generate Where instances.
        super().__init__()
        self._description_string = ""

        # Not sure this is needed or wanted.
        # See datasource argument to get_games_matching_filters().
        # dbset not used until a QueryStatement instance evaluates query.
        # self._dbset = None

        # _dbset and __database are passed to QueryStatement instances which
        # evaluate the query: not used directly in this class.

        self._dbset = None

        # Support using where.Where or where_dpt.Where depending on database
        # engine being used.
        # This attribute should not be used for anything else.
        self.__database = None
        # self.root_filter_node = None

    @property
    def dbset(self):
        return self._dbset

    @dbset.setter
    def dbset(self, value):
        if self._dbset is None:
            self._dbset = value
        elif self._dbset != value:
            raise CQLStatementError(
                "".join(
                    (
                        "Database file name already set to ",
                        repr(self._dbset),
                        ", cannot change to ",
                        repr(value),
                        ".",
                    )
                )
            )

    def set_database(self, database=None):
        """Set Database instance to which ChessQL query is applied."""
        self.__database = database

    def get_name_text(self):
        """Return name text."""
        return self._description_string

    def get_name_statement_text(self):
        """Return name and statement text."""
        return NAME_DELIMITER.join(
            (
                self._description_string,
                self.get_statement_text(),
            )
        )

    def process_statement(self, text):
        """Lex and parse the ChessQL statement.

        Two attempts to process the text are done.  The first treats the whole
        text as a ChessQL statement.  If it fails the second attempt treats
        the first line of text as the query's name and the rest as a ChessQL
        statement.

        Thus the query's name cannot be a valid CQL version 6 filter or
        sequence of filters.

        """
        self._description_string = ""
        super().process_statement(text.strip())
        if self.cql_error:
            rule = [t.strip() for t in text.split(NAME_DELIMITER, 1)]
            if len(rule) == 1:

                # The text cannot have an initial name component because text
                # equals rule[0] and there is no point in processing the text
                # again without the non-existent name component.
                # Assume initialization needed if text == ''.
                if text == "":
                    self._statement_string = ""
                    self._reset_state()
                    self._error_information = False
                return

            self._description_string = rule[0]
            super().process_statement(rule[1])

        # As it was in chessql.core.statement module, where it did not reject
        # any statements (possibly because rotate45 was never tried seriously)
        # before evaluation code transferred to ChessTab.
        # return self._rotate45_specific_squares(self.cql_filters, [])

        # self.cql_parameters and self.cql_filters contain a node tree for a
        # valid Chess QL statement.
        if self.cql_filters is None:
            return
        r = self.cql_filters.transform_piece_designators(
            FSNode(self.cql_filters)
        )
        if r:
            self.cql_error = r
        return

    def _rotate45_specific_squares(self, filter_, rotate45stack):
        if filter_.name == "rotate45":
            rotate45stack.append(None)
        for n in filter_.children:
            if rotate45stack and n.name == "piecedesignator":
                # if {c for c in n.leaf}.intersection('12345678'))
                if n.leaf != n.leaf.translate(_ROTATE45_VALIDATION_TABLE):
                    self._error_information = ErrorInformation(
                        self._statement_string.strip()
                    )
                    self._error_information.description = (
                        "rotate45 on specific squares"
                    )
                    return self._error_information
            r45ss = self._rotate45_specific_squares(n, rotate45stack)
            if r45ss:
                return r45ss
        if filter_.name == "rotate45":
            rotate45stack.pop()
        return None
