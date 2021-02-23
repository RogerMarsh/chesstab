# engineedit.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a chess engine definition.

The EngineEdit class displays a chess engine definition and allows editing.

This class has the selection.Engine class as a superclass.

This class does not allow deletion of chess engine definitions from a database.

An instance of these classes fits into the user interface as the only item in a
new toplevel widget.

"""
import os.path

from solentware_misc.workarounds import dialogues

from ..core.constants import NAME_DELIMITER
from ..core.engine import Engine
from . import engine
from .eventspec import EventSpec

import sys
_win32_platform = (sys.platform == 'win32')
_freebsd_platform = sys.platform.startswith('freebsd')
del sys


class EngineEdit(engine.Engine):
    
    """Display a chess engine definition with editing allowed.
    """

    # True means selection selection can be edited
    _is_definition_editable = True

    def __init__(self, **ka):
        """Extend chess engine definition widget as editor."""
        super(EngineEdit, self).__init__(**ka)
        # Context is same for each location so do not need dictionary of
        # Engine instances.
        self.engine_definition_checker = Engine()

    def bind_for_viewmode(self):
        """Set keyboard bindings for chess engine definition display."""
        super(EngineEdit, self).bind_for_viewmode()
        for sequence, function in (
            (EventSpec.databaseengineedit_browse, self.browse_engine),
            ):
            if function:
                self.score.bind(sequence[0], self.try_event(function))
                self.viewmode_popup.add_command(
                    label=sequence[1],
                    command=self.try_command(
                        function, self.viewmode_popup),
                    accelerator=sequence[2])

    def disable_keyboard(self):
        """Override and do nothing."""

    def browse_engine(self, event=None):
        """"""
        if _win32_platform:
            filetypes = (('Chess Engines', '*.exe'),)
        else:
            filetypes = ()
        filename = dialogues.askopenfilename(
            title='Browse Chess Engine',
            filetypes=filetypes,
            initialfile='',
            initialdir='~')
        if not filename:
            return
        definition = self.definition
        definition.update_engine_definition(
            self.get_name_engine_definition_dict())
        enginename = definition.get_name_text()
        if not enginename:
            enginename = os.path.splitext(os.path.basename(filename))[0]
        definition.extract_engine_definition(
            NAME_DELIMITER.join((enginename, filename)))
        self.set_engine_definition()
