# cqlinsert.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Insert Chess Query Language statements.

The CQLInsert class provides methods to insert a new CQL record.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.core.dataclient import DataNotify

import chessql.core.basenode

from .cqledit import CQLEdit
from .displaytext import (
    InsertText,
    ListGamesText,
)
from .cqlinsertbase import CQLInsertBase
from .cqldisplay import CQLDisplay


class CQLInsert(
    CQLInsertBase, ListGamesText, InsertText, CQLDisplay, CQLEdit, DataNotify
):
    """Update an existing CQL statement database record.

    The list od records matching the statement is also updated.

    Listing games for ChessQL statements is different to selection rule
    statements because selection rules share the listing area with the Game
    and Index options to the Select menu.  Index opens up the 'Move to' and
    Filter options too.  A definite user action is always required to generate
    game lists for selection rules, in addition to navigating to (giving focus
    to) the selection rule.  The area where ChessQL game lists are shown is
    dedicated to ChessQL statements.
    """

    def _process_and_set_cql_statement_list(self, event=None):
        """Display games with position matching edited ChessQL statement."""
        del event
        title = "List CQL Statement"
        self._clear_statement_tags()
        try:
            self.cql_statement.prepare_cql_statement(
                self.get_name_cql_statement_text()
            )
        except (
            chessql.core.basenode.NodeError,
            chessql.core.parameters.CQLParameterError,
        ) as exc:
            self._report_statement_error(self.cql_statement, exc)
            return "break"
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message="CQL statement is valid\n\nRun and list games",
        ):
            return "break"
        try:
            self.refresh_game_list(ignore_sourceobject=True)
        except AttributeError as exc:
            if str(exc) == "'NoneType' object has no attribute 'answer'":
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement, ",
                        "probably because an 'empty square' is in the query ",
                        "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                        str(exc),
                    )
                )
            else:
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement:\n\n",
                        "The reported error is:\n\n",
                        str(exc),
                    )
                )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=msg,
            )
        return "break"
