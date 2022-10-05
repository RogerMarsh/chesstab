# gameedit_handlers.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to edit a chess game score and put current position on a board.

The GameEdit class displays a game of chess and allows editing.  It is a
subclass of game.Game.

This class does not allow deletion of games from a database.

An instance of GameEdit fits into the user interface in two ways: as an item
in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

import tkinter
import tkinter.messagebox

from solentware_misc.workarounds.workarounds import text_count

from pgn_read.core.constants import (
    TAG_RESULT,
)

from ..core.constants import (
    WHITE_WIN,
    BLACK_WIN,
    DRAW,
    UNKNOWN_RESULT,
)
from . import gameedit_move
from .eventspec import EventSpec
from .constants import (
    EDIT_RESULT,
    EDIT_PGN_TAG_NAME,
    EDIT_MOVE,
    MOVE_EDITED,
    NAVIGATE_MOVE,  # absence matters if no EDIT_... exists
    LINE_TAG,
    START_SCORE_MARK,
    START_EDIT_MARK,
    END_EDIT_MARK,
    PGN_TAG,
    TERMINATION_TAG,
)

# Tk keysym map to PGN termination sequences:
_TERMINATION_MAP = {
    "plus": WHITE_WIN,
    "equal": DRAW,
    "minus": BLACK_WIN,
    "asterisk": UNKNOWN_RESULT,
}

# The characters used in moves. Upper and lower case L are included as synonyms
# for B to allow shiftless typing of moves such as Bb5.
_MOVECHARS = "abcdefghklnoqrABCDEFGHKLNOQR12345678xX-="
_FORCECASE = bytes.maketrans(b"ACDEFGHLXklnoqr", b"acdefghBxKBNOQR")
# The use of return 'break' throughout this module means that \r to \n does
# not get done by Text widget.  The two places where typing \r is allowed are
# dealt with using _NEWLINE.
_NEWLINE = bytes.maketrans(b"\r", b"\n")


