# gamedbdelete.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete dialogue to delete chess game record.
"""

from solentware_grid.gui.datadelete import DataDelete

from pgn_read.core.parser import PGN
from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from .chessexception import ChessException
from .gamedisplay import DialogueGameDisplay


class ChessDBdeleteGame(ChessException, DataDelete):
    
    """Dialog to delete a game from database.

    The game is in it's own Toplevel widget and playing through the game does
    not change the list of games, in the main widget, matching the current
    position on the board.

    """

    def __init__(self, parent, oldobject, ui=None):
        """Extend and create dialogue widget for deleting chess game."""
        oldview = DialogueGameDisplay(master=parent, ui=ui)
        oldview.set_position_analysis_data_source()
        if ui is not None:
            ui.games_and_repertoires_in_toplevels.add(oldview)
        oldview.collected_game = next(
            PGN(game_class=oldview.gameclass
                ).read_games(oldobject.get_srvalue()))
        oldview.set_game()
        tags = oldobject.value.collected_game._tags
        try:
            tt = '  '.join((
                'Delete Game:',
                ' - '.join((
                    tags[TAG_WHITE],
                    tags[TAG_BLACK])),
                ))
        except TypeError:
            tt = 'Delete Game - names unknown or invalid'
        except KeyError:
            tt = 'Delete Game - names unknown or invalid'
        super(ChessDBdeleteGame, self).__init__(oldobject, parent, oldview, tt)
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
        return super(ChessDBdeleteGame, self).dialog_ok()

    def delete(self):
        """Mark partial position records for recalculation and return key"""
        self.datasource.dbhome.mark_partial_positions_to_be_recalculated()
        super(ChessDBdeleteGame, self).delete()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.games_and_repertoires_in_toplevels.discard(self.oldview)
        self.ui.base_games.selection.clear()
