# enginetext.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a chess engine definition.
"""

import tkinter
import tkinter.messagebox
from urllib.parse import urlsplit

from ..core.engine import Engine
from .eventspec import EventSpec
from .blanktext import NonTagBind, BlankText
from .sharedtext import SharedTextEngineText
    

class EngineText(SharedTextEngineText, BlankText):

    """Chess engine definition widget.

    panel is used as the panel argument for the super().__init__ call.

    ui is the user interface manager for an instance of EngineText, usually an
    instance of ChessUI.

    items_manager is used as the items_manager argument for the
    super().__init__ call.

    itemgrid is the ui reference to the DataGrid from which the record was
    selected.

    Subclasses are responsible for providing a geometry manager.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    
    """

    def __init__(
        self,
        panel,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Create widgets to display chess engine definition."""
        super().__init__(panel, items_manager=items_manager, **ka)
        self.ui = ui

        # The popup menus for the engine definition.
        self.active_popup = None

        # Selection rule parser instance to process text.
        self.definition = Engine()
        
    # Not sure what events these are yet; or if name is best.
    # Remove '_navigation'?
    # Engine description records are always shown in a Toplevel.
    # Dismiss item and database update actions by keypress and buttunpress
    # are assumed to be exposed by the associated solentware_misc class.
    def get_active_navigation_events(self):
        return (
            (EventSpec.databaseenginedisplay_run, self.run_engine),
            )

    def get_active_button_events(self):
        return self.get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_3, self.post_active_menu),
            )

    def create_active_popup(self):
        assert self.active_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_active_navigation_events())
        database_submenu = self.create_database_submenu(popup)
        if database_submenu:
            popup.add_cascade(label='Database', menu=database_submenu)
        self.active_popup = popup
        return popup

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
        
    def set_engine_definition(self, reset_undo=False):
        """Display the chess engine definition as text.
        
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of an engine definition for editing so that repeated
        Ctrl-Z in text editing mode recovers the original engine definition.
        
        """
        if not self._is_text_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_engine_definition()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_primary_activity()
        if not self._is_text_editable:
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
