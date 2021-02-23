# gameedit.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a chess game score and put current position on a board.

The GameEdit class displays a game of chess and allows editing.

The RepertoireEdit class displays PGN text representing an opening repertoire
and allows editing.

These classes have the game.Game class as a superclass.

These classes do not allow deletion of games from a database.

These classes differ in the requirements placed on the pgn package to import,
store, and export, PGN text.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

import tkinter
import re

from solentware_misc.workarounds.workarounds import text_count
from solentware_misc.workarounds import dialogues

from pgn_read.core.constants import (
    TAG_RESULT,
    SEVEN_TAG_ROSTER,
    TAG_FEN,
    TAG_SETUP,
    SETUP_VALUE_FEN_PRESENT,
    FEN_BLACK_BISHOP,
    PGN_BISHOP,
    PGN_CAPTURE_MOVE,
    )
from pgn_read.core.parser import PGN
from pgn_read.core.game import GameStrictPGN

from ..core.constants import (
    WHITE_WIN,
    BLACK_WIN,
    DRAW,
    UNKNOWN_RESULT,
    REPERTOIRE_TAG_ORDER,
    START_RAV,
    END_RAV,
    START_COMMENT,
    ERROR_START_COMMENT,
    ESCAPE_END_COMMENT,
    END_COMMENT,
    END_TAG,
    START_TAG,
    )
from ..core.pgn import GameDisplayMoves
from .game import Game
from .eventspec import EventSpec
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
    NAVIGATE_MOVE, # absence matters if no EDIT_... exists
    NAVIGATE_TOKEN,
    TOKEN,
    RAV_MOVES,
    CHOICE,
    PRIOR_MOVE,
    RAV_SEP,
    RAV_TAG,
    ALL_CHOICES,
    POSITION,
    MOVE_TAG,
    ALTERNATIVE_MOVE_TAG,
    LINE_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    NAVIGATE_COMMENT,
    TOKEN_MARK,
    INSERT_TOKEN_MARK,
    START_EDIT_MARK,
    END_EDIT_MARK,
    PGN_TAG,
    MOVES_PLAYED_IN_GAME_FONT,
    VARIATION_TAG,
    RAV_END_TAG,
    TERMINATION_TAG,
    SPACE_SEP,
    )
from ..core import exporters

# Each editable PGN item is tagged with one tag from this set.
# Except that PGN Tag Values get tagged with EDIT_PGN_TAG_NAME as well as the
# intended EDIT_PGN_TAG_VALUE.  Corrected by hack.
_EDIT_TAGS = frozenset(
    (EDIT_GLYPH,
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
     ))

# Leading and trailing character counts around PGN item payload characters
_TOKEN_LEAD_TRAIL = {
    EDIT_GLYPH: (1, 0),
    EDIT_RESULT: (0, 0),
    EDIT_PGN_TAG_NAME: (1, 0),
    EDIT_PGN_TAG_VALUE: (1, 0),
    EDIT_COMMENT: (1, 1),
    EDIT_RESERVED: (1, 1),
    EDIT_COMMENT_EOL: (1, 0),
    EDIT_ESCAPE_EOL: (2, 0),
    EDIT_MOVE_ERROR: (0, 0),
    EDIT_MOVE: (0, 0),
    INSERT_RAV: (0, 0),
    MOVE_EDITED: (0, 0),
    }

# Tk keysym map to PGN termination sequences:
_TERMINATION_MAP = {
    'plus': WHITE_WIN,
    'equal': DRAW,
    'minus': BLACK_WIN,
    'asterisk': UNKNOWN_RESULT,
    }

# The characters used in moves. Upper and lower case L are included as synonyms
# for B to allow shiftless typing of moves such as Bb5.
_MOVECHARS = 'abcdefghklnoqrABCDEFGHKLNOQR12345678xX-='
_FORCECASE = bytes.maketrans(b'ACDEFGHLXklnoqr', b'acdefghBxKBNOQR')
# The use of return 'break' throughout this module means that \r to \n does
# not get done by Text widget.  The two places where typing \r is allowed are
# dealt with using _NEWLINE.
_NEWLINE = bytes.maketrans(b'\r', b'\n')
# These may be moved to pgn.constants.py as the values are derived from the
# PGN specification (but their use is here only).
# allowed in comment to eol and escape to eol
_ALL_PRINTABLE = ''.join(
    (''.join([chr(i) for i in range(ord(' '), 127)]), # symbols and string data
     ''.join([chr(i) for i in range(160, 192)]), # string data but discouraged
     ''.join([chr(i) for i in range(192, 256)]), # string data
     ))
# allowed in {comments}
_ALL_PRINTABLE_AND_NEWLINE_WITHOUT_BRACERIGHT = ''.join(
    ('\n', _ALL_PRINTABLE)).replace('}', '')
# allowed in <reserved>
_ALL_PRINTABLE_AND_NEWLINE_WITHOUT_GREATER = ''.join(
    ('\n', _ALL_PRINTABLE)).replace('>', '')
# allowed in PGN tag names
_PGN_TAG_NAMES = ''.join(
    ('0123456789',
     'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
     '_',
     'abcdefghijklmnopqrstuvwxyz'))
# allowed in PGN tag values (not quite right as \ and " can be escaped by \)
_ALL_PRINTABLE_WITHOUT_QUOTEDBL = _ALL_PRINTABLE.replace('"', '')
# allowed in glyphs
_GLYPHS = '0123456789'
# allowed in game termination and Results PGN tag value
_TERMINATOR = '-/012*'

# lookup dictionary for characters allowed in tokens with given tag
_CHARACTERS_ALLOWED_IN_TOKEN = {
    EDIT_GLYPH: _GLYPHS,
    EDIT_RESULT: _TERMINATOR,
    EDIT_PGN_TAG_NAME: _PGN_TAG_NAMES,
    EDIT_PGN_TAG_VALUE: _ALL_PRINTABLE_WITHOUT_QUOTEDBL,
    EDIT_COMMENT: _ALL_PRINTABLE_AND_NEWLINE_WITHOUT_BRACERIGHT,
    EDIT_RESERVED: _ALL_PRINTABLE_AND_NEWLINE_WITHOUT_GREATER,
    EDIT_COMMENT_EOL: _ALL_PRINTABLE,
    EDIT_ESCAPE_EOL: _ALL_PRINTABLE,
    EDIT_MOVE_ERROR: _MOVECHARS,
    EDIT_MOVE: _MOVECHARS,
    INSERT_RAV: _MOVECHARS,
    MOVE_EDITED: _MOVECHARS,
    }

# PGN validation wrapper for editing moves.
_EDIT_MOVE_CONTEXT = (
    ''.join((START_TAG, TAG_SETUP, '"', SETUP_VALUE_FEN_PRESENT, '"', END_TAG,
             START_TAG, TAG_FEN, '"')),
    ''.join(('"', END_TAG)),
    )

# Error wrapper detector.
_error_wrapper_re = re.compile(
    r''.join(
        (r'(', START_COMMENT, r'\s*', ERROR_START_COMMENT, r'.*?',
         ESCAPE_END_COMMENT, r'\s*', END_COMMENT, r')')),
    flags=re.DOTALL)


