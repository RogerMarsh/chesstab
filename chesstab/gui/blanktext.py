# blanktext.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define tkinter.Text widget to be customized and used within ChessTab.

The positionrow.PositionRow and positionscore.PositionScore classes do not use
this class because their Text widgets come from solentware_grid.gui.DataRow.

"""

import tkinter
import enum

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .eventspec import EventSpec
from .displayitems import DisplayItemsStub


# 'Tag' in these names refers to tags in Tk Text widgets, not PGN tags.
# NO_EDITABLE_TAGS and INITIAL_BINDINGS are used if _is_text_editable is False.
# All the names are used if _is_text_editable is True.
# See score.Score.NonTagBind for a case with more values.
class NonTagBind(enum.Enum):
    NO_EDITABLE_TAGS = 1
    DEFAULT_BINDINGS = 3
    INITIAL_BINDINGS = 4
    

class BlankText(ExceptionHandler):

    """Create Text widget with configuration shared by subclasses.

    The subclasses are cqltext.CQLText, querytext.QueryText, score.Score,
    and enginetext.EngineText.

    panel is used as the master argument for the tkinter Text and Scrollbar
    widgets created to display the statement text.

    items_manager is the ui attribute which tracks which EngineText instance is
    active (as defined by ui).

    Subclasses are responsible for providing a geometry manager.

    Attribute _is_text_editable is False to indicate text cannot be edited.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.
    
    """

    # True means the content can be edited.
    _is_text_editable = False

    # Indicate the most recent set of bindings applied to score attribute.
    # Values are Tk tag names or members of NonTagBind enumeration. 
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def __init__(
        self,
        panel,
        items_manager=None,
        **ka):
        """Create widgets to display chess engine definition."""
        super().__init__(**ka)

        # May be worth using a Null() instance for these two attributes.
        if items_manager is None:
            items_manager = DisplayItemsStub()
        self.items = items_manager

        self.panel = panel
        self.score = tkinter.Text(
            master=self.panel,
            width=0,
            height=0,
            takefocus=tkinter.FALSE,
            undo=True,
            wrap=tkinter.WORD)
        self.scrollbar = tkinter.Scrollbar(
            master=self.panel,
            orient=tkinter.VERTICAL,
            takefocus=tkinter.FALSE,
            command=self.score.yview)
        self.score.configure(yscrollcommand=self.scrollbar.set)

        # Keyboard actions do nothing by default.
        self.set_keypress_binding(switch=False)
        self.set_event_bindings_score(self.get_menubar_events())

        # The popup menus used by all subclasses.
        self.inactive_popup = None
        
    def set_event_bindings_score(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        for sequence, function in bindings:
            self.score.bind(
                sequence[0],
                ste(function) if switch and function else '')

    def set_keypress_binding(self, function=None, bindings=(), switch=True):
        """Set bindings to function if switch is True or disable keypress."""
        if switch and function:
            stef = self.try_event(function)
            for sequence in bindings:
                self.score.bind(sequence[0], stef)
        else:
            stekb = self.try_event(self.press_break)
            for sequence in bindings:
                self.score.bind(sequence[0], stekb)

    def get_menubar_events(self):
        """Return tuple of event binding definitions passed for menubar."""
        return (
            (EventSpec.score_enable_F10_menubar, self.press_none),
            )

    def press_break(self, event=None):
        """Do nothing and prevent event handling by next handlers."""
        return 'break'

    def press_none(self, event=None):
        """Do nothing and allow event to be handled by next handler."""
        return None
