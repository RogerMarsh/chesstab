# gameedit_nonmove.py
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
import re

from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
    FEN_BLACK_BISHOP,
    PGN_BISHOP,
    PGN_CAPTURE_MOVE,
)
from pgn_read.core.parser import PGN
from pgn_read.core.game import GameStrictPGN

from ..core.constants import (
    START_RAV,
    START_COMMENT,
    ERROR_START_COMMENT,
    ESCAPE_END_COMMENT,
    HIDE_END_COMMENT,
    END_COMMENT,
)
from ..core.pgn import GameDisplayMoves
from . import gameedit_misc
from .constants import (
    EDIT_GLYPH,
    EDIT_RESULT,
    EDIT_PGN_TAG_NAME,
    EDIT_PGN_TAG_VALUE,
    EDIT_COMMENT,
    EDIT_RESERVED,
    EDIT_COMMENT_EOL,
    EDIT_ESCAPE_EOL,
    EDIT_MOVE_ERROR,
    EDIT_MOVE,
    INSERT_RAV,
    MOVE_EDITED,
    NAVIGATE_MOVE,  # absence matters if no EDIT_... exists
    NAVIGATE_TOKEN,
    TOKEN,
    RAV_MOVES,
    CHOICE,
    PRIOR_MOVE,
    RAV_TAG,
    POSITION,
    MOVE_TAG,
    START_SCORE_MARK,
    NAVIGATE_COMMENT,
    START_EDIT_MARK,
    END_EDIT_MARK,
    RAV_END_TAG,
    RAV_START_TAG,
)

# Error wrapper detector.
_error_wrapper_re = re.compile(
    r"".join(
        (
            r"(",
            START_COMMENT,
            r"\s*",
            ERROR_START_COMMENT,
            r".*?",
            ESCAPE_END_COMMENT,
            r"\s*",
            END_COMMENT,
            r")",
        )
    ),
    flags=re.DOTALL,
)


