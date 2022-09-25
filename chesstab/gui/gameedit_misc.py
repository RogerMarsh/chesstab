# gameedit_misc.py
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

from pgn_read.core.constants import (
    TAG_RESULT,
    TAG_FEN,
    TAG_SETUP,
    SETUP_VALUE_FEN_PRESENT,
)

from ..core.constants import (
    UNKNOWN_RESULT,
    END_RAV,
    END_TAG,
    START_TAG,
)
from . import gameedit_widget
from .score import NonTagBind
from ._lead_trail import _LeadTrail
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
    RAV_SEP,
    RAV_TAG,
    POSITION,
    MOVE_TAG,
    START_SCORE_MARK,
    TOKEN_MARK,
    START_EDIT_MARK,
    END_EDIT_MARK,
    PGN_TAG,
    RAV_END_TAG,
    TERMINATION_TAG,
    RAV_START_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    FORCED_NEWLINE_TAG,
    FORCE_NEWLINE_AFTER_FULLMOVES,
)

# Each editable PGN item is tagged with one tag from this set.
# Except that PGN Tag Values get tagged with EDIT_PGN_TAG_NAME as well as the
# intended EDIT_PGN_TAG_VALUE.  Corrected by hack.
_EDIT_TAGS = frozenset(
    (
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
    )
)

# Leading and trailing character counts around PGN item payload characters
_TOKEN_LEAD_TRAIL = {
    EDIT_GLYPH: (1, 0),
    EDIT_RESULT: (0, 0),
    EDIT_PGN_TAG_NAME: (1, 0),
    EDIT_PGN_TAG_VALUE: (1, 0),
    EDIT_COMMENT: (1, 1),
    EDIT_RESERVED: (1, 1),
    EDIT_COMMENT_EOL: (1, 0),
    EDIT_ESCAPE_EOL: (1, 0),
    EDIT_MOVE_ERROR: (0, 0),
    EDIT_MOVE: (0, 0),
    INSERT_RAV: (0, 0),
    MOVE_EDITED: (0, 0),
}

# The characters used in moves. Upper and lower case L are included as synonyms
# for B to allow shiftless typing of moves such as Bb5.
_MOVECHARS = "abcdefghklnoqrABCDEFGHKLNOQR12345678xX-="
# These may be moved to pgn.constants.py as the values are derived from the
# PGN specification (but their use is here only).
# allowed in comment to eol and escape to eol
_ALL_PRINTABLE = "".join(
    (
        "".join(
            [chr(i) for i in range(ord(" "), 127)]
        ),  # symbols and string data
        "".join(
            [chr(i) for i in range(160, 192)]
        ),  # string data but discouraged
        "".join([chr(i) for i in range(192, 256)]),  # string data
    )
)
# allowed in ';comments\n' and '%escaped lines\n'
_ALL_PRINTABLE_AND_NEWLINE = "".join(("\n", _ALL_PRINTABLE))
# allowed in {comments}
_ALL_PRINTABLE_AND_NEWLINE_WITHOUT_BRACERIGHT = "".join(
    ("\n", _ALL_PRINTABLE)
).replace("}", "")
# allowed in <reserved>
_ALL_PRINTABLE_AND_NEWLINE_WITHOUT_GREATER = "".join(
    ("\n", _ALL_PRINTABLE)
).replace(">", "")
# allowed in PGN tag names
_PGN_TAG_NAMES = "".join(
    (
        "0123456789",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "_",
        "abcdefghijklmnopqrstuvwxyz",
    )
)
# allowed in PGN tag values (not quite right as \ and " can be escaped by \)
_ALL_PRINTABLE_WITHOUT_QUOTEDBL = _ALL_PRINTABLE.replace('"', "")
# allowed in glyphs
_GLYPHS = "0123456789"
# allowed in game termination and Results PGN tag value
_TERMINATOR = "-/012*"

