# enginedbedit.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert chess engine definition record.
"""
import tkinter.messagebox

from solentware_grid.gui.dataedit import DataEdit

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .enginetoplevel import EngineToplevel, EngineToplevelEdit
from .topleveltext import EditText


class EngineDbEdit(ExceptionHandler, EditText, DataEdit):
    """Edit chess engine definition on database, or insert a new record.

    parent is used as the master argument in EngineToplevelEdit calls.

    ui is used as the ui argument in EngineToplevelEdit calls.

    newobject, parent, oldobject, and the one or two EngineToplevelEdit
    instances created, are used as arguments in the super.__init__ call.

    showinitial determines whether a EngineToplevelEdit is created for
    oldobject if there is one.

    Attribute text_name provides the name used in widget titles and message
    text.

    Methods get_title_for_object and set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    text_name = "Engine Definition"

    def __init__(
        self, newobject, parent, oldobject, showinitial=True, ui=None
    ):
        """Extend and create toplevel to edit or insert chess engine definition.

        ui should be a UCI instance.

        """
        if not oldobject:
            showinitial = False
        super().__init__(
            newobject,
            parent,
            oldobject,
            EngineToplevelEdit(master=parent, ui=ui),
            "",
            oldview=EngineToplevel(master=parent, ui=ui)
            if showinitial
            else showinitial,
        )
        self.initialize()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a chess engine definition
        object_.

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
        return self.ui.base_engines

    @property
    def ui_items_in_toplevels(self):
        return self.ui.engines_in_toplevels

    @property
    def ui(self):
        return self.newview.ui

    def set_item(self, view, object_):
        view.definition.extract_engine_definition(object_.get_srvalue())
        view.set_engine_definition(object_.value)

    def dialog_ok(self):
        """Update record and return update action response (True for updated).

        Check that database is open and is same one as update action was
        started.

        """
        ed = self.newview.get_name_engine_definition_dict()
        title = (self.get_title_for_object(),)
        if not ed:
            tkinter.messagebox.showerror(
                parent=self.parent,
                title=title,
                message="".join(
                    (
                        "No chess engine definition given.\n\n",
                        "Name of chess engine definition must be ",
                        "first line, and subsequent lines the ",
                        "command to run the engine.",
                    )
                ),
            )
            return False
        self.newobject.value.load(repr(ed))
        if not self.newobject.value.get_engine_command_text():
            tkinter.messagebox.showerror(
                parent=self.parent,
                title=title,
                message="".join(
                    (
                        "No chess engine definition given.\n\n",
                        "Name of chess engine definition must be ",
                        "first line, and subsequent lines the ",
                        "command to run the engine.",
                    )
                ),
            )
            return False
        url = self.newobject.value.engine_url_or_error_message()
        if isinstance(url, str):
            tkinter.messagebox.showerror(
                parent=self.parent, title=title, message=url
            )
            return False
        return super().dialog_ok()

    def tidy_on_destroy(self):
        # ui_base_table is None when this happens other than directly closing
        # the Toplevel.
        try:
            super().tidy_on_destroy()
        except AttributeError:
            if self.ui_base_table is not None:
                raise
