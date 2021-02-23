# gamedbedit.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit dialogue to edit or insert chess game record.
"""

import tkinter

from solentware_grid.gui.dataedit import DataEdit

from solentware_misc.workarounds import dialogues

from pgn_read.core.parser import PGN
from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from .chessexception import ChessException
from .gamedisplay import DialogueGameDisplay, DialogueGameEdit
from .constants import EMPTY_SEVEN_TAG_ROSTER


class ChessDBeditGame(ChessException, DataEdit):
    
    """Dialog to edit a game on, or insert a game into, database.

    The game is in it's own Toplevel widget and playing through the game does
    not change the list of games, in the main widget, matching the current
    position on the board.

    """

    def __init__(self, newobject, parent, oldobject, showinitial=True, ui=None):
        """Extend and create dialogue widget to edit or insert chess game."""
        if oldobject:
            tags = oldobject.value.collected_game._tags
            try:
                title = '  '.join((
                    'Edit Game:',
                    ' - '.join((
                        tags[TAG_WHITE],
                        tags[TAG_BLACK])),
                    ))
            except TypeError:
                title = 'Edit Game - names unknown or invalid'
            except KeyError:
                title = 'Edit Game - names unknown or invalid'
        else:
            title = 'Insert Game'
            showinitial = False
        if showinitial:
            showinitial = DialogueGameDisplay(master=parent, ui=ui)
            showinitial.set_position_analysis_data_source()
            if ui is not None:
                ui.games_and_repertoires_in_toplevels.add(showinitial)
            showinitial.collected_game = next(
                PGN(game_class=showinitial.gameclass
                    ).read_games(newobject.get_srvalue()))
            showinitial.set_game()
        newview = DialogueGameEdit(master=parent, ui=ui)
        newview.set_position_analysis_data_source()
        if ui is not None:
            ui.games_and_repertoires_in_toplevels.add(newview)
        if oldobject:
            newview.collected_game = next(
                PGN(game_class=newview.gameclass
                    ).read_games(oldobject.get_srvalue()))
        else:
            newview.collected_game = next(
                PGN(game_class=newview.gameclass
                    ).read_games(''.join((EMPTY_SEVEN_TAG_ROSTER, '*'))))
        newview.set_game()
        super(ChessDBeditGame, self).__init__(
            newobject,
            parent,
            oldobject,
            newview,
            title,
            oldview=showinitial,
            )

        # Bind only to newview.score and newview.analysis.score because these
        # alone takes focus.
        self.bind_buttons_to_widget(newview.score)
        self.bind_buttons_to_widget(newview.analysis.score)

        self.ui = ui

    def dialog_ok(self):
        """Update record and return update action response (True for updated).

        Check that database is open and is same one as update action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text='Cannot update because not connected to a database')
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        text = self.newview.get_score_error_escapes_removed()
        self.newobject.value.load(repr(text))
        if not self.newobject.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != dialogues.askquestion(
                title='Edit Game',
                message=''.join(
                    ('The edited game score contains at least one illegal ',
                     'move in PGN.\n\nPlease re-confirm request to edit game.',
                     ))):
                return False
            self.newobject.value.set_game_source('Editor')
        return super(ChessDBeditGame, self).dialog_ok()
        
    def put(self):
        """Mark partial position records for recalculation and return key."""
        self.datasource.dbhome.mark_partial_positions_to_be_recalculated()
        super(ChessDBeditGame, self).put()

    def edit(self):
        """Mark partial position records for recalculation and return key."""
        self.datasource.dbhome.mark_partial_positions_to_be_recalculated()
        super(ChessDBeditGame, self).edit()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.games_and_repertoires_in_toplevels.discard(self.oldview)
        self.ui.games_and_repertoires_in_toplevels.discard(self.newview)
        self.ui.base_games.selection.clear()
