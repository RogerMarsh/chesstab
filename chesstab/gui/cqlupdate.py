# cqlupdate.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update Chess Query Language statements.

The CQLUpdate class provides methods to update an existing CQL record.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.gui.dataedit import RecordEdit

import chessql.core.basenode

from ..core.chessrecord import ChessDBrecordPartial
from .displaytext import EditText
from .cqlinsert import CQLInsert


class CQLUpdate(EditText, CQLInsert):
    """Update an existing CQL statement database record.

    The list od records matching the statement is also updated.
    """

    def _update_item_database(self, event=None):
        """Modify existing ChessQL statement record."""
        del event
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit ChessQL Statement",
                message="Cannot edit ChessQL statement:\n\nNo database open.",
            )
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit ChessQL Statement",
                message="".join(
                    (
                        "Cannot edit ChessQL statement:\n\n",
                        "Partial position list hidden.",
                    )
                ),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit ChessQL Statement",
                message="".join(
                    (
                        "The ChessQL statement to edit has not ",
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
                title="Edit ChessQL Statement",
                message="\n".join(
                    (
                        "Cannot edit ChessQL statement.",
                        "It has been amended since this copy was displayed.",
                    )
                ),
            )
            return
        original = ChessDBrecordPartial()
        original.load_record(
            (self.sourceobject.key.recno, self.sourceobject.srvalue)
        )

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        updater = ChessDBrecordPartial()

        self._clear_statement_tags()
        try:
            updater.value.prepare_cql_statement(
                self.get_name_cql_statement_text()
            )
        except chessql.core.basenode.NodeError as exc:
            self._report_statement_error(updater.value, exc)
            return
        title = "Edit ChessQL Statement"
        tname = title.replace("Edit ", "").replace("S", "s")
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
                    "Confirm request to edit ",
                    tname,
                    " named:\n\n",
                    updater.value.get_name_text(),
                    "\n\non database.\n\n",
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
                    message=tname.join(("Edit ", " on database abandonned.")),
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
                    message=tname.join(("Edit ", " on database abandonned.")),
                )
                return
        editor = RecordEdit(updater, original)
        editor.set_data_source(source=datasource)
        updater.set_database(editor.get_data_source().dbhome)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        editor.edit()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    tname,
                    ' "',
                    updater.value.get_name_text(),
                    '" amended on database.',
                )
            ),
        )
