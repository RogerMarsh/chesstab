# cqldbdelete.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete toplevel to delete Chess Query Language (ChessQL) statement
record.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""
from solentware_grid.gui.datadelete import DataDelete
from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .cqltoplevel import CQLToplevel
from .topleveltext import DeleteText


class CQLDbDelete(ExceptionHandler, DeleteText, DataDelete):
    """Delete ChessQL statement from database.

    parent is used as the master argument in a CQLToplevel call.

    ui is used as the ui argument in a CQLToplevel call.

    parent, oldobject, and the CQLToplevel instance created, are used as
    arguments in the super.__init__ call.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods get_title_for_object and set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "ChessQL Statement"

    def __init__(self, parent, oldobject, ui=None):
        """Extend and create toplevel widget to delete ChessQL statement."""
        # Toplevel title set '' in __init__ and to proper value in initialize.
        super().__init__(
            oldobject, parent, CQLToplevel(master=parent, ui=ui), ""
        )
        self.initialize()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a ChessQL statement object_.

        Default value of object_ is object attribute from DataDelete class.

        """
        if object_ is None:
            object_ = self.object
        return "  ".join(
            (
                self.text_name.join(("Delete ", ":")),
                object_.value.get_name_text(),
            )
        )

    @property
    def ui_base_table(self):
        return self.ui.base_partials

    @property
    def ui_items_in_toplevels(self):
        return self.ui.partials_in_toplevels

    @property
    def ui(self):
        return self.oldview.ui

    def set_item(self, view, object_):
        view.cql_statement.process_statement(object_.get_srvalue())
        view.set_and_tag_item_text()

    def dialog_ok(self):
        """Return delete action response (True for deleted).

        Delegate to superclass if the active item on the main display is not a
        'Position | Partial' widget and is not set to edit the same record.

        """
        if self.ui.partial_items.active_item:
            if self.ui.partial_items.active_item.sourceobject is None:
                tkinter.messagebox.showinfo(
                    parent=self.parent,
                    title=self.get_title_for_object(),
                    message="".join(
                        (
                            "Cannot use this delete dialogue while the active ",
                            "item in cql queries is one opened by menu action ",
                            "'Position | Partial'.",
                        )
                    ),
                )
                return False
            if (
                self.ui.partial_items.active_item.sourceobject.key
                == self.object.key
            ):
                tkinter.messagebox.showinfo(
                    parent=self.parent,
                    title=self.get_title_for_object(),
                    message="".join(
                        (
                            "Cannot use this delete dialogue while the active ",
                            "item in cql queries is one that displays the record ",
                            "being deleted.",
                        )
                    ),
                )
                return False
        return super().dialog_ok()

    def delete(self, commit=True):
        """Delegate to superclass to delete record then delete game list."""
        if commit:
            self.datasource.dbhome.start_transaction()
        super().delete(commit=False)
        cqls = self.ui.partialpositionds(
            self.ui.base_games.datasource.dbhome,
            self.ui.base_games.datasource.dbset,
            self.ui.base_games.datasource.dbset,
            newrow=None,
        )
        assert self.object.newrecord is None
        cqls.forget_cql_statement_games(self.object, commit=False)
        if commit:
            self.datasource.dbhome.commit()
