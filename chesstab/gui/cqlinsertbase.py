# cqlinsertbase.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Events for insert Chess Query Language statements."""

from .eventspec import EventSpec
from .cqldisplaybase import CQLDisplayBase


class CQLInsertBaseError(Exception):
    """Exception class fo cqlinsertbase module."""


# Inheriting from CQLDisplayBase retains access to methods in CQLInsert
# hierarchy after splitting CQLInsertBase from CQLInsert; except for
# _process_and_set_cql_statement_list() which must be implemented in a
# subclass.
class CQLInsertBase(CQLDisplayBase):
    """Methods taht set up event handlers for insert CQL statement."""

    def _process_and_set_cql_statement_list(self, event=None):
        """Raise CQLInsertBaseError exception for method not implemented."""
        del event
        raise CQLInsertBaseError(
            "".join(
                (
                    "A subclass must implement ",
                    "'_process_and_set_cql_statement_list' method",
                )
            )
        )

    def _get_list_games_events(self):
        """Return tuple of event bindings to list games for ChessQL rule."""
        return (
            (EventSpec.display_list, self._process_and_set_cql_statement_list),
        )

    def _add_list_games_entry_to_popup(self, popup):
        """Add option to list games for selection rule to popup."""
        self._set_popup_bindings(
            popup, bindings=self._get_list_games_events(), index="Close Item"
        )

    def _set_database_navigation_close_item_bindings(self, switch=True):
        """Delegate then set list games event bindings."""
        super()._set_database_navigation_close_item_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_list_games_events(), switch=switch
        )
