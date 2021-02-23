# repertoiredbedit.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit dialogue to edit or insert repertoire record.
"""

import tkinter

from solentware_grid.gui.dataedit import DataEdit

from solentware_misc.workarounds import dialogues

from pgn_read.core.parser import PGN

from ..core.constants import TAG_OPENING
from .chessexception import ChessException
from .repertoiredisplay import DialogueRepertoireDisplay, DialogueRepertoireEdit
from .constants import EMPTY_REPERTOIRE_GAME


class ChessDBeditRepertoire(ChessException, DataEdit):
    
    """Dialog to edit a repertoire on, or insert a repertoire into, database.

    The repertoire is in it's own Toplevel widget and playing through it does
    not change the list of games, in the main widget, matching the current
    position on the board.

    """

    def __init__(self, newobject, parent, oldobject, showinitial=True, ui=None):
        """Extend and create dialogue widget to edit or insert chess game."""
        if oldobject:
            try:
                title = '  '.join((
                    'Edit Repertoire:',
                    oldobject.value.collected_game._tags[TAG_OPENING],
                    ))
            except TypeError:
                title = 'Edit Repertoire - name unknown or invalid'
            except KeyError:
                title = 'Edit Repertoire - name unknown or invalid'
        else:
            title = 'Insert Repertoire'
            showinitial = False
        if showinitial:
            showinitial = DialogueRepertoireDisplay(master=parent, ui=ui)
            showinitial.set_position_analysis_data_source()
            if ui is not None:
                ui.games_and_repertoires_in_toplevels.add(showinitial)
            showinitial.collected_game = next(
                PGN(game_class=showinitial.gameclass
                    ).read_games(newobject.get_srvalue()))
            showinitial.set_game()
        newview = DialogueRepertoireEdit(master=parent, ui=ui)
        newview.set_position_analysis_data_source()
        if ui is not None:
            ui.games_and_repertoires_in_toplevels.add(newview)
        if oldobject:
            newview.collected_game = next(
                PGN(game_class=newview.gameclass
                    ).read_games(newobject.get_srvalue()))
            oldobject.value.set_game_source('No opening name')
        else:
            newview.collected_game = next(
                PGN(game_class=newview.gameclass
                    ).read_games(''.join((EMPTY_REPERTOIRE_GAME, '*'))))
        newview.set_game()
        super(ChessDBeditRepertoire, self).__init__(
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
                title='Edit Repertoire',
                message=''.join(
                    ('The edited repertoire contains at least one illegal ',
                     'move in PGN.\n\nPlease re-confirm request to edit ',
                     'repertoire.',
                     ))):
                return False
            self.newobject.value.set_game_source('No opening name')
        return super(ChessDBeditRepertoire, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.games_and_repertoires_in_toplevels.discard(self.oldview)
        self.ui.games_and_repertoires_in_toplevels.discard(self.newview)
        self.ui.base_repertoires.selection.clear()
