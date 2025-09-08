# gamedbdelete.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete toplevel to delete chess game record."""

import ast
import tkinter

from solentware_grid.gui.datadelete import DataDelete

from pgn_read.core.parser import PGN
from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from .gametoplevel import GameToplevel
from .toplevelpgn import DeletePGNToplevel
from ..core import utilities


class GameDbDelete(DeletePGNToplevel, DataDelete):
    """Delete PGN text for game from database.

    parent is used as the master argument in a GameToplevel call.

    ui is used as the ui argument in a GameToplevel call.

    parent, oldobject, and the GameToplevel instance created, are used as
    arguments in the super.__init__ call.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    pgn_score_name = "Game"

    def __init__(self, parent=None, oldobject=None, ui=None):
        """Extend and create toplevel widget for deleting chess game."""
        # Toplevel title set '' in __init__ and to proper value in _initialize.
        super().__init__(
            instance=oldobject,
            parent=parent,
            oldview=GameToplevel(master=parent, ui=ui),
            title="",
        )
        self._initialize()
        if utilities.is_game_import_in_progress_txn(
            self.ui.database, self.object
        ):
            tkinter.messagebox.showinfo(
                parent=parent,
                title="Game import not complete",
                message="".join(
                    (
                        "The selected game is displayed but attempts ",
                        "to delete the game will be ",
                        "rejected because some stages of importing this ",
                        "game have not been completed.",
                    )
                ),
            )
            self.blockchange = True

    @property
    def ui_base_table(self):
        """Return the User Interface TagRosterGrid object."""
        return self.ui.base_games

    @property
    def ui_items_in_toplevels(self):
        """Return the User Interface objects in Toplevels."""
        return self.ui.games_and_repertoires_in_toplevels

    @property
    def ui(self):
        """Return the User Interface object from 'read-only' view."""
        return self.oldview.ui

    def _set_item(self, view, object_):
        """Populate view with the repertoire extracted from object_."""
        self._set_default_source_for_object(object_)
        view.set_position_analysis_data_source()
        view.collected_game = next(
            PGN(game_class=view.gameclass).read_games(
                ast.literal_eval(object_.get_srvalue()[0])
            )
        )
        view.set_and_tag_item_text()

    def _get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a Game object_.

        Default value of object_ is object attribute from DataDelete class.

        """
        if object_ is None:
            object_ = self.object
        try:
            tags = object_.value.collected_game.pgn_tags
            return "  ".join(
                (
                    self.pgn_score_name.join(("Delete ", ":")),
                    " - ".join((tags[TAG_WHITE], tags[TAG_BLACK])),
                )
            )
        except TypeError:
            return self.pgn_score_name.join(
                ("Delete ", " - names unknown or invalid")
            )
        except KeyError:
            return self.pgn_score_name.join(
                ("Delete ", " - names unknown or invalid")
            )

    def _set_default_source_for_object(self, object_=None):
        """Set default source for Toplevel containing a Game object_.

        Default value of object_ is object attribute from DataDelete class.

        Currently do nothing for games.  Originally used for games with PGN
        errors, where it was the name of the PGN file containing the game.

        Now present for compatibility with Repertoires.

        """

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    # mark...recalculated starts and commits a transaction unconditionally.
    # No harm in using the same default as the 'super()' method.
    def delete(self, commit=True):
        """Mark CQL query records for recalculation and return key.

        If commit evaluates False caller is responsible for evaluating
        CQL queries on the changes.

        """
        dbhome = self.datasource.dbhome
        dbhome.mark_games_evaluated(
            allexceptkey=(
                self.object.key.recno if self.object is not None else None
            )
        )
        dbhome.mark_all_cql_statements_not_evaluated()
        if commit:
            dbhome.remove_game_key_from_all_cql_query_match_lists(
                self.object.key.recno
            )
        super().delete(commit=commit)
        dbhome.clear_cql_queries_pending_evaluation()
