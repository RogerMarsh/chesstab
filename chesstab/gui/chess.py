# chess.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define top level user interface to a ChessTab database.

Add menu options to insert and edit chess games.
"""

import tkinter

from solentware_bind.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN

from .. import (
    APPLICATION_NAME,
    PARTIAL_POSITION_MODULE,
)
from ..core.constants import UNKNOWN_RESULT
from .gamedisplay import GameDisplayInsert
from . import constants
from .uci import UCI
from .chess_ui import ChessUI
from .eventspec import EventSpec
from . import _chess
from . import help_
from .cqlinsert import CQLInsert

ExceptionHandler.set_application_name(APPLICATION_NAME)


class Chess(_chess.Chess):
    """Connect a chess database with User Interface."""

    def _create_menu3_game(self, menus, menubar):
        """Create menu specification for entering a new game."""
        menu3 = tkinter.Menu(menubar, name="game", tearoff=False)
        menus.append(menu3)
        menubar.add_cascade(label="Game", menu=menu3, underline=0)
        menu3.add_separator()
        for accelerator, function in (
            (EventSpec.menu_game_new_game, self._game_new_game),
        ):
            menu3.add_command(
                label=accelerator[1],
                command=self.try_command(function, menu3),
                underline=accelerator[3],
            )
        menu3.add_separator()

    def _game_new_game(self):
        """Enter a new game (callback for Menu option)."""
        self._new_game()

    def _new_game(self):
        """Enter a new game."""
        game = GameDisplayInsert(
            master=self.ui.view_games_pw,
            ui=self.ui,
            items_manager=self.ui.game_items,
            itemgrid=self.ui.game_games,
        )
        game.set_position_analysis_data_source()
        game.collected_game = next(
            PGN(game_class=game.gameclass).read_games(
                "".join(
                    (
                        constants.EMPTY_SEVEN_TAG_ROSTER,
                        UNKNOWN_RESULT,
                    )
                )
            )
        )
        game.set_and_tag_item_text()
        self.ui.add_game_to_display(game)
        try:
            # Is new window only one available for user interaction?
            if self.root.focus_displayof() != self.root:
                return
        except KeyError:
            # Launch; Database Open; Database Close; Game New
            pass

        # Wrap to take account of self.ui.single_view
        self.ui.game_items.active_item.takefocus_widget.focus_set()

    def _create_menu4_position(self, menus, menubar):
        """Create menu specification for position queries."""
        menu4 = tkinter.Menu(menubar, name="position", tearoff=False)
        menus.append(menu4)
        menubar.add_cascade(label="Position", menu=menu4, underline=0)
        for accelerator, function in (
            (EventSpec.menu_position_partial, self._position_partial),
            (EventSpec.menu_show, self._position_show),
            (EventSpec.menu_hide, self._position_hide),
        ):
            menu4.add_command(
                label=accelerator[1],
                command=self.try_command(function, menu4),
                underline=accelerator[3],
            )
        menu4.add_separator()
        for index in (1, 0):
            menu4.insert_separator(index)

    def _create_chessui_instance(self, toppane, menu7, menu8, toolbarframe):
        """Return ChessUI instance."""
        return ChessUI(
            toppane,
            statusbar=self.statusbar,
            uci=UCI(menu7, menu8),
            toolbarframe=toolbarframe,
        )

    def _help_guide(self):
        """Display brief User Guide for Chess application."""
        help_.help_guide(self.root)

    def _help_selection(self):
        """Display description of selection rules for Chess application."""
        help_.help_selection(self.root)

    def _help_file_size(self):
        """Display brief instructions for file size dialogue."""
        help_.help_file_size(self.root)

    def _help_notes(self):
        """Display technical notes about Chess application."""
        help_.help_notes(self.root)

    def _help_about(self):
        """Display information about Chess application."""
        help_.help_about(self.root)

    @staticmethod
    def _get_partial_position_module_name(enginename):
        """Return name of partial position module."""
        return PARTIAL_POSITION_MODULE[enginename]

    def _create_cql_display_insert_instance(self):
        """Return a ..gui.cqlinsert.CQLInsert instance."""
        position = CQLInsert(
            master=self.ui.view_partials_pw,
            ui=self.ui,
            items_manager=self.ui.partial_items,
            itemgrid=self.ui.partial_games,
        )
        position.cql_statement.prepare_cql_statement("")
        return position
