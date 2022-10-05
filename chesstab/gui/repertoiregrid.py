# gamelistgrid.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of games on chess database."""

import tkinter.messagebox

from pgn_read.core.parser import PGN

from ..core.chessrecord import (
    ChessDBrecordRepertoireUpdate,
)
from .positionrow import ChessDBrowPosition
from .repertoirerow import ChessDBrowRepertoire
from .repertoiredisplay import RepertoireDisplay, RepertoireDisplayEdit
from .constants import (
    STATUS_SEVEN_TAG_ROSTER_EVENT,
    EMPTY_REPERTOIRE_GAME,
)
from ..core import export_repertoire
from .eventspec import EventSpec
from ..core.constants import REPERTOIRE_TAG_ORDER, UNKNOWN_RESULT
from .gamelistgrid import GameListGrid


class RepertoireGrid(GameListGrid):
    """Customized GameListGrid for list of repertoires on database."""

    def __init__(self, ui):
        """Extend with definition and bindings for games on database grid.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.repertoires_pw, ui)
        self.make_header(ChessDBrowRepertoire.header_specification)
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
        self._set_event_bindings_frame(
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
                (EventSpec.display_record_from_grid, self._display_game),
                (EventSpec.edit_record_from_grid, self._edit_game),
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
        """Display selected repertoire and cancel selection."""
        del event
        self._display_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def _display_game_from_popup(self, event=None):
        """Display repertoire selected by pointer."""
        del event
        self._display_selected_item(self.pointer_popup_selection)

    def _edit_game(self, event=None):
        """Display selected repertoire for editing and cancel selection."""
        del event
        self._edit_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def _edit_game_from_popup(self, event=None):
        """Display repertoire with editing allowed selected by pointer."""
        del event
        self._edit_selected_item(self.pointer_popup_selection)

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

    def _display_selected_item(self, key):
        """Display and return a RepertoireDisplay for selected game."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplay is to be put.
        # Yes because GameDisplayEdit (see _edit_selected_item) includes
        # extra widgets. Want to say game.widget.destroy() eventually.
        # Read make_display_widget for GameDisplay and GameDisplayEdit.
        game = self.make_display_widget(selected)
        self.ui.add_repertoire_to_display(game)
        self.ui.repertoire_items.increment_object_count(key)
        self.ui.repertoire_items.set_itemmap(game, key)
        self.set_properties(key)
        return game

    def _edit_selected_item(self, key):
        """Display and return a RepertoireDisplayEdit for selected game."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplayEdit is to be put.
        # Yes because GameDisplay (see _display_selected_item) includes
        # less widgets. Want to say game.widget.destroy() eventually.
        # Read make_edit_widget for GameDisplay and GameDisplayEdit.
        game = self.make_edit_widget(selected)
        self.ui.add_repertoire_to_display(game)
        self.ui.repertoire_items.increment_object_count(key)
        self.ui.repertoire_items.set_itemmap(game, key)
        self.set_properties(key)
        return game

    def _export_pgn(self, event=None):
        """Export selected repertoires in PGN export format."""
        self.ui.export_report(
            export_repertoire.export_selected_repertoires_pgn(
                self, self.ui.get_export_filename("Repertoires", pgn=True)
            ),
            "Repertoires",
        )

    def _export_pgn_no_comments(self, event=None):
        """Export selected repertoires in PGN export format no comments."""
        self.ui.export_report(
            export_repertoire.export_selected_repertoires_pgn_no_comments(
                self,
                self.ui.get_export_filename(
                    "Repertoires (no comments)", pgn=True
                ),
            ),
            "Repertoires (no comments)",
        )

    def _export_text(self, event=None):
        """Export selected repertoires as text."""
        self.ui.export_report(
            export_repertoire.export_selected_repertoires_text(
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
            export_repertoire.export_selected_repertoires_pgn_import_format(
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
                (EventSpec.display_record_from_grid, self._display_game),
                (EventSpec.edit_record_from_grid, self._edit_game),
                (
                    EventSpec.pgn_reduced_export_format,
                    self._export_pgn_reduced_export_format,
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
