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

    def press_break(self, event=None):
        """Do nothing and prevent event handling by next handlers."""
        return "break"

    def press_none(self, event=None):
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

    def give_focus_to_widget(self, event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return "break"

    def get_F10_popup_events(self, top_left, pointer):
        """Return tuple of event definitions to post popup menus at top left
        of focus widget and at pointer location within application widget.

        top_left and pointer are functions.

        """
        return (
            (EventSpec.score_enable_F10_popupmenu_at_top_left, top_left),
            (EventSpec.score_enable_F10_popupmenu_at_pointer, pointer),
        )

    # Subclasses with database interfaces may override method.
    def create_database_submenu(self, menu):
        return None

    def post_menu(self, menu, create_menu, allowed=True, event=None):
        if menu is None:
            menu = create_menu()
        if not allowed:
            return "break"
        menu.tk_popup(*self.score.winfo_pointerxy())

        # So 'Control-F10' does not fire 'F10' (menubar) binding too.
        return "break"

    def post_menu_at_top_left(
        self, menu, create_menu, allowed=True, event=None
    ):
        if menu is None:
            menu = create_menu()
        if not allowed:
            return "break"
        menu.tk_popup(event.x_root - event.x, event.y_root - event.y)

        # So 'Shift-F10' does not fire 'F10' (menubar) binding too.
        return "break"

    def is_active_item_mapped(self):
        """ """
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
        assert self.primary_activity_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_primary_activity_events())
        database_submenu = self.create_database_submenu(popup)
        if database_submenu:
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

    # Take a snapshot of the tkinter.Text widget bound to self.score.  It is
    # intended for problem tracing.  It is saved as a sibling of ErrorLog.
    # At a convenient time dump_text_widget will become a method in the
    # solentware_misc.gui.exceptionhandler.ExceptionHandler class.
    def dump_text_widget(self, textwidget, filename=None):
        if filename is None:
            filename = "dumptextwidget"
        import os
        import datetime

        filename = "_".join(
            (
                filename,
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
        )
        with open(
            os.path.join(
                os.path.dirname(self.get_error_file_name()), filename
            ),
            "w",
        ) as f:
            for t in textwidget.dump("1.0", tkinter.END):
                f.write(repr(t) + "\n")
