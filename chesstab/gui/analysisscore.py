# analysisscore.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display the analysis by chess engines of a game of chess."""

import tkinter

from pgn_read.core.constants import (
    FEN_WHITE_ACTIVE,
    PGN_DOT,
)

from ..core.pgn import GameAnalysis
from .constants import (
    MOVES_PLAYED_IN_GAME_FONT,
    NAVIGATE_MOVE,
    PRIOR_MOVE,
    RAV_SEP,
    ALL_CHOICES,
    SELECTION,
    BUILD_TAG,
    SPACE_SEP,
    NEWLINE_SEP,
    NULL_SEP,
)
from .eventspec import EventSpec
from .blanktext import NonTagBind
from .score import Score, ScoreNoInitialPositionException


class ScoreMapToBoardException(Exception):
    """Raise to indicate display of chess engine analysis for illegal move.

    In particular in the GameEdit class when the move played is the last in
    game or variation, but is being edited at the time and not complete.  It
    is caught in the AnalysisScore class but should be treated as a real
    error in the Score class.

    """


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

    Attribute pgn_export_type is a tuple with the name of the type of data and
    the class used to generate export PGN.  It exists so Game*, Repertoire*,
    and AnalysisScore*, instances can use identical code to display PGN tags.
    It is ('Analysis', GameAnalysis).

    Attribute analysis_text is the default for PGN text in the AnalysyisScore
    widget.  It is None meaning there is no analysis to show.

    """

    # Initial value of current text displayed in analysis widget: used to
    # control refresh after periodic update requests.
    analysis_text = None

    pgn_export_type = "Analysis", GameAnalysis

    def __init__(self, *a, owned_by_game=None, **ka):
        """Delegate then set owned_by_game to game for this analysis."""
        super().__init__(*a, **ka)
        self.owned_by_game = owned_by_game

    def clear_score(self):
        """Clear data stuctures for navigating a game score.

        Normally a game is loaded into the Score instance and remains for the
        lifetime of the instance.  UCI Chess Engine analysis, in particular, is
        used to refresh the game score snippet in an analysis widget after each
        navigation event in the main game widget.

        This method allows the Score instance to be reused for many PGN game
        scores, full games or otherwise.

        """
        self.variation_number = 0
        self.varstack = []
        self.choice_number = 0
        self.choicestack = []
        self.position_number = 0
        self.tagpositionmap = {}
        self.previousmovetags = {}
        self.nextmovetags = {}

    def _go_to_token(self, event=None):
        """Set position and highlighting for token under pointer in analysis.

        Do nothing if self.analysis is not the active item.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item.analysis:
                return "break"
        return self.go_to_move(
            self.score.index("".join(("@", str(event.x), ",", str(event.y))))
        )

    def _is_active_item_mapped(self):
        """Return True if self.analysis is the active item, or False if not."""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item.analysis:
                return False
        return True

    def set_score(self, analysis_text, reset_undo=False):
        """Display the position analysis as moves.

        starttoken is the move played to reach the position displayed and this
        move becomes the current move.
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a game for editing so that repeated Ctrl-Z in text
        editing mode recovers the original score.

        """
        if not self._is_text_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete("1.0", tkinter.END)

        # An attempt to insert an illegal move into a game score will cause
        # an exception when parsing the engine output.  Expected to happen when
        # editing or inserting a game and the move before an incomplete move
        # becomes the current move.
        # Illegal moves are wrapped in '{Error::  ::{{::}' comments by the
        # game updater: like '--' moves found in some PGN files which do not
        # follow the standard strictly.
        try:
            self.map_game()
        except ScoreMapToBoardException:
            self.score.insert(
                tkinter.END,
                "".join(
                    (
                        "The analysis is attached to an illegal move, which ",
                        "can happen while editing or inserting a game.\n\nIt ",
                        "is displayed but cannot be played through.\n\n",
                    )
                ),
            )
            self.score.insert(tkinter.END, analysis_text)

        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self._bind_for_primary_activity()
        if not self._is_text_editable:
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
            except ScoreNoInitialPositionException:
                return False

            self._see_first_move()
        else:
            try:
                self.board.set_board(self.tagpositionmap[self.current][0])
            except TypeError:
                self.board.set_board(self.fen_tag_square_piece_map())
                self.score.see(self.score.tag_ranges(self.current)[0])
                return False
            self.score.see(self.score.tag_ranges(self.current)[0])
        return False

    def _map_move_text(self, token, position):
        """Add token to game text. Set navigation tags. Return token range.

        self._start_latest_move and self._end_latest_move are set to range
        occupied by token text so that variation tags can be constructed as
        more moves are processed.

        """
        self._modify_square_piece_map(position)
        widget = self.score
        scaffold = self._game_scaffold
        positiontag = self._get_next_positiontag_name()
        self.tagpositionmap[positiontag] = (
            scaffold.square_piece_map.copy(),
        ) + position[1][1:]

        # The only way found to get the move number at start of analysis.
        # Direct use of self.score.insert(...), as in _insert_token_into_text,
        # or a separate call to _insert_token_into_text(...), does not work:
        # interaction with _refresh_analysis_widget_from_database() in
        # game.Game when building the text is assumed to be the cause.
        if len(self.varstack) == 0:
            active_side = position[0][1]
            fullmove_number = position[0][5]
            if active_side == FEN_WHITE_ACTIVE:
                fullmove_number = str(fullmove_number) + PGN_DOT
            else:
                fullmove_number = str(fullmove_number) + PGN_DOT * 3
            start, end, sepend = self._insert_token_into_text(
                "".join((fullmove_number, SPACE_SEP, token)), SPACE_SEP
            )
        else:
            start, end, sepend = self._insert_token_into_text(token, SPACE_SEP)

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
        self._set_square_piece_map(position)
        widget = self.score
        scaffold = self._game_scaffold
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
        start, end, sepend = self._insert_token_into_text(token, SPACE_SEP)
        widget.tag_add(BUILD_TAG, start, end)
        scaffold.next_move_is_choice = True
        return start, end, sepend

    def map_end_rav(self, token, position):
        """Add token to game text. position is ignored. Return token range.

        Variation tags are set for guiding move navigation. self._vartag
        self._token_position and self._choicetag are restored from the stack
        to reconstruct the position at the end of the variation.
        (self._start_latest_move, self._end_latest_move) is set to the range
        of the move which the first move of the variation replaced.

        """
        scaffold = self._game_scaffold
        try:
            (
                scaffold.start_latest_move,
                scaffold.end_latest_move,
            ) = self.score.tag_prevrange(ALL_CHOICES, tkinter.END)
        except TypeError:
            (scaffold.start_latest_move, scaffold.end_latest_move) = (
                tkinter.END,
                tkinter.END,
            )
        start, end, sepend = self._insert_token_into_text(token, NEWLINE_SEP)
        self.score.tag_add(BUILD_TAG, start, end)
        scaffold.vartag, scaffold.token_position = self.varstack.pop()
        scaffold.choicetag = self.choicestack.pop()
        return start, end, sepend

    def _map_start_comment(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self._insert_token_into_text(token, SPACE_SEP)

    def _map_comment_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token)
        end = widget.index(tkinter.INSERT + " -1 chars")
        widget.insert(tkinter.INSERT, NULL_SEP)
        return start, end, widget.index(tkinter.INSERT)

    def map_termination(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self._insert_token_into_text(token, NEWLINE_SEP)

    # Analysis does not follow PGN export format, so those options are absent.
    def _get_all_export_events(self):
        """Return tuple of keypress events and callbacks for PGN export."""
        return (
            (EventSpec.pgn_import_format, self.export_pgn_import_format),
            (EventSpec.text_internal_format, self._export_text),
        )

    # Analysis widget uses the associated Game method to make active or dismiss
    # item.  Some searching through the self.board.ui object is likely.
    def _create_inactive_popup(self):
        """Return popup menu of keypress event bindings for inactive item."""
        game = self.owned_by_game
        assert self.inactive_popup is None and game is not None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self._set_popup_bindings(popup, self._get_inactive_events())
        self.inactive_popup = popup
        return popup

    def _get_inactive_button_events(self):
        """Return tuple of button events and callbacks for inactive item."""
        game = self.owned_by_game
        assert game is not None and self is game.analysis
        return self._get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_1, game.give_focus_to_widget),
            (EventSpec.buttonpress_3, game.post_inactive_menu),
        )

    def _get_inactive_events(self):
        """Return tuple of keypress events and callbacks for inactive item."""
        game = self.owned_by_game
        assert game is not None and self is game.analysis
        return (
            (EventSpec.display_make_active, game.set_focus_panel_item_command),
            (EventSpec.display_dismiss_inactive, game.delete_item_view),
        )

    # Subclasses which need widget navigation in their popup menus should
    # call this method.
    def _create_widget_navigation_submenu_for_popup(self, popup):
        """Create and populate a submenu of popup for widget navigation.

        The commands in the submenu should switch focus to another widget.

        Subclasses should define a generate_popup_navigation_maps method and
        binding_labels iterable suitable for allowed navigation.

        """
        (
            navigation_map,
            local_map,
        ) = self.owned_by_game.generate_popup_navigation_maps()
        del local_map[EventSpec.scoresheet_to_analysis]
        local_map[
            EventSpec.analysis_to_scoresheet
        ] = self.owned_by_game.current_item
        local_map.update(navigation_map)
        self._add_cascade_menu_to_popup(
            "Navigation",
            popup,
            bindings=local_map,
            order=self.owned_by_game.binding_labels,
        )

    def _create_primary_activity_popup(self):
        """Delegate then add navigation submenu and return popup menu."""
        popup = super()._create_primary_activity_popup()
        self._create_widget_navigation_submenu_for_popup(popup)
        return popup

    def _create_select_move_popup(self):
        """Delegate then add navigation submenu and return popup menu."""
        popup = super()._create_select_move_popup()
        self._create_widget_navigation_submenu_for_popup(popup)
        return popup

    def _set_select_variation_bindings(self, switch=True):
        """Delegate then set board pointer bindings for select variation."""
        super()._set_select_variation_bindings(switch=switch)
        self.set_board_pointer_select_variation_bindings(switch=switch)

    # A way of getting pointer clicks on board to behave like pointer clicks
    # on analysis score when traversing to previous moves has not been found.
    # The problem seems to be the lack of a move prior to the move played and
    # variations, compared with the game or repertoire score.  Also the clicks
    # on board are the same event for previous move without leaving variation
    # and previous move and leave variation if at at first move; but these are
    # separate events for clicks, or keystrokes, on the analysis score.
    def variation_cancel(self, event=None):
        """Remove all variation highlighting."""
        if self.score is event.widget:
            return super().variation_cancel(event=event)
        current = self.current
        self._show_prev_in_line()
        if current != self.current:
            return "break"
        if current is None:
            return "break"
        return self._show_prev_in_variation()
        # self._show_prev_in_variation()
        # if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
        #    self._bind_for_primary_activity()
