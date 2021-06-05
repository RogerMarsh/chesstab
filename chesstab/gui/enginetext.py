# enginetext.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a chess engine definition.
"""

import tkinter
import tkinter.messagebox
from urllib.parse import urlunsplit

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
        self, panel, ui=None, items_manager=None, itemgrid=None, **ka
    ):
        """Create widgets to display chess engine definition."""
        super().__init__(panel, items_manager=items_manager, **ka)
        self.ui = ui

        # The popup menus for the engine definition.
        self.primary_activity_popup = None

        # Selection rule parser instance to process text.
        self.definition = Engine()

    # Engine description records are always shown in a Toplevel.
    # Dismiss item and database update actions by keypress and buttunpress
    # are assumed to be exposed by the associated solentware_misc class.
    def get_primary_activity_events(self):
        return ((EventSpec.databaseenginedisplay_run, self.run_engine),)

    def set_primary_activity_bindings(self, switch=True):
        """Switch bindings for editing chess engine definition on or off."""
        self.set_event_bindings_score(
            self.get_primary_activity_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_F10_popup_events(
                self.post_active_menu_at_top_left, self.post_active_menu
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_button_events(buttonpress3=self.post_active_menu),
            switch=switch,
        )

    def set_engine_definition(self, reset_undo=False):
        """Display the chess engine definition as text.

        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of an engine definition for editing so that repeated
        Ctrl-Z in text editing mode recovers the original engine definition.

        """
        if not self._is_text_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete("1.0", tkinter.END)
        self.map_engine_definition()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_primary_activity()
        if not self._is_text_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()

    def set_statusbar_text(self):
        """Set status bar to display chess engine definition name."""
        # self.ui.statusbar.set_status_text(self.definition.get_name_text())

    def get_name_engine_definition_dict(self):
        """Extract chess engine definition from Text widget."""
        e = Engine()
        if e.extract_engine_definition(
            self.score.get("1.0", tkinter.END).strip()
        ):
            return e.__dict__
        return {}

    def map_engine_definition(self):
        """Insert chess engine definition in Text widget.

        Method name arises from development history: the source class tags
        inserted text extensively and this method name survived the cull.

        """
        # No mapping of tokens to text in widget (yet).
        self.score.insert(
            tkinter.INSERT, self.definition.get_name_engine_command_text()
        )

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
        # if self.ui.uci.uci_drivers_reply is None:
        #    tkinter.messagebox.showinfo(
        #        parent=self.panel,
        #        title='Chesstab Restriction',
        #        message=' '.join(
        #            ('Starting an UCI chess engine is not allowed because',
        #             'an interface cannot be created:',
        #             'this is expected if running under Wine.')))
        #    return

        url = self.definition.engine_url_or_error_message()
        if isinstance(url, str):
            tkinter.messagebox.showerror(
                parent=self.parent, title="Run Engine", message=url
            )
            return
        if url.query:
            self.ui.run_engine(urlunsplit(url))
        elif url.path:
            command = url.path.split(" ", 1)
            if len(command) == 1:
                self.ui.run_engine(command[0])
            else:
                self.ui.run_engine(command[0], args=command[1].strip())
        else:
            tkinter.messagebox.showerror(
                parent=self.parent,
                title="Run Engine",
                message="".join(
                    (
                        "Unable to run engine for\n\n",
                        self.definition.get_engine_command_text(),
                    )
                ),
            )
