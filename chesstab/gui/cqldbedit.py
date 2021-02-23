# cqldbedit.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit or insert dialogue for Chess Query Language (ChessQL) statement record.
"""
import tkinter

from solentware_misc.workarounds import dialogues

from solentware_grid.gui.dataedit import DataEdit

from .chessexception import ChessException
from .cqldisplay import DialogueCQLDisplay, DialogueCQLEdit


class ChessDBeditCQL(ChessException, DataEdit):
    """Dialog to edit a ChessQL statement on, or insert one into, database.

    The ChessQL statement is in it's own Toplevel widget.

    """

    def __init__(self, newobject, parent, oldobject, showinitial=True, ui=None):
        """Extend and create dialogue to edit or insert ChessQL statement."""
        if oldobject:
            title = ':  '.join((
                'Edit ChessQL statement',
                oldobject.value.get_name_text()))
        else:
            title = 'Insert ChessQL Statement'
            showinitial = False
        self.__title = title.split(':')[0]
        if showinitial:
            showinitial = DialogueCQLDisplay(master=parent, ui=ui)
            if ui is not None:
                ui.partials_in_toplevels.add(showinitial)
            showinitial.cql_statement.process_statement(
                oldobject.get_srvalue())
            showinitial.set_cql_statement()
        newview = DialogueCQLEdit(master=parent, ui=ui)
        if ui is not None:
            ui.partials_in_toplevels.add(newview)
        newview.cql_statement.process_statement(newobject.get_srvalue())
        newview.set_cql_statement()
        super().__init__(
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
            repr(self.newview.get_name_cql_statement_text()))
        if not len(self.newobject.value.get_name_text()):
            if not self.newobject.value.cql_error:
                dialogues.showerror(
                    title=self.__title,
                    message=''.join((
                        "The ChessQL statement has no name.\n\nPlease enter ",
                        "it's name as the first line of text.'")))
            else:
                dialogues.showerror(
                    title=self.__title,
                    message=''.join((
                        "The text does not contain a valid ChessQL ",
                        "statement. ")))
            return False
        elif self.newobject.value.cql_error:
            if tkinter.messagebox.YES != dialogues.askquestion(
                title=self.__title,
                message=''.join((
                    'Confirm request to update ChessQL statement named:\n\n',
                    self.newobject.value.get_name_text(),
                    '\n\non database.\n\n',
                    self.newobject.value.cql_error.get_error_report()))):
                return False
        if self.ui.partial_items.active_item:
            if self.ui.partial_items.active_item.sourceobject is None:
                dialogues.showinfo(
                    title=self.__title,
                    message=''.join((
                        "Cannot use this insert dialogue while the active ",
                        "item in cql queries is one opened by menu action ",
                        "'Position | Partial'.")))
                return False
        return super().dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.partials_in_toplevels.discard(self.oldview)
        self.ui.partials_in_toplevels.discard(self.newview)
        self.ui.base_partials.selection.clear()

    def edit(self, commit=True):
        """Edit the records and refresh widgets.

        The ChessQL query statement update is delegated to the superclass.

        This method updates the foundset calculated from the query.

        """
        if commit:
            self.datasource.dbhome.start_transaction()
        super().edit(commit=False)
        cqls = self.ui.partialpositionds(
            self.ui.base_games.datasource.dbhome,
            self.ui.base_games.datasource.dbset,
            self.ui.base_games.datasource.dbset,
            newrow=None)
        cqls.update_cql_statement_games(self.newobject, commit=False)
        if commit:
            self.datasource.dbhome.commit()
        
    def put(self, commit=True):
        """Insert the records and refresh widgets.

        The ChessQL query statement update is delegated to the superclass.

        This method updates the foundset calculated from the query.

        """
        if commit:
            self.datasource.dbhome.start_transaction()
        super().put(commit=False)
        cqls = self.ui.partialpositionds(
            self.ui.base_games.datasource.dbhome,
            self.ui.base_games.datasource.dbset,
            self.ui.base_games.datasource.dbset,
            newrow=None)
        cqls.update_cql_statement_games(self.newobject, commit=False)
        if commit:
            self.datasource.dbhome.commit()
