# gamelistgrid.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of games on chess database."""

import tkinter.messagebox

from ..core.chessrecord import (
    PLAYER_NAME_TAGS,
    re_normalize_player_name,
)
from .gamerow import ChessDBrowGame
from .positionrow import ChessDBrowPosition
from .constants import (
    STATUS_SEVEN_TAG_ROSTER_EVENT,
    STATUS_SEVEN_TAG_ROSTER_SCORE,
    STATUS_SEVEN_TAG_ROSTER_PLAYERS,
)
from .eventspec import EventSpec
from .gamelistgrid import GameListGrid
from .score import ScoreMapToBoardException


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
        self._set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self._display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self._edit_game_from_popup),
            ),
        )
        self._add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self._export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self._export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self._export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self._export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self._set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self._set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self._set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self._set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self._add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self._add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self._set_event_bindings_frame(
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
        self._set_event_bindings_frame(
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
                (EventSpec.display_record_from_grid, self._display_game),
                (EventSpec.edit_record_from_grid, self._edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self._export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self._export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self._export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self._export_text),
            )
        )

    def _display_game(self, event=None):
        """Display selected game and cancel selection."""
        del event
        self.set_move_highlight(
            self._display_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def _display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        del event
        self.set_move_highlight(
            self._display_selected_item(self.pointer_popup_selection)
        )

    def _edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        del event
        self.set_move_highlight(
            self._edit_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def _edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        del event
        self.set_move_highlight(
            self._edit_selected_item(self.pointer_popup_selection)
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
                tags = self.objects[ss0].value.collected_game.pgn_tags
                supiai = self.ui.partial_items.active_item  # For line length.
                self.ui.statusbar.set_status_text(
                    "  ".join(
                        [
                            tags.get(k, "")
                            for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS
                        ]
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
        self._set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self._display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self._edit_game_from_popup),
            ),
        )
        self._add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self._export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self._export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self._export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self._export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_active_game,
                self._set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self._set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self._set_focus_partialpanel_item_command,
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
                self._set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self._add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self._add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self._set_event_bindings_frame(
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
        self._set_event_bindings_frame(
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
                (EventSpec.display_record_from_grid, self._display_game),
                (EventSpec.edit_record_from_grid, self._edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self._export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self._export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self._export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self._export_text),
            )
        )

    def _display_game(self, event=None):
        """Display selected game and cancel selection."""
        del event
        self.set_move_highlight(
            self._display_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def _display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        del event
        self.set_move_highlight(
            self._display_selected_item(self.pointer_popup_selection)
        )

    def _edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        del event
        self.set_move_highlight(
            self._edit_selected_item(self.get_visible_selected_key())
        )
        self.cancel_selection()

    def _edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        del event
        self.set_move_highlight(
            self._edit_selected_item(self.pointer_popup_selection)
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
                tags = self.objects[ss0].score.collected_game.pgn_tags
                self.ui.statusbar.set_status_text(
                    "  ".join(
                        [
                            tags.get(k, "")
                            for k in STATUS_SEVEN_TAG_ROSTER_EVENT
                        ]
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
        self._set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self._display_game_from_popup,
                ),
                (EventSpec.edit_record_from_grid, self._edit_game_from_popup),
            ),
        )
        self._add_cascade_menu_to_popup(
            "Export",
            self.menupopup,
            (
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self._export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self._export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self._export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self._export_text),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self._set_focus_gamepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self._set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_partial,
                self._set_focus_partialpanel_item_command,
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
                self._set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self._add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self._add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self._set_event_bindings_frame(
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
        self._set_event_bindings_frame(
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
                (EventSpec.display_record_from_grid, self._display_game),
                (EventSpec.edit_record_from_grid, self._edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self._export_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self._export_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self._export_pgn),
                (EventSpec.pgn_import_format, self.export_pgn_import_format),
                (EventSpec.text_internal_format, self._export_text),
            )
        )

    def _display_game(self, event=None):
        """Display selected game and cancel selection."""
        del event
        try:
            self._display_selected_item(self.get_visible_selected_key())
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Display Game")
        self.cancel_selection()

    def _display_game_from_popup(self, event=None):
        """Display game selected by pointer."""
        del event
        try:
            self._display_selected_item(self.pointer_popup_selection)
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Display Game")

    def _edit_game(self, event=None):
        """Display selected game with editing allowed and cancel selection."""
        del event
        try:
            self._edit_selected_item(self.get_visible_selected_key())
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Display Game for Edit")
        self.cancel_selection()

    def _edit_game_from_popup(self, event=None):
        """Display game with editing allowed selected by pointer."""
        del event
        try:
            self._edit_selected_item(self.pointer_popup_selection)
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Display Game for Edit")

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
                tags = self.objects[ss0].value.collected_game.pgn_tags
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
