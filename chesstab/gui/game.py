# game.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a game of chess.

The display contains the game score, a board with the current position in the
game, and any analysis of the current position by chess engines.

The Game class displays a game of chess.

Instances of Game have an instance of score.Score as an attribute to display
chess engine analysis as well as inheriting much of their function from the
Score class.

An instance of Game fits into the user interface in two ways: as an item in a
panedwindow of the main widget, or as the only item in a new toplevel widget.

"""
# Obsolete comment, but the idea is being realised through the displaypgn and
# displaytext modules.  (partial has meanwhile become cql).
# Game (game.py) and Partial (partial.py) should be
# subclasses of some more basic class.  They are not because Game started
# as a game displayer while Partial started as a Text widget with no
# validation and they have been converging ever since.  Next step will get
# there.  Obviously this applies to subclasses GameEdit (gameedit.py)
# and PartialEdit (partialedit.py) as well.

# Score is now a superclass of Game.  It is a PGN handling class, not the
# 'more basic class' above.

import tkinter

from pgn_read.core.constants import (
    TAG_FEN,
)
from pgn_read.core.parser import PGN
from pgn_read.core.game import generate_fen_for_position

from ..core.pgn import (
    GameDisplayMoves,
    GameAnalysis,
)
from .board import Board
from .score import Score, AnalysisScore, ScoreNoGameException
from .constants import (
    ANALYSIS_INDENT_TAG,
    ANALYSIS_PGN_TAGS_TAG,
    MOVETEXT_INDENT_TAG,
    FORCED_INDENT_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    STATUS_SEVEN_TAG_ROSTER_PLAYERS,
)
from .eventspec import EventSpec
from ..core.analysis import Analysis
from ..core.constants import (
    UNKNOWN_RESULT,
    END_TAG,
    START_TAG,
)


class Game(Score):
    """Chess game widget composed from Board and Text widgets.

    master is used as the master argument for the tkinter Frame widget passed
    to superclass and the Board call.

    ui is used as the ui argument in the Board call, and bound to the ui
    attribute of self.

    The Board widget is used as the board argument in the super().__init__
    and AnalysisScore calls.

    tags_variations_comments_font is used as the tags_variations_comments_font
    argument in the super().__init__ and AnalysisScore calls.

    moves_played_in_game_font is used as the moves_played_in_game_font
    argument in the super().__init__ and AnalysisScore calls.

    items_manager is used as the items_manager argument in the
    super().__init__ and AnalysisScore calls.

    itemgrid is used as the itemgrid argument in the super().__init__ and
    AnalysisScore calls.

    boardfont is used as the boardfont argument in the Board call.

    gameclass is used as the gameclass argument in the super().__init__ call.

    Analysis of the game's current position, where available, is provided by
    an AnalysisDS instance from the dpt.analysisds or basecore.analysisds
    modules.

    """

    # Some menu popup entries in the Game hierarchy declare their location
    # as 'before Analyse' or 'before Export'.  This is a convenient way of
    # getting the popup entries in the desired order, taking order of
    # execution of various methods into account: nothing special about the
    # analyse or export entries otherwise.
    analyse_popup_label = EventSpec.analyse_game[1]
    export_popup_label = EventSpec.menu_database_export[1]

    def __init__(
        self,
        master=None,
        tags_variations_comments_font=None,
        moves_played_in_game_font=None,
        boardfont=None,
        gameclass=GameDisplayMoves,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka
    ):
        """Create Frame and Board, then delegate, then set grid geometry."""
        self.ui = ui
        panel = tkinter.Frame(master, borderwidth=2, relief=tkinter.RIDGE)
        panel.bind("<Configure>", self.try_event(self._on_configure))
        panel.grid_propagate(False)
        board = Board(panel, boardfont=boardfont, ui=ui)
        super().__init__(
            panel,
            board,
            tags_variations_comments_font=tags_variations_comments_font,
            moves_played_in_game_font=moves_played_in_game_font,
            gameclass=gameclass,
            items_manager=items_manager,
            itemgrid=itemgrid,
            **ka
        )
        self.scrollbar.grid(column=2, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.analysis = AnalysisScore(
            panel,
            board,
            owned_by_game=self,
            tags_variations_comments_font=tags_variations_comments_font,
            moves_played_in_game_font=moves_played_in_game_font,
            gameclass=GameAnalysis,
            items_manager=items_manager,
            itemgrid=itemgrid,
            **ka
        )
        self.score.tag_configure(FORCED_INDENT_TAG, lmargin1=20)
        self.score.tag_configure(MOVETEXT_INDENT_TAG, lmargin2=20)
        self.score.tag_configure(MOVETEXT_MOVENUMBER_TAG, elide=tkinter.FALSE)
        self.analysis.score.configure(wrap=tkinter.WORD)
        self.analysis.score.tag_configure(ANALYSIS_INDENT_TAG, lmargin2=80)
        self.analysis.score.tag_configure(
            ANALYSIS_PGN_TAGS_TAG, elide=tkinter.TRUE
        )
        self.analysis.scrollbar.grid(
            column=2, row=1, rowspan=1, sticky=tkinter.NSEW
        )
        self.board.get_top_widget().grid(
            column=0, row=0, rowspan=1, sticky=tkinter.NSEW
        )
        self.score.grid(column=1, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.analysis.score.grid(
            column=0, row=1, columnspan=2, sticky=tkinter.NSEW
        )
        if not ui.show_analysis:
            panel.after_idle(self.hide_game_analysis)
        if not ui.visible_scrollbars:
            panel.after_idle(self.hide_scrollbars)
        self.configure_game_widget()

        # True means analysis widget refers to same position as game widget; so
        # highlighting of analysis still represents future valid navigation.
        # Any navigation in game widget makes any highlighting in analysis
        # widget out of date.
        self.game_position_analysis = False

        self.game_analysis_in_progress = False
        self.takefocus_widget = self.score
        self.analysis_data_source = None

    def get_top_widget(self):
        """Return topmost widget for game display."""
        return self.panel

    def destroy_widget(self):
        """Destroy the widget displaying game."""
        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under Wine on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        # try:
        #    self.ui.uci.uci.ui_analysis_queue.put(
        #        (self.analysis.score, self.analysis.score))
        # except AttributeError:
        #    if self.ui.uci.uci.uci_drivers_reply is not None:
        #        raise
        self.ui.uci.uci.ui_analysis_queue.put(
            (self.analysis.score, self.analysis.score)
        )
        self.panel.destroy()

    def _on_configure(self, event=None):
        """Catch initial configure and rebind to on_configure."""
        # Not sure, at time of writing this, how partial.py is
        # different but that module does not need this trick to display
        # the control with the right size on creation.
        # Here extra first event has width=1 height=1 followed up by event
        # with required dimensions.
        self.panel.bind("<Configure>", self.try_event(self.on_configure))

    def on_configure(self, event=None):
        """Reconfigure board and score after container has been resized."""
        self.configure_game_widget()
        self.see_current_move()

    def _analyse_position(self, *position):
        analysis = self.get_analysis(*position)
        self.refresh_analysis_widget_from_database(analysis)
        if self.game_analysis_in_progress:
            if not self.ui.uci.uci.is_positions_pending_empty():
                return
            self.game_analysis_in_progress = False
        analysis.variations.clear()

        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under Wine on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        # try:
        #    self.ui.uci.uci.ui_analysis_queue.put((self.analysis.score, pa))
        # except AttributeError:
        #    if self.ui.uci.uci.uci_drivers_reply is not None:
        #        raise
        self.ui.uci.uci.ui_analysis_queue.put((self.analysis.score, analysis))

    def set_game_board(self):
        """Set board to show position after highlighted move."""
        # Assume setting new position implies analysis is out of date.
        # Caller should reset to True if sure analysis still refers to game
        # position. (Probably just F7 or F8 to the game widget.)
        self.game_position_analysis = False

        if not super().set_game_board():
            return
        if self.current is None:
            position = self.fen_tag_tuple_square_piece_map()
        else:
            position = self.tagpositionmap[self.current]
        self._analyse_position(*position)

    def set_and_tag_item_text(self, reset_undo=False):
        """Delegate then queue analysis request to chess engines."""
        try:
            super().set_and_tag_item_text(reset_undo=reset_undo)
        except ScoreNoGameException:
            return
        self.score.tag_add(MOVETEXT_INDENT_TAG, "1.0", tkinter.END)
        self._analyse_position(*self.fen_tag_tuple_square_piece_map())

    def analyse_game(self):
        """Analyse all positions in game using all active engines."""
        uci = self.ui.uci.uci
        sas = self.analysis.score
        sga = self.get_analysis
        self.game_analysis_in_progress = True
        for value in self.tagpositionmap.values():
            analysis = sga(*value)
            analysis.variations.clear()

            # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3
            # running under Wine on FreeBSD 10.1 by disabling the UCI functions.
            # Assume all later Pythons are affected because they do not install
            # under Wine at time of writing.
            # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
            # get_nowait() fails to 'not wait', so ChessTab never gets going
            # under wine at present.  Leave alone because it looks like the
            # problem is being shifted constructively.
            # At Python3.5 running under Wine on FreeBSD 10.1, get() does not
            # wait when the queue is empty either, and ChessTab does not run
            # under Python3.3 because it uses asyncio: so no point in disabling.
            # try:
            #    uci.ui_analysis_queue.put((sas, pa))
            # except AttributeError:
            #    if uci.uci_drivers_reply is not None:
            #        raise
            #    break
            uci.ui_analysis_queue.put((sas, analysis))

    def hide_game_analysis(self):
        """Hide the widgets which show analysis from chess engines."""
        self.analysis.score.grid_remove()
        self.analysis.scrollbar.grid_remove()
        self.score.grid_configure(rowspan=2)
        if self.score.grid_info()["columnspan"] == 1:
            self.scrollbar.grid_configure(rowspan=2)
        self.configure_game_widget()
        self.see_current_move()

    def show_game_analysis(self):
        """Show the widgets which show analysis from chess engines."""
        self.score.grid_configure(rowspan=1)
        if self.score.grid_info()["columnspan"] == 1:
            self.scrollbar.grid_configure(rowspan=1)
            self.analysis.score.grid_configure(columnspan=2)
            self.analysis.scrollbar.grid_configure()
        else:
            self.analysis.score.grid_configure(columnspan=3)
        self.configure_game_widget()
        self.see_current_move()

    def hide_scrollbars(self):
        """Hide the scrollbars in the game display widgets."""
        self.scrollbar.grid_remove()
        self.analysis.scrollbar.grid_remove()
        self.score.grid_configure(columnspan=2)
        if self.score.grid_info()["rowspan"] == 1:
            self.analysis.score.grid_configure(columnspan=3)
        self.configure_game_widget()
        self.see_current_move()

    def show_scrollbars(self):
        """Show the scrollbars in the game display widgets."""
        self.score.grid_configure(columnspan=1)
        if self.score.grid_info()["rowspan"] == 1:
            self.scrollbar.grid_configure(rowspan=1)
            self.analysis.score.grid_configure(columnspan=2)
            self.analysis.scrollbar.grid_configure()
        else:
            self.scrollbar.grid_configure(rowspan=2)
        self.configure_game_widget()
        self.see_current_move()

    def toggle_analysis_fen(self):
        """Toggle display of FEN in analysis widgets."""
        widget = self.analysis.score
        if int(widget.tag_cget(ANALYSIS_PGN_TAGS_TAG, "elide")):
            widget.tag_configure(ANALYSIS_PGN_TAGS_TAG, elide=tkinter.FALSE)
        else:
            widget.tag_configure(ANALYSIS_PGN_TAGS_TAG, elide=tkinter.TRUE)
        self.see_current_move()

    def toggle_game_move_numbers(self):
        """Toggle display of move numbers in game score widgets."""
        widget = self.score
        if int(widget.tag_cget(MOVETEXT_MOVENUMBER_TAG, "elide")):
            widget.tag_configure(MOVETEXT_MOVENUMBER_TAG, elide=tkinter.FALSE)
        else:
            widget.tag_configure(MOVETEXT_MOVENUMBER_TAG, elide=tkinter.TRUE)
        self.see_current_move()

    def refresh_analysis_widget_from_engine(self, analysis):
        """Refresh game widget with updated chess engine analysis."""
        uci = self.ui.uci.uci
        move_played = self.get_move_for_start_of_analysis()
        if analysis.position in uci.position_analysis:
            new_text = uci.position_analysis[
                analysis.position
            ].translate_analysis_to_pgn(move_played=move_played)
        else:
            new_text = []
            new_text.append(UNKNOWN_RESULT)
            if move_played:
                new_text.insert(0, move_played)
                new_text.insert(
                    0,
                    "".join(
                        (
                            START_TAG,
                            TAG_FEN,
                            '"',
                            analysis.position,
                            END_TAG.join('"\n'),
                        )
                    ),
                )
            new_text = "".join(new_text)
        if new_text == self.analysis.analysis_text:
            return

        # Assume TypeError exception happens because analysis is being shown
        # for a position which is checkmate or stalemate.
        try:
            self.analysis.collected_game = next(
                PGN(game_class=self.analysis.gameclass).read_games(new_text)
            )
        except TypeError:
            pass

        # Assume analysis movetext problems occur only if editing moves.
        # if not pgn.is_movetext_valid():
        if not self.analysis.collected_game.is_movetext_valid():
            return

        self.analysis.clear_score()
        self.analysis.set_score(new_text)
        try:
            fmog = self.analysis.select_first_move_of_game()
        except tkinter.TclError:
            fmog = False
        if fmog:
            widget = self.analysis.score
            widget.tag_add(
                ANALYSIS_INDENT_TAG, widget.tag_ranges(fmog)[0], tkinter.END
            )
            widget.tag_add(
                ANALYSIS_PGN_TAGS_TAG, "1.0", widget.tag_ranges(fmog)[0]
            )

    def refresh_analysis_widget_from_database(self, analysis):
        """Refresh game widget with updated chess engine analysis."""
        # When a database is open the analysis is refreshed from the database
        # while checking if that analysis is up-to-date compared with the depth
        # and multiPV parameters held in self.uci.uci UCI object.
        if self.ui.database is None:
            self.refresh_analysis_widget_from_engine(analysis)
            return

        # Assume TypeError exception happens because analysis is being shown
        # for a position which is checkmate or stalemate.
        try:
            new_text = analysis.translate_analysis_to_pgn(
                self.get_move_for_start_of_analysis()
            )
        except TypeError:
            return

        if new_text == self.analysis.analysis_text:
            return

        # Assume TypeError exception happens because analysis is being shown
        # for a position which is checkmate or stalemate.
        try:
            self.analysis.collected_game = next(
                PGN(game_class=self.analysis.gameclass).read_games(new_text)
            )
        except TypeError:
            pass

        self.analysis.clear_score()
        self.analysis.set_score(new_text)
        try:
            fmog = self.analysis.select_first_move_of_game()
        except tkinter.TclError:
            fmog = False
        if fmog:
            widget = self.analysis.score
            widget.tag_add(
                ANALYSIS_INDENT_TAG, widget.tag_ranges(fmog)[0], tkinter.END
            )
            widget.tag_add(
                ANALYSIS_PGN_TAGS_TAG, "1.0", widget.tag_ranges(fmog)[0]
            )

    def refresh_analysis_widget(self, analysis):
        """Refresh game widget with new chess engine analysis."""
        # This method called at regular intervals to cope with fresh analysis
        # of displayed positions due to changes in engine parameters (depth
        # and multiPV). Need a set of new analysis since last call.
        self.refresh_analysis_widget_from_database(analysis)

    def configure_game_widget(self):
        """Configure board and score widgets for a game display."""
        width = self.panel.winfo_width()
        height = self.panel.winfo_height()
        borderwidth = self.panel.cget("borderwidth")
        if self.ui.show_analysis:
            row_minsize = (height - borderwidth * 2) // 2
            column_minsize = width - row_minsize
        else:
            row_minsize = height - borderwidth * 2
            column_minsize = width - borderwidth * 2
            measure = (row_minsize + column_minsize) // 3
            if measure * 3 > column_minsize * 2:
                measure = (column_minsize * 2) // 3
            elif measure > row_minsize:
                measure = row_minsize
            row_minsize = row_minsize - measure
            column_minsize = column_minsize - measure
        self.panel.grid_rowconfigure(1, minsize=row_minsize)
        self.panel.grid_columnconfigure(1, minsize=column_minsize)
        self.panel.grid_rowconfigure(0, weight=1)
        self.panel.grid_rowconfigure(1, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_columnconfigure(1, weight=1)
        self.panel.grid_columnconfigure(2, weight=0)

    def set_primary_activity_bindings(self, switch=True):
        """Delegate then set board pointer move navigation bindings."""
        super().set_primary_activity_bindings(switch=switch)
        if self.score is self.takefocus_widget:
            self.set_board_pointer_move_bindings(switch=switch)
        else:
            self.analysis.set_board_pointer_move_bindings(switch=switch)

    def set_select_variation_bindings(self, switch=True):
        """Delegate then set board pointer select variation bindings."""
        super().set_select_variation_bindings(switch=switch)
        if self.score is self.takefocus_widget:
            self.set_board_pointer_select_variation_bindings(switch=switch)
        else:
            self.analysis.set_board_pointer_select_variation_bindings(
                switch=switch
            )

    # It is not wrong to activate, or deactivate, all three sets of bindings
    # for both self(.score) and self.analysis(.score) but the current choice
    # is to leave Database and Close Item bindings out of self.analysis.
    # Database and Close Item refer to the item, game or repertoire, not the
    # engine analysis.
    def set_database_navigation_close_item_bindings(self, switch=True):
        """Enable or disable bindings for navigation and database selection."""
        self.set_event_bindings_score(
            self.get_database_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigation_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_close_item_events(), switch=switch
        )
        self.analysis.set_event_bindings_score(
            self.get_navigation_events(), switch=switch
        )

    def set_board_pointer_widget_navigation_bindings(self, switch):
        """Enable or disable bindings for widget selection."""
        self.set_event_bindings_board(
            self.get_modifier_buttonpress_suppression_events(), switch=switch
        )
        self.set_event_bindings_board(
            (
                (EventSpec.buttonpress_1, self.give_focus_to_widget),
                (EventSpec.buttonpress_3, self.post_inactive_menu),
            ),
            switch=switch,
        )

    def set_score_pointer_widget_navigation_bindings(self, switch):
        """Set or unset pointer bindings for widget navigation."""
        self.set_event_bindings_board(
            self.get_modifier_buttonpress_suppression_events(), switch=switch
        )
        if not switch:
            bindings = (
                (EventSpec.buttonpress_1, self.press_break),
                (EventSpec.buttonpress_3, self.press_break),
            )
            self.set_event_bindings_score(bindings)
            self.analysis.set_event_bindings_score(bindings)
        else:
            bindings = ((EventSpec.buttonpress_1, self.give_focus_to_widget),)
            self.set_event_bindings_score(bindings)
            self.analysis.set_event_bindings_score(bindings)
            self.set_event_bindings_score(
                ((EventSpec.buttonpress_3, self.post_inactive_menu),)
            )
            self.analysis.set_event_bindings_score(
                ((EventSpec.buttonpress_3, self.analysis.post_inactive_menu),)
            )

    def set_toggle_game_analysis_bindings(self, switch):
        """Set keystoke bindings to switch between game and analysis."""
        self.set_event_bindings_score(
            ((EventSpec.scoresheet_to_analysis, self.analysis_current_item),)
        )
        self.analysis.set_event_bindings_score(
            ((EventSpec.analysis_to_scoresheet, self.current_item),)
        )

    def set_score_pointer_to_score_bindings(self, switch):
        """Set score pointer bindings to go to game."""
        self.set_event_bindings_score(
            ((EventSpec.alt_buttonpress_1, self.current_item),), switch=switch
        )

    def set_analysis_score_pointer_to_analysis_score_bindings(self, switch):
        """Set analysis score pointer bindings to go to analysis score."""
        self.analysis.set_event_bindings_score(
            ((EventSpec.alt_buttonpress_1, self.analysis_current_item),),
            switch=switch,
        )

    def set_colours(self, sbg, bbg, bfg):
        """Set colours and fonts used to display games.

        sbg == True - set game score colours
        bbg == True - set board square colours
        bfg == True - set board piece colours

        """
        if sbg:
            for widget in self, self.analysis:
                widget.score.tag_configure(
                    "l_color", background=widget.l_color
                )
                widget.score.tag_configure(
                    "m_color", background=widget.m_color
                )
                widget.score.tag_configure(
                    "am_color", background=widget.am_color
                )
                widget.score.tag_configure(
                    "v_color", background=widget.v_color
                )
        if bbg:
            self.board.set_color_scheme()
        if bfg:
            self.board.draw_board()

    def set_position_analysis_data_source(self):
        """Attach database analysis for position to game widget."""
        if self.ui is None:
            self.analysis_data_source = None
            return
        self.analysis_data_source = (
            self.ui.make_position_analysis_data_source()
        )

    def get_analysis(self, *a):
        """Return database analysis for position or empty position Analysis.

        get_analysis is not interested in the arguments, which are passed on
        to self.generate_fen_for_position().

        """
        if self.analysis_data_source:
            return self.analysis_data_source.get_position_analysis(
                self.generate_fen_for_position(*a)
            )
        return Analysis(position=self.generate_fen_for_position(*a))

    @staticmethod
    def generate_fen_for_position(squares, *a):
        """Return FEN for current position.

        Ensure the Piece instances in the squares dictionary reference their
        squares key value in the Piece.square attribute before calling the
        generate_fen_for_position() function imported from pgn_read.core.game.

        These can be different while choosing which of the pieces of a type,
        usually two, can make the move specified in the PGN.

        """
        for square, piece in squares.items():
            piece.set_square(square)
        return generate_fen_for_position(squares.values(), *a)

    def create_primary_activity_popup(self):
        """Delegate then add navigation submenu and return popup menu."""
        popup = super().create_primary_activity_popup()
        self.set_popup_bindings(
            popup,
            ((EventSpec.analyse_game, self.analyse_game),),
            index=self.export_popup_label,
        )
        self.create_widget_navigation_submenu_for_popup(popup)
        return popup

    def create_select_move_popup(self):
        """Delegate then add navigation submenu and return popup menu."""
        popup = super().create_select_move_popup()
        self.create_widget_navigation_submenu_for_popup(popup)
        return popup

    def set_statusbar_text(self):
        """Set status bar to display player name PGN Tags."""
        tags = self.collected_game._tags
        self.ui.statusbar.set_status_text(
            "  ".join(
                [tags.get(k, "") for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS]
            )
        )
