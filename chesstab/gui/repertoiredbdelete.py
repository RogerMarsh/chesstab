# repertoiredbdelete.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete dialogue to delete repertoire record.
"""

from solentware_grid.gui.datadelete import DataDelete

from pgn_read.core.parser import PGN

from ..core.constants import TAG_OPENING
from .chessexception import ChessException
from .repertoiredisplay import DialogueRepertoireDisplay


class ChessDBdeleteRepertoire(ChessException, DataDelete):
    
    """Dialog to delete a repertoire from database.

    The repertoire is in it's own Toplevel widget and playing through it does
    not change the list of games, in the main widget, matching the current
    position on the board.

    """

    def __init__(self, parent, oldobject, ui=None):
        """Extend and create dialogue widget for deleting chess game."""
        oldview = DialogueRepertoireDisplay(master=parent, ui=ui)
        oldview.set_position_analysis_data_source()
        if ui is not None:
            ui.games_and_repertoires_in_toplevels.add(oldview)
        oldview.collected_game = next(
            PGN(game_class=oldview.gameclass
                ).read_games(oldobject.get_srvalue()))
        oldobject.value.set_game_source('No opening name')
        oldview.set_game()
        try:
            tt = '  '.join((
                'Delete Repertoire:',
                oldobject.value.collected_game._tags[TAG_OPENING],
                ))
        except TypeError:
            tt = 'Delete Repertoire - name unknown or invalid'
        except KeyError:
            tt = 'Delete Repertoire - name unknown or invalid'
        super(ChessDBdeleteRepertoire, self).__init__(
            oldobject, parent, oldview, tt)
        self.bind_buttons_to_widget(oldview.score)
        self.bind_buttons_to_widget(oldview.analysis.score)
        self.ui = ui

    def dialog_ok(self):
        """Delete record and return delete action response (True for deleted).

        Check that database is open and is same one as deletion action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text='Cannot delete because not connected to a database')
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super(ChessDBdeleteRepertoire, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.games_and_repertoires_in_toplevels.discard(self.oldview)
        self.ui.base_repertoires.selection.clear()
