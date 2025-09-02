# cqlinsertbase.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Events for insert Chess Query Language statements."""

from .cqldisplaybase import CQLDisplayBase


class CQLInsertBaseError(Exception):
    """Exception class fo cqlinsertbase module."""


# Inheriting from CQLDisplayBase retains access to methods in CQLInsert
# hierarchy after splitting CQLInsertBase from CQLInsert; except for
# _process_and_set_cql_statement_list() which must be implemented in a
# subclass.
# _process_and_set_cql_statement_list() is now not used and deleted.
class CQLInsertBase(CQLDisplayBase):
    """Methods taht set up event handlers for insert CQL statement."""

    def _add_list_games_entry_to_popup(self, popup):
        """Do nothing.

        Calculating the list for temporary display is too expensive now.
        """
