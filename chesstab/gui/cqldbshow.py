# cqldbshow.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise show toplevel to display Chess Query Language (ChessQL) statement
record.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""

from solentware_grid.gui.datashow import DataShow

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .cqltoplevel import CQLToplevel
from .topleveltext import ShowText


class CQLDbShow(ExceptionHandler, ShowText, DataShow):
    """Show ChessQL statement from database.

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
        """Extend and create toplevel widget to display ChessQL statement."""
        # Toplevel title set '' in __init__ and to proper value in initialize.
        super().__init__(
            oldobject, parent, CQLToplevel(master=parent, ui=ui), ""
        )
        self.initialize()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a ChessQL statement object_.

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
