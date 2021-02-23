# positionscore.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""A chess game score display class highlighting moves for a position.

List of classes

PositionScore

"""

import tkinter

from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
    IFG_TAG_SYMBOL,
    IFG_TAG_STRING_VALUE,
    IFG_PIECE_SQUARE,
    IFG_PAWN_SQUARE,
    IFG_PIECE_CAPTURE_SQUARE,
    IFG_PAWN_CAPTURE_SQUARE,
    IFG_PIECE_CHOICE_SQUARE,
    IFG_PAWN_PROMOTE_SQUARE,
    IFG_CASTLES,
    IFG_START_RAV,
    IFG_END_RAV,
    IFG_TERMINATION,
    IFG_ANYTHING_ELSE,
    IFG_CHECK,
    IFG_ANNOTATION,
    FULLSTOP,
)
from pgn_read.core.parser import (
    PGNDisplayMoves,
    )

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
    ALTERNATIVE_MOVE_COLOR,
    VARIATION_COLOR,
    SPACE_SEP,
    NEWLINE_SEP,
    NULL_SEP,
    FORCE_FULLMOVE_PER_LINE,
    )


# May need to make this a superclass of Tkinter.Text because DataRow method
# make_row_widgets expects to be able to call Tkinter widget methods.
class PositionScore(ChessException):

    """Chess game score widget composed from a Text widget.    
    """

    m_color = MOVE_COLOR
    am_color = ALTERNATIVE_MOVE_COLOR
    v_color = VARIATION_COLOR
    tags_variations_comments_font = TAGS_VARIATIONS_COMMENTS_FONT
    moves_played_in_game_font = MOVES_PLAYED_IN_GAME_FONT

    def __init__(
        self,
        widget,
        tags_variations_comments_font=None,
        moves_played_in_game_font=None,
        ui=None,
        **ka):
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
        super(PositionScore, self).__init__()
        self.ui = ui
        if tags_variations_comments_font:
            self.tags_variations_comments_font = tags_variations_comments_font
        if moves_played_in_game_font:
            self.moves_played_in_game_font = moves_played_in_game_font
        # Use widget argument rather than create one here like similar classes.
        self.score = widget
        widget.tag_configure(
            MOVES_PLAYED_IN_GAME_FONT, font=self.moves_played_in_game_font)
        # Order is MOVE_TAG ALTERNATIVE_MOVE_TAG VARIATION_TAG so that correct
        # colour has highest priority as moves are added to and removed from
        # tags.
        widget.tag_configure(MOVE_TAG, background=self.m_color)
        widget.tag_configure(ALTERNATIVE_MOVE_TAG, background=self.am_color)
        widget.tag_configure(VARIATION_TAG, background=self.v_color)
        widget.bind('<Map>', self.try_event(self.on_map))
        # None implies initial position and is deliberately not a valid Tk tag.
        self.current = None # Tk tag of current move
        self._clear_tag_maps()
        self.pgn = PGNDisplayMoves()
        
    def bind_for_viewmode(self):
        """Set keyboard bindings for traversing moves."""
        # Appropriate bindings still to be decided
        #self.score.bind('<KeyPress>', lambda e: 'break')

    # Nothing needed on <Unmap> event at present
    def on_map(self, event):
        """Scroll text of move into current position to left edge of widget.

        This is done correctly only if the widget is mapped.  So do it when
        a Map event occurs.

        """
        self.set_game_board()

    def _clear_tag_maps(self):
        """Clear mappings of tags and positions.

        Instances of PositionScore are reused as games are navigated and not
        necessarely for the game already in the instance.
        
        Tags are cross-referenced using the position of the pieces and side to
        move to pick which moves to colour but the en passant and castling
        flags may be used to pick the colours used.  Hence the positions and
        fullpositions attributes.

        """
        self.rav_number = 0
        self.varstack = []
        self.position_number = 0
        self.positions = dict()
        self.fullpositions = dict()
        self.positiontags = dict()
        self.nextmovetags = dict()
        self.previousmovetags = dict()

    def colour_score(self, context=None):
        """Set tags on the displayedmovetext.
        """
        widget = self.score
        for t in ALTERNATIVE_MOVE_TAG, MOVE_TAG, VARIATION_TAG, LINE_TAG:
            widget.tag_remove(t, '1.0', tkinter.END)
        prevposition, currposition, nextposition = self._context
        if currposition:
            current = self.positiontags.get(currposition[:2], ())
            for tn in current:
                widget.tag_add(
                    LINE_TAG,
                    *widget.tag_ranges(tn))
                prevtag = self.previousmovetags[tn]
                if prevtag is not None:
                    try:
                        # prevposition may be None if errors in imported games
                        if self.positions[prevtag] != prevposition[:2]:
                            widget.tag_add(
                                VARIATION_TAG,
                                *widget.tag_ranges(tn))
                    except TypeError:
                        pass
                if nextposition:
                    nexttag = self.nextmovetags.get(tn)
                    if nexttag is not None:
                        for nt in nexttag:
                            if self.positions[nt] != nextposition[:2]:
                                widget.tag_add(
                                    ALTERNATIVE_MOVE_TAG,
                                    *widget.tag_ranges(nt))
            if len(current):
                self.current = current[0]
            else:
                self.current = None
        else:
            self.current = None
        #self.set_game_board()
        
    def process_score(self, text=None, context=None):
        """Wrapper for Tkinter.Text configure method for score attribute"""
        if text:
            self._clear_tag_maps()
            self.pgn.get_first_game(text)
            self._context = context
            self._inhibit_force_newline_count = 0
            try:
                self.set_game()
                self.colour_score()
            finally:
                del self._context
                del self._inhibit_force_newline_count
        
    def get_top_widget(self):
        """Return topmost widget for game display.

        The topmost widget is put in a container widget in some way
        """
        return self.score

    def destroy_widget(self):
        """Destroy the widget displaying game."""
        self.score.destroy()

    def see_first_move(self):
        """Make first move visible on navigation to initial position.

        Current move is always made visible but no current move defined
        for initial position.
        """
        self.score.see(START_SCORE_MARK)
        
    def set_game_board(self):
        """Set board to show position after highlighted move."""
        # Use see or see_first_move to get the current move visible and then
        # adjust it's position to left edge of widget by xview_scroll taking
        # borders into account
        if self.current is None:
            self.see_first_move()
            return
        index = self.score.tag_ranges(self.current)[0]
        self.score.see(index)
        bbox = self.score.bbox(index)
        if not bbox:
            return
        self.score.xview_scroll(bbox[0] - 3, 'pixels')
        # 15 is a hack assuming a font and size.  It is the bbox[-1] value for
        # text which looks correct from a print(bbox) statement.
        if bbox[-1] != 15:
            self.score.yview_scroll(15 - bbox[-1], 'pixels')
        bbox = self.score.bbox(index)
        if not bbox:
            return
        if bbox[0] != 3:
            index = self.score.index(str(index) + '-1c')
            # Adjust colouring or font or style of leading text to indicate
            # that scrolling was not possible (because there is not enough
            # text to right to be scrolled into widget).
            # May need to do similar when existing display is resized.
            # Perhaps simplest is pad to right with spaces.
        
    def set_game(self, starttoken=None, reset_undo=False):
        """Display the game as board and moves.

        starttoken is the move played to reach the position displayed and this
        move becomes the current move.
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a game for editing so that repeated Ctrl-Z in text
        editing mode recovers the original score.
        
        """
        self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_game()
        self.score.configure(state=tkinter.DISABLED)
        
    def clear_current_range(self):
        """Remove existing MOVE_TAG ranges."""
        tr = self.score.tag_ranges(MOVE_TAG)
        if tr:
            self.score.tag_remove(MOVE_TAG, tr[0], tr[1])

    def get_tags_display_order(self):
        """Return text of PGN Tags in defined display order."""
        str_tags = []
        other_tags = []
        for t in self.pgn.collected_game[0]:
            tn = t.group(IFG_TAG_SYMBOL)
            if tn not in SEVEN_TAG_ROSTER:
                other_tags.append((tn, t.group(IFG_TAG_STRING_VALUE)))
            else:
                str_tags.append((tn, t.group(IFG_TAG_STRING_VALUE)))
        return other_tags + str_tags
    
    def get_rav_tag_names(self):
        """Return suffixed RAV_MOVES and RAV_TAG tag names.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.rav_number += 1
        suffix = str(self.rav_number)
        return ''.join((RAV_MOVES, suffix))

    def get_next_positiontag_name(self):
        """Return suffixed POSITION tag name."""
        self.position_number += 1
        return ''.join((POSITION, str(self.position_number)))

    def get_position_tag_of_index(self, index):
        """Return Tk tag name if index is in a position tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(POSITION):
                return tn
        return None

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
    def map_game(self):
        """Tag and mark the displayed text of game score.

        The tags and marks are used for colouring and navigating the score.

        """
        dispatch_table = {
            IFG_PIECE_SQUARE: self.map_move_text,
            IFG_PAWN_SQUARE: self.map_move_text,
            IFG_PIECE_CAPTURE_SQUARE: self.map_move_text,
            IFG_PAWN_CAPTURE_SQUARE: self.map_move_text,
            IFG_PIECE_CHOICE_SQUARE: self.map_move_text,
            IFG_PAWN_PROMOTE_SQUARE: self.map_move_text,
            IFG_CASTLES: self.map_move_text,
            IFG_START_RAV: self.map_start_rav,
            IFG_END_RAV: self.map_end_rav,
            IFG_TERMINATION: self.map_termination,
            IFG_ANYTHING_ELSE: self.map_non_move,
            IFG_CHECK: self.map_non_move,
            IFG_ANNOTATION: self.map_non_move,
            }

        # With get_current_...() methods as well do not need self._vartag
        # state attributes.
        self._vartag = self.get_rav_tag_names()
        self._gamevartag = self._vartag
        
        for token, position in self.pgn.moves:
            for group in (IFG_PIECE_SQUARE,
                          IFG_PAWN_SQUARE,
                          IFG_PIECE_CAPTURE_SQUARE,
                          IFG_PAWN_CAPTURE_SQUARE,
                          IFG_PIECE_CHOICE_SQUARE,
                          IFG_PAWN_PROMOTE_SQUARE,
                          IFG_CASTLES,
                          IFG_START_RAV,
                          IFG_END_RAV,
                          IFG_TERMINATION,
                          ):
                try:
                    if token.group(group):
                        dispatch_table[group](token.group(), position)
                        break
                except AttributeError:
                    group = None
                    break
                except KeyError:
                    break

                # If group == IFG_PIECE_SQUARE and len(token.group()) == 5 or
                # group == IFG_PIECE_CAPTURE_SQUARE and len(token.group()) == 6
                # assume movetext such as 'Qb2c3' meaning there are more than
                # two queens able to move to 'c3' and the one om 'b2' does so.
                # The PGN parser treats 'Qb2c3' as a special case after seeing
                # 'Qb2' cannot be a move.
                except IndexError:
                    if ((len(token.group()) == 5 and
                         group == IFG_PIECE_SQUARE) or
                        (len(token.group()) == 6 and
                         group == IFG_PIECE_CAPTURE_SQUARE)):
                        dispatch_table[group](token.group(), position)
                        break
                    raise

        for k, v in self.previousmovetags.items():
            self.nextmovetags.setdefault(v, []).append(k)

        tr = self.score.tag_nextrange(NAVIGATE_MOVE, '1.0')
        if tr:
            self.score.mark_set(START_SCORE_MARK, str(tr[0]))
        else:
            self.score.mark_set(START_SCORE_MARK, '1.0')

    def map_move_text(self, token, position):
        """Add token to game text. Set navigation tags. Return token range.

        Ignore castling and en passant options when comparing positions.

        """
        widget = self.score
        positiontag = self.get_next_positiontag_name()
        self.positiontags.setdefault(position[:2], []).append(positiontag)
        self.positions[positiontag] = position[:2]
        self.fullpositions[positiontag] = position
        if len(self.pgn.moves) > FORCE_FULLMOVE_PER_LINE:
            if self._inhibit_force_newline_count:
                self._inhibit_force_newline_count -= 1
            elif position[:2] == self._context[2][:2]:
                # An arbitrary number of half-moves to fill the widget.
                self._inhibit_force_newline_count = 25
            elif position[1]:
                widget.insert(tkinter.INSERT, NEWLINE_SEP)
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        for tag in positiontag, self._vartag, NAVIGATE_MOVE:
            widget.tag_add(tag, start, end)
        if self._vartag is self._gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        widget.tag_add(''.join((RAV_SEP, self._vartag)), start, sepend)
        tr = widget.tag_prevrange(self._vartag, start)
        if not tr:
            varstack = list(self.varstack)
            while varstack:
                var = varstack.pop()
                tr = widget.tag_prevrange(
                    var, widget.tag_prevrange(var, start)[0])
                if tr:
                    break
        if tr:
            self.previousmovetags[positiontag] = self.get_position_tag_of_index(
                tr[0])
        else:
            self.previousmovetags[positiontag] = None

    def map_start_rav(self, token, position):
        """Add token to game text. position is ignored. Return range and prior.

        Variation tags are set for guiding move navigation. self._vartag
        is placed on
        a stack for restoration at the end of the variation.

        """
        widget = self.score
        self.varstack.append(self._vartag)
        self._vartag = self.get_rav_tag_names()
        self.insert_token_into_text(token, SPACE_SEP)

    def map_end_rav(self, token, position):
        """Add token to game text. position is ignored. Return token range.

        Variation tags are set for guiding move navigation. self._vartag
        is restored
        from the stack for restoration at the end of the variation.

        """
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        self._vartag = self.varstack.pop()

    def map_termination(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_token_into_text(token, SPACE_SEP)

    def map_move_error(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_token_into_text(token, SPACE_SEP)

    def map_move_after_error(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_token_into_text(token, SPACE_SEP)

    def map_non_move(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_token_into_text(token, SPACE_SEP)

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

    def set_move_tag(self, start, end):
        """Add range start to end to MOVE_TAG (which is expected to be empty).

        Assumption is that set_current_range has been called and MOVE_TAG is
        still empty following that call.

        """
        self.score.tag_add(MOVE_TAG, start, end)

    def down_one_transposition(self):
        """Cycle forward one tranposition to position in selected game."""
        tr = self.score.tag_nextrange(
            LINE_TAG, self.score.tag_ranges(self.current)[-1])
        if not tr:
            tr = self.score.tag_nextrange(LINE_TAG, '1.0')
        if tr:
            self.current = self.get_position_tag_of_index(tr[0])
        else:
            self.current = None
        if self.score.winfo_ismapped():
            self.set_game_board()
        
    def up_one_transposition(self):
        """Cycle backward one tranposition to position in selected game."""
        tr = self.score.tag_prevrange(
            LINE_TAG, self.score.tag_ranges(self.current)[0])
        if not tr:
            tr = self.score.tag_prevrange(LINE_TAG, tkinter.END)
        if tr:
            self.current = self.get_position_tag_of_index(tr[0])
        else:
            self.current = None
        if self.score.winfo_ismapped():
            self.set_game_board()
