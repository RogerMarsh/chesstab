# cqldbdelete.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete toplevel to delete ChessQL statement record.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""
import tkinter

from solentware_grid.gui.datadelete import DataDelete

from .cqltoplevel import CQLToplevel
from .topleveltext import DeleteText


class CQLDbDelete(DeleteText, DataDelete):
    """Delete ChessQL statement from database.

    parent is used as the master argument in a CQLToplevel call.

    ui is used as the ui argument in a CQLToplevel call.

    parent, oldobject, and the CQLToplevel instance created, are used as
    arguments in the super.__init__ call.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "ChessQL Statement"

    def __init__(self, parent=None, oldobject=None, ui=None):
        """Extend and create toplevel widget to delete ChessQL statement."""
        # Toplevel title set '' in __init__ and to proper value in _initialize.
        super().__init__(
            instance=oldobject,
            parent=parent,
            oldview=CQLToplevel(master=parent, ui=ui),
            title="",
        )
        self._initialize()

    def _get_title_for_object(self, object_=None):
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
        """Return the User Interface TagRosterGrid object."""
        return self.ui.base_partials

    @property
    def ui_items_in_toplevels(self):
        """Return the User Interface objects in Toplevels."""
        return self.ui.partials_in_toplevels

    @property
    def ui(self):
        """Return the User Interface object from 'read-only' view."""
        return self.oldview.ui

    @staticmethod
    def _set_item(view, object_):
        """Populate view with the CQL query extracted from object_."""
        view.cql_statement.prepare_cql_statement(object_.get_srvalue())
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
                    title=self._get_title_for_object(),
                    message="".join(
                        (
                            "Cannot use this delete dialogue while the ",
                            "active item in cql queries is one opened by ",
                            "menu action 'Position | Partial'.",
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
                    title=self._get_title_for_object(),
                    message="".join(
                        (
                            "Cannot use this delete dialogue while the ",
                            "active item in cql queries is one that ",
                            "displays the record being deleted.",
                        )
                    ),
                )
                return False
        return super().dialog_ok()

    def delete(self, commit=True):
        """Delegate to superclass to delete record then delete game list.

        If commit evaluates False caller is responsible for evaluating
        CQL queries on the changes.

        """
        dbhome = self.datasource.dbhome
        dbhome.mark_cql_statements_evaluated(
            allexceptkey=self.object.key.recno
        )
        dbhome.mark_all_games_not_evaluated()
        if commit:
            dbhome.remove_cql_query_match_list_for_query_key(
                self.object.key.recno
            )
        super().delete(commit=commit)
        dbhome.clear_cql_queries_pending_evaluation()
