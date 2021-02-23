# enginetext.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display a chess engine definition.
"""

import tkinter
from urllib.parse import urlsplit

from solentware_misc.workarounds import dialogues

from .chessexception import ChessException
from ..core.engine import Engine
from .eventspec import EventSpec
from .displayitems import DisplayItemsStub
    

class EngineText(ChessException):

    """Chess engine definition widget built from Text and Scrollbar widgets.
    """

    # True means engine definition can be edited
    _is_definition_editable = False

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
        self.disable_keyboard()

        # The popup menus for the engine definition

        self.viewmode_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.viewmode_navigation_popup = None

        # Selection rule parser instance to process text.
        self.definition = Engine()
        
    def bind_for_viewmode(self):
        """Set keyboard bindings for chess engine definition display."""
        for sequence, function in (
            (EventSpec.databaseenginedisplay_run, self.run_engine),
            ):
            if function:
                self.score.bind(sequence[0], self.try_event(function))
                self.viewmode_popup.add_command(
                    label=sequence[1],
                    command=self.try_command(
                        function, self.viewmode_popup),
                    accelerator=sequence[2])

    def bind_pointer_for_viewmode_popup(self):
        """Show popup menu."""
        self.score.bind('<ButtonPress-3>',
                        self.try_event(self.popup_viewmode_menu))

    def give_focus_to_widget(self, event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return 'break'
        
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
        
    def popup_viewmode_menu(self, event=None):
        """Show the popup menu for chess engine definition actions.

        Subclasses define particular entries for this menu.  This class adds
        no items to the menu.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return 'break'
        self.viewmode_popup.tk_popup(*self.score.winfo_pointerxy())

    def disable_keyboard(self):
        """"""
        self.score.bind(EventSpec.selectiontext_disable_keypress[0],
                        lambda e: 'break')

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
        #    dialogues.showinfo(
        #        'Chesstab Restriction',
        #        ' '.join(('Starting an UCI chess engine is not allowed because',
        #                  'an interface cannot be created:',
        #                  'this is expected if running under Wine.')))
        #    return

        url = urlsplit(self.definition.get_engine_command_text())
        try:
            url.port
        except ValueError as exc:
            dialogues.showerror(
                title=self.__title,
                message=''.join(('The port in the chess engine definition is ',
                                 'invalid.\n\n',
                                 'The reported error for the port is:\n\n',
                                 str(exc),
                                 'but neither hostname nor port may be given ',
                                 'here.\n',
                                 )))
            return
        if not self.definition.get_engine_command_text():
            dialogues.showinfo(
                title='Run Engine',
                message=''.join((
                    'The engine definition does not have a command to ',
                    'run chess engine.',
                    )))
            return
        elif url.port or url.hostname:
            dialogues.showinfo(
                title='Run Engine',
                message=''.join(
                    ('Neither hostname nor port may be given here.\n',
                     "Hostname is: '", url.hostname, "'.\n\n",
                     "Port is: '", url.port, "'.\n",
                     )))
            return
        elif not self.definition.is_run_engine_command():
            dialogues.showinfo(
                title='Run Engine',
                message=''.join((
                    'The engine definition command to run a chess engine ',
                    'does not name a file.',
                    )))
            return
        self.ui.run_engine(self.definition.get_engine_command_text())
