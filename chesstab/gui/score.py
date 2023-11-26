# score.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class with methods to display and navigate the score of a game of chess.

The Score class displays text derived from PGN and highlights moves.

The score of the game is extracted, by default, from a GameDisplayMoves
instance.  That class is defined in the core.pgn module.

"""

import tkinter

from pgn_read.core.parser import PGN
from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
    FEN_WHITE_ACTIVE,
)

from .constants import (
    LINE_COLOR,
    MOVE_COLOR,
    ALTERNATIVE_MOVE_COLOR,
    VARIATION_COLOR,
    MOVES_PLAYED_IN_GAME_FONT,
    TAGS_VARIATIONS_COMMENTS_FONT,
    NAVIGATE_MOVE,
    TOKEN,
    RAV_MOVES,
    CHOICE,
    PRIOR_MOVE,
    RAV_SEP,
    ALL_CHOICES,
    POSITION,
    MOVE_TAG,
    SELECTION,
    ALTERNATIVE_MOVE_TAG,
    LINE_TAG,
    VARIATION_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    TOKEN_MARK,
    BUILD_TAG,
    SPACE_SEP,
    NEWLINE_SEP,
    FORCE_NEWLINE_AFTER_FULLMOVES,
    FORCED_INDENT_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    FORCED_NEWLINE_TAG,
)
from .eventspec import EventSpec
from .blanktext import BlankText, NonTagBind
from .sharedtext import SharedTextScore
from ..core import export_game
from ..core.pgn import get_position_string, GameDisplayMoves
from ._score_scaffold import _ScoreScaffold


class ScoreNoGameException(Exception):
    """Raise to indicate non-PGN text after Game Termination Marker.

    The ScoreNoGameException is intended to catch cases where a file
    claiming to be a PGN file contains text with little resemblance to
    the PGN standard between a Game Termination Marker and a PGN Tag or
    a move description like Ba4.  For example 'anytext*anytextBa4anytext'
    or 'anytext0-1anytext[tagname"tagvalue"]anytext'.

    """


class ScoreNoInitialPositionException(Exception):
    """Raise to indicate non-PGN text after Game Termination Marker.

    The ScoreNoInitialPositionException is intended to catch cases where a
    file claiming to be a PGN file contains text with little resemblance to
    the PGN standard between a Game Termination Marker and a PGN Tag or
    a move description like Ba4.  For example 'anytext*anytextBa4anytext'
    or 'anytext0-1anytext[tagname"tagvalue"]anytext'.

    """


class ScoreMapToBoardException(Exception):
    """Raise to indicate display of chess engine analysis for illegal move.

    In particular in the GameEdit class when the move played is the last in
    game or variation, but is being edited at the time and not complete.  It
    is caught in the AnalysisScore class but should be treated as a real
    error in the Score class.

    """


class ScoreRAVNoPriorMoveException(Exception):
    """Raise to indicate a start RAV marker does not have a prior move."""


class Score(SharedTextScore, BlankText):
    """The game score, a board for current position, and navigation.

    panel is used as the panel argument for the super().__init__ call.

    board is the board.Board instance where the current position in this
    ScoreWidget instance is shown.

    tags_variations_comments_font is the font used for non-move PGN tokens,
    the default font is in class attribute tags_variations_comments_font.

    moves_played_in_game_font is the font used for non-move PGN tokens, the
    default font is in class attribute moves_played_in_game_font.

    ui is the user interface manager for an instance of ScoreWidget, usually
    an instance of ChessUI.  It is ignored and ScoreWidget instances refer
    to the board for the ui.

    items_manager is used as the items_manager argument for the
    super().__init__ call.

    itemgrid is the ui reference to the DataGrid from which the record was
    selected.

    Subclasses are responsible for providing a geometry manager.

    Attribute l_color is the background colour for a variation when it has
    the current move.

    Attribute m_color is the background colour for moves in a variation when
    it has the current move, which are before the current move.

    Attribute am_color is the background colour for moves which start other
    variations when selecting a variation.  The current choice has the colour
    specified by l_color.

    Attribute v_color is the background colour for the game move preceding
    the first move in the variation.

    Attribute tags_displayed_last is the PGN tags, in order, to be displayed
    immediately before the movetext.  It exists so Game*, Repertoire*, and
    AnalysisScore*, instances can use identical code to display PGN tags.  It
    is the PGN Seven Tag Roster.

    Attribute pgn_export_type is a tuple with the name of the type of data and
    the class used to generate export PGN.  It exists so Game*, Repertoire*,
    and AnalysisScore*, instances can use identical code to display PGN tags.
    It is ('Game', GameDisplayMoves).

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    """

    l_color = LINE_COLOR
    m_color = MOVE_COLOR
    am_color = ALTERNATIVE_MOVE_COLOR
    v_color = VARIATION_COLOR
    tags_variations_comments_font = TAGS_VARIATIONS_COMMENTS_FONT
    moves_played_in_game_font = MOVES_PLAYED_IN_GAME_FONT

    tags_displayed_last = SEVEN_TAG_ROSTER
    pgn_export_type = "Game", GameDisplayMoves

    # Indicate the most recent set of bindings applied to score attribute.
    # There will be some implied bindings to the board attribute, but board
    # may  be shared by more than one Score instance.  The analysis.score and
    # score attributes of a Game instance for example.
    # Values are Tk tag names or members of NonTagBind enumeration.
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    # Maybe do not need pgn_export_type for 'export_..' methods if repertoire
    # subclasses use gameclass=GameRepertoireDisplayMoves.
    def __init__(
        self,
        panel,
        board,
        tags_variations_comments_font=None,
        moves_played_in_game_font=None,
        gameclass=GameDisplayMoves,
        items_manager=None,
        itemgrid=None,
        **ka
    ):
        """Create widgets to display game score."""
        super().__init__(panel, items_manager=items_manager, **ka)
        self.itemgrid = itemgrid
        if tags_variations_comments_font:
            self.tags_variations_comments_font = tags_variations_comments_font
        if moves_played_in_game_font:
            self.moves_played_in_game_font = moves_played_in_game_font
        self.board = board
        self.score.configure(
            font=self.tags_variations_comments_font,
            selectbackground=self.score.cget("background"),
            inactiveselectbackground="",
        )
        self.score.tag_configure(
            MOVES_PLAYED_IN_GAME_FONT, font=self.moves_played_in_game_font
        )

        # Order is ALTERNATIVE_MOVE_TAG LINE_TAG VARIATION_TAG LINE_END_TAG
        # MOVE_TAG so that correct colour has highest priority as moves are
        # added to and removed from tags.
        self.score.tag_configure(
            ALTERNATIVE_MOVE_TAG, background=self.am_color
        )
        self.score.tag_configure(LINE_TAG, background=self.l_color)
        self.score.tag_configure(VARIATION_TAG, background=self.v_color)
        self.score.tag_configure(
            LINE_END_TAG, background=self.score.cget("background")
        )
        self.score.tag_configure(MOVE_TAG, background=self.m_color)

        # The popup menus for the game score.
        self.select_move_popup = None

        # None implies initial position and is deliberately not a valid Tk tag.
        self.current = None  # Tk tag of current move

        # These attributes replace the structure used with wxWidgets controls.
        # Record the structure by tagging text in the Tk Text widget.
        self.variation_number = 0
        self.varstack = []
        self.choice_number = 0
        self.choicestack = []
        self.position_number = 0
        self.tagpositionmap = {}
        self.previousmovetags = {}
        self.nextmovetags = {}

        # PGN parser creates a gameclass instance for game data structure and
        # binds it to collected_game attribute.
        self.gameclass = gameclass
        self.collected_game = None

        self.gamevartag = None
        self._game_scaffold = None

    # The methods which bind and handle events.

    def _set_event_bindings_board(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        sbbv = self.board.boardsquares.values
        for sequence, function in bindings:
            stef = ste(function) if switch and function else ""
            for widget in sbbv():
                self.bind(widget, sequence[0], function=stef)

    # Renamed from 'bind_for_select_variation_mode' when 'bind_for_*' methods
    # tied to Tk Text widget tag names were introduced.
    def bind_for_select_variation(self, switch=True):
        """Set keyboard bindings and popup menu for selecting a variation.

        Two navigation states are assumed.  Traversing the game score through
        adjacent tokens, and selecting the next move from a set of variations.

        For pointer clicks a token is defined to be adjacent to all tokens.

        """
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.SELECT_VARIATION
        self._set_select_variation_bindings(switch=True)

    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = BlankText.token_bind_method.copy()
    token_bind_method[NonTagBind.SELECT_VARIATION] = bind_for_select_variation

    # Renamed from '_bind_viewmode' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    def _set_primary_activity_bindings(self, switch=True):
        """Switch bindings for traversing moves on or off."""
        self.set_event_bindings_score(
            self.get_primary_activity_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_f10_popup_events(
                self._post_move_menu_at_top_left, self._post_move_menu
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_all_export_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_primary_activity_button_events(), switch=switch
        )

    # Renamed from '_bind_select_variation' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    def _set_select_variation_bindings(self, switch=True):
        """Switch bindings for selecting a variation on or off."""
        self.set_event_bindings_score(
            self._get_select_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_f10_popup_events(
                self._post_select_move_menu_at_top_left,
                self._post_select_move_menu,
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self.variation_cancel,
                buttonpress3=self._post_select_move_menu,
            ),
            switch=switch,
        )

    # This method may have independence from _set_primary_activity_bindings
    # when the control_buttonpress_1 event is fired.
    # (So there should be a 'select_variation' version too?)
    # Renamed from bind_score_pointer_for_board_navigation to fit current use.
    def set_score_pointer_item_navigation_bindings(self, switch):
        """Set or unset pointer bindings for game navigation."""
        self.set_event_bindings_score(
            self._get_primary_activity_button_events(), switch=switch
        )

    # Not yet used.
    # Recently added to game.py but moved here because it makes more sense to
    # do the work in the (game).score or (game.analysis).score object than
    # choose which is wanted in the (game) object.
    # _set_board_pointer_widget_navigation_bindings is likely to follow.
    # There is no equivalent of _set_select_variation_bindings to contain this.
    def set_board_pointer_select_variation_bindings(self, switch):
        """Enable or disable bindings for variation selection."""
        self._set_event_bindings_board(
            self._get_modifier_buttonpress_suppression_events(), switch=switch
        )
        self._set_event_bindings_board(
            (
                (EventSpec.buttonpress_1, self.variation_cancel),
                (EventSpec.buttonpress_3, self._show_next_in_variation),
                (EventSpec.shift_buttonpress_3, self._show_variation),
            ),
            switch=switch,
        )

    # There is no equivalent of _set_primary_activity_bindings to contain this.
    def set_board_pointer_move_bindings(self, switch):
        """Enable or disable bindings for game navigation."""
        self._set_event_bindings_board(
            self._get_modifier_buttonpress_suppression_events(), switch=switch
        )
        self._set_event_bindings_board(
            (
                (EventSpec.buttonpress_1, self._show_prev_in_line),
                (EventSpec.shift_buttonpress_1, self._show_prev_in_variation),
                (EventSpec.buttonpress_3, self._show_next_in_variation),
            ),
            switch=switch,
        )

    def get_keypress_suppression_events(self):
        """Return tuple of bindings to ignore all key presses.

        F10 should be enabled by a more specific binding to activate the
        menubar.

        """
        return ((EventSpec.score_disable_keypress, self.press_break),)

    # May become an eight argument ButtonPress event handler setter method
    # because it is always associated with settings for ButtonPress-1 and
    # ButtonPress-3.  Especially if events other than Control-ButtonPress-1
    # get handlers.
    def _get_modifier_buttonpress_suppression_events(self):
        """Return tuple of bindings to ignore button presses with modifiers.

        Button_1 and button_3 events with Control, Shift, or Alt, are ignored.

        """
        return (
            (EventSpec.control_buttonpress_1, self.press_break),
            (EventSpec.control_buttonpress_3, self.press_break),
            (EventSpec.shift_buttonpress_1, self.press_break),
            (EventSpec.shift_buttonpress_3, self.press_break),
            (EventSpec.alt_buttonpress_1, self.press_break),
            (EventSpec.alt_buttonpress_3, self.press_break),
        )

    # A Game widget has one Board widget and two Score widgets.  Each Score
    # widget has a Text widget but only one of these can have the focus.
    # Whichever has the focus may have item navigation bindings for it's
    # pointer, and the other one's pointer bindings are disabled.
    # The control_buttonpress_1 event is intended to give focus to the other's
    # Text widget, but is not set yet.
    def _get_primary_activity_button_events(self):
        """Return tuple of button presses and callbacks for game navigation."""
        return self._get_button_events(
            buttonpress1=self._go_to_token, buttonpress3=self._post_move_menu
        )

    # These get_xxx_events methods are used by event bind and popup creation
    # methods.

    def _get_select_move_events(self):
        """Return tuple of variation selection keypresses and callbacks."""
        return (
            (
                EventSpec.score_cycle_selection_to_next_variation,
                self._variation_cycle,
            ),
            (EventSpec.score_show_selected_variation, self._show_variation),
            (
                EventSpec.score_cancel_selection_of_variation,
                self.variation_cancel,
            ),
        )

    def _get_all_export_events(self):
        """Return tuple of PGN export keypresses and callbacks."""
        return (
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

    # These are the event bindings to traverse moves in PGN movetext.
    # The method name emphasizes the connection with implementation of main
    # purpose of CQLText, EngineText, and QueryText, widgets; rather than
    # being one of several sets of events available for PGN text files.
    def get_primary_activity_events(self):
        """Return tuple of game navigation keypresses and callbacks."""
        return (
            (EventSpec.score_show_next_in_line, self._show_next_in_line),
            (
                EventSpec.score_show_next_in_variation,
                self._show_next_in_variation,
            ),
            (EventSpec.score_show_previous_in_line, self._show_prev_in_line),
            (
                EventSpec.score_show_previous_in_variation,
                self._show_prev_in_variation,
            ),
            (EventSpec.score_show_first_in_game, self._show_first_in_game),
            (EventSpec.score_show_last_in_game, self._show_last_in_game),
            (EventSpec.score_show_first_in_line, self._show_first_in_line),
            (EventSpec.score_show_last_in_line, self._show_last_in_line),
        )

    # Analysis subclasses override method to exclude the first four items.
    # Repertoire subclasses override method to exclude the first two items.
    def _populate_export_submenu(self, submenu):
        """Populate export submenu with export event bindings."""
        self._set_popup_bindings(submenu, self._get_all_export_events())

    def _create_primary_activity_popup(self):
        """Delegate then add export submenu and return popup menu."""
        popup = super()._create_primary_activity_popup()
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_export_submenu(export_submenu)
        index = "Database"
        try:
            popup.index(index)
        except tkinter.TclError as exc:
            if str(exc) != index.join(('bad menu entry index "', '"')):
                raise
            index = tkinter.END
        popup.insert_cascade(label="Export", menu=export_submenu, index=index)
        return popup

    def _create_select_move_popup(self):
        """Create and return select move popup menu."""
        assert self.select_move_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self._set_popup_bindings(popup, self._get_select_move_events())
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_export_submenu(export_submenu)
        popup.add_cascade(label="Export", menu=export_submenu)
        # pylint message assignment-from-none is false positive.
        # However it is sensible to do an isinstance test.
        database_submenu = self._create_database_submenu(popup)
        if isinstance(database_submenu, tkinter.Menu):
            popup.add_cascade(label="Database", menu=database_submenu)
        self.select_move_popup = popup
        return popup

    def _post_move_menu(self, event=None):
        """Show the popup menu for game score navigation."""
        return self._post_menu(
            self.primary_activity_popup,
            self._create_primary_activity_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )

    def _post_move_menu_at_top_left(self, event=None):
        """Show the popup menu for game score navigation."""
        return self.post_menu_at_top_left(
            self.primary_activity_popup,
            self._create_primary_activity_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )

    def _post_select_move_menu(self, event=None):
        """Show the popup menu for variation selection in game score."""
        return self._post_menu(
            self.select_move_popup,
            self._create_select_move_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )

    def _post_select_move_menu_at_top_left(self, event=None):
        """Show the popup menu for variation selection in game score."""
        return self.post_menu_at_top_left(
            self.select_move_popup,
            self._create_select_move_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )

    def _show_first_in_game(self, event=None):
        """Display initial position of game score (usually start of game)."""
        del event
        return self._show_new_current(new_current=None)

    def _show_first_in_line(self, event=None):
        """Display initial position of line containing current move."""
        del event
        if self.current is None:
            return "break"
        if self._is_currentmove_in_main_line():
            return self._show_first_in_game()
        selected_first_move = self._select_first_move_in_line(self.current)
        self.current = selected_first_move
        self.set_current()
        self._set_variation_tags_from_currentmove()
        self.set_game_board()
        return "break"

    def _show_variation(self, event=None):
        """Enter selected variation and display its initial position."""
        del event
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self._bind_for_primary_activity()
        self._colour_variation(self.current)
        return "break"

    def _show_last_in_game(self, event=None):
        """Display final position of game score."""
        del event
        return self._show_new_current(
            new_current=self._select_last_move_played_in_game()
        )

    def _show_last_in_line(self, event=None):
        """Display final position of line containing current move."""
        del event
        if self.current is None:
            return self._show_last_in_game()
        if self._is_currentmove_in_main_line():
            return self._show_last_in_game()
        self.current = self._select_last_move_in_line()
        self._add_variation_before_move_to_colouring_tag(self.current)
        self.set_current()
        self.set_game_board()
        return "break"

    def _show_next_in_line(self, event=None):
        """Display next position of selected line."""
        del event
        if self.current is None:
            self.current = self.select_first_move_of_game()
        else:
            if self._is_variation_entered():
                self.add_move_to_moves_played_colouring_tag(self.current)
            self.current = self._select_next_move_in_line()
        self.set_current()
        self.set_game_board()
        return "break"

    def _show_next_in_variation(self, event=None):
        """Display choices if these exist or next position of selected line."""
        del event
        if self.current is None:
            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self._get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            if choice is None:
                return self._show_next_in_line()
            selection = self.get_selection_tag_for_choice(choice)

        else:
            prior = self._get_prior_to_variation_tag_of_move(self.current)
            if prior is None:
                return self._show_next_in_line()
            choice = self.get_choice_tag_for_prior(prior)
            selection = self.get_selection_tag_for_prior(prior)

        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self._cycle_selection_tag(choice, selection)

        variation = self._get_colouring_variation_tag_for_selection(selection)
        self._set_variation_selection_tags(prior, choice, selection, variation)
        if self._most_recent_bindings != NonTagBind.SELECT_VARIATION:
            self.bind_for_select_variation()
        return "break"

    def _show_prev_in_line(self, event=None):
        """Display previous position of selected line."""
        del event
        if self.current is None:
            return "break"
        if not self._is_currentmove_in_main_line():
            self._remove_currentmove_from_moves_played_in_variation()
        self.current = self._select_prev_move_in_line()
        self.set_current()
        self.set_game_board()
        return "break"

    def _show_prev_in_variation(self, event=None):
        """Display choices in previous position of selected line."""
        del event
        if self.current is None:
            return "break"
        if not self._is_currentmove_in_main_line():
            self._remove_currentmove_from_moves_played_in_variation()
            if self._is_currentmove_start_of_variation():
                self._clear_variation_colouring_tag()
                self.current = self._get_position_tag_of_previous_move()
                self.set_current()
                self.set_game_board()
                if self.current is None:
                    self.clear_moves_played_in_variation_colouring_tag()
                elif (
                    self._get_prior_to_variation_tag_of_move(self.current)
                    is None
                ):
                    return "break"
                if self._most_recent_bindings != NonTagBind.SELECT_VARIATION:
                    self.bind_for_select_variation()
                self._variation_cycle()
                return "break"
        self.current = self._select_prev_move_in_line()
        self.set_current()
        self.set_game_board()
        return "break"

    def variation_cancel(self, event=None):
        """Remove all variation highlighting."""
        del event
        if self.current is None:
            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self._get_choice_tag_of_move(
                self.select_first_move_of_game()
            )

        else:
            prior = self._get_prior_to_variation_tag_of_move(self.current)
            choice = self.get_choice_tag_for_prior(prior)
        self._clear_variation_choice_colouring_tag(choice)
        self._clear_variation_colouring_tag()
        if self.current is not None:
            if not self._is_currentmove_in_main_line():
                self._add_currentmove_variation_to_colouring_tag()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self._bind_for_primary_activity()
        return "break"

    def _variation_cycle(self, event=None):
        """Highlight next variation in choices at current position."""
        del event
        self._step_one_variation(self.current)
        return "break"

    # Methods which export *.pgn files.

    def _export_pgn_reduced_export_format(self, event=None):
        """Export PGN tags and movetext in reduced export format."""
        del event
        type_name, game_class = self.pgn_export_type
        collected_game = next(
            PGN(game_class=game_class).read_games(
                self.score.get("1.0", tkinter.END)
            )
        )
        if not collected_game.is_pgn_valid():
            tkinter.messagebox.showinfo(
                parent=self.board.ui.get_toplevel(),
                title=type_name.join(("Export ", " (reduced export format)")),
                message=type_name
                + " score is not PGN export format compliant",
            )
            return
        export_game.export_single_game_pgn_reduced_export_format(
            collected_game,
            self.board.ui.get_export_filename_for_single_item(
                type_name + " (reduced export format)", pgn=True
            ),
        )

    def _export_pgn(self, event=None):
        """Export PGN tags and movetext in export format."""
        del event
        type_name, game_class = self.pgn_export_type
        collected_game = next(
            PGN(game_class=game_class).read_games(
                self.score.get("1.0", tkinter.END)
            )
        )
        if not collected_game.is_pgn_valid():
            tkinter.messagebox.showinfo(
                parent=self.board.ui.get_toplevel(),
                title="Export " + type_name,
                message=type_name
                + " score is not PGN export format compliant",
            )
            return
        export_game.export_single_game_pgn(
            collected_game,
            self.board.ui.get_export_filename_for_single_item(
                "Game", pgn=True
            ),
        )

    def _export_pgn_no_comments_no_ravs(self, event=None):
        """Export PGN tags and moves in export format.

        Comments and RAVs are not included.

        """
        del event
        type_name, game_class = self.pgn_export_type
        collected_game = next(
            PGN(game_class=game_class).read_games(
                self.score.get("1.0", tkinter.END)
            )
        )
        if not collected_game.is_pgn_valid():
            tkinter.messagebox.showinfo(
                parent=self.board.ui.get_toplevel(),
                title=type_name.join(("Export ", " (no comments or RAVs)")),
                message=type_name
                + " score is not PGN export format compliant",
            )
            return
        export_game.export_single_game_pgn_no_comments_no_ravs(
            collected_game,
            self.board.ui.get_export_filename_for_single_item(
                type_name + " (no comments or RAVs)", pgn=True
            ),
        )

    def _export_pgn_no_comments(self, event=None):
        """Export PGN tags and movetext in export format without comments."""
        del event
        type_name, game_class = self.pgn_export_type
        collected_game = next(
            PGN(game_class=game_class).read_games(
                self.score.get("1.0", tkinter.END)
            )
        )
        if not collected_game.is_pgn_valid():
            tkinter.messagebox.showinfo(
                parent=self.board.ui.get_toplevel(),
                title=type_name.join(("Export ", " (no comments)")),
                message=type_name
                + " score is not PGN export format compliant",
            )
            return
        export_game.export_single_game_pgn_no_comments(
            collected_game,
            self.board.ui.get_export_filename_for_single_item(
                type_name + " (no comments)", pgn=True
            ),
        )

    def export_pgn_import_format(self, event=None):
        """Export PGN tags and movetext in an import format.

        Optional whitespace and indicators are removed from the export format
        and then a single space is inserted between each PGN tag or movetext
        token, except a newline is used to fit the 80 character limit on line
        length.

        """
        del event
        type_name, game_class = self.pgn_export_type
        collected_game = next(
            PGN(game_class=game_class).read_games(
                self.score.get("1.0", tkinter.END)
            )
        )
        if not collected_game.is_pgn_valid():
            tkinter.messagebox.showinfo(
                parent=self.board.ui.get_toplevel(),
                title=type_name.join(("Export ", " (import format)")),
                message=type_name
                + " score is not PGN import format compliant",
            )
            return
        export_game.export_single_game_pgn_import_format(
            collected_game,
            self.board.ui.get_export_filename_for_single_item(
                type_name + " (import format)", pgn=True
            ),
        )

    def _export_text(self, event=None):
        """Export PGN tags and movetext as text.

        Optional whitespace, move number indicators, and check indicators
        are not included.

        A single newline separates games, but newlines may appear in comments,
        as the boundaries of escaped lines, or as termination of a comment to
        end of line.

        Newlines are not inserted to keep line lengths below some limit.

        """
        del event
        type_name, game_class = self.pgn_export_type
        collected_game = next(
            PGN(game_class=game_class).read_games(
                self.score.get("1.0", tkinter.END)
            )
        )
        export_game.export_single_game_text(
            collected_game,
            self.board.ui.get_export_filename_for_single_item(
                type_name, pgn=False
            ),
        )

    # The methods which display the score of a game of chess.

    def fen_tag_square_piece_map(self):
        """Return square to piece mapping for position in game's FEN tag.

        The position was assumed to be the standard initial position of a game
        if there was no FEN tag.

        """
        try:
            return {
                square: piece
                for piece, square in self.collected_game.initial_position[0]
            }
        except TypeError as error:
            raise ScoreNoInitialPositionException(
                "No initial position: probably text has no PGN elements"
            ) from error

    def fen_tag_tuple_square_piece_map(self):
        """Return FEN tag as tuple with pieces in square to piece mapping."""
        cgip = self.collected_game.initial_position
        return (
            self.fen_tag_square_piece_map(),
            cgip[1],
            cgip[2],
            cgip[3],
            cgip[4],
            cgip[5],
        )

    def add_pgntag_to_map(self, name, value):
        r"""Add a PGN Tag, a name and value, to the game score.

        The PGN Tag consists of two editable tokens: the Tag name and the Tag
        value.  These are inserted and deleted together, never separately,
        formatted as [ <name> "<value>" ]\n.

        """
        widget = self.score
        widget.insert(tkinter.INSERT, "[")
        name_tag = self.add_text_pgntag_or_pgnvalue(
            "".join((" ", name)),
            tagset=(TAGS_VARIATIONS_COMMENTS_FONT,),
        )
        name_suffix = self.position_number
        value_tag = self.add_text_pgntag_or_pgnvalue(
            "".join(('"', value)),
            tagset=(TAGS_VARIATIONS_COMMENTS_FONT,),
            separator='"',
        )
        value_suffix = self.position_number
        widget.insert(tkinter.INSERT, " ]\n")
        widget.mark_set(START_SCORE_MARK, tkinter.INSERT)
        return ((name_suffix, name_tag), (value_suffix, value_tag))

    def add_text_pgntag_or_pgnvalue(self, token, tagset=(), separator=" "):
        """Insert token and separator text. Return start and end indicies.

        token is ' 'text or '"'text.  The trailing ' ' or '"' required in the
        PGN specification is provided as separator.  The markers surrounding
        text are not editable.

        tagset is ignored but present for compatibility with subclasses.

        """
        del tagset
        return self._insert_token_into_text(token, separator)

    def _build_nextmovetags(self):
        """Create next move references for all tags."""
        widget = self.score
        for this, value in self.previousmovetags.items():
            if widget.tag_nextrange(NAVIGATE_MOVE, *widget.tag_ranges(this)):
                previous, thisrav, previousrav = value
                nmt = self.nextmovetags.setdefault(previous, [None, []])
                if thisrav == previousrav:
                    nmt[0] = this
                else:
                    nmt[1].append(this)

    def get_range_of_prior_move(self, start):
        """Return range of PRIOR_MOVE tag before start.

        This method exists for use by _create_previousmovetag() method so
        it can be overridden in GameEdit class.  The Score class does not
        tag '(' with a PRIOR_MOVE tag, but a route to this tag exists via
        the CHOICE tag of the nearest move before the '('.

        The GameEdit class tags '('s with a PRIOR_MOVE tag in it's extended
        map_start_rav() method, which happens to break the algorithm in
        Score.get_range_of_prior_move() {this method}.

        """
        widget = self.score
        for name in widget.tag_names(
            self._get_range_for_prior_move_before_insert()[0]
        ):
            if name.startswith(CHOICE):
                return widget.tag_prevrange(
                    self.get_prior_tag_for_choice(name), start
                )
        raise ScoreRAVNoPriorMoveException("Unable to find prior move for RAV")

    def _create_previousmovetag(self, positiontag, start):
        """Create previous move tag reference for positiontag."""
        # Add code similar to this which sets up self.previousmovetags a method
        # of same name in positionscore.py to link prev-current-next positions.
        # Use these positions as starting point for colouring tags in score
        # displayed by positionscore.py

        widget = self.score
        vartag = self._game_scaffold.vartag
        tag_range = widget.tag_prevrange(vartag, start)
        if tag_range:
            self.previousmovetags[positiontag] = (
                self._get_position_tag_of_index(tag_range[0]),
                vartag,
                vartag,
            )
        else:
            varstack = list(self.varstack)
            while varstack:
                var = varstack.pop()[0]
                tag_range = widget.tag_prevrange(var, start)
                if tag_range:
                    tag_range = widget.tag_prevrange(var, tag_range[0])

                # Assume it is a '((' sequence.
                # The text for var has not been put in the widget yet since
                # it is after the RAV being processed, not before.
                # _get_range_for_prior_move_before_insert returns the inserted
                # move range in this case, and prior is found relative to
                # choice.
                else:
                    tag_range = self.get_range_of_prior_move(start)

                if tag_range:
                    self.previousmovetags[positiontag] = (
                        self._get_position_tag_of_index(tag_range[0]),
                        vartag,
                        var,
                    )
                    break
            else:
                if vartag == self.gamevartag:
                    self.previousmovetags[positiontag] = (None, None, None)
                else:
                    self.previousmovetags[positiontag] = (None, False, None)

    def _get_range_for_prior_move_before_insert(self):
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
        tpr = widget.tag_prevrange(BUILD_TAG, widget.index(tkinter.INSERT))
        while tpr:
            wtn = widget.tag_names(tpr[0])
            for tag_name in wtn:
                if tag_name.startswith(RAV_MOVES):
                    if skip_move_before_rav:
                        skip_move_before_rav = False
                        start_search = tpr[0]
                        break
                    for position_tag_name in wtn:
                        if position_tag_name.startswith(POSITION):
                            return tpr
                    return None

                # Commented rather than removed because it may be an attempt
                # to deal with ...<move1><move2>((<move3>)<move4>... style
                # RAVs.  However these break in _create_previousmovetag at
                # line 958 when processing <move3> before getting here.
                # (See code in commit to which this change was made.)
                # The other RAV styles do not get here, using the 'RAV_MOVES'
                # path instead.  This is only use of RAV_TAG in Score.
                # So RAV_TAG is converted to mark the insertion point for a
                # new RAV after an existing one, like <move4> in:
                # ...<move1><move2>(<move3>)(<move4>)<move5>... from
                # ...<move1><move2>(<move3>)<move5>... for example.
                # RAV_TAG was used in GameEdit to spot the '(' tokens which
                # start a RAV, and was thus only interested in a tag's first
                # range.
                # The RAV_TAGs did not always have the ranges as described in
                # .constants: 'rt1' has ranges for ')' only, and most RAV_TAG
                # tags refer to a '(' range only, for example.  'rt2' has the
                # '(' for 'rt1'.
                # Basically the RAV_TAG structure was rubbish.
                # if tag_name.startswith(RAV_TAG):
                #    start_search = widget.tag_ranges(tag_name)[0]
                #    skip_move_before_rav = True
                #    break

            else:
                start_search = tpr[0]
            tpr = widget.tag_prevrange(BUILD_TAG, start_search)
            if not tpr:
                return None

    def _get_position_tag_of_index(self, index):
        """Return Tk tag name if index is in a position tag."""
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _get_tags_display_order(self):
        """Return tags in alphabetic order except any chosen to be last.

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
        tags = self.collected_game.pgn_tags
        for pgn_tag in sorted(tags.items()):
            if pgn_tag[0] not in last:
                tag_values.append(pgn_tag)
        for pgn_tag_name in last:
            if pgn_tag_name in tags:
                tag_values.append((pgn_tag_name, tags[pgn_tag_name]))
        return tag_values

    def _get_choice_tag_name(self):
        """Return suffixed CHOICE tag name.

        The suffix is arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.choice_number += 1
        suffix = str(self.choice_number)
        return "".join((CHOICE, suffix))

    def get_variation_tag_name(self):
        """Return suffixed RAV_MOVES tag name.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.variation_number += 1
        return "".join((RAV_MOVES, str(self.variation_number)))

    def _get_next_positiontag_name(self):
        """Return suffixed POSITION tag name."""
        self.position_number += 1
        return "".join((POSITION, str(self.position_number)))

    @staticmethod
    def get_prior_tag_for_choice(choice):
        """Return Tk tag name for prior move with same suffix as choice."""
        return "".join((PRIOR_MOVE, choice[len(CHOICE) :]))

    def _insert_token_into_text(self, token, separator):
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

    def _insert_forced_newline_into_text(self):
        """Insert newline and tag it if widget is editable.

        A newline is added after FORCE_NEWLINE_AFTER_FULLMOVES fullmoves
        without a newline, or before various non-move tokens.  It is tagged
        if the widget is editable so deletion of the token can force deletion
        of the newline.

        """
        if self._is_text_editable:
            widget = self.score
            start = widget.index(tkinter.INSERT)
            widget.insert(tkinter.INSERT, NEWLINE_SEP)
            widget.tag_add(
                FORCED_NEWLINE_TAG, start, widget.index(tkinter.INSERT)
            )
        else:
            self.score.insert(tkinter.INSERT, NEWLINE_SEP)

    # Attempt to re-design map_game method to fit new pgn_read package.
    def map_game(self):
        """Tag and mark the displayed text of game score.

        The tags and marks are used for colouring and navigating the score.

        """
        self._game_scaffold = _ScoreScaffold(
            self.get_variation_tag_name(), self._get_choice_tag_name()
        )
        self.gamevartag = self._game_scaffold.vartag
        self.score.mark_set(START_SCORE_MARK, "1.0")
        self.score.mark_gravity(START_SCORE_MARK, tkinter.LEFT)
        game = self.collected_game
        spm = self._game_scaffold.square_piece_map
        try:
            for piece, square in game.initial_position[0]:
                spm[square] = piece
        except TypeError as error:
            raise ScoreMapToBoardException(
                "Unable to map text to board"
            ) from error
        assert len(game.pgn_text) == len(game.position_deltas)
        tags_displayed = self._map_tags_display_order()
        for text, position in zip(game.pgn_text, game.position_deltas):
            first_char = text[0]
            if first_char in "abcdefghKQRBNkqrnO":
                self._map_move_text(text, position)
            elif first_char == "[":
                if not tags_displayed:
                    self._map_tag(text)
            elif first_char == "{":
                self._map_start_comment(text)
            elif first_char == "(":
                self.map_start_rav(text, position)
            elif first_char == ")":
                self.map_end_rav(text, position)
            elif first_char in "10*":
                self.map_termination(text)
            elif first_char == ";":
                self._map_comment_to_eol(text)
            elif first_char == "$":
                self._map_glyph(text)

            # Currently ignored if present in PGN input.
            elif first_char == "%":
                self._map_escape_to_eol(text)

            # Currently not ignored if present in PGN input.
            elif first_char == "<":
                self._map_start_reserved(text)

            else:
                self.map_non_move(text)

        self._build_nextmovetags()

        # BUILD_TAG used to track moves and RAV markers during construction of
        # text.  Subclasses setup and use NAVIGATE_TOKEN for post-construction
        # comparisons of this, and other, kinds if necessary.  This class, and
        # subclasses, do not need this information after construction.
        # self.nextmovetags tracks the things BUILD_TAG is used for.  Maybe
        # change technique to use it rather than BUILD_TAG.
        self.score.tag_delete(BUILD_TAG)

        # Delete the attributes used to build the self.score Text widget.
        self._game_scaffold = None

    def _map_move_text(self, token, position):
        """Add token to game text. Set navigation tags. Return token range.

        self._start_latest_move and self._end_latest_move are set to range
        occupied by token text so that variation tags can be constructed as
        more moves are processed.

        """
        scaffold = self._game_scaffold
        self._modify_square_piece_map(position)
        widget = self.score
        positiontag = self._get_next_positiontag_name()
        next_position = position[1]
        self.tagpositionmap[positiontag] = (
            scaffold.square_piece_map.copy(),
        ) + next_position[1:]
        fwa = next_position[1] == FEN_WHITE_ACTIVE
        if not fwa:
            scaffold.force_newline += 1
        if scaffold.force_newline > FORCE_NEWLINE_AFTER_FULLMOVES:
            self._insert_forced_newline_into_text()
            scaffold.force_newline = 1
        if not fwa:
            start, end, sepend = self._insert_token_into_text(
                str(next_position[5]) + ".", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            if self._is_text_editable or scaffold.force_newline == 1:
                widget.tag_add(FORCED_INDENT_TAG, start, end)
        elif scaffold.next_move_is_choice:
            start, end, sepend = self._insert_token_into_text(
                str(position[0][5]) + "...", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            if self._is_text_editable or scaffold.force_newline == 1:
                widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self._insert_token_into_text(token, SPACE_SEP)
        if self._is_text_editable or scaffold.force_newline == 1:
            widget.tag_add(FORCED_INDENT_TAG, start, end)
        for tag in positiontag, scaffold.vartag, NAVIGATE_MOVE, BUILD_TAG:
            widget.tag_add(tag, start, end)
        if scaffold.vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        widget.tag_add("".join((RAV_SEP, scaffold.vartag)), start, sepend)
        if scaffold.next_move_is_choice:
            widget.tag_add(ALL_CHOICES, start, end)

            # A START_RAV is needed to define and set choicetag and set
            # next_move_is_choice True.  There cannot be a START_RAV
            # until a MOVE_TEXT has occured: from PGN grammar.
            # So define and set choicetag then increment choice_number
            # in 'type_ is START_RAV' processing rather than other way
            # round, with initialization, to avoid tag name clutter.
            widget.tag_add(scaffold.choicetag, start, end)
            scaffold.next_move_is_choice = False
            scaffold.unresolved_choice_count -= 1

        scaffold.start_latest_move = start
        scaffold.end_latest_move = end
        self._create_previousmovetag(positiontag, start)
        return start, end, sepend

    def map_start_rav(self, token, position):
        """Add token to game text.  Return range and prior.

        Variation tags are set for guiding move navigation. self._vartag
        self._token_position and self._choicetag are placed on a stack for
        restoration at the end of the variation.
        self._next_move_is_choice is set True indicating that the next move
        is the default selection when choosing a variation.

        The _square_piece_map is reset from position.

        """
        scaffold = self._game_scaffold
        self._set_square_piece_map(position)
        widget = self.score
        if not widget.tag_nextrange(
            ALL_CHOICES, scaffold.start_latest_move, scaffold.end_latest_move
        ):
            # start_latest_move will be the second move, at earliest,
            # in current variation except if it is the first move in
            # the game.  Thus the move before start_latest_move using
            # tag_prevrange() can be tagged as the move creating the
            # position in which the choice of moves occurs.
            scaffold.choicetag = self._get_choice_tag_name()
            widget.tag_add(
                "".join((SELECTION, str(self.choice_number))),
                scaffold.start_latest_move,
                scaffold.end_latest_move,
            )
            prior = self._get_range_for_prior_move_before_insert()
            if prior:
                widget.tag_add(
                    "".join((PRIOR_MOVE, str(self.choice_number))), *prior
                )

        widget.tag_add(
            ALL_CHOICES, scaffold.start_latest_move, scaffold.end_latest_move
        )
        widget.tag_add(
            scaffold.choicetag,
            scaffold.start_latest_move,
            scaffold.end_latest_move,
        )
        self.varstack.append((scaffold.vartag, scaffold.token_position))
        self.choicestack.append(scaffold.choicetag)
        scaffold.vartag = self.get_variation_tag_name()
        nttpr = widget.tag_prevrange(BUILD_TAG, widget.index(tkinter.END))
        if nttpr:
            if widget.get(*nttpr) != "(":
                self._insert_forced_newline_into_text()
                scaffold.force_newline = 0
        else:
            self._insert_forced_newline_into_text()
            scaffold.force_newline = 0
        start, end, sepend = self._insert_token_into_text(token, SPACE_SEP)
        widget.tag_add(BUILD_TAG, start, end)
        scaffold.next_move_is_choice = True
        scaffold.unresolved_choice_count += 1
        return start, end, sepend

    def map_end_rav(self, token, position):
        """Add token to game text.  Return token range.

        Variation tags are set for guiding move navigation. scaffold.vartag
        scaffold.token_position and scaffold.choicetag are restored from the
        stack for restoration at the end of the variation.
        (scaffold.start_latest_move, scaffold.end_latest_move) is set to the
        range of the move which the first move of the variation replaced.

        The _square_piece_map is reset from position.

        """
        scaffold = self._game_scaffold
        if scaffold.unresolved_choice_count:
            scaffold.next_move_is_choice = True

        # ValueError exception has happened if and only if opening an invalid
        # game generated from an arbitrary text file completely unlike a PGN
        # file.  Probably no valid PGN tokens at all must be in the file to
        # cause this exception.
        try:
            (
                scaffold.start_latest_move,
                scaffold.end_latest_move,
            ) = self.score.tag_prevrange(ALL_CHOICES, tkinter.END)
        except ValueError:
            return tkinter.END, tkinter.END, tkinter.END

        self._set_square_piece_map(position)
        start, end, sepend = self._insert_token_into_text(token, SPACE_SEP)
        self.score.tag_add(BUILD_TAG, start, end)
        scaffold.vartag, scaffold.token_position = self.varstack.pop()
        scaffold.choicetag = self.choicestack.pop()
        scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return start, end, sepend

    def _map_tag(self, token):
        """Add PGN Tag to game text."""
        tag_name, tag_value = token[1:-1].split('"', 1)
        tag_value = tag_value[:-1]
        self.add_pgntag_to_map(tag_name, tag_value)

    def _map_tags_display_order(self):
        """Add PGN Tags to game text."""
        tag_values = self._get_tags_display_order()
        self.tagpositionmap[None] = self.fen_tag_tuple_square_piece_map()
        if tag_values is None:
            return False
        for pgn_tag in tag_values:
            self.add_pgntag_to_map(*pgn_tag)
        return True

    def map_termination(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self.score.insert(tkinter.INSERT, NEWLINE_SEP)
        return self._insert_token_into_text(token, NEWLINE_SEP)

    def _map_start_comment(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self._insert_forced_newline_into_text()
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return self._insert_token_into_text(token, SPACE_SEP)

    # newline_prefix argument avoids arguments-differ message from pylint.
    def _map_initial_comment_to_eol(self, token, newline_prefix):
        """Add token to game text. position is ignored. Return token range."""
        del newline_prefix
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token[:-1])  # token)
        end = widget.index(tkinter.INSERT)  # + ' -1 chars')
        # widget.insert(tkinter.INSERT, NULL_SEP)
        return start, end, widget.index(tkinter.INSERT)

    def _map_comment_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self._insert_forced_newline_into_text()
        token_indicies = self._map_initial_comment_to_eol(token, False)
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return token_indicies

    # newline_prefix argument avoids arguments-differ message from pylint.
    def _map_initial_escape_to_eol(self, token, newline_prefix):
        """Add token to game text. position is ignored. Return token range."""
        del newline_prefix
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token[:-1])
        end = widget.index(tkinter.INSERT)  # + ' -1 chars')

        # First character of this token is the newline to be tagged.
        # If necessary it is probably safe to use the commented version
        # because a forced newline will appear after the escaped line's EOL.
        # widget.tag_add(
        #     FORCED_NEWLINE_TAG, start, widget.index(tkinter.INSERT)
        # )
        widget.tag_add(FORCED_NEWLINE_TAG, start)

        # widget.insert(tkinter.INSERT, NULL_SEP)
        return start, end, widget.index(tkinter.INSERT)

    def _map_escape_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        token_indicies = self._map_initial_escape_to_eol(token, False)
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return token_indicies

    def map_integer(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        del position
        return self._insert_token_into_text(token, SPACE_SEP)

    def _map_glyph(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self._insert_token_into_text(token, SPACE_SEP)

    def map_period(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        del position
        return self._insert_token_into_text(token, SPACE_SEP)

    def _map_start_reserved(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self._insert_forced_newline_into_text()
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return self._insert_token_into_text(token, SPACE_SEP)

    def map_non_move(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self._insert_token_into_text(token, SPACE_SEP)

    def _set_square_piece_map(self, position):
        assert len(position) == 1
        spm = self._game_scaffold.square_piece_map
        spm.clear()
        for piece, square in position[0][0]:
            spm[square] = piece

    def _modify_square_piece_map(self, position):
        assert len(position) == 2
        spm = self._game_scaffold.square_piece_map
        for square, piece in position[0][0]:
            del spm[square]
        for square, piece in position[1][0]:
            spm[square] = piece

    # The methods which support event handlers.

    def _see_first_move(self):
        """Make first move visible on navigation to initial position.

        Current move is always made visible but no current move defined
        for initial position.
        """
        self.score.see(START_SCORE_MARK)

    def set_game_board(self):
        """Show position after highlighted move and return True if it exists.

        True means further processing appropriate to a game score can be done,
        while None means a problem occurred and the first position in score
        is displayed as a default.

        The setup_game_board() in AnalysisScore always returns False.

        """
        if self.current is None:
            try:
                self.board.set_board(self.fen_tag_square_piece_map())
            except ScoreNoGameException:
                return False
            self._see_first_move()
        else:
            try:
                self.board.set_board(self.tagpositionmap[self.current][0])
            except TypeError:
                self.board.set_board(self.fen_tag_square_piece_map())
                self.score.see(self.score.tag_ranges(self.current)[0])
                return None
            self.score.see(self.score.tag_ranges(self.current)[0])
        self.set_game_list()
        return True

    def clear_current_range(self):
        """Remove existing MOVE_TAG ranges."""
        tag_range = self.score.tag_ranges(MOVE_TAG)
        if tag_range:
            self.score.tag_remove(MOVE_TAG, tag_range[0], tag_range[1])

    def clear_moves_played_in_variation_colouring_tag(self):
        """Clear the colouring tag for moves played in variation."""
        self.score.tag_remove(VARIATION_TAG, "1.0", tkinter.END)

    def _clear_choice_colouring_tag(self):
        """Clear the colouring tag for variation choice."""
        self.score.tag_remove(ALTERNATIVE_MOVE_TAG, "1.0", tkinter.END)

    def _clear_variation_colouring_tag(self):
        """Clear the colouring tag for moves in variation."""
        self.score.tag_remove(LINE_TAG, "1.0", tkinter.END)
        self.score.tag_remove(LINE_END_TAG, "1.0", tkinter.END)

    def _get_position_for_current(self):
        """Return position associated with the current range."""
        if self.current is None:
            return self.tagpositionmap[None]
        return self._get_position_for_text_index(
            self.score.tag_ranges(self.current)[0]
        )

    def _get_position_for_text_index(self, index):
        """Return position associated with index in game score text widget."""
        tagpositionmap = self.tagpositionmap
        for tag in self.score.tag_names(index):
            if tag in tagpositionmap:
                return tagpositionmap[tag]
        return None

    def _get_position_key(self):
        """Return position key string for position associated with current."""
        try:
            # Hack.  _get_position_for_current returns None on next/prev token
            # navigation at end of imported game with errors when editing.
            return get_position_string(*self._get_position_for_current())

        except TypeError:
            return False

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
        tag_range = self._set_current_range()
        if tag_range:
            self._set_move_tag(tag_range[0], tag_range[1])
            return tag_range
        return None

    def _set_current_range(self):
        """Remove existing MOVE_TAG ranges and add self.currentmove ranges.

        Subclasses may adjust the MOVE_TAG range if the required colouring
        range of the item is different.  For example just <text> in {<text>}
        which is a PGN comment where <text> may be null after editing.

        The adjusted range must be a subset of self.currentmove range.

        """
        self.clear_current_range()
        if self.current is None:
            return None
        tag_range = self.score.tag_ranges(self.current)
        if not tag_range:
            return None
        return tag_range

    def _set_move_tag(self, start, end):
        """Add range start to end to MOVE_TAG (which is expected to be empty).

        Assumption is that _set_current_range has been called and MOVE_TAG is
        still empty following that call.

        """
        self.score.tag_add(MOVE_TAG, start, end)

    def _show_new_current(self, new_current=None):
        """Set current to new item and adjust display."""
        self.clear_moves_played_in_variation_colouring_tag()
        self._clear_choice_colouring_tag()
        self._clear_variation_colouring_tag()
        self.current = new_current
        self.set_current()
        self.set_game_board()
        return "break"

    def _show_item(self, new_item=None):
        """Display new item if not None."""
        if not new_item:
            return "break"
        return self._show_new_current(new_current=new_item)

    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a game including switching from
        one game to another.

        """
        grid = self.itemgrid
        if grid is None:
            return
        if grid.get_database() is not None:
            newpartialkey = self._get_position_key()
            if grid.partial != newpartialkey:
                grid.partial = newpartialkey
                grid.rows = 1
                grid.close_client_cursor()
                grid.datasource.get_full_position_games(newpartialkey)
                grid.load_new_index()

    def add_move_to_moves_played_colouring_tag(self, move):
        """Add move to colouring tag for moves played in variation."""
        widget = self.score
        tag_range = widget.tag_nextrange(move, "1.0")
        widget.tag_add(VARIATION_TAG, tag_range[0], tag_range[1])

    def _is_index_in_main_line(self, index):
        """Return True if index is in the main line tag."""
        return bool(
            self.score.tag_nextrange(
                self.gamevartag, index, "".join((str(index), "+1 chars"))
            )
        )

    def _is_move_in_main_line(self, move):
        """Return True if move is in the main line."""
        return self._is_index_in_main_line(self.score.tag_ranges(move)[0])

    def _add_variation_before_move_to_colouring_tag(self, move):
        """Add variation before current move to moves played colouring tag."""
        widget = self.score
        index = widget.tag_nextrange(move, "1.0")[0]
        for ctn in widget.tag_names(index):
            if ctn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(ctn, "1.0", index)
                while tag_range:
                    widget.tag_add(VARIATION_TAG, tag_range[0], tag_range[1])
                    tag_range = widget.tag_nextrange(ctn, tag_range[1], index)
                return

    def _select_first_move_in_line(self, move):
        """Return tag name for first move in rav containing move."""
        widget = self.score
        tag_range = widget.tag_ranges(move)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(oldtn, "1.0")
                break
        else:
            return None
        if not tag_range:
            return move
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _get_choice_tag_of_index(self, index):
        """Return Tk tag name if index is in a choice tag."""
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(CHOICE):
                return tag_name
        return None

    def _get_choice_tag_of_move(self, move):
        """Return Tk tag name if move is first move of a variation choice."""
        if move:
            return self._get_choice_tag_of_index(
                self.score.tag_ranges(move)[0]
            )
        return None

    @staticmethod
    def get_selection_tag_for_choice(choice):
        """Return Tk tag name for selection with same suffix as choice."""
        return "".join((SELECTION, choice[len(CHOICE) :]))

    def _add_tag_ranges_to_color_tag(self, tag, colortag):
        """Add the index ranges in tag to colortag.

        Tkinter Text.tag_add() takes two indicies as arguments rather than
        the list of 2n indicies, for n ranges, accepted by Tk tag_add.
        So do it a long way.

        """
        add = self.score.tag_add
        tag_range = list(self.score.tag_ranges(tag))
        while tag_range:
            start = tag_range.pop(0)
            end = tag_range.pop(0)
            add(colortag, start, end)

    def _add_currentmove_variation_to_colouring_tag(self):
        """Add current move variation to selected variation colouring tag."""
        widget = self.score
        for tag_name in widget.tag_names(
            widget.tag_nextrange(self.current, "1.0")[0]
        ):
            if tag_name.startswith(RAV_SEP):
                self._add_tag_ranges_to_color_tag(tag_name, LINE_TAG)
                widget.tag_add(
                    LINE_END_TAG,
                    "".join(
                        (
                            str(
                                widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]
                            ),
                            "-1 chars",
                        )
                    ),
                )
                return

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
        if not self._is_move_in_main_line(move):
            self._add_currentmove_variation_to_colouring_tag()
        while not self._is_move_in_main_line(move):
            self.add_move_to_moves_played_colouring_tag(move)
            self._add_variation_before_move_to_colouring_tag(move)
            first_move_of_variation = self._select_first_move_in_line(move)
            choice = self._get_choice_tag_of_move(first_move_of_variation)
            prior = self.score.tag_ranges(
                self.get_prior_tag_for_choice(choice)
            )
            if not prior:
                move = None
                break
            move = self._get_position_tag_of_index(prior[0])
            selection = self.get_selection_tag_for_choice(choice)
            if selection:
                self.score.tag_remove(selection, "1.0", tkinter.END)
                self.score.tag_add(
                    selection, *self.score.tag_ranges(first_move_of_variation)
                )
        if self.score.tag_nextrange(VARIATION_TAG, "1.0"):
            if move:
                self.add_move_to_moves_played_colouring_tag(move)

    # If pointer click location is between last PGN Tag and first move in
    # movetext, it would be reasonable to allow the call to reposition at
    # start of game.  Then there is a pointer click option equivalent to
    # the popup menu and keypress ways of getting to start of game.
    def go_to_move(self, index):
        """Show position for move text at index."""
        widget = self.score
        move = widget.tag_nextrange(NAVIGATE_MOVE, index)
        if not move:
            move = widget.tag_prevrange(NAVIGATE_MOVE, index)
            if not move:
                return None
            if widget.compare(move[1], "<", index):
                return None
        elif widget.compare(move[0], ">", index):
            move = widget.tag_prevrange(NAVIGATE_MOVE, move[0])
            if not move:
                return None
            if widget.compare(move[1], "<", index):
                return None
        selected_move = self._get_position_tag_of_index(index)
        if selected_move:
            self.clear_moves_played_in_variation_colouring_tag()
            self._clear_choice_colouring_tag()
            self._clear_variation_colouring_tag()
            self.current = selected_move
            self.set_current()
            self.apply_colouring_to_variation_back_to_main_line()
            self.set_game_board()
            return True
        return None

    def _go_to_token(self, event=None):
        """Highlight token at pointer in active item, and set position."""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return "break"
        return self.go_to_move(
            self.score.index("".join(("@", str(event.x), ",", str(event.y))))
        )

    def _is_game_in_text_edit_mode(self):
        """Return True if current state of score widget is 'normal'."""
        return self.score.cget("state") == tkinter.NORMAL

    def _cycle_selection_tag(self, choice, selection):
        """Cycle selection one range round the choice ranges if coloured.

        The choice ranges are coloured if they are on ALTERNATIVE_MOVE_TAG.

        """
        if choice is None:
            return
        if selection is None:
            return
        widget = self.score
        choice_tnr = widget.tag_nextrange(choice, "1.0")
        if not choice_tnr:
            return
        if not widget.tag_nextrange(ALTERNATIVE_MOVE_TAG, choice_tnr[0]):
            return
        selection_tnr = widget.tag_nextrange(
            choice, widget.tag_nextrange(selection, "1.0")[1]
        )
        widget.tag_remove(selection, "1.0", tkinter.END)
        if selection_tnr:
            widget.tag_add(selection, selection_tnr[0], selection_tnr[1])
        else:
            widget.tag_add(selection, choice_tnr[0], choice_tnr[1])

    def _get_prior_to_variation_tag_of_index(self, index):
        """Return Tk tag name if index is in a prior to variation tag."""
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(PRIOR_MOVE):
                return tag_name
        return None

    def _get_colouring_variation_tag_of_index(self, index):
        """Return Tk tag name if index is in a varsep tag.

        RAV_SEP for colouring (RAV_MOVES for editing).

        """
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(RAV_SEP):
                return tag_name
        return None

    @staticmethod
    def get_choice_tag_for_prior(prior):
        """Return Tk tag name for choice with same suffix as prior."""
        return "".join((CHOICE, prior[len(PRIOR_MOVE) :]))

    @staticmethod
    def get_selection_tag_for_prior(prior):
        """Return Tk tag name for selection with same suffix as prior."""
        return "".join((SELECTION, prior[len(PRIOR_MOVE) :]))

    def _is_variation_entered(self):
        """Return True if currentmove is, or about to be, in variation.

        Colour tag LINE_TAG will contain at least one range if a variation
        has been entered; in particular when self.currentmove is about to
        be set to the first move of the variation at which point no other
        way of determining this is easy.  In fact LINE_TAG is populated
        ahead of time in this case to enable the test.

        """
        if self.score.tag_nextrange(LINE_TAG, "1.0"):
            return True
        return False

    def _get_position_tag_of_previous_move(self):
        """Return name of tag of move played prior to current move in line.

        Assumes self.currentmove has been removed from VARIATION_TAG.

        """
        widget = self.score
        tag_range = widget.tag_prevrange(VARIATION_TAG, tkinter.END)
        if not tag_range:
            # Should be so just for variations on the first move of game
            return None

        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _set_next_variation_move_played_colouring_tag(self, move):
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
        for vtn in widget.tag_names(widget.tag_nextrange(move, "1.0")[0]):
            if vtn.startswith(RAV_SEP):
                tag_range = widget.tag_nextrange(
                    NAVIGATE_MOVE, widget.tag_nextrange(vtn, "1.0")[0]
                )
                widget.tag_add(VARIATION_TAG, tag_range[0], tag_range[1])
                break

    def _remove_tag_ranges_from_color_tag(self, tag, colortag):
        """Remove the index ranges in tag from colortag.

        Tkinter Text.tag_add() takes two indicies as arguments rather than
        the list of 2n indicies, for n ranges, accepted by Tk tag_remove.
        So do it a long way.

        """
        remove = self.score.tag_remove
        tag_range = list(self.score.tag_ranges(tag))
        while tag_range:
            start = tag_range.pop(0)
            end = tag_range.pop(0)
            remove(colortag, start, end)

    def _select_move_for_start_of_analysis(self, movetag=MOVE_TAG):
        """Return name of tag for move to which analysis will be attached.

        Differs from _select_next_move_in_line() by returning None if at last
        position in line or game, rather than self.current.

        """
        widget = self.score
        tag_range = widget.tag_ranges(movetag)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(
                    oldtn, "".join((str(tag_range[0]), "+1 chars"))
                )
                break
        else:
            return None
        if not tag_range:
            return None
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _colour_variation(self, move):
        """Colour variation and display its initial position.

        The current move is coloured to indicate it is a move played to reach
        the position in the variation.  Colour is removed from any moves to
        enter alternative variations.  The move played to enter the variation
        becomes the current move and is coloured to indicate that it is in a
        variation.

        """
        if move is None:
            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self._get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            selection = self.get_selection_tag_for_choice(choice)

        else:
            prior = self._get_prior_to_variation_tag_of_move(move)
            choice = self.get_choice_tag_for_prior(prior)
            selection = self.get_selection_tag_for_prior(prior)
        self._clear_variation_choice_colouring_tag(choice)
        selected_first_move = self._select_first_move_of_selected_line(
            selection
        )
        if self._is_move_in_main_line(selected_first_move):
            self.clear_moves_played_in_variation_colouring_tag()
            self._clear_variation_colouring_tag()
        elif move is None:
            self._set_next_variation_move_played_colouring_tag(selection)
        else:
            self.add_move_to_moves_played_colouring_tag(move)
        self.current = selected_first_move
        self.set_current()
        self.set_game_board()

    def _see_current_move(self):
        """Make current move visible and default to first move."""
        if self.current:
            self.score.see(self.score.tag_ranges(self.current)[0])
        else:
            self._see_first_move()

    def _step_one_variation(self, move):
        """Highlight next variation in choices at current position."""
        if move is None:
            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self._get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            selection = self.get_selection_tag_for_choice(choice)

        else:
            prior = self._get_prior_to_variation_tag_of_move(move)
            choice = self.get_choice_tag_for_prior(prior)
            selection = self.get_selection_tag_for_prior(prior)

        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self._cycle_selection_tag(choice, selection)

        variation = self._get_colouring_variation_tag_for_selection(selection)
        self._set_variation_selection_tags(prior, choice, selection, variation)
        return variation

    def _clear_variation_choice_colouring_tag(self, first_moves_in_variations):
        """Remove ranges in first_moves_in_variations from colour tag.

        The colour tag is ALTERNATIVE_MOVE_TAG which should contain just the
        ranges that exist in first_moves_in_variation.  However do what the
        headline says rather than delete everything in an attempt to ensure
        correctness.

        """
        self._remove_tag_ranges_from_color_tag(
            first_moves_in_variations, ALTERNATIVE_MOVE_TAG
        )

    def _get_range_next_move(self):
        """Return range of move after current move in variation."""
        if self.current is None:
            tnr = self.score.tag_nextrange(NAVIGATE_MOVE, "1.0")
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
                self.previousmovetags[self.current][0]
            ]
        except KeyError:
            # The result at the end of an editable game score for example
            prevpos = None

        currpos = self.tagpositionmap[self.current]
        npc = self.nextmovetags.get(self.current)
        if npc is None:
            nextpos = None
        else:
            try:
                nextpos = self.tagpositionmap[npc[0]]
            except KeyError:
                nextpos = None
        return (prevpos, currpos, nextpos)

    def _get_prior_to_variation_tag_of_move(self, move):
        """Return Tk tag name if currentmove is prior to a variation."""
        return self._get_prior_to_variation_tag_of_index(
            self.score.tag_ranges(move)[0]
        )

    def _get_colouring_variation_tag_for_selection(self, selection):
        """Return Tk tag name for variation associated with selection."""
        return self._get_colouring_variation_tag_of_index(
            self.score.tag_ranges(selection)[0]
        )

    def _get_current_tag_and_mark_names(self):
        """Return suffixed POSITION and TOKEN tag and TOKEN_MARK mark names."""
        suffix = str(self.position_number)
        return ["".join((t, suffix)) for t in (POSITION, TOKEN, TOKEN_MARK)]

    def _get_tag_and_mark_names(self):
        """Return suffixed POSITION and TOKEN tag and TOKEN_MARK mark names.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        A TOKEN_MARK name is generated for each token but the mark will be
        created only for editable tokens.

        """
        self.position_number += 1
        suffix = str(self.position_number)
        return ["".join((t, suffix)) for t in (POSITION, TOKEN, TOKEN_MARK)]

    def _is_currentmove_in_main_line(self):
        """Return True if currentmove is in the main line tag."""
        return self._is_index_in_main_line(
            self.score.tag_ranges(self.current)[0]
        )

    def _is_currentmove_start_of_variation(self):
        """Return True if currentmove is at start of a variation tag."""
        widget = self.score
        index = widget.tag_ranges(self.current)[0]
        for tag_name in widget.tag_names(index):
            if tag_name.startswith(RAV_SEP):
                return not bool(self.score.tag_prevrange(tag_name, index))
        return None

    def is_index_of_variation_next_move_in_choice(self):
        """Return True if index is in a choice of variations tag."""
        tag_range = self._get_range_next_move()
        if not tag_range:
            return False
        for tag_name in self.score.tag_names(tag_range[0]):
            if tag_name.startswith(CHOICE):
                return True
        return False

    def _remove_currentmove_from_moves_played_in_variation(self):
        """Remove current move from moves played in variation colouring tag."""
        widget = self.score
        tag_range = widget.tag_nextrange(self.current, "1.0")
        widget.tag_remove(VARIATION_TAG, tag_range[0], tag_range[1])

    def select_first_move_of_game(self):
        """Return name of tag associated with first move of game."""
        widget = self.score
        try:
            index = widget.tag_nextrange(self.gamevartag, "1.0")[0]
        except IndexError:
            return None
        for tag_name in widget.tag_names(index):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _select_first_move_of_selected_line(self, selection):
        """Return name of tag associated with first move of line."""
        widget = self.score
        for tag_name in widget.tag_names(widget.tag_ranges(selection)[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_last_move_of_selected_line(self, selection):
        """Return name of tag associated with last move of line."""
        widget = self.score
        for tag_name in widget.tag_names(widget.tag_ranges(selection)[-2]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _select_last_move_played_in_game(self):
        """Return name of tag associated with last move played in game."""
        widget = self.score
        try:
            index = widget.tag_prevrange(self.gamevartag, tkinter.END)[0]
        except IndexError:
            return None
        for tag_name in widget.tag_names(index):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _select_last_move_in_line(self):
        """Return name of tag associated with last move in line."""
        widget = self.score
        tag_range = widget.tag_ranges(MOVE_TAG)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_prevrange(oldtn, tkinter.END)
                break
        else:
            return None
        if not tag_range:
            return self.current
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _select_next_move_in_line(self, movetag=MOVE_TAG):
        """Return name of tag associated with next move in line."""
        widget = self.score
        tag_range = widget.tag_ranges(movetag)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(
                    oldtn, "".join((str(tag_range[0]), "+1 chars"))
                )
                break
        else:
            return None
        if not tag_range:
            return self.current
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _select_prev_move_in_line(self):
        """Return name of tag associated with previous move in line."""
        widget = self.score
        oldtr = widget.tag_ranges(MOVE_TAG)
        if not oldtr:
            return None
        for oldtn in widget.tag_names(oldtr[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_prevrange(oldtn, oldtr[0])
                break
        else:
            return None
        if not tag_range:
            if widget.tag_prevrange(NAVIGATE_MOVE, oldtr[0]):
                return self.current
            return None
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def _set_variation_selection_tags(
        self,
        move_prior_to_choice,
        first_moves_in_variations,
        selected_first_move,
        moves_in_variation,
    ):
        """Replace existing ranges on color tags with ranges in arguments.

        The replacement is applied to the right of move_prior_to_choice,
        which is usually the same as current move.  In practice this only
        effects moves_in_variation because the moves to left of current move
        are not present unless the variation is the main line.

        """
        # ####### warning ######
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
        # ######################
        #
        # Now it may be possible to use START_SCORE_MARK rather than '1.0'
        #
        # ######################

        del selected_first_move
        widget = self.score
        if move_prior_to_choice is None:
            index = "1.0"
        else:
            index = widget.tag_ranges(move_prior_to_choice)[0]

        # Remove current move from VARIATION_TAG (for _show_prev_in_variation)
        if move_prior_to_choice:
            widget.tag_remove(VARIATION_TAG, index, tkinter.END)

        widget.tag_remove(ALTERNATIVE_MOVE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_END_TAG, index, tkinter.END)
        self._add_tag_ranges_to_color_tag(
            first_moves_in_variations, ALTERNATIVE_MOVE_TAG
        )
        self._add_tag_ranges_to_color_tag(moves_in_variation, LINE_TAG)

        # In all cases but one there is nothing to remove.  But if the choice
        # includes a move played in the game LINE_TAG contains all these moves
        # when the move played is the selection.
        widget.tag_remove(
            LINE_TAG,
            "1.0",
            widget.tag_nextrange(first_moves_in_variations, "1.0")[0],
        )

        widget.tag_add(
            LINE_END_TAG,
            "".join(
                (
                    str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                    "-1 chars",
                )
            ),
        )

    def _set_variation_tags_from_currentmove(self):
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
            self._get_colouring_variation_tag_of_index(index), LINE_TAG
        )
        widget.tag_add(
            LINE_END_TAG,
            "".join(
                (
                    str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                    "-1 chars",
                )
            ),
        )

    def _get_range_next_move_in_variation(self):
        """Return range of move after current move in variation."""
        widget = self.score
        tag_range = widget.tag_ranges(self.current)
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(
                    tag_name, "".join((str(tag_range[0]), "+1 chars"))
                )
                break
        else:
            return None
        if not tag_range:
            return None
        return tag_range

    def _get_move_for_start_of_analysis(self):
        """Return PGN text of move to which analysis will be RAVs.

        Default to first move played in game, or '' if no moves played, or ''
        if current position is last in line or game.

        """
        if self.current is None:
            tag = self.select_first_move_of_game()
        else:
            tag = self._select_move_for_start_of_analysis()
        if tag is None:
            return ""
        tag_range = self.score.tag_ranges(tag)
        if not tag_range:
            return ""
        return self.score.get(*tag_range)
