# gamedbedit.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert chess game record.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.gui.dataedit import DataEdit

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN
from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from .gametoplevel import GameToplevel, GameToplevelEdit
from .toplevelpgn import EditPGN
from .constants import EMPTY_SEVEN_TAG_ROSTER


class GameDbEdit(ExceptionHandler, EditPGN, DataEdit):

    """Edit PGN text for game on database, or insert a new record.

    parent is used as the master argument in GameToplevel calls.

    ui is used as the ui argument in GameToplevel calls.

    newobject, parent, oldobject, and the one or two GameToplevel instances
    created, are used as arguments in the super.__init__ call.

    showinitial determines whether a GameToplevel is created for oldobject if
    there is one.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Attribute pgn_score_tags provides empty PGN tags to present when creating
    an insert Toplevel.  It is the empty PGN Seven Tag Roster.

    Attribute pgn_score_source provides the error key value to index a PGN
    game score with errors.

    Methods get_title_for_object and set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    pgn_score_name = "Game"
    pgn_score_tags = EMPTY_SEVEN_TAG_ROSTER
    pgn_score_source = "Editor"

    def __init__(
        self, newobject, parent, oldobject, showinitial=True, ui=None
    ):
        """Extend and create dialogue widget to edit or insert chess game."""
        if not oldobject:
            showinitial = False
        super().__init__(
            newobject,
            parent,
            oldobject,
            GameToplevelEdit(master=parent, ui=ui),
            "",
            oldview=GameToplevel(master=parent, ui=ui)
            if showinitial
            else showinitial,
        )
        self.initialize()

    @property
    def ui_base_table(self):
        return self.ui.base_games

    @property
    def ui_items_in_toplevels(self):
        return self.ui.games_and_repertoires_in_toplevels

    @property
    def ui(self):
        return self.newview.ui

    def set_item(self, view, object_):
        self.set_default_source_for_object(object_)
        view.set_position_analysis_data_source()
        view.collected_game = next(
            PGN(game_class=view.gameclass).read_games(object_.get_srvalue())
        )
        view.set_and_tag_item_text()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a Game object_.

        Default value of object_ is oldobject attribute from DataEdit class.

        """
        if object_ is None:
            object_ = self.oldobject
        if object_:
            tags = object_.value.collected_game._tags
            try:
                return "  ".join(
                    (
                        self.pgn_score_name.join(("Edit ", ":")),
                        " - ".join((tags[TAG_WHITE], tags[TAG_BLACK])),
                    )
                )
            except TypeError:
                return self.pgn_score_name.join(
                    ("Edit ", " - names unknown or invalid")
                )
            except KeyError:
                return self.pgn_score_name.join(
                    ("Edit ", " - names unknown or invalid")
                )
        else:
            return "".join(("Insert ", self.pgn_score_name))

    def set_default_source_for_object(self, object_=None):
        """Set default source for Toplevel containing a Game object_.

        Default value of object_ is oldobject attribute from DataEdit class.

        Currently do nothing for games.  Originally used for games with PGN
        errors, where it was the name of the PGN file containing the game.

        Now present for compatibility with Repertoires.

        """
        pass

    def put(self):
        """Mark partial position records for recalculation and return key."""
        self.datasource.dbhome.mark_partial_positions_to_be_recalculated()
        super().put()

    def edit(self):
        """Mark partial position records for recalculation and return key."""
        self.datasource.dbhome.mark_partial_positions_to_be_recalculated()
        super().edit()
