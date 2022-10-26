# querydbedit.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert game selection rule record."""
import tkinter.messagebox

from solentware_grid.gui.dataedit import DataEdit

from .querytoplevel import QueryToplevel, QueryToplevelEdit
from .topleveltext import EditText


class QueryDbEdit(EditText, DataEdit):
    """Edit game selection rule on database, or insert a new record.

    parent is used as the master argument in QueryToplevel calls.

    ui is used as the ui argument in QueryToplevel calls.

    newobject, parent, oldobject, and the one or two QueryToplevel instances
    created, are used as arguments in the super.__init__ call.

    showinitial determines whether a QueryToplevel is created for oldobject if
    there is one.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "Selection Rule Statement"

    def __init__(
        self,
        newobject=None,
        parent=None,
        oldobject=None,
        showinitial=True,
        ui=None,
    ):
        """Extend and create toplevel to edit or insert selection rule."""
        if not oldobject:
            showinitial = False
        super().__init__(
            newobject=newobject,
            parent=parent,
            oldobject=oldobject,
            newview=QueryToplevelEdit(master=parent, ui=ui),
            title="",
            oldview=QueryToplevel(master=parent, ui=ui)
            if showinitial
            else showinitial,
        )
        if ui is not None:
            nqs = self.newview.query_statement
            nqs.set_database(ui.base_games.datasource.dbhome)
            nqs.dbset = ui.base_games.datasource.dbset
            if showinitial:
                oqs = self.oldview.query_statement
                oqs.set_database(ui.base_games.datasource.dbhome)
                oqs.dbset = ui.base_games.datasource.dbset
        self._initialize()

    def _get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a selection rule object_.

        Default value of object_ is object attribute from DataShow class.

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
        return "".join(("Insert ", self.text_name))

    @property
    def ui_base_table(self):
        """Return the User Interface QueryGrid object."""
        return self.ui.base_selections

    @property
    def ui_items_in_toplevels(self):
        """Return the User Interface objects in Toplevels."""
        return self.ui.selections_in_toplevels

    @property
    def ui(self):
        """Return the User Interface object from 'editable' view."""
        return self.newview.ui

    @staticmethod
    def _set_item(view, object_):
        """Populate view with the query extracted from object_."""
        view.query_statement.process_query_statement(object_.get_srvalue())
        view.set_and_tag_item_text(reset_undo=True)

    def dialog_ok(self):
        """Return update action response (True for deleted).

        Delegate to superclass if the game selection rule is a valid statement
        or confirmation has been given for an invalid statement.

        """
        title = self._get_title_for_object()
        self.newobject.value.load(
            repr(self.newview.get_name_query_statement_text())
        )
        if not self.newobject.value.get_name_text():
            tkinter.messagebox.showerror(
                parent=self.parent,
                title=title,
                message="".join(
                    (
                        "The selection rule has no name.\n\nPlease enter ",
                        "it's name as the first line of text.'",
                    )
                ),
            )
            return False
        if self.newobject.value.where_error:
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.parent,
                title=title,
                message="".join(
                    (
                        "Confirm request to update game selection rule ",
                        "named:\n\n",
                        self.newobject.value.get_name_text(),
                        "\n\non database.\n\n",
                        self.newobject.value.where_error.get_error_report(
                            self.ui.base_games.get_data_source()
                        ),
                    )
                ),
            ):
                return False
        return super().dialog_ok()
