# gamelistgrid.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of games on chess database."""

import tkinter

from solentware_grid.datagrid import DataGrid

from pgn_read.core.parser import PGN

from ..core.chessrecord import ChessDBrecordGameUpdate
from .gamedisplay import GameDisplay, GameDisplayEdit
from .constants import EMPTY_SEVEN_TAG_ROSTER
from ..core import export_game
from .display import Display
from ..shared.cql_gamelist_query import CQLGameListQuery
from ..shared.allgrid import AllGrid
from ..core.constants import UNKNOWN_RESULT
from .score import ScoreMapToBoardException


class _BookmarkStatusText:
    """Isolate set_selection_text call.

    This class is added to the ignored-classes list in pylint.conf.

    The associated super().bookmark_up and super().bookmark_down calls
    refer to DataGrid methods in the solentware_grid project.

    """

    def _set_selection_text_bookmark(self):
        """Show selection summary in status bar and hide call from pylint."""
        self.set_selection_text()


class GameListGrid(
    AllGrid,
    CQLGameListQuery,
    _BookmarkStatusText,
    DataGrid,
    Display,
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
        self.ui = ui
        self._configure_frame_and_initial_event_bindings()

    def _display_selected_item_kind(self, key, selected):
        # Should the Frame containing board and score be created here and
        # passed to GameDisplay. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # GameDisplay is to be put.
        # Yes because GameDisplayEdit (see _edit_selected_item) includes
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

    def _edit_selected_item(self, key):
        """Create display and return a GameDisplayEdit for selected game."""
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
        self.ui.add_game_to_display(game)
        self.ui.game_items.increment_object_count(key)
        self.ui.game_items.set_itemmap(game, key)
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
        if self.ui.game_items.object_display_count(key):
            return self.objects[key].grid_row_on_display(**kargs)
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        return None

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordGameUpdate()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        try:
            self.create_delete_dialog(
                self.objects[key], oldobject, modal, title="Delete Game"
            )
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Delete Game")

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        try:
            self.create_edit_dialog(
                self.objects[key],
                ChessDBrecordGameUpdate(),
                ChessDBrecordGameUpdate(),
                False,
                modal,
                title="Edit Game",
            )
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Edit Game")

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        try:
            self.create_edit_dialog(
                self.objects[key],
                ChessDBrecordGameUpdate(),
                ChessDBrecordGameUpdate(),
                True,
                modal,
                title="Edit Game",
            )
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Edit Game")

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
        try:
            self.create_show_dialog(
                self.objects[key], oldobject, modal, title="Show Game"
            )
        except ScoreMapToBoardException as exc:
            self._score_map_exception_dialogue(exc, "Show Game")

    def _set_object_panel_item_properties(self):
        """Adjust properties of game_items to fit configure canvas event."""
        ui = self.ui
        for key in ui.game_items.object_panel_count:
            self.set_properties(key)

    @staticmethod
    def set_move_highlight(game):
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
        self._set_selection_text_bookmark()

    def bookmark_up(self):
        """Extend to show selection summary in status bar."""
        super().bookmark_up()
        self._set_selection_text_bookmark()

    def _export_text(self, event=None):
        """Export selected games as text."""
        del event
        self.ui.export_report(
            export_game.export_selected_games_text(
                self,
                self.ui.get_export_filename(
                    "Games (internal format)", pgn=False
                ),
            ),
            "Games (internal format)",
        )

    def export_pgn_import_format(self, event=None):
        """Export selected games in a PGN import format."""
        del event
        self.ui.export_report(
            export_game.export_selected_games_pgn_import_format(
                self,
                self.ui.get_export_filename("Games (import format)", pgn=True),
            ),
            "Games (import format)",
        )

    def _export_pgn(self, event=None):
        """Export selected games in PGN export format."""
        del event
        self.ui.export_report(
            export_game.export_selected_games_pgn(
                self, self.ui.get_export_filename("Games", pgn=True)
            ),
            "Games",
        )

    def _export_pgn_reduced_export_format(self, event=None):
        """Export selected games in PGN Reduced Export Format."""
        del event
        self.ui.export_report(
            export_game.export_selected_games_pgn_reduced_export_format(
                self,
                self.ui.get_export_filename(
                    "Games (reduced export format)", pgn=True
                ),
            ),
            "Games (reduced export format)",
        )

    def _export_pgn_no_comments_no_ravs(self, event=None):
        """Export selected games as PGN excluding all comments and RAVs."""
        del event
        self.ui.export_report(
            export_game.export_selected_games_pgn_no_comments_no_ravs(
                self,
                self.ui.get_export_filename(
                    "Games (no comments no ravs)", pgn=True
                ),
            ),
            "Games (no comments no ravs)",
        )

    def _export_pgn_no_comments(self, event=None):
        """Export selected games as PGN excluding all commentary tokens."""
        del event
        self.ui.export_report(
            export_game.export_selected_games_pgn_no_comments(
                self,
                self.ui.get_export_filename("Games (no comments)", pgn=True),
            ),
            "Games (no comments)",
        )

    def _score_map_exception_dialogue(self, exception_instance, title):
        """Display dialogue to report problem displaying game."""
        tkinter.messagebox.showinfo(
            parent=self.get_frame(),
            title=title,
            message=str(exception_instance),
        )
