# cqldelete.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Delete Chess Query Language statements.

Add ability to delete statements from database.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from .cql import CQL
from .cqldisplay import CQLDisplay


class CQLDelete(CQLDisplay, CQL, DataNotify):
    """Delete ChessQL statement from database.

    Method _delete_item_database allows records to be deleted from a database.
    """

    def _delete_item_database(self, event=None):
        """Remove ChessQL statement from database."""
        del event
        if self.ui.is_database_update_inhibited():
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="".join(
                    (
                        "Cannot delete ChessQL statement\n\n",
                        "No database open or an import or CQL query ",
                        "is unfinished",
                    )
                ),
            )
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="".join(
                    (
                        "Cannot delete ChessQL statement:\n\n",
                        "ChessQL statement list hidden.",
                    )
                ),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="".join(
                    (
                        "The ChessQL statement to delete has not ",
                        "been given.\n\nProbably because database ",
                        "has been closed and opened since this copy ",
                        "was displayed.",
                    )
                ),
            )
            return
        if self.blockchange:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="\n".join(
                    (
                        "Cannot delete ChessQL statement.",
                        "Record has been amended since this copy displayed.",
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title="Delete ChessQL Statement",
            message="Confirm request to delete ChessQL statement.",
        ):
            return
        self.cql_statement.split_statement(
            "\n".join(
                (
                    self.get_tagged_text(self.TITLE_DATA),
                    self.get_tagged_text(self.TEXT_DATA),
                )
            )
        )
        editor = RecordDelete(self.sourceobject)
        editor.set_data_source(source=datasource)
        datasource.dbhome.mark_cql_statements_evaluated(
            allexceptkey=self.sourceobject.key.recno
        )
        datasource.dbhome.mark_all_games_not_evaluated()
        datasource.dbhome.remove_cql_query_match_list_for_query_key(
            querykey=self.sourceobject.key.recno
        )
        editor.delete()
        datasource.dbhome.clear_cql_queries_pending_evaluation()
        self.refresh_game_list()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title="Delete ChessQL Statement",
            message="".join(
                (
                    'ChessQL statement "',
                    self.sourceobject.value.get_name_text(),
                    '" deleted from database.',
                )
            ),
        )