class GameEdit(gameedit_misc.GameEdit):
    """Display a game with editing allowed."""

    def get_implied_current_move(self):
        """Return implied current if self.current is RAV start.

        RAV start is associated with the position in which the first move
        of the RAV is made.  The implied current is the move made to reach
        this position.

        """
        assert self.current
        widget = self.score
        tr_q = widget.tag_ranges(self.current)
        if widget.get(*tr_q) == START_RAV:
            move = None
            for n_q in widget.tag_names(tr_q[0]):
                if n_q.startswith(PRIOR_MOVE):
                    for m_q in widget.tag_names(widget.tag_ranges(n_q)[0]):
                        if m_q.startswith(POSITION):
                            move = m_q
                            break
                    break
        else:
            move = self.current
        return move

    def add_move_to_moves_played_colouring_tag(self, move):
        """Extend. Allow for '(' as surrogate for move when placing RAVs."""
        widget = self.score
        tr_q = widget.tag_ranges(move)
        if widget.get(*tr_q) == START_RAV:
            for n_q in widget.tag_names(tr_q[0]):
                if n_q.startswith(PRIOR_MOVE):
                    for m_q in widget.tag_names(widget.tag_ranges(n_q)[0]):
                        if m_q.startswith(POSITION):
                            move = m_q
                            break
                    break
        super().add_move_to_moves_played_colouring_tag(move)

    def is_currentmove_being_edited(self):
        """Return True if currentmove is the text of an incomplete move.

        The incomplete move text is valid while it remains possible to append
        text that would convert the text to a valid move.  At this stage no
        attempt is made to rule out syntactically correct incomplete move text
        that cannot become a move such as "Rc" when the side to move has no
        rooks or no rook can reach the c-file.

        """
        return self.is_currentmove_in_edited_move()

    def is_currentmove_editable(self):
        """Return True if currentmove is one of the editable moves.

        The last move of a rav or the game is editable.  If such a move is
        being edited the move is also in the 'being edited' set.

        """
        return self.is_currentmove_in_edit_move()

    def is_game_or_rav_valid_without_move(self):
        """Return True if current move can be removed leaving valid PGN text.

        It is assumed the move to be removed is the last in the rav or game.

        Last move in game or variation may be followed by one or more RAVs
        which prevent deletion of move because the RAVs lose the move giving
        them meaning.  If such RAVs exist the next RAV end token will occur
        after the next move token.

        If the move is in a variation there may be, and probably are, move
        tokens after the variation's RAV end token.

        If the move is the only move in the variation the sequence
        ( <move> ( <move sequence> ) ) is possible and is equivalent to
        ( <move> ) ( <move sequence> ) and hence <move> can be deleted.  The
        problem is picking the ) token to delete along with <move>.

        """
        if not self.is_currentmove_in_main_line():
            if self.is_currentmove_start_of_variation():
                # Should any comments be ignored? (as done here)
                return True
        current = self.score.tag_ranges(self.current)
        next_move = self.score.tag_nextrange(NAVIGATE_MOVE, current[1])
        if next_move:
            next_rav_end = self.score.tag_nextrange(RAV_END_TAG, current[1])
            if self.score.compare(next_rav_end[0], ">", next_move[0]):
                return False
        return True

    def set_nearest_move_to_token_as_currentmove(self):
        """Set current, if a non-move token, to prior move token in game."""
        if self.current:
            # Hack coping with Page Down, Shift + Right to end, Control + Left,
            # Page Down in an imported game with errors being edited if there
            # is a token after the termination symbol. First two actions are
            # setup and last two cause program failure.
            self.current = self.get_nearest_move_to_token(self.current)
        self.set_current()
        self.apply_colouring_to_variation_back_to_main_line()
        # Set colouring of moves. This is either correct as stands (Alt-Left
        # for example) or base for modification (Alt-Right for example).

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    def add_text_pgntag_or_pgnvalue(self, token, tagset=(), separator=" "):
        """Add PGN Tagname or Tagvalue to game. Return POSITION tagname."""
        start, end, sepend = super().add_text_pgntag_or_pgnvalue(
            token, separator=separator
        )
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        del tokentag
        widget = self.score
        for tag in tagset:
            widget.tag_add(tag, start, end)
        widget.mark_set(tokenmark, end)
        for tag in (NAVIGATE_TOKEN,):
            widget.tag_add(tag, start, end)
        self.add_position_tag_to_pgntag_tags(positiontag, start, end)
        return start, end, sepend

    def delete_empty_token(self):
        """Delete empty non-move token from PGN movetext."""
        widget = self.score
        if widget.count(START_EDIT_MARK, END_EDIT_MARK)[0] > 1:
            return
        tr_q = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if tr_q:
            current = self.select_prev_token_in_game()
            if not current:
                current = self.select_next_token_in_game()
            widget.delete(*tr_q)
            self.delete_forced_newline_token_prefix(NAVIGATE_TOKEN, tr_q)
            del self.tagpositionmap[self.current]
            self.current = current
            self.set_current()
            self.set_game_board()
            return

    def delete_char_next_to_insert_mark(self, first, last):
        """Delete char after INSERT mark if INSERT equals first, else before.

        (first, last) should be (START_EDIT_MARK, Tkinter.INSERT) or
        (Tkinter.INSERT, END_EDIT_MARK).  A character is deleted only if the
        count of characters between first and last is greater than zero.  One
        of the characters next to the INSERT mark is deleted depending on the
        equality of first and INSERT mark.  If leading characters exist for
        the token when the text length is zero, the last of these is tagged
        with MOVE_TEXT (instead of the token characters).

        """
        widget = self.score
        if widget.count(first, last)[0]:
            if widget.compare(first, "==", tkinter.INSERT):
                widget.delete(tkinter.INSERT)
            else:
                widget.delete(tkinter.INSERT + "-1 chars")
            if widget.count(START_EDIT_MARK, END_EDIT_MARK)[0] == 0:
                if (
                    self._lead_trail.lead
                ):  # self.current will have a range. Or test range.
                    widget.tag_add(
                        MOVE_TAG,
                        "".join(
                            (
                                str(widget.tag_ranges(self.current)[0]),
                                " +",
                                str(self._lead_trail.lead - 1),
                                "chars",
                            )
                        ),
                    )

    def get_rav_tag_of_index(self, index):
        """Return Tk tag name if index is in a rav_tag tag."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(RAV_TAG):
                return tn_q
        return None

    def get_previous_move_to_position(self, position):
        """Return previous move (may be None) to position, otherwise False.

        position is a POSITION<suffix> tag name which may no longer have any
        tagged characters but TOKEN<suffix> still tags at least one character.

        """
        # Find the previous token then call get_nearest_move_to_token.
        tr_q = self.score.tag_ranges(self.get_token_tag_for_position(position))
        if tr_q:
            return self.get_nearest_move_to_token(
                self.get_token_tag_of_index(
                    self.score.tag_prevrange(NAVIGATE_TOKEN, tr_q[0])[0]
                )
            )
        return False

    def insert_empty_comment(self):
        """Insert "{<null>) " sequence."""
        self.set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self.add_start_comment("{}", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t_q[0]

    def insert_empty_comment_to_eol(self):
        r"""Insert ";<null>\n " sequence."""
        self.set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self.add_comment_to_eol(";\n", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t_q[0]

    def insert_empty_escape_to_eol(self):
        r"""Insert "\n%<null>\n " sequence.

        Leading '\n' is the PGN rule.  Here this is done as a consequence
        of putting all non-move movetext tokens on their own line.  Thus
        identical to comment to EOL except '%' not ';' at beginning.

        """
        self.set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self.add_escape_to_eol("%\n", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t_q[0]

    def insert_empty_glyph(self):
        """Insert "$<null> " sequence."""
        self.set_insertion_point_before_next_token(between_newlines=False)
        t_q = self.add_glyph("$", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t_q[0]

    def insert_empty_pgn_tag(self):
        """Insert ' [ <null> "<null>" ] ' sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        self.add_pgntag_to_map("", "")

    def insert_empty_pgn_seven_tag_roster(self):
        """Insert ' [ <fieldname> "<null>" ... ] ' seven tag roster tags."""
        self.set_insertion_point_before_next_pgn_tag()
        for t_q in SEVEN_TAG_ROSTER:
            self.add_pgntag_to_map(t_q, "")

    def insert_empty_reserved(self):
        """Insert "<[null]>) " sequence."""
        self.set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self.add_start_reserved("<>", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t_q[0]

    def is_move_last_of_variation(self, move):
        """Return True if currentmove is at end of a variation tag."""
        widget = self.score
        index = widget.tag_ranges(move)[1]
        for tn_q in widget.tag_names(index):
            if tn_q.startswith(RAV_MOVES):
                return not bool(self.score.tag_nextrange(tn_q, index))
        return None

    def is_move_start_of_variation(self, move, variation):
        """Return True if move is at start of variation."""
        widget = self.score
        return widget.compare(
            widget.tag_ranges(move)[0], "==", widget.tag_ranges(variation)[0]
        )

    # Renamed from is_movetext_insertion_allowed because it is possible to
    # assume it means 'moves can be inserted' but NOT other things allowed in
    # movetext.  (This had bad, but nearly always non-fatal, consequences in
    # set_current method!)
    # The docstring says what the method does.
    # PGN has two areas: tags and movetext.
    # The method is_pgn_tag_insertion_allowed is therefore removed and calls
    # replaced by is_current_in_movetext calls.
    def is_current_in_movetext(self):
        """Return True if current is not before start of movetext."""
        return bool(
            self.score.compare(
                START_SCORE_MARK, "<=", self.score.tag_ranges(self.current)[0]
            )
        )

    # Renamed from is_rav_insertion_allowed to fit docstring better, which is
    # what the method does.
    # If current is last move in game or variation a new move is appended, but
    # a RAV is inserted elsewhere if allowed (not decided by this method).
    def is_at_least_one_move_in_movetext(self):
        """Return True if at least one move exists in game score."""
        # To be decided if at least one legal move exists.  Check EDIT_MOVE
        # instead?
        return bool(self.score.tag_nextrange(NAVIGATE_MOVE, "1.0"))

    def get_range_of_prior_move(self, start):
        """Override. Return range of PRIOR_MOVE tag before start.

        The GameEdit class tags '('s with a PRIOR_MOVE tag which can be used
        directly to get the range for the prior move.

        Presence of the PRIOR_MOVE tag on '(' breaks the algorithm used in
        the Score class' version of this method.

        """
        widget = self.score
        for n_q in widget.tag_names(start):
            if n_q.startswith(CHOICE):
                return widget.tag_prevrange(
                    self.get_prior_tag_for_choice(n_q), start
                )
            if n_q.startswith(PRIOR_MOVE):
                return widget.tag_nextrange(n_q, START_SCORE_MARK)
        return None

    def process_move(self):
        """Splice a move being edited into the game score.

        In English PGN piece and file designators are case insensitive except
        for 'b' and 'B'.  Movetext like 'bxc4' and 'bxa4' could mean a pawn
        move or a bishop move.

        Typing 'B' means a bishop move and typing 'b' means a pawn move unless
        the specified pawn move is illegal when it means a bishop move if that
        is possible.  Where both pawn and bishop moves are legal a dialogue
        prompting for a decision is given.

        """
        widget = self.score
        movetext = widget.get(*widget.tag_ranges(self.current))
        mtc = next(
            PGN(game_class=GameDisplayMoves).read_games(
                movetext.join(self.edit_move_context[self.current])
            )
        )
        if mtc.is_movetext_valid():
            bishopmove = False
            if (
                movetext.startswith(FEN_BLACK_BISHOP + PGN_CAPTURE_MOVE)
                and movetext[2] in "ac"
                and movetext[3] not in "18"
            ):
                amtc = next(
                    PGN(game_class=GameDisplayMoves).read_games(
                        (PGN_BISHOP + movetext[1:]).join(
                            self.edit_move_context[self.current]
                        )
                    )
                )
                if amtc.is_movetext_valid():
                    if tkinter.messagebox.askyesno(
                        parent=self.ui.get_toplevel(),
                        title="Bishop or Pawn Capture",
                        message="".join(
                            (
                                "Movetext '",
                                movetext,
                                "' would be a bishop ",
                                "move if 'b' were 'B'.\n\n",
                                "Is it a bishop move?",
                            )
                        ),
                    ):
                        bishopmove = True
                        mtc = amtc
            self.tagpositionmap[self.current] = (
                mtc._piece_placement_data.copy(),
                mtc._active_color,
                mtc._castling_availability,
                mtc._en_passant_target_square,
                mtc._halfmove_clock,
                mtc._fullmove_number,
            )
            del self.edit_move_context[self.current]
            # remove from MOVE_EDITED tag and place on EDIT_MOVE tag
            # removed from EDIT_MOVE tag and placed on INSERT_RAV tag when
            # starting insert of next move.
            start, end = self.score.tag_ranges(self.current)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(MOVE_EDITED, start, end)
            if bishopmove:
                widget.insert(widget.index(start) + "+1 char", PGN_BISHOP)
                widget.delete(widget.index(start))
            self.set_current()
            self.set_game_board()
            return

        # 'b' may have been typed meaning bishop, not pawn on b-file.
        # If so the movetext must be at least 3 characters, or 4 characters
        # for a capture.
        if movetext[0] != FEN_BLACK_BISHOP:
            return
        if len(movetext) < 3:
            return
        if len(movetext) < 4 and movetext[1] == PGN_CAPTURE_MOVE:
            return
        mtc = next(
            PGN(game_class=GameDisplayMoves).read_games(
                (PGN_BISHOP + movetext[1:]).join(
                    self.edit_move_context[self.current]
                )
            )
        )
        if mtc.is_movetext_valid():
            self.tagpositionmap[self.current] = (
                mtc._piece_placement_data.copy(),
                mtc._active_color,
                mtc._castling_availability,
                mtc._en_passant_target_square,
                mtc._halfmove_clock,
                mtc._fullmove_number,
            )
            del self.edit_move_context[self.current]
            # remove from MOVE_EDITED tag and place on EDIT_MOVE tag
            # removed from EDIT_MOVE tag and placed on INSERT_RAV tag when
            # starting insert of next move.
            start, end = self.score.tag_ranges(self.current)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(MOVE_EDITED, start, end)
            widget.insert(widget.index(start) + "+1 char", PGN_BISHOP)
            widget.delete(widget.index(start))
            self.set_current()
            self.set_game_board()

    def select_item_at_index(self, index):
        """Return the itemtype tag associated with index."""
        try:
            tns = set(self.score.tag_names(index))
            # EDIT_PGN_TAG_VALUE before EDIT_PGN_TAG_NAME as both tag values
            # while only EDIT_PGN_TAG_NAME tags names.
            for tagtype in (
                EDIT_PGN_TAG_VALUE,
                EDIT_PGN_TAG_NAME,
                EDIT_GLYPH,
                EDIT_RESULT,
                EDIT_COMMENT,
                EDIT_RESERVED,
                EDIT_COMMENT_EOL,
                EDIT_ESCAPE_EOL,
                EDIT_MOVE_ERROR,
                EDIT_MOVE,
                INSERT_RAV,
                MOVE_EDITED,
            ):
                if tagtype in tns:
                    for tn_q in tns:
                        if tn_q.startswith(POSITION):
                            return tn_q
        except IndexError:
            # Not sure the explicit setting is needed.
            self._allowed_chars_in_token = ""
            return None
        # Not sure the explicit setting is needed.
        self._allowed_chars_in_token = ""
        return None

    def select_first_comment_in_game(self):
        """Return POSITION tag associated with first comment in game."""
        return self.select_first_item_in_game(NAVIGATE_COMMENT)

    def select_last_comment_in_game(self):
        """Return POSITION tag associated with last comment in game."""
        return self.select_last_item_in_game(NAVIGATE_COMMENT)

    def select_next_comment_in_game(self):
        """Return POSITION tag for comment after current in game."""
        return self.select_next_item_in_game(NAVIGATE_COMMENT)

    def select_prev_comment_in_game(self):
        """Return POSITION tag for comment before current in game."""
        return self.select_prev_item_in_game(NAVIGATE_COMMENT)

    def select_next_pgn_tag_field_name(self):
        """Return POSITION tag for nearest following PGN Tag field."""
        widget = self.score
        try:
            if self.current:
                index = widget.tag_nextrange(
                    NAVIGATE_TOKEN,
                    widget.index(
                        str(widget.tag_ranges(self.current)[0]) + " lineend"
                    ),
                    START_SCORE_MARK,
                )
                for tn_q in widget.tag_names(index[0]):
                    if tn_q.startswith(POSITION):
                        return tn_q
        except IndexError:
            return self.current
        return self.current

    def select_prev_pgn_tag_field_name(self):
        """Return POSITION tag for nearest preceding PGN Tag field."""
        widget = self.score
        try:
            if self.current:
                index = widget.tag_prevrange(
                    NAVIGATE_TOKEN,
                    widget.index(
                        str(widget.tag_ranges(self.current)[0]) + " linestart"
                    ),
                )
                for tn_q in widget.tag_names(index[0]):
                    if tn_q.startswith(POSITION):
                        return tn_q
            else:
                index = widget.tag_prevrange(
                    NAVIGATE_TOKEN,
                    widget.tag_prevrange(NAVIGATE_TOKEN, START_SCORE_MARK)[0],
                )
                for tn_q in widget.tag_names(index[0]):
                    if tn_q.startswith(POSITION):
                        return tn_q
        except IndexError:
            return self.current
        return self.current

    def select_nearest_pgn_tag(self):
        """Return POSITION tag for nearest preceding PGN Tag field."""
        # do nothing at first
        return self.current

    def select_first_token_in_game(self):
        """Return POSITION tag associated with first token in game."""
        return self.select_first_item_in_game(NAVIGATE_TOKEN)

    def select_last_token_in_game(self):
        """Return POSITION tag associated with last token in game."""
        return self.select_last_item_in_game(NAVIGATE_TOKEN)

    def select_next_rav_start_in_game(self):
        """Return POSITION tag associated with RAV after current in game."""
        return self.select_next_item_in_game(RAV_START_TAG)

    def select_prev_rav_start_in_game(self):
        """Return POSITION tag associated with RAV before current in game."""
        return self.select_prev_item_in_game(RAV_START_TAG)

    def set_insert_mark_at_end_of_token(self):
        """Move insert mark to end edit mark."""
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)

    def set_insert_mark_at_start_of_token(self):
        """Move insert mark to start edit mark."""
        self.score.mark_set(tkinter.INSERT, START_EDIT_MARK)

    def set_insert_mark_down_one_line(self):
        """Move insert mark down one line limited by end edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, "<", END_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + " +1 display lines"
            )
            if widget.compare(tkinter.INSERT, ">", END_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, END_EDIT_MARK)

    def set_insert_mark_left_one_char(self):
        """Move insert mark left one character limited by start edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, ">", START_EDIT_MARK):
            widget.mark_set(tkinter.INSERT, tkinter.INSERT + " -1 chars")

    def set_insert_mark_right_one_char(self):
        """Move insert mark right one character limited by end edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, "<", END_EDIT_MARK):
            widget.mark_set(tkinter.INSERT, tkinter.INSERT + " +1 chars")

    def set_insert_mark_up_one_line(self):
        """Move insert mark up one line limited by start edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, ">", START_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + " -1 display lines"
            )
            if widget.compare(tkinter.INSERT, "<", START_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, START_EDIT_MARK)

    def get_token_range(self, tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames."""
        for tn_q in tagnames:
            if tn_q.startswith(TOKEN):
                return self.score.tag_nextrange(tn_q, "1.0")
        return None

    def set_marks_for_editing_comment_eol(self, tagnames, tagranges):
        """Set token editing bound marks from TOKEN<suffix> in tagnames."""
        start, end = tagranges
        if self.score.count(start, end)[0] < 2:
            for tn_q in tagnames:
                if tn_q.startswith(TOKEN):
                    start = self.score.tag_nextrange(tn_q, "1.0")[0]
                    break
            else:
                return
        self.score.mark_set(START_EDIT_MARK, start)
        self.score.mark_set(END_EDIT_MARK, end)
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)
        self.set_move_tag(START_EDIT_MARK, END_EDIT_MARK)

    def _add_char_to_token(self, char):
        """Insert char at insert point."""
        if not char:
            return None
        if self._allowed_chars_in_token:
            if char not in self._allowed_chars_in_token:
                return None
        widget = self.score
        start, end = widget.tag_ranges(self.current)
        non_empty = (
            widget.count(start, end)[0] - self._lead_trail.header_length
        )
        insert = str(widget.index(tkinter.INSERT))
        copy_from_insert = widget.compare(start, "==", insert)
        widget.insert(tkinter.INSERT, char)
        if copy_from_insert:
            for tn_q in widget.tag_names(tkinter.INSERT):
                widget.tag_add(tn_q, insert)
        else:
            for tn_q in widget.tag_names(start):
                widget.tag_add(tn_q, insert)
        # MOVE_TAG must tag something if token has leading and trailing only.
        widget.tag_add(MOVE_TAG, insert)
        if not non_empty:
            widget.tag_remove(
                MOVE_TAG,
                "".join(
                    (str(start), " +", str(self._lead_trail.lead - 1), "chars")
                ),
            )
        return True

    def get_score_error_escapes_removed(self):
        """Unwrap valid PGN text wrapped by '{Error:  ::{{::}' comments.

        The editor uses Game as the game_class argument to PGN but strict
        adherence to PGN is enforced when unwrapping PGN text: GameStrictPGN
        is the game_class argument to PGN.

        """
        text = self.score.get("1.0", tkinter.END)
        t_q = _error_wrapper_re.split(text)
        if len(t_q) == 1:
            return text
        parser = PGN(game_class=GameStrictPGN)
        mtc = next(parser.read_games(text))
        if mtc.state:
            return text
        replacements = 0
        candidates = 0
        tc_q = t_q.copy()
        for e_q in range(1, len(t_q), 2):
            candidates += 1
            tc_q[e_q] = (
                tc_q[e_q]
                .rstrip(END_COMMENT)
                .rstrip()
                .rstrip(ESCAPE_END_COMMENT)
                .lstrip(START_COMMENT)
                .lstrip()
                .lstrip(ERROR_START_COMMENT)
                .replace(HIDE_END_COMMENT, END_COMMENT)
            )
            mtc = next(parser.read_games("".join(tc_q)))
            if mtc.state:
                tc_q[e_q] = t_q[e_q]
            else:
                replacements += 1
        if replacements == 0:
            return text
        return "".join(tc_q)
