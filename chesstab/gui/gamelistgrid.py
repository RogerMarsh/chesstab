# gamelistgrid.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of games on chess database."""

import tkinter.messagebox

from solentware_grid.datagrid import DataGrid

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN

from ..core.chessrecord import (
    ChessDBrecordGameUpdate,
    ChessDBrecordRepertoireUpdate,
    PLAYER_NAME_TAGS,
    re_normalize_player_name,
)
from .gamerow import ChessDBrowGame
from .positionrow import ChessDBrowPosition
from .repertoirerow import ChessDBrowRepertoire
from .gamedisplay import GameDisplay, GameDisplayEdit
from .repertoiredisplay import RepertoireDisplay, RepertoireDisplayEdit
from .constants import (
    EMPTY_SEVEN_TAG_ROSTER,
    STATUS_SEVEN_TAG_ROSTER_EVENT,
    STATUS_SEVEN_TAG_ROSTER_SCORE,
    STATUS_SEVEN_TAG_ROSTER_PLAYERS,
    EMPTY_REPERTOIRE_GAME,
)
from ..core.filespec import POSITIONS_FIELD_DEF
from ..core import exporters
from .eventspec import EventSpec
from .display import Display
from ..shared.cql_gamelist_query import CQLGameListQuery
from ..shared.allgrid import AllGrid
from ..core.constants import REPERTOIRE_TAG_ORDER, UNKNOWN_RESULT