# lookup dictionary for characters allowed in tokens with given tag
_CHARACTERS_ALLOWED_IN_TOKEN = {
    EDIT_GLYPH: _GLYPHS,
    EDIT_RESULT: _TERMINATOR,
    EDIT_PGN_TAG_NAME: _PGN_TAG_NAMES,
    EDIT_PGN_TAG_VALUE: _ALL_PRINTABLE_WITHOUT_QUOTEDBL,
    EDIT_COMMENT: _ALL_PRINTABLE_AND_NEWLINE_WITHOUT_BRACERIGHT,
    EDIT_RESERVED: _ALL_PRINTABLE_AND_NEWLINE_WITHOUT_GREATER,
    EDIT_COMMENT_EOL: _ALL_PRINTABLE_AND_NEWLINE,
    EDIT_ESCAPE_EOL: _ALL_PRINTABLE_AND_NEWLINE,
    EDIT_MOVE_ERROR: _MOVECHARS,
    EDIT_MOVE: _MOVECHARS,
    INSERT_RAV: _MOVECHARS,
    MOVE_EDITED: _MOVECHARS,
}

# PGN validation wrapper for editing moves.
_EDIT_MOVE_CONTEXT = (
    "".join(
        (
            START_TAG,
            TAG_SETUP,
            '"',
            SETUP_VALUE_FEN_PRESENT,
            '"',
            END_TAG,
            START_TAG,
            TAG_FEN,
            '"',
        )
    ),
    "".join(('"', END_TAG)),
)


