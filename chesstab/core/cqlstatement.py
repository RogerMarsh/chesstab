# cqlstatement.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (CQL) statement parser and evaluator.

See http://www.gadycosteff.com/ for a description of the latest version.

A limited CQL evaluator is provided internally.

The CQL program can be run to evaluate statements and return a list of
games which match the query statement.

The earlier partial position scheme implemented a sequence of piece designator
filters in CQL terms.  The equivalent of piece designator was limited to the
form 'Ra3', with pieces identified as one of 'KQRBNPkqrbnp?Xx-' where X is
replaced by A, x by a, ? by [Aa], and - by [Aa.], in CQL.  'A' is any white
piece, 'a' is any black piece, and '.' is an empty square. '[Aa.]' means it
does not matter whether the square is occupied because either white piece or
black piece or empty square matches.

"""
import os
import re

from . import cqlcontainer
from . import filespec

# Search for start of CQL statement for internal evaluator.
_title_re = re.compile("^[^\n]*")


class CQLStatementError(Exception):
    """Exception class for cqlstatement module."""


class CQLStatement:
    """CQL statement parser and evaluator.

    The command and opendatabase arguments allow for evaluation by the CQL
    program or internally.
    """

    # Keyword arguments for compatibility with existing chesstab code.
    def __init__(
        self, command=None, opendatabase=None, query_container_class=None
    ):
        """Delegate then initialize description and database name.

        query_container_class is ignored if opendatabase is None but
        should be the class which will evaluate CQL queries otherwise.

        """
        super().__init__()
        self._description_string = ""
        self._statement_string = ""

        # File searched for matching records.
        self._dbset = None

        # For setup of internal or external evaluation of CQL statement.
        self._query_container_class = None
        self._query_container = None

        # For internal evaluation of CQL statement.
        self._query_evaluator = None

        # For evaluation of CQL statement by CQL program.
        self._command = None
        self._recordset = None
        self._home_directory = None
        self._database_file = None

        # For evaluation of CQL statement by CQL program.
        self._command = command

        if opendatabase is not None:
            self._recordset = opendatabase.recordlist_nil(
                filespec.GAMES_FILE_DEF
            )
            self._home_directory = opendatabase.home_directory
            self._database_file = opendatabase.database_file
            self._query_container_class = query_container_class
        else:
            self._query_container_class = cqlcontainer.CQLContainer
            self._database_file = None

    @property
    def query_container_class(self):
        """Return query container class."""
        return self._query_container_class

    @property
    def query_container(self):
        """Return query container."""
        return self._query_container

    @property
    def query_evaluator(self):
        """Return query evaluator."""
        return self._query_evaluator

    @property
    def dbset(self):
        """Return database filename."""
        return self._dbset

    @dbset.setter
    def dbset(self, value):
        """Set database filename."""
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

    @property
    def pgn_filename(self):
        """Return pgn filename for pattern engine command."""
        name = os.path.basename(self._database_file)
        return os.path.join(
            self._home_directory,
            ".".join(("-".join((name, name)), "pgn")),
        )

    @property
    def cql_filename(self):
        """Return CQL query filename for pattern engine command."""
        name = os.path.basename(self._database_file)
        return os.path.join(
            self._home_directory,
            ".".join(("-".join((name, name)), "cql")),
        )

    @property
    def recordset(self):
        """Return self._recordset."""
        return self._recordset

    @property
    def cql_error(self):
        """Return the error information for the CQL statement."""
        return None

    def is_statement(self):
        """Return True if the statement has no errors."""
        return not self.cql_error

    # Called from chessrecord.ChessDBrecordPartial.load_value().
    def set_database(self, database=None):
        """Set Database instance to which ChessQL query is applied."""
        # pylint unused-private-member report W0238.
        # Commented because vaguely similar querystatement module does use it.
        # self.__database = database

    def get_name_text(self):
        """Return name text."""
        return self._description_string

    def get_statement_text(self):
        """Return statement text including leading newline delimiter."""
        return self._statement_string

    def get_statement_text_display(self):
        """Return statement text excluding leading newline delimiter."""
        return self._statement_string.split("\n", 1)[-1]

    def get_name_statement_text(self):
        """Return name and statement text."""
        return self._description_string + self.get_statement_text()

    def _split_statement(self, text):
        """Split text into description and statement strings.

        Leading and trailing whitespace has been stripped from the value
        passed as text argument.

        """
        self._description_string = ""
        title = _title_re.search(text)
        title_end = title.end() if title else 0
        self._description_string = text[:title_end]
        self._statement_string = text[title_end:]
        return title_end

    def load_statement(self, text):
        """Split text into description and statement strings for grids."""
        self._split_statement(text)

    @property
    def database_file(self):
        """Return database file."""
        return self._database_file

    def prepare_cql_statement(self, text):
        """Verify CQL statement but do not evaluate."""
        self._query_container = self._query_container_class()
        self._query_container.prepare_statement(self, text)
        if self._query_container.message is not None:
            raise CQLStatementError(self._query_container.message)

    # At time of writing the implementation is same as load_statement but
    # it is correct these are different methods.
    def split_statement(self, text):
        """Split text into title and query text."""
        return self._split_statement(text)
