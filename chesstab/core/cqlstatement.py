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

from ..cql import querycontainer
from ..cql.queryevaluator import QueryEvaluatorError

# Search for start of CQL statement for internal evaluator.
_title_re = re.compile("^[^\n]*")


class CQLStatement:
    """CQL statement parser and evaluator.

    The command and opendatabase arguments allow for evaluation by the CQL
    program or internally.
    """

    def __init__(self):
        """Delegate then initialize description and database name."""
        super().__init__()
        self._description_string = ""
        self._statement_string = ""

        # For setup of internal or external evaluation of CQL statement.
        self._query_container = None

        # For evaluation of CQL statement by CQL program.
        self._recordset = None
        self._opendatabase = None
        self._dbset = None

    @property
    def query_container(self):
        """Return query container."""
        return self._query_container

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
            raise QueryEvaluatorError(
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
        name = os.path.basename(self._opendatabase.database_file)
        return os.path.join(
            self._opendatabase.home_directory,
            ".".join(("-".join((name, name)), "pgn")),
        )

    @property
    def cql_filename(self):
        """Return CQL query filename for pattern engine command."""
        name = os.path.basename(self._opendatabase.database_file)
        return os.path.join(
            self._opendatabase.home_directory,
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

    def set_database(self, database=None):
        """Set Database instance to which ChessQL query is applied."""
        self._opendatabase = database

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
        return self._opendatabase.database_file

    def prepare_cql_statement(self, text):
        """Verify CQL statement but do not evaluate."""
        self._query_container = querycontainer.QueryContainer()
        self._recordset = self._opendatabase.recordlist_nil(self._dbset)
        if text:  # Assume text "" means an insert new action.
            self._query_container.prepare_statement(self, text)
        if self._query_container.message is not None:
            raise QueryEvaluatorError(self._query_container.message)

    # At time of writing the implementation is same as load_statement but
    # it is correct these are different methods.
    def split_statement(self, text):
        """Split text into title and query text."""
        return self._split_statement(text)
