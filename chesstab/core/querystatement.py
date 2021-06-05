# querystatement.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Game selection rule parser.
"""

import re

from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from solentware_base.core.where import LIKE

from .constants import NAME_DELIMITER

# Normalize player names for index consistency.
# Format defined in the PGN specification is 'surname, forename I.J.' assuming
# no spaces between initials when more than one are adjacent. Real PGN files do
# not always adhere.
# Names like 'surname, I. forename J.' may occur.
# Index values are created by replacing all sequences containing just commas,
# periods, and whitespace, by a single space.
re_normalize_player_name = re.compile("([^,\.\s]+)(?:[,\.\s]*)")


class QueryStatementError(Exception):
    pass


class QueryStatement(object):
    """Game selection rule parser.

    Parse text for a game selection rule specification.

    """

    def __init__(self):
        """ """
        super().__init__()
        self._dbset = None

        # Support using where.Where or where_dpt.Where depending on database
        # engine being used.
        # This attribute should not be used for anything else.
        self.__database = None

        self._description_string = ""
        self._query_statement_string = ""
        self._where_error = None

        self._reset_rule_state()

    def _reset_rule_state(self):
        """Initialiase the selection rule parsing state.

        The analyser is able to have at least two goes at a statement.

        """
        self.where = None
        self.textok = ""
        self.texterror = ""

    @property
    def where_error(self):
        return self._where_error

    @property
    def dbset(self):
        return self._dbset

    @dbset.setter
    def dbset(self, value):
        if self._dbset is None:
            self._dbset = value
        elif self._dbset != value:
            raise QueryStatementError(
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

    def process_query_statement(self, text):
        """Process selection rule in text.

        First attempt treats whole text as a selection rule.
        Second attempt treats first line, of at least two, as the name of the
        selection rule and the rest as a selection rule.

        """
        if self.__database is None:
            return

        # Assume no error, but set False indicating process_query_statement
        # has been called.
        self._where_error = False

        for rule in (
            ("", text.strip()),
            [t.strip() for t in text.split(NAME_DELIMITER, 1)],
        ):

            if len(rule) == 1:

                # The second element of rule is being processed and the text in
                # rule[1] cannot be a valid selection rule because it is the
                # text which was processed from the first element of rule.
                # self._where_error is bound to a WhereStatementError instance.
                return False

            self._reset_rule_state()
            self._description_string, self._query_statement_string = rule
            w = self.__database.record_selector(self._query_statement_string)
            w.lex()
            w.parse()
            if w.validate(self.__database, self.dbset):
                self._where_error = w.error_information
                continue
            self.where = w
            self.textok = self._query_statement_string
            self.texterror = ""
            self._where_error = False
            for n in w.node.get_clauses_from_root_in_walk_order():
                if n.field in (TAG_WHITE, TAG_BLACK):
                    if n.condition == LIKE:
                        continue
                    if not isinstance(n.value, tuple):
                        n.value = " ".join(
                            re_normalize_player_name.findall(n.value)
                        )
                    else:
                        n.value = tuple(
                            [
                                " ".join(re_normalize_player_name.findall(nv))
                                for nv in n.value
                            ]
                        )
            return True

        # self._where_error is not bound to a WhereStatementError instance.
        return False

    def get_name_text(self):
        """Return name text."""
        return self._description_string

    def get_name_query_statement_text(self):
        """Return name and position text."""
        return NAME_DELIMITER.join(
            (
                self._description_string,
                self._query_statement_string,
            )
        )

    def get_query_statement_text(self):
        """Return position text."""
        return self._query_statement_string

    def set_database(self, database=None):
        """Set Database instance to which selection rule is applied."""
        self.__database = database
