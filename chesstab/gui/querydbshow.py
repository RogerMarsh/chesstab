# querydbshow.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete dialogue to delete game selection rule record.
"""

from solentware_grid.gui.datashow import DataShow

from .chessexception import ChessException
from .querydisplay import DialogueQueryDisplay


class ChessDBshowQuery(ChessException, DataShow):
    """Dialog to show a game selection rule from database.

    The game selection rule is in it's own Toplevel widget.

    """

    def __init__(self, parent, instance, ui=None):
        """Extend and create dialogue widget for deleting selection rule."""
        oldview = DialogueQueryDisplay(master=parent, ui=ui)
        if ui is not None:
            ui.selections_in_toplevels.add(oldview)
            oldview.query_statement.set_database(
                ui.base_games.datasource.dbhome)
            oldview.query_statement.dbset = ui.base_games.datasource.dbset
        oldview.query_statement.process_query_statement(instance.get_srvalue())
        oldview.set_query_statement(instance.value)
        super(ChessDBshowQuery, self).__init__(
            instance,
            parent,
            oldview,
            ':  '.join((
                'Show Selection Rule',
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
        return super(ChessDBshowQuery, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.selections_in_toplevels.discard(self.oldview)
        self.ui.base_selections.selection.clear()
