# enginedbshow.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise show toplevel to show chess engine definition record."""

from solentware_grid.gui.datashow import DataShow

from .enginetoplevel import EngineToplevel
from .topleveltext import ShowText


class EngineDbShow(ShowText, DataShow):
    """Show a chess engine definition from database.

    parent is used as the master argument in an EngineToplevel call.

    ui is used as the ui argument in an EngineToplevel call.

    parent, oldobject, and the EngineToplevel instance created, are used as
    arguments in the super.__init__ call.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "Engine Definition"

    def __init__(self, parent=None, oldobject=None, ui=None):
        """Create toplevel widget for showing chess engine definition.

        ui should be a UCI instance.

        """
        # Toplevel title set '' in __init__ and to proper value in _initialize.
        super().__init__(
            instance=oldobject,
            parent=parent,
            oldview=EngineToplevel(master=parent, ui=ui),
            title="",
        )
        self._initialize()

    def _get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a chess engine definition.

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
        """Return the User Interface EngineListGrid object."""
        return self.ui.base_engines

    @property
    def ui_items_in_toplevels(self):
        """Return the User Interface objects in Toplevels."""
        return self.ui.engines_in_toplevels

    @property
    def ui(self):
        """Return the User Interface object from 'read-only' view."""
        return self.oldview.ui

    @staticmethod
    def _set_item(view, object_):
        """Populate view with the engine definition extracted from object_."""
        view.definition.extract_engine_definition(object_.get_srvalue())
        view.set_engine_definition(object_.value)

    def tidy_on_destroy(self):
        """Clear up after Toplevel destruction."""
        # ui_base_table is None when this happens other than directly closing
        # the Toplevel.
        try:
            super().tidy_on_destroy()
        except AttributeError:
            if self.ui_base_table is not None:
                raise
