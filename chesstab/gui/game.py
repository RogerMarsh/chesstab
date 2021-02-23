# game.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display a game of chess.

The display contains the game score, a board with the current position in the
game, and any analysis of the current position by chess engines.

The Game class displays a game of chess.

The Repertoire class displays PGN text representing an opening repertoire.

Repertoire is a subclass of Game.

Instances of Game have an instance of score.Score as an attribute to display
chess engine analysis as well as inheriting much of their function from the
Score class.

These classes differ in the requirements placed on the pgn package to import,
store, and export, PGN text.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

The gameedit module provides subclasses which allow editing in the main
application window.

The gamedbshow, repertoiredbshow, gamedbedit, and repertoiredbedit, modules
provide subclasses used in a new toplevel widget to display or edit games or
repertoires.

The gamedbdelete and repertoiredbdelete modules provide subclasses used in a
new toplevel widget to allow deletion of games or repertoires from a database.

"""
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

from ..core.pgn import GameDisplayMoves, GameAnalysis
from .board import Board
from .score import Score, AnalysisScore
from ..core import exporters
from .constants import (
    ANALYSIS_INDENT_TAG,
    ANALYSIS_PGN_TAGS_TAG,
    POSITION,
    MOVETEXT_INDENT_TAG,
    FORCED_INDENT_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    )
from .eventspec import EventSpec
from ..core.filespec import ANALYSIS_FILE_DEF
from ..core.analysis import Analysis
from ..core.constants import (
    REPERTOIRE_GAME_TAGS,
    UNKNOWN_RESULT,
    END_TAG,
    START_TAG,
    BOARDSIDE,
    NOPIECE,
    )


class Game(Score):

    """Chess game widget composed from Board and Text widgets.

    Analysis of the game's current position, where available, is provided by
    an AnalysisDS instance from the dpt.analysisds or basecore.analysisds
    modules.
    """

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
        **ka):
        """Extend with widgets to display game.

        master - parent widget for frame created to display game
        tags_variations_comments_font - font for tags variations and comments
        moves_played_in_game_font - font for move played in game
        boardfont - font for pieces on board showing current position
        gameclass - Game subclass for data structure created by PGN class
        ui - the container for game list and game display widgets.

        Create Frame in toplevel and add Canvas and Text.
        Text width and height set to zero so widget fit itself into whatever
        space Frame has available.
        Canvas must be square leaving Text at least half the Frame.

        """
        panel = tkinter.Frame(
            master,
            borderwidth=2,
            relief=tkinter.RIDGE)
        panel.bind('<Configure>', self.try_event(self._on_configure))
        panel.grid_propagate(False)
        board = Board(
            panel,
            boardfont=boardfont,
            ui=ui)
        super(Game, self).__init__(
            panel,
            board,
            tags_variations_comments_font=tags_variations_comments_font,
            moves_played_in_game_font=moves_played_in_game_font,
            gameclass=gameclass,
            ui=ui,
            items_manager=items_manager,
            itemgrid=itemgrid,
            **ka)
        self.scrollbar.grid(column=2, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.analysis = AnalysisScore(
            panel,
            board,
            tags_variations_comments_font=tags_variations_comments_font,
            moves_played_in_game_font=moves_played_in_game_font,
            gameclass=GameAnalysis,
            ui=ui,
            items_manager=items_manager,
            itemgrid=itemgrid,
            **ka)
        self.score.tag_configure(FORCED_INDENT_TAG, lmargin1=20)
        self.score.tag_configure(MOVETEXT_INDENT_TAG, lmargin2=20)
        self.score.tag_configure(
            MOVETEXT_MOVENUMBER_TAG, elide=tkinter.FALSE)
        self.analysis.score.configure(wrap=tkinter.WORD)
        self.analysis.score.tag_configure(ANALYSIS_INDENT_TAG, lmargin2=80)
        self.analysis.score.tag_configure(
            ANALYSIS_PGN_TAGS_TAG, elide=tkinter.TRUE)
        self.analysis.scrollbar.grid(
            column=2, row=1, rowspan=1, sticky=tkinter.NSEW)
        self.board.get_top_widget().grid(
            column=0, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.score.grid(column=1, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.analysis.score.grid(
            column=0, row=1, columnspan=2, sticky=tkinter.NSEW)
        if not ui.show_analysis:
            panel.after_idle(self.hide_game_analysis)
        if not ui.visible_scrollbars:
            panel.after_idle(self.hide_scrollbars)
        self.configure_game_widget()

        # The popup menus specific to Game subclass

        for function, accelerator in (
            (self.analyse_game,
             EventSpec.analyse_game),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.viewmode_popup),
                accelerator=accelerator[2])
        self.viewmode_popup.add_cascade(
            label='Database', menu=self.viewmode_database_popup)
        for function, accelerator in (
            (self.export_archive_pgn,
             EventSpec.export_archive_pgn_from_game),
            (self.export_rav_pgn,
             EventSpec.export_rav_pgn_from_game),
            (self.export_pgn,
             EventSpec.export_pgn_from_game),
            ):
            self.viewmode_database_popup.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.viewmode_database_popup),
                accelerator=accelerator[2])

        # True means analysis widget refers to same position as game widget; so
        # highlighting of analysis still represents future valid navigation.
        # Any navigation in game widget makes any highlighting in analysis
        # widget out of date.
        self.game_position_analysis = False

        self.game_analysis_in_progress = False
        self.takefocus_widget = self.score
        self.analysis_data_source = None
        
    def bind_for_viewmode(self):
        """Set keyboard bindings and popup menu for traversing moves."""
        super(Game, self).bind_for_viewmode()
        self._bind_export(True)

    def bind_for_select_variation_mode(self):
        """Set keyboard bindings and popup menu for selecting a variation."""
        super(Game, self).bind_for_select_variation_mode()
        self._bind_export(False)
        
    def _bind_export(self, switch):
        """Set keyboard bindings for exporting games."""
        ste = self.try_event
        for sequence, function in (
            (EventSpec.export_archive_pgn_from_game,
             self.export_archive_pgn),
            (EventSpec.export_rav_pgn_from_game,
             self.export_rav_pgn),
            (EventSpec.export_pgn_from_game,
             self.export_pgn),
            ):
            self.score.bind(
                sequence[0],
                '' if not switch else '' if not function else ste(function))
        
    def get_top_widget(self):
        """Return topmost widget for game display.

        The topmost widget is put in a container widget in some way
        """
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
        #try:
        #    self.ui.uci.uci.ui_analysis_queue.put(
        #        (self.analysis.score, self.analysis.score))
        #except AttributeError:
        #    if self.ui.uci.uci.uci_drivers_reply is not None:
        #        raise
        self.ui.uci.uci.ui_analysis_queue.put(
            (self.analysis.score, self.analysis.score))
        self.panel.destroy()

    def _on_configure(self, event=None):
        """Catch initial configure and rebind to on_configure."""
        # Not sure, at time of writing this, how partial.py is
        # different but that module does not need this trick to display
        # the control with the right size on creation.
        # Here extra first event has width=1 height=1 followed up by event
        # with required dimensions.
        self.panel.bind('<Configure>', self.try_event(self.on_configure))
        
    def on_configure(self, event=None):
        """Reconfigure board and score after container has been resized."""
        self.configure_game_widget()
        self.see_current_move()
        
    def _analyse_position(self, *position):
        """"""
        pa = self.get_analysis(*position)
        self.refresh_analysis_widget_from_database(pa)
        if self.game_analysis_in_progress:
            if not self.ui.uci.uci.is_positions_pending_empty():
                return
            self.game_analysis_in_progress = False
        pa.variations.clear()

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
        #try:
        #    self.ui.uci.uci.ui_analysis_queue.put((self.analysis.score, pa))
        #except AttributeError:
        #    if self.ui.uci.uci.uci_drivers_reply is not None:
        #        raise
        self.ui.uci.uci.ui_analysis_queue.put((self.analysis.score, pa))
        
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
        
    def set_game(self, starttoken=None, reset_undo=False):
        """Delegate to superclass method and queue analysis request to engines.

        starttoken is the move played to reach the position displayed and this
        move becomes the current move.
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a game for editing so that repeated Ctrl-Z in text
        editing mode recovers the original score.
        
        """
        super().set_game(starttoken=starttoken, reset_undo=reset_undo)
        self.score.tag_add(MOVETEXT_INDENT_TAG, '1.0', tkinter.END)
        self._analyse_position(*self.fen_tag_tuple_square_piece_map())

    def analyse_game(self):
        """Analyse all positions in game using all active engines."""
        uci = self.ui.uci.uci
        sas = self.analysis.score
        sga = self.get_analysis
        self.game_analysis_in_progress = True
        for v in self.tagpositionmap.values():
            pa = sga(*v)
            pa.variations.clear()

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
            #try:
            #    uci.ui_analysis_queue.put((sas, pa))
            #except AttributeError:
            #    if uci.uci_drivers_reply is not None:
            #        raise
            #    break
            uci.ui_analysis_queue.put((sas, pa))

    def export_archive_pgn(self, event=None):
        """Export game as PGN Archive."""
        exporters.export_single_game_as_archive_pgn(
            self.score.get('1.0', tkinter.END),
            self.ui.get_export_filename_for_single_item(
                'Archive Game', pgn=True))

    def export_pgn(self, event=None):
        """Export game as PGN."""
        exporters.export_single_game_as_pgn(
            self.score.get('1.0', tkinter.END),
            self.ui.get_export_filename_for_single_item('Game', pgn=True))

    def export_rav_pgn(self, event=None):
        """Export game as PGN moves and RAVs but excluding commentary."""
        exporters.export_single_game_as_rav_pgn(
            self.score.get('1.0', tkinter.END),
            self.ui.get_export_filename_for_single_item('RAV Game', pgn=True))

    def hide_game_analysis(self):
        """Hide the widgets which show analysis from chess engines."""
        self.analysis.score.grid_remove()
        self.analysis.scrollbar.grid_remove()
        self.score.grid_configure(rowspan=2)
        if self.score.grid_info()['columnspan'] == 1:
            self.scrollbar.grid_configure(rowspan=2)
        self.configure_game_widget()
        self.see_current_move()

    def show_game_analysis(self):
        """Show the widgets which show analysis from chess engines."""
        self.score.grid_configure(rowspan=1)
        if self.score.grid_info()['columnspan'] == 1:
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
        if self.score.grid_info()['rowspan'] == 1:
            self.analysis.score.grid_configure(columnspan=3)
        self.configure_game_widget()
        self.see_current_move()

    def show_scrollbars(self):
        """Show the scrollbars in the game display widgets."""
        self.score.grid_configure(columnspan=1)
        if self.score.grid_info()['rowspan'] == 1:
            self.scrollbar.grid_configure(rowspan=1)
            self.analysis.score.grid_configure(columnspan=2)
            self.analysis.scrollbar.grid_configure()
        else:
            self.scrollbar.grid_configure(rowspan=2)
        self.configure_game_widget()
        self.see_current_move()

    def toggle_analysis_fen(self):
        """Toggle display of FEN in analysis widgets."""
        s = self.analysis.score
        if int(s.tag_cget(ANALYSIS_PGN_TAGS_TAG, 'elide')):
            s.tag_configure(ANALYSIS_PGN_TAGS_TAG, elide=tkinter.FALSE)
        else:
            s.tag_configure(ANALYSIS_PGN_TAGS_TAG, elide=tkinter.TRUE)
        self.see_current_move()

    def toggle_game_move_numbers(self):
        """Toggle display of move numbers in game score widgets."""
        s = self.score
        if int(s.tag_cget(MOVETEXT_MOVENUMBER_TAG, 'elide')):
            s.tag_configure(MOVETEXT_MOVENUMBER_TAG, elide=tkinter.FALSE)
        else:
            s.tag_configure(MOVETEXT_MOVENUMBER_TAG, elide=tkinter.TRUE)
        self.see_current_move()

    def refresh_analysis_widget_from_engine(self, analysis):
        """Refresh game widget with updated chess engine analysis."""
        u = self.ui.uci.uci
        move_played = self.get_move_for_start_of_analysis()
        if analysis.position in u.position_analysis:
            new_text = u.position_analysis[
                analysis.position].translate_analysis_to_pgn(
                    move_played=move_played)
        else:
            new_text = []
            new_text.append(UNKNOWN_RESULT)
            if move_played:
                new_text.insert(0, move_played)
                new_text.insert(0,
                                ''.join(
                                    (START_TAG, TAG_FEN, '"',
                                     analysis.position,
                                     END_TAG.join('"\n'))))
            new_text = ''.join(new_text) 
        a = self.analysis
        if new_text == a.analysis_text:
            return

        # Assume TypeError exception happens because analysis is being shown
        # for a position which is checkmate or stalemate.
        try:
            a.collected_game = next(
                PGN(game_class=a.gameclass
                    ).read_games(new_text))
        except TypeError:
            pass

        # Assume analysis movetext problems occur only if editing moves.
        #if not pgn.is_movetext_valid():
        if not a.collected_game.is_movetext_valid():
            return
        
        a.clear_score()
        a.set_score(new_text)
        try:
            fmog = a.select_first_move_of_game()
        except tkinter.TclError:
            fmog = False
        if fmog:
            sa = a.score
            sa.tag_add(ANALYSIS_INDENT_TAG, sa.tag_ranges(fmog)[0], tkinter.END)
            sa.tag_add(ANALYSIS_PGN_TAGS_TAG, '1.0', sa.tag_ranges(fmog)[0])

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
                self.get_move_for_start_of_analysis())
        except TypeError:
            new_text == self.analysis_text

        a = self.analysis
        if new_text == a.analysis_text:
            return

        # Assume TypeError exception happens because analysis is being shown
        # for a position which is checkmate or stalemate.
        try:
            a.collected_game = next(
                PGN(game_class=a.gameclass
                    ).read_games(new_text))
        except TypeError:
            pass
        
        a.clear_score()
        a.set_score(new_text)
        try:
            fmog = a.select_first_move_of_game()
        except tkinter.TclError:
            fmog = False
        if fmog:
            sa = a.score
            sa.tag_add(ANALYSIS_INDENT_TAG, sa.tag_ranges(fmog)[0], tkinter.END)
            sa.tag_add(ANALYSIS_PGN_TAGS_TAG, '1.0', sa.tag_ranges(fmog)[0])

    def refresh_analysis_widget(self, analysis):
        """Refresh game widget with new chess engine analysis."""

        # This method called at regular intervals to cope with fresh analysis
        # of displayed positions due to changes in engine parameters (depth
        # and multiPV). Need a set of new analysis since last call.
        self.refresh_analysis_widget_from_database(analysis)
        
    def configure_game_widget(self):
        """Configure board and score widgets for a game display."""
        cw = self.panel.winfo_width()
        ch = self.panel.winfo_height()
        bd = self.panel.cget('borderwidth')
        if self.ui.show_analysis:
            a = (ch - bd * 2) // 2
            b = cw - a
        else:
            a = ch - bd * 2
            b = cw - bd * 2
            x = (a + b) // 3
            if x * 3 > b * 2:
                x = (b * 2) // 3
            elif x > a:
                x = a
            a = a - x
            b = b - x
        self.panel.grid_rowconfigure(1, minsize=a)
        self.panel.grid_columnconfigure(1, minsize=b)
        self.panel.grid_rowconfigure(0, weight=1)
        self.panel.grid_rowconfigure(1, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_columnconfigure(1, weight=1)
        self.panel.grid_columnconfigure(2, weight=0)

    def bind_board_pointer_for_board_navigation(self, switch):
        """Enable or disable bindings for game navigation."""
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', self.try_event(self._spil)),
            ('<ButtonPress-3>', self.try_event(self._sniv)),
            ):
            for s in self.board.boardsquares.values():
                s.bind(sequence, '' if not switch else function)

    def _spil(self, event=None):
        if self.takefocus_widget is self.analysis.score:
            return self.analysis.show_prev_in_line(event=event)
        else:
            return self.show_prev_in_line(event=event)

    def _sniv(self, event=None):
        if self.takefocus_widget is self.analysis.score:
            return self.analysis.show_next_in_variation(event=event)
        else:
            return self.show_next_in_variation(event=event)

    def bind_board_pointer_for_widget_navigation(self, switch):
        """Enable or disable bindings for widget selection."""
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', self.try_event(self.give_focus_to_widget)),
            ('<ButtonPress-3>', self.try_event(self.popup_inactive_menu)),
            ):
            for s in self.board.boardsquares.values():
                s.bind(sequence, '' if not switch else function)

    def bind_score_pointer_for_widget_navigation(self, switch):
        """Set or unset pointer bindings for widget navigation."""
        if not switch:
            p1score = ''
            p1analysis = ''
            p3score = ''
            p3analysis = ''
        else:
            if self is not self.items.active_item:
                p1score = self.try_event(self.give_focus_to_widget)
                p1analysis = p1score
                p3score = self.try_event(self.popup_inactive_menu)
                p3analysis = self.try_event(self.analysis.popup_inactive_menu)
            elif self.score is self.takefocus_widget:
                p1score = self.try_event(self.give_focus_to_widget)
                p1analysis = p1score
                p3score = self.try_event(self.popup_viewmode_menu)
                p3analysis = self.try_event(self.analysis.popup_inactive_menu)
            else:
                p1score = self.try_event(self.give_focus_to_widget)
                p1analysis = p1score
                p3score = self.try_event(self.popup_inactive_menu)
                p3analysis = self.try_event(self.analysis.popup_viewmode_menu)
        for sequence, function, widget in (
            ('<Control-ButtonPress-1>', '', self.score),
            ('<ButtonPress-1>', p1score, self.score),
            ('<ButtonPress-3>', p3score, self.score),
            ('<Control-ButtonPress-1>', '', self.analysis.score),
            ('<ButtonPress-1>', p1analysis, self.analysis.score),
            ('<ButtonPress-3>', p3analysis, self.analysis.score),
            ):
            widget.bind(sequence, function)

    def set_colours(self, sbg, bbg, bfg):
        """Set colours and fonts used to display games.

        sbg == True - set game score colours
        bbg == True - set board square colours
        bfg == True - set board piece colours

        """
        if sbg:
            for w in self, self.analysis:
                w.score.tag_configure('l_color', background=w.l_color)
                w.score.tag_configure('m_color', background=w.m_color)
                w.score.tag_configure('am_color', background=w.am_color)
                w.score.tag_configure('v_color', background=w.v_color)
        if bbg:
            self.board.set_color_scheme()
        if bfg:
            self.board.draw_board()

    def bind_score_pointer_for_toggle_game_analysis(self, switch):
        """Set or unset pointer bindings for widget navigation."""
        for sequence, function, widget in (
            ('<Control-ButtonPress-1>', self.current_item, self.score),
            ('<Control-ButtonPress-1>',
             self.analysis_current_item, self.analysis.score),
            ):
            widget.bind(sequence, '' if not switch else function)

    def set_position_analysis_data_source(self):
        """Attach database analysis for position to game widget."""
        if self.ui is None:
            self.analysis_data_source = None
            return
        self.analysis_data_source = self.ui.make_position_analysis_data_source()
        
    def get_analysis(self, *a):
        """Return database analysis for position or empty position Analysis."""
        if self.analysis_data_source:
            return self.analysis_data_source.get_position_analysis(
                self.generate_fen_for_position(*a))
        else:
            return Analysis(position=self.generate_fen_for_position(*a))

    @staticmethod
    def generate_fen_for_position(squares, *a):
        for s, p in squares.items():
            p.set_square(s)
        return generate_fen_for_position(squares.values(), *a)


class Repertoire(Game):

    """Chess repertoire game widget composed from Board and Text widgets.
    """
    # Override methods referring to Seven Tag Roster

    tags_displayed_last = REPERTOIRE_GAME_TAGS

    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend to display repertoire game.

        gameclass - Game subclass for data structure created by PGN class

        """
        super(Repertoire, self).__init__(gameclass=gameclass, **ka)
        self.viewmode_database_popup.delete(
            EventSpec.export_archive_pgn_from_game[1])
        
    def bind_for_viewmode(self):
        """Set keyboard bindings and popup menu for traversing moves."""
        super(Repertoire, self).bind_for_viewmode()
        for sequence, function in (
            (EventSpec.export_archive_pgn_from_game, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def export_pgn(self, event=None):
        """Export repertoire as PGN."""
        exporters.export_single_repertoire_as_pgn(
            self.score.get('1.0', tkinter.END),
            self.ui.get_export_filename_for_single_item('Repertoire', pgn=True))

    def export_rav_pgn(self, event=None):
        """Export repertoire as PGN moves and RAVs but excluding commentary."""
        exporters.export_single_repertoire_as_rav_pgn(
            self.score.get('1.0', tkinter.END),
            self.ui.get_export_filename_for_single_item(
                'RAV Repertoire', pgn=True))

