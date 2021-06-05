# cqldbedit.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert Chess Query Language (ChessQL)
statement record.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""
import tkinter.messagebox

from solentware_grid.gui.dataedit import DataEdit
from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .cqltoplevel import CQLToplevel, CQLToplevelEdit
from .topleveltext import EditText


class CQLDbEdit(ExceptionHandler, EditText, DataEdit):
    """Edit ChessQL statement on database, or insert a new record.

    parent is used as the master argument in CQLToplevel calls.

    ui is used as the ui argument in CQLToplevel calls.

    newobject, parent, oldobject, and the one or two CQLToplevel instances
    created, are used as arguments in the super.__init__ call.

    showinitial determines whether a CQLToplevel is created for oldobject if
    there is one.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods get_title_for_object and set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "ChessQL Statement"

    def __init__(
        self, newobject, parent, oldobject, showinitial=True, ui=None
    ):
        """Extend and create toplevel to edit or insert ChessQL statement."""
        if not oldobject:
            showinitial = False
        super().__init__(
            newobject,
            parent,
            oldobject,
            CQLToplevelEdit(master=parent, ui=ui),
            "",
            oldview=CQLToplevel(master=parent, ui=ui)
            if showinitial
            else showinitial,
        )
        self.initialize()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a ChessQL statement object_.

        Default value of object_ is oldobject attribute from DataEdit class.

        """
        if object_ is None:
            object_ = self.oldobject
        if object_:
            return "  ".join(
                (
                    self.text_name.join(("Edit ", ":")),
                    object_.value.get_name_text(),
                )
            )
        else:
            return "".join(("Insert ", self.text_name))

    @property
    def ui_base_table(self):
        return self.ui.base_partials

    @property
    def ui_items_in_toplevels(self):
        return self.ui.partials_in_toplevels

    @property
    def ui(self):
        return self.newview.ui

    def set_item(self, view, object_):
        view.cql_statement.process_statement(object_.get_srvalue())
        view.set_and_tag_item_text(reset_undo=True)

    def dialog_ok(self):
        """Return update action response (True for deleted).

        Delegate to superclass if the active item on the main display is not a
        'Position | Partial' widget and contains a valid statement.

        """
        self.newobject.value.load(
            repr(self.newview.get_name_cql_statement_text())
        )
        title = self.get_title_for_object()
        if not len(self.newobject.value.get_name_text()):
            if not self.newobject.value.cql_error:
                tkinter.messagebox.showerror(
                    parent=self.parent,
                    title=title,
                    message="".join(
                        (
                            "The ChessQL statement has no name.\n\nPlease enter ",
                            "it's name as the first line of text.'",
                        )
                    ),
                )
            else:
                tkinter.messagebox.showerror(
                    parent=self.parent,
                    title=title,
                    message="".join(
                        (
                            "The text does not contain a valid ChessQL ",
                            "statement. ",
                        )
                    ),
                )
            return False
        elif self.newobject.value.cql_error:
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.parent,
                title=title,
                message="".join(
                    (
                        "Confirm request to update ChessQL statement named:\n\n",
                        self.newobject.value.get_name_text(),
                        "\n\non database.\n\n",
                        self.newobject.value.cql_error.get_error_report(),
                    )
                ),
            ):
                return False
        if self.ui.partial_items.active_item:
            if self.ui.partial_items.active_item.sourceobject is None:
                tkinter.messagebox.showinfo(
                    parent=self.parent,
                    title=title,
                    message="".join(
                        (
                            "Cannot use this insert dialogue while the active ",
                            "item in cql queries is one opened by menu action ",
                            "'Position | Partial'.",
                        )
                    ),
                )
                return False
        return super().dialog_ok()

    def edit(self, commit=True):
        """Delegate to superclass to edit record then update game list."""
        if commit:
            self.datasource.dbhome.start_transaction()
        super().edit(commit=False)
        cqls = self.ui.partialpositionds(
            self.ui.base_games.datasource.dbhome,
            self.ui.base_games.datasource.dbset,
            self.ui.base_games.datasource.dbset,
            newrow=None,
        )
        cqls.update_cql_statement_games(self.newobject, commit=False)
        if commit:
            self.datasource.dbhome.commit()

    def put(self, commit=True):
        """Delegate to superclass to insert record then insert game list."""
        if commit:
            self.datasource.dbhome.start_transaction()
        super().put(commit=False)
        cqls = self.ui.partialpositionds(
            self.ui.base_games.datasource.dbhome,
            self.ui.base_games.datasource.dbset,
            self.ui.base_games.datasource.dbset,
            newrow=None,
        )
        cqls.update_cql_statement_games(self.newobject, commit=False)
        if commit:
            self.datasource.dbhome.commit()