class GameEdit(gameedit_move.GameEdit):
    """Display a game with editing allowed."""

    def _add_char_to_token(self, event):
        """Handle <KeyPress> event for non-move token."""
        self._insert_char_at_insert_point(event.char.translate(_NEWLINE))
        return "break"

    def _add_move_char_to_token(self, event):
        """Handle <KeyPress> event for move token."""
        if self._insert_char_at_insert_point(event.char.translate(_FORCECASE)):
            self._process_move()
        return "break"

    def _delete_char_right(self, event):
        """Handle <Del> event."""
        del event
        self._delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
        return "break"

    def _delete_char_left(self, event):
        """Handle <BackSpace> event."""
        del event
        self._delete_char_next_to_insert_mark(START_EDIT_MARK, tkinter.INSERT)
        return "break"

    def _delete_move_char_right(self, event):
        """Handle <Shift-Del> event for move token."""
        del event
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self._delete_char_next_to_insert_mark(
                tkinter.INSERT, END_EDIT_MARK
            )
            self._process_move()
        elif self._is_game_or_rav_valid_without_move():
            self._delete_empty_move()
        return "break"

    def _delete_move_char_left(self, event):
        """Handle <Shift-BackSpace> event for move token."""
        del event
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self._delete_char_next_to_insert_mark(
                START_EDIT_MARK, tkinter.INSERT
            )
            self._process_move()
        elif self._is_game_or_rav_valid_without_move():
            self._delete_empty_move()
        return "break"

    def _delete_token_char_right(self, event):
        """Handle <Shift-Del> event for non-move token."""
        del event
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self._delete_char_next_to_insert_mark(
                tkinter.INSERT, END_EDIT_MARK
            )
        else:
            self._delete_empty_token()
        return "break"

    def _delete_token_char_left(self, event):
        """Handle <Shift-BackSpace> event for non-move token."""
        del event
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self._delete_char_next_to_insert_mark(
                START_EDIT_MARK, tkinter.INSERT
            )
        else:
            self._delete_empty_token()
        return "break"

    # Not sure if this will be needed.
    # Maybe use to handle text edit mode
    def edit_gamescore(self, event):
        """Edit game score on keyboard event."""
        del event
        if not self._is_game_in_text_edit_mode():
            return

    def _insert_comment(self, event=None):
        """Insert comment in game score after current."""
        del event
        if self.current:
            if not self._is_current_in_movetext():
                return "break"
        return self._show_item(new_item=self._insert_empty_comment())

    def _insert_comment_to_eol(self, event=None):
        """Insert comment to eol in game score after current."""
        del event
        if self.current:
            if not self._is_current_in_movetext():
                return "break"
        return self._show_item(new_item=self._insert_empty_comment_to_eol())

    def _insert_escape_to_eol(self, event=None):
        """Insert escape to eol in game score after current."""
        del event
        if self.current:
            if not self._is_current_in_movetext():
                return "break"
        return self._show_item(new_item=self._insert_empty_escape_to_eol())

    def _insert_glyph(self, event=None):
        """Insert glyph in game score after current."""
        del event
        if self.current:
            if not self._is_current_in_movetext():
                return "break"
        return self._show_item(new_item=self._insert_empty_glyph())

    def _insert_pgn_tag(self, event=None):
        """Insert a single empty pgn tag in game score after current."""
        del event
        if self.current:
            if self._is_current_in_movetext():
                return "break"
        self._insert_empty_pgn_tag()
        if self.current:
            return self._show_next_pgn_tag_field_name()
        if self.score.compare(tkinter.INSERT, "<", START_SCORE_MARK):
            self.score.mark_set(
                tkinter.INSERT,
                self.score.index(tkinter.INSERT + " linestart -1 lines"),
            )
            return self._show_next_token()
        return self._show_prev_pgn_tag_field_name()

    def _insert_pgn_seven_tag_roster(self, event=None):
        """Insert an empty pgn seven tag roster in game score after current."""
        del event
        if self.current:
            if self._is_current_in_movetext():
                return "break"
        self._insert_empty_pgn_seven_tag_roster()
        if self.current:
            return self._show_next_pgn_tag_field_name()
        if self.score.compare(tkinter.INSERT, "<", START_SCORE_MARK):
            self.score.mark_set(
                tkinter.INSERT,
                self.score.index(tkinter.INSERT + " linestart -7 lines"),
            )
            return self._show_next_token()
        return self._show_prev_pgn_tag_field_name()

    def _insert_rav(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the move following the current move, and
        before any existing RAVs in that place.

        KeyPress events are bound to _insert_rav() when a move is the current
        token, except for the last move in the game or a RAV when these are
        bound to _insert_move().  When no moves exist, either incomplete or
        illegal, KeyPress events are bound to _insert_rav().

        KeyPress events are bound to _insert_move() when the first character
        has been processed.

        """
        if not self._is_at_least_one_move_in_movetext():
            return self._insert_move(event)
        if not event.char:
            return "break"
        if event.char in _MOVECHARS:
            inserted_move = self._insert_empty_rav_after_next_move(
                event.char.translate(_FORCECASE)
            )
            while not self._is_move_start_of_variation(
                inserted_move, self._step_one_variation(self.current)
            ):
                pass
            self._colour_variation(self.current)
            # self.set_current() already called
        return "break"

    def _insert_rav_after_rav_start(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the current RAV start marker, '(', and
        before any existing move or RAVs in that place.

        <Alt KeyPress> events are bound to _insert_rav_after_rav_start() when
        a RAV start marker is the current token.

        KeyPress events are bound to _insert_move() when the first character
        has been processed.

        """
        if not event.char:
            return "break"
        move = self._get_implied_current_move()
        if event.char in _MOVECHARS:
            inserted_move = self._insert_empty_rav_after_rav_start(
                event.char.translate(_FORCECASE)
            )
            while not self._is_move_start_of_variation(
                inserted_move, self._step_one_variation(move)
            ):
                pass
            self._colour_variation(move)
        return "break"

    def _insert_rav_after_rav_start_move_or_rav(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the first move, or RAV, after the current
        RAV start marker, '('.

        <Shift KeyPress> events are bound to
        _insert_rav_after_rav_start_move_or_rav() when a RAV start marker is
        the current token.

        KeyPress events are bound to _insert_move() when the first character
        has been processed.

        """
        if not event.char:
            return "break"
        move = self._get_implied_current_move()
        if event.char in _MOVECHARS:
            inserted_move = self._insert_empty_rav_after_rav_start_move_or_rav(
                event.char.translate(_FORCECASE)
            )
            while not self._is_move_start_of_variation(
                inserted_move, self._step_one_variation(move)
            ):
                pass
            self._colour_variation(move)
        return "break"

    def _insert_rav_after_rav_end(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the RAV end marker, ')', paired with the
        current RAV start marker, '('.

        <KeyPress> events are bound to _insert_rav_after_rav_end() when a RAV
        start marker is the current token.

        KeyPress events are bound to _insert_move() when the first character
        has been processed.

        """
        if not event.char:
            return "break"
        move = self._get_implied_current_move()
        if event.char in _MOVECHARS:
            inserted_move = self._insert_empty_rav_after_rav_end(
                event.char.translate(_FORCECASE)
            )
            while not self._is_move_start_of_variation(
                inserted_move, self._step_one_variation(move)
            ):
                pass
            self._colour_variation(move)
        return "break"

    def _insert_rav_command(self, event=None):
        """Display information dialogue saying how to insert a RAV."""
        del event
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title="Insert RAV",
            message="".join(
                (
                    "The menu entry exists to advertise the function.\n\n",
                    "Type a character valid in moves to open the RAV.",
                )
            ),
        )

    def _insert_rav_castle_queenside(self, event):
        """Insert or edit the O-O-O movetext.

        If intending to type O-O-O when both O-O and O-O-O are possible the
        O-O is accepted before the chance to type the second '-' arrives.
        'Ctrl o' and the menu equivalent provide a positive way of indicating
        the O-O-O move.  A negative way of inserting O-O-O is to type O--O and
        then type the middle 'O'.

        """
        # To catch insertion when no moves, even incomplete or illegal, exist.
        # Perhaps it is better to put this test in bind_...() methods.  Hope
        # that will not add too many states for one rare case.
        if not self._is_at_least_one_move_in_movetext():
            return self._insert_move_castle_queenside(event)
        if not event.char:
            return "break"
        if not self.current:
            move = self.current
        else:
            move = self._get_implied_current_move()
        inserted_move = self._insert_empty_rav_after_next_move("O-O-O")
        while not self._is_move_start_of_variation(
            inserted_move, self._step_one_variation(move)
        ):
            pass
        self._colour_variation(move)
        self._process_move()
        return "break"

    def _insert_result(self, v_q):
        """Insert or edit the game termination sequence and PGN Result Tag."""
        er_q = self.score.tag_ranges(EDIT_RESULT)
        tt_q = self.score.tag_ranges(TERMINATION_TAG)
        if tt_q:
            ttn = self.score.tag_prevrange(EDIT_PGN_TAG_NAME, tt_q[-4])
            if ttn:
                if self.score.get(*ttn).strip() == TAG_RESULT:
                    # Insert then delete difference between tt_q[-2] and
                    # ntt[-2] before ntt[-2] to do tagging automatically.
                    start = str(tt_q[-4]) + "+1c"
                    self.score.delete(start, tt_q[-3])
                    self.score.insert(start, v_q)
                    ntt = self.score.tag_ranges(TERMINATION_TAG)
                    end = str(ntt[-2]) + "-1c"
                    for t_q in self.score.tag_names(tt_q[-4]):
                        self.score.tag_add(t_q, ntt[-3], end)
        if er_q:
            self.score.insert(er_q[0], v_q)
            ner = self.score.tag_ranges(EDIT_RESULT)
            for tn_q in self.score.tag_names(ner[0]):
                self.score.tag_add(tn_q, er_q[0], ner[0])
            self.score.delete(*ner)
        return "break"

    def _insert_result_draw(self, event=None):
        """Set 1/2-1/2 as the game termination sequence and PGN Result Tag."""
        del event
        self._insert_result(DRAW)

    def insert_result_event(self, event=None):
        """Insert or edit the game termination sequence and PGN Result Tag."""
        del event
        self._insert_result(_TERMINATION_MAP.get(event.keysym))

    def _insert_result_loss(self, event=None):
        """Set 0-1 as the game termination sequence and PGN Result Tag."""
        del event
        self._insert_result(BLACK_WIN)

    def _insert_result_termination(self, event=None):
        """Set * as the game termination sequence and PGN Result Tag."""
        del event
        self._insert_result(UNKNOWN_RESULT)

    def _insert_result_win(self, event=None):
        """Set 1-0 as the game termination sequence and PGN Result Tag."""
        del event
        self._insert_result(WHITE_WIN)

    def _insert_reserved(self, event=None):
        """Insert reserved in game score after current."""
        del event
        if self.current:
            if not self._is_current_in_movetext():
                return "break"
        return self._show_item(new_item=self._insert_empty_reserved())

    def _insert_castle_queenside_command(self):
        """Insert or edit the O-O-O movetext."""
        ria = self._is_at_least_one_move_in_movetext()
        c_q = self.score.tag_ranges(self.current)

        # Is current move last move in game?
        # [-2], start of move, would do too.
        if c_q and ria:
            if c_q[-1] == self.score.tag_ranges(NAVIGATE_MOVE)[-1]:
                ria = False

        # Is current move last move in a variation?
        # Not [-1], end of move, because rm_q[-1] includes space after move.
        if ria:
            rm_q = self.score.tag_ranges(LINE_TAG)
            if rm_q:
                if rm_q[-2] == c_q[-2]:
                    ria = False

        if not ria:
            self._insert_empty_move_after_currentmove("O-O-O")
            self._show_next_in_line()
            self._process_move()
            return "break"
        inserted_move = self._insert_empty_rav_after_next_move("O-O-O")
        while not self._is_move_start_of_variation(
            inserted_move, self._step_one_variation(self.current)
        ):
            pass
        self._colour_variation(self.current)
        self._process_move()
        return "break"

    def _edit_move(self, event):
        """Start editing last move in variation.

        Remove current move from EDIT_MOVE tag and add to MOVE_EDITED tag.
        Reset current and delete the last character from the token.

        """
        start, end = self.score.tag_ranges(self.current)
        self.score.tag_remove(EDIT_MOVE, start, end)
        self.score.tag_add(MOVE_EDITED, start, end)
        if self._is_currentmove_in_main_line():
            current = self._select_prev_move_in_line()
        elif self._is_currentmove_start_of_variation():
            choice = self._get_choice_tag_of_index(start)
            prior = self.get_prior_tag_for_choice(choice)
            try:
                current = self._get_position_tag_of_index(
                    self.score.tag_ranges(prior)[0]
                )
            except IndexError:
                current = None
        else:
            current = self._select_prev_move_in_line()
        self.edit_move_context[self.current] = self.create_edit_move_context(
            current
        )
        self.tagpositionmap[self.current] = self.tagpositionmap[current]
        self.set_current()
        self.set_game_board()
        return self._delete_move_char_left(event)

    def _insert_move(self, event):
        """Insert characters of new moves in game score.

        KeyPress events are bound to _insert_move() when the last move in the
        game or a RAV is the current token.  When no moves exist, either
        incomplete or illegal, KeyPress events are bound to _insert_rav().

        KeyPress events are bound to _insert_move() when the first character
        has been processed by _insert_rav(), or it's variants for the Alt and
        Shift modifiers.

        """
        if not event.char:
            return "break"
        if event.char in _MOVECHARS:
            self._insert_empty_move_after_currentmove(
                event.char.translate(_FORCECASE)
            )
            return self._show_next_in_line()
        return "break"

    def _insert_move_castle_queenside(self, event):
        """Insert or edit the O-O-O movetext.

        If intending to type O-O-O when both O-O and O-O-O are possible the
        O-O is accepted before the chance to type the second '-' arrives.
        'Ctrl o' and the menu equivalent provide a positive way of indicating
        the O-O-O move.  A negative way of inserting O-O-O is to type O--O and
        then type the middle 'O'.

        """
        if not event.char:
            return "break"
        self._insert_empty_move_after_currentmove("O-O-O")
        self._show_next_in_line()
        self._process_move()
        return "break"

    def _set_insert_first_char_in_token(self, event):
        """Handle <Home> event."""
        del event
        self._set_insert_mark_at_start_of_token()
        return "break"

    def _set_insert_last_char_in_token(self, event):
        """Handle <End> event."""
        del event
        self._set_insert_mark_at_end_of_token()
        return "break"

    def _set_insert_next_char_in_token(self, event):
        """Handle <Right> event."""
        del event
        self._set_insert_mark_right_one_char()
        return "break"

    def _set_insert_next_line_in_token(self, event):
        """Handle <Alt-Down> event."""
        del event
        self._set_insert_mark_down_one_line()
        return "break"

    def _set_insert_prev_char_in_token(self, event):
        """Handle <Left> event."""
        del event
        self._set_insert_mark_left_one_char()
        return "break"

    def _set_insert_prev_line_in_token(self, event):
        """Handle <Alt-Up> event."""
        del event
        self._set_insert_mark_up_one_line()
        return "break"

    def _show_move_or_item(self, new_item=None):
        """Display new item if not None."""
        if not new_item:
            return "break"
        tr_q = self.score.tag_ranges(new_item)
        if NAVIGATE_MOVE in self.score.tag_names(tr_q[0]):
            return self.go_to_move(tr_q[0])
        return self._show_item(new_item=new_item)

    def _show_first_comment(self, event=None):
        """Display first comment in game score."""
        del event
        return self._show_item(new_item=self._select_first_comment_in_game())

    def _show_last_comment(self, event=None):
        """Display last comment in game score."""
        del event
        return self._show_item(new_item=self._select_last_comment_in_game())

    def _show_next_comment(self, event=None):
        """Display next comment in game score."""
        del event
        return self._show_item(new_item=self._select_next_comment_in_game())

    def _show_prev_comment(self, event=None):
        """Display previous comment in game score."""
        del event
        return self._show_item(new_item=self._select_prev_comment_in_game())

    def _show_first_token(self, event=None):
        """Display first token in game score (usually first PGN Tag)."""
        del event
        if self.current is None:
            return "break"
        return self._show_move_or_item(
            new_item=self._select_first_token_in_game()
        )

    def _show_last_token(self, event=None):
        """Display last token in game score (usually termination, 1-0 etc)."""
        del event
        return self._show_move_or_item(
            new_item=self._select_last_token_in_game()
        )

    def _show_next_token(self, event=None):
        """Display next token in game score (ignore rav structure of game).

        Return 'break' so Tk selection is not modified or set.  This event is
        fired by Shift Right.

        """
        del event
        self._show_move_or_item(new_item=self._select_next_token_in_game())
        return "break"

    def _show_prev_token(self, event=None):
        """Display prev token in game score (ignore rav structure of game).

        Return 'break' so Tk selection is not modified or set.  This event is
        fired by Shift Left.

        """
        del event
        self._show_move_or_item(new_item=self._select_prev_token_in_game())
        return "break"

    def _show_next_rav_start(self, event=None):
        """Display next RAV Start in game score."""
        del event
        return self._show_item(new_item=self._select_next_rav_start_in_game())

    def _show_prev_rav_start(self, event=None):
        """Display previous RAV Start in game score."""
        del event
        return self._show_item(new_item=self._select_prev_rav_start_in_game())

    def _show_next_pgn_tag_field_name(self, event=None):
        """Display next pgn tag field name."""
        del event
        return self._show_item(new_item=self._select_next_pgn_tag_field_name())

    def _show_prev_pgn_tag_field_name(self, event=None):
        """Display previous pgn tag field name."""
        del event
        return self._show_item(new_item=self._select_prev_pgn_tag_field_name())

    def _to_prev_pgn_tag(self, event=None):
        """Position insertion cursor before preceding pgn tag in game score."""
        del event
        self.clear_moves_played_in_variation_colouring_tag()
        self._clear_choice_colouring_tag()
        self._clear_variation_colouring_tag()
        if self.score.compare(tkinter.INSERT, ">", START_SCORE_MARK):
            self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
        else:
            tr_q = self.score.tag_prevrange(PGN_TAG, tkinter.INSERT)
            if tr_q:
                self.score.mark_set(tkinter.INSERT, tr_q[0])
            else:
                self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
        self.current = None
        # self.set_current() # sets Tkinter.INSERT to wrong position

        # Hack in case arriving from last move in line
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_insert_move, self.press_break),
                (EventSpec.gameedit_edit_move, self.press_break),
                (EventSpec.gameedit_insert_castle_queenside, self.press_break),
            )
        )

        self.clear_current_range()
        self.set_game_board()
        self.score.see(tkinter.INSERT)
        return "break"

    def _to_next_pgn_tag(self, event=None):
        """Position insertion cursor before following pgn tag in game score."""
        del event
        self.clear_moves_played_in_variation_colouring_tag()
        self._clear_choice_colouring_tag()
        self._clear_variation_colouring_tag()
        if self.score.compare(tkinter.INSERT, ">", START_SCORE_MARK):
            tr_q = self.score.tag_nextrange(PGN_TAG, "1.0")
        else:
            tr_q = self.score.tag_nextrange(PGN_TAG, tkinter.INSERT)
        if tr_q:
            self.score.mark_set(tkinter.INSERT, str(tr_q[-1]) + "+1c")
        else:
            self.score.mark_set(tkinter.INSERT, "1.0")
        self.current = None
        # self.set_current() # sets Tkinter.INSERT to wrong position

        # Hack in case arriving from last move in line
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_insert_move, self.press_break),
                (EventSpec.gameedit_edit_move, self.press_break),
                (EventSpec.gameedit_insert_castle_queenside, self.press_break),
            )
        )

        self.clear_current_range()
        self.set_game_board()
        self.score.see(tkinter.INSERT)
        return "break"

    # Renamed from 'bind_and_show_first_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_first_in_line which does same thing.
    def _show_first_in_line_from_non_move_token(self, event=None):
        """Set first move in line before currrent token as current move."""
        self._set_nearest_move_to_token_as_currentmove()
        return self._show_first_in_line(event)

    # Renamed from 'bind_and_show_first_in_game' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_first_in_game which does same thing.
    def _show_first_in_game_from_non_move_token(self, event=None):
        """Set first move in game as current move."""
        self._set_nearest_move_to_token_as_currentmove()
        return self._show_first_in_game(event)

    # Renamed from 'bind_and_show_last_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_last_in_line which does same thing.
    def _show_last_in_line_from_non_move_token(self, event=None):
        """Set last move in line after currrent token as current move."""
        self._set_nearest_move_to_token_as_currentmove()
        return self._show_last_in_line(event)

    # Renamed from 'bind_and_show_last_in_game' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_last_in_game which does same thing.
    def _show_last_in_game_from_non_move_token(self, event=None):
        """Set last move in game as current move."""
        self._set_nearest_move_to_token_as_currentmove()
        return self._show_last_in_game(event)

    # Renamed from 'bind_and_show_next_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_next_in_line which does same thing.
    def _show_next_in_line_from_non_move_token(self, event=None):
        """Set move after currrent token as current move."""
        self._set_nearest_move_to_token_as_currentmove()
        return self._show_next_in_line(event)

    # Renamed from 'bind_and_show_next_in_var' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_next_in_variation which does same thing.
    def _show_next_in_variation_from_non_move_token(self, event=None):
        """Set move after currrent token in variation as current move."""
        self._set_nearest_move_to_token_as_currentmove()
        return self._show_next_in_variation(event)

    # Renamed from 'bind_and_show_prev_in_var' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_prev_in_variation which does same thing.
    def _show_prev_in_variation_from_non_move_token(self, event=None):
        """Set move before currrent token in variation as current move."""
        del event
        self._set_nearest_move_to_token_as_currentmove()

        # self.set_current() already called but return is not via a method
        # which will call self.set_game_board().
        self.set_game_board()
        return "break"

    # Renamed from 'bind_and_show_prev_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_prev_in_line which does same thing.
    def _show_prev_in_line_from_non_move_token(self, event=None):
        """Set move before currrent token as current move."""
        del event
        self._set_nearest_move_to_token_as_currentmove()

        # self.set_current() already called but return is not via a method
        # which will call self.set_game_board().
        self.set_game_board()
        return "break"

    def _delete_empty_pgn_tag(self, event=None):
        """Delete empty PGN tag token."""
        del event
        widget = self.score
        start = widget.index(tkinter.INSERT + " linestart")
        tr_q = widget.tag_nextrange(PGN_TAG, start, START_SCORE_MARK)
        if tr_q:
            if widget.compare(start, "==", tr_q[0]):
                # Hack. Empty PGN Tag is len('[  "" ]').
                # Assume one PGN Tag per line.
                # Could change this to work like 'forced_newline', but PGN tags
                # are supposed to be preceded by a newline.
                if len(widget.get(*tr_q)) == 7:
                    widget.delete(*tr_q)
                    widget.delete(
                        tr_q[0] + "-1c"
                    )  # the preceding newline if any
                    # INSERT has moved to end of previous line.  Put INSERT at
                    # start of PGN tag after the deleted one.
                    self._to_prev_pgn_tag()
                    self._to_next_pgn_tag()
        return "break"

    def go_to_move(self, index):
        """Extend, set keyboard bindings for new pointer location."""
        if super().go_to_move(index):
            return True
        new_current = self._select_item_at_index(index)
        if new_current is None:
            return "break"
        return self._show_new_current(new_current)
