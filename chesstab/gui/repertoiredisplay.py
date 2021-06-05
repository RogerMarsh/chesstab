# repertoiredisplay.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit repertoires.

These four classes display PGN text for games in the main window: they are
used in the gamelistgrid module.

The _RepertoireDisplay class provides attributes and behaviour shared by the
RepertoireDisplay, RepertoireDisplayInsert, and RepertoireDisplayEdit,
classes.  It also provides properties to support implementation of behaviour
shared with the CQL*, Game*, and Query*, classes.

The RepertoireDisplay, RepertoireDisplayInsert, and RepertoireDisplayEdit,
classes are subclasses of the relevant ShowPGN, InsertPGN, EditPGN, and
DisplayPGN, classes from the displaypgn module; to implement behaviour shared
with all text widgets in the main display (that includes widgets displaying
text).

"""

import tkinter
import tkinter.messagebox

from solentware_grid.core.dataclient import DataNotify

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from ..core.constants import TAG_OPENING
from .repertoire import Repertoire
from .repertoireedit import RepertoireEdit
from ..core.chessrecord import ChessDBrecordRepertoireUpdate
from .eventspec import EventSpec
from .display import Display
from .displaypgn import ShowPGN, InsertPGN, EditPGN, DisplayPGN


class _RepertoireDisplay(ExceptionHandler, Display):

    """Extend and link PGN repertoire text to database.

    sourceobject - link to database.

    Attribute binding_labels specifies the order navigation bindings appear
    in popup menus.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Attribute pgn_score_tags provides the PGN tag names used in widget titles
    and message text.  It is the opening PGN tag defined in ChessTab.

    Attribute pgn_score_source_name provides the error key value to index a
    PGN game score with errors.

    Attribute pgn_score_updater provides the class used to process PGN text
    into a database update.

    """

    binding_labels = (
        EventSpec.navigate_to_position_grid,
        EventSpec.navigate_to_active_game,
        EventSpec.navigate_to_game_grid,
        EventSpec.navigate_to_repertoire_grid,
        EventSpec.repertoiredisplay_to_previous_repertoire,
        EventSpec.analysis_to_scoresheet,
        EventSpec.repertoiredisplay_to_next_repertoire,
        EventSpec.navigate_to_repertoire_game_grid,
        EventSpec.scoresheet_to_analysis,
        EventSpec.navigate_to_partial_grid,
        EventSpec.navigate_to_active_partial,
        EventSpec.navigate_to_partial_game_grid,
        EventSpec.navigate_to_selection_rule_grid,
        EventSpec.navigate_to_active_selection_rule,
        EventSpec.tab_traverse_backward,
        EventSpec.tab_traverse_forward,
    )

    # These exist so the insert_game_database methods in _RepertoireDisplay and
    # gamedisplay._GameDisplay, and delete_game_database in RepertoireDisplay
    # and gameedisplay.GameDisplay, can be modified and replaced by single
    # copies in the displaypgn.ShowPGN class.
    # See mark_partial_positions_to_be_recalculated() method too.
    # The names need to be more generic to make sense in cql, engine, and
    # query, context.
    pgn_score_name = "repertoire"
    pgn_score_source_name = "No opening name"
    pgn_score_tags = (TAG_OPENING,)
    pgn_score_updater = ChessDBrecordRepertoireUpdate

    def __init__(self, sourceobject=None, **ka):
        """Extend and link repertoire to database."""
        super().__init__(**ka)
        self.blockchange = False
        if self.ui.base_repertoires.datasource:
            self.set_data_source(self.ui.base_repertoires.get_data_source())
        self.sourceobject = sourceobject

    # Could be put in game.Repertoire class to hide the game.Game version.
    # Here can be justified because purpose is allow some methods to be moved
    # to displaypgn.ShowPGN class.
    @property
    def ui_displayed_items(self):
        return self.ui.repertoire_items

    # Defined so cycle_item and give_focus_to_widget methods can be shared by
    # gamedisplay._GameDisplay and repertoiredisplay._RepertoireDisplay classes.
    @property
    def ui_configure_item_list_grid(self):
        return self.ui.configure_repertoire_grid

    # ui_base_table and mark_partial_positions_to_be_recalculated defined
    # so insert_game_database method can be shared by gamedisplay._GameDisplay
    # and repertoiredisplay._RepertoireDisplay classes.
    # See class attributes pgn_score_name and pgn_score_source_name too.

    @property
    def ui_base_table(self):
        return self.ui.base_repertoires

    @property
    def ui_items_in_toplevels(self):
        return self.ui.games_and_repertoires_in_toplevels

    def mark_partial_positions_to_be_recalculated(self, datasource=None):
        pass

    def get_navigation_events(self):
        """Return event description tuple for navigation from repertoire."""
        return (
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
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
            (EventSpec.navigate_to_active_game, self.set_focus_gamepanel_item),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item,
            ),
            (
                EventSpec.repertoiredisplay_to_previous_repertoire,
                self.prior_item,
            ),
            (EventSpec.repertoiredisplay_to_next_repertoire, self.next_item),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            # No traverse_round because Alt-F8 toggles repertoire and analysis.
        )

    def delete_item_view(self, event=None):
        """Remove repertoire item from screen."""
        self.set_data_source()
        self.ui.delete_repertoire_view(self)

    def on_game_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            self.patch_pgn_score_to_fit_record_change_and_refresh_grid(
                self.ui.repertoire_games, instance
            )

    def on_repertoire_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            if (
                instance.key == self.sourceobject.key
                and self.datasource.dbname == self.sourceobject.dbname
                and self.datasource.dbset == self.sourceobject.dbset
            ):
                self.blockchange = True

    def get_text_for_statusbar(self):
        """ """
        return "".join(
            (
                "Please wait while finding games for repertoire position in ",
                self.pgn.tags.get(TAG_OPENING, "?"),
            )
        )

    def get_selection_text_for_statusbar(self):
        """ """
        return self.pgn.tags.get(TAG_OPENING, "?")

    def generate_popup_navigation_maps(self):
        navigation_map = {k: v for k, v in self.get_navigation_events()}
        local_map = {
            EventSpec.scoresheet_to_analysis: self.analysis_current_item,
        }
        return navigation_map, local_map


class RepertoireDisplay(
    _RepertoireDisplay, DisplayPGN, ShowPGN, Repertoire, DataNotify
):

    """Display a repertoire from a database allowing delete and insert."""

    # Allow for structure difference between RepertoireDisplay and GameDisplay
    # versions of delete_game_database.
    # Method comments suggest a problem exists which needs fixing.
    # Existence of this method prevents delete_game_database being used by
    # instances of superclasses of RepertoireDisplay, emulating the behaviour
    # before introduction of displaypgn module.
    def pgn_score_original_value(self, original_value):

        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        # original.value.set_game_source(self.sourceobject.value.gamesource)
        original_value.set_game_source("No opening name")

    def create_primary_activity_popup(self):
        popup = super().create_primary_activity_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_select_move_popup(self):
        popup = super().create_select_move_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup


class RepertoireDisplayInsert(
    _RepertoireDisplay, InsertPGN, ShowPGN, RepertoireEdit, DataNotify
):

    """Display a repertoire from a database allowing insert.

    RepertoireEdit provides the widget and _RepertoireDisplay the database
    interface.

    """


class RepertoireDisplayEdit(EditPGN, RepertoireDisplayInsert):

    """Display a repertoire from a database allowing edit and insert."""

    # Allow for structure difference between RepertoireDisplay and GameDisplay
    # versions of delete_game_database.
    # Method comments suggest a problem exists which needs fixing.
    # Existence of this method prevents delete_game_database being used by
    # instances of superclasses of RepertoireDisplay, emulating the behaviour
    # before introduction of displaypgn module.
    def pgn_score_original_value(self, original_value):

        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        # original.value.set_game_source(self.sourceobject.value.gamesource)
        original_value.set_game_source("No opening name")

    # set_properties_on_grids defined so update_game_database method can be
    # shared by repertoiredisplay.RepertoireDisplayEdit and
    # gamedisplay.GameDisplayEdit classes.
    # See class attributes pgn_score_name and pgn_score_source_name too.
    # The property which returns self.ui.base_repertoires is ignored because
    # the GameDisplayEdit version of the method sets properties on all grids.
    def set_properties_on_game_grids(self, newkey):
        self.ui.base_repertoires.set_properties(newkey)
