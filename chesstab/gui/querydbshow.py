# querydbshow.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise show toplevel to show game selection rule record."""

from solentware_grid.gui.datashow import DataShow

from .querytoplevel import QueryToplevel
from .topleveltext import ShowText


class QueryDbShow(ShowText, DataShow):
    """Show a game selection rule from database.

    parent is used as the master argument in a QueryToplevel call.

    ui is used as the ui argument in a QueryToplevel call.

    parent, oldobject, and the QueryToplevel instance created, are used as
    arguments in the super.__init__ call.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "Selection Rule Statement"

    def __init__(self, parent=None, oldobject=None, ui=None):
        """Extend and create toplevel widget to display game selection rule."""
        # Toplevel title set '' in __init__ and to proper value in _initialize.
        super().__init__(
            instance=oldobject,
            parent=parent,
            oldview=QueryToplevel(master=parent, ui=ui),
            title="",
        )
        if ui is not None:
            self.oldview.query_statement.set_database(
                ui.base_games.datasource.dbhome
            )
            self.oldview.query_statement.dbset = ui.base_games.datasource.dbset
        self._initialize()

    def _get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a selection rule object_.

        Default value of object_ is object attribute from DataShow class.

        """
        if object_ is None:
            object_ = self.object
        return "  ".join(
            (
                self.text_name.join(("Show ", ":")),
                object_.value.get_name_text(),
            )
        )

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
        """Return the User Interface object from 'read-only' view."""
        return self.oldview.ui

    @staticmethod
    def _set_item(view, object_):
        """Populate view with the query extracted from object_."""
        view.query_statement.process_query_statement(object_.get_srvalue())
        view.set_and_tag_item_text()
