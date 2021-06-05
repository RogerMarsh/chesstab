# gamedisplay.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit game scores.

These four classes display PGN text for games in the main window: they are
used in the gamelistgrid module.

The _GameDisplay class provides attributes and behaviour shared by the
GameDisplay, GameDisplayInsert, and GameDisplayEdit, classes.  It also provides
properties to support implementation of behaviour shared with the CQL*,
Repertoire*, and Query*, classes.

The GameDisplay, GameDisplayInsert, and GameDisplayEdit, classes are subclasses
of the relevant ShowPGN, InsertPGN, EditPGN, and DisplayPGN, classes from the
displaypgn module; to implement behaviour shared with all text widgets in the
main display (that includes widgets displaying text).

"""

from solentware_grid.core.dataclient import DataNotify

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .game import Game
from .gameedit import GameEdit
from ..core.chessrecord import ChessDBrecordGameUpdate
from .constants import STATUS_SEVEN_TAG_ROSTER_PLAYERS
from .eventspec import EventSpec
from .display import Display
from .displaypgn import ShowPGN, InsertPGN, EditPGN, DisplayPGN


class _GameDisplay(ExceptionHandler, Display):
    """Extend and link PGN game text to database.

    sourceobject - link to database.

    Attribute binding_labels specifies the order navigation bindings appear
    in popup menus.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Attribute pgn_score_tags provides the PGN tag names used in widget titles
    and message text.  It is the black, result, and white, PGN tags.

    Attribute pgn_score_source_name provides the error key value to index a
    PGN game score with errors.

    Attribute pgn_score_updater provides the class used to process PGN text
    into a database update.

    """

    binding_labels = (
        EventSpec.navigate_to_position_grid,
        EventSpec.gamedisplay_to_previous_game,
        EventSpec.analysis_to_scoresheet,
        EventSpec.gamedisplay_to_next_game,
        EventSpec.navigate_to_game_grid,
        EventSpec.scoresheet_to_analysis,
        EventSpec.navigate_to_repertoire_grid,
        EventSpec.navigate_to_active_repertoire,
        EventSpec.navigate_to_repertoire_game_grid,
        EventSpec.navigate_to_partial_grid,
        EventSpec.navigate_to_active_partial,
        EventSpec.navigate_to_partial_game_grid,
        EventSpec.navigate_to_selection_rule_grid,
        EventSpec.navigate_to_active_selection_rule,
        EventSpec.tab_traverse_backward,
        EventSpec.tab_traverse_forward,
    )

    # These exist so the insert_game_database methods in _GameDisplay and
    # repertoiredisplay._RepertoireDisplay, and delete_game_database in
    # GameDisplay and repertoiredisplay.RepertoireDisplay, can be modified and
    # replaced by single copies in the displaypgn.ShowPGN class.
    # See mark_partial_positions_to_be_recalculated() method too.
    # The names need to be more generic to make sense in cql, engine, and
    # query, context.
    pgn_score_name = "game"
    pgn_score_source_name = "Editor"
    pgn_score_tags = STATUS_SEVEN_TAG_ROSTER_PLAYERS
    pgn_score_updater = ChessDBrecordGameUpdate

    def __init__(self, sourceobject=None, **ka):
        """Extend and link PGN text of game to database."""
        super().__init__(**ka)
        self.blockchange = False
        if self.ui.base_games.datasource:
            self.set_data_source(self.ui.base_games.get_data_source())
        self.sourceobject = sourceobject

    # Could be put in game.Game class, but score.Score seems too deep.
    # Here can be justified because purpose is allow some methods to be moved
    # to displaypgn.ShowPGN class.
    @property
    def ui_displayed_items(self):
        """Return the displayed games."""
        return self.ui.game_items

    # Defined so cycle_item and give_focus_to_widget methods can be shared by
    # gamedisplay._GameDisplay and repertoiredisplay._RepertoireDisplay classes.
    @property
    def ui_configure_item_list_grid(self):
        """Return method to configure game grid widget."""
        return self.ui.configure_game_grid

    # ui_base_table and mark_partial_positions_to_be_recalculated defined
    # so insert_game_database method can be shared by gamedisplay._GameDisplay
    # and repertoiredisplay._RepertoireDisplay classes.
    # See class attributes pgn_score_name and pgn_score_source_name too.

    @property
    def ui_base_table(self):
        """Return grid widget for database games."""
        return self.ui.base_games

    @property
    def ui_items_in_toplevels(self):
        """Return game and repertoire items in Toplevels."""
        return self.ui.games_and_repertoires_in_toplevels

    def mark_partial_positions_to_be_recalculated(self, datasource=None):
        """Mark ChessQL statements, in datasource, to be recalculated."""
        datasource.dbhome.mark_partial_positions_to_be_recalculated()

    def get_navigation_events(self):
        """Return event description tuple for navigation from game."""
        return (
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item,
            ),
            (EventSpec.gamedisplay_to_previous_game, self.prior_item),
            (EventSpec.gamedisplay_to_next_game, self.next_item),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            # No traverse_round because Alt-F8 toggles game and analysis.
        )

    def delete_item_view(self, event=None):
        """Remove game item from screen."""
        self.set_data_source()
        self.ui.delete_game_view(self)

    def on_game_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            if (
                instance.key == self.sourceobject.key
                and self.datasource.dbname == self.sourceobject.dbname
                and self.datasource.dbset == self.sourceobject.dbset
            ):
                self.blockchange = True
            self.patch_pgn_score_to_fit_record_change_and_refresh_grid(
                self.ui.game_games, instance
            )

    def generate_popup_navigation_maps(self):
        """Return tuple of widget navigation map and switch to analysis map."""
        navigation_map = {k: v for k, v in self.get_navigation_events()}
        local_map = {
            EventSpec.scoresheet_to_analysis: self.analysis_current_item,
        }
        return navigation_map, local_map


class GameDisplay(_GameDisplay, DisplayPGN, ShowPGN, Game, DataNotify):
    """Display a chess game from a database allowing delete and insert."""

    # Notes here because GameDisplay instances used extensively to diagnose
    # problem.
    # Open a game with variations.  Analysis is affected too.
    # Navigate to a move where 'Down' cycles through available variations.
    # Use pointer to go somewhere else where 'Down' goes to next move.  The
    # pointer action can be over game score or board.
    # Use 'Up' or 'Down' to go to adjacent move.
    # This causes an exception and crashes ChessTab.
    # There is no crash if 'Up' is used to move away from a point where
    # cycling through variations occurs, or just to get out of cycling and
    # then use pointer.
    # Investigation suggests a rewrite of the management of keystroke and
    # pointer events is needed to fix the problem.

    # Allow for structure difference between GameDisplay and RepertoireDisplay
    # versions of delete_game_database.
    # Method comments suggest a problem exists which needs fixing.
    # Existence of this method prevents delete_game_database being used by
    # instances of superclasses of RepertoireDisplay, emulating the
    # behaviour before introduction of displaypgn module.
    @staticmethod
    def pgn_score_original_value(original_value):
        """Set game source as 'Editor' if error comment in original_value."""
        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has no
        # attribute 'gamesource'.
        # original.value.set_game_source(self.sourceobject.value.gamesource)
        # original.value.set_game_source('Copy, possibly edited')
        if original_value.is_error_comment_present():
            original_value.set_game_source("Editor")

    def create_primary_activity_popup(self):
        """Delegate then add close item entry and return popup menu."""
        popup = super().create_primary_activity_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_select_move_popup(self):
        """Delegate then add close item entry and return popup menu."""
        popup = super().create_select_move_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup


class GameDisplayInsert(
    _GameDisplay, InsertPGN, ShowPGN, GameEdit, DataNotify
):
    """Display a chess game from a database allowing insert.

    GameEdit provides the widget and _GameDisplay the database interface.

    """


class GameDisplayEdit(EditPGN, GameDisplayInsert):
    """Display a chess game from a database allowing edit and insert."""

    # Allow for structure difference between GameDisplay and RepertoireDisplay
    # versions of delete_game_database.
    # Method comments suggest a problem exists which needs fixing.
    # Existence of this method prevents delete_game_database being used by
    # instances of superclasses of RepertoireDisplay, emulating the behaviour
    # before introduction of displaypgn module.
    @staticmethod
    def pgn_score_original_value(original_value):
        """Set game source as 'Editor' if error comment in original_value."""
        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        # original.value.set_game_source(self.sourceobject.value.gamesource)
        # original.value.set_game_source('Copy, possibly edited')
        if original_value.is_error_comment_present():
            original_value.set_game_source("Editor")

    # set_properties_on_grids defined so update_game_database method can be
    # shared by repertoiredisplay.RepertoireDisplayEdit and
    # gamedisplay.GameDisplayEdit classes.
    # See class attributes pgn_score_name and pgn_score_source_name too.
    def set_properties_on_grids(self, newkey):
        """Set properties of widgets for newkey on all grids."""
        self.ui.set_properties_on_all_game_grids(newkey)
