# enginetoplevel.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Toplevel widgets to display and edit chess engine definitions.

These two classes display chess engine definitions in their own Toplevel
widget: they are used in the enginedbdelete, enginedbedit, and enginedbshow,
modules.

"""

from .engine import Engine
from .engineedit import EngineEdit
from .topleveltext import ToplevelText


class EngineToplevel(ToplevelText, Engine):

    """Customize Engine to be the single instance in a Toplevel widget."""


class EngineToplevelEdit(ToplevelText, EngineEdit):

    """Customize EngineEdit to be the single instance in a Toplevel widget."""

    # A method like GameToplevelEdit.create_primary_activity_popup is not
    # needed because the standard edit operations of Text widget are
    # sufficient.
