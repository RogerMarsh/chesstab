# querydbedit.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit dialogue to edit or insert game selection rule record.
"""

import tkinter.messagebox

from solentware_misc.workarounds import dialogues

from solentware_grid.gui.dataedit import DataEdit

from .chessexception import ChessException
from .querydisplay import DialogueQueryDisplay, DialogueQueryEdit


class ChessDBeditQuery(ChessException, DataEdit):
    """Dialog to edit a game selection rule on, or insert one into, database.

    The game selection rule is in it's own Toplevel widget.

    """

    def __init__(self, newobject, parent, oldobject, showinitial=True, ui=None):
        """Extend and create dialogue to edit or insert selection rule."""
        if oldobject:
            title = ':  '.join((
                'Edit Selection Rule',
                oldobject.value._description_string))
        else:
            title = 'Insert Selection Rule'
            showinitial = False
        self.__title = title.split(':')[0]
        if showinitial:
            showinitial = DialogueQueryDisplay(master=parent, ui=ui)
            if ui is not None:
                ui.selections_in_toplevels.add(showinitial)
                showinitial.query_statement.set_database(
                    ui.base_games.datasource.dbhome)
                showinitial.query_statement.dbset = (
                    ui.base_games.datasource.dbset)
            showinitial.query_statement.process_query_statement(
                oldobject.get_srvalue())
            showinitial.set_query_statement()
        newview = DialogueQueryEdit(master=parent, ui=ui)
        if ui is not None:
            ui.selections_in_toplevels.add(newview)
            newview.query_statement.set_database(
                ui.base_games.datasource.dbhome)
            newview.query_statement.dbset = ui.base_games.datasource.dbset
        newview.query_statement.process_query_statement(newobject.get_srvalue())
        newview.set_query_statement()
        super(ChessDBeditQuery, self).__init__(
            newobject,
            parent,
            oldobject,
            newview,
            title,
            oldview=showinitial,
            )

        # Bind only to newview.score because it alone takes focus.
        self.bind_buttons_to_widget(newview.score)

        self.ui = ui
        
    def dialog_ok(self):
        """Update record and return update action response (True for updated).

        Check that database is open and is same one as update action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text='Cannot update because not connected to a database')
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        self.newobject.value.load(
            repr(self.newview.get_name_query_statement_text()))
        if not len(self.newobject.value.get_name_text()):
            dialogues.showerror(
                title=self.__title,
                message=''.join((
                    "The selection rule has no name.\n\nPlease enter it's ",
                    "name as the first line of text.'")))
            return False
        if self.newobject.value.where_error:
            if tkinter.messagebox.YES != dialogues.askquestion(
                title=self.__title,
                message=''.join((
                    'Confirm request to update game selection rule named:\n\n',
                    self.newobject.value.get_name_text(),
                    '\n\non database.\n\n',
                    self.newobject.value.where_error.get_error_report(
                        self.ui.base_games.get_data_source())))):
                return False
        return super(ChessDBeditQuery, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.selections_in_toplevels.discard(self.oldview)
        self.ui.selections_in_toplevels.discard(self.newview)
        self.ui.base_selections.selection.clear()