class GameEdit(Game):
    
    """Display a game with editing allowed.

    Two PGN objects are available to a GameEdit instance: one provided
    by the creator of the instance used to display the game (from Game
    a base class of DatabaseGameDisplay); the other inherited directly from PGN
    which is used for editing. This class provides methods to handle single
    moves complementing the game facing methods in PGN.
    
    """
    # get_first_game() does not care whether self.score.get() returns
    # string or unicode but self.set_game() does a string.translate() so the
    # get_first_game(x) calls must be get_first_game(x.encode()).
    # ( encode() was introduced for compatibility with Python 2.5 but )
    # ( as this app now uses the hide attribute of paned windows from )
    # ( Tk 8.5 which is not available on Python 2.5 maybe convert to  )
    # ( unicode for Python 3.n compatibility and drop encode().       )

    # True means game score can be edited
    _is_score_editable = True

    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend with bindings to edit game score."""
        super().__init__(gameclass=gameclass, **ka)
        self._allowed_chars_in_token = '' # or an iterable of characters
        self.edit_move_context = dict()
        self.menupopup_movemode_score_navigation = tkinter.Menu(
            master=self.viewmode_popup, tearoff=False)
        self.menupopup_movemode_pgn_insert = tkinter.Menu(
            master=self.viewmode_popup, tearoff=False)
        # selectmode_popup is same as display game version
        # viewmode_popup has pointer actions to add non-move PGN constructs
        # to game. Direct typing is allowed only in error situations.
        # Additional popup menus are defined for non-move PGN contexts.
        self.viewmode_popup.insert_cascade(
            'Database',
            label='Navigate Score',
            menu=self.menupopup_movemode_score_navigation)
        self.viewmode_popup.insert_cascade(
            'Database',
            label='PGN',
            menu=self.menupopup_movemode_pgn_insert)
        for function, accelerator in (
            # Non-move navigation
            (self.show_prev_token,
             EventSpec.gameedit_show_previous_token),
            (self.show_next_token,
             EventSpec.gameedit_show_next_token),
            (self.show_first_token,
             EventSpec.gameedit_show_first_token),
            (self.show_last_token,
             EventSpec.gameedit_show_last_token),
            (self.show_first_comment,
             EventSpec.gameedit_show_first_comment),
            (self.show_last_comment,
             EventSpec.gameedit_show_last_comment),
            (self.show_prev_comment,
             EventSpec.gameedit_show_previous_comment),
            (self.show_next_comment,
             EventSpec.gameedit_show_next_comment),
            (self.to_prev_pgn_tag,
             EventSpec.gameedit_to_previous_pgn_tag),
            (self.to_next_pgn_tag,
             EventSpec.gameedit_to_next_pgn_tag),
            ):
            self.menupopup_movemode_score_navigation.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_movemode_score_navigation),
                accelerator=accelerator[2])
        for function, accelerator in (
            # PGN constructs
            (self.insert_comment,
             EventSpec.gameedit_insert_comment),
            (self.insert_reserved,
             EventSpec.gameedit_insert_reserved),
            (self.insert_comment_to_eol,
             EventSpec.gameedit_insert_comment_to_eol),
            (self.insert_escape_to_eol,
             EventSpec.gameedit_insert_escape_to_eol),
            (self.insert_glyph,
             EventSpec.gameedit_insert_glyph),
            (self.insert_result_win,
             EventSpec.gameedit_insert_white_win),
            (self.insert_result_draw,
             EventSpec.gameedit_insert_draw),
            (self.insert_result_loss,
             EventSpec.gameedit_insert_black_win),
            (self.insert_result_termination,
             EventSpec.gameedit_insert_other_result),
            (self.insert_castle_queenside_command,
             EventSpec.gameedit_insert_castle_queenside),
            ):
            self.menupopup_movemode_pgn_insert.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_movemode_pgn_insert),
                accelerator=accelerator[2])
        # Define popup menu for non-move contexts which are not PGN Tags.
        self.menupopup_nonmove = tkinter.Menu(
            master=self.score, tearoff=False)
        self.menupopup_nonmove_score_navigation = tkinter.Menu(
            master=self.menupopup_nonmove, tearoff=False)
        self.menupopup_nonmove_database = tkinter.Menu(
            master=self.menupopup_nonmove, tearoff=False)
        for function, accelerator in (
            # superclass game navigation
            (self.bind_and_show_next_in_line,
             EventSpec.gameedit_bind_and_show_next_in_line),
            (self.bind_and_show_next_in_var,
             EventSpec.gameedit_bind_and_show_next_in_variation),
            (self.bind_and_show_prev_in_line,
             EventSpec.gameedit_bind_and_show_previous_in_line),
            (self.bind_and_show_prev_in_var,
             EventSpec.gameedit_bind_and_show_previous_in_variation),
            (self.bind_and_show_first_in_game,
             EventSpec.gameedit_bind_and_show_first_in_game),
            (self.bind_and_show_last_in_game,
             EventSpec.gameedit_bind_and_show_last_in_game),
            (self.bind_and_show_first_in_line,
             EventSpec.gameedit_bind_and_show_first_in_line),
            (self.bind_and_show_last_in_line,
             EventSpec.gameedit_bind_and_show_last_in_line),
            ):
            self.menupopup_nonmove.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.menupopup_nonmove),
                accelerator=accelerator[2])
        self.menupopup_nonmove.add_cascade(
            label='Navigate Score',
            menu=self.menupopup_nonmove_score_navigation)
        self.menupopup_nonmove.add_cascade(
            label='Database',
            menu=self.menupopup_nonmove_database)
        for function, accelerator in (
            # PGN tag navigation
            (self.bind_and_to_prev_pgn_tag,
             EventSpec.gameedit_bind_and_to_previous_pgn_tag),
            (self.bind_and_to_next_pgn_tag,
             EventSpec.gameedit_bind_and_to_next_pgn_tag),
            ):
            self.menupopup_nonmove_score_navigation.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_nonmove_score_navigation),
                accelerator=accelerator[2])
        for function, accelerator in (
            # Export options
            (self.export_archive_pgn,
             EventSpec.export_archive_pgn_from_game),
            (self.export_rav_pgn,
             EventSpec.export_rav_pgn_from_game),
            (self.export_pgn,
             EventSpec.export_pgn_from_game),
            ):
            self.menupopup_nonmove_database.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_nonmove_database),
                accelerator=accelerator[2])
        # Define popup menu for PGN Tag context.
        self.menupopup_pgntagmode = tkinter.Menu(
            master=self.score, tearoff=False)
        self.menupopup_pgntag_score_navigation = tkinter.Menu(
            master=self.menupopup_pgntagmode, tearoff=False)
        self.menupopup_pgntag_pgn_insert = tkinter.Menu(
            master=self.menupopup_pgntagmode, tearoff=False)
        self.menupopup_pgntag_database = tkinter.Menu(
            master=self.menupopup_pgntagmode, tearoff=False)
        for function, accelerator in (
            # superclass game navigation
            (self.non_move_show_next_in_line,
             EventSpec.gameedit_non_move_show_next_in_line),
            (self.non_move_show_next_in_variation,
             EventSpec.gameedit_non_move_show_next_in_variation),
            (self.non_move_show_prev_in_line,
             EventSpec.gameedit_non_move_show_previous_in_line),
            (self.non_move_show_prev_in_variation,
             EventSpec.gameedit_non_move_show_previous_in_variation),
            (self.non_move_show_first_in_game,
             EventSpec.gameedit_non_move_show_first_in_game),
            (self.non_move_show_last_in_game,
             EventSpec.gameedit_non_move_show_last_in_game),
            (self.non_move_show_first_in_line,
             EventSpec.gameedit_non_move_show_first_in_line),
            (self.non_move_show_last_in_line,
             EventSpec.gameedit_non_move_show_last_in_line),
            ):
            self.menupopup_pgntagmode.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.menupopup_pgntagmode),
                accelerator=accelerator[2])
        self.menupopup_pgntagmode.add_cascade(
            label='Navigate Score',
            menu=self.menupopup_pgntag_score_navigation)
        self.menupopup_pgntagmode.add_cascade(
            label='PGN',
            menu=self.menupopup_pgntag_pgn_insert)
        self.menupopup_pgntagmode.add_cascade(
            label='Database',
            menu=self.menupopup_pgntag_database)
        for function, accelerator in (
            # Non-move navigation
            (self.show_prev_token,
             EventSpec.gameedit_show_previous_token),
            (self.show_next_token,
             EventSpec.gameedit_show_next_token),
            (self.show_first_token,
             EventSpec.gameedit_show_first_token),
            (self.show_last_token,
             EventSpec.gameedit_show_last_token),
            (self.show_first_comment,
             EventSpec.gameedit_show_first_comment),
            (self.show_last_comment,
             EventSpec.gameedit_show_last_comment),
            (self.show_prev_comment,
             EventSpec.gameedit_show_previous_comment),
            (self.show_next_comment,
             EventSpec.gameedit_show_next_comment),
            (self.to_prev_pgn_tag,
             EventSpec.gameedit_to_previous_pgn_tag),
            (self.to_next_pgn_tag,
             EventSpec.gameedit_to_next_pgn_tag),
            ):
            self.menupopup_pgntag_score_navigation.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_pgntag_score_navigation),
                accelerator=accelerator[2])
        for function, accelerator in (
            # PGN constructs
            (self.insert_pgn_tag,
             EventSpec.gameedit_insert_pgn_tag),
            (self.insert_pgn_seven_tag_roster,
             EventSpec.gameedit_insert_pgn_seven_tag_roster),
            (self.delete_empty_pgn_tag,
             EventSpec.gameedit_delete_empty_pgn_tag),
            ):
            self.menupopup_pgntag_pgn_insert.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_pgntag_pgn_insert),
                accelerator=accelerator[2])
        for function, accelerator in (
            # Export options
            (self.export_archive_pgn,
             EventSpec.export_archive_pgn_from_game),
            (self.export_rav_pgn,
             EventSpec.export_rav_pgn_from_game),
            (self.export_pgn,
             EventSpec.export_pgn_from_game),
            ):
            self.menupopup_pgntag_database.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.menupopup_pgntag_database),
                accelerator=accelerator[2])

    def add_char_to_token(self, event):
        """"""
        self._add_char_to_token(event.char.translate(_NEWLINE))
        return 'break'

    def add_move_char_to_token(self, event):
        """"""
        if self._add_char_to_token(event.char.translate(_FORCECASE)):
            self.process_move()
        return 'break'

    def bind_for_viewmode(self):
        """Set keyboard bindings for traversing moves."""
        super().bind_for_viewmode()
        # PGN move insertion
        if self.score.tag_ranges(EDIT_RESULT):
            self.score.bind(
                EventSpec.gameedit_insert_rav[0],
                self.try_event(self.insert_rav))
            self.score.bind(
                EventSpec.gameedit_insert_rav_castle_queenside[0],
                self.try_event(self.insert_rav_castle_queenside))
        for sequence, function in (
            # PGN non-move symbol insertion
            (EventSpec.gameedit_insert_comment,
             self.insert_comment),
            (EventSpec.gameedit_insert_reserved,
             self.insert_reserved),
            (EventSpec.gameedit_insert_comment_to_eol,
             self.insert_comment_to_eol),
            (EventSpec.gameedit_insert_escape_to_eol,
             self.insert_escape_to_eol),
            (EventSpec.gameedit_insert_glyph,
             self.insert_glyph),
            (EventSpec.gameedit_insert_pgn_tag,
             self.insert_pgn_tag),
            (EventSpec.gameedit_insert_pgn_seven_tag_roster,
             self.insert_pgn_seven_tag_roster),
            (EventSpec.gameedit_insert_white_win,
             self.insert_result_event),
            (EventSpec.gameedit_insert_draw,
             self.insert_result_event),
            (EventSpec.gameedit_insert_black_win,
             self.insert_result_event),
            (EventSpec.gameedit_insert_other_result,
             self.insert_result_event),
            # Token navigation ignoring token purpose (can reach all tokens)
            (EventSpec.gameedit_show_previous_token,
             self.show_prev_token),
            (EventSpec.gameedit_show_next_token,
             self.show_next_token),
            (EventSpec.gameedit_show_first_token,
             self.show_first_token),
            (EventSpec.gameedit_show_last_token,
             self.show_last_token),
            # Comment navigation
            (EventSpec.gameedit_show_first_comment,
             self.show_first_comment),
            (EventSpec.gameedit_show_last_comment,
             self.show_last_comment),
            (EventSpec.gameedit_show_previous_comment,
             self.show_prev_comment),
            (EventSpec.gameedit_show_next_comment,
             self.show_next_comment),
            # PGN tag navigation
            (EventSpec.gameedit_to_previous_pgn_tag,
             self.to_prev_pgn_tag),
            (EventSpec.gameedit_to_next_pgn_tag,
             self.to_next_pgn_tag),
            # PGN tag deletion
            (EventSpec.gameedit_delete_empty_pgn_tag, ''),
            # Character editing
            (EventSpec.gameedit_set_insert_previous_line_in_token, ''),
            (EventSpec.gameedit_set_insert_previous_char_in_token, ''),
            (EventSpec.gameedit_set_insert_next_char_in_token, ''),
            (EventSpec.gameedit_set_insert_next_line_in_token, ''),
            (EventSpec.gameedit_set_insert_first_char_in_token, ''),
            (EventSpec.gameedit_set_insert_last_char_in_token, ''),
            (EventSpec.gameedit_delete_move_char_left_shift, ''),
            (EventSpec.gameedit_delete_move_char_right_shift, ''),
            (EventSpec.gameedit_delete_move_char_left, ''),
            (EventSpec.gameedit_delete_move_char_right, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_for_select_variation_mode(self):
        """Set keyboard bindings for selecting a variation.

        Cancel all the bindings for editing and navigating a game.  Character
        editing is not enabled in the situations where select variation can be
        invoked so those bindings do not need cancelling.

        """
        super().bind_for_select_variation_mode()
        for sequence, function in (
            # PGN non-move symbol insertion
            (EventSpec.gameedit_insert_comment, ''),
            (EventSpec.gameedit_insert_reserved, ''),
            (EventSpec.gameedit_insert_comment_to_eol, ''),
            (EventSpec.gameedit_insert_escape_to_eol, ''),
            (EventSpec.gameedit_insert_glyph, ''),
            (EventSpec.gameedit_insert_pgn_tag, ''),
            (EventSpec.gameedit_insert_pgn_seven_tag_roster, ''),
            (EventSpec.gameedit_insert_white_win, ''),
            (EventSpec.gameedit_insert_draw, ''),
            (EventSpec.gameedit_insert_black_win, ''),
            (EventSpec.gameedit_insert_other_result, ''),
            (EventSpec.gameedit_insert_castle_queenside, ''),
            # Token navigation ignoring token purpose (can reach all tokens)
            (EventSpec.gameedit_show_previous_token, ''),
            (EventSpec.gameedit_show_next_token, ''),
            (EventSpec.gameedit_show_first_token, ''),
            (EventSpec.gameedit_show_last_token, ''),
            # Comment navigation
            (EventSpec.gameedit_show_first_comment, ''),
            (EventSpec.gameedit_show_last_comment, ''),
            (EventSpec.gameedit_show_previous_comment, ''),
            (EventSpec.gameedit_show_next_comment, ''),
            # PGN tag navigation
            (EventSpec.gameedit_to_previous_pgn_tag, ''),
            (EventSpec.gameedit_to_next_pgn_tag, ''),
            # PGN tag deletion
            (EventSpec.gameedit_delete_empty_pgn_tag, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_for_edit_symbol_mode(self):
        """Set keyboard bindings for editing symbols.

        The bindings set in superclass method bind_for_viewmode are replaced by
        versions that cancel character edit bindings, restore the superclass
        bindings, and do the action.  The same is done for the PGN tag bindings
        set in bind_for_viewmode in this class.  The other bindings set in this
        class are kept because they allow character editing.

        """
        for sequence, function in (
            # superclass game navigation
            (EventSpec.gameedit_bind_and_show_previous_in_line,
             self.bind_and_show_prev_in_line),
            (EventSpec.gameedit_bind_and_show_previous_in_variation,
             self.bind_and_show_prev_in_var),
            (EventSpec.gameedit_bind_and_show_next_in_line,
             self.bind_and_show_next_in_line),
            (EventSpec.gameedit_bind_and_show_next_in_variation,
             self.bind_and_show_next_in_var),
            (EventSpec.gameedit_bind_and_show_first_in_line,
             self.bind_and_show_first_in_line),
            (EventSpec.gameedit_bind_and_show_last_in_line,
             self.bind_and_show_last_in_line),
            (EventSpec.gameedit_bind_and_show_first_in_game,
             self.bind_and_show_first_in_game),
            (EventSpec.gameedit_bind_and_show_last_in_game,
             self.bind_and_show_last_in_game),
            # PGN tag navigation
            (EventSpec.gameedit_bind_and_to_previous_pgn_tag,
             self.bind_and_to_prev_pgn_tag),
            (EventSpec.gameedit_bind_and_to_next_pgn_tag,
             self.bind_and_to_next_pgn_tag),
            # PGN tag deletion
            (EventSpec.gameedit_delete_empty_pgn_tag,
             self.delete_empty_pgn_tag),
            # Character editing
            (EventSpec.gameedit_delete_token_char_left,
             self.delete_token_char_left),
            (EventSpec.gameedit_delete_token_char_right,
             self.delete_token_char_right),
            (EventSpec.gameedit_delete_char_left,
             self.delete_char_left),
            (EventSpec.gameedit_delete_char_right,
             self.delete_char_right),
            (EventSpec.gameedit_set_insert_previous_line_in_token,
             self.set_insert_prev_line_in_token),
            (EventSpec.gameedit_set_insert_previous_char_in_token,
             self.set_insert_prev_char_in_token),
            (EventSpec.gameedit_set_insert_next_char_in_token,
             self.set_insert_next_char_in_token),
            (EventSpec.gameedit_set_insert_next_line_in_token,
             self.set_insert_next_line_in_token),
            (EventSpec.gameedit_set_insert_first_char_in_token,
             self.set_insert_first_char_in_token),
            (EventSpec.gameedit_set_insert_last_char_in_token,
             self.set_insert_last_char_in_token),
            (EventSpec.gameedit_add_char_to_token,
             self.add_char_to_token),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
        # Allowed characters defined in set_token_context() call

    def bind_for_movemode_on_exit_edit_symbol_mode(self):
        """Set keyboard bindings for editing symbols.

        The bindings set by bind_for_edit_symbol_mode() are replaced with those
        set by bind_for_viewmode().
        
        """
        super().bind_for_viewmode()
        if self.score.tag_ranges(EDIT_RESULT):
            self.score.bind(EventSpec.gameedit_insert_rav[0],
                            self.try_event(self.insert_rav))
            self.score.bind(EventSpec.gameedit_insert_rav_castle_queenside[0],
                            self.try_event(self.insert_rav_castle_queenside))
        for sequence, function in (
            # PGN tag navigation
            (EventSpec.gameedit_to_previous_pgn_tag, self.to_prev_pgn_tag),
            (EventSpec.gameedit_to_next_pgn_tag, self.to_next_pgn_tag),
            # PGN tag deletion
            (EventSpec.gameedit_delete_empty_pgn_tag, ''),
            # Character editing
            (EventSpec.gameedit_delete_token_char_left, ''),
            (EventSpec.gameedit_delete_token_char_right, ''),
            (EventSpec.gameedit_delete_char_left, ''),
            (EventSpec.gameedit_delete_char_right, ''),
            (EventSpec.gameedit_set_insert_previous_line_in_token, ''),
            (EventSpec.gameedit_set_insert_previous_char_in_token, ''),
            (EventSpec.gameedit_set_insert_next_char_in_token, ''),
            (EventSpec.gameedit_set_insert_next_line_in_token, ''),
            (EventSpec.gameedit_set_insert_first_char_in_token, ''),
            (EventSpec.gameedit_set_insert_last_char_in_token, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_for_non_move_navigation(self):
        """Set keyboard bindings for non-editable non-move tokens.

        The bindings set in superclass method bind_for_viewmode are replaced by
        versions that restore the superclass bindings, and do the action.

        """
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', ''),
            ('<ButtonPress-3>', self.try_event(self.popup_nonmove_menu)),
            ):
            self.score.bind(sequence, function)

        # This event rather than one of the others binding to '<KeyPress>':
        # gameedit_add_move_char_to_token, gameedit_insert_move, or
        # gameedit_insert_rav.
        # (Is the intent to cancel an action or wipe the slate clean.)
        self.score.bind(EventSpec.gameedit_add_char_to_token[0],
                        lambda e: 'break')

        for sequence, function in (
            # superclass game navigation
            (EventSpec.gameedit_non_move_show_previous_in_variation,
             self.non_move_show_prev_in_variation),
            (EventSpec.gameedit_non_move_show_previous_in_line,
             self.non_move_show_prev_in_line),
            (EventSpec.gameedit_non_move_show_next_in_line,
             self.non_move_show_next_in_line),
            (EventSpec.gameedit_non_move_show_next_in_variation,
             self.non_move_show_next_in_variation),
            (EventSpec.gameedit_non_move_show_first_in_line,
             self.non_move_show_first_in_line),
            (EventSpec.gameedit_non_move_show_last_in_line,
             self.non_move_show_last_in_line),
            (EventSpec.gameedit_non_move_show_first_in_game,
             self.non_move_show_first_in_game),
            (EventSpec.gameedit_non_move_show_last_in_game,
             self.non_move_show_last_in_game),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_for_movemode_on_exit_non_move_navigation(self):
        """Set keyboard bindings for move navigation.

        The <...> bindings set by bind_for_non_move_navigation() are replaced
        with those set by bind_for_viewmode().
        
        """
        # superclass game navigation
        super().bind_for_viewmode()
        if self.score.tag_ranges(EDIT_RESULT):
            self.score.bind(EventSpec.gameedit_insert_rav[0],
                            self.try_event(self.insert_rav))
            self.score.bind(EventSpec.gameedit_insert_rav_castle_queenside[0],
                            self.try_event(self.insert_rav_castle_queenside))

    def bind_for_edit_edited_move(self):
        """Set keyboard bindings for editing symbols when editing a move.

        The standard insert and delete character bindings are replaced.

        """
        self.bind_for_edit_symbol_mode()
        for sequence, function in (
            (EventSpec.gameedit_delete_move_char_left_shift,
             self.delete_move_char_left),
            (EventSpec.gameedit_delete_move_char_right_shift,
             self.delete_move_char_right),
            (EventSpec.gameedit_delete_move_char_left,
             self.delete_move_char_left),
            (EventSpec.gameedit_delete_move_char_right,
             self.delete_move_char_right),
            (EventSpec.gameedit_add_move_char_to_token,
             self.add_move_char_to_token),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_for_insert_or_edit_move(self):
        """Set keyboard bindings to start insert or edit move."""
        for sequence, function in (
            (EventSpec.gameedit_insert_move, self.insert_move),
            (EventSpec.gameedit_edit_move, self.edit_move),
            (EventSpec.gameedit_insert_castle_queenside,
             self.insert_move_castle_queenside),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
        
    def bind_for_insert_rav_no_edit_move(self):
        """Set keyboard bindings to insert variations with no move editing."""
        for sequence, function in (
            (EventSpec.gameedit_insert_rav, self.insert_rav),
            (EventSpec.gameedit_insert_rav_castle_queenside,
             self.insert_rav_castle_queenside),
            (EventSpec.gameedit_delete_move_char_left_shift, ''),
            (EventSpec.gameedit_delete_move_char_right_shift, ''),
            (EventSpec.gameedit_delete_move_char_left, ''),
            (EventSpec.gameedit_delete_move_char_right, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
        
    def bind_for_no_token_editing(self):
        """"""
        self.score.bind(EventSpec.gameedit_add_move_char_to_token,
                        lambda e: 'break')
        for sequence, function in (
            (EventSpec.gameedit_delete_move_char_left_shift, ''),
            (EventSpec.gameedit_delete_move_char_right_shift, ''),
            (EventSpec.gameedit_delete_move_char_left, ''),
            (EventSpec.gameedit_delete_move_char_right, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def delete_char_right(self, event):
        """"""
        self.delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
        return 'break'
        
    def delete_char_left(self, event):
        """"""
        self.delete_char_next_to_insert_mark(START_EDIT_MARK, tkinter.INSERT)
        return 'break'
        
    def delete_move_char_right(self, event):
        """"""
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
            self.process_move()
        elif self.is_game_or_rav_valid_without_move():
            self.delete_empty_move()
        return 'break'
        
    def delete_move_char_left(self, event):
        """"""
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(
                START_EDIT_MARK, tkinter.INSERT)
            self.process_move()
        elif self.is_game_or_rav_valid_without_move():
            self.delete_empty_move()
        return 'break'
        
    def delete_token_char_right(self, event):
        """"""
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
        else:
            self.delete_empty_token()
        return 'break'
        
    def delete_token_char_left(self, event):
        """"""
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(
                START_EDIT_MARK, tkinter.INSERT)
        else:
            self.delete_empty_token()
        return 'break'
        
    # Not sure if this will be needed.
    # Maybe use to handle text edit mode
    def edit_gamescore(self, event):
        """Edit game score on keyboard event."""
        if not self.is_game_in_text_edit_mode():
            return

    def map_game(self):
        """Extend to set insertion cursor at start of moves."""
        super().map_game()
        # Is INSERT_TOKEN_MARK redundant now?
        self.score.mark_set(INSERT_TOKEN_MARK, START_SCORE_MARK)
        self.score.mark_set(tkinter.INSERT, INSERT_TOKEN_MARK)

    def insert_comment(self, event=None):
        """Insert comment in game score after current."""
        if self.current:
            if not self.is_movetext_insertion_allowed():
                return 'break'
        self.insert_empty_comment()
        return self.show_next_comment()
        
    def insert_comment_to_eol(self, event=None):
        """Insert comment to eol in game score after current."""
        if self.current:
            if not self.is_movetext_insertion_allowed():
                return 'break'
        self.insert_empty_comment_to_eol()
        return self.show_next_comment()
        
    def insert_escape_to_eol(self, event=None):
        """Insert escape to eol in game score after current."""
        if self.current:
            if not self.is_movetext_insertion_allowed():
                return 'break'
        self.insert_empty_escape_to_eol()
        return self.show_next_comment()
        
    def insert_glyph(self, event=None):
        """Insert glyph in game score after current."""
        if self.current:
            if not self.is_movetext_insertion_allowed():
                return 'break'
        self.insert_empty_glyph()
        return self.show_next_comment()
        
    def insert_pgn_tag(self, event=None):
        """Insert a single empty pgn tag in game score after current."""
        if self.current:
            if not self.is_pgn_tag_insertion_allowed():
                return 'break'
        self.insert_empty_pgn_tag()
        if self.current:
            return self.show_next_pgn_tag_field_name()
        elif self.score.compare(tkinter.INSERT, '<', START_SCORE_MARK):
            self.score.mark_set(
                tkinter.INSERT,
                self.score.index(tkinter.INSERT + ' linestart -1 lines'))
            return self.show_next_token()
        else:
            return self.show_prev_pgn_tag_field_name()
        
    def insert_pgn_seven_tag_roster(self, event=None):
        """Insert an empty pgn seven tag roster in game score after current."""
        if self.current:
            if not self.is_pgn_tag_insertion_allowed():
                return 'break'
        self.insert_empty_pgn_seven_tag_roster()
        if self.current:
            return self.show_next_pgn_tag_field_name()
        elif self.score.compare(tkinter.INSERT, '<', START_SCORE_MARK):
            self.score.mark_set(
                tkinter.INSERT,
                self.score.index(tkinter.INSERT + ' linestart -7 lines'))
            return self.show_next_token()
        else:
            return self.show_prev_pgn_tag_field_name()
        
    def insert_rav(self, event):
        """Edit game score on keyboard event."""
        # To catch insertion when no moves, even incomplete or illegal, exist.
        # Perhaps it is better to put this test in bind_...() methods.  Hope
        # that will not add too many states for one rare case.
        if not self.is_rav_insertion_allowed():
            return self.insert_move(event)
        if not event.char:
            return 'break'
        if event.char in _MOVECHARS:
            inserted_move = self.insert_empty_rav_after_next_move(
                event.char.translate(_FORCECASE))
            while not self.is_move_start_of_variation(
                inserted_move, self.step_one_variation(self.current)):
                pass
            self.colour_variation()
            # self.set_current() already called
        return 'break'

    def insert_rav_castle_queenside(self, event):
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
        if not self.is_rav_insertion_allowed():
            return self.insert_move_castle_queenside(event)
        if not event.char:
            return 'break'
        inserted_move = self.insert_empty_rav_after_next_move('O-O-O')
        while not self.is_move_start_of_variation(
            inserted_move, self.step_one_variation(self.current)):
            pass
        self.colour_variation()
        self.process_move()
        return 'break'

    def insert_result(self, v):
        """Insert or edit the game termination sequence and PGN Result Tag."""
        er = self.score.tag_ranges(EDIT_RESULT)
        tt = self.score.tag_ranges(TERMINATION_TAG)
        if tt:
            ttn = self.score.tag_prevrange(EDIT_PGN_TAG_NAME, tt[-4])
            if ttn:
                if self.score.get(*ttn).strip() == TAG_RESULT:
                    # Insert then delete difference between tt[-2] and ntt[-2]
                    # before ntt[-2] to do tagging automatically.
                    start = str(tt[-4]) + '+1c'
                    self.score.delete(start, tt[-3])
                    self.score.insert(start, v)
                    ntt = self.score.tag_ranges(TERMINATION_TAG)
                    end = str(ntt[-2]) + '-1c'
                    for t in self.score.tag_names(tt[-4]):
                        self.score.tag_add(t, ntt[-3], end)
        if er:
            self.score.insert(er[0], v)
            ner = self.score.tag_ranges(EDIT_RESULT)
            for tn in self.score.tag_names(ner[0]):
                self.score.tag_add(tn, er[0], ner[0])
            self.score.delete(*ner)
        return 'break'

    def insert_result_draw(self):
        """Set 1/2-1/2 as the game termination sequence and PGN Result Tag."""
        self.insert_result(DRAW)

    def insert_result_event(self, event=None):
        """Insert or edit the game termination sequence and PGN Result Tag."""
        self.insert_result(_TERMINATION_MAP.get(event.keysym))

    def insert_result_loss(self):
        """Set 0-1 as the game termination sequence and PGN Result Tag."""
        self.insert_result(BLACK_WIN)

    def insert_result_termination(self):
        """Set * as the game termination sequence and PGN Result Tag."""
        self.insert_result(UNKNOWN_RESULT)

    def insert_result_win(self):
        """Set 1-0 as the game termination sequence and PGN Result Tag."""
        self.insert_result(WHITE_WIN)
        
    def insert_reserved(self, event=None):
        """Insert reserved in game score after current."""
        if self.current:
            if not self.is_movetext_insertion_allowed():
                return 'break'
        self.insert_empty_reserved()
        return self.show_next_comment()

    def insert_castle_queenside_command(self):
        """Insert or edit the O-O-O movetext."""
        ria = self.is_rav_insertion_allowed()
        c = self.score.tag_ranges(self.current)

        # Is current move last move in game?
        # [-2], start of move, would do too.
        if c and ria:
            if c[-1] == self.score.tag_ranges(NAVIGATE_MOVE)[-1]:
                ria = False

        # Is current move last move in a variation?
        # Not [-1], end of move, because rm[-1] includes space after move.
        if ria:
            rm = self.score.tag_ranges(LINE_TAG)
            if rm:
                if rm[-2] == c[-2]:
                    ria = False

        if not ria:
            self.insert_empty_move_after_currentmove('O-O-O')
            self.show_next_in_line()
            self.process_move()
            return 'break'
        inserted_move = self.insert_empty_rav_after_next_move('O-O-O')
        while not self.is_move_start_of_variation(
            inserted_move, self.step_one_variation(self.current)):
            pass
        self.colour_variation()
        self.process_move()
        return 'break'
        
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
            if self.score.compare(next_rav_end[0], '>', next_move[0]):
                return False
        return True

    def edit_move(self, event):
        """Start editing last move in variation.

        Remove current move from EDIT_MOVE tag and add to MOVE_EDITED tag.
        Reset current and delete the last character from the token.

        """
        start, end = self.score.tag_ranges(self.current)
        self.score.tag_remove(EDIT_MOVE, start, end)
        self.score.tag_add(MOVE_EDITED, start, end)
        if self.is_currentmove_in_main_line():
            current = self.select_prev_move_in_line()
        elif self.is_currentmove_start_of_variation():
            choice = self.get_choice_tag_of_index(start)
            prior = self.get_prior_tag_for_choice(choice)
            try:
                current = self.get_position_tag_of_index(
                    self.score.tag_ranges(prior)[0])
            except IndexError:
                current = None
        else:
            current = self.select_prev_move_in_line()
        self.edit_move_context[
            self.current] = self.create_edit_move_context(current)
        self.tagpositionmap[self.current] = self.tagpositionmap[current]
        self.set_current()
        self.set_game_board()
        return self.delete_move_char_left(event)

    def insert_move(self, event):
        """Insert first character of new move in game score."""
        if not event.char:
            return 'break'
        if event.char in _MOVECHARS:
            self.insert_empty_move_after_currentmove(
                event.char.translate(_FORCECASE))
            return self.show_next_in_line()
        return 'break'

    def insert_move_castle_queenside(self, event):
        """Insert or edit the O-O-O movetext.

        If intending to type O-O-O when both O-O and O-O-O are possible the
        O-O is accepted before the chance to type the second '-' arrives.
        'Ctrl o' and the menu equivalent provide a positive way of indicating
        the O-O-O move.  A negative way of inserting O-O-O is to type O--O and
        then type the middle 'O'.

        """
        if not event.char:
            return 'break'
        self.insert_empty_move_after_currentmove('O-O-O')
        self.show_next_in_line()
        self.process_move()
        return 'break'

    def setup_non_move_navigation(self, tagnames, tagranges):
        """"""
        self.bind_for_non_move_navigation()
        
    def setup_no_editing(self):
        """"""
        self.bind_for_no_token_editing()

    def non_move_show_first_in_game(self, event=None):
        """Display initial position of line containing current move."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_first_in_game(event)

    def non_move_show_first_in_line(self, event=None):
        """Display initial position of line containing current move."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_first_in_line(event)

    def non_move_show_last_in_game(self, event=None):
        """Display final position of game."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_last_in_game(event)
        
    def non_move_show_last_in_line(self, event=None):
        """Display final position of line containing current move."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_last_in_line(event)
        
    def non_move_show_next_in_line(self, event=None):
        """Display next position of selected line."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_next_in_line(event)

    def non_move_show_next_in_variation(self, event=None):
        """Display choices if these exist or next position of selected line."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_next_in_variation(event)
        
    def non_move_show_prev_in_line(self, event=None):
        """Display previous position of selected line."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        # self.set_current() already called
        self.set_game_board()
        return 'break'
        
    def non_move_show_prev_in_variation(self, event=None):
        """Display choices in previous position of selected line."""
        self.bind_for_movemode_on_exit_non_move_navigation()
        self.set_nearest_move_to_token_as_currentmove()
        # self.set_current() already called
        self.set_game_board()
        return 'break'

    def set_current(self):
        """Extend to set edit and navigation bindings for current token.

        All characters have one tag which indicates the edit rules that apply
        to the token containing the character.  For RAV markers it is the
        absence of such a tag that indicates the rule.  Default is no editing.

        """
        # This method and those called adjust bindings so do not call context
        # independent binding setup methods after this method for an event.
        # May add RAV markers to _EDIT_TAGS eventually
        # Editing token possible only if no moves in game score
        tagranges = self.set_current_range()
        if tagranges:
            tagnames = self.score.tag_names(tagranges[0])
            if tagnames:
                tns = set(tagnames)
                tn = tns.intersection(_EDIT_TAGS)
                if tn:
                    # Hack to deal with PGN Tag Value tagging while these items
                    # are tagged by EDIT_PGN_TAG_VALUE and EDIT_PGN_TAG_NAME
                    tnn = tn.pop()
                    if EDIT_PGN_TAG_VALUE in tn:
                        tnn = EDIT_PGN_TAG_VALUE
                    self.set_token_context(tagnames, tagranges, tnn)
                    if self.is_movetext_insertion_allowed():
                        self.score.bind(
                            '<ButtonPress-3>',
                            self.try_event(self.popup_viewmode_menu)),
                    else:
                        self.score.bind(
                            '<ButtonPress-3>',
                            self.try_event(self.popup_pgn_tag_menu)),
                    return
                elif NAVIGATE_MOVE not in tns:
                    self.setup_non_move_navigation(tagnames, tagranges)
            self.score.mark_set(INSERT_TOKEN_MARK, tagranges[1])
            self.score.mark_set(tkinter.INSERT, INSERT_TOKEN_MARK)
            self.set_move_tag(*tagranges)
            if self.is_movetext_insertion_allowed():
                self.score.bind(
                    '<ButtonPress-3>',
                    self.try_event(self.popup_viewmode_menu)),
            else:
                self.score.bind(
                    '<ButtonPress-3>',
                    self.try_event(self.popup_pgn_tag_menu)),
        elif self.current is None:
            self.score.mark_set(INSERT_TOKEN_MARK, START_SCORE_MARK)
            self.score.mark_set(tkinter.INSERT, INSERT_TOKEN_MARK)
            self.bind_for_viewmode()
            return
        self.setup_no_editing()

    def set_insert_first_char_in_token(self, event):
        """"""
        self.set_insert_mark_at_start_of_token()
        return 'break'

    def set_insert_last_char_in_token(self, event):
        """"""
        self.set_insert_mark_at_end_of_token()
        return 'break'

    def set_insert_next_char_in_token(self, event):
        """"""
        self.set_insert_mark_right_one_char()
        return 'break'

    def set_insert_next_line_in_token(self, event):
        """"""
        self.set_insert_mark_down_one_line()
        return 'break'

    def set_insert_prev_char_in_token(self, event):
        """"""
        self.set_insert_mark_left_one_char()
        return 'break'

    def set_insert_prev_line_in_token(self, event):
        """"""
        self.set_insert_mark_up_one_line()
        return 'break'

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
    
    def show_first_comment(self, event=None):
        """Display first comment in game score."""
        return self.show_item(new_item=self.select_first_comment_in_game())
        
    def show_last_comment(self, event=None):
        """Display last comment in game score."""
        return self.show_item(new_item=self.select_last_comment_in_game())
        
    def show_next_comment(self, event=None):
        """Display next comment in game score."""
        return self.show_item(new_item=self.select_next_comment_in_game())
        
    def show_prev_comment(self, event=None):
        """Display previous comment in game score."""
        return self.show_item(new_item=self.select_prev_comment_in_game())
        
    def show_first_token(self, event=None):
        """Display first token in game score (usually first PGN Tag)."""
        if self.current is None:
            return 'break'
        return self.show_item(new_item=self.select_first_token_in_game())
        
    def show_last_token(self, event=None):
        """Display last token in game score (usually termination, 1-0 etc)."""
        return self.show_item(new_item=self.select_last_token_in_game())
        
    def show_next_token(self, event=None):
        """Display next token in game score (ignore rav structure of game)."""
        return self.show_item(new_item=self.select_next_token_in_game())
        
    def show_prev_token(self, event=None):
        """Display prev token in game score (ignore rav structure of game)."""
        return self.show_item(new_item=self.select_prev_token_in_game())
        
    def show_next_pgn_tag_field_name(self, event=None):
        """Display next pgn tag field name."""
        return self.show_item(new_item=self.select_next_pgn_tag_field_name())

    def show_prev_pgn_tag_field_name(self, event=None):
        """Display previous pgn tag field name."""
        return self.show_item(new_item=self.select_prev_pgn_tag_field_name())

    def to_prev_pgn_tag(self, event=None):
        """Position insertion cursor before preceding pgn tag in game score."""
        self.clear_moves_played_in_variation_colouring_tag()
        self.clear_choice_colouring_tag()
        self.clear_variation_colouring_tag()
        if self.score.compare(tkinter.INSERT, '>', START_SCORE_MARK):
            self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
        else:
            tr = self.score.tag_prevrange(PGN_TAG, tkinter.INSERT)
            if tr:
                self.score.mark_set(tkinter.INSERT, tr[0])
            else:
                self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
        self.current = None
        #self.set_current() # sets Tkinter.INSERT to wrong position

        # Hack in case arriving from last move in line
        self.score.bind(EventSpec.gameedit_insert_move, lambda e: 'break')
        self.score.bind(EventSpec.gameedit_edit_move, '')
        self.score.bind(EventSpec.gameedit_insert_castle_queenside,
                        lambda e: 'break')

        self.clear_current_range()
        self.set_game_board()
        self.score.see(tkinter.INSERT)
        return 'break'
        
    def to_next_pgn_tag(self, event=None):
        """Position insertion cursor before following pgn tag in game score."""
        self.clear_moves_played_in_variation_colouring_tag()
        self.clear_choice_colouring_tag()
        self.clear_variation_colouring_tag()
        if self.score.compare(tkinter.INSERT, '>', START_SCORE_MARK):
            tr = self.score.tag_nextrange(PGN_TAG, '1.0')
        else:
            tr = self.score.tag_nextrange(PGN_TAG, tkinter.INSERT)
        if tr:
            self.score.mark_set(tkinter.INSERT, str(tr[-1]) + '+1c')
        else:
            self.score.mark_set(tkinter.INSERT, '1.0')
        self.current = None
        #self.set_current() # sets Tkinter.INSERT to wrong position

        # Hack in case arriving from last move in line
        self.score.bind(EventSpec.gameedit_insert_move, lambda e: 'break')
        self.score.bind(EventSpec.gameedit_edit_move, '')
        self.score.bind(EventSpec.gameedit_insert_castle_queenside,
                        lambda e: 'break')

        self.clear_current_range()
        self.set_game_board()
        self.score.see(tkinter.INSERT)
        return 'break'
        
    def bind_and_show_first_in_line(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_first_in_line(event)

    def bind_and_show_first_in_game(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_first_in_game(event)

    def bind_and_show_last_in_line(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_last_in_line(event)

    def bind_and_show_last_in_game(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_last_in_game(event)

    def bind_and_show_next_in_line(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_next_in_line(event)

    def bind_and_show_next_in_var(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_next_in_variation(event)

    def bind_and_show_prev_in_var(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        # self.set_current() already called
        self.set_game_board()
        return 'break'

    def bind_and_show_prev_in_line(self, event=None):
        """"""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        self.set_nearest_move_to_token_as_currentmove()
        # self.set_current() already called
        self.set_game_board()
        return 'break'

    def bind_and_to_prev_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at previous PGN tag."""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        return self.to_prev_pgn_tag()
        
    def bind_and_to_next_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at next PGN tag."""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        return self.to_prev_pgn_tag() # to start of current PGN tag if in one
        
    def _edit_current_move(self, event):
        """Edit current move from character in event."""
        self.bind_for_movemode_on_exit_edit_symbol_mode()
        return self.show_first_in_line()
        
    # dispatch dictionary for token binding selection
    token_bind_method = {
        EDIT_GLYPH: bind_for_edit_symbol_mode,
        EDIT_RESULT: bind_for_edit_symbol_mode,
        EDIT_PGN_TAG_NAME: bind_for_edit_symbol_mode,
        EDIT_PGN_TAG_VALUE: bind_for_edit_symbol_mode,
        EDIT_COMMENT: bind_for_edit_symbol_mode,
        EDIT_RESERVED: bind_for_edit_symbol_mode,
        EDIT_COMMENT_EOL: bind_for_edit_symbol_mode,
        EDIT_ESCAPE_EOL: bind_for_edit_symbol_mode,
        EDIT_MOVE_ERROR: bind_for_edit_symbol_mode,
        EDIT_MOVE: bind_for_insert_or_edit_move,
        INSERT_RAV: bind_for_insert_rav_no_edit_move,
        MOVE_EDITED: bind_for_edit_edited_move,
        }

    def add_move_to_editable_moves(self, start, end, variation):
        """Remove editable move in current line and add move at start end.

        This method allows editing of the last move in a rav or the game, and
        insertion of a new move after the editable move which then ceases to
        be editable.

        """
        widget = self.score
        current = widget.tag_prevrange(variation, tkinter.END)
        if current:
            widget.tag_remove(EDIT_MOVE, current[0], current[-1])
            widget.tag_add(INSERT_RAV, current[0], current[-1])
        widget.tag_add(EDIT_MOVE, start, end)
        widget.tag_remove(INSERT_RAV, start, end)

    def add_pgntag_to_map(self, name, value):
        """Add a PGN Tag, a name and value, to the game score.

        The PGN Tag consists of two editable tokens: the Tag name and the Tag
        value.  These are inserted and deleted together, never separately,
        formatted as [ <name> "<value>" ]\n.

        """
        widget = self.score
        start_tag = widget.index(tkinter.INSERT)
        # tag_symbols is, with tag having its Tk meaning,
        # ((<name tag suffix>, <range>), (<value tag suffix>, <range>))
        tag_symbols = super().add_pgntag_to_map(name, value)
        widget.tag_add(PGN_TAG, start_tag, str(tkinter.INSERT) + '-1c')
        widget.mark_set(
            START_SCORE_MARK,
            widget.index(
                widget.tag_prevrange(PGN_TAG, tkinter.END)[-1]) + '+1c')
        for et, ts in zip((EDIT_PGN_TAG_NAME, EDIT_PGN_TAG_VALUE), tag_symbols):
            widget.tag_add(et, *ts[-1])
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
            
    def add_text_pgntag_or_pgnvalue(self, token, tagset=(), separator=' '):
        """Add PGN Tagname or Tagvalue to game. Return POSITION tagname."""
        start, end, sepend = super(
            ).add_text_pgntag_or_pgnvalue(token, separator=separator)
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        widget = self.score
        for tag in tagset:
            widget.tag_add(tag, start, end)
        widget.mark_set(tokenmark, end)
        for tag in (NAVIGATE_TOKEN,):
            widget.tag_add(tag, start, end)
        self.add_position_tag_to_pgntag_tags(positiontag, start, end)
        return start, end, sepend

    def delete_empty_move(self):
        """"""
        widget = self.score
        if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) > 1:
            return
        tr = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if not tr:
            return
        if self.is_currentmove_in_main_line():
            current = self.select_prev_move_in_line()
            delete_rav = False
        elif self.is_currentmove_start_of_variation():
            choice = self.get_choice_tag_of_index(tr[0])
            prior = self.get_prior_tag_for_choice(choice)
            try:
                current = self.get_position_tag_of_index(
                    widget.tag_ranges(prior)[0])
            except IndexError:
                current = None
            self.step_one_variation_select(current)
            selection = self.get_selection_tag_for_prior(prior)
            sr = widget.tag_nextrange(choice, widget.tag_ranges(selection)[1])
            if sr:
                widget.tag_add(selection, *sr)
            else:
                widget.tag_add(
                    selection,
                    *widget.tag_nextrange(choice, '1.0')[:2])
            delete_rav = True
        else:
            current = self.select_prev_move_in_line()
            delete_rav = False
        if delete_rav:
            ravtag = self.get_rav_tag_for_rav_moves(
                self.get_variation_tag_of_index(tr[0]))
            # Tkinter.Text.delete does not support multiple ranges at
            # Python 2.7.1 so call delete for each range from highest to
            # lowest.  Perhaps put a hack in workarounds?
            widget.delete(*widget.tag_ranges(self.get_token_tag_of_index(
                widget.tag_nextrange(
                    RAV_END_TAG,
                    widget.tag_prevrange(ravtag, tkinter.END)[0])[0])))
            widget.delete(tr[0], tr[1])
            widget.delete(*widget.tag_ranges(self.get_token_tag_of_index(
                widget.tag_nextrange(ravtag, '1.0')[0])))
        else:
            widget.delete(tr[0], tr[1])
        del self.edit_move_context[self.current]
        del self.tagpositionmap[self.current]
        self.current = current
        if delete_rav:
            ci = widget.tag_nextrange(choice, '1.0')[0] 
            if widget.compare(
                ci,
                '==',
                widget.tag_prevrange(choice, tkinter.END)[0]):
                widget.tag_remove(
                    ALL_CHOICES,
                    *widget.tag_nextrange(ALL_CHOICES, ci))
                widget.tag_delete(
                    choice, prior, self.get_selection_tag_for_prior(prior))
            self.clear_choice_colouring_tag()
            self.bind_for_movemode_on_exit_edit_symbol_mode()
            self.set_current()
            self.apply_colouring_to_variation_back_to_main_line()
        elif self.current is None:
            self.set_current()
        else:
            start, end = widget.tag_ranges(self.current)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(INSERT_RAV, start, end)
            if widget.tag_ranges(LINE_TAG):
                widget.tag_add(LINE_END_TAG, end, end)
            self.bind_for_movemode_on_exit_edit_symbol_mode()
            self.set_current()
        self.set_game_board()

    def delete_empty_pgn_tag(self, event=None):
        """"""
        widget = self.score
        start = widget.index(tkinter.INSERT + ' linestart')
        tr = widget.tag_nextrange(PGN_TAG, start, START_SCORE_MARK)
        if tr:
            if widget.compare(start, '==',  tr[0]):
                # Hack. Empty PGN Tag is len('[  "" ]').
                # Assume one PGN Tag per line.
                if len(widget.get(*tr)) == 7:
                    widget.delete(*tr)
                    widget.delete(tr[0] + '-1c') # the preceding newline if any
                    # INSERT has moved to end of previous line.  Put INSERT at
                    # start of PGN tag after the deleted one.
                    self.to_prev_pgn_tag()
                    self.to_next_pgn_tag()
        return 'break'

    def delete_empty_token(self):
        """"""
        widget = self.score
        if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) > 1:
            return
        tr = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if tr:
            if widget.compare(START_SCORE_MARK, '>', tkinter.INSERT):
                current = self.select_prev_token_in_game()
            else:
                current = self.select_prev_comment_in_game()
                if not current:
                    tpr = widget.tag_prevrange(
                        NAVIGATE_TOKEN, widget.tag_ranges(self.current)[0])
                    if tpr:
                        if widget.compare(tpr[0], '>', START_SCORE_MARK):
                            current = self.get_position_tag_of_index(tpr[0])
            widget.delete(*tr)
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
        if text_count(widget, first, last):
            if widget.compare(first, '==', tkinter.INSERT):
                widget.delete(tkinter.INSERT)
            else:
                widget.delete(tkinter.INSERT + '-1 chars')
            if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) == 0:
                if self._lead: # self.current will have a range. Or test range.
                    widget.tag_add(
                        MOVE_TAG,
                        ''.join((
                            str(widget.tag_ranges(self.current)[0]),
                            ' +',
                            str(self._lead - 1),
                            'chars')))
        
    def get_insertion_point_at_end_of_rav(self, insert_point_limit):
        """Return insertion point for new move at end of RAV.

        insert_point_limit is the earliest point in the score at which the
        new move can be inserted and will usually be the index of the last
        character of the move before the new move.

        The possible situations before the new move is inserted are:

        ... move )
        ... move ( moves ) )
        ... move comment )
        ... move <ravs and comments in any order> )

        The final ) can be 1-0, 0-1, 1/2-1/2, or * instead: one of the
        termination symbols.
        
        The sequence ( moves ) is the simplest example of a RAV.

        The insertion point for the new move is just before the final ).
        
        """
        widget = self.score
        end_rav = widget.tag_nextrange(RAV_END_TAG, insert_point_limit)
        next_move = widget.tag_nextrange(NAVIGATE_MOVE, insert_point_limit)
        if not end_rav:
            point = widget.tag_nextrange(EDIT_RESULT, insert_point_limit)
            if not point:
                return widget.index(tkinter.END)
            return point[0]
        if not next_move:
            return end_rav[0]
        if widget.compare(next_move[0], '>', end_rav[0]):
            return end_rav[0]

        # In 'd4 d5 ( e5 Nf3 ) *' with current position after d5 an attempt to
        # insert a move by 'c4', say, gives 'd4 d5 ( e5 c4 Nf3 ) *' not the
        # correct 'd4 d5 ( e5 Nf3 ) c4 *'.  The position is correct but the
        # generated PGN text is wrong.
        # Fixed by stepping through adjacent variations.
        # The potential use of end_rav before binding is allowed because a next
        # range relative to self.current should exist.
        # Bug 2013-06-19 note.
        # This method had some code which attempted to solve RAV insertion
        # problem until correct code added to insert_empty_rav_after_next_move()
        # method on 2015-09-05.
        depth = 0
        nr = widget.tag_ranges(self.current)
        while True:
            nr = widget.tag_nextrange(NAVIGATE_TOKEN, nr[-1])
            if not nr:
                return widget.index(end_rav[1] + '+1char')
            end_rav = nr
            token = widget.get(*nr)
            if token == START_RAV:
                depth += 1
            elif token == END_RAV:
                depth -= 1
                if depth < 0:
                    return widget.index(end_rav[1] + '-1char')

    def get_choice_tag_and_range_of_first_move(self):
        """Return choice tag name and range of first char for first move."""
        tr = self.score.tag_nextrange(NAVIGATE_MOVE, '1.0')
        if tr:
            return self.get_choice_tag_of_index(tr[0]), tr

    def get_prior_tag_and_range_of_move(self, move):
        """Return prior move tag name and move range for move tag."""
        tr = self.score.tag_ranges(move)
        if tr:
            return self.get_prior_tag_of_index(tr[0]), tr

    def get_prior_tag_of_index(self, index):
        """Return Tk tag name if index is in a choice tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(PRIOR_MOVE):
                return tn
        return None

    def get_rav_moves_of_index(self, index):
        """Return Tk tag name if index is in a rav_moves tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(RAV_MOVES):
                return tn
        return None

    def get_rav_tag_for_rav_moves(self, rav_moves):
        """Return Tk tag name for RAV_TAG with same suffix as rav_moves."""
        return ''.join((RAV_TAG, rav_moves[len(RAV_MOVES):]))

    def get_rav_tag_of_index(self, index):
        """Return Tk tag name if index is in a rav_tag tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(RAV_TAG):
                return tn
        return None

    def get_token_tag_for_position(self, position):
        """Return Tk tag name for token with same suffix as position."""
        return ''.join((TOKEN, position[len(POSITION):]))

    def get_token_tag_of_index(self, index):
        """Return Tk tag name if index is in TOKEN tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(TOKEN):
                return tn
        return None

    def get_variation_tag_of_index(self, index):
        """Return Tk tag name for variation of currentmove."""
        for tn in self.score.tag_names(index):
            if tn.startswith(RAV_MOVES):
                return tn

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
        r = widget.tag_ranges(token)
        while r:
            if r == widget.tag_nextrange(NAVIGATE_MOVE, *r):
                return self.get_position_tag_of_index(r[0])
            prior = self.get_prior_tag_of_index(r[0])
            if prior:
                if widget.tag_nextrange(RAV_END_TAG, *r):
                    return self.select_next_move_in_line(
                        movetag=self.get_position_tag_of_index(
                            widget.tag_ranges(prior)[0]))
                else:
                    return self.get_position_tag_of_index(
                        widget.tag_ranges(prior)[0])
            r = widget.tag_prevrange(NAVIGATE_TOKEN, r[0], START_SCORE_MARK)

    def get_previous_move_to_position(self, position):
        """Return previous move (may be None) to position, otherwise False.

        position is a POSITION<suffix> tag name which may no longer have any
        tagged characters but TOKEN<suffix> still tags at least one character.

        """
        # Find the previous token then call get_nearest_move_to_token.
        tr = self.score.tag_ranges(self.get_token_tag_for_position(position))
        if tr:
            return self.get_nearest_move_to_token(
                self.get_token_tag_of_index(
                    self.score.tag_prevrange(NAVIGATE_TOKEN, tr[0])[0]))
        else:
            return False

    def go_to_move(self, index):
        """Extend, set keyboard bindings for new pointer location."""
        if super().go_to_move(index):
            return
        return self.show_new_current(
            new_current=self.select_item_at_index(index))

    def insert_empty_move_after_currentmove(self, event_char):
        """Insert empty NAVIGATE_MOVE range after current move.

        The empty NAVIGATE_MOVE range becomes the current move but because
        the move is not there yet, or is at best valid but incomplete, the
        position displayed on board is for the old current move.

        """
        widget = self.score
        if not self.is_currentmove_in_edit_move():
            # Likely will not happen because insert RAV is allowed in this case.
            return
        # Methods used to get variation and start designed for other, more
        # general, cases.  Extra return values ignored.
        current = self.current
        if self.current is None:
            # Assume that no moves, including incomplete or illegal, exist.
            # In other words bindings prevent getting here if they do exist.
            p = self.score.tag_ranges(EDIT_RESULT)
            if p:
                widget.mark_set(tkinter.INSERT, p[0])
            else:
                widget.mark_set(tkinter.INSERT, tkinter.END)
            vartag = self.get_rav_tag_names()[0]
            self._gamevartag = vartag
        else:
            start_current, end_current = widget.tag_ranges(self.current)
            insert_point = self.get_insertion_point_at_end_of_rav(end_current)
            if not insert_point:
                return
            vartag = self.get_variation_tag_of_index(start_current)
            widget.mark_set(tkinter.INSERT, insert_point)

        self.get_next_positiontag_name()
        positiontag, tokentag, tokenmark = self.get_current_tag_and_mark_names()
        self.tagpositionmap[positiontag] = self.tagpositionmap[self.current]
        self.edit_move_context[
            positiontag] = self.create_edit_move_context(positiontag)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)
        for tag in (
            positiontag,
            vartag,
            NAVIGATE_MOVE,
            NAVIGATE_TOKEN,
            MOVE_EDITED,
            ):
            widget.tag_add(tag, start, end)
        if self.current is not None:
            widget.tag_remove(EDIT_MOVE, start_current, end_current)
            widget.tag_add(INSERT_RAV, start_current, end_current)
        if vartag == self._gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            ''.join((RAV_SEP, vartag)),
            ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        if widget.tag_ranges(LINE_TAG):
            widget.tag_remove(LINE_END_TAG, end_current, start)
            widget.tag_add(LINE_END_TAG, end, sepend)
            widget.tag_add(LINE_TAG, start, sepend)
        self.previousmovetags[positiontag] = (
            current,
            vartag,
            vartag)
        self.nextmovetags[current] = [positiontag, []]

    def insert_empty_comment(self):
        """Insert "{<null>) " sequence."""
        self.set_insertion_point_before_next_token()
        self.add_start_comment('{}', self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()

    def insert_empty_comment_to_eol(self):
        """Insert ";<null>\n " sequence."""
        self.set_insertion_point_before_next_token()
        self.add_comment_to_eol(';\n', self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()

    def insert_empty_escape_to_eol(self):
        """Insert "\n%<null>\n " sequence."""
        self.set_insertion_point_before_next_token()
        self.add_escape_to_eol('\n%\n', self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()

    def insert_empty_glyph(self):
        """Insert "$<null> " sequence."""
        self.set_insertion_point_before_next_token()
        self.add_glyph('$', self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()

    def insert_empty_pgn_tag(self):
        """Insert ' [ <null> "<null>" ] ' sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        self.add_pgntag_to_map('', '')

    def insert_empty_pgn_seven_tag_roster(self):
        """Insert ' [ <fieldname> "<null>" ... ] ' seven tag roster sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        for t in SEVEN_TAG_ROSTER:
            self.add_pgntag_to_map(t, '')

    def insert_empty_reserved(self):
        """Insert "<[null]>) " sequence."""
        self.set_insertion_point_before_next_token()
        self.add_start_reserved('<>', self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()

    def insert_empty_rav_after_next_move(self, event_char):
        """Insert " ( <event_char> )" sequence.

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        current = self.current
        choice = None
        ins = None
        if self.current is None:
            # Insert RAV after first move of game
            prior = None
            choice, range_ = self.get_choice_tag_and_range_of_first_move()
            if not choice:
                choice = self.get_choice_tag_name()
            variation = self.get_variation_tag_of_index(range_[0])
            nextmove = widget.tag_nextrange(variation, range_[0])
        else:
            # Insert RAV after move after current move
            prior, range_ = self.get_prior_tag_and_range_of_move(self.current)
            if prior:
                choice = self.get_choice_tag_for_prior(prior)
            else:
                choice = self.get_choice_tag_name()
                prior = self.get_prior_tag_for_choice(choice)
            variation = self.get_variation_tag_of_index(range_[0])
            nextmove = widget.tag_nextrange(variation, range_[-1])
        # Figure point where the new empty RAV should be inserted.
        ctr = widget.tag_ranges(choice)
        if ctr:
            point = widget.tag_ranges(
                self.get_rav_tag_for_rav_moves(
                    self.get_rav_moves_of_index(ctr[2])))[0]
        else:
            # No existing RAVs for the next move.
            for tn in variation, RAV_END_TAG, EDIT_RESULT:
                tr = widget.tag_nextrange(tn, nextmove[1])
                if tr:
                    point = tr[0]
            else:
                # Can keep going, but both raise exception and issue warning
                # dialogue are better options here.
                point = widget.index(nextmove[1] + '+1char')
        colourvariation = ''.join((RAV_SEP, variation))
        if prior is None:
            # no prior move for initial position of game
            '''seems ok to just set these tags even if already set'''
            start, end = nextmove
            widget.tag_add(ALL_CHOICES, start, end)
            widget.tag_add(choice, start, end)
        elif not widget.tag_nextrange(prior, '1.0'):
            # no variations exist immediately after current move so set up
            # variation choice structures.  map_insert_rav cannot do this as
            # it assumes variation structure exists, if at all, for preceding
            # moves only.
            if self.current:
                start, end = widget.tag_ranges(self.current)
                widget.tag_add(prior, start, end)
            start, end = nextmove
            widget.tag_add(ALL_CHOICES, start, end)
            widget.tag_add(choice, start, end)
        widget.mark_set(tkinter.INSERT, point)
        start, end, sepend = self.insert_token_into_text('(', SPACE_SEP)

        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        vartag, ravtag = self.get_rav_tag_names()
        if prior:
            self.tagpositionmap[positiontag] = self.tagpositionmap[self.current]
        else:
            self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        widget.tag_add(tokentag, start, sepend)
        for tag in ravtag, positiontag, NAVIGATE_TOKEN:
            widget.tag_add(tag, start, end)
        # Insert is surrounded by tagged colourvariation text unlike add at end.
        # This breaks the sequence so rest of inserts in this method do not get
        # tagged by colourvariation as well as ravtag.
        widget.tag_remove(colourvariation, start, sepend)
        try:
            self.previousmovetags[positiontag] = (
                self.previousmovetags[current][0],
                variation,
                variation)
        except KeyError:
            self.previousmovetags[positiontag] = (
                None,
                variation,
                variation)
    
        newmovetag = self.get_next_positiontag_name()
        positiontag, tokentag, tokenmark = self.get_current_tag_and_mark_names()
        self.tagpositionmap[positiontag] = self.tagpositionmap[self.current]
        self.edit_move_context[
            positiontag] = self.create_edit_move_context(positiontag)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)
        for tag in (
            positiontag,
            vartag,
            NAVIGATE_MOVE,
            ALL_CHOICES,
            self.get_selection_tag_for_choice(choice),
            choice,
            NAVIGATE_TOKEN,
            MOVE_EDITED,
            ):
            widget.tag_add(tag, start, end)
        if vartag is self._gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            ''.join((RAV_SEP, vartag)),
            LINE_TAG,
            ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        s, e = start, sepend
        self.previousmovetags[positiontag] = (
            current,
            vartag,
            variation)
        self.nextmovetags[current][1].append(positiontag)

        start, end, sepend = self.insert_token_into_text(')', SPACE_SEP)
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        self.tagpositionmap[positiontag] = self.tagpositionmap[
            self.nextmovetags[current][0]]
        for tag in (
            self.get_rav_tag_for_rav_moves(variation),
            positiontag,
            NAVIGATE_TOKEN,
            RAV_END_TAG):
            widget.tag_add(tag, start, end)
        widget.tag_add(tokentag, start, sepend)
        self.previousmovetags[positiontag] = (
            current,
            variation,
            variation)

        return newmovetag

    def is_currentmove_in_edit_move(self):
        """Return True if current move is editable.

        If there are no moves in the game current move is defined as editable.
        This allows games to be inserted.

        """
        if self.current is None:
            return not bool(self.score.tag_nextrange(NAVIGATE_MOVE, '1.0'))
        start, end = self.score.tag_ranges(self.current)
        return bool(self.score.tag_nextrange(EDIT_MOVE, start, end))

    def is_currentmove_in_edited_move(self):
        """Return True if current move is being edited.

        If there are no moves in the game current move is not being edited.

        """
        if self.current is None:
            return bool(self.score.tag_nextrange(NAVIGATE_MOVE, '1.0'))
        start, end = self.score.tag_ranges(self.current)
        return bool(self.score.tag_nextrange(MOVE_EDITED, start, end))

    def is_move_last_of_variation(self, move):
        """Return True if currentmove is at end of a variation tag"""
        widget = self.score
        index = widget.tag_ranges(move)[1]
        for tn in widget.tag_names(index):
            if tn.startswith(RAV_MOVES):
                return not bool(self.score.tag_nextrange(tn, index))

    def is_move_start_of_variation(self, move, variation):
        """Return True if move is at start of variation"""
        widget = self.score
        return widget.compare(
            widget.tag_ranges(move)[0],
            '==',
            widget.tag_ranges(variation)[0])

    def is_movetext_insertion_allowed(self):
        """Return True if current is not before start of movetext"""
        return bool(self.score.compare(
            START_SCORE_MARK,
            '<=',
            self.score.tag_ranges(self.current)[0]))

    def is_pgn_tag_insertion_allowed(self):
        """Return True if current is before start of movetext"""
        return bool(self.score.compare(
            START_SCORE_MARK,
            '>',
            self.score.tag_ranges(self.current)[0]))

    def is_rav_insertion_allowed(self):
        """Return True if at least one move exists in game score."""
        # To be decided if at least one legal move exists.  Check EDIT_MOVE
        # instead?
        return bool(self.score.tag_nextrange(NAVIGATE_MOVE, '1.0'))

    # Do the add_* methods need position even though the map_* methods do not?
    def link_inserts_to_moves(self, positiontag, position):
        """Link inserted comments to moves for matching position display."""
        self.tagpositionmap[positiontag] = position
        if self.current:
            variation = self.get_variation_tag_of_index(
                self.score.tag_ranges(self.current)[0])
            try:
                self.previousmovetags[positiontag] = (
                    self.previousmovetags[self.current][0],
                    variation,
                    variation)
            except KeyError:
                self.previousmovetags[positiontag] = (None, None, None)
        else:
            self.previousmovetags[positiontag] = (None, None, None)

    def map_move_text(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_move_text(token, position),
            self.get_current_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, INSERT_RAV),
            tag_position=False, # already tagged by superclass method
            )
        self._token_position = self.tagpositionmap[positiontag]
        return token_indicies

    def map_start_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        # need self._choicetag set by supersclass method
        token_indicies = super().map_start_rav(token, position)
        prior = self.get_prior_tag_for_choice(self._choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            self._token_position = self.tagpositionmap[
                self.get_position_tag_of_index(prior_range[0])]
            tags = (self._ravtag, NAVIGATE_TOKEN, prior)
        else:
            self._token_position = self.tagpositionmap[None]
            tags = (self._ravtag, NAVIGATE_TOKEN)
        positiontag, token_indicies = self.tag_token_for_editing(
            token_indicies,
            self.get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
            )
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_end_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        # last move in rav is editable
        self.add_move_to_editable_moves(
            self._start_latest_move, self._end_latest_move, self._vartag)
        # need self._choicetag set by supersclass method
        token_indicies = super().map_end_rav(token, position)
        prior = self.get_prior_tag_for_choice(self._choicetag)
        if self.score.tag_ranges(prior):
            tags = (self._ravtag, NAVIGATE_TOKEN, RAV_END_TAG, prior)
        else:
            tags = (self._ravtag, NAVIGATE_TOKEN, RAV_END_TAG)
        # Superclass method will reset self._token_position self._vartag
        positiontag, token_indicies = self.tag_token_for_editing(
            token_indicies,
            self.get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
            )
        self.tagpositionmap[positiontag] = self.tagpositionmap[
            self.get_position_tag_of_index(
                self.score.tag_prevrange(self._vartag, tkinter.END)[0])]
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_termination(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # last move in game is editable
        if self._start_latest_move:
            self.add_move_to_editable_moves(
                self._start_latest_move, self._end_latest_move, self._vartag)
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_termination(token),
            self.get_tag_and_mark_names,
            #tag_start_to_end=(EDIT_RESULT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            tag_start_to_end=(EDIT_RESULT, ),
            )
        self.tagpositionmap[positiontag] = self._token_position
        return token_indicies

    def _map_start_comment(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        return self.tag_token_for_editing(
            super().map_start_comment(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_COMMENT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            )

    def add_start_comment(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_start_comment(token)
        self.link_inserts_to_moves(positiontag, position)
        return token_indicies

    def map_start_comment(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_start_comment(token)
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def _map_comment_to_eol(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        return self.tag_token_for_editing(
            super().map_comment_to_eol(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(
                EDIT_COMMENT_EOL, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            )

    def add_comment_to_eol(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_comment_to_eol(token)
        self.link_inserts_to_moves(positiontag, position)
        return token_indicies

    def map_comment_to_eol(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_comment_to_eol(token)
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def _map_escape_to_eol(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        return self.tag_token_for_editing(
            super().map_escape_to_eol(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(
                EDIT_ESCAPE_EOL, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            )

    def add_escape_to_eol(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_escape_to_eol(token)
        self.link_inserts_to_moves(positiontag, position)
        return token_indicies

    def map_escape_to_eol(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_escape_to_eol(token)
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_integer(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_integer(token, position),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, ),
            mark_for_edit=False,
            )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_glyph(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        return self.tag_token_for_editing(
            super().map_glyph(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_GLYPH, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            )

    def add_glyph(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_glyph(token)
        self.link_inserts_to_moves(positiontag, position)
        return token_indicies

    def map_glyph(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_glyph(token)
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_period(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_period(token, position),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, ),
            mark_for_edit=False,
            )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_start_reserved(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        return self.tag_token_for_editing(
            super().map_start_reserved(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_RESERVED, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            )

    def add_start_reserved(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_start_reserved(token)
        self.link_inserts_to_moves(positiontag, position)
        return token_indicies

    def map_start_reserved(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_start_reserved(token)
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_non_move(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # mark_for_edit is True while no EDIT_... tag is done?
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_non_move(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            )
        self.tagpositionmap[positiontag] = None
        return token_indicies

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
                movetext.join(self.edit_move_context[self.current])))
        if mtc.is_movetext_valid():
            bishopmove = False
            if (movetext.startswith(FEN_BLACK_BISHOP+PGN_CAPTURE_MOVE) and
                movetext[2] in 'ac' and movetext[3] not in '18'):
                amtc = next(
                    PGN(game_class=GameDisplayMoves).read_games(
                        (PGN_BISHOP+movetext[1:]).join(
                            self.edit_move_context[self.current])))
                if amtc.is_movetext_valid():
                    if dialogues.askyesno(
                        title='Bishop or Pawn Capture',
                        message=''.join(
                            ("Movetext '", movetext, "' would be a bishop ",
                             "move if 'b' were 'B'.\n\n",
                             "Is it a bishop move?",
                             ))):
                        bishopmove = True
                        mtc = amtc
            self.tagpositionmap[self.current] = (
                mtc._piece_placement_data.copy(),
                mtc._active_color,
                mtc._castling_availability,
                mtc._en_passant_target_square,
                mtc._halfmove_clock,
                mtc._fullmove_number)
            del self.edit_move_context[self.current]
            # remove from MOVE_EDITED tag and place on EDIT_MOVE tag
            # removed from EDIT_MOVE tag and placed on INSERT_RAV tag when
            # starting insert of next move.
            start, end = self.score.tag_ranges(self.current)
            vartag = self.get_variation_tag_of_index(start)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(MOVE_EDITED, start, end)
            if bishopmove:
                widget.insert(widget.index(start) + '+1 char', PGN_BISHOP)
                widget.delete(widget.index(start))
            self.bind_for_movemode_on_exit_edit_symbol_mode()
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
                (PGN_BISHOP+movetext[1:]).join(
                    self.edit_move_context[self.current])))
        if mtc.is_movetext_valid():
            self.tagpositionmap[self.current] = (
                mtc._piece_placement_data.copy(),
                mtc._active_color,
                mtc._castling_availability,
                mtc._en_passant_target_square,
                mtc._halfmove_clock,
                mtc._fullmove_number)
            del self.edit_move_context[self.current]
            # remove from MOVE_EDITED tag and place on EDIT_MOVE tag
            # removed from EDIT_MOVE tag and placed on INSERT_RAV tag when
            # starting insert of next move.
            start, end = self.score.tag_ranges(self.current)
            vartag = self.get_variation_tag_of_index(start)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(MOVE_EDITED, start, end)
            widget.insert(widget.index(start) + '+1 char', PGN_BISHOP)
            widget.delete(widget.index(start))
            self.bind_for_movemode_on_exit_edit_symbol_mode()
            self.set_current()
            self.set_game_board()

    def select_item_at_index(self, index):
        """Return the itemtype tag associated with index"""
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
                    for tn in tns:
                        if tn.startswith(POSITION):
                            return tn
        except IndexError:
            # Not sure the explicit setting is needed.
            self._allowed_chars_in_token = ''
            return None
        # Not sure the explicit setting is needed.
        self._allowed_chars_in_token = ''
        return None

    def select_first_comment_in_game(self):
        """Return POSITION tag associated with first comment in game"""
        widget = self.score
        try:
            index = widget.tag_nextrange(NAVIGATE_COMMENT, '1.0')[0]
            for tn in widget.tag_names(index):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return None
        return None

    def select_last_comment_in_game(self):
        """Return POSITION tag associated with last comment in game"""
        widget = self.score
        try:
            index = widget.tag_prevrange(NAVIGATE_COMMENT, tkinter.END)[0]
            for tn in widget.tag_names(index):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return None
        return None

    def select_next_comment_in_game(self):
        """Return POSITION tag associated with comment after current in game"""
        widget = self.score
        try:
            oldtr = widget.tag_ranges(MOVE_TAG)
            if oldtr:
                tr = widget.tag_nextrange(NAVIGATE_COMMENT, oldtr[-1])
            else:
                tr = widget.tag_nextrange(NAVIGATE_COMMENT, tkinter.INSERT)
            for tn in widget.tag_names(tr[0]):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return self.select_first_comment_in_game()
        return None

    def select_prev_comment_in_game(self):
        """Return POSITION tag associated with comment before current in game"""
        # Hack copied from select_prev_token_in_game
        widget = self.score
        try:
            if self.current:
                oldtr = widget.tag_ranges(self.current)
            else:
                oldtr = widget.tag_ranges(MOVE_TAG)
            if oldtr:
                index = widget.tag_prevrange(NAVIGATE_COMMENT, oldtr[0])[0]
            else:
                return None
            for tn in widget.tag_names(index):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return None
        return None

    def select_next_pgn_tag_field_name(self):
        """Return POSITION tag for nearest following PGN Tag field"""
        widget = self.score
        try:
            if self.current:
                index = widget.tag_nextrange(
                    NAVIGATE_TOKEN,
                    widget.index(
                        str(widget.tag_ranges(self.current)[0]) + ' lineend'),
                    START_SCORE_MARK)
                for tn in widget.tag_names(index[0]):
                    if tn.startswith(POSITION):
                        return tn
        except IndexError:
            return self.current
        return self.current

    def select_prev_pgn_tag_field_name(self):
        """Return POSITION tag for nearest preceding PGN Tag field"""
        widget = self.score
        try:
            if self.current:
                index = widget.tag_prevrange(
                    NAVIGATE_TOKEN,
                    widget.index(
                        str(widget.tag_ranges(self.current)[0]) + ' linestart'))
                for tn in widget.tag_names(index[0]):
                    if tn.startswith(POSITION):
                        return tn
            else:
                index = widget.tag_prevrange(
                    NAVIGATE_TOKEN,
                    widget.tag_prevrange(NAVIGATE_TOKEN, START_SCORE_MARK)[0])
                for tn in widget.tag_names(index[0]):
                    if tn.startswith(POSITION):
                        return tn
        except IndexError:
            return self.current
        return self.current

    def select_nearest_pgn_tag(self):
        """Return POSITION tag for nearest preceding PGN Tag field"""
        # do nothing at first
        return self.current

    def select_first_token_in_game(self):
        """Return POSITION tag associated with first token in game"""
        widget = self.score
        try:
            index = widget.tag_nextrange(NAVIGATE_TOKEN, '1.0')[0]
            for tn in widget.tag_names(index):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return None
        return None

    def select_last_token_in_game(self):
        """Return POSITION tag associated with last token in game"""
        widget = self.score
        try:
            index = widget.tag_prevrange(NAVIGATE_TOKEN, tkinter.END)[0]
            for tn in widget.tag_names(index):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return None
        return None

    def select_next_token_in_game(self):
        """Return POSITION tag associated with token after current in game"""
        widget = self.score
        try:
            oldtr = widget.tag_ranges(MOVE_TAG)
            if oldtr:
                tr = widget.tag_nextrange(NAVIGATE_TOKEN, oldtr[-1])
            else:
                tr = widget.tag_nextrange(NAVIGATE_TOKEN, tkinter.INSERT)
            for tn in widget.tag_names(tr[0]):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return self.select_first_token_in_game()
        return None

    def select_prev_token_in_game(self):
        """Return POSITION tag associated with token before current in game"""
        # Hack find prev token.  Needs to be in in prev comment as well.
        # And done properly.  Prev move ok as no lead chars to be left out
        # of MOVE_TAG when editing.
        widget = self.score
        tag = self.current
        if not tag:
            tag = MOVE_TAG
        try:
            oldtr = widget.tag_ranges(tag)
            if oldtr:
                tr = widget.tag_prevrange(NAVIGATE_TOKEN, oldtr[0])
            else:
                tr = widget.tag_prevrange(NAVIGATE_TOKEN, tkinter.INSERT)
            for tn in widget.tag_names(tr[0]):
                if tn.startswith(POSITION):
                    return tn
        except IndexError:
            return self.select_last_token_in_game()
        return None

    def set_insert_mark_at_end_of_token(self):
        """"""
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)
        
    def set_insert_mark_at_start_of_token(self):
        """"""
        self.score.mark_set(tkinter.INSERT, START_EDIT_MARK)
        
    def set_insert_mark_down_one_line(self):
        """"""
        widget = self.score
        if widget.compare(tkinter.INSERT, '<', END_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + ' +1 display lines')
            if widget.compare(tkinter.INSERT, '>', END_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, END_EDIT_MARK)
        
    def set_insert_mark_left_one_char(self):
        """"""
        widget = self.score
        if widget.compare(tkinter.INSERT, '>', START_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + ' -1 chars')
        
    def set_insert_mark_right_one_char(self):
        """"""
        widget = self.score
        if widget.compare(tkinter.INSERT, '<', END_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + ' +1 chars')
        
    def set_insert_mark_up_one_line(self):
        """"""
        widget = self.score
        if widget.compare(tkinter.INSERT, '>', START_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + ' -1 display lines')
            if widget.compare(tkinter.INSERT, '<', START_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, START_EDIT_MARK)
        
    def set_insertion_point_before_next_token(self):
        """"""
        widget = self.score
        if self.current is None:
            widget.mark_set(tkinter.INSERT, START_SCORE_MARK)
            return
        range_ = widget.tag_ranges(self.current)
        try:
            widget.mark_set(
                tkinter.INSERT,
                widget.tag_nextrange(
                    NAVIGATE_TOKEN,
                    range_[-1])[0]
                )
        except IndexError:
            widget.mark_set(tkinter.INSERT, widget.tag_ranges(EDIT_RESULT)[0])

    def set_insertion_point_before_next_pgn_tag(self):
        """Set INSERT at point for insertion of empty PGN Tag or Tags.

        Assumed to be called only when inserting a PGN Tag since this item is
        only insert allowed at new INSERT position unless at end of PGN Tags.

        """
        widget = self.score
        if widget.compare(tkinter.INSERT, '>=', START_SCORE_MARK):
            widget.mark_set(tkinter.INSERT, START_SCORE_MARK)
            return
        tr = widget.tag_nextrange(PGN_TAG, tkinter.INSERT)
        if tr:
            widget.mark_set(tkinter.INSERT, tr[0])
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
        self.token_bind_method[tokenprefix](self) # call set bindings method
        self._allowed_chars_in_token = _CHARACTERS_ALLOWED_IN_TOKEN[tokenprefix]
        start, end = tagranges
        lead_trail = _TOKEN_LEAD_TRAIL[tokenprefix]
        insert = self.get_token_insert(tagnames)
        self._lead, self._trail = lead_trail
        self._header_length = self._lead + self._trail
        if self._lead:
            sem = self.score.index(
                ''.join((str(start), ' +', str(self._lead), ' chars')))
        else:
            sem = start
        if self._trail:
            eem = self.score.index(
                ''.join((str(end), ' -', str(self._trail), ' chars')))
        else:
            eem = end
        offset = self.get_token_text_length(start, end) - self._header_length
        if offset:
            if self._lead:
                start = sem
            if self._trail:
                end = eem
        else:
            if self._lead:
                start = self.score.index(''.join((str(sem), ' -1 chars')))
            end = sem
        if not insert:
            insert = eem
        elif self.score.compare(insert, '>', eem):
            insert = eem
        elif self.score.compare(insert, '<', sem):
            insert = sem
        self.score.mark_set(START_EDIT_MARK, sem)
        self.score.mark_gravity(START_EDIT_MARK, 'left')
        self.score.mark_set(END_EDIT_MARK, eem)
        self.score.mark_set(tkinter.INSERT, insert)
        self.set_move_tag(start, end)

    def get_token_range(self, tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        for tn in tagnames:
            if tn.startswith(TOKEN):
                return self.score.tag_nextrange(tn, '1.0')

    def get_token_insert(self, tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        for tn in tagnames:
            if tn.startswith(TOKEN):
                return ''.join((TOKEN_MARK, tn[len(TOKEN):]))

    def get_token_text_length(self, start, end):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        return text_count(self.score, start, end)

    def set_marks_for_editing_comment_eol(self, tagnames, tagranges):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        start, end = tagranges
        if text_count(self.score, start, end) < 2:
            for tn in tagnames:
                if tn.startswith(TOKEN):
                    start = self.score.tag_nextrange(tn, '1.0')[0]
                    break
            else:
                return
        self.score.mark_set(START_EDIT_MARK, start)
        self.score.mark_set(END_EDIT_MARK, end)
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)
        self.set_move_tag(START_EDIT_MARK, END_EDIT_MARK)

    def set_start_score_mark_before_positiontag(self):
        """"""
        self.score.mark_set(
            START_SCORE_MARK,
            self.score.tag_ranges(
                ''.join((POSITION, str(self.position_number))))[0])

    def step_one_variation_select(self, move):
        """Select next variation in choices at current position."""
        # Hack of step_one_variation with setting code removed
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

    def tag_token_for_editing(
        self,
        token_indicies,
        tag_and_mark_names,
        tag_start_to_end=(),
        tag_start_to_sepend=(),
        mark_for_edit=True,
        tag_position=True, # assume superclass caller method has not done tag
        ):
        """Tag token for single-step navigation and game editing.

        token_indicies - the start end and separator end indicies of the token
        tag_and_mark_names - method which returns tag and mark names for token
        tag_start_to_end - state tags appropriate for editable text of token
        tag_start_to_sepend - state tags appropriate for token
        mark_for_edit - the insert index to be used when editing token
        tag_position - True if POSITION tag returned by tag_and_mark_names
        needs to be tagged. (There should be no harm doing this if not needed.)

        tag_and_mark_names is a method name because in some cases the current
        names are needed and in others new names should be generated first:
        pass the appropriate method.

        """
        # may yet do tag_and_mark_names as a flag (only two known cases).
        # tokenmark should remain between start and end, and may be further
        # restricted depending on the state tags.
        start, end, sepend = token_indicies
        positiontag, tokentag, tokenmark = tag_and_mark_names()
        tag_add = self.score.tag_add
        for tag in tag_start_to_end:
            tag_add(tag, start, end)
        for tag in tag_start_to_sepend:
            tag_add(tag, start, sepend)
        tag_add(tokentag, start, sepend)
        if mark_for_edit:
            self.score.mark_set(tokenmark, end)
        if tag_position:
            tag_add(positiontag, start, end)
        return positiontag, token_indicies

    def popup_pgn_tag_menu(self, event=None):
        """Show the popup menu for edit symbol mode in game score.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        self.menupopup_pgntagmode.tk_popup(*self.score.winfo_pointerxy())

    def popup_nonmove_menu(self, event=None):
        """Show popup menu for navigation from non-move items in game score.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        self.menupopup_nonmove.tk_popup(*self.score.winfo_pointerxy())

    def _add_char_to_token(self, char):
        """"""
        if not char:
            return
        if self._allowed_chars_in_token:
            if char not in self._allowed_chars_in_token:
                return
        widget = self.score
        start, end = widget.tag_ranges(self.current)
        non_empty = text_count(widget, start, end) - self._header_length
        insert = str(widget.index(tkinter.INSERT))
        copy_from_insert = widget.compare(start, '==', insert)
        widget.insert(tkinter.INSERT, char)
        if copy_from_insert:
            for tn in widget.tag_names(tkinter.INSERT):
                widget.tag_add(tn, insert)
        else:
            for tn in widget.tag_names(start):
                widget.tag_add(tn, insert)
        # MOVE_TAG must tag something if token has leading and trailing only.
        widget.tag_add(MOVE_TAG, insert)
        if not non_empty:
            widget.tag_remove(
                MOVE_TAG,
                ''.join((
                    str(start),
                    ' +',
                    str(self._lead - 1),
                    'chars')))
        return True

    def get_score_error_escapes_removed(self):
        """Unwrap valid PGN text wrapped by '{Error:  ::{{::}' comments.

        The editor uses Game as the game_class argument to PGN but strict
        adherence to PGN is enforced when unwrapping PGN text: GameStrictPGN
        is the game_class argument to PGN.

        """
        text = self.score.get('1.0', tkinter.END)
        t = _error_wrapper_re.split(text)
        if len(t) == 1:
            return text
        parser = PGN(game_class=GameStrictPGN)
        mtc = next(parser.read_games(text))
        if mtc.state:
            return text
        replacements = 0
        candidates = 0
        tc = t.copy()
        for e in range(1, len(t), 2):
            candidates += 1
            tc[e] = tc[e].rstrip(END_COMMENT).rstrip(
                ).rstrip(ESCAPE_END_COMMENT).lstrip(START_COMMENT).lstrip(
                    ).lstrip(ERROR_START_COMMENT)
            mtc = next(parser.read_games(''.join(tc)))
            if mtc.state:
                tc[e] = t[e]
            else:
                replacements += 1
        if replacements == 0:
            return text
        return ''.join(tc)

    def create_edit_move_context(self, tag):
        return (
            self.generate_fen_for_position(*self.tagpositionmap[tag]).join(
                _EDIT_MOVE_CONTEXT),
            UNKNOWN_RESULT)


class RepertoireEdit(GameEdit):
    
    """Display a repertoire with editing allowed.
    
    """
    tags_displayed_last = REPERTOIRE_TAG_ORDER

    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend with bindings to edit repertoire score."""
        super(RepertoireEdit, self).__init__(gameclass=gameclass, **ka)
        eapgn = EventSpec.export_archive_pgn_from_game
        self.viewmode_database_popup.delete(eapgn[1])
        self.menupopup_nonmove_database.delete(eapgn[1])
        self.menupopup_pgntag_database.delete(eapgn[1])
        for sequence, function in (
            (eapgn, ''),
            ):
            self.score.bind(sequence[0], function)

    def insert_empty_pgn_seven_tag_roster(self):
        """Insert ' [ <fieldname> "<null>" ... ] ' seven tag roster sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        for t in REPERTOIRE_TAG_ORDER:
            self.add_pgntag_to_map(t, '')
        
    def bind_for_viewmode(self):
        """Set keyboard bindings and popup menu for traversing moves."""
        super(RepertoireEdit, self).bind_for_viewmode()
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
