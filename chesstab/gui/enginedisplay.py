# enginedisplay.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit chess engine definitions.

These three classes display chess engine definitions in their own Toplevel
widget: they are used in the enginedbdelete, enginedbedit, and enginedbshow,
modules.

The EngineDialogue class binds events to navigate between widgets.

The DialogueEngineDisplay class adds insert and delete record to the
EngineDialogue class.

The DialogueEngineEdit class adds insert and edit record to the
EngineDialogue class.

"""

from .engine import Engine
from .engineedit import EngineEdit
from .chessexception import ChessException


class EngineDialogue(ChessException):
    
    """Manage UI interaction with database for a displayed engine definition.

    Subclasses provide the widget to display the engine definition.
    
    """

    # Formally the same as GameDialogue in gamedisplay module.
    # Follow whatever style of assignment is used there if this binding_labels
    # needs to be non-empty.
    binding_labels = tuple()

    def initialize_bindings(self):
        """Enable all bindings."""
        self.bind_for_viewmode()
        self.bind_pointer_for_viewmode_popup()


class DialogueEngineDisplay(Engine, EngineDialogue):
    
    """Display an engine definition from a database allowing delete and insert.
    """

    def __init__(self, **ka):
        """Extend and link chess engine definition to database.
        """
        super(DialogueEngineDisplay, self).__init__(**ka)
        self.initialize_bindings()


class DialogueEngineEdit(EngineEdit, EngineDialogue):
    
    """Display an engine definition from a database allowing edit and insert.
    """

    def __init__(self, **ka):
        """Extend and link engine definition to database.

        """
        super(DialogueEngineEdit, self).__init__(**ka)
        self.initialize_bindings()
