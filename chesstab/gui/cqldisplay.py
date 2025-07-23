# cqldisplay.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display Chess Query Language statements.

Add ability to display statements from database.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.gui.dataedit import RecordEdit

import chessql.core.basenode

from ..core.chessrecord import ChessDBrecordPartial
from .cqldisplaybase import CQLDisplayBase


class CQLDisplay(CQLDisplayBase):
    """Extend and link ChessQL statement to database.

    sourceobject - link to database.

    Attribute binding_labels specifies the order navigation bindings appear
    in popup menus.

    Method _insert_item_database allows records to be inserted into a database
    from any CQL widget.

    """

    def _insert_item_database(self, event=None):
        """Add ChessQL statement to database."""
        del event
        if self.ui.partial_items.active_item is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert ChessQL Statement",
                message="No active ChessQL statement to insert into database.",
            )
            return

        # This should see if ChessQL statement with same name already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert ChessQL Statement",
                message="Cannot add ChessQL statement:\n\nNo database open.",
            )
            return

        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert ChessQL Statement",
                message="".join(
                    (
                        "Cannot add ChessQL statement:\n\n",
                        "Partial position list hidden.",
                    )
                ),
            )
            return
        updater = ChessDBrecordPartial()
        self._clear_statement_tags()
        try:
            updater.value.prepare_cql_statement(
                self.get_name_cql_statement_text()
            )
        except chessql.core.basenode.NodeError as exc:
            self._report_statement_error(updater.value, exc)
            return
        title = "Insert ChessQL Statement"
        tname = title.replace("Insert ", "").replace("S", "s")
        if not updater.value.get_name_text():
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "The '",
                        tname,
                        " has no name.\n\nPlease enter it's ",
                        "name as the first line of text.'",
                    )
                ),
            )
            return
        message = [
            "".join(
                (
                    "Confirm request to add ",
                    tname,
                    " named:\n\n",
                    updater.value.get_name_text(),
                    "\n\nto database.\n\n",
                )
            )
        ]
        if not updater.value.cql_error:
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(message),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title=title,
                    message=tname.join(("Add ", " to database abandonned.")),
                )
                return
        else:
            message.append(updater.value.cql_error.get_error_report())
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(message),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title=title,
                    message=tname.join(("Add ", " to database abandonned.")),
                )
                return
        editor = RecordEdit(updater, None)
        editor.set_data_source(source=datasource)
        updater.set_database(editor.get_data_source().dbhome)
        updater.key.recno = None  # 0
        editor.put()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    tname,
                    ' "',
                    updater.value.get_name_text(),
                    '" added to database.',
                )
            ),
        )