class GameEdit(gameedit_widget.GameEdit):
    """Display a game with editing allowed."""

    # One set of bindings is needed for each self._most_recent_bindings value
    # tested.  That means one method to do the binding and one popup menu for
    # each set of bindings.
    # Take opportunity to rename self.veiwmode_popup as self.move_popup with
    # additional menus: but not yet as too many non-gameedit modules need
    # modifying.  It is inherited from Score.  self.selectmode_popup, also
    # inherited from Score, will be renamed select_move_popup.  Later
    # self.move_popup renamed to self.primay_activity_popup to be same as in
    # SharedText.
    # self.inactive_popup seems ok.
    # self.viewmode_comment_popup and self.viewmode_pgntag_popup can just drop
    # viewmode_ from their names.  The only references outside gameedit are in
    # gamedisplay and repertoiredisplay, four in all.  Ok to do now.
    # Event handler to post pgn_tag_popup menu is renamed post_pgn_tag_menu.
    # Two new ones, start_rav_popup and end_rav_popup, are needed.  It may be
    # best to have one each for all the editable tokens, in particular escaped
    # line and comment to end of line, to cope with the slight variation in
    # editing rules.
    # The bind_for_primary_activity() call must be replaced because it may,
    # probably will, occur when not in select variation state.
    def set_current(self):
        """Override to set edit and navigation bindings for current token.

        All significant characters except RAV markers have one tag which
        indicates the edit rules that apply to the token containing the
        character.  The absence of such a tag indicates the character may be a
        RAV marker.  Default is no editing.

        RAV markers are used to adjust the insertion point for a new RAV,
        compared with insertion when a move is the current token, but
        cannot be edited.

        """
        # This method and those called adjust bindings so do not call context
        # independent binding setup methods after this method for an event.
        # May add RAV markers to _EDIT_TAGS eventually.
        # Editing token possible only if no moves in game score.
        tagranges = self.set_current_range()
        if tagranges:
            tagnames = self.score.tag_names(tagranges[0])
            if tagnames:
                tns = set(tagnames)
                tn_q = tns.intersection(_EDIT_TAGS)
                if tn_q:

                    # Hack to deal with PGN Tag Value tagging while these items
                    # are tagged by EDIT_PGN_TAG_VALUE and EDIT_PGN_TAG_NAME
                    tnn = tn_q.pop()
                    if EDIT_PGN_TAG_VALUE in tn_q:
                        tnn = EDIT_PGN_TAG_VALUE

                    # Could replace 'not self.is_current_in_movetext()' with
                    # 'PGN_TAG in tns', but a 'self.is_current_in_movetext()'
                    # just before the 'else' clause becomes wise.
                    # Maybe explicit tests for all the EDIT_* tags (Tk sense)
                    # is best.
                    self.set_token_context(tagnames, tagranges, tnn)

                # The '(' and ')' around a RAV are the only things that matched
                # for original 'else' clause.  The 'else' is retained for
                # unexpected cases, and the RAV_START_TAG and RAV_END_TAG
                # clauses are introduced to support alternate placement of
                # inserted RAVs.  (Code for each clause will be put in methods
                # for tidiness.)
                # (That code was wrapped in chain of methods used here only,
                # and protected by a test based on false assumption.)
                elif RAV_END_TAG in tns:
                    if self._most_recent_bindings != RAV_END_TAG:
                        self.token_bind_method[RAV_END_TAG](self)
                    self.score.mark_set(tkinter.INSERT, tagranges[1])
                    self.set_move_tag(*tagranges)
                elif RAV_START_TAG in tns:
                    if self._most_recent_bindings != RAV_START_TAG:
                        self.token_bind_method[RAV_START_TAG](self)
                    self.score.mark_set(tkinter.INSERT, tagranges[1])
                    self.set_move_tag(*tagranges)
                else:
                    if (
                        self._most_recent_bindings
                        != NonTagBind.DEFAULT_BINDINGS
                    ):
                        self.token_bind_method[NonTagBind.DEFAULT_BINDINGS](
                            self
                        )
                    self.score.mark_set(tkinter.INSERT, tagranges[1])
                    self.set_move_tag(*tagranges)

                return
        elif self.current is None:
            if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
                self.token_bind_method[NonTagBind.NO_EDITABLE_TAGS](self)
            self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
            if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
                self.bind_for_primary_activity()
            return

        # Disable editing.  (This was wrapped in a method used here only.)
        # (Just the popup menu route to block now: after reorganising menus.)
        if self._most_recent_bindings != NonTagBind.CURRENT_NO_TAGS:
            self.token_bind_method[NonTagBind.CURRENT_NO_TAGS](self)

    def add_pgntag_to_map(self, name, value):
        r"""Add a PGN Tag, a name and value, to the game score.

        The PGN Tag consists of two editable tokens: the Tag name and the Tag
        value.  These are inserted and deleted together, never separately,
        formatted as [ <name> "<value>" ]\n.

        """
        widget = self.score
        start_tag = widget.index(tkinter.INSERT)
        # tag_symbols is, with tag having its Tk meaning,
        # ((<name tag suffix>, <range>), (<value tag suffix>, <range>))
        tag_symbols = super().add_pgntag_to_map(name, value)
        widget.tag_add(PGN_TAG, start_tag, str(tkinter.INSERT) + "-1c")
        widget.mark_set(
            START_SCORE_MARK,
            widget.index(widget.tag_prevrange(PGN_TAG, tkinter.END)[-1])
            + "+1c",
        )
        for et_q, ts_q in zip(
            (EDIT_PGN_TAG_NAME, EDIT_PGN_TAG_VALUE), tag_symbols
        ):
            widget.tag_add(et_q, *ts_q[-1])
        if name == TAG_RESULT:
            widget.tag_add(TERMINATION_TAG, *tag_symbols[-1][-1])
        return tag_symbols

    def add_position_tag_to_pgntag_tags(self, tag, start, end):
        """Add position tag to to PGN Tag tokens for position display.

        Navigation to non-move tokens is allowed in edit mode and the initial
        position of the game is displayed when a PGN Tag is current.

        """
        self.score.tag_add(tag, start, end)
        self.tagpositionmap[tag] = self.fen_tag_tuple_square_piece_map()

    def delete_forced_newline_token_prefix(self, tag, range_):
        """Delete nearest newline in tag before range_ keeping lines short.

        Newline is not deleted if a sequence of fullmoves longer than
        FORCE_NEWLINE_AFTER_FULLMOVES without a newline would be created.

        """
        # Maybe always look at NAVIGATE_TOKEN if the search can be stopped
        # at start of movetext: is this START_SCORE_MARK at all times.  Doubt
        # is when START_SCORE_MARK is set.
        widget = self.score
        tpr = widget.tag_prevrange(tag, range_[0])
        if not tpr:
            return
        forced_newline = widget.tag_prevrange(
            FORCED_NEWLINE_TAG, range_[0], tpr[-1]
        )
        if not forced_newline:
            return

        # Do not delete both newlines around the RAV being deleted if
        # it the last one in a list of several for a move.

        # A non-move token before, and adjacent to, a forced newline will
        # leave '\n\n' when deleted, failing the 'len(tri)' test if there
        # are more than FORCE_NEWLINE_AFTER_FULLMOVES fullmoves enclosing
        # the token without a non-move token.  Second newline is forced
        # newline associated with adjacent token: delete other one.
        if widget.get(*forced_newline) == "\n\n":
            nttpr = widget.tag_prevrange(NAVIGATE_TOKEN, range_[0])
            widget.delete(forced_newline[0])
            forced_newline = widget.tag_prevrange(
                FORCED_NEWLINE_TAG, range_[0], tpr[-1]
            )
            if not forced_newline:
                return
            nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, forced_newline[-1])
            if nttnr and NAVIGATE_MOVE not in widget.tag_names(nttnr[0]):
                if widget.get(*nttnr) != END_RAV:
                    return
            if not nttnr:
                return
            if nttpr:
                if RAV_START_TAG in widget.tag_names(nttpr[0]):
                    widget.delete(*forced_newline)
                    return
                if NAVIGATE_MOVE not in widget.tag_names(nttpr[0]):
                    return

        fnltpr = widget.tag_prevrange(FORCED_NEWLINE_TAG, forced_newline[0])
        if not fnltpr:
            fnltpr = [widget.index(START_SCORE_MARK)]
        fnltnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, forced_newline[-1])
        if not fnltnr:
            fnltnr = [widget.index(tkinter.END)]
        tri = 0
        if fnltpr or fnltnr:
            tr_q = widget.tag_ranges(NAVIGATE_MOVE)
            pr_q = fnltpr[-1]
            nr_q = fnltnr[0]
            for ti_q in tr_q:
                if widget.compare(ti_q, ">", pr_q) and widget.compare(
                    ti_q, "<", nr_q
                ):
                    tri += 1

        # Two tokens per fullmove; two index values per token. So * 4.
        if tri <= FORCE_NEWLINE_AFTER_FULLMOVES * 4:
            widget.delete(*forced_newline)

    def get_choice_tag_and_range_of_first_move(self):
        """Return choice tag name and range of first char for first move."""
        tr_q = self.score.tag_nextrange(NAVIGATE_MOVE, "1.0")
        if tr_q:
            return self.get_choice_tag_of_index(tr_q[0]), tr_q
        return None

    def get_prior_tag_and_range_of_move(self, move):
        """Return prior move tag name and move range for move tag."""
        tr_q = self.score.tag_ranges(move)
        if tr_q:
            return self.get_prior_tag_of_index(tr_q[0]), tr_q
        return None

    def get_prior_tag_of_index(self, index):
        """Return Tk tag name if index is in a choice tag."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(PRIOR_MOVE):
                return tn_q
        return None

    def get_rav_moves_of_index(self, index):
        """Return Tk tag name if index is in a rav_moves tag."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(RAV_MOVES):
                return tn_q
        return None

    @staticmethod
    def get_rav_tag_for_rav_moves(rav_moves):
        """Return Tk tag name for RAV_TAG with same suffix as rav_moves."""
        return "".join((RAV_TAG, rav_moves[len(RAV_MOVES) :]))

    @staticmethod
    def get_token_tag_for_position(position):
        """Return Tk tag name for token with same suffix as position."""
        return "".join((TOKEN, position[len(POSITION) :]))

    def get_token_tag_of_index(self, index):
        """Return Tk tag name if index is in TOKEN tag."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(TOKEN):
                return tn_q
        return None

    def get_variation_tag_of_index(self, index):
        """Return Tk tag name for variation of currentmove."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(RAV_MOVES):
                return tn_q
        return None

    def get_nearest_move_to_token(self, token):
        """Return tag for nearest move to token.

        The nearest move to a move is itself.
        The nearest move to a RAV start is the prior move.
        The nearest move to a RAV end is the move after the prior move in the
        RAV of the prior move.
        The nearest move to any other token is the nearest move to the first
        move or RAV start or RAV end found preceding the token.

        """
        widget = self.score
        r_q = widget.tag_ranges(token)
        while r_q:
            if r_q == widget.tag_nextrange(NAVIGATE_MOVE, *r_q):
                return self.get_position_tag_of_index(r_q[0])
            prior = self.get_prior_tag_of_index(r_q[0])
            if prior:
                if widget.tag_nextrange(RAV_END_TAG, *r_q):
                    return self.select_next_move_in_line(
                        movetag=self.get_position_tag_of_index(
                            widget.tag_ranges(prior)[0]
                        )
                    )
                return self.get_position_tag_of_index(
                    widget.tag_ranges(prior)[0]
                )
            r_q = widget.tag_prevrange(
                NAVIGATE_TOKEN, r_q[0], START_SCORE_MARK
            )

    def find_choice_prior_move_variation_main_move(self, tag_names):
        """Return arguments for insert_rav derived from RAV tag in tag_names.

        The choice tag will be the one which tags the characters tagged by
        the variation identifier tag with the same numeric suffix as the RAV
        tag.  choice is set None if no match exists, and implies there is
        something wrong and no RAV insertion should be done.

        The prior_move tag is the one with the 'prior move' prefix in
        tag_names.  prior_move is set None if this tag is absent, and implies
        the RAV is being inserted for the first move in the game.

        """
        widget = self.score
        variation_prefix = "".join((RAV_SEP, RAV_MOVES))

        # PRIOR_MOVE not in search because it will not be present if the
        # RAV is for the first move.
        search = {CHOICE}
        search_done = False

        choice = None
        prior_move = None
        variation_containing_choice = None
        main_line_move = None
        for n_q in tag_names:
            if n_q.startswith(RAV_TAG):
                rsrm = "".join((variation_prefix, n_q.lstrip(RAV_TAG)))
                for en_q in widget.tag_names(widget.tag_ranges(rsrm)[0]):
                    if en_q.startswith(CHOICE):
                        choice = en_q
                        variation_containing_choice = rsrm
                        search.remove(CHOICE)
                        break
                search_done = True
                if prior_move:
                    break
            elif n_q.startswith(PRIOR_MOVE):
                prior_move = n_q
                for en_q in widget.tag_names(widget.tag_ranges(prior_move)[0]):
                    if en_q.startswith(POSITION):
                        main_line_move = en_q
                        break
                if search_done:
                    break
        if prior_move is None:
            for n_q in widget.tag_names(
                widget.tag_nextrange(NAVIGATE_TOKEN, START_SCORE_MARK)[0]
            ):
                if n_q.startswith(POSITION):
                    main_line_move = n_q
                    break
        return choice, prior_move, variation_containing_choice, main_line_move

    def get_nearest_in_tags_between_point_and_end(self, point, tags):
        """Return nearest index of a tag in tags after point.

        tkinter.END is returned if no ranges are found after point in any of
        the tags.

        """
        widget = self.score
        nearest = tkinter.END
        for tag in tags:
            nr_q = widget.tag_nextrange(tag, point)
            if nr_q and widget.compare(nr_q[0], "<", nearest):
                nearest = nr_q[0]
        return nearest

    def is_currentmove_in_edit_move(self):
        """Return True if current move is editable.

        If there are no moves in the game current move is defined as editable.
        This allows games to be inserted.

        """
        if self.current is None:
            return not bool(self.score.tag_nextrange(NAVIGATE_MOVE, "1.0"))
        start, end = self.score.tag_ranges(self.current)
        return bool(self.score.tag_nextrange(EDIT_MOVE, start, end))

    def is_currentmove_in_edited_move(self):
        """Return True if current move is being edited.

        If there are no moves in the game current move is not being edited.

        """
        if self.current is None:
            return bool(self.score.tag_nextrange(NAVIGATE_MOVE, "1.0"))
        start, end = self.score.tag_ranges(self.current)
        return bool(self.score.tag_nextrange(MOVE_EDITED, start, end))

    # Do the add_* methods need position even though the map_* methods do not?
    def link_inserts_to_moves(self, positiontag, position):
        """Link inserted comments to moves for matching position display."""
        self.tagpositionmap[positiontag] = position
        if self.current:
            variation = self.get_variation_tag_of_index(
                self.score.tag_ranges(self.current)[0]
            )
            try:
                self.previousmovetags[positiontag] = (
                    self.previousmovetags[self.current][0],
                    variation,
                    variation,
                )
            except KeyError:
                self.previousmovetags[positiontag] = (None, None, None)
        else:
            self.previousmovetags[positiontag] = (None, None, None)

    def add_start_comment(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self.tokens_exist_between_movetext_start_and_insert_point()
        after = self.tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_start_comment(token, before)
        if not before and after:
            self.insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self.link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def add_comment_to_eol(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self.tokens_exist_between_movetext_start_and_insert_point()
        after = self.tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_comment_to_eol(token, before)
        if not before and after:
            self.insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self.link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def add_escape_to_eol(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self.tokens_exist_between_movetext_start_and_insert_point()
        after = self.tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_escape_to_eol(token, before)
        if not before and after:
            self.insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self.link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def add_glyph(self, token, position):
        """Tag token for single-step navigation and game editing."""
        # At present NAGs are not put on a line of their own when following
        # a move.  They would be if the NAG translations were shown too.
        # before = self.tokens_exist_between_movetext_start_and_insert_point()
        before = self.score.tag_prevrange(
            NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
        )
        if before:
            before = NAVIGATE_MOVE not in self.score.tag_names(before[0])
        else:
            before = False

        after = self.tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_glyph(token, before)
        if not before and after:
            self.insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self.link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def add_start_reserved(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self.tokens_exist_between_movetext_start_and_insert_point()
        after = self.tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_start_reserved(token, before)
        if not before and after:
            self.insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self.link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def tokens_exist_between_insert_point_and_game_terminator(self):
        """Return True if tokens exist from insert point_to_game_terminator."""
        return bool(self.score.tag_nextrange(NAVIGATE_TOKEN, tkinter.INSERT))

    def select_first_item_in_game(self, item):
        """Return POSITION tag associated with first item in game."""
        widget = self.score
        tr_q = widget.tag_nextrange(item, "1.0")
        if not tr_q:
            return None
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return None

    def select_last_item_in_game(self, item):
        """Return POSITION tag associated with last item in game."""
        widget = self.score
        tr_q = widget.tag_prevrange(item, tkinter.END)
        if not tr_q:
            return None
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return None

    def select_next_item_in_game(self, item):
        """Return POSITION tag associated with item after current in game."""
        widget = self.score
        oldtr = widget.tag_ranges(MOVE_TAG)
        if oldtr:
            tr_q = widget.tag_nextrange(item, oldtr[-1])
        else:
            tr_q = widget.tag_nextrange(item, tkinter.INSERT)
        if not tr_q:
            return self.select_first_item_in_game(item)
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return self.select_first_item_in_game(item)

    def select_prev_item_in_game(self, item):
        """Return POSITION tag associated with item before current in game."""
        widget = self.score
        if self.current:
            oldtr = widget.tag_ranges(self.current)
        else:
            oldtr = widget.tag_ranges(MOVE_TAG)
        if oldtr:
            tr_q = widget.tag_prevrange(item, oldtr[0])
        else:
            tr_q = widget.tag_prevrange(item, tkinter.END)
        if not tr_q:
            return self.select_last_item_in_game(item)
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return self.select_last_item_in_game(item)

    def select_next_token_in_game(self):
        """Return POSITION tag associated with token after current in game."""
        return self.select_next_item_in_game(NAVIGATE_TOKEN)

    def select_prev_token_in_game(self):
        """Return POSITION tag associated with token before current in game."""
        return self.select_prev_item_in_game(NAVIGATE_TOKEN)

    # Adding between_newlines argument seemed a good idea at first, but when
    # the insert_empty_comment() method turned out to need a conditional to
    # set the argument the whole thing began to look far too complicated.
    # See the other insert_empty_*() methods, except moves, too.
    # Solution may involve a new mark with right gravity, END_SCORE_MARK,
    # set at end of line before the Game Termination Marker.  Perhaps the
    # blank line between the PGN Tags and the Game Termination Marker in the
    # new game template should be removed, if this is not forced.
    # The escaped line may continue to be a problem.
    def set_insertion_point_before_next_token(self, between_newlines=True):
        """Set the insert point at start of token after current token.

        INSERT is set before next token and it's move number if any, and
        before it's 'forced newline' too if there is one.  Ensure there is an
        adjacent newline before and after INSERT if between_newlines is true.

        PGN export format will put a newline between a move number indicator
        and a move to keep line length below 80 characters.  The newlines
        inserted in the tkinter.Text widget are always put before the move
        number indicator, never between it and a move.

        Numberic Annotation Glyths are short and between_newlines is False
        for them, although a case can be made for putting these on a line
        by themselves too.

        Any text inserted at INSERT if between_newlines is true will need
        the FORCED_NEWLINE_TAG tag removed (inherited by enclosure).

        """
        widget = self.score
        if self.current is None:
            widget.mark_set(tkinter.INSERT, START_SCORE_MARK)
            return
        trc = widget.tag_ranges(self.current)
        tr_q = widget.tag_nextrange(NAVIGATE_TOKEN, trc[-1])
        if not tr_q:
            tr_q = [
                widget.index(
                    widget.tag_nextrange(EDIT_RESULT, trc[-1])[0]
                    + "-1 lines lineend"
                )
            ]
        trfnl = widget.tag_prevrange(FORCED_NEWLINE_TAG, tr_q[0], trc[-1])
        if trfnl:
            tr_q = trfnl
        else:
            trmm = widget.tag_prevrange(
                MOVETEXT_MOVENUMBER_TAG, tr_q[0], trc[-1]
            )
            if trmm:
                tr_q = trmm
        widget.mark_set(tkinter.INSERT, tr_q[0])
        if between_newlines:
            if not trfnl:
                self.insert_forced_newline_into_text()
                widget.mark_set(tkinter.INSERT, tkinter.INSERT + " -1 char")

    def set_insertion_point_before_next_pgn_tag(self):
        """Set INSERT at point for insertion of empty PGN Tag or Tags.

        Assumed to be called only when inserting a PGN Tag since this item is
        only insert allowed at new INSERT position unless at end of PGN Tags.

        """
        widget = self.score
        if widget.compare(tkinter.INSERT, ">=", START_SCORE_MARK):
            widget.mark_set(tkinter.INSERT, START_SCORE_MARK)
            return
        tr_q = widget.tag_nextrange(PGN_TAG, tkinter.INSERT)
        if tr_q:
            widget.mark_set(tkinter.INSERT, tr_q[0])
        else:
            widget.mark_set(tkinter.INSERT, START_SCORE_MARK)

    def set_token_context(self, tagnames, tagranges, tokenprefix):
        """Set token editing and navigation context for tokenprefix.

        tagnames is passed to get_token_insert to derive the end of token
        mark from TOKEN<suffix> tag for setting Tkinter.INSERT.
        tagranges is used to set the editing bounds while the token is the
        active (current) token.
        tokenprefix is the tag in tagnames also in _edit_tokens.  It is used
        to set the keyboard event bindings and the characters allowed as the
        token data.

        """
        if self._most_recent_bindings != tokenprefix:
            self.token_bind_method[tokenprefix](self)
        self._allowed_chars_in_token = _CHARACTERS_ALLOWED_IN_TOKEN[
            tokenprefix
        ]
        start, end = tagranges
        insert = self.get_token_insert(tagnames)
        self._lead_trail = _LeadTrail(*_TOKEN_LEAD_TRAIL[tokenprefix])
        lead_trail = self._lead_trail
        if lead_trail.lead:
            sem = self.score.index(
                "".join((str(start), " +", str(lead_trail.lead), " chars"))
            )
        else:
            sem = start
        if lead_trail.trail:
            eem = self.score.index(
                "".join((str(end), " -", str(lead_trail.trail), " chars"))
            )
        else:
            eem = end
        offset = (
            self.get_token_text_length(start, end) - lead_trail.header_length
        )
        if offset:
            if lead_trail.lead:
                start = sem
            if lead_trail.trail:
                end = eem
        else:
            if lead_trail.lead:
                start = self.score.index("".join((str(sem), " -1 chars")))
            end = sem
        if not insert:
            insert = eem
        elif self.score.compare(insert, ">", eem):
            insert = eem
        elif self.score.compare(insert, "<", sem):
            insert = sem
        self.score.mark_set(START_EDIT_MARK, sem)
        self.score.mark_gravity(START_EDIT_MARK, "left")
        self.score.mark_set(END_EDIT_MARK, eem)
        self.score.mark_set(tkinter.INSERT, insert)
        self.set_move_tag(start, end)

    @staticmethod
    def get_token_insert(tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames."""
        for tn_q in tagnames:
            if tn_q.startswith(TOKEN):
                return "".join((TOKEN_MARK, tn_q[len(TOKEN) :]))
        return None

    def get_token_text_length(self, start, end):
        """Set token editing bound marks from TOKEN<suffix> in tagnames."""
        return self.score.count(start, end)[0]

    def set_start_score_mark_before_positiontag(self):
        """Set start score mark at start self.position_number position tag."""
        self.score.mark_set(
            START_SCORE_MARK,
            self.score.tag_ranges(
                "".join((POSITION, str(self.position_number)))
            )[0],
        )

    def step_one_variation_select(self, move):
        """Select next variation in choices at current position."""
        # Hack of step_one_variation with setting code removed
        if move is None:
            # No prior to variation tag exists: no move to attach it to.
            pt_q = None
            ct_q = self.get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            st_q = self.get_selection_tag_for_choice(ct_q)
        else:
            pt_q = self.get_prior_to_variation_tag_of_move(move)
            ct_q = self.get_choice_tag_for_prior(pt_q)
            st_q = self.get_selection_tag_for_prior(pt_q)
        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self.cycle_selection_tag(ct_q, st_q)
        vt_q = self.get_colouring_variation_tag_for_selection(st_q)
        self.set_variation_selection_tags(pt_q, ct_q, st_q, vt_q)
        return vt_q

    def create_edit_move_context(self, tag):
        """Return tuple of FEN (position) and * (unknown result) for tag."""
        return (
            self.generate_fen_for_position(*self.tagpositionmap[tag]).join(
                _EDIT_MOVE_CONTEXT
            ),
            UNKNOWN_RESULT,
        )
