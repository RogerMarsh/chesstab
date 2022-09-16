# score.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class with event handlers to control display of a chess game.

The Score class is not used directly to display games.  Subclasses of Score,
principally Game and Repertoire, do that.  Those classes arrange for display
of any chess engine analysis of positions in the game: alongside the game
score and sharing the game's board.

"""

import tkinter

from pgn_read.core.parser import PGN

from .eventspec import EventSpec
from .blanktext import BlankText, NonTagBind
from .sharedtext import SharedTextScore
from .scoreshow import ScoreShow
from ..core import export_game


class ScoreNoGameException(Exception):
    """Raise to indicate non-PGN text after Game Termination Marker.

    The ScoreNoGameException is intended to catch cases where a file
    claiming to be a PGN file contains text with little resemblance to
    the PGN standard between a Game Termination Marker and a PGN Tag or
    a move description like Ba4.  For example 'anytext*anytextBa4anytext'
    or 'anytext0-1anytext[tagname"tagvalue"]anytext'.

    """


class Score(ScoreShow, SharedTextScore):
    """Event handlers for the chess game widget.

    The stuff specific to game scores is in ScoreShow; some stuff which is
    identical in non-game score context is in SharedTextScore.  Stuff
    shared via BlankText is available because ScoreWidget is a sublass of
    BlankText.
    """

    def set_event_bindings_board(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        sbbv = self.board.boardsquares.values
        for sequence, function in bindings:
            stef = ste(function) if switch and function else ""
            for widget in sbbv():
                widget.bind(sequence[0], stef)

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
        self.set_select_variation_bindings(switch=True)

    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = BlankText.token_bind_method.copy()
    token_bind_method[NonTagBind.SELECT_VARIATION] = bind_for_select_variation

    # Renamed from '_bind_viewmode' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    def set_primary_activity_bindings(self, switch=True):
        """Switch bindings for traversing moves on or off."""
        self.set_event_bindings_score(
            self.get_primary_activity_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_f10_popup_events(
                self.post_move_menu_at_top_left, self.post_move_menu
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_all_export_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_primary_activity_button_events(), switch=switch
        )

    # Renamed from '_bind_select_variation' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    def set_select_variation_bindings(self, switch=True):
        """Switch bindings for selecting a variation on or off."""
        self.set_event_bindings_score(
            self.get_select_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_f10_popup_events(
                self.post_select_move_menu_at_top_left,
                self.post_select_move_menu,
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_button_events(
                buttonpress1=self.variation_cancel,
                buttonpress3=self.post_select_move_menu,
            ),
            switch=switch,
        )

    # This method may have independence from set_primary_activity_bindings
    # when the control_buttonpress_1 event is fired.
    # (So there should be a 'select_variation' version too?)
    # Renamed from bind_score_pointer_for_board_navigation to fit current use.
    def set_score_pointer_item_navigation_bindings(self, switch):
        """Set or unset pointer bindings for game navigation."""
        self.set_event_bindings_score(
            self.get_primary_activity_button_events(), switch=switch
        )

    # Not yet used.
    # Recently added to game.py but moved here because it makes more sense to
    # do the work in the (game).score or (game.analysis).score object than
    # choose which is wanted in the (game) object.
    # set_board_pointer_widget_navigation_bindings is likely to follow.
    # There is no equivalent of set_select_variation_bindings to contain this.
    def set_board_pointer_select_variation_bindings(self, switch):
        """Enable or disable bindings for variation selection."""
        self.set_event_bindings_board(
            self.get_modifier_buttonpress_suppression_events(), switch=switch
        )
        self.set_event_bindings_board(
            (
                (EventSpec.buttonpress_1, self.variation_cancel),
                (EventSpec.buttonpress_3, self.show_next_in_variation),
                (EventSpec.shift_buttonpress_3, self.show_variation),
            ),
            switch=switch,
        )

    # There is no equivalent of set_primary_activity_bindings to contain this.
    def set_board_pointer_move_bindings(self, switch):
        """Enable or disable bindings for game navigation."""
        self.set_event_bindings_board(
            self.get_modifier_buttonpress_suppression_events(), switch=switch
        )
        self.set_event_bindings_board(
            (
                (EventSpec.buttonpress_1, self.show_prev_in_line),
                (EventSpec.shift_buttonpress_1, self.show_prev_in_variation),
                (EventSpec.buttonpress_3, self.show_next_in_variation),
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
    def get_modifier_buttonpress_suppression_events(self):
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
    def get_primary_activity_button_events(self):
        """Return tuple of button presses and callbacks for game navigation."""
        return self.get_button_events(
            buttonpress1=self.go_to_token, buttonpress3=self.post_move_menu
        )

    # Subclasses which need non-move PGN navigation should call this method.
    # Intended for editors.
    def add_pgn_navigation_to_submenu_of_popup(self, popup, index=tkinter.END):
        """Add non-move PGN navigation to a submenu of popup.

        Subclasses must provide the methods named.

        """
        navigate_score_submenu = tkinter.Menu(master=popup, tearoff=False)
        self.populate_navigate_score_submenu(navigate_score_submenu)
        popup.insert_cascade(
            index=index, label="Navigate Score", menu=navigate_score_submenu
        )

    # These get_xxx_events methods are used by event bind and popup creation
    # methods.

    def get_select_move_events(self):
        """Return tuple of variation selection keypresses and callbacks."""
        return (
            (
                EventSpec.score_cycle_selection_to_next_variation,
                self.variation_cycle,
            ),
            (EventSpec.score_show_selected_variation, self.show_variation),
            (
                EventSpec.score_cancel_selection_of_variation,
                self.variation_cancel,
            ),
        )

    def get_all_export_events(self):
        """Return tuple of PGN export keypresses and callbacks."""
        return (
            (
                EventSpec.pgn_reduced_export_format,
                self.export_pgn_reduced_export_format,
            ),
            (
                EventSpec.pgn_export_format_no_comments_no_ravs,
                self.export_pgn_no_comments_no_ravs,
            ),
            (
                EventSpec.pgn_export_format_no_comments,
                self.export_pgn_no_comments,
            ),
            (EventSpec.pgn_export_format, self.export_pgn),
            (EventSpec.pgn_import_format, self.export_pgn_import_format),
            (EventSpec.text_internal_format, self.export_text),
        )

    # These are the event bindings to traverse moves in PGN movetext.
    # The method name emphasizes the connection with implementation of main
    # purpose of CQLText, EngineText, and QueryText, widgets; rather than
    # being one of several sets of events available for PGN text files.
    def get_primary_activity_events(self):
        """Return tuple of game navigation keypresses and callbacks."""
        return (
            (EventSpec.score_show_next_in_line, self.show_next_in_line),
            (
                EventSpec.score_show_next_in_variation,
                self.show_next_in_variation,
            ),
            (EventSpec.score_show_previous_in_line, self.show_prev_in_line),
            (
                EventSpec.score_show_previous_in_variation,
                self.show_prev_in_variation,
            ),
            (EventSpec.score_show_first_in_game, self.show_first_in_game),
            (EventSpec.score_show_last_in_game, self.show_last_in_game),
            (EventSpec.score_show_first_in_line, self.show_first_in_line),
            (EventSpec.score_show_last_in_line, self.show_last_in_line),
        )

    # Analysis subclasses override method to exclude the first four items.
    # Repertoire subclasses override method to exclude the first two items.
    def populate_export_submenu(self, submenu):
        """Populate export submenu with export event bindings."""
        self.set_popup_bindings(submenu, self.get_all_export_events())

    def create_primary_activity_popup(self):
        """Delegate then add export submenu and return popup menu."""
        popup = super().create_primary_activity_popup()
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self.populate_export_submenu(export_submenu)
        index = "Database"
        try:
            popup.index(index)
        except tkinter.TclError as exc:
            if str(exc) != index.join(('bad menu entry index "', '"')):
                raise
            index = tkinter.END
        popup.insert_cascade(label="Export", menu=export_submenu, index=index)
        return popup

    def create_select_move_popup(self):
        """Create and return select move popup menu."""
        assert self.select_move_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_select_move_events())
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self.populate_export_submenu(export_submenu)
        popup.add_cascade(label="Export", menu=export_submenu)
        # pylint message assignment-from-none is false positive.
        # However it is sensible to do an isinstance test.
        database_submenu = self.create_database_submenu(popup)
        if isinstance(database_submenu, tkinter.Menu):
            popup.add_cascade(label="Database", menu=database_submenu)
        self.select_move_popup = popup
        return popup

    def post_move_menu(self, event=None):
        """Show the popup menu for game score navigation."""
        return self.post_menu(
            self.primary_activity_popup,
            self.create_primary_activity_popup,
            allowed=self.is_active_item_mapped(),
            event=event,
        )

    def post_move_menu_at_top_left(self, event=None):
        """Show the popup menu for game score navigation."""
        return self.post_menu_at_top_left(
            self.primary_activity_popup,
            self.create_primary_activity_popup,
            allowed=self.is_active_item_mapped(),
            event=event,
        )

    def post_select_move_menu(self, event=None):
        """Show the popup menu for variation selection in game score."""
        return self.post_menu(
            self.select_move_popup,
            self.create_select_move_popup,
            allowed=self.is_active_item_mapped(),
            event=event,
        )

    def post_select_move_menu_at_top_left(self, event=None):
        """Show the popup menu for variation selection in game score."""
        return self.post_menu_at_top_left(
            self.select_move_popup,
            self.create_select_move_popup,
            allowed=self.is_active_item_mapped(),
            event=event,
        )

    def show_first_in_game(self, event=None):
        """Display initial position of game score (usually start of game)."""
        del event
        return self.show_new_current(new_current=None)

    def show_first_in_line(self, event=None):
        """Display initial position of line containing current move."""
        del event
        if self.current is None:
            return "break"
        if self.is_currentmove_in_main_line():
            return self.show_first_in_game()
        selected_first_move = self.select_first_move_in_line(self.current)
        self.current = selected_first_move
        self.set_current()
        self.set_variation_tags_from_currentmove()
        self.set_game_board()
        return "break"

    def show_variation(self, event=None):
        """Enter selected variation and display its initial position."""
        del event
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_primary_activity()
        self.colour_variation(self.current)
        return "break"

    def show_last_in_game(self, event=None):
        """Display final position of game score."""
        del event
        return self.show_new_current(
            new_current=self.select_last_move_played_in_game()
        )

    def show_last_in_line(self, event=None):
        """Display final position of line containing current move."""
        del event
        if self.current is None:
            return self.show_last_in_game()
        if self.is_currentmove_in_main_line():
            return self.show_last_in_game()
        self.current = self.select_last_move_in_line()
        self.add_variation_before_move_to_colouring_tag(self.current)
        self.set_current()
        self.set_game_board()
        return "break"

    def show_next_in_line(self, event=None):
        """Display next position of selected line."""
        del event
        if self.current is None:
            self.current = self.select_first_move_of_game()
        else:
            if self.is_variation_entered():
                self.add_move_to_moves_played_colouring_tag(self.current)
            self.current = self.select_next_move_in_line()
        self.set_current()
        self.set_game_board()
        return "break"

    def show_next_in_variation(self, event=None):
        """Display choices if these exist or next position of selected line."""
        del event
        if self.current is None:

            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self.get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            if choice is None:
                return self.show_next_in_line()
            selection = self.get_selection_tag_for_choice(choice)

        else:
            prior = self.get_prior_to_variation_tag_of_move(self.current)
            if prior is None:
                return self.show_next_in_line()
            choice = self.get_choice_tag_for_prior(prior)
            selection = self.get_selection_tag_for_prior(prior)

        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self.cycle_selection_tag(choice, selection)

        variation = self.get_colouring_variation_tag_for_selection(selection)
        self.set_variation_selection_tags(prior, choice, selection, variation)
        if self._most_recent_bindings != NonTagBind.SELECT_VARIATION:
            self.bind_for_select_variation()
        return "break"

    def show_prev_in_line(self, event=None):
        """Display previous position of selected line."""
        del event
        if self.current is None:
            return "break"
        if not self.is_currentmove_in_main_line():
            self.remove_currentmove_from_moves_played_in_variation()
        self.current = self.select_prev_move_in_line()
        self.set_current()
        self.set_game_board()
        return "break"

    def show_prev_in_variation(self, event=None):
        """Display choices in previous position of selected line."""
        del event
        if self.current is None:
            return "break"
        if not self.is_currentmove_in_main_line():
            self.remove_currentmove_from_moves_played_in_variation()
            if self.is_currentmove_start_of_variation():
                self.clear_variation_colouring_tag()
                self.current = self.get_position_tag_of_previous_move()
                self.set_current()
                self.set_game_board()
                if self.current is None:
                    self.clear_moves_played_in_variation_colouring_tag()
                elif (
                    self.get_prior_to_variation_tag_of_move(self.current)
                    is None
                ):
                    return "break"
                if self._most_recent_bindings != NonTagBind.SELECT_VARIATION:
                    self.bind_for_select_variation()
                self.variation_cycle()
                return "break"
        self.current = self.select_prev_move_in_line()
        self.set_current()
        self.set_game_board()
        return "break"

    def variation_cancel(self, event=None):
        """Remove all variation highlighting."""
        del event
        if self.current is None:

            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self.get_choice_tag_of_move(
                self.select_first_move_of_game()
            )

        else:
            prior = self.get_prior_to_variation_tag_of_move(self.current)
            choice = self.get_choice_tag_for_prior(prior)
        self.clear_variation_choice_colouring_tag(choice)
        self.clear_variation_colouring_tag()
        if self.current is not None:
            if not self.is_currentmove_in_main_line():
                self.add_currentmove_variation_to_colouring_tag()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_primary_activity()
        return "break"

    def variation_cycle(self, event=None):
        """Highlight next variation in choices at current position."""
        del event
        self.step_one_variation(self.current)
        return "break"

    # Methods which export *.pgn files.

    def export_pgn_reduced_export_format(self, event=None):
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

    def export_pgn(self, event=None):
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

    def export_pgn_no_comments_no_ravs(self, event=None):
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

    def export_pgn_no_comments(self, event=None):
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

    def export_text(self, event=None):
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
