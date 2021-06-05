# chess_ui.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define the User Interface in detail.

A number of PanedWindows display scrollable grids which show lists of records
from the open database, and others display records selected from these grids
in more detail.
"""
# Split out of chess.py several years after it became clear ChessUI deserves a
# module of it's own.

import os
import tkinter
import tkinter.ttk
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog
import queue

from solentware_grid.core.dataclient import DataSource

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .gamerow import make_ChessDBrowGame
from .positionrow import make_ChessDBrowPosition
from .cqlrow import make_ChessDBrowCQL
from .repertoirerow import make_ChessDBrowRepertoire
from .gamelistgrid import (
    TagRosterGrid,
    GamePositionGames,
    PartialPositionGames,
    RepertoireGrid,
    RepertoirePositionGames,
)
from .game import Game
from .board import Board
from .cqlgrid import CQLGrid
from . import constants, fonts
from ..core.filespec import (
    GAMES_FILE_DEF,
    PARTIAL_FILE_DEF,
    REPERTOIRE_FILE_DEF,
    ANALYSIS_FILE_DEF,
    VARIATION_FIELD_DEF,
    SELECTION_FILE_DEF,
    RULE_FIELD_DEF,
    EVENT_FIELD_DEF,
    SITE_FIELD_DEF,
    DATE_FIELD_DEF,
    ROUND_FIELD_DEF,
    WHITE_FIELD_DEF,
    BLACK_FIELD_DEF,
    RESULT_FIELD_DEF,
    OPENING_FIELD_DEF,
    PARTIALPOSITION_NAME_FIELD_DEF,
)
from .displayitems import DisplayItems
from ..core.chessrecord import ChessDBrecordAnalysis
from .querygrid import QueryGrid
from .queryrow import make_ChessDBrowQuery
from .score import ScoreNoGameException


class ChessUIError(Exception):
    """Raise exception in chess_ui module."""


class ChessUI(ExceptionHandler):
    """Define widgets which form the User Interface."""

    allow_filter = {
        EVENT_FIELD_DEF,
        SITE_FIELD_DEF,
        DATE_FIELD_DEF,
        ROUND_FIELD_DEF,
        WHITE_FIELD_DEF,
        BLACK_FIELD_DEF,
        RESULT_FIELD_DEF,
    }

    def __init__(self, panel, statusbar=None, uci=None, toolbarframe=None):
        """Create the elements of the chess GUI.

        panel: the Panedwindow at root of the User Interface.
        statusbar: objects created by ChessUI can put text in the statusbar.
        uci: ChessUI objects communicate with chess engines via uci object.
        toolbarframe: selection rule control widgets are placed here.
        """
        self.top_pw = panel
        self.database = None
        self.partialpositionds = None
        self.fullpositionds = None
        self.engineanalysisds = None
        self.selectionds = None
        self.statusbar = statusbar
        self.uci = uci
        self.show_analysis = True
        self.visible_scrollbars = True

        # Create widgets for toolbarframe (to left of Statusbar set by Chess).
        if toolbarframe is not None:
            self.tb_entry = tkinter.ttk.Entry(toolbarframe, width=20)
            self.tb_entry.pack(side=tkinter.LEFT)
            self.tb_moveto = tkinter.ttk.Button(
                toolbarframe, text="Move to", underline=0
            )
            self.tb_moveto.pack(side=tkinter.LEFT)
            self.tb_filter = tkinter.ttk.Button(
                toolbarframe, text="Filter", underline=0
            )
            self.tb_filter.pack(side=tkinter.LEFT)
            self.set_toolbarframe_disabled()
        else:
            self.tb_entry = None
            self.tb_moveto = None
            self.tb_filter = None

        # All panes or just one with focus visible.
        self.single_view = False

        # So the parents can be given weight 1 when only one pane shown.
        self.pw_parent_map = {}

        # Pane weights when visible.
        # Top pane weight is 1 by definition: only item.
        # Consider removing top_pw settings as top_pw is not a subpane of a
        # PanedWindow.
        self.pw_weights = {}
        self.pw_current_weights = {}
        self.pw_weights[self.top_pw] = 1
        self.pw_current_weights[self.top_pw] = 0

        # So the payload widgets can be attached to their PanedWindows and
        # focus traversal can work when only one of the available payloads
        # is made visible.
        self.payload_parent_map = {}
        self.payload_available = {}

        self.error_file = None  # error log file name if available for use
        self._import_subprocess = None

        self.listfont = fonts.make_list_fonts(panel.winfo_toplevel())
        (
            self.tags_variations_comments_font,
            self.moves_played_in_game_font,
            self.boardfont,
            self.wildpieces,
        ) = fonts.make_chess_fonts(panel.winfo_toplevel())

        # The top pane has four panes arranged in columns.
        # Selection rules, database games list, displayed games, and analysis:
        # panes appear in this order from left to right when visible.
        self.selections_pw = tkinter.ttk.PanedWindow(
            self.top_pw, orient=tkinter.VERTICAL
        )
        self.list_games_pw = tkinter.ttk.PanedWindow(
            self.top_pw,
            # background='yellow',
            # opaqueresize=tkinter.FALSE,
            orient=tkinter.VERTICAL,
        )
        self.view_games_pw = tkinter.ttk.PanedWindow(
            self.top_pw,
            # background='yellow')
            orient=tkinter.VERTICAL,
        )
        self.analysis_pw = tkinter.ttk.PanedWindow(
            self.top_pw,
            # background='yellow',
            # opaqueresize=tkinter.FALSE,
            orient=tkinter.VERTICAL,
        )

        self.pw_parent_map[self.selections_pw] = self.top_pw
        self.pw_parent_map[self.list_games_pw] = self.top_pw
        self.pw_parent_map[self.view_games_pw] = self.top_pw
        self.pw_parent_map[self.analysis_pw] = self.top_pw

        # The analysis pane has two panes arranged in rows.
        self.repertoires_display_pw = tkinter.ttk.PanedWindow(
            self.analysis_pw, orient=tkinter.VERTICAL
        )
        self.partials_display_pw = tkinter.ttk.PanedWindow(
            self.analysis_pw, orient=tkinter.VERTICAL
        )
        self.pw_parent_map[self.repertoires_display_pw] = self.analysis_pw
        self.pw_parent_map[self.partials_display_pw] = self.analysis_pw

        # The lowest level PanedWindows.
        self.games_pw = tkinter.ttk.PanedWindow(
            self.list_games_pw, orient=tkinter.VERTICAL
        )
        self.position_games_pw = tkinter.ttk.PanedWindow(
            self.list_games_pw, orient=tkinter.VERTICAL
        )
        self.repertoires_pw = tkinter.ttk.PanedWindow(
            self.repertoires_display_pw, orient=tkinter.VERTICAL
        )
        self.position_repertoires_pw = tkinter.ttk.PanedWindow(
            self.repertoires_display_pw, orient=tkinter.VERTICAL
        )
        self.partials_pw = tkinter.ttk.PanedWindow(
            self.partials_display_pw, orient=tkinter.VERTICAL
        )
        self.position_partials_pw = tkinter.ttk.PanedWindow(
            self.partials_display_pw, orient=tkinter.VERTICAL
        )
        self.selection_rules_pw = tkinter.ttk.PanedWindow(
            self.selections_pw, orient=tkinter.VERTICAL
        )
        self.view_selection_rules_pw = tkinter.ttk.PanedWindow(
            self.selections_pw, orient=tkinter.VERTICAL
        )
        self.pw_parent_map[self.games_pw] = self.list_games_pw
        self.pw_parent_map[self.position_games_pw] = self.list_games_pw
        self.pw_parent_map[self.repertoires_pw] = self.repertoires_display_pw
        self.pw_parent_map[
            self.position_repertoires_pw
        ] = self.repertoires_display_pw
        self.pw_parent_map[self.partials_pw] = self.partials_display_pw
        self.pw_parent_map[
            self.position_partials_pw
        ] = self.partials_display_pw
        self.pw_parent_map[self.selection_rules_pw] = self.selections_pw
        self.pw_parent_map[self.view_selection_rules_pw] = self.selections_pw

        # These two, with self.view_games.pw bound earlier, contain the widgets
        # used to view the detail of games, repertoires, and partial positions.
        self.view_repertoires_pw = tkinter.ttk.PanedWindow(
            self.repertoires_display_pw, orient=tkinter.VERTICAL
        )
        self.view_partials_pw = tkinter.ttk.PanedWindow(
            self.partials_display_pw, orient=tkinter.VERTICAL
        )
        self.pw_parent_map[
            self.view_repertoires_pw
        ] = self.repertoires_display_pw
        self.pw_parent_map[self.view_partials_pw] = self.partials_display_pw

        # These display the lists of games, repertoires, partial positions, and
        # game selection rules, on the database.
        self.base_games = TagRosterGrid(self)
        self.base_repertoires = RepertoireGrid(self)
        self.base_partials = CQLGrid(self)
        self.base_selections = QueryGrid(self)

        # These display the lists of games, repertoires, and partial positions,
        # which match the current position of the active displayed item.
        self.game_games = GamePositionGames(self)
        self.repertoire_games = RepertoirePositionGames(self)
        self.partial_games = PartialPositionGames(self)

        def add_panedwindow(widget, weight):
            self.pw_current_weights[widget] = 0
            self.pw_parent_map[widget].add(
                widget, weight=self.pw_current_weights[widget]
            )
            self.pw_weights[widget] = weight

        # Selection columnn
        add_panedwindow(self.selections_pw, 1)

        # Database columnn
        add_panedwindow(self.list_games_pw, 2)

        # Games column (only item a container for managing subitems)
        add_panedwindow(self.view_games_pw, 4)

        # Analysis column
        add_panedwindow(self.analysis_pw, 2)

        # Selection column has two items, ratio 1:2
        add_panedwindow(self.selection_rules_pw, 1)
        add_panedwindow(self.view_selection_rules_pw, 2)

        # Database column has two items, ratio 2:1
        add_panedwindow(self.games_pw, 2)
        add_panedwindow(self.position_games_pw, 1)

        # Analysis column has two items, ratio 3:2
        add_panedwindow(self.repertoires_display_pw, 3)
        add_panedwindow(self.partials_display_pw, 2)

        # Upper item in analysis column has three items, ratio 1:2:1
        add_panedwindow(self.repertoires_pw, 1)
        add_panedwindow(self.view_repertoires_pw, 2)
        add_panedwindow(self.position_repertoires_pw, 1)

        # Lower item in analysis column has three items, ratio 1:1:1
        add_panedwindow(self.partials_pw, 1)
        add_panedwindow(self.view_partials_pw, 1)
        add_panedwindow(self.position_partials_pw, 1)

        # The managers for the four types of displayed item.
        self.game_items = DisplayItems()
        self.repertoire_items = DisplayItems()
        self.partial_items = DisplayItems()
        self.selection_items = DisplayItems()

        # The visibility of the repertoire and partial position lists when a
        # close action was done to a database: restore to this state on opening
        # a database.
        # Anything more complex will need something like DisplayItems.
        self.base_repertoires_displayed_at_database_close = False
        self.base_partials_displayed_at_database_close = False
        self.base_selections_displayed_at_database_close = False

        # Forward and backward traversal maps for next focus.
        self.traverse_forward = {
            self.base_games: self.game_games,
            self.game_games: self.game_items,
            self.game_items: self.base_repertoires,
            self.base_repertoires: self.repertoire_items,
            self.repertoire_items: self.repertoire_games,
            self.repertoire_games: self.base_partials,
            self.base_partials: self.partial_items,
            self.partial_items: self.partial_games,
            self.partial_games: self.base_selections,
            self.base_selections: self.selection_items,
            self.selection_items: self.base_games,
        }
        self.traverse_backward = {
            self.base_selections: self.partial_games,
            self.selection_items: self.base_selections,
            self.base_games: self.selection_items,
            self.game_games: self.base_games,
            self.game_items: self.game_games,
            self.base_repertoires: self.game_items,
            self.repertoire_items: self.base_repertoires,
            self.repertoire_games: self.repertoire_items,
            self.base_partials: self.repertoire_games,
            self.partial_items: self.base_partials,
            self.partial_games: self.partial_items,
        }

        def map_payload(payload, parent):
            self.payload_parent_map[payload] = parent
            self.payload_available[payload] = False

        # Map payload objects to their panedwindows, initially not available.
        # The widget is obtained from the payload's get_frame() method.
        map_payload(self.base_games, self.games_pw)
        map_payload(self.base_repertoires, self.repertoires_pw)
        map_payload(self.base_partials, self.partials_pw)
        map_payload(self.game_items, self.view_games_pw)
        map_payload(self.repertoire_items, self.view_repertoires_pw)
        map_payload(self.partial_items, self.view_partials_pw)
        map_payload(self.game_games, self.position_games_pw)
        map_payload(self.repertoire_games, self.position_repertoires_pw)
        map_payload(self.partial_games, self.position_partials_pw)
        map_payload(self.base_selections, self.selection_rules_pw)
        map_payload(self.selection_items, self.view_selection_rules_pw)

        # The game, repertoire, partial, and selection rule, widgets in their
        # own Toplevel.
        # Should these, added later, be helper class responsibility as well?
        # Similar construct in .uci.UCI too.
        self.games_and_repertoires_in_toplevels = set()
        self.partials_in_toplevels = set()
        self.selections_in_toplevels = set()

        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under wine-1.8.1_1,1 on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        # if self.uci.uci.uci_drivers_reply:
        #    self.uci.uci.set_analysis_queue(queue.Queue())
        #    self.process_uci_commands_from_engines_and_analysis_requests()
        # else:
        #    tkinter.messagebox.showinfo(
        #        'Chesstab Restriction',
        #        ' '.join(('Cannot create an interface for UCI engines:',
        #                  'this is expected if running under Wine.\n\n',
        #                  'You will not be allowed to start chess engines.')))
        self.uci.uci.set_analysis_queue(queue.Queue())
        self.process_uci_commands_from_engines_and_analysis_requests()

    def add_game_to_display(self, item):
        """Add game item to GUI."""
        self.game_items.add_item_to_display(item)
        if self.game_items.contains_one_item():

            # Call may not be necessary.
            # This one repeats call in gamedisplay.GameDisplay.
            # item.set_score_pointer_widget_navigation_bindings(True)

            self.set_game_position_data_source()
            self.calculate_payload_availability()
        self.configure_game_grid()
        self.set_game_change_notifications(item, callback=item.on_game_change)
        self.show_game_games()

    def add_partial_position_to_display(self, item):
        """Add partial position item to GUI."""
        self.partial_items.add_item_to_display(item)
        if self.partial_items.contains_one_item():
            self.set_partial_position_data_source()
            self.calculate_payload_availability()
            if self.database is not None:
                item.set_game_list()
        self.configure_partial_grid()
        self.set_partial_change_notifications(
            item, callback=item.on_partial_change
        )
        self.set_game_change_notifications(item, callback=item.on_game_change)
        self.show_partial_position_games()

    def add_repertoire_to_display(self, item):
        """Add repertoire item to GUI."""
        self.repertoire_items.add_item_to_display(item)
        if self.repertoire_items.contains_one_item():

            # Call may not be necessary.
            # item.set_score_pointer_widget_navigation_bindings(True)

            self.calculate_payload_availability()
            self.set_repertoire_data_source()
        self.configure_repertoire_grid()
        self.set_repertoire_change_notifications(
            item, callback=item.on_repertoire_change
        )
        self.set_game_change_notifications(item, callback=item.on_game_change)
        self.show_repertoire_games()

    def add_selection_rule_to_display(self, item):
        """Add selection rule item to GUI."""
        self.selection_items.add_item_to_display(item)
        if self.selection_items.contains_one_item():

            # Call may not be necessary.
            item.set_score_pointer_widget_navigation_bindings(True)

            self.calculate_payload_availability()
        self.configure_selection_grid()
        self.set_selection_rule_change_notifications(
            item, callback=item.on_selection_change
        )
        self.set_game_change_notifications(item, callback=item.on_game_change)
        self.show_selection_rule_games()

    def configure_game_grid(self):
        """Adjust game grid row sizes after navigate add or delete."""
        self.game_items.configure_items_grid(self.view_games_pw)

    def configure_partial_grid(self):
        """Adjust partial grid row sizes after navigate add or delete."""
        # If the constant is 2, like in configure_game_grid, sizing enters an
        # infinite loop if the first Partial Position is added when one or
        # more Repertoires are present.  The effect changes with constant, but
        # sizing finishes in all cases tried if it is Repertoire that is added
        # to one or more Partial Positions.  The work arounds are add another
        # display item of either type or drag resize the application.
        # There seems to be no problem if the constant is 1.
        # Baffling.
        # if len(self.partial_items.order) > 2:
        #    active_weight = len(self.partial_items.order) - 1
        # elif len(self.partialorder) == 0:
        #    # Closest to original code, but nothing gets done
        #    active_weight = 2
        # elif (self.partial_items.order[0].__class__ ==
        #      self.partial_items.order[-1].__class__):
        #    # So it looks like it's meant to do what it does.
        #    active_weight = 2
        # else:
        #    active_weight = 1
        # Back to original code when repertoire and partial position fully
        # separated.
        # The baffling problem may have been a consequence of references to
        # items displayed in list_games_pw (left-most) when deciding what to do
        # in analysis_pw (right-most).
        active_weight = max(2, len(self.partial_items.order) - 1)

        self.partial_items.configure_items_grid(
            self.view_partials_pw, active_weight=active_weight
        )

    def configure_repertoire_grid(self):
        """Adjust repertoire grid row sizes after navigate add or delete."""
        self.repertoire_items.configure_items_grid(self.view_repertoires_pw)

    def configure_selection_grid(self):
        """Adjust selection grid row sizes after navigate add or delete."""
        self.selection_items.configure_items_grid(self.view_selection_rules_pw)

    def delete_game_view(self, item):
        """Remove (game) panel from GUI on 'delete' event from panel."""
        views = self.game_items
        grid_item = views.delete_item_counters(item)
        if grid_item:
            self.set_properties_on_all_game_grids(grid_item)
        had_focus = item.has_focus()
        was_active = views.delete_item(item)

        self.configure_game_grid()
        self.view_games_pw.grid_rowconfigure(
            len(views.order), weight=0, uniform=""
        )

        # To refresh grid if current key is first after next database open.
        if self.database is None and self.game_games.partial not in (
            None,
            False,
        ):
            self.game_games.set_partial_key()

        if views.count_items_in_stack():
            if was_active:
                views.active_item.set_game_list()
            if had_focus:
                views.active_item.takefocus_widget.focus_set()
        else:
            if self.database:
                self.game_games.close_client_cursor()

                self.game_games.get_data_source().get_full_position_games(None)
                # Line above is reasonable when dealing with a built record set.
                # Line below seemed hackish at first.
                # However it is probably correct and the dubious code is likely
                # the long established use of None as the initial and default
                # value of attribute partial in instances of _DataAccess class.
                self.game_games.set_partial_key(key=False)

            self.calculate_payload_availability()
            self.configure_panedwindows()
            self.hide_game_games()
            if self.database is not None:
                if self.base_games and self.base_games.is_visible():
                    self.base_games.frame.focus_set()
                    return
                if self.base_partials and self.base_partials.is_visible():
                    self.base_partials.frame.focus_set()
                    return
            if self.partial_items.count_items_in_stack() != 0:

                # BUG start
                # partial position not resized
                self.partial_items.active_item.takefocus_widget.focus_set()
                # BUG end

    def delete_position_view(self, item):
        """Remove (partial) panel from GUI on 'delete' event from panel."""
        views = self.partial_items
        grid_item = views.delete_item_counters(item)
        if grid_item:
            if grid_item in self.base_partials.objects:
                self.base_partials.set_properties(grid_item)
        had_focus = item.has_focus()
        was_active = views.delete_item(item)

        self.configure_partial_grid()
        self.view_partials_pw.grid_rowconfigure(
            len(views.order), weight=0, uniform=""
        )

        # To refresh grid if current key is first after next database open.
        if self.database is None:
            if self.partial_games.partial not in (None, False):
                self.partial_games.set_partial_key()

        if views.count_items_in_stack():
            if was_active:
                self._set_find_partial_name_games(-1)
                widget = views.active_item.panel
                widget.after(
                    1,
                    func=self.try_command(
                        views.active_item.refresh_game_list, widget
                    ),
                )
                widget.after(
                    2, func=self.try_command(self._set_partial_name, widget)
                )
            if had_focus:
                views.active_item.takefocus_widget.focus_set()
        elif self.database is not None:
            self.hide_partial_position_games()

    def delete_repertoire_view(self, item):
        """Remove (game) panel from GUI on 'delete' event from panel."""
        views = self.repertoire_items
        grid_item = views.delete_item_counters(item)
        if grid_item:
            if grid_item in self.base_repertoires.objects:
                self.base_repertoires.set_properties(grid_item)
        had_focus = item.has_focus()
        was_active = views.delete_item(item)

        self.configure_repertoire_grid()
        self.view_repertoires_pw.grid_rowconfigure(
            len(views.order), weight=0, uniform=""
        )

        # To refresh grid if current key is first after next database open.
        if self.database is None:
            if self.repertoire_games.partial not in (None, False):
                self.repertoire_games.set_partial_key()

        if views.count_items_in_stack():
            if was_active:
                views.active_item.set_game_list()
            if had_focus:
                views.active_item.takefocus_widget.focus_set()
        elif self.database is not None:
            self.hide_repertoire_games()

    def delete_selection_rule_view(self, item):
        """Remove (selection rule) panel on 'delete' event from panel."""
        views = self.selection_items
        grid_item = views.delete_item_counters(item)
        if grid_item:
            if grid_item in self.base_selections.objects:
                self.base_selections.set_properties(grid_item)
        had_focus = item.has_focus()
        was_active = views.delete_item(item)

        self.configure_selection_grid()
        self.view_selection_rules_pw.grid_rowconfigure(
            len(views.order), weight=0, uniform=""
        )

        if views.count_items_in_stack():
            if was_active:
                views.active_item.refresh_game_list()
            if had_focus:
                views.active_item.takefocus_widget.focus_set()
        elif self.database is not None:
            self.hide_selection_rules()
            # Show all games in base_games.

    def _set_find_partial_name_games(self, index):
        """Set status text to partial position name being searched."""
        self.statusbar.set_status_text(
            self.partial_items.get_stack_item(index).get_text_for_statusbar()
        )

    def _set_partial_name(self):
        """Set status text to active partial position name."""
        self.statusbar.set_status_text(
            self.partial_items.active_item.get_text_for_statusbar()
        )

    def _set_selection_name(self):
        """Set status text to active selection rule name."""
        self.statusbar.set_status_text(
            self.selection_items.active_item.get_text_for_statusbar()
        )

    def get_active_game_move(self):
        """Return current move context of game being navigated."""
        try:
            return self.game_items.active_item.get_current_move_context()
        except IndexError:
            return None

    def get_active_repertoire_move(self):
        """Return current move context of repertoire being navigated."""
        try:
            return self.repertoire_items.active_item.get_current_move_context()
        except IndexError:
            return None

    def _hide_base_games(self):
        """Hide widget containing list of games in database."""
        if not self.base_games.is_visible():
            return
        self.base_games.forget_payload(
            self.payload_parent_map[self.base_games]
        )
        self.base_games.load_new_partial_key(False)
        self.base_games.set_data_source()

    def hide_game_grid(self):
        """Hide widget containing list of games in database."""
        if not self.base_games.is_visible():
            return
        if self.payload_available[self.base_repertoires]:
            self.base_repertoires_displayed_at_database_close = True
        if self.payload_available[self.base_partials]:
            self.base_partials_displayed_at_database_close = True
        if self.payload_available[self.base_selections]:
            self.base_selections_displayed_at_database_close = True
        self._hide_base_selection_rules()
        self._hide_base_partials()
        self._hide_base_repertoires()
        self._hide_base_games()
        self._set_position_analysis_data_source_all_items()
        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def hide_game_games(self):
        """Hide widgets containing selected games."""
        if self.game_items.count_items_in_stack():
            return
        self.game_games.clear_grid_keys()

        # Is next comment, kept from earlier version of this method called
        # hide_middle_column(), still relevant?

        ## Why different to hide_partial_position_games and
        ## hide_repertoire_games?
        ## Problem surfaces when games shown again.
        ## Only style of the three which works here.

        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def hide_partial_position_games(self):
        """Hide widgets containing selected partial positions and games."""
        if self.partial_items.count_items_in_stack():
            return

        # Why different to hide_game_games and hide_repertoire_games?
        # Problem surfaces when games shown again.
        # Only style of the three which works here.
        self.partial_games.forget_payload(
            self.payload_parent_map[self.partial_games]
        )
        if self.partials_display_pw.pane(self.position_partials_pw, "weight"):
            self.partial_games.load_new_partial_key(False)
            self.partial_games.set_data_source()

        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def _hide_base_partials(self):
        """Hide widget containing list of partial positions in database."""
        if not self.base_partials.is_visible():
            return
        self.base_partials.forget_payload(
            self.payload_parent_map[self.base_partials]
        )
        self.base_partials.load_new_partial_key(False)
        self.base_partials.set_data_source()

    def hide_partial_position_grid(self):
        """Hide widget containing list of partial positions in database."""
        if not self.base_partials.is_visible():
            return
        self._hide_base_partials()
        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def hide_repertoire_games(self):
        """Hide widgets containing selected repertoires and games."""
        if self.repertoire_items.count_items_in_stack():
            return

        # Why different to hide_partial_position_games and hide_game_games?
        # Problem surfaces when games shown again.
        # Only style of the three which works here.
        if self.repertoires_display_pw.pane(
            self.position_repertoires_pw, "weight"
        ):
            self.repertoire_games.load_new_partial_key(False)
            self.repertoire_games.set_data_source()

        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def _hide_base_repertoires(self):
        """Hide widget containing list of repertoire games in database."""
        if not self.base_repertoires.is_visible():
            return
        self.base_repertoires.forget_payload(
            self.payload_parent_map[self.base_repertoires]
        )
        self.base_repertoires.load_new_partial_key(False)
        self.base_repertoires.set_data_source()

    def hide_repertoire_grid(self):
        """Hide widget containing list of repertoire games in database."""
        if not self.base_repertoires.is_visible():
            return
        self._hide_base_repertoires()
        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def _hide_base_selection_rules(self):
        """Hide widget containing list of selection rules in database."""
        if not self.base_selections.is_visible():
            return
        self.base_selections.forget_payload(
            self.payload_parent_map[self.base_selections]
        )
        self.base_selections.load_new_partial_key(False)
        self.base_selections.set_data_source()

    def hide_selection_rules_grid(self):
        """Hide widget containing list of selection rules in database."""
        if not self.base_selections.is_visible():
            return
        self._hide_base_selection_rules()
        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def hide_selection_rules(self):
        """Hide widgets containing selected selection rules."""
        if self.selection_items.count_items_in_stack():
            return
        self.calculate_payload_availability()
        self.configure_panedwindows()
        self.reset_focus_on_hide_widget()

    def reset_focus_on_hide_widget(self):
        """Switch focus when widget with focus is hidden."""
        # BUG start
        # There was a comment here on a problem whose detail was not recorded.
        # But if sashes have been dragged such that the widget being hidden
        # is not visible when being hiddden, the list of games on close database
        # for example, then w is None in the w.winfo_pathname(...) call.
        #
        # hidden is the wrong argument.  Should be the widgets to take focus in
        # preference order and if that does not give an answer go through the
        # list below.
        if self.base_games.is_visible():
            self.base_games.frame.focus_set()
        elif self.base_partials.is_visible():
            self.base_partials.frame.focus_set()
        elif self.base_repertoires.is_visible():
            self.base_repertoires.frame.focus_set()
        elif self.game_items.count_items_in_stack():
            self.game_items.active_item.takefocus_widget.focus_set()
        elif self.repertoire_items.count_items_in_stack():
            self.repertoire_items.active_item.takefocus_widget.focus_set()
        elif self.partial_items.count_items_in_stack():
            self.partial_items.active_item.takefocus_widget.focus_set()
        else:
            self.top_pw.focus_set()
        # BUG end

    def set_board_colours(self, colourscheme):
        """Set board colours to match colourscheme."""
        sbg = False
        if colourscheme.game.l_color != Game.l_color:
            Game.l_color = colourscheme.game.l_color
            sbg = True
        if colourscheme.game.m_color != Game.m_color:
            Game.m_color = colourscheme.game.m_color
            sbg = True
        if colourscheme.game.am_color != Game.am_color:
            Game.am_color = colourscheme.game.am_color
            sbg = True
        if colourscheme.game.v_color != Game.v_color:
            Game.v_color = colourscheme.game.v_color
            sbg = True
        bbg = False
        if colourscheme.game.board.litecolor != Board.litecolor:
            Board.litecolor = colourscheme.game.board.litecolor
            bbg = True
        if colourscheme.game.board.darkcolor != Board.darkcolor:
            Board.darkcolor = colourscheme.game.board.darkcolor
            bbg = True
        bfg = False
        if colourscheme.game.board.whitecolor != Board.whitecolor:
            Board.whitecolor = colourscheme.game.board.whitecolor
            bfg = True
        if colourscheme.game.board.blackcolor != Board.blackcolor:
            Board.blackcolor = colourscheme.game.board.blackcolor
            bfg = True
        self._set_board_colours(sbg, bbg, bfg)

    def set_board_colours_from_options(self, defaults):
        """Set colour scheme board on opening database."""
        if not defaults:
            return
        sbg = False
        bbg = False
        bfg = False
        if defaults[constants.LINE_COLOR_NAME]:
            Game.l_color = defaults[constants.LINE_COLOR_NAME]
            sbg = True
        if defaults[constants.MOVE_COLOR_NAME]:
            Game.m_color = defaults[constants.MOVE_COLOR_NAME]
            sbg = True
        if defaults[constants.ALTERNATIVE_MOVE_COLOR_NAME]:
            Game.am_color = defaults[constants.ALTERNATIVE_MOVE_COLOR_NAME]
            sbg = True
        if defaults[constants.VARIATION_COLOR_NAME]:
            Game.v_color = defaults[constants.VARIATION_COLOR_NAME]
            sbg = True
        if defaults[constants.LITECOLOR_NAME]:
            Board.litecolor = defaults[constants.LITECOLOR_NAME]
            bbg = True
        if defaults[constants.DARKCOLOR_NAME]:
            Board.darkcolor = defaults[constants.DARKCOLOR_NAME]
            bbg = True
        if defaults[constants.WHITECOLOR_NAME]:
            Board.whitecolor = defaults[constants.WHITECOLOR_NAME]
            bfg = True
        if defaults[constants.BLACKCOLOR_NAME]:
            Board.blackcolor = defaults[constants.BLACKCOLOR_NAME]
            bfg = True
        self._set_board_colours(sbg, bbg, bfg)
        if defaults[constants.MOVES_PLAYED_IN_GAME_FONT]:
            fonts.copy_font_attributes(
                defaults[constants.MOVES_PLAYED_IN_GAME_FONT],
                tkinter.font.nametofont(constants.MOVES_PLAYED_IN_GAME_FONT),
            )
        if defaults[constants.TAGS_VARIATIONS_COMMENTS_FONT]:
            fonts.copy_font_attributes(
                defaults[constants.TAGS_VARIATIONS_COMMENTS_FONT],
                tkinter.font.nametofont(constants.MOVES_PLAYED_IN_GAME_FONT),
            )
        if defaults[constants.PIECES_ON_BOARD_FONT]:
            fonts.copy_board_font_attributes(
                defaults[constants.PIECES_ON_BOARD_FONT],
                tkinter.font.nametofont(constants.PIECES_ON_BOARD_FONT),
            )

    def set_board_fonts(self, colourscheme):
        """Set board fonts to match colourscheme."""
        exceptions = []
        capobftf = colourscheme.apply_pieces_on_board_font_to_font
        for games in (
            self.game_items.order,
            self.partial_items.order,
            self.repertoire_items.order,
            self.games_and_repertoires_in_toplevels,
            self.partials_in_toplevels,
        ):
            for item in games:
                try:
                    capobftf(item.board.font)
                except tkinter.TclError:
                    exceptions.append((item, games))
        for item, games in exceptions:
            games.remove(item)

    @staticmethod
    def set_data_change_notifications(widget, notifiers, callback=None):
        """Enable or disable database update notifications for widget.

        widget - object to be notified
        notifiers - sequence of objects which do the notifying
        callback - function, usually a method of widget, used to do notifying

        if callback is None the specified notifications are cancelled
        """
        if callback is None:
            for grid in notifiers:
                widget.register_out(grid.get_data_source())
        else:
            for grid in notifiers:
                widget.register_in(grid.get_data_source(), callback)

    def set_game_change_notifications(self, widget, callback=None):
        """Set or unset game update notifications to widget."""
        self.set_data_change_notifications(
            widget,
            (self.base_games, self.game_games, self.partial_games),
            callback,
        )

    def set_partial_change_notifications(self, widget, callback=None):
        """Set or unset partial position update notifications to widget."""
        self.set_data_change_notifications(
            widget, (self.base_partials,), callback
        )

    def set_repertoire_change_notifications(self, widget, callback=None):
        """Set or unset partial position update notifications to widget."""
        self.set_data_change_notifications(
            widget, (self.base_repertoires,), callback
        )

    def set_selection_rule_change_notifications(self, widget, callback=None):
        """Set or unset selection rule update notifications to widget."""
        self.set_data_change_notifications(
            widget, (self.base_selections,), callback
        )

    def set_open_database_and_engine_classes(
        self,
        database=None,
        fullpositionclass=None,
        partialpositionclass=None,
        engineanalysisclass=None,
        selectionclass=None,
    ):
        """Set current open database and engine specific dataset classes."""
        self.database = database
        if database is None:
            self.partialpositionds = None
            self.fullpositionds = None
            self.engineanalysisds = None
            self.selectionds = None
            self.uci.uci.set_position_analysis_data_source()
            self.uci.set_open_database_and_engine_classes()
        else:
            self.partialpositionds = partialpositionclass
            self.fullpositionds = fullpositionclass
            self.engineanalysisds = engineanalysisclass
            self.selectionds = selectionclass
            self.uci.uci.set_position_analysis_data_source(
                datasource=self.make_position_analysis_data_source()
            )
            self.uci.set_open_database_and_engine_classes(database=database)

    def set_focus_gamepanel_item(self, event=None):
        """Give game at top of stack the focus."""
        self.set_toolbarframe_disabled()
        self.game_items.set_focus()

    def set_focus_game_grid(self, event=None):
        """Give widget displaying list of games on database the focus."""
        if self.database is not None:
            if self.base_games.datasource.dbname in self.allow_filter:
                self.set_toolbarframe_normal(
                    self.move_to_game, self.filter_game
                )
            else:
                self.set_toolbarframe_disabled()
            self.base_games.set_focus()
            self.base_games.set_selection_text()

    def set_focus_partial_game_grid(self, event=None):
        """Give widget displaying list of games for partial position focus."""
        if self.database is not None:
            self.set_toolbarframe_disabled()
            self.partial_games.set_focus()
            self.partial_games.set_selection_text()

    def set_focus_partial_grid(self, event=None):
        """Give widget displaying list of partial positions the focus."""
        if self.database is not None:
            self.set_toolbarframe_normal(
                self.move_to_partial, self.filter_partial
            )
            self.base_partials.set_focus()
            self.base_partials.set_selection_text()

    def set_focus_partialpanel_item(self, event=None):
        """Give partial position at top of stack the focus."""
        self.set_toolbarframe_disabled()
        self.partial_items.set_focus()

    def set_focus_position_grid(self, event=None):
        """Give widget displaying list of games matching position the focus."""
        if self.database is not None:
            self.set_toolbarframe_disabled()
            self.game_games.set_focus()
            self.game_games.set_selection_text()

    def set_focus_repertoire_game_grid(self, event=None):
        """Give widget displaying list of games for repertoire focus."""
        if self.database is not None:
            self.set_toolbarframe_disabled()
            self.repertoire_games.set_focus()
            self.repertoire_games.set_selection_text()

    def set_focus_repertoire_grid(self, event=None):
        """Give focus to widget displaying list of database repertoire games."""
        if self.database is not None:
            self.set_toolbarframe_normal(
                self.move_to_repertoire, self.filter_repertoire
            )
            self.base_repertoires.set_focus()
            self.base_repertoires.set_selection_text()

    def set_focus_repertoirepanel_item(self, event=None):
        """Give repertoire game at top of stack the focus."""
        self.set_toolbarframe_disabled()
        self.repertoire_items.set_focus()

    def set_focus_selection_rule_grid(self, event=None):
        """Give widget displaying list of selection rules the focus."""
        if self.database is not None:
            self.set_toolbarframe_normal(
                self.move_to_selection, self.filter_selection
            )
            self.base_selections.set_focus()
            self.base_selections.set_selection_text()

    def set_focus_selectionpanel_item(self, event=None):
        """Give selection rule at top of stack the focus."""
        self.set_toolbarframe_disabled()
        self.selection_items.set_focus()

    def set_game_position_data_source(self):
        """Attach database to widget that displays games for position."""
        if self.database is not None:
            sqds = self.fullpositionds(
                self.database,
                GAMES_FILE_DEF,
                GAMES_FILE_DEF,
                make_ChessDBrowPosition(self),
            )
        else:
            sqds = None
        self.game_games.set_data_source(sqds)

    def set_partial_position_data_source(self):
        """Attach database to widget displaying games for partial position."""
        if self.database is not None:
            sqds = self.partialpositionds(
                self.database,
                GAMES_FILE_DEF,
                GAMES_FILE_DEF,
                make_ChessDBrowGame(self),
            )
        else:
            sqds = None

        # The expected effect, using correct header, does not happen.
        # self.partial_games.set_data_header(header=ChessDBrowGame)
        # In some runs always does right thing but in others gives empty grid.
        # Seems to be wrong always if partial item is asked for first.
        # self.partial_games.make_header(ChessDBrowGame.header_specification)
        self.partial_games.set_data_source(sqds)

    def set_repertoire_data_source(self):
        """Attach database to widget displaying games for repertoire."""
        if self.database is not None:
            sqds = self.fullpositionds(
                self.database,
                GAMES_FILE_DEF,
                GAMES_FILE_DEF,
                make_ChessDBrowPosition(self),
            )
        else:
            sqds = None

        # The expected effect, using correct header, does not happen.
        # self.partial_games.set_data_header(header=ChessDBrowPosition)
        # In some runs always does right thing but in others gives empty grid.
        # Seems to be correct always if repertoire item is asked for first,
        # but only if database is open when first is requested.
        # self.partial_games.make_header(
        #    ChessDBrowPosition.header_specification)
        self.repertoire_games.set_data_source(sqds)

    def _show_base_games(self):
        """Show widget containing list of games in database."""
        if self.list_games_pw.pane(self.games_pw, "weight"):

            # Size is assumed to be (1,1) as created at first call and grid
            # will be filled after <Configure> event to size the widget.
            # Subsequent calls are not associated with a <Configure> event so
            # fill the widget by after_idle(...).
            if self.base_games.get_frame().winfo_width() != 1:
                self.games_pw.after_idle(self.base_games.load_new_index)

    @staticmethod
    def _show_active_item_position_games(active):
        """Show list for current position in active item."""
        if not active:
            return

        # Test is on active.score because active.analysis does not exist if
        # active is from self.partial_items.
        if active.takefocus_widget is not active.score:
            active = active.analysis

        active.itemgrid.set_partial_key()
        active.set_game_list()

    def show_game_grid(self, database):
        """Show widget containing list of games in database."""
        if self.game_items.count_items_in_stack():
            self.set_game_position_data_source()
            self.game_items.active_item.set_game_list()
            self.game_items.set_insert_or_delete_on_all_items()
        if self.partial_items.count_items_in_stack():
            self.set_partial_position_data_source()
            self.partial_items.active_item.refresh_game_list()
            self.partial_items.set_insert_or_delete_on_all_items()
        if self.repertoire_items.count_items_in_stack():
            self.set_repertoire_data_source()
            self.repertoire_items.active_item.set_game_list()
            self.repertoire_items.set_insert_or_delete_on_all_items()
        if self.selection_items.count_items_in_stack():
            for i in self.selection_items.order:
                if i.query_statement.dbset is None:
                    i.query_statement.dbset = GAMES_FILE_DEF
            # self.set_repertoire_data_source()
            # self.selection_items.active_item.set_game_list()
            self.selection_items.set_insert_or_delete_on_all_items()
        self._set_position_analysis_data_source_all_items()

        ## Hack to cope with GUI use while Import in progress.
        # if self.base_games.get_data_source().get_database() is not None:
        #    self.base_games.clear_grid_keys()

        if self.base_repertoires_displayed_at_database_close:
            self._create_repertoire_datasource(database)
        if self.base_partials_displayed_at_database_close:
            self._create_partial_position_datasource(database)
        if self.base_selections_displayed_at_database_close:
            self._create_selection_rules_datasource(database)
        self.base_repertoires_displayed_at_database_close = False
        self.base_partials_displayed_at_database_close = False
        self.base_selections_displayed_at_database_close = False
        self.calculate_payload_availability()
        self.configure_panedwindows()
        self._show_base_games()
        self._show_base_partials()
        self._show_base_repertoires()
        self._show_base_selection_rules()

        # All the active items except selection_items, which is excluded so all
        # games in database are listed when database is opened.
        self._show_active_item_position_games(self.game_items.active_item)
        self._show_active_item_position_games(
            self.repertoire_items.active_item
        )
        self._show_active_item_position_games(self.partial_items.active_item)

        self.base_games.set_focus()

        # Refresh.
        self.set_game_change_notifications(
            self.base_games, callback=self.base_games.on_game_change
        )

    def show_game_games(self):
        """List games containing position in active game."""
        if not self.game_items.count_items_in_stack():
            return

        ## Hack to cope with GUI use while Import in progress.
        ##if self.partial_games.get_data_source() is not None:
        ##    if self.partial_games.get_data_source(
        ##        ).get_database() is not None:
        ##        self.partial_games.clear_grid_keys()
        # if self.game_games.get_data_source() is not None:
        #    if self.game_games.get_data_source(
        #        ).get_database() is not None:
        #        self.game_games.clear_grid_keys()

        if self.top_pw.pane(self.list_games_pw, "weight"):
            self.set_game_change_notifications(
                self.base_games, callback=self.base_games.on_game_change
            )
        self.configure_panedwindows()

    def show_partial_position_games(self):
        """List games containing partial position in active partial position."""
        if not self.partial_items.count_items_in_stack():
            if not self.top_pw.pane(self.analysis_pw, "weight"):
                return

        ## Hack to cope with GUI use while Import in progress.
        # if self.partial_games.get_data_source() is not None:
        #    if self.partial_games.get_data_source(
        #        ).get_database() is not None:
        #        self.partial_games.clear_grid_keys()

        if not self.partials_display_pw.pane(self.view_partials_pw, "weight"):
            self.set_game_change_notifications(
                self.base_games, callback=self.base_games.on_game_change
            )
        self.configure_panedwindows()

    def show_repertoire_games(self):
        """List games containing position in active repertoire."""
        if not self.repertoire_items.count_items_in_stack():
            if not self.top_pw.pane(self.analysis_pw, "weight"):
                return

        ## Hack to cope with GUI use while Import in progress.
        # if self.repertoire_games.get_data_source() is not None:
        #    if self.repertoire_games.get_data_source(
        #        ).get_database() is not None:
        #        self.repertoire_games.clear_grid_keys()

        if not self.repertoires_display_pw.pane(
            self.view_repertoires_pw, "weight"
        ):
            self.set_game_change_notifications(
                self.base_games, callback=self.base_games.on_game_change
            )
        self.configure_panedwindows()

    # Not sure how correct this is yet: in pane hierarchy terms.
    def show_selection_rule_games(self):
        """List games containing position in active repertoire."""
        if not self.selection_items.count_items_in_stack():
            if not self.top_pw.pane(self.selections_pw, "weight"):
                return

        ## Hack to cope with GUI use while Import in progress.
        # if self.repertoire_games.get_data_source() is not None:
        #    if self.repertoire_games.get_data_source(
        #        ).get_database() is not None:
        #        self.repertoire_games.clear_grid_keys()

        if not self.selections_pw.pane(self.selection_rules_pw, "weight"):
            self.set_game_change_notifications(
                self.base_games, callback=self.base_games.on_game_change
            )
        self.configure_panedwindows()

    def _create_partial_position_datasource(self, database):
        """Create a new DataSource for list of partial positions."""
        # Probably wrong because datasource = F(active item), but this is a
        # constant at present.
        self.base_partials.set_data_source(
            DataSource(
                database,
                PARTIAL_FILE_DEF,
                PARTIALPOSITION_NAME_FIELD_DEF,
                make_ChessDBrowCQL(self),
            ),
            self.base_partials.on_data_change,
        )
        if self.partial_items.any_items_displayed_of_type():
            self.set_partial_position_data_source()
            self.partial_items.set_insert_or_delete_on_all_items()

    def _show_base_partials(self):
        """Show widget containing list of partial positions in database."""
        if self.partials_display_pw.pane(self.partials_pw, "weight"):

            # Size is assumed to be (1,1) as created at first call and grid
            # will be filled after <Configure> event to size the widget.
            # Subsequent calls are not associated with a <Configure> event so
            # fill the widget by after_idle(...).
            if self.base_partials.get_frame().winfo_width() != 1:
                self.base_partials.set_partial_key()
                self.partials_pw.after_idle(self.base_partials.load_new_index)

    def show_partial_position_grid(self, database):
        """Show widget containing list of partial positions in database."""
        self._create_partial_position_datasource(database)

        ## Hack to cope with GUI use while Import in progress.
        # if self.base_partials.get_data_source().get_database() is not None:
        #    self.base_partials.clear_grid_keys()

        self.calculate_payload_availability()
        self.configure_panedwindows()
        self._show_base_partials()
        self.base_partials.set_focus()

    def _create_repertoire_datasource(self, database):
        """Create a new DataSource for list of repertoires."""
        # Probably wrong because datasource = F(active item), but this is a
        # constant at present.
        self.base_repertoires.set_data_source(
            DataSource(
                database,
                REPERTOIRE_FILE_DEF,
                OPENING_FIELD_DEF,
                make_ChessDBrowRepertoire(self),
            ),
            self.base_repertoires.on_data_change,
        )
        if self.repertoire_items.any_items_displayed_of_type():
            self.set_repertoire_data_source()
            self.repertoire_items.set_insert_or_delete_on_all_items()

    def _show_base_repertoires(self):
        """Show widget containing list of repertoire games in database."""
        if self.repertoires_display_pw.pane(self.repertoires_pw, "weight"):

            # Size is assumed to be (1,1) as created at first call and grid
            # will be filled after <Configure> event to size the widget.
            # Subsequent calls are not associated with a <Configure> event so
            # fill the widget by after_idle(...).
            if self.base_repertoires.get_frame().winfo_width() != 1:
                self.base_repertoires.set_partial_key()
                self.repertoires_pw.after_idle(
                    self.base_repertoires.load_new_index
                )

    def show_repertoire_grid(self, database):
        """Show widget containing list of repertoire games in database."""
        self._create_repertoire_datasource(database)

        ## Hack to cope with GUI use while Import in progress.
        # if self.base_repertoires.get_data_source().get_database() is not None:
        #    self.base_repertoires.clear_grid_keys()

        self.calculate_payload_availability()
        self.configure_panedwindows()
        self._show_base_repertoires()
        self.base_repertoires.set_focus()

    def set_import_subprocess(self, subprocess_id=None):
        """Set the import subprocess object if not already active."""
        if self.is_import_subprocess_active():
            raise ChessUIError("Attempt to set import subprocess while active")
        self._import_subprocess = subprocess_id

    def get_import_subprocess(self):
        """Return the import subprocess identity."""
        return self._import_subprocess

    def get_import_subprocess_poll(self):
        """Poll the import subprocess and return the response."""
        return self._import_subprocess.poll()

    def is_import_subprocess_active(self):
        """Return True if the import subprocess object is active."""
        if self._import_subprocess is None:
            return False
        return self._import_subprocess.poll() is None

    def get_toplevel(self):
        """Return the toplevel widget."""
        return self.top_pw.winfo_toplevel()

    def process_uci_commands_from_engines_and_analysis_requests(self):
        """Periodically process UCI actions required and response queues."""
        self.uci.uci.get_engine_responses()
        self.uci.uci.get_analysis_requests()
        self.refresh_analysis_widgets()
        self.top_pw.after(
            1000, self.process_uci_commands_from_engines_and_analysis_requests
        )

    @staticmethod
    def _configure_font(target, source):
        """Set target font properties from source font."""
        for property_ in "family", "weight", "slant", "size":
            target[property_] = source[property_]

    def _set_board_colours(self, sbg, bbg, bfg):
        """Set colours and fonts used to display games.

        sbg == True - set game score colours
        bbg == True - set board square colours
        bfg == True - set board piece colours

        """
        exceptions = []
        for games in (
            self.game_items.order,
            self.partial_items.order,
            self.repertoire_items.order,
            self.games_and_repertoires_in_toplevels,
            self.partials_in_toplevels,
        ):
            for item in games:
                try:
                    item.set_colours(sbg, bbg, bfg)
                except tkinter.TclError:
                    exceptions.append((item, games))
        for item, games in exceptions:
            games.remove(item)

    def get_export_filename(self, datatype, pgn=True):
        """Return filename to contain export of datatype or None."""
        title = " ".join(("Export", datatype))
        if self.is_import_subprocess_active():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title=title,
                message="An import of data is in progress",
            )
            return None
        if not self.database:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title=title,
                message="".join(
                    ("Open the database from which the export is to be done.",)
                ),
            )
            return None
        return self._get_export_filename(datatype, pgn, title)

    def get_export_filename_for_single_item(self, datatype, pgn=True):
        """Return filename to contain export of datatype or None."""
        return self._get_export_filename(
            datatype, pgn, " ".join(("Export", datatype))
        )

    def get_export_folder(self):
        """Return folder name to contain export of database or None."""
        title = "Export database as Text"
        if self.is_import_subprocess_active():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title=title,
                message="An import of data is in progress",
            )
            return None
        if not self.database:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title=title,
                message="".join(
                    ("Open the database from which the export is to be done.",)
                ),
            )
            return None
        filename = tkinter.filedialog.askdirectory(
            parent=self.get_toplevel(), title=title, initialdir="~"
        )
        if not filename:
            tkinter.messagebox.showwarning(
                parent=self.get_toplevel(),
                title=title,
                message="Database not exported",
            )
            return None
        bfn = os.path.basename(filename)
        fns = (
            os.path.join(filename, "".join((bfn, "_games", ".txt"))),
            os.path.join(filename, "".join((bfn, "_repertoires", ".txt"))),
            os.path.join(filename, "".join((bfn, "_partials", ".txt"))),
        )
        if not tkinter.messagebox.askokcancel(
            parent=self.get_toplevel(),
            title=title,
            message="".join(
                (
                    "The database will be exported to files:\n\n",
                    "\n\n".join((os.path.basename(f) for f in fns)),
                    "\n\nprovided none of these already exist.\n",
                )
            ),
        ):
            return None
        for filename in fns:
            if os.path.exists(filename):
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    title=title,
                    message="\n".join(
                        (
                            "Cannot export because file\n",
                            filename,
                            "\nalready exists.\n",
                        )
                    ),
                )
                return None
        return fns

    def _get_export_filename(self, datatype, pgn, title):
        """Return filename to contain export of datatype or None."""
        if pgn:
            extn = "pgn"
        else:
            extn = "txt"
        filename = tkinter.filedialog.asksaveasfilename(
            parent=self.get_toplevel(),
            title=title,
            defaultextension="".join((".", extn)),
            filetypes=((datatype, ".".join(("*", extn))),),
        )
        if not filename:
            tkinter.messagebox.showwarning(
                parent=self.get_toplevel(),
                title=title,
                message=" ".join((datatype, "file not saved")),
            )
            return None
        return filename

    def refresh_analysis_widgets(self):
        """Refresh game widgets with updated chess engine analysis."""
        exceptions = []
        for games in (
            self.game_items.order,
            self.repertoire_items.order,
            self.games_and_repertoires_in_toplevels,
        ):
            for item in games:
                try:
                    if item.current is None:
                        try:
                            position = item.fen_tag_tuple_square_piece_map()
                        except ScoreNoGameException:
                            continue
                    else:
                        position = item.tagpositionmap[item.current]
                    item.refresh_analysis_widget(item.get_analysis(*position))
                except tkinter.TclError:
                    exceptions.append((item, games))
        for item, games in exceptions:
            games.remove(item)

    @staticmethod
    def _give_focus(current, traverse):
        """Give focus to adjacent widget type in traversal order."""
        give = current
        while True:
            give = traverse[give]
            if give == current:
                break
            if give.is_visible():
                give.set_focus()
                break

    def give_focus_backward(self, current):
        """Give focus to previous widget type in traversal order."""
        self._give_focus(current, self.traverse_backward)

    def give_focus_forward(self, current):
        """Give focus to next widget type in traversal order."""
        self._give_focus(current, self.traverse_forward)

    def show_all_panedwindows(self):
        """Show all panes with weights prior to toggle to single pane view."""
        if not self.single_view:
            return
        for widget, parent in self.pw_parent_map.items():
            parent.pane(widget, weight=self.pw_current_weights[widget])
        self.single_view = False
        self.configure_game_grid()
        self.configure_partial_grid()
        self.configure_repertoire_grid()
        self.configure_selection_grid()

    def show_just_panedwindow_with_focus(self, gainfocus):
        """Show pane containing widget with focus and hide the other panes."""
        ppmi = {v: k for k, v in self.payload_parent_map.items()}
        widget = gainfocus
        while True:
            if widget in ppmi:
                if widget in self.pw_parent_map:
                    self.single_view = True
                    self.single_view = self.show_payload_panedwindows(
                        ppmi[widget]
                    )
                break
            if widget is self.top_pw:
                break
            widget = self.top_pw.nametowidget(widget.winfo_parent())
        if self.single_view:
            self.configure_game_grid()
            self.configure_partial_grid()
            self.configure_repertoire_grid()

    def show_payload_panedwindows(self, payload):
        """Show just payload's ancestor's panes if payload available."""
        if not self.single_view:
            return False
        if not self.payload_available[payload]:
            return False
        for ppw, parent in self.pw_parent_map.items():
            parent.pane(ppw, weight=0)
        ppw = self.payload_parent_map[payload]
        while True:
            if ppw not in self.pw_parent_map:
                break
            self.pw_parent_map[ppw].pane(ppw, weight=1)
            ppw = self.pw_parent_map[ppw]
        return True

    def calculate_payload_availability(self):
        """Calculate availability of data for display."""
        pla = self.payload_available
        ppm = self.payload_parent_map
        pwpm = self.pw_parent_map
        pwcw = self.pw_current_weights
        pww = self.pw_weights
        for payload in pla:
            pla[payload] = payload.is_payload_available()
            widget = ppm[payload]
            while widget in pwpm:
                pwcw[widget] = 0
                widget = pwpm[widget]
        for key, value in pla.items():
            widget = ppm[key]
            while widget in pwpm:
                if value:
                    pwcw[widget] = pww[widget]
                widget = pwpm[widget]
        if pwcw[ppm[self.base_games]]:
            if pwcw[ppm[self.game_items]]:
                # Same parent tree as base_games so just do child.
                widget = ppm[self.game_games]
                pwcw[widget] = pww[widget]
            if pwcw[ppm[self.repertoire_items]]:
                # Same parent tree as repertoire_items so just do child.
                widget = ppm[self.repertoire_games]
                pwcw[widget] = pww[widget]
            if pwcw[ppm[self.partial_items]]:
                # Same parent tree as partial_items so just do child.
                widget = ppm[self.partial_games]
                pwcw[widget] = pww[widget]

    def configure_panedwindows(self):
        """Display available panedwindows subject to single_view status."""
        for k in self.payload_available:
            widget = self.payload_parent_map[k]
            if self.pw_current_weights[widget]:
                k.insert_payload(widget)
            elif k in widget.panes():
                k.forget_payload(widget)
            while widget in self.pw_parent_map:
                self.pw_parent_map[widget].pane(
                    widget, weight=self.pw_current_weights[widget]
                )
                widget = self.pw_parent_map[widget]

    def set_properties_on_all_game_grids(self, game):
        """Set properties for game on all grids where it is visible."""
        for grid in (
            self.base_games,
            self.game_games,
            self.repertoire_games,
            self.partial_games,
        ):
            grid.set_properties(game)

    def set_bindings_on_item_losing_focus_by_pointer_click(self):
        """Set bindings for an active item when it does not have focus.

        Binary moves of focus between two items by keyboard or popup menu
        action are dealt with elsewhere.

        This method deals with many-to-one possibilities implied by pointer
        click on a specific item.  It could deal with the binary ones too, and
        maybe that is better, or not.

        """
        for item in (
            self.game_items,
            self.repertoire_items,
            self.base_games,
            self.game_games,
            self.repertoire_games,
            self.base_repertoires,
            self.partial_games,
            self.partial_items,
            self.base_partials,
        ):
            if item.bind_for_widget_without_focus():
                break

    def _set_position_analysis_data_source_all_items(self):
        """Set game and repertoire analysis data sources to match database.

        self.ui.database will be None if no database open, or the database
        instance if open.

        """
        for items in (
            self.game_items.order,
            self.repertoire_items.order,
            self.games_and_repertoires_in_toplevels,
        ):
            for item in items:
                item.set_position_analysis_data_source()

    def make_position_analysis_data_source(self):
        """Create a new DataSource for stored chess engine analysis."""
        if self.database:

            # Without the 'is not None' seems unreliable at 08 Nov 2015.
            # What is wrong with 'if <obj>:' where obj is a bsddb3.DB instance?
            # It does work sometimes, so some environment clutter perhaps.
            # Not yet known what happens with sqlite3 and so forth.
            if (
                self.database.is_database_file_active(ANALYSIS_FILE_DEF)
                is not None
            ):
                return self.engineanalysisds(
                    self.database,
                    ANALYSIS_FILE_DEF,
                    VARIATION_FIELD_DEF,
                    newrow=ChessDBrecordAnalysis,
                )
        return None

    def _create_selection_rules_datasource(self, database):
        """Create a new DataSource for list of selection rules."""
        # Probably wrong because datasource = F(active item), but this is a
        # constant at present.
        self.base_selections.set_data_source(
            DataSource(
                database,
                SELECTION_FILE_DEF,
                RULE_FIELD_DEF,
                make_ChessDBrowQuery(self),
            ),
            self.base_selections.on_data_change,
        )
        if self.selection_items.any_items_displayed_of_type():
            self.selection_items.set_insert_or_delete_on_all_items()

    def _show_base_selection_rules(self):
        """Show widget containing list of selection rules in database."""
        if self.selections_pw.pane(self.selection_rules_pw, "weight"):

            # Size is assumed to be (1,1) as created at first call and grid
            # will be filled after <Configure> event to size the widget.
            # Subsequent calls are not associated with a <Configure> event so
            # fill the widget by after_idle(...).
            if self.base_selections.get_frame().winfo_width() != 1:
                self.base_selections.set_partial_key()
                self.selections_pw.after_idle(
                    self.base_selections.load_new_index
                )

    def show_selection_rules_grid(self, database):
        """Show widget containing list of selection rules in database."""
        self._create_selection_rules_datasource(database)

        ## Hack to cope with GUI use while Import in progress.
        # if self.base_selections.get_data_source().get_database() is not None:
        #    self.base_selections.clear_grid_keys()

        self.calculate_payload_availability()
        self.configure_panedwindows()
        self._show_base_selection_rules()
        self.base_selections.set_focus()

    def _set_find_selection_name_games(self, index):
        """Set status text to selection rule name being searched."""
        self.statusbar.set_status_text(
            self.selection_items.get_stack_item(index).get_text_for_statusbar()
        )

    def set_toolbarframe_disabled(self):
        """Set state for widgets in toolbar frame."""
        self.tb_entry.configure(state=tkinter.DISABLED)
        for widget in (self.tb_moveto, self.tb_filter):
            widget.configure(state=tkinter.DISABLED, command="")

    def set_toolbarframe_normal(self, move_to, filter_):
        """Set state for widgets in toolbar frame."""
        self.tb_entry.configure(state=tkinter.NORMAL)
        self.tb_moveto.configure(state=tkinter.NORMAL, command=move_to)
        self.tb_filter.configure(state=tkinter.NORMAL, command=filter_)

    def move_to_game(self):
        """Move to first game with PGN Tag value starting text in filter."""
        self.base_games.move_to_row_in_grid(self.tb_entry.get())

    def move_to_partial(self):
        """Move to first ChessQL statement with name starting text in filter."""
        self.base_partials.move_to_row_in_grid(self.tb_entry.get())

    def move_to_repertoire(self):
        """Move to first repertoire with name starting text in filter."""
        self.base_repertoires.move_to_row_in_grid(self.tb_entry.get())

    def move_to_selection(self):
        """Move to first query with name starting text in filter."""
        self.base_selections.move_to_row_in_grid(self.tb_entry.get())

    def filter_game(self):
        """Show games with PGN Tag value starting text in filter."""
        text = self.tb_entry.get()
        self.base_games.record_count = None
        self.base_games.set_partial_key(text if len(text) else None)

        # Not yet sure if other three filter_* methods need fill_view() call to
        # populate widget without an explicit scroll action by user.
        # '*' seems to be treated as a 0-n wildcard character when passed to
        # SQLite3 via apsw or sqlite3 interfaces, and creates a situation that
        # looks difficult to resolve in DataGrid.
        # (Added much later:)
        # Implementing filters with '*' characters could be done by selection
        # rules evaluated here using the 't' value.
        try:
            self.base_games.fill_view()
        except KeyError:
            if "*" in text:
                tkinter.messagebox.showwarning(
                    parent=self.get_toplevel(),
                    title="Filter Games",
                    message="".join(
                        (
                            "Filter '",
                            text,
                            "' contains a '*'.\n\nThis warning ",
                            "is expected to appear if the database engine is ",
                            "SQLite3 and means an attempt to scroll the list of ",
                            "games will cause a program crash.\n\nA known way ",
                            "to avoid this is menu option 'Select | Game'.\n\n",
                            "Assuming the filter was enabled by menu option ",
                            "'Select | White' the filter can be done by 'Select ",
                            "| Rule', typing 'White starts ",
                            text,
                            "', followed ",
                            "by 'Ctrl + Enter'.\n\nIf the filter was enabled by ",
                            "'Select | Result' the appropriate rule is likely ",
                            "to be 'Result eq *'.",
                        )
                    ),
                )

    def filter_partial(self):
        """Show ChessQL statements with name starting text in filter."""
        text = self.tb_entry.get()
        self.base_partials.load_new_partial_key(text if len(text) else None)

    def filter_repertoire(self):
        """Show repertoires with name starting text in filter."""
        text = self.tb_entry.get()
        self.base_repertoires.load_new_partial_key(text if len(text) else None)

    def filter_selection(self):
        """Show query statements with name starting text in filter."""
        text = self.tb_entry.get()
        self.base_selections.load_new_partial_key(text if len(text) else None)

    def hide_scrollbars(self):
        """Hide the scrollbars in the game display widgets."""
        self.visible_scrollbars = False
        exceptions = []
        for items in (
            self.game_items.order,
            self.repertoire_items.order,
            self.partial_items.order,
            self.selection_items.order,
            self.games_and_repertoires_in_toplevels,
            self.partials_in_toplevels,
            self.selections_in_toplevels,
        ):
            for i in items:
                try:
                    i.hide_scrollbars()
                except tkinter.TclError:
                    exceptions.append((i, items))
        for i, items in exceptions:
            items.remove(i)

    def show_scrollbars(self):
        """Show the scrollbars in the game display widgets."""
        self.visible_scrollbars = True
        exceptions = []
        for items in (
            self.game_items.order,
            self.repertoire_items.order,
            self.partial_items.order,
            self.selection_items.order,
            self.games_and_repertoires_in_toplevels,
            self.partials_in_toplevels,
            self.selections_in_toplevels,
        ):
            for i in items:
                try:
                    i.show_scrollbars()
                except tkinter.TclError:
                    exceptions.append(i, items)
        for i, items in exceptions:
            items.remove(i)

    def export_report(self, result, title):
        """Show a report dialogue if some game scores could not be exported."""
        if result is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "No games scores output because none are ",
                        "PGN export format compliant",
                    )
                ),
            )
        elif result is False:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "Some games scores are not output because they are ",
                        "not PGN export format compliant",
                    )
                ),
            )
