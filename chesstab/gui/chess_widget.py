# chess_widget.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define menu of user interface functions excluding database functions."""

import os
import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import queue

from solentware_misc.core import callthreadqueue
from solentware_misc.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN

from .gamedisplay import GameDisplayInsert
from .cqldisplay import CQLDisplayInsert
from .repertoiredisplay import RepertoireDisplayInsert
from . import constants, options
from . import colourscheme
from . import help_
from .. import APPLICATION_NAME, ERROR_LOG
from ..core.filespec import (
    GAMES_FILE_DEF,
    SOURCE_FIELD_DEF,
    EVENT_FIELD_DEF,
    SITE_FIELD_DEF,
    DATE_FIELD_DEF,
    ROUND_FIELD_DEF,
    WHITE_FIELD_DEF,
    BLACK_FIELD_DEF,
    RESULT_FIELD_DEF,
)
from ..core.constants import UNKNOWN_RESULT
from .uci import UCI
from .chess_ui import ChessUI
from .eventspec import EventSpec

STARTUP_MINIMUM_WIDTH = 340
STARTUP_MINIMUM_HEIGHT = 400

ExceptionHandler.set_application_name(APPLICATION_NAME)


class ChessError(Exception):
    """Exception class fo chess module."""


class Chess(ExceptionHandler):
    """Connect a chess database with User Interface."""

    _index = GAMES_FILE_DEF
    _open_msg = "Open a chess database with Database | Open"

    def __init__(self, dptmultistepdu=False, dptchunksize=None, **kargs):
        """Create the database and ChessUI objects.

        dptmultistepdu is True: use multi-step deferred update in dpt
        otherwise use single-step deferred update in dpt.
        dptchunksize is None: obey dptmultistepdu rules for deferred update.
        dptchunksize is integer >= 5000: divide pgn file into dptchunksize game
        chunks and do a single-step deferred update for each chunk.
        otherwise behave as if dptchunksize == 5000.
        This parameter is provided to cope with running deferred updates under
        versions of Wine which do not report memory usage correctly causing
        dpt single-step deferred update to fail after processing a few
        thousand games.

        **kargs - passed through to database object

        """
        self.root = tkinter.Tk()
        try:
            self.root.wm_title(APPLICATION_NAME)
            self.root.wm_minsize(
                width=STARTUP_MINIMUM_WIDTH, height=STARTUP_MINIMUM_HEIGHT
            )

            if dptchunksize is not None:
                if not isinstance(dptchunksize, int):
                    dptchunksize = 5000
                self._dptchunksize = max(dptchunksize, 5000)
                self._dptmultistepdu = False
            else:
                self._dptchunksize = dptchunksize
                self._dptmultistepdu = dptmultistepdu is True
            self._database_class = None
            self._chessdbkargs = kargs
            self.opendatabase = None
            self._database_enginename = None
            self._database_modulename = None
            self._partialposition_class = None
            self._fullposition_class = None
            self._engineanalysis_class = None
            self._selection_class = None
            self._pgnfiles = None
            self.queue = None
            self.reportqueue = queue.Queue(maxsize=1)

            # For tooltip binding, if it ever works.
            # See create_menu_changed_callback() method.
            menus = []

            menubar = tkinter.Menu(self.root)
            menus.append(menubar)

            menu1 = tkinter.Menu(menubar, name="database", tearoff=False)
            menus.append(menu1)
            menubar.add_cascade(label="Database", menu=menu1, underline=0)
            for accelerator, function in (
                (EventSpec.menu_database_open, self.database_open),
                (EventSpec.menu_database_new, self.database_new),
                (EventSpec.menu_database_close, self.database_close),
                (EventSpec.menu_database_delete, self.database_delete),
                (EventSpec.menu_database_quit, self.database_quit),
            ):
                menu1.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu1),
                    underline=accelerator[3],
                )
            menu1.add_separator()
            menu101 = tkinter.Menu(menu1, name="export", tearoff=False)
            menu1.insert_cascade(
                3,
                label=EventSpec.menu_database_export[1],
                menu=menu101,
                underline=EventSpec.menu_database_export[3],
            )
            menu102 = tkinter.Menu(menu1, name="import", tearoff=False)
            menu1.insert_cascade(
                3,
                label=EventSpec.menu_database_import[1],
                menu=menu102,
                underline=EventSpec.menu_database_import[3],
            )
            for index in (6, 5, 3, 0):
                menu1.insert_separator(index)
            for accelerator, function in (
                (EventSpec.menu_database_games, self.database_import),
                (EventSpec.menu_database_repertoires, self.import_repertoires),
                (EventSpec.menu_database_positions, self.import_positions),
            ):
                menu102.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu102),
                    underline=accelerator[3],
                )
            menu10101 = tkinter.Menu(menu101, name="games", tearoff=False)
            menu101.add_cascade(
                label=EventSpec.menu_database_games[1],
                menu=menu10101,
                underline=EventSpec.menu_database_games[3],
            )
            for accelerator, function in (
                (
                    EventSpec.pgn_reduced_export_format,
                    self.export_all_games_pgn_reduced_export_format,
                ),
                (
                    EventSpec.pgn_export_format_no_comments_no_ravs,
                    self.export_all_games_pgn_no_comments_no_ravs,
                ),
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_all_games_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_all_games_pgn),
                (
                    EventSpec.pgn_import_format,
                    self.export_all_games_pgn_import_format,
                ),
                (EventSpec.text_internal_format, self.export_all_games_text),
            ):
                menu10101.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu10101),
                    underline=accelerator[3],
                )
            menu10102 = tkinter.Menu(
                menu101, name="repertoires", tearoff=False
            )
            menu101.add_cascade(
                label=EventSpec.menu_database_repertoires[1],
                menu=menu10102,
                underline=EventSpec.menu_database_repertoires[3],
            )
            for accelerator, function in (
                (
                    EventSpec.pgn_export_format_no_comments,
                    self.export_all_repertoires_pgn_no_comments,
                ),
                (EventSpec.pgn_export_format, self.export_all_repertoires_pgn),
                (
                    EventSpec.pgn_import_format,
                    self.export_all_repertoires_pgn_import_format,
                ),
                (
                    EventSpec.text_internal_format,
                    self.export_all_repertoires_text,
                ),
            ):
                menu10102.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu10102),
                    underline=accelerator[3],
                )
            for accelerator, function in (
                (EventSpec.menu_database_positions, self.export_positions),
                (
                    EventSpec.menu_database_export_all_text,
                    self.export_all_games_text,
                ),
            ):
                menu101.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu101),
                    underline=accelerator[3],
                )

            menu2 = tkinter.Menu(menubar, name="select", tearoff=False)
            menus.append(menu2)
            menubar.add_cascade(label="Select", menu=menu2, underline=0)
            for accelerator, function in (
                (EventSpec.menu_select_rule, self.index_select),
                (EventSpec.menu_show, self.index_show),
                (EventSpec.menu_hide, self.index_hide),
                (
                    EventSpec.menu_select_game,
                    self.create_options_index_callback(GAMES_FILE_DEF),
                ),
                (
                    EventSpec.menu_select_error,
                    self.create_options_index_callback(SOURCE_FIELD_DEF),
                ),
            ):
                menu2.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu2),
                    underline=accelerator[3],
                )
            menu2.add_separator()
            menu201 = tkinter.Menu(menu2, name="index", tearoff=False)
            menus.append(menu201)
            menu2.insert_cascade(
                4,
                label=EventSpec.menu_select_index[1],
                menu=menu201,
                underline=EventSpec.menu_select_index[3],
            )
            for index in (5, 4, 3, 1, 0):
                menu2.insert_separator(index)
            for accelerator, field in (
                (EventSpec.menu_select_index_black, BLACK_FIELD_DEF),
                (EventSpec.menu_select_index_white, WHITE_FIELD_DEF),
                (EventSpec.menu_select_index_event, EVENT_FIELD_DEF),
                (EventSpec.menu_select_index_date, DATE_FIELD_DEF),
                (EventSpec.menu_select_index_result, RESULT_FIELD_DEF),
                (EventSpec.menu_select_index_site, SITE_FIELD_DEF),
                (EventSpec.menu_select_index_round, ROUND_FIELD_DEF),
            ):
                menu201.add_command(
                    label=accelerator[1],
                    command=self.try_command(
                        self.create_options_index_callback(field), menu201
                    ),
                    underline=accelerator[3],
                )

            menu3 = tkinter.Menu(menubar, name="game", tearoff=False)
            menus.append(menu3)
            menubar.add_cascade(label="Game", menu=menu3, underline=0)
            menu3.add_separator()
            for accelerator, function in (
                (EventSpec.menu_game_new_game, self.game_new_game),
            ):
                menu3.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu3),
                    underline=accelerator[3],
                )
            menu3.add_separator()

            menu4 = tkinter.Menu(menubar, name="position", tearoff=False)
            menus.append(menu4)
            menubar.add_cascade(label="Position", menu=menu4, underline=0)
            for accelerator, function in (
                (EventSpec.menu_position_partial, self.position_partial),
                (EventSpec.menu_show, self.position_show),
                (EventSpec.menu_hide, self.position_hide),
            ):
                menu4.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu4),
                    underline=accelerator[3],
                )
            menu4.add_separator()
            for index in (1, 0):
                menu4.insert_separator(index)

            menu5 = tkinter.Menu(menubar, name="repertoire", tearoff=False)
            menus.append(menu5)
            menubar.add_cascade(label="Repertoire", menu=menu5, underline=0)
            for accelerator, function in (
                (EventSpec.menu_repertoire_opening, self.repertoire_game),
                (EventSpec.menu_show, self.repertoire_show),
                (EventSpec.menu_hide, self.repertoire_hide),
            ):
                menu5.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu5),
                    underline=accelerator[3],
                )
            menu5.add_separator()
            for index in (1, 0):
                menu5.insert_separator(index)

            menu6 = tkinter.Menu(menubar, name="tools", tearoff=False)
            menus.append(menu6)
            menubar.add_cascade(label="Tools", menu=menu6, underline=0)
            for accelerator, function in (
                (EventSpec.menu_tools_board_style, self.select_board_style),
                (EventSpec.menu_tools_board_fonts, self.select_board_fonts),
                (
                    EventSpec.menu_tools_board_colours,
                    self.select_board_colours,
                ),
                (
                    EventSpec.menu_tools_hide_game_analysis,
                    self.hide_game_analysis,
                ),
                (
                    EventSpec.menu_tools_show_game_analysis,
                    self.show_game_analysis,
                ),
                (
                    EventSpec.menu_tools_hide_game_scrollbars,
                    self.hide_scrollbars,
                ),
                (
                    EventSpec.menu_tools_show_game_scrollbars,
                    self.show_scrollbars,
                ),
                (
                    EventSpec.menu_tools_toggle_game_move_numbers,
                    self.toggle_game_move_numbers,
                ),
                (
                    EventSpec.menu_tools_toggle__analysis_fen,
                    self.toggle_analysis_fen,
                ),
                (
                    EventSpec.menu_tools_toggle_single_view,
                    self.toggle_single_view,
                ),
            ):
                menu6.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menu6),
                    underline=accelerator[3],
                )
            menu6.add_separator()
            for index in (9, 8, 7, 5, 3, 0):
                menu6.insert_separator(index)

            menu7 = tkinter.Menu(menubar, name="engines", tearoff=False)
            menus.append(menu7)
            menubar.add_cascade(label="Engines", menu=menu7, underline=0)

            menu8 = tkinter.Menu(menubar, name="commands", tearoff=False)
            menus.append(menu7)
            menubar.add_cascade(label="Commands", menu=menu8, underline=0)

            menuhelp = tkinter.Menu(menubar, name="help", tearoff=False)
            menus.append(menuhelp)
            menubar.add_cascade(label="Help", menu=menuhelp, underline=0)
            menuhelp.add_separator()
            for accelerator, function in (
                (EventSpec.menu_help_guide, self.help_guide),
                (EventSpec.menu_help_selection_rules, self.help_selection),
                (EventSpec.menu_help_file_size, self.help_file_size),
                (EventSpec.menu_help_notes, self.help_notes),
                (EventSpec.menu_help_about, self.help_about),
            ):
                menuhelp.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menuhelp),
                    underline=accelerator[3],
                )
            menuhelp.add_separator()

            self.root.configure(menu=menubar)

            for menu in menus:
                menu.bind(
                    "<<MenuSelect>>",
                    self.try_event(self.create_menu_changed_callback(menu)),
                )

            toolbarframe = tkinter.ttk.Frame(self.root)
            toolbarframe.pack(side=tkinter.TOP, fill=tkinter.X)
            self.statusbar = Statusbar(
                toolbarframe, self.root.cget("background")
            )
            toppane = tkinter.ttk.PanedWindow(
                self.root,
                # background='cyan2',
                # opaqueresize=tkinter.FALSE,
                width=STARTUP_MINIMUM_WIDTH * 2,
                orient=tkinter.HORIZONTAL,
            )
            toppane.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)

            self.ui = ChessUI(
                toppane,
                statusbar=self.statusbar,
                uci=UCI(menu7, menu8),
                toolbarframe=toolbarframe,
            )
            self.queue = callthreadqueue.CallThreadQueue()

            # See comment near end of class definition ChessDeferredUpdate in
            # sibling module chessdu for explanation of this change.
            self.__run_ui_task_from_queue(5000)

        except Exception as exc:
            self.root.destroy()
            del self.root
            # pylint message broad-except.
            # Can keep going for some exceptions.
            raise ChessError(
                " initialize ".join(("Unable to ", APPLICATION_NAME))
            ) from exc

    def __del__(self):
        """Ensure database Close method is called on destruction."""
        if self.opendatabase:
            self.opendatabase.close_database()
            self.opendatabase = None

    def database_open(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def database_new(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def database_close(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def database_delete(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def database_quit(self):
        """Quit chess database."""
        if self.is_import_subprocess_active():
            quitmsg = "".join(
                (
                    "An import of PGN data is in progress.\n\n",
                    "The import will continue if you confirm quit but you ",
                    "will not be informed when the import finishes nor if ",
                    "it succeeded.  Try opening it later or examine the ",
                    "error log to find out.\n\n",
                    "You will not be able to open this database again until ",
                    "the import has finished.",
                )
            )
        else:
            quitmsg = "Confirm Quit"
        dlg = tkinter.messagebox.askquestion(
            parent=self.get_toplevel(), title="Quit", message=quitmsg
        )
        if dlg == tkinter.messagebox.YES:
            if self.ui.uci:
                self.ui.uci.remove_engines_and_menu_entries()
            if self.opendatabase:
                self._close_recordsets()
                self.opendatabase.close_database()
                self.opendatabase = None
                self._set_error_file_name(directory=None)
            self.root.destroy()

    def is_import_subprocess_active(self):
        """Return the exception report file object."""
        return self.ui.is_import_subprocess_active()

    def get_toplevel(self):
        """Return the toplevel widget."""
        return self.root

    def _close_recordsets(self):
        """Do nothing.  Override in chess_database.Chess class.

        The override in chess_database.Chess has significant, but obsolete,
        block comments in the source code.
        """

    @staticmethod
    def _set_error_file_name(directory=None):
        """Set the exception report file name to filename."""
        if directory is None:
            Chess.set_error_file_name(None)
        else:
            Chess.set_error_file_name(os.path.join(directory, ERROR_LOG))

    def database_import(self):
        """Do nothing.  Override in chess_import.Chess class."""

    def import_repertoires(self):
        """Do nothing.  Override in chess_import.Chess class."""

    def import_positions(self):
        """Do nothing.  Override in chess_import.Chess class."""

    def export_all_games_pgn_reduced_export_format(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_games_pgn_no_comments_no_ravs(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_games_pgn_no_comments(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_games_pgn(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_games_pgn_import_format(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_games_text(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_repertoires_pgn_no_comments(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_repertoires_pgn(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_repertoires_pgn_import_format(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_all_repertoires_text(self):
        """Do nothing.  Override in chess.Chess class."""

    def export_positions(self):
        """Do nothing.  Override in chess.Chess class."""

    def index_select(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def index_show(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def index_hide(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def create_options_index_callback(self, index):
        """Do nothing.  Override in chess_database.Chess class."""

    def game_new_game(self):
        """Enter a new game (callback for Menu option)."""
        self.new_game()

    def new_game(self):
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

    def position_partial(self):
        """Enter a new partial position (callback for Menu option)."""
        self.new_partial_position()

    def new_partial_position(self):
        """Enter a new partial position."""
        position = CQLDisplayInsert(
            master=self.ui.view_partials_pw,
            ui=self.ui,
            items_manager=self.ui.partial_items,
            itemgrid=self.ui.partial_games,
        )
        position.cql_statement.process_statement("")
        position.set_and_tag_item_text(reset_undo=True)
        self.ui.add_partial_position_to_display(position)
        try:
            # Is new window only one available for user interaction?
            if self.root.focus_displayof() != self.root:
                return
        except KeyError:
            # Launch; Database Open; Database Close; Position Partial
            pass

        # Wrap to take account of self.ui.single_view
        self.ui.partial_items.active_item.takefocus_widget.focus_set()

    def position_show(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def position_hide(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def repertoire_game(self):
        """Enter a new opening variation (callback for Menu option)."""
        self.new_repertoire_game()

    def new_repertoire_game(self):
        """Enter a new repertoire game (opening variation)."""
        game = RepertoireDisplayInsert(
            master=self.ui.view_repertoires_pw,
            ui=self.ui,
            items_manager=self.ui.repertoire_items,
            itemgrid=self.ui.repertoire_games,
        )
        game.set_position_analysis_data_source()
        game.collected_game = next(
            PGN(game_class=game.gameclass).read_games(
                "".join((constants.EMPTY_REPERTOIRE_GAME, UNKNOWN_RESULT))
            )
        )
        game.set_and_tag_item_text(reset_undo=True)
        self.ui.add_repertoire_to_display(game)
        try:
            # Is new window only one available for user interaction?
            if self.root.focus_displayof() != self.root:
                return
        except KeyError:
            # Launch; Database Open; Database Close; Game New
            pass

        # Wrap to take account of self.ui.single_view
        self.ui.repertoire_items.active_item.takefocus_widget.focus_set()

    def repertoire_show(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def repertoire_hide(self):
        """Do nothing.  Override in chess_database.Chess class."""

    def select_board_style(self):
        """Choose and set colour scheme and font forchessboard."""
        decor = colourscheme.FontColourChooser(ui=self.ui)
        if decor.is_ok():
            if self.opendatabase:
                options.save_options(
                    self.opendatabase.home_directory, decor.get_options()
                )
            decor.apply_to_named_fonts()
            self.ui.set_board_fonts(decor)
            self.ui.set_board_colours(decor)

    def select_board_fonts(self):
        """Choose and set font for board."""
        decor = colourscheme.FontChooser(ui=self.ui)
        if decor.is_ok():
            if self.opendatabase:
                options.save_options(
                    self.opendatabase.home_directory, decor.get_options()
                )
            decor.apply_to_named_fonts()
            self.ui.set_board_fonts(decor)

    def select_board_colours(self):
        """Choose and set colour scheme for board."""
        decor = colourscheme.ColourChooser(ui=self.ui)
        if decor.is_ok():
            if self.opendatabase:
                options.save_options(
                    self.opendatabase.home_directory, decor.get_options()
                )
            self.ui.set_board_colours(decor)

    def hide_game_analysis(self):
        """Hide the widgets which show analysis from chess engines."""
        self.ui.show_analysis = False
        exceptions = []
        for games in (
            self.ui.game_items.order,
            self.ui.repertoire_items.order,
            self.ui.games_and_repertoires_in_toplevels,
        ):
            for game in games:
                try:
                    game.hide_game_analysis()
                except tkinter.TclError:
                    exceptions.append((game, games))
        for game, games in exceptions:
            games.remove(game)

    def show_game_analysis(self):
        """Show the widgets which show analysis from chess engines."""
        self.ui.show_analysis = True
        exceptions = []
        for games in (
            self.ui.game_items.order,
            self.ui.repertoire_items.order,
            self.ui.games_and_repertoires_in_toplevels,
        ):
            for game in games:
                try:
                    game.show_game_analysis()
                except tkinter.TclError:
                    exceptions.append((game, games))
        for game, games in exceptions:
            games.remove(game)

    def hide_scrollbars(self):
        """Hide the scrollbars in the game display widgets."""
        self.ui.hide_scrollbars()
        self.ui.uci.hide_scrollbars()

    def show_scrollbars(self):
        """Show the scrollbars in the game display widgets."""
        self.ui.show_scrollbars()
        self.ui.uci.show_scrollbars()

    def toggle_game_move_numbers(self):
        """Toggle display of move numbers in game score widgets."""
        exceptions = []
        for games in (
            self.ui.game_items.order,
            self.ui.repertoire_items.order,
            self.ui.games_and_repertoires_in_toplevels,
        ):
            for game in games:
                try:
                    game.toggle_game_move_numbers()
                except tkinter.TclError:
                    exceptions.append((game, games))
        for game, games in exceptions:
            games.remove(game)

    def toggle_analysis_fen(self):
        """Toggle display of PGN tags in analysis widgets."""
        exceptions = []
        for games in (
            self.ui.game_items.order,
            self.ui.repertoire_items.order,
            self.ui.games_and_repertoires_in_toplevels,
        ):
            for game in games:
                try:
                    game.toggle_analysis_fen()
                except tkinter.TclError:
                    exceptions.append((game, games))
        for game, games in exceptions:
            games.remove(game)

    def toggle_single_view(self):
        """Toggle display single pane or all panes with non-zero weight."""
        if self.ui.single_view:
            self.ui.show_all_panedwindows()
        else:
            self.ui.show_just_panedwindow_with_focus(
                self.ui.top_pw.focus_displayof()
            )

    def help_guide(self):
        """Display brief User Guide for Chess application."""
        help_.help_guide(self.root)

    def help_selection(self):
        """Display description of selection rules for Chess application."""
        help_.help_selection(self.root)

    def help_file_size(self):
        """Display brief instructions for file size dialogue."""
        help_.help_file_size(self.root)

    def help_notes(self):
        """Display technical notes about Chess application."""
        help_.help_notes(self.root)

    def help_about(self):
        """Display information about Chess application."""
        help_.help_about(self.root)

    @staticmethod
    def create_menu_changed_callback(menu):
        """Return callback to bind to <<MenuSelect>> event for menu."""
        del menu

        def menu_changed(event):
            """Display menu tip in status bar."""
            # entrycget('active', <property>) always returns None
            # <index> and 'end' forms work though
            # even tried repeating in an 'after_idle' call
            # similar on FreeBSD and W2000
            # PERL has same problem as found when looked at www
            # print 'menu changed', menu.entrycget('active', 'label')
            # print menu, event, 'changed', menu.entrycget('active', 'label')
            del event

        return menu_changed

    # See comment near end of class definition ChessDeferredUpdate in sibling
    # module chessdu for explanation of this change: which is addition and use
    # of the __run_ui_task_from_queue and try_command_after_idle methods.

    def __run_ui_task_from_queue(self, interval):
        """Do all queued tasks then wake-up after interval."""
        while True:
            try:
                method, args, kwargs = self.reportqueue.get_nowait()
                method(*args, **kwargs)
            except queue.Empty:
                self.root.after(
                    interval,
                    self.try_command(self.__run_ui_task_from_queue, self.root),
                    *(interval,)
                )
                break
            self.reportqueue.task_done()


class Statusbar:
    """Status bar for chess application."""

    def __init__(self, root, background):
        """Create status bar widget."""
        self.status = tkinter.Text(
            root,
            height=0,
            width=0,
            background=background,
            relief=tkinter.FLAT,
            state=tkinter.DISABLED,
            wrap=tkinter.NONE,
        )
        self.status.pack(
            side=tkinter.RIGHT, expand=tkinter.TRUE, fill=tkinter.X
        )

    def get_status_text(self):
        """Return text displayed in status bar."""
        return self.status.cget("text")

    def set_status_text(self, text=""):
        """Display text in status bar."""
        self.status.configure(state=tkinter.NORMAL)
        self.status.delete("1.0", tkinter.END)
        self.status.insert(tkinter.END, text)
        self.status.configure(state=tkinter.DISABLED)
