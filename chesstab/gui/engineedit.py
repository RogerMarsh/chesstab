# engineedit.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a chess engine definition.

The EngineEdit class extends the engine.Engine class to allow editing.

An instance of this class fits into the user interface as the only item in a
new toplevel widget.

"""
import sys
import os.path
import tkinter.filedialog

from ..core.constants import NAME_DELIMITER
from ..core.engine import Engine
from . import engine
from .eventspec import EventSpec

# Eyeball logic wants these attribute names to be same style.
# pylint logic disagrees.
_WIN32_PLATFORM = sys.platform == "win32"
_freebsd_platform = sys.platform.startswith("freebsd")

del sys


class EngineEdit(engine.Engine):
    """Display a chess engine definition with editing allowed.

    Attribute _is_text_editable is True meaning the statement can be
    edited.

    """

    # True means selection selection can be edited
    _is_text_editable = True

    def __init__(self, **ka):
        """Extend chess engine definition widget as editor."""
        super().__init__(**ka)
        # Context is same for each location so do not need dictionary of
        # Engine instances.
        self.engine_definition_checker = Engine()

    def get_primary_activity_events(self):
        """Return tuple of game navigation keypresses and callbacks."""
        return (
            (EventSpec.databaseenginedisplay_run, self.run_engine),
            (EventSpec.databaseengineedit_browse, self._browse_engine),
        )

    def _browse_engine(self, event=None):
        """Dialogue to replace chess engine definition in editor."""
        del event
        if _WIN32_PLATFORM:
            filetypes = (("Chess Engines", "*.exe"),)
        else:
            filetypes = ()
        filename = tkinter.filedialog.askopenfilename(
            parent=self.panel.winfo_toplevel(),
            title="Browse Chess Engine",
            filetypes=filetypes,
            initialfile="",
            initialdir="~",
        )
        if not filename:
            return
        definition = self.definition
        definition.update_engine_definition(
            self.get_name_engine_definition_dict()
        )
        enginename = definition.get_name_text()
        if not enginename:
            enginename = os.path.splitext(os.path.basename(filename))[0]
        definition.extract_engine_definition(
            NAME_DELIMITER.join((enginename, filename))
        )
        self.set_engine_definition()
