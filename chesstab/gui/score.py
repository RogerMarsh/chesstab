# score.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display the score of a game of chess.

The Score class displays text derived from PGN and highlights moves depending
on the current position while navigating the game score.

The current position is put on the instance's board.Board widget.

Score is a superclass of game.Game and instances of game.Game have a separate
Score instance as an attribute so chess engine analysis for the current position
in the score can be shown.  The Game instance uses the same board.Board instance
for it's two instances of Score.  Repertoires are similar because game.Game is
a superclass of game.Repertoire.

"""
# Not sure what to call this yet.
# It is meant to be the text part of the Game class, pre-uci analysis, so
# the game score and the analysis score can share the board in a Game
# instance.  Given cg = Game(...) both cg and cg.analysis are Score
# instances and cg.score and cg.analysis.score are the Text instances rather
# than the old cg.score Text instance.

# The following note is copied from the top of the game module.  Score is
# not the 'more basic class' implied in the note.

# Game (game.py) and Partial (partial.py) should be
# subclasses of some more basic class.  They are not because Game started
# as a game displayer while Partial started as a Text widget with no
# validation and they have been converging ever since.  Next step will get
# there.  Obviously this applies to subclasses GameEdit (gameedit.py)
# and PartialEdit (partialedit.py) as well.

import tkinter

from pgn_read.core.constants import (
    TAG_FEN,
    SEVEN_TAG_ROSTER,
    FEN_WHITE_ACTIVE,
    PGN_DOT,
    )
from pgn_read.core.squares import Squares

from ..core.pgn import GameDisplayMoves
from .chessexception import ChessException
from .constants import (
    LINE_COLOR,
    MOVE_COLOR,
    ALTERNATIVE_MOVE_COLOR,
    VARIATION_COLOR,
    MOVES_PLAYED_IN_GAME_FONT,
    TAGS_VARIATIONS_COMMENTS_FONT,
    NAVIGATE_TOKEN,
    NAVIGATE_MOVE,
    INSERT_RAV,
    MOVE_EDITED,
    TOKEN,
    RAV_MOVES,
    CHOICE,
    PRIOR_MOVE,
    RAV_SEP,
    RAV_TAG,
    ALL_CHOICES,
    POSITION,
    MOVE_TAG,
    SELECTION,
    ALTERNATIVE_MOVE_TAG,
    LINE_TAG,
    VARIATION_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    NAVIGATE_COMMENT,
    TOKEN_MARK,
    INSERT_TOKEN_MARK,
    PGN_TAG,
    BUILD_TAG,
    TERMINATION_TAG,
    SPACE_SEP,
    NEWLINE_SEP,
    NULL_SEP,
    STATUS_SEVEN_TAG_ROSTER_PLAYERS,
    FORCE_NEWLINE_AFTER_FULLMOVES,
    FORCED_INDENT_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    )
from .eventspec import EventSpec
from .displayitems import DisplayItemsStub
from ..core.pgn import get_position_string


class Score(ChessException):

    """Chess score widget composed from Text and Scrollbar widgets.
    """

    l_color = LINE_COLOR
    m_color = MOVE_COLOR
    am_color = ALTERNATIVE_MOVE_COLOR
    v_color = VARIATION_COLOR
    tags_variations_comments_font = TAGS_VARIATIONS_COMMENTS_FONT
    moves_played_in_game_font = MOVES_PLAYED_IN_GAME_FONT

    # True means game score can be edited
    _is_score_editable = False

    tags_displayed_last = SEVEN_TAG_ROSTER

    def __init__(
        self,
        panel,
        board,
        tags_variations_comments_font=None,
        moves_played_in_game_font=None,
        gameclass=GameDisplayMoves,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Extend with widgets to display game score.

        tags_variations_comments_font - font for tags variations and comments
        moves_played_in_game_font - font for move played in game
        gameclass - Game subclass for data structure created by PGN class
        ui - the container for game list and game display widgets.

        Create Frame in toplevel and add Canvas and Text.
        Text width and height set to zero so widget fit itself into whatever
        space Frame has available.
        Canvas must be square leaving Text at least half the Frame.

        """
        super(Score, self).__init__(**ka)
        self.ui = ui

        # May be worth using a Null() instance for these two attributes.
        if items_manager is None:
            items_manager = DisplayItemsStub()
        self.items = items_manager
        self.itemgrid = itemgrid
        
        if tags_variations_comments_font:
            self.tags_variations_comments_font = tags_variations_comments_font
        if moves_played_in_game_font:
            self.moves_played_in_game_font = moves_played_in_game_font
        self.panel = panel
        self.board = board
        self.score = tkinter.Text(
            self.panel,
            width=0,
            height=0,
            takefocus=tkinter.FALSE,
            font=self.tags_variations_comments_font,
            undo=True,
            wrap=tkinter.WORD)
        self.score.tag_configure(
            MOVES_PLAYED_IN_GAME_FONT, font=self.moves_played_in_game_font)

        # Order is ALTERNATIVE_MOVE_TAG LINE_TAG VARIATION_TAG LINE_END_TAG
        # MOVE_TAG so that correct colour has highest priority as moves are
        # added to and removed from tags.
        self.score.tag_configure(ALTERNATIVE_MOVE_TAG, background=self.am_color)
        self.score.tag_configure(LINE_TAG, background=self.l_color)
        self.score.tag_configure(VARIATION_TAG, background=self.v_color)
        self.score.tag_configure(
            LINE_END_TAG, background=self.score.cget('background'))
        self.score.tag_configure(MOVE_TAG, background=self.m_color)

        self.scrollbar = tkinter.Scrollbar(
            master=self.panel,
            orient=tkinter.VERTICAL,
            takefocus=tkinter.FALSE,
            command=self.score.yview)
        self.score.configure(yscrollcommand=self.scrollbar.set)

        # Keyboard actions do nothing by default.
        self.score.bind(EventSpec.score_disable_keypress[0],
                        lambda e: 'break')

        # The popup menus for the game score

        self.viewmode_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.viewmode_database_popup = tkinter.Menu(
            master=self.viewmode_popup, tearoff=False)
        for function, accelerator in (
            (self.show_next_in_line,
             EventSpec.score_show_next_in_line),
            (self.show_next_in_variation,
             EventSpec.score_show_next_in_variation),
            (self.show_prev_in_line,
             EventSpec.score_show_previous_in_line),
            (self.show_prev_in_variation,
             EventSpec.score_show_previous_in_variation),
            (self.show_first_in_game,
             EventSpec.score_show_first_in_game),
            (self.show_last_in_game,
             EventSpec.score_show_last_in_game),
            (self.show_first_in_line,
             EventSpec.score_show_first_in_line),
            (self.show_last_in_line,
             EventSpec.score_show_last_in_line),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        self.selectmode_popup = tkinter.Menu(
            master=self.score, tearoff=False)
        for function, accelerator in (
            (self.variation_cycle,
             EventSpec.score_cycle_selection_to_next_variation),
            (self.show_variation,
             EventSpec.score_show_selected_variation),
            (self.variation_cancel,
             EventSpec.score_cancel_selection_of_variation),
            ):
            self.selectmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.selectmode_popup),
                accelerator=accelerator[2])
        self.inactive_popup = None
        self.viewmode_navigation_popup = None

        # None implies initial position and is deliberately not a valid Tk tag.
        self.current = None # Tk tag of current move

        # These attributes replace the structure used with wxWidgets controls.
        # Record the structure by tagging text in the Tk Text widget.
        self.rav_number = 0
        self.varstack = []
        self.choice_number = 0
        self.choicestack = []
        self.position_number = 0
        self.tagpositionmap = dict()
        self.previousmovetags = dict()
        self.nextmovetags = dict()

        # PGN parser creates a gameclass instance for game data structure and
        # binds it to collected_game attribute.
        self.gameclass = gameclass
        self.collected_game = None

        # Used to force a newline before a white move in large games after a
        # after FORCE_NEWLINE_AFTER_FULLMOVES black moves have been added to
        # a line.
        # map_game uses self._force_newline as a fullmove number clock which
        # is reset after comments, the start or end of recursive annotation
        # variations, escaped lines '\n%...\n', and reserved '<...>'
        # sequences.  In each case a newline is added before the next token.
        # The AnalysisScore subclass makes its own arrangements because the
        # Score technique does not work, forced newlines are not needed, and
        # only the first move gets numbered.
        self._force_newline = False

    def add_navigation_to_viewmode_popup(self, **kwargs):
        '''Add 'Navigation' entry to movemode popup if not already present.'''

        # Cannot see a way of asking 'Does entry exist?' other than:
        try:
            self.viewmode_popup.index('Navigation')
        except:
            self.viewmode_navigation_popup = tkinter.Menu(
                master=self.viewmode_popup, tearoff=False)
            self.viewmode_popup.add_cascade(
                label='Navigation', menu=self.viewmode_navigation_popup)
            self.bind_navigation_for_viewmode_popup(**kwargs)
        
    def bind_for_viewmode(self):
        """Set keyboard bindings and popup menu for traversing moves."""
        self._bind_select_variation(False)
        self._bind_viewmode(True)

    def bind_for_select_variation_mode(self):
        """Set keyboard bindings and popup menu for selecting a variation."""
        self._bind_viewmode(False)
        self._bind_select_variation(True)
        
    def _bind_viewmode(self, switch):
        """Set keyboard bindings for traversing moves."""
        ste = self.try_event
        for sequence, function in (
            (EventSpec.score_show_previous_in_variation,
             self.show_prev_in_variation),
            (EventSpec.score_show_previous_in_line,
             self.show_prev_in_line),
            (EventSpec.score_show_next_in_line,
             self.show_next_in_line),
            (EventSpec.score_show_next_in_variation,
             self.show_next_in_variation),
            (EventSpec.score_show_first_in_line,
             self.show_first_in_line),
            (EventSpec.score_show_last_in_line,
             self.show_last_in_line),
            (EventSpec.score_show_first_in_game,
             self.show_first_in_game),
            (EventSpec.score_show_last_in_game,
             self.show_last_in_game),
            ):
            self.score.bind(
                sequence[0],
                '' if not switch else '' if not function else ste(function))

    def _bind_select_variation(self, switch):
        """Set keyboard bindings for selecting a variation."""
        ste = self.try_event
        for sequence, function in (
            (EventSpec.score_cancel_selection_of_variation,
             self.variation_cancel),
            (EventSpec.score_show_selected_variation,
             self.show_variation),
            (EventSpec.score_cycle_selection_to_next_variation,
             self.variation_cycle),
            ):
            self.score.bind(
                sequence[0],
                '' if not switch else '' if not function else ste(function))

    def bind_score_pointer_for_board_navigation(self, switch):
        """Set or unset pointer bindings for game navigation."""
        ste = self.try_event
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', ste(self.go_to_token)),
            ('<ButtonPress-3>', ste(self.popup_viewmode_menu)),
            ):
            self.score.bind(sequence, '' if not switch else function)

    def bind_navigation_for_viewmode_popup(self, bindings=None, order=None):
        """Set popup bindings for toplevel navigation."""
        if order is None:
            order = ()
        if bindings is None:
            bindings = {}
        for label, accelerator in order:
            function = bindings.get(label)
            if function is not None:
                self.viewmode_navigation_popup.add_command(
                    label=label,
                    command=self.try_command(
                        function, self.viewmode_navigation_popup),
                    accelerator=accelerator)

    def colour_variation(self):
        """Colour variation and display its initial position.

        The current move is coloured to indicate it is a move played to reach
        the position in the variation.  Colour is removed from any moves to
        enter alternative variations.  The move played to enter the variation
        becomes the current move and is coloured to indicate that it is in a
        variation.

        """
        if self.current is None:

            # No prior to variation tag exists: no move to attach it to.
            pt = None
            ct = self.get_choice_tag_of_move(self.select_first_move_of_game())
            st = self.get_selection_tag_for_choice(ct)

        else:
            pt = self.get_prior_to_variation_tag_of_move(self.current)
            ct = self.get_choice_tag_for_prior(pt)
            st = self.get_selection_tag_for_prior(pt)
        self.clear_variation_choice_colouring_tag(ct)
        selected_first_move = self.select_first_move_of_selected_line(st)
        if self.is_move_in_main_line(selected_first_move):
            self.clear_moves_played_in_variation_colouring_tag()
            self.clear_variation_colouring_tag()
        elif self.current is None:
            self.set_next_variation_move_played_colouring_tag(st)
        else:
            self.add_move_to_moves_played_colouring_tag(self.current)
        self.current = selected_first_move
        self.set_current()
        self.set_game_board()

    def give_focus_to_widget(self, event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return 'break'

    def is_game_in_text_edit_mode(self):
        """Return True if current state of score widget is 'normal'."""
        return self.score.cget('state') == tkinter.NORMAL
        
    def see_first_move(self):
        """Make first move visible on navigation to initial position.

        Current move is always made visible but no current move defined
        for initial position.
        """
        self.score.see(START_SCORE_MARK)
        
    def see_current_move(self):
        """Make current move visible and default to first move"""
        if self.current:
            self.score.see(self.score.tag_ranges(self.current)[0])
        else:
            self.see_first_move()
        
    def fen_tag_square_piece_map(self):
        """Return square to piece mapping for position in game's FEN tag.

        The position was assumed to be the standard initial position of a game
        if there was no FEN tag.

        """
        return {s: p for p, s in  self.collected_game._initial_position[0]}
        
    def fen_tag_tuple_square_piece_map(self):
        """Return FEN tag as tuple with pieces in square to piece mapping."""
        ip = self.collected_game._initial_position
        return (self.fen_tag_square_piece_map(),
                ip[1], ip[2], ip[3], ip[4], ip[5])
        
    def set_game_board(self):
        """Show position after highlighted move and return True if it exists.

        True means further processing appropriate to a game score can be done,
        while None means a problem occurred and the first position in score
        is displayed as a default.

        The setup_game_board() in AnalysisScore always returns False.

        """
        if self.current is None:
            self.board.set_board(self.fen_tag_square_piece_map())
            self.see_first_move()
        else:
            try:
                self.board.set_board(self.tagpositionmap[self.current][0])
            except TypeError:
                self.board.set_board(self.fen_tag_square_piece_map())
                self.score.see(self.score.tag_ranges(self.current)[0])
                return
            self.score.see(self.score.tag_ranges(self.current)[0])
        self.set_game_list()
        return True
        
    def set_game(self, starttoken=None, reset_undo=False):
        """Display the game as board and moves.

        starttoken is the move played to reach the position displayed and this
        move becomes the current move.
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a game for editing so that repeated Ctrl-Z in text
        editing mode recovers the original score.
        
        """
        if not self._is_score_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_game()
        self.bind_for_viewmode()
        if not self._is_score_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()
        self.board.set_board(self.fen_tag_square_piece_map())
        
    def show_first_in_game(self, event=None):
        """Display initial position of game score (usually start of game)."""
        return self.show_new_current(new_current=None)
        
    def show_first_in_line(self, event=None):
        """Display initial position of line containing current move."""
        if self.current is None:
            return 'break'
        if self.is_currentmove_in_main_line():
            return self.show_first_in_game()
        selected_first_move = self.select_first_move_in_line(self.current)
        self.current = selected_first_move
        self.set_current()
        self.set_variation_tags_from_currentmove()
        self.set_game_board()
        return 'break'

    def show_variation(self, event=None):
        """Enter selected variation and display its initial position."""
        self.bind_for_viewmode()
        self.colour_variation()
        return 'break'
        
    def show_last_in_game(self, event=None):
        """Display final position of game score."""
        return self.show_new_current(
            new_current=self.select_last_move_played_in_game())

    def show_last_in_line(self, event=None):
        """Display final position of line containing current move."""
        if self.current is None:
            return self.show_last_in_game()
        if self.is_currentmove_in_main_line():
            return self.show_last_in_game()
        self.current = self.select_last_move_in_line()
        self.add_variation_before_move_to_colouring_tag(self.current)
        self.set_current()
        self.set_game_board()
        return 'break'
        
    def show_next_in_line(self, event=None):
        """Display next position of selected line."""
        if self.current is None:
            self.current = self.select_first_move_of_game()
        else:
            if self.is_variation_entered():
                self.add_move_to_moves_played_colouring_tag(self.current)
            self.current = self.select_next_move_in_line()
        self.set_current()
        self.set_game_board()
        return 'break'

    def show_next_in_variation(self, event=None):
        """Display choices if these exist or next position of selected line."""
        if self.current is None:

            # No prior to variation tag exists: no move to attach it to.
            pt = None
            ct = self.get_choice_tag_of_move(self.select_first_move_of_game())
            if ct is None:
                return self.show_next_in_line()
            st = self.get_selection_tag_for_choice(ct)

        else:
            pt = self.get_prior_to_variation_tag_of_move(self.current)
            if pt is None:
                return self.show_next_in_line()
            ct = self.get_choice_tag_for_prior(pt)
            st = self.get_selection_tag_for_prior(pt)

        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self.cycle_selection_tag(ct, st)

        vt = self.get_colouring_variation_tag_for_selection(st)
        self.set_variation_selection_tags(pt, ct, st, vt)
        self.bind_for_select_variation_mode()
        return 'break'
        
    def show_prev_in_line(self, event=None):
        """Display previous position of selected line."""
        if self.current is None:
            return 'break'
        if not self.is_currentmove_in_main_line():
            self.remove_currentmove_from_moves_played_in_variation()
        self.current = self.select_prev_move_in_line()
        self.set_current()
        self.set_game_board()
        return 'break'
        
    def show_prev_in_variation(self, event=None):
        """Display choices in previous position of selected line."""
        if self.current is None:
            return 'break'
        if not self.is_currentmove_in_main_line():
            self.remove_currentmove_from_moves_played_in_variation()
            if self.is_currentmove_start_of_variation():
                self.clear_variation_colouring_tag()
                self.current = self.get_position_tag_of_previous_move()
                self.set_current()
                self.set_game_board()
                if self.current is None:
                    self.clear_moves_played_in_variation_colouring_tag()
                elif self.get_prior_to_variation_tag_of_move(
                    self.current) is None:
                    return 'break'
                self.bind_for_select_variation_mode()
                self.variation_cycle()
                return 'break'
        self.current = self.select_prev_move_in_line()
        self.set_current()
        self.set_game_board()
        return 'break'

    def step_one_variation(self, move):
        """Highlight next variation in choices at current position."""
        if move is None:

            # No prior to variation tag exists: no move to attach it to.
            pt = None
            ct = self.get_choice_tag_of_move(self.select_first_move_of_game())
            st = self.get_selection_tag_for_choice(ct)

        else:
            pt = self.get_prior_to_variation_tag_of_move(move)
            ct = self.get_choice_tag_for_prior(pt)
            st = self.get_selection_tag_for_prior(pt)

        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self.cycle_selection_tag(ct, st)

        vt = self.get_colouring_variation_tag_for_selection(st)
        self.set_variation_selection_tags(pt, ct, st, vt)
        return vt
        
    def variation_cancel(self, event=None):
        """Remove all variation highlighting."""
        if self.current is None:

            # No prior to variation tag exists: no move to attach it to.
            pt = None
            ct = self.get_choice_tag_of_move(self.select_first_move_of_game())
            st = self.get_selection_tag_for_choice(ct)

        else:
            pt = self.get_prior_to_variation_tag_of_move(self.current)
            ct = self.get_choice_tag_for_prior(pt)
            st = self.get_selection_tag_for_prior(pt)
        self.clear_variation_choice_colouring_tag(ct)
        self.clear_variation_colouring_tag()
        if self.current is not None:
            if not self.is_currentmove_in_main_line():
                self.add_currentmove_variation_to_colouring_tag()
        self.bind_for_viewmode()
        return 'break'
        
    def variation_cycle(self, event=None):
        """Highlight next variation in choices at current position."""
        self.step_one_variation(self.current)
        return 'break'

    def add_move_to_moves_played_colouring_tag(self, move):
        """Add move to colouring tag for moves played in variation."""
        widget = self.score
        tr = widget.tag_nextrange(move, '1.0')
        widget.tag_add(VARIATION_TAG, tr[0], tr[1])

    def add_currentmove_variation_to_colouring_tag(self):
        """Add current move variation to selected variation colouring tag."""
        widget = self.score
        for tn in widget.tag_names(
            widget.tag_nextrange(self.current, '1.0')[0]):
            if tn.startswith(RAV_SEP):
                self._add_tag_ranges_to_color_tag(tn, LINE_TAG)
                widget.tag_add(
                    LINE_END_TAG,
                    ''.join((
                        str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                        '-1 chars')))
                return

    def add_pgntag_to_map(self, name, value):
        """Add a PGN Tag, a name and value, to the game score.

        The PGN Tag consists of two editable tokens: the Tag name and the Tag
        value.  These are inserted and deleted together, never separately,
        formatted as [ <name> "<value>" ]\n.

        """
        widget = self.score
        widget.insert(tkinter.INSERT, '[')
        name_tag = self.add_text_pgntag_or_pgnvalue(
            ''.join((' ', name)),
            tagset=(TAGS_VARIATIONS_COMMENTS_FONT,),
            )
        name_suffix = self.position_number
        value_tag = self.add_text_pgntag_or_pgnvalue(
            ''.join(('"', value)),
            tagset=(TAGS_VARIATIONS_COMMENTS_FONT,),
            separator='"')
        value_suffix = self.position_number
        widget.insert(tkinter.INSERT, ' ]\n')
        widget.mark_set(START_SCORE_MARK, tkinter.INSERT)
        return ((name_suffix, name_tag), (value_suffix, value_tag))

    def add_text_pgntag_or_pgnvalue(self, token, separator=' ', **k):
        """Insert token and separator text. Return start and end indicies.

        token is ' 'text or '"'text.  The trailing ' ' or '"' required in the
        PGN specification is provided as separator.  The markers surrounding
        text are not editable.

        """
        return self.insert_token_into_text(token, separator)

    def add_variation_before_move_to_colouring_tag(self, move):
        """Add variation before current move to moves played colouring tag."""
        widget = self.score
        index = widget.tag_nextrange(move, '1.0')[0]
        for ctn in widget.tag_names(index):
            if ctn.startswith(RAV_MOVES):
                tr = widget.tag_nextrange(ctn, '1.0', index)
                while tr:
                    widget.tag_add(VARIATION_TAG, tr[0], tr[1])
                    tr = widget.tag_nextrange(ctn, tr[1], index)
                return

    def build_nextmovetags(self):
        """"""
        widget = self.score
        navigatemove = widget.tag_ranges(NAVIGATE_MOVE)
        for this, v in self.previousmovetags.items():
            if widget.tag_nextrange(NAVIGATE_MOVE, *widget.tag_ranges(this)):
                previous, thisrav, previousrav = v
                nmt = self.nextmovetags.setdefault(previous, [None, []])
                if thisrav == previousrav:
                    nmt[0] = this
                else:
                    nmt[1].append(this)

    def clear_current_range(self):
        """Remove existing MOVE_TAG ranges."""
        tr = self.score.tag_ranges(MOVE_TAG)
        if tr:
            self.score.tag_remove(MOVE_TAG, tr[0], tr[1])

    def clear_moves_played_in_variation_colouring_tag(self):
        """Clear the colouring tag for moves played in variation."""
        self.score.tag_remove(VARIATION_TAG, '1.0', tkinter.END)

    def clear_choice_colouring_tag(self):
        """Clear the colouring tag for variation choice."""
        self.score.tag_remove(ALTERNATIVE_MOVE_TAG, '1.0', tkinter.END)

    def clear_variation_choice_colouring_tag(
        self,
        first_moves_in_variations):
        """Remove ranges in first_moves_in_variations from colour tag.

        The colour tag is ALTERNATIVE_MOVE_TAG which should contain just the
        ranges that exist in first_moves_in_variation.  However do what the
        headline says rather than delete everything in an attempt to ensure
        correctness.

        """
        self._remove_tag_ranges_from_color_tag(
            first_moves_in_variations,
            ALTERNATIVE_MOVE_TAG)

    def clear_variation_colouring_tag(self):
        """Clear the colouring tag for moves in variation."""
        self.score.tag_remove(LINE_TAG, '1.0', tkinter.END)
        self.score.tag_remove(LINE_END_TAG, '1.0', tkinter.END)

    def create_previousmovetag(self, positiontag, start):
        """"""

        # Add code similar to this which sets up self.previousmovetags a method
        # of same name in positionscore.py to link prev-current-next positions.
        # Use these positions as starting point for colouring tags in score
        # displayed by positionscore.py

        widget = self.score
        tr = widget.tag_prevrange(self._vartag, start)
        if tr:
            self.previousmovetags[positiontag] = (
                self.get_position_tag_of_index(tr[0]),
                self._vartag,
                self._vartag)
        else:
            varstack = list(self.varstack)
            while varstack:
                var = varstack.pop()[0]
                tr = widget.tag_prevrange(
                    var, widget.tag_prevrange(var, start)[0])
                if tr:
                    self.previousmovetags[positiontag] = (
                        self.get_position_tag_of_index(tr[0]),
                        self._vartag,
                        var)
                    break
            else:
                if self._vartag is self._gamevartag:
                    self.previousmovetags[positiontag] = (None, None, None)
                else:
                    self.previousmovetags[positiontag] = (None, False, None)

    def cycle_selection_tag(self, choice, selection):
        """Cycle selection one range round the choice ranges if coloured.

        The choice ranges are coloured if they are on ALTERNATIVE_MOVE_TAG.

        """
        if choice is None:
            return
        if selection is None:
            return
        widget = self.score
        cr = widget.tag_nextrange(choice, '1.0')
        if not cr:
            return
        if not widget.tag_nextrange(ALTERNATIVE_MOVE_TAG, cr[0]):
            return
        sr = widget.tag_nextrange(
            choice,
            widget.tag_nextrange(selection, '1.0')[1])
        widget.tag_remove(selection, '1.0', tkinter.END)
        if sr:
            widget.tag_add(selection, sr[0], sr[1])
        else:
            widget.tag_add(selection, cr[0], cr[1])

    def get_choice_tag_of_index(self, index):
        """Return Tk tag name if index is in a choice tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(CHOICE):
                return tn
        return None

    def get_range_for_prior_move_before_insert(self):
        """Return range for move token preceding INSERT to be prior move.

        The prior move is the one played to reach the current position at the
        insertion point.  For RAV start and end markers it is the move before
        the move preceding the start of the RAV.  The nearest move to a move
        is itself.

        """
        # This algorithm is intended for use when building the Text widget
        # content from a PGN score.  INSERT is assumed to be at END and the
        # BUILD_TAG tag to still exist tagging the tokens relevant to the
        # search. 
        skip_move_before_rav = True
        widget = self.score
        r = widget.tag_prevrange(BUILD_TAG, widget.index(tkinter.INSERT))
        while r:
            wtn = widget.tag_names(r[0])
            for tn in wtn:
                if tn.startswith(RAV_MOVES):
                    if skip_move_before_rav:
                        skip_move_before_rav = False
                        start_search = r[0]
                        break
                    for pn in wtn:
                        if pn.startswith(POSITION):
                            return r
                    return None
                if tn.startswith(RAV_TAG):
                    start_search = widget.tag_ranges(tn)[0]
                    skip_move_before_rav = True
                    break
            else:
                start_search = r[0]
            r = widget.tag_prevrange(BUILD_TAG, start_search)
            if not r:
                return None

    def get_range_next_move_in_variation(self):
        """Return range of move after current move in variation."""
        if self.current is None:
            tnr = self.score.tag_nextrange(NAVIGATE_MOVE, '1.0')
            if tnr:
                return tnr
            return None
        return self._get_range_next_move_in_variation()

    def get_current_move_context(self):
        """Return the previous current and next positions in line.

        Alternative next moves in sub-variations are not included.

        """
        # This method gets called once for each game listed in the games
        # containing the current position.  An alternative is to pass these
        # values in the 'set partial key' route for the the grid which is
        # one call.
        try:
            prevpos = self.tagpositionmap[
                self.previousmovetags[self.current][0]]
        except KeyError:

            # The result at the end of an editable game score for example
            prevpos = None

        currpos = self.tagpositionmap[self.current]
        np = self.nextmovetags.get(self.current)
        if np is None:
            nextpos = None
        else:
            try:
                nextpos = self.tagpositionmap[np[0]]
            except KeyError:
                nextpos = None
        return (prevpos, currpos, nextpos)

    def get_position_for_current(self):
        """Return position associated with the current range."""
        if self.current is None:
            return self.tagpositionmap[None]
        return self.get_position_for_text_index(
            self.score.tag_ranges(self.current)[0])

    def get_position_for_text_index(self, index):
        """Return position associated with index in game score text widget."""
        tagpositionmap = self.tagpositionmap
        for tag in self.score.tag_names(index):
            if tag in tagpositionmap:
                return tagpositionmap[tag]

    def get_position_key(self):
        """Return position key string for position associated with current."""
        try:

            # Hack.  get_position_for_current returns None on next/prev token
            # navigation at end of imported game with errors when editing.
            return get_position_string(*self.get_position_for_current())

        except:
            return False

    def get_position_tag_of_index(self, index):
        """Return Tk tag name if index is in a position tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(POSITION):
                return tn
        return None

    def get_prior_to_variation_tag_of_index(self, index):
        """Return Tk tag name if index is in a prior to variation tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(PRIOR_MOVE):
                return tn
        return None

    def get_tags_display_order(self):
        """Return tags in alphabetic order modified by self.tags_displayed_last.

        last=None means do not display the tags: assume tags will be displayed
        in the order they appear in the PGN text.

        Return None if last is None, and list of '(tag, value)'s otherwise.

        last modifies the order PGN tags are displayed.  Normally the Seven
        Tag Roster appears first in a PGN game score followed by other tags
        in alphabetic order.  Tags not in last are displayed in alphabetic
        order followed by the tags in last.  If last is None the PGN tags are
        displayed in the order they appear in the PGN game score.

        The intention is to display the important tags adjacent to the game
        score.  Thus if last is the Seven Tag Roster these tags are displayed
        after the other tags, rather than appearing before the other tags as
        in a PGN file.
        """
        last = self.tags_displayed_last
        if last is None:
            return None
        tag_values = []
        tags = self.collected_game._tags
        for tv in sorted(tags.items()):
            if tv[0] not in last:
                tag_values.append(tv)
        for t in last:
            if t in tags:
                tag_values.append((t, tags[t]))
        return tag_values
    
    def get_colouring_variation_tag_of_index(self, index):
        """Return Tk tag name if index is in a varsep tag.

        RAV_SEP for colouring (RAV_MOVES for editing).

        """
        for tn in self.score.tag_names(index):
            if tn.startswith(RAV_SEP):
                return tn
        return None

    def get_prior_to_variation_tag_of_move(self, move):
        """Return Tk tag name if currentmove is prior to a variation"""
        return self.get_prior_to_variation_tag_of_index(
            self.score.tag_ranges(move)[0])

    def get_choice_tag_for_prior(self, prior):
        """Return Tk tag name for choice with same suffix as prior."""
        return ''.join((CHOICE, prior[len(PRIOR_MOVE):]))

    def get_choice_tag_of_move(self, move):
        """Return Tk tag name if move is first move of a variation choice."""
        if move:
            return self.get_choice_tag_of_index(
                self.score.tag_ranges(move)[0])

    def get_selection_tag_for_choice(self, choice):
        """Return Tk tag name for selection with same suffix as choice."""
        return ''.join((SELECTION, choice[len(CHOICE):]))

    def get_selection_tag_for_prior(self, prior):
        """Return Tk tag name for selection with same suffix as prior."""
        return ''.join((SELECTION, prior[len(PRIOR_MOVE):]))

    def get_colouring_variation_tag_for_selection(self, selection):
        """Return Tk tag name for variation associated with selection."""
        return self.get_colouring_variation_tag_of_index(
            self.score.tag_ranges(selection)[0])

    def get_choice_tag_name(self):
        """Return suffixed CHOICE tag name.

        The suffix is arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.choice_number += 1
        suffix = str(self.choice_number)
        return ''.join((CHOICE, suffix))

    def get_rav_tag_names(self):
        """Return suffixed RAV_MOVES and RAV_TAG tag names.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.rav_number += 1
        suffix = str(self.rav_number)
        return [''.join((t, suffix)) for t in (RAV_MOVES, RAV_TAG)]

    def get_next_positiontag_name(self):
        """Return suffixed POSITION tag name."""
        self.position_number += 1
        return ''.join((POSITION, str(self.position_number)))

    def get_current_tag_and_mark_names(self):
        """Return suffixed POSITION and TOKEN tag and TOKEN_MARK mark names."""
        suffix = str(self.position_number)
        return [''.join((t, suffix)) for t in (POSITION, TOKEN, TOKEN_MARK)]

    def get_tag_and_mark_names(self):
        """Return suffixed POSITION and TOKEN tag and TOKEN_MARK mark names.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        A TOKEN_MARK name is generated for each token but the mark will be
        created only for editable tokens.

        """
        self.position_number += 1
        suffix = str(self.position_number)
        return [''.join((t, suffix)) for t in (POSITION, TOKEN, TOKEN_MARK)]

    def insert_token_into_text(self, token, separator):
        """Insert token and separator in widget.  Return boundary indicies.

        Indicies for start and end of token text are noted primarily to control
        editing and highlight significant text.  The end of separator index is
        used to generate contiguous regions for related tokens and act as a
        placeholder when there is no text between start and end.

        """
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token)
        end = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, separator)
        return start, end, widget.index(tkinter.INSERT)

    def is_currentmove_in_main_line(self):
        """Return True if currentmove is in the main line tag"""
        return self.is_index_in_main_line(
            self.score.tag_ranges(self.current)[0])

    def is_currentmove_start_of_variation(self):
        """Return True if currentmove is at start of a variation tag"""
        widget = self.score
        index = widget.tag_ranges(self.current)[0]
        for tn in widget.tag_names(index):
            if tn.startswith(RAV_SEP):
                return not bool(self.score.tag_prevrange(tn, index))

    def is_index_of_variation_next_move_in_choice(self):
        """Return True if index is in a choice of variations tag"""
        tr = self.get_range_next_move_in_variation()
        if not tr:
            return False
        for tn in self.score.tag_names(tr[0]):
            if tn.startswith(CHOICE):
                return True
        return False

    def is_index_in_main_line(self, index):
        """Return True if index is in the main line tag"""
        return bool(self.score.tag_nextrange(
            self._gamevartag,
            index,
            ''.join((str(index), '+1 chars'))))

    def is_move_in_main_line(self, move):
        """Return True if move is in the main line"""
        return self.is_index_in_main_line(
            self.score.tag_ranges(move)[0])

    def is_variation_entered(self):
        """Return True if currentmove is, or about to be, in variation.

        Colour tag LINE_TAG will contain at least one range if a variation
        has been entered; in particular when self.currentmove is about to
        be set to the first move of the variation at which point no other
        way of determining this is easy.  In fact LINE_TAG is populated
        ahead of time in this case to enable the test.

        """
        if self.score.tag_nextrange(LINE_TAG, '1.0'):
            return True
        return False

    '''At present both POSITION<suffix> and TOKEN<suffix> tags exist.

    Now that setting MOVE_TAG has been moved to token-type specific code there
    is probably no need for both.  TOKEN marks the active text of a POSITION,
    for example {<active text>} where POSITION includes the surrounding braces,
    but as active text can vary and when null POSITION is used to set MOVE_TAG
    might as well refer to POSITION directly.

    This means the set_insert_mark_for_editing and set_bound_marks_for_editing
    methods do not need to loop through tag names for TOKEN because it starts
    from a POSITION tag name.

    '''

    def _set_square_piece_map(self, position):
        assert len(position) == 1
        spm = self._square_piece_map
        spm.clear()
        for p, s in position[0][0]:
            spm[s] = p

    def _modify_square_piece_map(self, position):
        assert len(position) == 2
        spm = self._square_piece_map
        for s, p in position[0][0]:
            del spm[s]
        for s, p in position[1][0]:
            spm[s] = p

    # Attempt to re-design map_game method to fit new pgn_read package.
    def map_game(self):
        """Tag and mark the displayed text of game score.

        The tags and marks are used for colouring and navigating the score.

        """
        self._force_newline = 0

        # With get_current_...() methods as well do not need self._vartag
        # self._ravtag and self._choicetag state attributes.
        self._vartag, self._ravtag = self.get_rav_tag_names()
        self._choicetag = self.get_choice_tag_name()
        self._gamevartag = self._vartag

        self._start_latest_move = ''
        self._end_latest_move = ''
        self._next_move_is_choice = False
        self._token_position = None
        self._square_piece_map = {}
        
        self.score.mark_set(START_SCORE_MARK, '1.0')
        self.score.mark_gravity(START_SCORE_MARK, tkinter.LEFT)
        cg = self.collected_game
        spm = self._square_piece_map
        for p, s in cg._initial_position[0]:
            spm[s] = p
        assert len(cg._text) == len(cg._position_deltas)
        tags_displayed = self.map_tags_display_order()
        for text, position in zip(cg._text, cg._position_deltas):
            t0 = text[0]
            if t0 in 'abcdefghKQRBNkqrnO':
                self.map_move_text(text, position)
            elif t0 == '[':
                if not tags_displayed:
                    self.map_tag(text)
            elif t0 == '{':
                self.map_start_comment(text)
            elif t0 == '(':
                self.map_start_rav(text, position)
            elif t0 == ')':
                self.map_end_rav(text, position)
            elif t0 in '10*':
                self.map_termination(text)
            elif t0 == ';':
                self.map_comment_to_eol(text)
            elif t0 == '$':
                self.map_glyph(text)

            # Currently ignored if present in PGN input.
            elif t0 == '%':
                self.map_non_move(text)

            # Currently ignored if present in PGN input.
            elif t0 == '<':
                self.map_non_move(text)

            else:
                self.map_non_move(text)

        self.build_nextmovetags()

        # BUILD_TAG used to track moves and RAV markers during construction of
        # text.  Subclasses setup and use NAVIGATE_TOKEN for post-construction
        # comparisons of this, and other, kinds if necessary.  This class, and
        # subclasses, do not need this information after construction.
        # self.nextmovetags tracks the things BUILD_TAG is used for.  Maybe
        # change technique to use it rather than BUILD_TAG.
        self.score.tag_delete(BUILD_TAG)

    def map_move_text(self, token, position):
        """Add token to game text. Set navigation tags. Return token range.

        self._start_latest_move and self._end_latest_move are set to range
        occupied by token text so that variation tags can be constructed as
        more moves are processed.

        """
        self._modify_square_piece_map(position)
        widget = self.score
        positiontag = self.get_next_positiontag_name()
        p1 = position[1]
        self.tagpositionmap[
            positiontag] = (self._square_piece_map.copy(),) + p1[1:]
        fwa = p1[1] == FEN_WHITE_ACTIVE
        if not fwa:
            self._force_newline += 1
        if self._force_newline > FORCE_NEWLINE_AFTER_FULLMOVES:
            widget.insert(tkinter.INSERT, NEWLINE_SEP)
            self._force_newline = 1
        if not fwa:
            start, end, sepend = self.insert_token_into_text(
                str(p1[5])+'.', SPACE_SEP)
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            if self._force_newline == 1:
                widget.tag_add(FORCED_INDENT_TAG, start, end)
        elif self._next_move_is_choice:
            start, end, sepend = self.insert_token_into_text(
                str(position[0][5])+'...', SPACE_SEP)
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        if self._force_newline == 1:
            widget.tag_add(FORCED_INDENT_TAG, start, end)
        for tag in positiontag, self._vartag, NAVIGATE_MOVE, BUILD_TAG:
            widget.tag_add(tag, start, end)
        if self._vartag is self._gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        widget.tag_add(''.join((RAV_SEP, self._vartag)), start, sepend)
        if self._next_move_is_choice:
            widget.tag_add(ALL_CHOICES, start, end)

            # A START_RAV is needed to define and set choicetag and set
            # next_move_is_choice True.  There cannot be a START_RAV
            # until a MOVE_TEXT has occured: from PGN grammar.
            # So define and set choicetag then increment choice_number
            # in 'type_ is START_RAV' processing rather than other way
            # round, with initialization, to avoid tag name clutter.
            widget.tag_add(self._choicetag, start, end)
            self._next_move_is_choice = False

        self._start_latest_move = start
        self._end_latest_move = end
        self.create_previousmovetag(positiontag, start)
        return start, end, sepend

    def map_start_rav(self, token, position):
        """Add token to game text.  Return range and prior.

        Variation tags are set for guiding move navigation. self._vartag
        self._ravtag self._token_position and self._choicetag are placed on
        a stack for restoration at the end of the variation.
        self._next_move_is_choice is set True indicating that the next move
        is the default selection when choosing a variation.

        The _square_piece_map is reset from position.

        """
        self._set_square_piece_map(position)
        widget = self.score
        if not widget.tag_nextrange(
            ALL_CHOICES, self._start_latest_move, self._end_latest_move):

            # start_latest_move will be the second move, at earliest,
            # in current variation except if it is the first move in
            # the game.  Thus the move before start_latest_move using
            # tag_prevrange() can be tagged as the move creating the
            # position in which the choice of moves occurs.
            self._choicetag = self.get_choice_tag_name()
            widget.tag_add(
                ''.join((SELECTION, str(self.choice_number))),
                self._start_latest_move,
                self._end_latest_move)
            prior = self.get_range_for_prior_move_before_insert()
            if prior:
                widget.tag_add(
                    ''.join((PRIOR_MOVE, str(self.choice_number))),
                    *prior)

        widget.tag_add(
            ALL_CHOICES, self._start_latest_move, self._end_latest_move)
        widget.tag_add(
            self._choicetag, self._start_latest_move, self._end_latest_move)
        self.varstack.append((self._vartag, self._ravtag, self._token_position))
        self.choicestack.append(self._choicetag)
        self._vartag, self._ravtag = self.get_rav_tag_names()
        widget.insert(tkinter.INSERT, NEWLINE_SEP)
        self._force_newline = 0
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        widget.tag_add(BUILD_TAG, start, end)
        self._next_move_is_choice = True
        return start, end, sepend

    def map_end_rav(self, token, position):
        """Add token to game text.  Return token range.

        Variation tags are set for guiding move navigation. self._vartag
        self._ravtag self._token_position and self._choicetag are restored
        from the stack for restoration at the end of the variation.
        self._start_latest_move is set to the move which the first move of
        the variation replaced.

        The _square_piece_map is reset from position.

        """
        # ValueError exception has happened if and only if opening an invalid
        # game generated from an arbitrary text file completely unlike a PGN
        # file.  Probably no valid PGN tokens at all must be in the file to
        # cause this exception.
        try:
            (self._start_latest_move,
             self._end_latest_move) = self.score.tag_prevrange(
                 ALL_CHOICES, tkinter.END)
        except ValueError:
            return tkinter.END, tkinter.END, tkinter.END
        
        self._set_square_piece_map(position)
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        self.score.tag_add(BUILD_TAG, start, end)
        self._vartag, self._ravtag, self._token_position = self.varstack.pop()
        self._choicetag = self.choicestack.pop()
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return start, end, sepend

    def map_tag(self, token):
        """Add PGN Tag to game text."""
        t, v = token[1:-1].split('"', 1)
        v = v[:-1]
        self.add_pgntag_to_map(t, v)

    def map_tags_display_order(self):
        """Add PGN Tags to game text."""
        tag_values = self.get_tags_display_order()
        self.tagpositionmap[None] = self.fen_tag_tuple_square_piece_map()
        if tag_values is None:
            return False
        for tv in tag_values:
            self.add_pgntag_to_map(*tv)
        return True

    def map_termination(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self.score.insert(tkinter.INSERT, NEWLINE_SEP)
        return self.insert_token_into_text(token, NEWLINE_SEP)

    def map_start_comment(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.score.insert(tkinter.INSERT, NEWLINE_SEP)
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_comment_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        widget = self.score
        widget.insert(tkinter.INSERT, NEWLINE_SEP)
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token[:-1])#token)
        end = widget.index(tkinter.INSERT)# + ' -1 chars')
        #widget.insert(tkinter.INSERT, NULL_SEP)
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return start, end, widget.index(tkinter.INSERT)

    def map_escape_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token[:-1])
        end = widget.index(tkinter.INSERT)# + ' -1 chars')
        #widget.insert(tkinter.INSERT, NULL_SEP)
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return start, end, widget.index(tkinter.INSERT)

    def map_integer(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_glyph(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_period(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_start_reserved(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_non_move(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def remove_currentmove_from_moves_played_in_variation(self):
        """Remove current move from moves played in variation colouring tag."""
        widget = self.score
        tr = widget.tag_nextrange(self.current, '1.0')
        widget.tag_remove(VARIATION_TAG, tr[0], tr[1])

    def select_first_move_in_line(self, move):
        """Return tag name for first move in rav containing move."""
        widget = self.score
        tr = widget.tag_ranges(move)
        if not tr:
            return None
        for oldtn in widget.tag_names(tr[0]):
            if oldtn.startswith(RAV_MOVES):
                break
        else:
            return None
        tr = widget.tag_nextrange(oldtn, '1.0')
        if not tr:
            return move
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_first_move_of_game(self):
        """Return name of tag associated with first move of game"""
        widget = self.score
        try:
            index = widget.tag_nextrange(self._gamevartag, '1.0')[0]
        except IndexError:
            return None
        for tn in widget.tag_names(index):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_first_move_of_selected_line(self, selection):
        """Return name of tag associated with first move of line"""
        widget = self.score
        for tn in widget.tag_names(widget.tag_ranges(selection)[0]):
            if tn.startswith(POSITION):
                return tn

    def select_last_move_of_selected_line(self, selection):
        """Return name of tag associated with last move of line"""
        widget = self.score
        for tn in widget.tag_names(widget.tag_ranges(selection)[-2]):
            if tn.startswith(POSITION):
                return tn

    def select_last_move_played_in_game(self):
        """Return name of tag associated with last move played in game"""
        widget = self.score
        try:
            index = widget.tag_prevrange(self._gamevartag, tkinter.END)[0]
        except IndexError:
            return None
        for tn in widget.tag_names(index):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_last_move_in_line(self):
        """Return name of tag associated with last move in line"""
        widget = self.score
        tr = widget.tag_ranges(MOVE_TAG)
        if not tr:
            return None
        for oldtn in widget.tag_names(tr[0]):
            if oldtn.startswith(RAV_MOVES):
                break
        else:
            return None
        tr = widget.tag_prevrange(oldtn, tkinter.END)
        if not tr:
            return self.current
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_next_move_in_line(self, movetag=MOVE_TAG):
        """Return name of tag associated with next move in line"""
        widget = self.score
        tr = widget.tag_ranges(movetag)
        if not tr:
            return None
        for oldtn in widget.tag_names(tr[0]):
            if oldtn.startswith(RAV_MOVES):
                break
        else:
            return None
        tr = widget.tag_nextrange(oldtn, ''.join((str(tr[0]), '+1 chars')))
        if not tr:
            return self.current
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_prev_move_in_line(self):
        """Return name of tag associated with previous move in line"""
        widget = self.score
        oldtr = widget.tag_ranges(MOVE_TAG)
        if not oldtr:
            return None
        for oldtn in widget.tag_names(oldtr[0]):
            if oldtn.startswith(RAV_MOVES):
                break
        else:
            return None
        tr = widget.tag_prevrange(oldtn, oldtr[0])
        if not tr:
            if widget.tag_prevrange(NAVIGATE_MOVE, oldtr[0]):
                return self.current
            return None
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def get_position_tag_of_previous_move(self):
        """Return name of tag of move played prior to current move in line.

        Assumes self.currentmove has been removed from VARIATION_TAG.

        """
        widget = self.score
        tr = widget.tag_prevrange(VARIATION_TAG, tkinter.END)
        if not tr:

            # Should be so just for variations on the first move of game
            return None

        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn

    def set_current(self):
        """Remove existing MOVE_TAG ranges and add self.currentmove ranges.

        Subclasses may adjust the MOVE_TAG range if the required colouring
        range of the item is different.  For example just <text> in {<text>}
        which is a PGN comment where <text> may be null after editing.

        The adjusted range must be a subset of self.currentmove range.

        """
        # Superclass set_current method may adjust bindings so do not call
        # context independent binding setup methods after this method for
        # an event.
        tr = self.set_current_range()
        if tr:
            self.set_move_tag(tr[0], tr[1])
            return tr

    def set_current_range(self):
        """Remove existing MOVE_TAG ranges and add self.currentmove ranges.

        Subclasses may adjust the MOVE_TAG range if the required colouring
        range of the item is different.  For example just <text> in {<text>}
        which is a PGN comment where <text> may be null after editing.

        The adjusted range must be a subset of self.currentmove range.

        """
        self.clear_current_range()
        if self.current is None:
            return
        tr = self.score.tag_ranges(self.current)
        if not tr:
            return
        return tr

    def set_statusbar_text(self):
        """Set status bar to display player name PGN Tags."""
        tags = self.collected_game._tags
        self.ui.statusbar.set_status_text(
            '  '.join(
                [tags.get(k, '')
                 for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS]))

    def set_move_tag(self, start, end):
        """Add range start to end to MOVE_TAG (which is expected to be empty).

        Assumption is that set_current_range has been called and MOVE_TAG is
        still empty following that call.

        """
        self.score.tag_add(MOVE_TAG, start, end)

    def set_next_variation_move_played_colouring_tag(self, move):
        """Add range from selected variation for move to moves played tag.

        Used at start of game when no move has been played.

        Find the range in the selected variation (RAV_SEP) corresponding to
        the range of move (usually the current move except at start of game)
        and add it to the colouring tag (VARIATION_TAG) for moves played in
        the selected variation leading to the current move.  It is assumed
        self.set_current() will be called to change the current move,
        including the colouring tag (MOVE_TAG), exposing this setting.

        self.set_current uses the existence of a range in VARIATION_TAG
        to decide if the current move is in the main line of the game.

        """
        widget = self.score
        for vtn in widget.tag_names(widget.tag_nextrange(move, '1.0')[0]):
            if vtn.startswith(RAV_SEP):
                tr = widget.tag_nextrange(
                    NAVIGATE_MOVE,
                    widget.tag_nextrange(vtn, '1.0')[0])
                widget.tag_add(VARIATION_TAG, tr[0], tr[1])
                break

    def set_variation_selection_tags(
        self,
        move_prior_to_choice,
        first_moves_in_variations,
        selected_first_move,
        moves_in_variation):
        """Replace existing ranges on color tags with ranges in arguments.

        The replacement is applied to the right of move_prior_to_choice,
        which is usually the same as current move.  In practice this only
        effects moves_in_variation because the moves to left of current move
        are not present unless the variation is the main line.

        """
        ######## warning ######
        #
        # VARIATION_COLOR is the colour applied to moves up to the current
        # move in a RAV.
        # LINE_COLOR is the colour applied to moves after the selected move
        # where a choice of next moves exists.
        #
        # RAV_SEP<suffix> is the Tk tag for a set of moves to which the
        # colour LINE_COLOR may be applied.
        # VARIATION_TAG is the Tk tag for the set of moves to which the
        # colour VARIATION_COLOR may be applied.
        # RAV_MOVES<suffix> is the Tk tag for the editable characters in a
        # set of moves for which RAV_SEP<suffix> is the colouring tag.
        #
        #######################
        #
        # Now it may be possible to use START_SCORE_MARK rather than '1.0'
        #
        #######################

        widget = self.score
        if move_prior_to_choice is None:
            index = '1.0'
        else:
            index = widget.tag_ranges(move_prior_to_choice)[0]

        # Remove current move from VARIATION_TAG (for show_prev_in_variation)
        if move_prior_to_choice:
            widget.tag_remove(VARIATION_TAG, index, tkinter.END)

        widget.tag_remove(ALTERNATIVE_MOVE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_END_TAG, index, tkinter.END)
        self._add_tag_ranges_to_color_tag(
            first_moves_in_variations, ALTERNATIVE_MOVE_TAG)
        self._add_tag_ranges_to_color_tag(moves_in_variation, LINE_TAG)

        # In all cases but one there is nothing to remove.  But if the choice
        # includes a move played in the game LINE_TAG contains all these moves
        # when the move played is the selection.
        widget.tag_remove(
            LINE_TAG,
            '1.0',
            widget.tag_nextrange(first_moves_in_variations, '1.0')[0])

        widget.tag_add(
            LINE_END_TAG,
            ''.join((
                str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                '-1 chars')))

    def set_variation_tags_from_currentmove(self):
        """Replace existing color tags ranges with those current move.

        Assumes colour tags are already set correctly for moves prior to
        current move in variation.

        """
        widget = self.score
        index = widget.tag_ranges(self.current)[0]
        widget.tag_remove(VARIATION_TAG, index, tkinter.END)
        widget.tag_remove(LINE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_END_TAG, index, tkinter.END)
        self._add_tag_ranges_to_color_tag(
            self.get_colouring_variation_tag_of_index(index), LINE_TAG)
        widget.tag_add(
            LINE_END_TAG,
            ''.join((
                str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                '-1 chars')))

    def apply_colouring_to_variation_back_to_main_line(self):
        """Apply colouring as if move navigation used to reach current move.

        Used in point and click navigation and when exiting token navigation
        to resume move navigation.  It is assumed that no colouring is applied
        to moves (compare with move navigation where incremental colouring
        occurs).

        """
        if self.current is None:
            return
        move = self.current
        if not self.is_move_in_main_line(move):
            self.add_currentmove_variation_to_colouring_tag()
        while not self.is_move_in_main_line(move):
            self.add_move_to_moves_played_colouring_tag(move)
            self.add_variation_before_move_to_colouring_tag(move)
            first_move_of_variation = self.select_first_move_in_line(move)
            choice = self.get_choice_tag_of_move(first_move_of_variation)
            prior = self.score.tag_ranges(self.get_prior_tag_for_choice(choice))
            if not prior:
                move = None
                break
            move = self.get_position_tag_of_index(prior[0])
            selection = self.get_selection_tag_for_choice(choice)
            if selection:
                self.score.tag_remove(selection, '1.0', tkinter.END)
                self.score.tag_add(
                    selection,
                    *self.score.tag_ranges(first_move_of_variation))
        if self.score.tag_nextrange(VARIATION_TAG, '1.0'):
            if move:
                self.add_move_to_moves_played_colouring_tag(move)

    def get_prior_tag_for_choice(self, choice):
        """Return Tk tag name for prior move with same suffix as choice."""
        return ''.join((PRIOR_MOVE, choice[len(CHOICE):]))

    def go_to_move(self, index):
        """Show position for move text at index"""
        widget = self.score
        move = widget.tag_nextrange(NAVIGATE_MOVE, index)
        if not move:
            move = widget.tag_prevrange(NAVIGATE_MOVE, index)
            if not move:
                return
            elif widget.compare(move[1], '<', index):
                return
        elif widget.compare(move[0], '>', index):
            move = widget.tag_prevrange(NAVIGATE_MOVE, move[0])
            if not move:
                return
            if widget.compare(move[1], '<', index):
                return
        selected_move = self.get_position_tag_of_index(index)
        if selected_move:
            self.clear_moves_played_in_variation_colouring_tag()
            self.clear_choice_colouring_tag()
            self.clear_variation_colouring_tag()
            self.current = selected_move
            self.set_current()
            self.apply_colouring_to_variation_back_to_main_line()
            self.set_game_board()
            return True

    def go_to_token(self, event=None):
        """Set position and highlighting for token under pointer"""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return 'break'
        self.go_to_move(
            self.score.index(''.join(('@', str(event.x), ',', str(event.y)))))
        
    def popup_inactive_menu(self, event=None):
        """Show the popup menu for a score in an inactive item.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        self.inactive_popup.tk_popup(*self.score.winfo_pointerxy())
        
    def popup_viewmode_menu(self, event=None):
        """Show the popup menu for game score navigation.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return 'break'
        self.viewmode_popup.tk_popup(*self.score.winfo_pointerxy())

    def popup_variation_menu(self, event=None):
        """Show the popup menu for variation selection in game score.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return 'break'
        self.selectmode_popup.tk_popup(*self.score.winfo_pointerxy())

    def show_new_current(self, new_current=None):
        """Set current to new item and adjust display."""
        self.clear_moves_played_in_variation_colouring_tag()
        self.clear_choice_colouring_tag()
        self.clear_variation_colouring_tag()
        self.current = new_current
        self.set_current()
        self.set_game_board()
        return 'break'
        
    def show_item(self, new_item=None):
        """Display new item if not None."""
        if new_item:
            return self.show_new_current(new_current=new_item)
        return 'break'

    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a game including switching from
        one game to another.
        
        """
        grid = self.itemgrid
        if grid is None:
            return
        if grid.get_database() is not None:
            newpartialkey = self.get_position_key()
            if grid.partial != newpartialkey:
                grid.partial = newpartialkey
                grid.rows = 1
                grid.close_client_cursor()
                grid.datasource.get_full_position_games(newpartialkey)
                grid.load_new_index()
        
    def _add_tag_ranges_to_color_tag(self, tag, colortag):
        """Add the index ranges in tag to colortag.

        Tkinter Text.tag_add() takes two indicies as arguments rather than
        the list of 2n indicies, for n ranges, accepted by Tk tag_add.
        So do it a long way.

        """
        add = self.score.tag_add
        tr = list(self.score.tag_ranges(tag))
        while len(tr):
            start = tr.pop(0)
            end = tr.pop(0)
            add(colortag, start, end)

    def _get_range_next_move_in_variation(self):
        """Return range of move after current move in variation."""
        widget = self.score
        tr = widget.tag_ranges(self.current)
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(RAV_MOVES):
                break
        else:
            return
        tr = widget.tag_nextrange(tn, ''.join((str(tr[0]), '+1 chars')))
        if not tr:
            return
        return tr

    def _remove_tag_ranges_from_color_tag(self, tag, colortag):
        """Remove the index ranges in tag from colortag.

        Tkinter Text.tag_add() takes two indicies as arguments rather than
        the list of 2n indicies, for n ranges, accepted by Tk tag_remove.
        So do it a long way.

        """
        remove = self.score.tag_remove
        tr = list(self.score.tag_ranges(tag))
        while len(tr):
            start = tr.pop(0)
            end = tr.pop(0)
            remove(colortag, start, end)

    def select_move_for_start_of_analysis(self, movetag=MOVE_TAG):
        """Return name of tag for move to which analysis will be attached.

        Differs from select_next_move_in_line() by returning None if at last
        position in line or game, rather than self.current.

        """
        widget = self.score
        tr = widget.tag_ranges(movetag)
        if not tr:
            return None
        for oldtn in widget.tag_names(tr[0]):
            if oldtn.startswith(RAV_MOVES):
                break
        else:
            return None
        tr = widget.tag_nextrange(oldtn, ''.join((str(tr[0]), '+1 chars')))
        if not tr:
            return None
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def get_move_for_start_of_analysis(self):
        """Return PGN text of move to which analysis will be RAVs.

        Default to first move played in game, or '' if no moves played, or ''
        if current position is last in line or game.

        """
        if self.current is None:
            tag = self.select_first_move_of_game()
        else:
            tag = self.select_move_for_start_of_analysis()
        if tag is None:
            return ''
        tr = self.score.tag_ranges(tag)
        if not tr:
            return ''
        return self.score.get(*tr)


class AnalysisScore(Score):

    """Chess position analysis widget, a customised Score widget.

    The move number of the move made in the game score is given, but move
    numbers are not shown for the analysis from chess engines.  Each variation
    has it's own line, possibly wrapped depending on widget width, so newlines
    are not inserted as a defence against slow response times for very long
    wrapped lines which would occur for depth arguments in excess of 500
    passed to chess engines.

    The Score widget is set up once from a gui.Game widget, and may be edited
    move by move on instruction from that widget.

    This class provides one method to clear that part of the state derived from
    a pgn_read.Game instance, and overrides one method to allow for analysis of
    the final position in the game or a variation.

    Recursive analysis (of a position in the analysis) is not supported.
    
    """
    # Initial value of current text displayed in analysis widget: used to
    # control refresh after periodic update requests.
    analysis_text = None
    

    def clear_score(self):
        """Clear data stuctures for navigating a game score.

        Normally a game is loaded into the Score instance and remains for the
        lifetime of the instance.  UCI Chess Engine analysis, in particular, is
        used to refresh the game score snippet in an analysis widget after each
        navigation event in the main game widget.

        This method allows the Score instance to be reused for many PGN game
        scores, full games or otherwise.

        """
        self.rav_number = 0
        self.varstack = []
        self.choice_number = 0
        self.choicestack = []
        self.position_number = 0
        self.tagpositionmap = dict()
        self.previousmovetags = dict()
        self.nextmovetags = dict()

    def go_to_token(self, event=None):
        """Set position and highlighting for token under pointer"""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item.analysis:
                return 'break'
        self.go_to_move(
            self.score.index(''.join(('@', str(event.x), ',', str(event.y)))))
        
    def popup_viewmode_menu(self, event=None):
        """Show the popup menu for game score navigation.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item.analysis:
                return 'break'
        self.viewmode_popup.tk_popup(*self.score.winfo_pointerxy())

    def popup_variation_menu(self, event=None):
        """Show the popup menu for variation selection in game score.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item.analysis:
                return 'break'
        self.selectmode_popup.tk_popup(*self.score.winfo_pointerxy())
        
    def set_score(self, analysis_text, reset_undo=False):
        """Display the game as moves.

        starttoken is the move played to reach the position displayed and this
        move becomes the current move.
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a game for editing so that repeated Ctrl-Z in text
        editing mode recovers the original score.
        
        """
        if not self._is_score_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)

        # An attempt to insert an illegal move into a game score will cause
        # an exception when parsing the engine.  Expected to happen when
        # editing or inserting a game and the move before an incomplete move
        # becomes the current move.
        # Illegal moves are wrapped in '{Error::  ::{{::}' comments by the
        # game updater: like '--' moves found in some PGN files which do not
        # follow the standard strictly.
        try:
            self.map_game()
        except TypeError:
            self.score.insert(
                tkinter.END,
                ''.join(('The analysis is attached to an illegal move, ',
                         'likely while editing or inserting a game.\n\nIt ',
                         'is displayed but cannot be played through.\n\n')))
            self.score.insert(tkinter.END, analysis_text)

        self.bind_for_viewmode()
        if not self._is_score_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()
        self.analysis_text = analysis_text
        
    def set_game_board(self):
        """Show position after highlighted move and return False.

        False means this is not a game score.

        The setup_game_board() in Score returns True normally, or None if a
        problem occurs.

        """
        if self.current is None:

            # Arises as a consequence of avoiding the exception caught in
            # map_game.
            try:
                self.board.set_board(self.fen_tag_square_piece_map())
            except TypeError:
                return False

            self.see_first_move()
        else:
            try:
                self.board.set_board(self.tagpositionmap[self.current][0])
            except TypeError:
                self.board.set_board(self.fen_tag_square_piece_map())
                self.score.see(self.score.tag_ranges(self.current)[0])
                return False
            self.score.see(self.score.tag_ranges(self.current)[0])
        return False

    def map_move_text(self, token, position):
        """Add token to game text. Set navigation tags. Return token range.

        self._start_latest_move and self._end_latest_move are set to range
        occupied by token text so that variation tags can be constructed as
        more moves are processed.

        """
        self._modify_square_piece_map(position)
        widget = self.score
        positiontag = self.get_next_positiontag_name()
        self.tagpositionmap[
            positiontag] = (self._square_piece_map.copy(),) + position[1][1:]

        # The only way found to get the move number at start of analysis.
        # Direct use of self.score.insert(...), as in insert_token_into_text,
        # or a separate call to insert_token_into_text(...), does not work:
        # interaction with refresh_analysis_widget_from_database() in
        # game.Game when building the text is assumed to be the cause.
        if not len(self.varstack):
            a, active_side, a, a, a, fullmove_number = position[0]
            del a
            if active_side == FEN_WHITE_ACTIVE:
                fullmove_number = str(fullmove_number) + PGN_DOT
            else:
                fullmove_number = str(fullmove_number) + PGN_DOT * 3
            start, end, sepend = self.insert_token_into_text(
                ''.join((fullmove_number, SPACE_SEP, token)),
                SPACE_SEP)
        else:
            start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)

        for tag in positiontag, self._vartag, NAVIGATE_MOVE, BUILD_TAG:
            widget.tag_add(tag, start, end)
        if self._vartag is self._gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        widget.tag_add(''.join((RAV_SEP, self._vartag)), start, sepend)
        if self._next_move_is_choice:
            widget.tag_add(ALL_CHOICES, start, end)

            # A START_RAV is needed to define and set choicetag and set
            # next_move_is_choice True.  There cannot be a START_RAV
            # until a MOVE_TEXT has occured: from PGN grammar.
            # So define and set choicetag then increment choice_number
            # in 'type_ is START_RAV' processing rather than other way
            # round, with initialization, to avoid tag name clutter.
            widget.tag_add(self._choicetag, start, end)
            self._next_move_is_choice = False

        self._start_latest_move = start
        self._end_latest_move = end
        self.create_previousmovetag(positiontag, start)
        return start, end, sepend

    def map_start_rav(self, token, position):
        """Add token to game text.  Return range and prior.

        Variation tags are set for guiding move navigation. self._vartag
        self._ravtag self._token_position and self._choicetag are placed on
        a stack for restoration at the end of the variation.
        self._next_move_is_choice is set True indicating that the next move
        is the default selection when choosing a variation.

        The _square_piece_map is reset from position.

        """
        self._set_square_piece_map(position)
        widget = self.score
        if not widget.tag_nextrange(
            ALL_CHOICES, self._start_latest_move, self._end_latest_move):

            # start_latest_move will be the second move, at earliest,
            # in current variation except if it is the first move in
            # the game.  Thus the move before start_latest_move using
            # tag_prevrange() can be tagged as the move creating the
            # position in which the choice of moves occurs.
            self._choicetag = self.get_choice_tag_name()
            widget.tag_add(
                ''.join((SELECTION, str(self.choice_number))),
                self._start_latest_move,
                self._end_latest_move)
            prior = self.get_range_for_prior_move_before_insert()
            if prior:
                widget.tag_add(
                    ''.join((PRIOR_MOVE, str(self.choice_number))),
                    *prior)

        widget.tag_add(
            ALL_CHOICES, self._start_latest_move, self._end_latest_move)
        widget.tag_add(
            self._choicetag, self._start_latest_move, self._end_latest_move)
        self.varstack.append((self._vartag, self._ravtag, self._token_position))
        self.choicestack.append(self._choicetag)
        self._vartag, self._ravtag = self.get_rav_tag_names()
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        widget.tag_add(BUILD_TAG, start, end)
        self._next_move_is_choice = True
        return start, end, sepend

    def map_end_rav(self, token, position):
        """Add token to game text. position is ignored. Return token range.

        Variation tags are set for guiding move navigation. self._vartag
        self._ravtag self._token_position and self._choicetag are restored
        from the stack for restoration at the end of the variation.
        self._start_latest_move is set to the move which the first move of
        the variation replaced.

        """
        try:
            (self._start_latest_move,
             self._end_latest_move) = self.score.tag_prevrange(
                 ALL_CHOICES, tkinter.END)
        except:
            (self._start_latest_move,
             self._end_latest_move) = (tkinter.END, tkinter.END)
        start, end, sepend = self.insert_token_into_text(token, NEWLINE_SEP)
        self.score.tag_add(BUILD_TAG, start, end)
        self._vartag, self._ravtag, self._token_position = self.varstack.pop()
        self._choicetag = self.choicestack.pop()
        return start, end, sepend

    def map_start_comment(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_comment_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token)
        end = widget.index(tkinter.INSERT + ' -1 chars')
        widget.insert(tkinter.INSERT, NULL_SEP)
        return start, end, widget.index(tkinter.INSERT)

    def map_termination(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, NEWLINE_SEP)
