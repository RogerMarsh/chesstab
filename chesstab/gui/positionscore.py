# positionscore.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""A chess game score display class highlighting moves for a position.

List of classes

PositionScore

"""

import tkinter
import ast

from solentware_bind.gui.bindings import Bindings

from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
    FEN_WHITE_ACTIVE,
    DEFAULT_TAG_RESULT_VALUE,
    DEFAULT_TAG_VALUE,
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
)
from pgn_read.core.parser import PGN

from ..core.pgn import GameDisplayMoves
from .constants import (
    MOVE_COLOR,
    ALTERNATIVE_MOVE_COLOR,
    VARIATION_COLOR,
    MOVES_PLAYED_IN_GAME_FONT,
    TAGS_VARIATIONS_COMMENTS_FONT,
    NAVIGATE_MOVE,
    TOKEN,
    RAV_MOVES,
    RAV_SEP,
    POSITION,
    MOVE_TAG,
    ALTERNATIVE_MOVE_TAG,
    VARIATION_TAG,
    START_SCORE_MARK,
    TOKEN_MARK,
    SPACE_SEP,
    MOVETEXT_MOVENUMBER_TAG,
)
from ._score_scaffold import _ScoreScaffold


# May need to make this a superclass of Tkinter.Text because DataRow method
# make_row_widgets expects to be able to call Tkinter widget methods.
class PositionScore(Bindings):
    """Chess game score widget composed from a Text widget."""

    m_color = MOVE_COLOR
    am_color = ALTERNATIVE_MOVE_COLOR
    v_color = VARIATION_COLOR
    tags_variations_comments_font = TAGS_VARIATIONS_COMMENTS_FONT
    moves_played_in_game_font = MOVES_PLAYED_IN_GAME_FONT

    tags_displayed_last = SEVEN_TAG_ROSTER
    _context = None

    def __init__(
        self,
        widget,
        tags_variations_comments_font=None,
        moves_played_in_game_font=None,
        ui=None,
        **ka
    ):
        """Extend with widgets to display game.

        widget - Tkinter.Text instance to contain game score
        tags_variations_comments_font - font for tags variations and comments
        moves_played_in_game_font - font for move played in game
        ui - the ChessUI instance

        Create Frame in toplevel and add Canvas and Text.
        Text width and height set to zero so widget fit itself into whatever
        space Frame has available.
        Canvas must be square leaving Text at least half the Frame.

        """
        del ka
        super().__init__()
        self.ui = ui
        if tags_variations_comments_font:
            self.tags_variations_comments_font = tags_variations_comments_font
        if moves_played_in_game_font:
            self.moves_played_in_game_font = moves_played_in_game_font
        # Use widget argument rather than create one here like similar classes.
        self.score = widget
        widget.tag_configure(MOVETEXT_MOVENUMBER_TAG, elide=tkinter.FALSE)
        widget.tag_configure(
            MOVES_PLAYED_IN_GAME_FONT, font=self.moves_played_in_game_font
        )
        # Order is MOVE_TAG ALTERNATIVE_MOVE_TAG VARIATION_TAG so that correct
        # colour has highest priority as moves are added to and removed from
        # tags.
        widget.tag_configure(MOVE_TAG, background=self.m_color)
        widget.tag_configure(ALTERNATIVE_MOVE_TAG, background=self.am_color)
        widget.tag_configure(VARIATION_TAG, background=self.v_color)
        self.bind(widget, "<Map>", function=self.try_event(self._on_map))
        # None implies initial position and is deliberately not a valid Tk tag.
        self.current = None  # Tk tag of current move
        self._clear_tag_maps()
        self.collected_game = None

        self.gamevartag = None
        self._game_scaffold = None

    # Nothing needed on <Unmap> event at present
    def _on_map(self, event):
        """Scroll text of move into current position to left edge of widget.

        This is done correctly only if the widget is mapped.  So do it when
        a Map event occurs.

        """

    def _clear_tag_maps(self):
        """Clear mappings of tags and positions.

        Instances of PositionScore are reused as games are navigated and not
        necessarely for the game already in the instance.

        """
        # Mappings tagpositionmap, fullpositions, positiontags, and recently
        # added varmovetags, are removed because the compare_two_positions()
        # method and _context attributes seems to be able to do the job.
        # Probably including taking account of castling and en-passant options
        # if required.
        self.variation_number = 0
        self.varstack = []
        self.position_number = 0

    def process_score(self, text=None, context=None):
        """Populate collected_game with PGN score derived from text."""
        if text:
            self._clear_tag_maps()
            self.collected_game = next(
                PGN(game_class=GameDisplayMoves).read_games(
                    ast.literal_eval(text[0])
                )
            )
            self._context = context
            try:
                self.set_and_tag_item_text()
            finally:
                del self._context

    def get_top_widget(self):
        """Return topmost widget for game display.

        The topmost widget is put in a container widget in some way
        """
        return self.score

    def destroy_widget(self):
        """Destroy the widget displaying game."""
        self.score.destroy()

    def set_and_tag_item_text(self, reset_undo=False):
        """Display the game as board and moves.

        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a game for editing so that repeated Ctrl-Z in text
        editing mode recovers the original score.

        """
        del reset_undo
        self.score.configure(state=tkinter.NORMAL)
        self.score.delete("1.0", tkinter.END)
        self.map_game()
        self.score.configure(state=tkinter.DISABLED)

    def clear_current_range(self):
        """Remove existing MOVE_TAG ranges."""
        tagrange = self.score.tag_ranges(MOVE_TAG)
        if tagrange:
            self.score.tag_remove(MOVE_TAG, tagrange[0], tagrange[1])

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
        for value in sorted(tags.items()):
            if value[0] not in last:
                tag_values.append(value)
        for tag in last:
            if tag in tags:
                tag_values.append((tag, tags[tag]))
        return tag_values

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

    def _get_position_tag_of_index(self, index):
        """Return Tk tag name if index is in a position tag."""
        for tagname in self.score.tag_names(index):
            if tagname.startswith(POSITION):
                return tagname
        return None

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

    def _is_currentmove_in_main_line(self):
        """Return True if currentmove is in the main line tag."""
        return self._is_index_in_main_line(
            self.score.tag_ranges(self.current)[0]
        )

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

    # At present both POSITION<suffix> and TOKEN<suffix> tags exist.
    # Now that setting MOVE_TAG has been moved to token-type specific code
    # there is probably no need for both.  TOKEN marks the active text of a
    # POSITION, for example {<active text>} where POSITION includes the
    # surrounding braces, but as active text can vary and when null
    # POSITION is used to set MOVE_TAG might as well refer to POSITION
    # directly.

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

    # Attempt to re-design map_game method to fit new pgn_read package.
    def map_game(self):
        """Tag and mark the displayed text of game score.

        The tags and marks are used for colouring and navigating the score.

        """
        self._game_scaffold = _ScoreScaffold(
            self.get_variation_tag_name(), None
        )
        self.gamevartag = self._game_scaffold.vartag

        game = self.collected_game
        spm = self._game_scaffold.square_piece_map
        for piece, square in game.initial_position[0]:
            spm[square] = piece
        assert len(game.pgn_text) == len(game.position_deltas)
        for text, delta in zip(game.pgn_text, game.position_deltas):
            text0 = text[0]
            if text0 in "abcdefghKQRBNkqrnO":
                self._map_move_text(text, delta)
            elif text0 == "(":
                self.map_start_rav(text, delta)
            elif text0 == ")":
                self.map_end_rav(text, delta)
            elif text0 in "10*":
                self.map_termination(text)
            else:
                self.map_non_move(text)
        self._insert_token_into_text(
            game.pgn_tags.get(TAG_WHITE, DEFAULT_TAG_VALUE), SPACE_SEP
        )
        self._insert_token_into_text(
            game.pgn_tags.get(TAG_RESULT, DEFAULT_TAG_RESULT_VALUE), SPACE_SEP
        )
        self._insert_token_into_text(
            game.pgn_tags.get(TAG_BLACK, DEFAULT_TAG_VALUE), SPACE_SEP
        )

        tagrange = self.score.tag_nextrange(NAVIGATE_MOVE, "1.0")
        if tagrange:
            self.score.mark_set(START_SCORE_MARK, str(tagrange[0]))
        else:
            self.score.mark_set(START_SCORE_MARK, "1.0")

        self._game_scaffold = None

    @staticmethod
    def compare_two_positions(one, two):
        """Return True if positions one and two are same, otherwise False.

        Ignore castling and en passant options when comparing positions.

        The move on which the positions occur is not relevant so full move
        number and half move clock are ignored.

        """
        # At end of game or variation either one or two will be None, depending
        # on argument order.
        # Exception return must be False because True causes too much display.
        try:
            if one[1] != two[1]:
                return False
        except TypeError:
            if one is None or two is None:
                return False
            raise
        if set(one[0]) != set(two[0]):
            return False
        two0 = two[0]
        for square, piece in one[0].items():
            if piece.name != two0[square].name:
                return False
        return True

    def _map_move_text(self, token, delta):
        """Add token to game text and modify game position by delta."""
        prevcontext, currcontext, nextcontext = self._context
        scaffold = self._game_scaffold

        # Does position in which move is played match the previous or current
        # position in self._context?
        prev_position = (scaffold.square_piece_map.copy(),) + delta[0][1:]
        prev_match_prevcontext = self.compare_two_positions(
            prev_position, prevcontext
        )
        prev_match_currcontext = self.compare_two_positions(
            prev_position, currcontext
        )

        self._modify_square_piece_map(delta)

        # Does position after move is played match the current or next
        # position in self._context?
        curr_position = (scaffold.square_piece_map.copy(),) + delta[1][1:]
        curr_match_currcontext = self.compare_two_positions(
            curr_position, currcontext
        )
        next_match_nextcontext = self.compare_two_positions(
            curr_position, nextcontext
        )

        if not (
            prev_match_prevcontext
            or prev_match_currcontext
            or curr_match_currcontext
            or next_match_nextcontext
        ):
            return
        widget = self.score
        if delta[1][1] != FEN_WHITE_ACTIVE:
            start, end, sepend = self._insert_token_into_text(
                str(delta[1][5]) + ".", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        elif scaffold.force_movenumber:
            start, end, sepend = self._insert_token_into_text(
                str(delta[0][5]) + "...", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        scaffold.force_movenumber = False
        positiontag = self._get_next_positiontag_name()
        start, end, sepend = self._insert_token_into_text(token, SPACE_SEP)
        for tag in positiontag, scaffold.vartag, NAVIGATE_MOVE:
            widget.tag_add(tag, start, end)
        if scaffold.vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        widget.tag_add("".join((RAV_SEP, scaffold.vartag)), start, sepend)
        if not (prev_match_prevcontext or prev_match_currcontext):
            # token is move to reach position and different from context
            widget.tag_add(VARIATION_TAG, start, end)
        if not (curr_match_currcontext or next_match_nextcontext):
            # token is move out of position and  different from context
            widget.tag_add(ALTERNATIVE_MOVE_TAG, start, end)
        tagrange = widget.tag_prevrange(scaffold.vartag, start)
        if not tagrange:
            varstack = list(self.varstack)
            while varstack:
                var = varstack.pop()
                tpr = widget.tag_prevrange(var, start)
                if not tpr:
                    break
                tagrange = widget.tag_prevrange(var, tpr[0])
                if tagrange:
                    break

    def map_start_rav(self, token, position):
        """Add token to game text. position is ignored. Return range and prior.

        Variation tags are set for guiding move navigation.  vartag
        is placed on a stack for restoration at the end of the variation.

        """
        scaffold = self._game_scaffold
        self._set_square_piece_map(position)
        self.varstack.append(scaffold.vartag)
        scaffold.vartag = self.get_variation_tag_name()
        self._insert_token_into_text(token, SPACE_SEP)
        scaffold.force_movenumber = True

    def map_end_rav(self, token, position):
        """Add token to game text. position is ignored. Return token range.

        Variation tags are set for guiding move navigation.  vartag
        is restored from the stack for restoration at the end of the
        variation.

        """
        scaffold = self._game_scaffold
        self._set_square_piece_map(position)
        self._insert_token_into_text(token, SPACE_SEP)
        scaffold.vartag = self.varstack.pop()
        scaffold.force_movenumber = True

    def map_termination(self, token):
        """Add token to game text. position is ignored. Return token range."""
        if self.collected_game.pgn_tags.get(TAG_RESULT) != token:
            self._insert_token_into_text(token, SPACE_SEP)

    def map_non_move(self, token):
        """Add token to game text. position is ignored. Return token range."""
        # self._insert_token_into_text(token, SPACE_SEP)

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
        tagrange = self._set_current_range()
        if tagrange:
            self._set_move_tag(tagrange[0], tagrange[1])
            return tagrange
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
        tagrange = self.score.tag_ranges(self.current)
        if not tagrange:
            return None
        return tagrange

    def _set_move_tag(self, start, end):
        """Add range start to end to MOVE_TAG (which is expected to be empty).

        Assumption is that _set_current_range has been called and MOVE_TAG is
        still empty following that call.

        """
        self.score.tag_add(MOVE_TAG, start, end)
