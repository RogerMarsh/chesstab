# cqlupdate.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update Chess Query Language statements.

The CQLUpdate class provides methods to update an existing CQL record.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.gui import dataedit

from . import displaytext
from ..cql import queryevaluator
from ..cql import runcql
from ..core import chessrecord
from ..core import filespec
from . import cqlinsert


class CQLUpdate(displaytext.EditText, cqlinsert.CQLInsert):
    """Update an existing CQL statement database record.

    The list od records matching the statement is also updated.
    """

    def _update_item_database(self, event=None):
        """Modify existing ChessQL statement record."""
        del event
        title = "Edit ChessQL Statement"
        if self.ui.is_database_update_inhibited():
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "Cannot edit ChessQL statement\n\n",
                        "No database open or an import or CQL query ",
                        "is unfinished",
                    )
                ),
            )
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
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
                title=title,
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
                title=title,
                message="\n".join(
                    (
                        "Cannot edit ChessQL statement.",
                        "It has been amended since this copy was displayed.",
                    )
                ),
            )
            return
        # Ignore self.cql_statement except for getting statement text
        # because ChessDBvaluePartial(CQLStatement, ...) will lead to a
        # database update.
        self.cql_statement.split_statement(
            "\n".join(
                (
                    self.get_tagged_text(self.TITLE_DATA),
                    self.get_tagged_text(self.TEXT_DATA),
                )
            )
        )
        if not self.cql_statement.get_name_text():
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "The '",
                        "CQL statement",
                        " has no name.\n\nPlease enter it's ",
                        "name as the first line of text.'",
                    )
                ),
            )
            return
        # The ChessDBvaluePartial with default __init__ arguments is not
        # appropriate here.
        original = chessrecord.ChessDBrecordPartial()
        original.value.dbset = filespec.GAMES_FILE_DEF
        original.value.set_database(database=self.ui.database)
        original.load_record(
            (self.sourceobject.key.recno, self.sourceobject.srvalue)
        )
        updater = chessrecord.ChessDBrecordPartial()
        updater.value.dbset = filespec.GAMES_FILE_DEF
        updater.value.set_database(database=self.ui.database)
        try:
            updater.value.prepare_cql_statement(
                self.get_name_cql_statement_text()
            )
        except queryevaluator.QueryEvaluatorError as exc:
            tag_ranges = self.score.tag_ranges(self.TEXT_DATA)
            evaluator = updater.value.query_container.evaluator
            if evaluator.error_location is not None:
                start = self.score.index(evaluator.error_location)
                if not tag_ranges or len(tag_ranges) > 2:
                    self.score.tag_add(self.ERROR_TAG, start)
                else:
                    self.score.tag_add(
                        self.ERROR_TAG,
                        start,
                        start + str(evaluator.error_length).join("+c"),
                    )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=str(exc),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    "Confirm request to edit CQL statement named:\n\n",
                    updater.value.get_name_text(),
                    "\n\non database\n\n",
                )
            ),
        ):
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message="Add CQL statement to database abandonned",
            )
            return
        editor = dataedit.RecordEdit(updater, original)
        editor.set_data_source(source=datasource)
        updater.set_database(editor.get_data_source().dbhome)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        datasource.dbhome.mark_cql_statements_evaluated(
            allexceptkey=updater.key.recno
        )
        datasource.dbhome.mark_all_games_not_evaluated()
        editor.edit()
        if datasource.dbhome.valid_cql_statements_exist():
            runcql.make_runcql(datasource.dbhome, self.ui, True)
            self.refresh_game_list(key_recno=updater.key.recno)
        else:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(
                    (
                        'CQL statement "',
                        updater.value.get_name_text(),
                        '" amended on database.',
                    )
                ),
            )