class GameListGrid(
    ExceptionHandler, AllGrid, CQLGameListQuery, DataGrid, Display
):
    """A DataGrid for lists of chess games.

    Subclasses provide navigation and extra methods appropriate to list use.

    """

    def __init__(self, parent, ui):
        """Extend with link to user interface object.

        parent - see superclass
        ui - container for user interface widgets and methods.

        """
        super().__init__(parent=parent)
        self._configure_frame_and_initial_event_bindings(ui)

    def _display_selected_item(self, key, selected):
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplay is to be put.
        # Yes because GameDisplayEdit (see edit_selected_item) includes
        # extra widgets. Want to say game.widget.destroy() eventually.
        # Read make_display_widget for GameDisplay and GameDisplayEdit.
        game = self.make_display_widget(selected)
        self.ui.add_game_to_display(game)
        self.ui.game_items.increment_object_count(key)
        self.ui.game_items.set_itemmap(game, key)
        self.ui.set_properties_on_all_game_grids(key)
        return game

    def make_display_widget(self, sourceobject):
        """Return a GameDisplay for sourceobject."""
        game = GameDisplay(
            master=self.ui.view_games_pw,
            ui=self.ui,
            items_manager=self.ui.game_items,
            itemgrid=self.ui.game_games,
            sourceobject=sourceobject,
        )
        game.set_position_analysis_data_source()
        game.collected_game = next(
            PGN(game_class=game.gameclass).read_games(
                sourceobject.get_srvalue()
            )
        )
        return game

    def edit_selected_item(self, key):
        """Create display and return a GameDisplayEdit for selected game."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplayEdit is to be put.
        # Yes because GameDisplay (see display_selected_item) includes
        # less widgets. Want to say game.widget.destroy() eventually.
        # Read make_edit_widget for GameDisplay and GameDisplayEdit.
        game = self.make_edit_widget(selected)
        self.ui.add_game_to_display(game)
        self.ui.game_items.increment_object_count(selected.srvalue)
        self.ui.game_items.set_itemmap(game, selected.srvalue)
        self.ui.set_properties_on_all_game_grids(key)
        return game

    def make_edit_widget(self, sourceobject):
        """Return a GameDisplayEdit for sourceobject."""
        game = GameDisplayEdit(
            master=self.ui.view_games_pw,
            ui=self.ui,
            items_manager=self.ui.game_items,
            itemgrid=self.ui.game_games,
            sourceobject=sourceobject,
        )
        game.set_position_analysis_data_source()
        game.collected_game = next(
            PGN(game_class=game.gameclass).read_games(
                sourceobject.get_srvalue()
            )
        )
        return game

    def set_properties(self, key, dodefaultaction=True):
        """Return True if properties for game key set or False."""
        if super().set_properties(key, dodefaultaction=False):
            return True
        if self.ui.game_items.object_display_count(key):
            self._set_background_on_display_row_under_pointer(key)
            return True
        if dodefaultaction:
            self._set_background_normal_row_under_pointer(key)
            return True
        return False

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for game key or None."""
        row = super().set_row(key, dodefaultaction=False, **kargs)
        if row is not None:
            return row
        if key not in self.keys:
            return None
        if self.ui.game_items.object_display_count(self.objects[key].srvalue):
            return self.objects[key].grid_row_on_display(**kargs)
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        else:
            return None

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordGameUpdate()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_delete_dialog(
            self.objects[key], oldobject, modal, title="Delete Game"
        )

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordGameUpdate(),
            ChessDBrecordGameUpdate(),
            False,
            modal,
            title="Edit Game",
        )

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordGameUpdate(),
            ChessDBrecordGameUpdate(),
            True,
            modal,
            title="Edit Game",
        )

    def launch_insert_new_record(self, modal=True):
        """Create insert dialogue."""
        newobject = ChessDBrecordGameUpdate()
        instance = self.datasource.new_row()
        instance.srvalue = repr(EMPTY_SEVEN_TAG_ROSTER + UNKNOWN_RESULT)
        self.create_edit_dialog(
            instance, newobject, None, False, modal, title="New Game"
        )

    def launch_show_record(self, key, modal=True):
        """Create show dialogue."""
        oldobject = ChessDBrecordGameUpdate()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_show_dialog(
            self.objects[key], oldobject, modal, title="Show Game"
        )

    def _set_object_panel_item_properties(self):
        """Adjust properties of game_items to fit configure canvas event."""
        ui = self.ui
        for key in ui.game_items.object_panel_count:
            self.set_properties(key)

    def set_move_highlight(self, game):
        """Set move highlight at current position in game.

        In particular a game displayed from the list of games matching a
        position is shown at that position.

        """
        if game is not None:
            if game.current:
                game.set_move_highlight(game.current, True, True)

    def bookmark_down(self):
        """Extend to show selection summary in status bar."""
        super().bookmark_down()
        self.set_selection_text()

    def bookmark_up(self):
        """Extend to show selection summary in status bar."""
        super().bookmark_up()
        self.set_selection_text()

    def export_text(self, event=None):
        """Export selected games as text."""
        self.ui.export_report(
            exporters.export_selected_games_text(
                self,
                self.ui.get_export_filename(
                    "Games (internal format)", pgn=False
                ),
            ),
            "Games (internal format)",
        )

    def export_pgn_import_format(self, event=None):
        """Export selected games in a PGN import format."""
        self.ui.export_report(
            exporters.export_selected_games_pgn_import_format(
                self,
                self.ui.get_export_filename("Games (import format)", pgn=True),
            ),
            "Games (import format)",
        )

    def export_pgn(self, event=None):
        """Export selected games in PGN export format."""
        self.ui.export_report(
            exporters.export_selected_games_pgn(
                self, self.ui.get_export_filename("Games", pgn=True)
            ),
            "Games",
        )

    def export_pgn_reduced_export_format(self, event=None):
        """Export selected games in PGN Reduced Export Format."""
        self.ui.export_report(
            exporters.export_selected_games_pgn_reduced_export_format(
                self,
                self.ui.get_export_filename(
                    "Games (reduced export format)", pgn=True
                ),
            ),
            "Games (reduced export format)",
        )

    def export_pgn_no_comments_no_ravs(self, event=None):
        """Export selected games as PGN excluding all comments and RAVs."""
        self.ui.export_report(
            exporters.export_selected_games_pgn_no_comments_no_ravs(
                self,
                self.ui.get_export_filename(
                    "Games (no comments no ravs)", pgn=True
                ),
            ),
            "Games (no comments no ravs)",
        )

    def export_pgn_no_comments(self, event=None):
        """Export selected games as PGN excluding all commentary tokens."""
        self.ui.export_report(
            exporters.export_selected_games_pgn_no_comments(
                self,
                self.ui.get_export_filename("Games (no comments)", pgn=True),
            ),
            "Games (no comments)",
        )


