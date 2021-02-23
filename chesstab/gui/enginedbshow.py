# enginedbshow.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete dialogue to delete chess engine definition record.
"""

from solentware_grid.gui.datashow import DataShow

from .chessexception import ChessException
from .enginedisplay import DialogueEngineDisplay


class ChessDBshowEngine(ChessException, DataShow):
    """Dialog to show a chess engine definition from database.

    The chess engine definition is in it's own Toplevel widget.

    """

    def __init__(self, parent, instance, ui=None):
        """Create dialogue widget for deleting chess engine definition."""
        oldview = DialogueEngineDisplay(master=parent, ui=ui)
        if ui is not None:
            ui.engines_in_toplevels.add(oldview)
        oldview.definition.extract_engine_definition(instance.get_srvalue())
        oldview.set_engine_definition(instance.value)
        super(ChessDBshowEngine, self).__init__(
            instance,
            parent,
            oldview,
            ':  '.join((
                'Show Engine Definition',
                instance.value._description_string)),
            )
        self.bind_buttons_to_widget(oldview.score)
        self.ui = ui
       
    def dialog_ok(self):
        """Delete record and return delete action response (True for deleted).

        Check that database is open and is same one as deletion action was
        started.

        """
        if self.ui.database is None:
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super(ChessDBshowEngine, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.engines_in_toplevels.discard(self.oldview)

        # base_engines is None when this happens on Quit.
        try:
            self.ui.base_engines.selection.clear()
        except AttributeError:
            if self.ui.base_engines is not None:
                raise
