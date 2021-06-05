# toplevelpgn.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define methods shared by classes in the gamedbdelete,
gamedbdisplay, gamedbedit, gamedbshow, repertoiredbdelete, repertoiredbdisplay,
repertoiredbedit, and repertoiredbshow, modules which display Portable Game
Notation (PGN) text.

All methods in the classes in this module existed as multiple copies in the
modules named above.  They are now deleted from those modules.

The classes in this module represent the different sets of classes with methods
in common.

The ToplevelPGN class is populated with the methods identical in
GameToplevel, RepertoireToplevel, GameToplevelEdit, and
RepertoireToplevelEdit, which were then removed from those two classes.

"""
import tkinter.messagebox

from .eventspec import EventSpec
from .scorepgn import ScorePGN
from .topleveltext import DeleteText, EditText, ShowText


class ToplevelPGN(ScorePGN):

    """Mixin providing methods shared by the gametoplevel.GameToplevel,
    repertoiretoplevel.RepertoireToplevel, gametoplevel.GameToplevelEdit,
    and repertoiretoplevel.RepertoireToplevelEdit, classes.

    The game and repertoire display methods assume there is an associated list
    of games for the current position.  The *Toplevel* classes do not have this
    list, so the method which updates it is overridden.

    """

    binding_labels = (
        EventSpec.analysis_to_scoresheet,
        EventSpec.scoresheet_to_analysis,
    )

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a PGN score including switching
        from one PGN score to another.

        """
        # Score.set_game_list() expects instance to have itemgrid attribute
        # bound to a DataGrid subclass instance, but the Dialogue* instances
        # can live without this being present.
        # It may be more appropriate to override set_game_list to do nothing so
        # there is a way of deleting a record without tracking games containing
        # the same positions.
        try:
            super().set_game_list()
        except AttributeError:
            if self.itemgrid is not None:
                raise

    def generate_popup_navigation_maps(self):
        navigation_map = {}
        local_map = {
            EventSpec.scoresheet_to_analysis: self.analysis_current_item,
        }
        return navigation_map, local_map

    def current_item(self, event=None):
        """Select current PGN score on display."""
        self.current_pgn_score(self)


class _ToplevelPGN:

    """Mixin providing methods shared by the toplevelpgn.ShowPGN,
    toplevelpgn.DeletePGN, and toplevelpgn.EditPGN, classes.

    """

    def initialize_item_bindings(self, item):
        self.bind_buttons_to_widget(item.score)
        self.bind_buttons_to_widget(item.analysis.score)
        item.set_score_pointer_to_score_bindings(False)
        item.set_analysis_score_pointer_to_analysis_score_bindings(True)
        item.set_toggle_game_analysis_bindings(True)
        item.set_board_pointer_move_bindings(True)


class ShowPGN(_ToplevelPGN, ShowText):
    pass


class DeletePGN(_ToplevelPGN, DeleteText):
    pass


class EditPGN(_ToplevelPGN, EditText):
    def dialog_ok(self):
        """Update record and return update action response (True for updated).

        Check that database is open and is same one as update action was
        started.

        """
        text = self.newview.get_score_error_escapes_removed()
        self.newobject.value.load(repr(text))
        if not self.newobject.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.parent,
                title="".join(("Edit ", self.pgn_score_name)),
                message=self.pgn_score_name.lower().join(
                    (
                        "The edited ",
                        "".join(
                            (
                                " contains at least one illegal move in PGN.",
                                "\n\nPlease re-confirm request to edit ",
                            )
                        ),
                        ".",
                    )
                ),
            ):
                return False
            self.newobject.value.set_game_source(self.pgn_score_source)
        return super().dialog_ok()