# Because of possible changes to GameListGrid to support database update after
# introducing subclasses of PGN to do just the required work it may not be
# possible for PartialPositionGames to be subclass of GameListGrid.
class PartialPositionGames(GameListGrid):
    """Customized GameListGrid for list of games matching a partial position.

    The grid is populated by a ChessQueryLanguageDS instance from the dpt.cqlds
    or basecore.cqlds modules.
    """

    def __init__(self, ui):
        """Extend with partial position grid definition and bindings.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.position_partials_pw, ui)
        self.make_header(ChessDBrowGame.header_specification)
        self.__bind_on()
        self.set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self.display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self.edit_game_from_popup),
            ),
        )
        self.add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self.set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self.add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self.add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self.set_event_bindings_frame(
            (
                (EventSpec.navigate_to_partial_grid, ""),
                (EventSpec.navigate_to_active_partial, ""),
                (EventSpec.navigate_to_repertoire_grid, ""),
                (EventSpec.navigate_to_active_repertoire, ""),
                (EventSpec.navigate_to_repertoire_game_grid, ""),
                (EventSpec.navigate_to_position_grid, ""),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_game_grid, ""),
                (EventSpec.navigate_to_selection_rule_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
                (EventSpec.pgn_reduced_export_format, ""),
                (EventSpec.pgn_export_format_no_comments, ""),
                (EventSpec.pgn_export_format, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self.set_event_bindings_frame(
            (
                (
                    EventSpec.navigate_to_partial_grid,
                    self.set_focus_partial_grid,
                ),
                (
                    EventSpec.navigate_to_active_partial,
                    self.set_focus_partialpanel_item,
                ),
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
                (
                    EventSpec.navigate_to_position_grid,
                    self.set_focus_position_grid,
                ),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
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
                (EventSpec.display_record_from_grid, self.display_game),
                (EventSpec.edit_record_from_grid, self.edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            )
        )

    def display_game(self, event=None):
        """Display selected game and cancel selection."""
        self.set_move_highlight(
            self.display_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        self.set_move_highlight(
            self.display_selected_item(self.pointer_popup_selection)
        )

    def edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        self.set_move_highlight(
            self.edit_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        self.set_move_highlight(
            self.edit_selected_item(self.pointer_popup_selection)
        )

    def on_game_change(self, instance):
        """Delegate to superclass if data source exists."""
        # datasource refers to a set derived from file and may need
        # to be recreated
        if self.get_data_source() is None:
            return
        super().on_data_change(instance)

    # Before version 4.3 collected_game[2] was always empty, and at time of
    # change it seemed wrong to include it even if occupied, so remove it from
    # displayed text rather than devise a way of generating it.
    def set_selection_text(self):
        """Set status bar to display main PGN Tags."""
        if self.selection:
            ss0 = self.selection[0]
            if ss0 in self.objects:
                t = self.objects[ss0].value.collected_game._tags
                supiai = self.ui.partial_items.active_item  # For line length.
                self.ui.statusbar.set_status_text(
                    "  ".join(
                        [t.get(k, "") for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS]
                    )
                    + supiai.get_selection_text_for_statusbar().join(
                        ("   (", ")")
                    )
                )
        else:
            self.ui.statusbar.set_status_text("")

    def is_visible(self):
        """Return True if list of games matching partials is displayed."""
        return str(self.get_frame()) in self.ui.position_partials_pw.panes()

    def is_payload_available(self):
        """Return True if connected to database and games displayed."""
        if not super().is_payload_available():
            return False
        return self.ui.partial_items.is_visible()

    def make_display_widget(self, sourceobject):
        """Return a GameDisplay for sourceobject."""
        game = super().make_display_widget(sourceobject)
        game.set_and_tag_item_text()
        return game

    def make_edit_widget(self, sourceobject):
        """Return a GameDisplayEdit for sourceobject."""
        game = super().make_edit_widget(sourceobject)
        game.set_and_tag_item_text(reset_undo=True)
        return game

    def focus_set_frame(self, event=None):
        """Delegate to superclass then set toolbar widget states."""
        super().focus_set_frame(event=event)
        self.ui.set_toolbarframe_disabled()


class GamePositionGames(GameListGrid):
    """Customized GameListGrid for list of games matching a game position.

    The grid is populated by a FullPositionDS instance from the
    dpt.fullpositionds or basecore.fullpositionds modules.
    """

    def __init__(self, ui):
        """Extend with position grid definition and bindings.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.position_games_pw, ui)
        self.make_header(ChessDBrowPosition.header_specification)
        self.__bind_on()
        self.set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self.display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self.edit_game_from_popup),
            ),
        )
        self.add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_active_game,
                self.set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self.add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self.add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self.set_event_bindings_frame(
            (
                (EventSpec.navigate_to_repertoire_grid, ""),
                (EventSpec.navigate_to_active_repertoire, ""),
                (EventSpec.navigate_to_repertoire_game_grid, ""),
                (EventSpec.navigate_to_partial_grid, ""),
                (EventSpec.navigate_to_active_partial, ""),
                (EventSpec.navigate_to_partial_game_grid, ""),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_game_grid, ""),
                (EventSpec.navigate_to_selection_rule_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
                (EventSpec.pgn_reduced_export_format, ""),
                (EventSpec.pgn_export_format_no_comments, ""),
                (EventSpec.pgn_export_format, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self.set_event_bindings_frame(
            (
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
                (
                    EventSpec.navigate_to_partial_grid,
                    self.set_focus_partial_grid,
                ),
                (
                    EventSpec.navigate_to_active_partial,
                    self.set_focus_partialpanel_item,
                ),
                (
                    EventSpec.navigate_to_partial_game_grid,
                    self.set_focus_partial_game_grid,
                ),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
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
                (EventSpec.display_record_from_grid, self.display_game),
                (EventSpec.edit_record_from_grid, self.edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            )
        )

    def display_game(self, event=None):
        """Display selected game and cancel selection."""
        self.set_move_highlight(
            self.display_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        self.set_move_highlight(
            self.display_selected_item(self.pointer_popup_selection)
        )

    def edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        self.set_move_highlight(
            self.edit_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        self.set_move_highlight(
            self.edit_selected_item(self.pointer_popup_selection)
        )

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for game key or None.

        Add arguments to **kargs for grid_row method in PositionRow class.

        """
        kargs.update(
            position=self.datasource.fullposition,
            context=self.ui.get_active_game_move(),
        )
        return super().set_row(key, dodefaultaction=dodefaultaction, **kargs)

    def on_game_change(self, instance):
        """Delegate to superclass if data source exists."""
        # datasource refers to a set derived from file and may need
        # to be recreated
        if self.get_data_source() is None:
            return
        # It may be on_data_change(None) should prevent GamePositionGames
        # being cleared on deleting game, but it does not.
        super().on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display main PGN Tags."""
        if self.selection:
            ss0 = self.selection[0]
            if ss0 in self.objects:
                t = self.objects[ss0].score.collected_game._tags
                self.ui.statusbar.set_status_text(
                    "  ".join(
                        [t.get(k, "") for k in STATUS_SEVEN_TAG_ROSTER_EVENT]
                    )
                )
        else:
            self.ui.statusbar.set_status_text("")

    def is_visible(self):
        """Return True if list of matching games is displayed."""
        return str(self.get_frame()) in self.ui.position_games_pw.panes()

    def is_payload_available(self):
        """Return True if connected to database and games displayed."""
        if not super().is_payload_available():
            return False
        return self.ui.game_items.is_visible()

    def make_display_widget(self, sourceobject):
        """Return a GameDisplay for sourceobject."""
        game = super().make_display_widget(sourceobject)

        # decode_move_number may be put in self.game
        # game.set_and_tag_item_text(
        #    str(sourceobject.decode_move_number(self.selection[0][-1])))
        game.set_and_tag_item_text()

        return game

    def make_edit_widget(self, sourceobject):
        """Return a GameDisplayEdit for sourceobject."""
        game = super().make_edit_widget(sourceobject)

        # decode_move_number may be put in self.game
        # game.set_and_tag_item_text(
        #    str(sourceobject.decode_move_number(self.selection[0][-1])),
        #    reset_undo=True)
        game.set_and_tag_item_text(reset_undo=True)

        return game

    def focus_set_frame(self, event=None):
        """Delegate to superclass then set toolbar widget states."""
        super().focus_set_frame(event=event)
        self.ui.set_toolbarframe_disabled()


class TagRosterGrid(GameListGrid):
    """Customized GameListGrid for list of games on database.

    The grid is usually populated by a DataSource instance from the
    solentware_grid.core.dataclient module, either all games or by index or
    filter, but can be populated by a ChessQLGames instance from the dpt.cqlds
    or basecore.cqlds modules, when a selection rule is invoked.
    """

    def __init__(self, ui):
        """Extend with definition and bindings for games on database grid.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.games_pw, ui)
        self.make_header(ChessDBrowGame.header_specification)
        self.__bind_on()
        self.set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self.display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self.edit_game_from_popup),
            ),
        )
        self.add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self.set_focus_gamepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self.add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self.add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self.set_event_bindings_frame(
            (
                (EventSpec.navigate_to_repertoire_grid, ""),
                (EventSpec.navigate_to_active_repertoire, ""),
                (EventSpec.navigate_to_repertoire_game_grid, ""),
                (EventSpec.navigate_to_partial_grid, ""),
                (EventSpec.navigate_to_active_partial, ""),
                (EventSpec.navigate_to_partial_game_grid, ""),
                (EventSpec.navigate_to_position_grid, ""),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_selection_rule_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
                (EventSpec.pgn_reduced_export_format, ""),
                (EventSpec.pgn_export_format_no_comments, ""),
                (EventSpec.pgn_export_format, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self.set_event_bindings_frame(
            (
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
                (
                    EventSpec.navigate_to_partial_grid,
                    self.set_focus_partial_grid,
                ),
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
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (
                    EventSpec.navigate_to_selection_rule_grid,
                    self.set_focus_selection_rule_grid,
                ),
                (
                    EventSpec.navigate_to_active_selection_rule,
                    self.set_focus_selectionpanel_item,
                ),
                (EventSpec.display_record_from_grid, self.display_game),
                (EventSpec.edit_record_from_grid, self.edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            )
        )

    def display_game(self, event=None):
        """Display selected game and cancel selection."""
        self.display_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        self.display_selected_item(self.pointer_popup_selection)

    def edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        self.edit_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        self.edit_selected_item(self.pointer_popup_selection)

    def on_game_change(self, instance):
        """Delegate to superclass if data source exists."""
        # may turn out to be just to catch datasource is None
        if self.get_data_source() is None:
            return
        super().on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display main PGN Tags."""
        if self.selection:
            ss0 = self.selection[0]
            if ss0 in self.objects:
                tags = self.objects[ss0].value.collected_game._tags
                self.ui.statusbar.set_status_text(
                    "  ".join(
                        [
                            tags.get(k, "")
                            for k in STATUS_SEVEN_TAG_ROSTER_SCORE
                        ]
                    )
                )
        else:
            self.ui.statusbar.set_status_text("")

    def is_visible(self):
        """Return True if list of games is displayed."""
        return str(self.get_frame()) in self.ui.games_pw.panes()

    def make_display_widget(self, sourceobject):
        """Return a GameDisplay for sourceobject."""
        game = super().make_display_widget(sourceobject)
        game.set_and_tag_item_text()
        return game

    def make_edit_widget(self, sourceobject):
        """Return a GameDisplayEdit for sourceobject."""
        game = super().make_edit_widget(sourceobject)
        game.set_and_tag_item_text(reset_undo=True)
        return game

    def focus_set_frame(self, event=None):
        """Delegate to superclass then set toolbar widget states."""
        super().focus_set_frame(event=event)
        ui = self.ui
        if ui.base_games.datasource.dbname in ui.allow_filter:
            ui.set_toolbarframe_normal(ui.move_to_game, ui.filter_game)
        else:
            ui.set_toolbarframe_disabled()

    def set_selection(self, key):
        """Hack to fix edge case when inserting records using apsw or sqlite3.

        Workaround a KeyError exception when a record is inserted while a grid
        keyed by a secondary index with only one key value in the index is on
        display.

        """
        try:
            super().set_selection(key)
        except KeyError:
            tkinter.messagebox.showinfo(
                parent=self.parent,
                title="Insert Game Workaround",
                message="".join(
                    (
                        "All records have same name on this display.\n\n",
                        "The new record has been inserted but you need to ",
                        "switch to another index, and back, to see the ",
                        "record in the list.",
                    )
                ),
            )

    def move_to_row_in_grid(self, key):
        """Navigate grid to nearest row starting with key."""
        if self.datasource.dbname in PLAYER_NAME_TAGS:
            if isinstance(key, str):
                key = " ".join(re_normalize_player_name.findall(key))
        super().move_to_row_in_grid(key)

    def load_new_partial_key(self, key):
        """Transform key if it's a str and a player's name then delegate."""
        if self.datasource.dbname in PLAYER_NAME_TAGS:
            if isinstance(key, str):
                key = " ".join(re_normalize_player_name.findall(key))
        super().load_new_partial_key(key)


class RepertoireGrid(GameListGrid):
    """Customized GameListGrid for list of repertoires on database."""

    def __init__(self, ui):
        """Extend with definition and bindings for games on database grid.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.repertoires_pw, ui)
        self.make_header(ChessDBrowRepertoire.header_specification)
        self.__bind_on()
        self.set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self.display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self.edit_game_from_popup),
            ),
        )
        self.add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self.set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self.add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self.add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self.set_event_bindings_frame(
            (
                (EventSpec.navigate_to_active_repertoire, ""),
                (EventSpec.navigate_to_repertoire_game_grid, ""),
                (EventSpec.navigate_to_partial_grid, ""),
                (EventSpec.navigate_to_active_partial, ""),
                (EventSpec.navigate_to_partial_game_grid, ""),
                (EventSpec.navigate_to_position_grid, ""),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_game_grid, ""),
                (EventSpec.navigate_to_selection_rule_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
                (EventSpec.pgn_export_format_no_comments, ""),
                (EventSpec.pgn_export_format, ""),
                (EventSpec.pgn_import_format, ""),
                (EventSpec.text_internal_format, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self.set_event_bindings_frame(
            (
                (
                    EventSpec.navigate_to_active_repertoire,
                    self.set_focus_repertoirepanel_item,
                ),
                (
                    EventSpec.navigate_to_repertoire_game_grid,
                    self.set_focus_repertoire_game_grid,
                ),
                (
                    EventSpec.navigate_to_partial_grid,
                    self.set_focus_partial_grid,
                ),
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
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
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
                (EventSpec.display_record_from_grid, self.display_game),
                (EventSpec.edit_record_from_grid, self.edit_game),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            )
        )

    def display_game(self, event=None):
        """Display selected repertoire and cancel selection."""
        self.display_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def display_game_from_popup(self, event=None):
        """Display repertoire selected by pointer."""
        self.display_selected_item(self.pointer_popup_selection)

    def edit_game(self, event=None):
        """Display selected repertoire for editing and cancel selection."""
        self.edit_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def edit_game_from_popup(self, event=None):
        """Display repertoire with editing allowed selected by pointer."""
        self.edit_selected_item(self.pointer_popup_selection)

    def on_game_change(self, instance):
        """Delegate to superclass if data source exists."""
        # may turn out to be just to catch datasource is None
        if self.get_data_source() is None:
            return
        super().on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display main PGN Tags."""
        if self.selection:
            ss0 = self.selection[0]
            if ss0 in self.objects:
                tags = self.objects[ss0].value.collected_game._tags
                self.ui.statusbar.set_status_text(
                    "  ".join([tags.get(k, "") for k in REPERTOIRE_TAG_ORDER])
                )
        else:
            self.ui.statusbar.set_status_text("")

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordRepertoireUpdate()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_delete_dialog(
            self.objects[key], oldobject, modal, title="Delete Repertoire"
        )

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordRepertoireUpdate(),
            ChessDBrecordRepertoireUpdate(),
            False,
            modal,
            title="Edit Repertoire",
        )

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordRepertoireUpdate(),
            ChessDBrecordRepertoireUpdate(),
            True,
            modal,
            title="Edit Repertoire",
        )

    def launch_insert_new_record(self, modal=True):
        """Create insert dialogue."""
        newobject = ChessDBrecordRepertoireUpdate()
        instance = self.datasource.new_row()
        instance.srvalue = repr(EMPTY_REPERTOIRE_GAME + UNKNOWN_RESULT)
        self.create_edit_dialog(
            instance, newobject, None, False, modal, title="New Repertoire"
        )

    def launch_show_record(self, key, modal=True):
        """Create show dialogue."""
        oldobject = ChessDBrecordRepertoireUpdate()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_show_dialog(
            self.objects[key], oldobject, modal, title="Show Repertoire"
        )

    def make_display_widget(self, sourceobject):
        """Return a RepertoireDisplay for sourceobject."""
        game = RepertoireDisplay(
            master=self.ui.view_repertoires_pw,
            ui=self.ui,
            items_manager=self.ui.repertoire_items,
            itemgrid=self.ui.repertoire_games,
            sourceobject=sourceobject,
        )
        game.set_position_analysis_data_source()
        game.collected_game = next(
            PGN(game_class=game.gameclass).read_games(
                sourceobject.get_srvalue()
            )
        )
        game.set_and_tag_item_text()
        return game

    def make_edit_widget(self, sourceobject):
        """Return a RepertoireDisplayEdit for sourceobject."""
        game = RepertoireDisplayEdit(
            master=self.ui.view_repertoires_pw,
            ui=self.ui,
            items_manager=self.ui.repertoire_items,
            itemgrid=self.ui.repertoire_games,
            sourceobject=sourceobject,
        )
        game.set_position_analysis_data_source()
        game.collected_game = next(
            PGN(game_class=game.gameclass).read_games(
                sourceobject.get_srvalue()
            )
        )
        game.set_and_tag_item_text(reset_undo=True)
        return game

    def display_selected_item(self, key):
        """Display and return a RepertoireDisplay for selected game."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplay is to be put.
        # Yes because GameDisplayEdit (see edit_selected_item) includes
        # extra widgets. Want to say game.widget.destroy() eventually.
        # Read make_display_widget for GameDisplay and GameDisplayEdit.
        game = self.make_display_widget(selected)
        self.ui.add_repertoire_to_display(game)
        self.ui.repertoire_items.increment_object_count(key)
        self.ui.repertoire_items.set_itemmap(game, key)
        self.set_properties(key)
        return game

    def edit_selected_item(self, key):
        """Display and return a RepertoireDisplayEdit for selected game."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplayEdit is to be put.
        # Yes because GameDisplay (see display_selected_item) includes
        # less widgets. Want to say game.widget.destroy() eventually.
        # Read make_edit_widget for GameDisplay and GameDisplayEdit.
        game = self.make_edit_widget(selected)
        self.ui.add_repertoire_to_display(game)
        self.ui.repertoire_items.increment_object_count(key)
        self.ui.repertoire_items.set_itemmap(game, key)
        self.set_properties(key)
        return game

    def export_pgn(self, event=None):
        """Export selected repertoires in PGN export format."""
        self.ui.export_report(
            exporters.export_selected_repertoires_pgn(
                self, self.ui.get_export_filename("Repertoires", pgn=True)
            ),
            "Repertoires",
        )

    def export_pgn_no_comments(self, event=None):
        """Export selected repertoires in PGN export format no comments."""
        self.ui.export_report(
            exporters.export_selected_repertoires_pgn_no_comments(
                self,
                self.ui.get_export_filename(
                    "Repertoires (no comments)", pgn=True
                ),
            ),
            "Repertoires (no comments)",
        )

    def export_text(self, event=None):
        """Export selected repertoires as text."""
        self.ui.export_report(
            exporters.export_selected_repertoires_text(
                self,
                self.ui.get_export_filename(
                    "Repertoires (internal format)", pgn=False
                ),
            ),
            "Repertoires (internal format)",
        )

    def export_pgn_import_format(self, event=None):
        """Export selected games in a PGN import format."""
        self.ui.export_report(
            exporters.export_selected_repertoires_pgn_import_format(
                self,
                self.ui.get_export_filename(
                    "Repertoires (import format)", pgn=True
                ),
            ),
            "Repertoires (import format)",
        )

    def is_visible(self):
        """Return True if list of repertoire games is displayed."""
        return str(self.get_frame()) in self.ui.repertoires_pw.panes()

    def set_properties(self, key, dodefaultaction=True):
        """Return True if properties for game key set or False."""
        # Skip the immediate superclass method to not touch self.game_items
        # pylint bad-super-call message given.
        if super(GameListGrid, self).set_properties(
            key, dodefaultaction=False
        ):
            return True
        if self.ui.repertoire_items.object_display_count(key):
            self._set_background_on_display_row_under_pointer(key)
            return True
        if dodefaultaction:
            self._set_background_normal_row_under_pointer(key)
            return True
        return False

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for game key or None."""
        # Skip the immediate superclass method to not touch self.game_items
        # pylint bad-super-call message given.
        row = super(GameListGrid, self).set_row(
            key, dodefaultaction=False, **kargs
        )
        if row is not None:
            return row
        if key not in self.keys:
            return None
        if self.ui.repertoire_items.object_display_count(key):
            return self.objects[key].grid_row_on_display(**kargs)
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        else:
            return None

    def focus_set_frame(self, event=None):
        """Delegate to superclass then set toolbar widget states."""
        super().focus_set_frame(event=event)
        self.ui.set_toolbarframe_normal(
            self.ui.move_to_repertoire, self.ui.filter_repertoire
        )

    def set_selection(self, key):
        """Hack to fix edge case when inserting records using apsw or sqlite3.

        Workaround a KeyError exception when a record is inserted while a grid
        keyed by a secondary index with only one key value in the index is on
        display.

        """
        try:
            super().set_selection(key)
        except KeyError:
            tkinter.messagebox.showinfo(
                parent=self.parent,
                title="Insert Repertoire Workaround",
                message="".join(
                    (
                        "All records have same name on this display.\n\nThe ",
                        "new record has been inserted but you need to Hide, ",
                        "and then Show, the display to see the record in ",
                        "the list.",
                    )
                ),
            )


class RepertoirePositionGames(GameListGrid):
    """Customized GameListGrid for list of games matching repertoire position.

    The grid is populated by a FullPositionDS instance from the
    dpt.fullpositionds or basecore.fullpositionds modules.
    """

    def __init__(self, ui):
        """Extend with position grid definition and bindings.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.position_repertoires_pw, ui)
        self.make_header(ChessDBrowPosition.header_specification)
        self.__bind_on()
        self.set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self.display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self.edit_game_from_popup),
            ),
        )
        self.add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self.set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item_command,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self.add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self.add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self.set_event_bindings_frame(
            (
                (EventSpec.navigate_to_repertoire_grid, ""),
                (EventSpec.navigate_to_active_repertoire, ""),
                (EventSpec.navigate_to_partial_grid, ""),
                (EventSpec.navigate_to_active_partial, ""),
                (EventSpec.navigate_to_partial_game_grid, ""),
                (EventSpec.navigate_to_position_grid, ""),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_game_grid, ""),
                (EventSpec.navigate_to_selection_rule_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
                (EventSpec.pgn_reduced_export_format, ""),
                (EventSpec.pgn_export_format_no_comments, ""),
                (EventSpec.pgn_export_format, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self.set_event_bindings_frame(
            (
                (
                    EventSpec.navigate_to_repertoire_grid,
                    self.set_focus_repertoire_grid,
                ),
                (
                    EventSpec.navigate_to_active_repertoire,
                    self.set_focus_repertoirepanel_item,
                ),
                (
                    EventSpec.navigate_to_partial_grid,
                    self.set_focus_partial_grid,
                ),
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
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
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
                (EventSpec.display_record_from_grid, self.display_game),
                (EventSpec.edit_record_from_grid, self.edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self.export_text),
            )
        )

    def display_game(self, event=None):
        """Display selected game and cancel selection."""
        self.set_move_highlight(
            self.display_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        self.set_move_highlight(
            self.display_selected_item(self.pointer_popup_selection)
        )

    def edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        self.set_move_highlight(
            self.edit_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        self.set_move_highlight(
            self.edit_selected_item(self.pointer_popup_selection)
        )

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for game key or None.

        Add arguments to **kargs for grid_row method in PositionRow class.

        """
        kargs.update(
            position=self.datasource.fullposition,
            context=self.ui.get_active_repertoire_move(),
        )
        return super().set_row(key, dodefaultaction=dodefaultaction, **kargs)

    def on_game_change(self, instance):
        """Delegate to superclass if data source exists."""
        # datasource refers to a set derived from file and may need
        # to be recreated
        if self.get_data_source() is None:
            return
        super().on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display main PGN Tags."""
        if self.selection:
            ss0 = self.selection[0]
            if ss0 in self.objects:
                t = self.objects[ss0].score.collected_game._tags
                self.ui.statusbar.set_status_text(
                    "  ".join(
                        [t.get(k, "") for k in STATUS_SEVEN_TAG_ROSTER_EVENT]
                    )
                )
        else:
            self.ui.statusbar.set_status_text("")

    def is_visible(self):
        """Return True if list of matching repertoire games is displayed."""
        return str(self.get_frame()) in self.ui.position_repertoires_pw.panes()

    def is_payload_available(self):
        """Return True if connected to database and games displayed."""
        if not super().is_payload_available():
            return False
        return self.ui.repertoire_items.is_visible()

    def make_display_widget(self, sourceobject):
        """Return a GameDisplay for sourceobject."""
        game = super().make_display_widget(sourceobject)
        game.set_and_tag_item_text()
        return game

    def make_edit_widget(self, sourceobject):
        """Return a GameDisplayEdit for sourceobject."""
        game = super().make_edit_widget(sourceobject)
        game.set_and_tag_item_text(reset_undo=True)
        return game

    def focus_set_frame(self, event=None):
        """Delegate to superclass then set toolbar widget states."""
        super().focus_set_frame(event=event)
        self.ui.set_toolbarframe_disabled()
