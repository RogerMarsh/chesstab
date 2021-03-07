# enginetext.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a chess engine definition.
"""

import tkinter
import tkinter.messagebox
from urllib.parse import urlsplit
import enum

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from ..core.engine import Engine
from .eventspec import EventSpec
from .displayitems import DisplayItemsStub


# 'Tag' in these names refers to tags in Tk Text widgets, not PGN tags.
# EngineText uses NO_EDITABLE_TAGS and INITIAL_BINDINGS.
# EngineEdit uses all the names.
# See Score.NonTagBind for the apparently missing values.
class NonTagBind(enum.Enum):
    NO_EDITABLE_TAGS = 1
    DEFAULT_BINDINGS = 3
    INITIAL_BINDINGS = 4
    

class EngineText(ExceptionHandler):

    """Chess engine definition widget.

    panel is used as the master argument for the tkinter Text and Scrollbar
    widgets created to display the statement text.

    ui is the user interface manager for an instance of EngineText, usually an
    instance of ChessUI.

    items_manager is the ui attribute which tracks which EngineText instance is
    active (as defined by ui).

    itemgrid is the ui reference to the DataGrid from which the record was
    selected.

    Subclasses are responsible for providing a geometry manager.

    Attribute _is_definition_editable is False meaning the statement cannot be
    edited.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    
    """

    # True means engine definition can be edited
    _is_definition_editable = False

    # Indicate the most recent set of bindings applied to score attribute.
    # Values are Tk tag names or members of NonTagBind enumeration. 
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def __init__(
        self,
        panel,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Create widgets to display chess engine definition."""
        super(EngineText, self).__init__(**ka)
        self.ui = ui

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

        # The popup menus for the engine definition.
        self.active_popup = None
        self.inactive_popup = None

        # Selection rule parser instance to process text.
        self.definition = Engine()

    def set_popup_bindings(self, popup, bindings=()):
        for accelerator, function in bindings:
            popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, popup),
                accelerator=accelerator[2])
        
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
        """No nothing and prevent event handling by next handlers."""
        return 'break'

    def press_none(self, event=None):
        """Do nothing and allow event to be handled by next handler."""
        return None
        
    def bind_for_active(self, switch=True):
        """Set keyboard bindings and popup menu for non-editing actions.

        Method exists for compatibility with score.Score way of doing things.

        The Text widget contains two tokens, the chess engine definition name
        and the definition.  Both tokens are editable, or both are not, and
        the standard Text widget operations are available when editable.

        """
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.NO_EDITABLE_TAGS
        self.set_active_bindings(switch=switch)
        
    def bind_for_initial_state(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.INITIAL_BINDINGS
        
    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = {
        NonTagBind.NO_EDITABLE_TAGS: bind_for_active,
        NonTagBind.INITIAL_BINDINGS: bind_for_initial_state,
        }

    def give_focus_to_widget(self, event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return 'break'
        
    # Not sure what events these are yet; or if name is best.
    # Remove '_navigation'?
    # Engine description records are always shown in a Toplevel.
    # Dismiss item and database update actions by keypress and buttunpress
    # are assumed to be exposed by the associated solentware_misc class.
    def get_active_navigation_events(self):
        return (
            (EventSpec.databaseenginedisplay_run, self.run_engine),
            )

    # Engine description records are always shown in a Toplevel.
    # The methods where get_inactive_events() is used are never used.
    def get_inactive_events(self):
        return (
            (EventSpec.display_make_active, self.set_focus_panel_item_command),
            (EventSpec.display_dismiss_inactive, self.delete_item_view),
            )

    def get_F10_popup_events(self, top_left, pointer):
        """Return tuple of event definitions to post popup menus at top left
        of focus widget and at pointer location within application widget.

        top_left and pointer are functions.

        """
        return (
            (EventSpec.score_enable_F10_popupmenu_at_top_left, top_left),
            (EventSpec.score_enable_F10_popupmenu_at_pointer, pointer),
            )

    # The default Text widget bindings are probably what is wanted.
    def get_modifier_buttonpress_suppression_events(self):
        """Return tuple of event binding definitions suppressing buttonpress
        with Control, Shift, or Alt."""
        return ()

    def get_active_button_events(self):
        return self.get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_3, self.post_active_menu),
            )

    def set_active_bindings(self, switch=True):
        """Switch bindings for editing chess engine definition on or off."""
        self.set_event_bindings_score(
            self.get_active_navigation_events(),
            switch=switch)
        self.set_event_bindings_score(
            self.get_F10_popup_events(self.post_active_menu_at_top_left,
                                      self.post_active_menu),
            switch=switch)
        self.set_event_bindings_score(
            self.get_active_button_events(),
            switch=switch)
        
    # Subclasses with database interfaces may override method.
    def create_database_submenu(self, menu):
        return None
        
    def create_active_popup(self):
        assert self.active_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_active_navigation_events())
        database_submenu = self.create_database_submenu(popup)
        if database_submenu:
            popup.add_cascade(label='Database', menu=database_submenu)
        self.active_popup = popup
        return popup
        
    # Engine description records are always shown in a Toplevel.
    # create_inactive_popup() is never used.
    def create_inactive_popup(self):
        assert self.inactive_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_inactive_events())
        self.inactive_popup = popup
        return popup
        
    def post_menu(self,
                  menu, create_menu,
                  allowed=True,
                  event=None):
        if menu is None:
            menu = create_menu()
        if not allowed:
            return 'break'
        menu.tk_popup(*self.score.winfo_pointerxy())

        # So 'Control-F10' does not fire 'F10' (menubar) binding too.
        return 'break'
        
    def post_menu_at_top_left(self,
                              menu,
                              create_menu,
                              allowed=True,
                              event=None):
        if menu is None:
            menu = create_menu()
        if not allowed:
            return 'break'
        menu.tk_popup(event.x_root-event.x, event.y_root-event.y)

        # So 'Shift-F10' does not fire 'F10' (menubar) binding too.
        return 'break'
        
    def post_active_menu(self, event=None):
        """Show the popup menu for chess engine definition navigation."""
        return self.post_menu(
            self.active_popup,
            self.create_active_popup,
            allowed=self.is_active_item_mapped(),
            event=event)
        
    def post_active_menu_at_top_left(self, event=None):
        """Show the popup menu for chess engine definition navigation."""
        return self.post_menu_at_top_left(
            self.active_popup,
            self.create_active_popup,
            allowed=self.is_active_item_mapped(),
            event=event)
        
    def post_inactive_menu(self, event=None):
        """Show the popup menu for a chess engine definition in an inactive
        item."""
        return self.post_menu(
            self.inactive_popup, self.create_inactive_popup, event=event)
        
    def post_inactive_menu_at_top_left(self, event=None):
        """Show the popup menu for a chess engine definition in an inactive
        item."""
        return self.post_menu_at_top_left(
            self.inactive_popup, self.create_inactive_popup, event=event)
        
    def is_active_item_mapped(self):
        """"""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return False
        return True
        
    def set_engine_definition(self, reset_undo=False):
        """Display the chess engine definition as text.
        
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of an engine definition for editing so that repeated
        Ctrl-Z in text editing mode recovers the original engine definition.
        
        """
        if not self._is_definition_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_engine_definition()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_active()
        if not self._is_definition_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()
        
    def set_statusbar_text(self):
        """Set status bar to display chess engine definition name."""
        #self.ui.statusbar.set_status_text(self.definition.get_name_text())

    def get_name_engine_definition_dict(self):
        """Extract chess engine definition from Text widget."""
        e = Engine()
        if e.extract_engine_definition(
            self.score.get('1.0', tkinter.END).strip()):
            return e.__dict__
        return {}

    def map_engine_definition(self):
        """Insert chess engine definition in Text widget.

        Method name arises from development history: the source class tags
        inserted text extensively and this method name survived the cull.

        """
        # No mapping of tokens to text in widget (yet).
        self.score.insert(tkinter.INSERT,
                          self.definition.get_name_engine_command_text())

    def run_engine(self, event=None):
        """Run chess engine."""

        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under Wine on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        #if self.ui.uci.uci_drivers_reply is None:
        #    tkinter.messagebox.showinfo(
        #        parent=self.panel,
        #        title='Chesstab Restriction',
        #        message=' '.join(
        #            ('Starting an UCI chess engine is not allowed because',
        #             'an interface cannot be created:',
        #             'this is expected if running under Wine.')))
        #    return

        url = urlsplit(self.definition.get_engine_command_text())
        try:
            url.port
        except ValueError as exc:
            tkinter.messagebox.showerror(
                parent=self.panel,
                title='Run Engine',
                message=''.join(('The port in the chess engine definition is ',
                                 'invalid.\n\n',
                                 'The reported error for the port is:\n\n',
                                 str(exc),
                                 'but neither hostname nor port may be given ',
                                 'here.\n',
                                 )))
            return
        if not self.definition.get_engine_command_text():
            tkinter.messagebox.showinfo(
                parent=self.panel,
                title='Run Engine',
                message=''.join((
                    'The engine definition does not have a command to ',
                    'run chess engine.',
                    )))
            return
        elif url.port or url.hostname:
            tkinter.messagebox.showinfo(
                parent=self.panel,
                title='Run Engine',
                message=''.join(
                    ('Neither hostname nor port may be given here.\n',
                     "Hostname is: '", url.hostname, "'.\n\n",
                     "Port is: '", url.port, "'.\n",
                     )))
            return
        elif not self.definition.is_run_engine_command():
            tkinter.messagebox.showinfo(
                parent=self.panel,
                title='Run Engine',
                message=''.join((
                    'The engine definition command to run a chess engine ',
                    'does not name a file.',
                    )))
            return
        command = self.definition.get_engine_command_text().split(' ', 1)
        if len(command) == 1:
            self.ui.run_engine(command[0])
        else:
            self.ui.run_engine(command[0], args=command[1].strip())
