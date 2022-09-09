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
# All subclasses use DEFAULT_BINDINGS is _is_text_editable is True.
# Score uses NO_CURRENT_TOKEN, CURRENT_NO_TAGS, and SELECT_VARIATION, which
# other subclasses do not.
# GameEdit uses all the names.
class NonTagBind(enum.Enum):
    """Enumerate the tkinter.Text tag state.

    The tag state is used to control the event bindings for the widget.
    """

    # Current token is a move.
    NO_EDITABLE_TAGS = 1
    NO_CURRENT_TOKEN = 2
    DEFAULT_BINDINGS = 3
    INITIAL_BINDINGS = 4
    CURRENT_NO_TAGS = 5
    # Current token is a move with variations for next move, and the attempt
    # to go to next move was intercepted to choose which one.
    SELECT_VARIATION = 6


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

    def __init__(self, panel, items_manager=None, **ka):
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
            wrap=tkinter.WORD,
        )
        self.scrollbar = tkinter.Scrollbar(
            master=self.panel,
            orient=tkinter.VERTICAL,
            takefocus=tkinter.FALSE,
            command=self.score.yview,
        )
        self.score.configure(yscrollcommand=self.scrollbar.set)

        # Keyboard actions do nothing by default.
        self.set_keypress_binding(switch=False)
        self.set_event_bindings_score(self.get_menubar_events())

        # The popup menus used by all subclasses.
        self.inactive_popup = None
        self.primary_activity_popup = None

    def set_event_bindings_score(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        for sequence, function in bindings:
            self.score.bind(
                sequence[0], ste(function) if switch and function else ""
            )

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
        return ((EventSpec.score_enable_F10_menubar, self.press_none),)

    @staticmethod
    def press_break(event=None):
        """Do nothing and prevent event handling by next handlers."""
        return "break"

    @staticmethod
    def press_none(event=None):
        """Do nothing and allow event to be handled by next handler."""
        return None

    # This method arose when seeking clarity in the way popup menus were set,
    # and replaces lots of 'add_command' calls scattered all over.
    # Long term, either this method or add_cascade_menu_to_popup will do all.
    def set_popup_bindings(self, popup, bindings=(), index=tkinter.END):
        """Insert bindings in popup before index in popup."""
        # Default index is tkinter.END which seems to mean insert at end of
        # popup, not before last entry in popup as might be expected from the
        # way expressed in the 'Tk menu manual page' for index command.  (The
        # manual page describes 'end' in the context of 'none' for 'activate'
        # option.  It does make sense 'end' meaning after existing entries
        # when inserting entries.)

        for accelerator, function in bindings:
            popup.insert_command(
                index=index,
                label=accelerator[1],
                command=self.try_command(function, popup),
                accelerator=accelerator[2],
            )

    @staticmethod
    def give_focus_to_widget(event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return "break"

    @staticmethod
    def get_F10_popup_events(top_left, pointer):
        """Return tuple of event definitions to post popup menus.

        top_left is a method to post the menu at top left corner of widget.
        pointer is a method to post the menu at current pointer location.

        """
        return (
            (EventSpec.score_enable_F10_popupmenu_at_top_left, top_left),
            (EventSpec.score_enable_F10_popupmenu_at_pointer, pointer),
        )

    # Subclasses with database interfaces may override method.
    @staticmethod
    def create_database_submenu(menu):
        """Do nothing.

        Subclasses should override this method as needed.

        """
        # pylint message assignment-from-none is reported when the return
        # value is assigned to a name.
        # The message is not reported if 'return None' is replaced like:
        # none = None
        # return none
        return None

    def post_menu(self, menu, create_menu, allowed=True, event=None):
        """Post the popup menu at current pointer location in widget.

        create_menu creates a popup menu if menu is None.
        event supplies the screen location for popup menu top left corner.
        allowed is True, default, permits display of menu.

        """
        if menu is None:
            menu = create_menu()
        if not allowed:
            return "break"
        menu.tk_popup(*self.score.winfo_pointerxy())

        # So 'Control-F10' does not fire 'F10' (menubar) binding too.
        return "break"

    @staticmethod
    def post_menu_at_top_left(menu, create_menu, allowed=True, event=None):
        """Post the popup menu at top left in widget.

        create_menu creates a popup menu if menu is None.
        event supplies the screen location for popup menu top left corner.
        allowed is True, default, permits display of menu.

        """
        if menu is None:
            menu = create_menu()
        if not allowed:
            return "break"
        menu.tk_popup(event.x_root - event.x, event.y_root - event.y)

        # So 'Shift-F10' does not fire 'F10' (menubar) binding too.
        return "break"

    def is_active_item_mapped(self):
        """Return True if this widget is visible and is the active item."""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return False
        return True

    def bind_for_primary_activity(self, switch=True):
        """Set (switch True) or clear bindings for main actions when active.

        If bool(switch) is true, clear the most recently set bindings first.

        """
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.NO_EDITABLE_TAGS
        self.set_primary_activity_bindings(switch=switch)

    def bind_for_initial_state(self, switch=True):
        """Clear the most recently set bindings if bool(switch) is True.

        Assume not setting new bindings leaves widget in initial state.

        If bool(switch) is False, nothing is done.

        """
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = {
        NonTagBind.NO_EDITABLE_TAGS: bind_for_primary_activity,
        NonTagBind.INITIAL_BINDINGS: bind_for_initial_state,
    }

    def create_primary_activity_popup(self):
        """Create and return popup menu with primary and database commands.

        The primary commands are set by subclasses and should be related
        to their main function.

        By default no database commands are set.  Subclasses should
        override the create_database_submanu method as needed.

        """
        # pylint message access-member-before-definition.
        # Initialize primary_activity_popup moved to blanktext from
        # enginetext module.
        assert self.primary_activity_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_primary_activity_events())
        # pylint message assignment-from-none is false positive.
        # However it is sensible to do an isinstance test.
        database_submenu = self.create_database_submenu(popup)
        if isinstance(database_submenu, tkinter.Menu):
            popup.add_cascade(label="Database", menu=database_submenu)
        self.primary_activity_popup = popup
        return popup

    def get_button_events(self, buttonpress1=None, buttonpress3=None):
        """Return tuple of buttonpress event bindings.

        buttonpress1 and buttonpress3 default to self.press_none().

        """
        if buttonpress1 is None:
            buttonpress1 = self.press_none
        if buttonpress3 is None:
            buttonpress3 = self.press_none
        return self.get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_1, buttonpress1),
            (EventSpec.buttonpress_3, buttonpress3),
        )
