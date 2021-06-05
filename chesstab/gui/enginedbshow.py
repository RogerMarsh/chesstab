# enginedbshow.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise show toplevel to show chess engine definition record.
"""

from solentware_grid.gui.datashow import DataShow

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .enginetoplevel import EngineToplevel
from .topleveltext import ShowText


class EngineDbShow(ExceptionHandler, ShowText, DataShow):
    """Show a chess engine definition from database.

    parent is used as the master argument in an EngineToplevel call.

    ui is used as the ui argument in an EngineToplevel call.

    parent, oldobject, and the EngineToplevel instance created, are used as
    arguments in the super.__init__ call.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods get_title_for_object and set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "Engine Definition"

    def __init__(self, parent, oldobject, ui=None):
        """Create toplevel widget for showing chess engine definition.

        ui should be a UCI instance.

        """
        # Toplevel title set '' in __init__ and to proper value in initialize.
        super().__init__(
            oldobject, parent, EngineToplevel(master=parent, ui=ui), ""
        )
        self.initialize()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a chess engine definition
        object_.

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
        return self.ui.base_engines

    @property
    def ui_items_in_toplevels(self):
        return self.ui.engines_in_toplevels

    @property
    def ui(self):
        return self.oldview.ui

    def set_item(self, view, object_):
        view.definition.extract_engine_definition(object_.get_srvalue())
        view.set_engine_definition(object_.value)

    def tidy_on_destroy(self):
        # ui_base_table is None when this happens other than directly closing
        # the Toplevel.
        try:
            super().tidy_on_destroy()
        except AttributeError:
            if self.ui_base_table is not None:
                raise
