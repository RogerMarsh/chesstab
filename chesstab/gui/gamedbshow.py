# gamedbshow.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise show dialogue to display chess game record.
"""

from solentware_grid.gui.datashow import DataShow

from pgn_read.core.parser import PGN
from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from .chessexception import ChessException
from .gamedisplay import DialogueGameDisplay


class ChessDBshowGame(ChessException, DataShow):
    
    """Dialog to show a game from database.

    The game is in it's own Toplevel widget and playing through the game does
    not change the list of games, in the main widget, matching the current
    position on the board.

    """

    def __init__(self, parent, oldobject, ui=None):
        """Extend and create dialogue widget for displaying chess game."""
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
                'Show Game:',
                ' - '.join((
                    tags[TAG_WHITE],
                    tags[TAG_BLACK])),
                ))
        except TypeError:
            tt = 'Show Game - names unknown or invalid'
        except KeyError:
            tt = 'Show Game - names unknown or invalid'
        super(ChessDBshowGame, self).__init__(oldobject, parent, oldview, tt)
        self.bind_buttons_to_widget(oldview.score)
        self.bind_buttons_to_widget(oldview.analysis.score)
        self.ui = ui

    def dialog_ok(self):
        """Dismiss dialogue."""
        if self.ui.database is None:
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super(ChessDBshowGame, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.games_and_repertoires_in_toplevels.discard(self.oldview)
        self.ui.base_games.selection.clear()
