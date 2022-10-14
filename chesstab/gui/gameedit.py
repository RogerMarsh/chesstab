# gameedit.py
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

from solentware_misc.workarounds.workarounds import text_count

from pgn_read.core.constants import (
    TAG_RESULT,
    SEVEN_TAG_ROSTER,
    TAG_FEN,
    TAG_SETUP,
    SETUP_VALUE_FEN_PRESENT,
    FEN_BLACK_BISHOP,
    PGN_BISHOP,
    PGN_CAPTURE_MOVE,
    FEN_WHITE_ACTIVE,
)
from pgn_read.core.parser import PGN
from pgn_read.core.game import GameStrictPGN

from ..core.constants import (
    WHITE_WIN,
    BLACK_WIN,
    DRAW,
    UNKNOWN_RESULT,
    START_RAV,
    END_RAV,
    START_COMMENT,
    ERROR_START_COMMENT,
    ESCAPE_END_COMMENT,
    HIDE_END_COMMENT,
    END_COMMENT,
    END_TAG,
    START_TAG,
)
from ..core.pgn import GameDisplayMoves
from .score import NonTagBind
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
    NAVIGATE_MOVE,  # absence matters if no EDIT_... exists
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
    START_EDIT_MARK,
    END_EDIT_MARK,
    PGN_TAG,
    MOVES_PLAYED_IN_GAME_FONT,
    RAV_END_TAG,
    TERMINATION_TAG,
    SPACE_SEP,
    RAV_START_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    FORCED_NEWLINE_TAG,
    FORCE_NEWLINE_AFTER_FULLMOVES,
    FORCED_INDENT_TAG,
    SELECTION,
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


class GameEditException(Exception):
    pass


class GameEdit(Game):

    """Display a game with editing allowed.

    gameclass is passed to the superclass as the gameclass argument.  It
    defaults to GameDisplayMoves.

    Two PGN objects are available to a GameEdit instance: one provided
    by the creator of the instance used to display the game (from Game
    a base class of GameDisplay); the other inherited directly from PGN
    which is used for editing. This class provides methods to handle single
    moves complementing the game facing methods in PGN.

    Attribute _is_text_editable is True meaning the statement can be edited.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    """

    # get_first_game() does not care whether self.score.get() returns
    # string or unicode but self.set_and_tag_item_text() does a
    # string.translate() so the get_first_game(x) calls must be
    # get_first_game(x.encode()).
    # ( encode() was introduced for compatibility with Python 2.5 but )
    # ( as this app now uses the hide attribute of paned windows from )
    # ( Tk 8.5 which is not available on Python 2.5 maybe convert to  )
    # ( unicode for Python 3.n compatibility and drop encode().       )

    # True means game score can be edited.
    _is_text_editable = True

    # Indicate the most recent set of bindings applied to score attribute.
    # There will be some implied bindings to the board attribute, but board is
    # shared with the analysis.score attribute so this indicator does not
    # imply anything about the board bindings.  Assumed that switching between
    # game and analysis will put the binding right.
    # Values are Tk tag names or members of NonTagBind enumeration.
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend with bindings to edit game score."""
        super().__init__(gameclass=gameclass, **ka)
        self.ravstack = []

        self._allowed_chars_in_token = ""  # or an iterable of characters.
        self.edit_move_context = dict()

        # Define popup menu for comment tokens.
        self.comment_popup = None

        # Define popup menu for PGN tag tokens.
        self.pgn_tag_popup = None

        # Define popup menu for Game Termination token.
        self.game_termination_popup = None

        # Define popup menu for '(' start RAV (recursive annotation variation)
        # tokens.
        self.start_rav_popup = None

        # Define popup menu for ')' end RAV (recursive annotation variation)
        # tokens.
        self.end_rav_popup = None

        # Define popup menu for '$' NAG (numeric annotation glyph) tokens.
        self.nag_popup = None

        # Define popup menu for ';...\n' comment to end of line tokens.
        self.comment_to_end_of_line_popup = None

        # Define popup menu for '\n%...\n' escape whole line tokens.
        self.escape_whole_line_popup = None

        # Define popup menu for '<...>' reserved tokens.
        self.reserved_popup = None

    def add_char_to_token(self, event):
        """ """
        self._add_char_to_token(event.char.translate(_NEWLINE))
        return "break"

    def add_move_char_to_token(self, event):
        """ """
        if self._add_char_to_token(event.char.translate(_FORCECASE)):
            self.process_move()
        return "break"

    def set_primary_activity_bindings(self, switch=True):
        """Delegate to toggle other relevant bindings and toggle bindings for
        inserting moves and traversing all tokens.

        Moves, including RAVs can only be inserted if the game termination
        marker is present.

        """
        super().set_primary_activity_bindings(switch=switch)
        if self.score.tag_ranges(EDIT_RESULT):
            self.set_keypress_binding(
                function=self.insert_rav,
                bindings=(EventSpec.gameedit_insert_rav,),
                switch=switch,
            )
            self.set_event_bindings_score(
                (
                    (
                        EventSpec.gameedit_insert_castle_queenside,
                        self.insert_rav_castle_queenside,
                    ),
                ),
                switch=switch,
            )
        self.set_event_bindings_score(
            self.get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )

    def set_select_variation_bindings(self, switch=True):
        """Switch bindings for selecting a variation on or off."""
        super().set_select_variation_bindings(switch=switch)
        self.set_event_bindings_score(
            self.get_insert_pgn_in_movetext_events(), switch=False
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=False
        )

    # Renamed from 'bind_for_edit_symbol_mode' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Shared by most 'bind_for_*' methods handling non-move tokens.
    def set_edit_symbol_mode_bindings(
        self,
        switch=True,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        popup_top_left=None,
        popup_pointer=None,
    ):
        """Set or unset bindings for editing symbols depending on switch.

        Defaults for include_ooo, include_tags, and include_movetext, are for
        non-move tokens in the movetext area of the PGN game score.

        include_ooo refers to the popup menu option and Ctrl-o option to insert
        O-O-O in the game score when both O-O and O-O-O are legal moves.

        include_tags refers to the popup menu options, and keystrokes, to add
        or delete empty PGN tags in the PGN tag area.

        include_movetext refers to the popup menu options, and keystrokes, to
        add empty non-move constructs in the movetext area.

        popup_top_left is expected to be a function to post a popup menu at
        top left of widget with focus by Shift F10.  Default is no popup which
        causes menubar to activate.

        popup_pointer is expected to be a function to post a popup menu at the
        pointer location by Control F10 or right click.  Default is no popup
        which means Control F10 causes menubar to activate.

        """
        self.set_event_bindings_score(
            self.get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )
        if include_movetext:
            self.set_event_bindings_score(
                self.get_insert_pgn_in_movetext_events(), switch=switch
            )
        if include_tags:
            self.set_event_bindings_score(
                self.get_insert_pgn_in_tags_events(), switch=switch
            )
        self.set_event_bindings_score(
            self.get_set_insert_in_token_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_delete_char_in_token_events(), switch=switch
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.add_char_to_token),),
            switch=switch,
        )
        if include_ooo:
            self.set_event_bindings_score(
                (
                    (
                        EventSpec.gameedit_insert_castle_queenside,
                        self.insert_castle_queenside_command,
                    ),
                ),
                switch=switch,
            )
        self.set_event_bindings_score(
            self.get_button_events(
                buttonpress1=self.go_to_token, buttonpress3=popup_pointer
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_F10_popup_events(popup_top_left, popup_pointer),
            switch=switch,
        )
        # Allowed characters defined in set_token_context() call

    def bind_for_edit_glyph(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_GLYPH
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_nag_menu_at_top_left,
            popup_pointer=self.post_nag_menu,
        )

    def bind_for_edit_game_termination(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_RESULT
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            include_movetext=False,
            popup_top_left=self.post_game_termination_menu_at_top_left,
            popup_pointer=self.post_game_termination_menu,
        )

    def bind_for_edit_pgn_tag_name(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_PGN_TAG_NAME
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            include_tags=True,
            include_movetext=False,
            popup_top_left=self.post_pgn_tag_menu_at_top_left,
            popup_pointer=self.post_pgn_tag_menu,
        )

    def bind_for_edit_pgn_tag_value(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_PGN_TAG_VALUE
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            include_tags=True,
            include_movetext=False,
            popup_top_left=self.post_pgn_tag_menu_at_top_left,
            popup_pointer=self.post_pgn_tag_menu,
        )

    def bind_for_edit_comment(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_COMMENT
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_comment_menu_at_top_left,
            popup_pointer=self.post_comment_menu,
        )

    def bind_for_edit_reserved(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_RESERVED
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_reserved_menu_at_top_left,
            popup_pointer=self.post_reserved_menu,
        )

    def bind_for_edit_comment_eol(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_COMMENT_EOL
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_comment_to_end_of_line_menu_at_top_left,
            popup_pointer=self.post_comment_to_end_of_line_menu,
        )

    def bind_for_edit_escape_eol(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_ESCAPE_EOL
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_escape_whole_line_menu_at_top_left,
            popup_pointer=self.post_escape_whole_line_menu,
        )

    def bind_for_edit_move_error(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_MOVE_ERROR
        self.set_edit_symbol_mode_bindings(switch=switch)

    def bind_for_edit_move(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = EDIT_MOVE
        super().set_primary_activity_bindings(switch=switch)
        self.set_event_bindings_score(
            self.get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_insert_move, self.insert_move),
                (EventSpec.gameedit_edit_move, self.edit_move),
                (
                    EventSpec.gameedit_insert_castle_queenside,
                    self.insert_move_castle_queenside,
                ),
            ),
            switch=switch,
        )

    def bind_for_insert_rav(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = INSERT_RAV
        self.set_primary_activity_bindings(switch=switch)

    def bind_for_move_edited(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = MOVE_EDITED
        super().set_primary_activity_bindings(switch=switch)
        self.set_event_bindings_score(
            self.get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_delete_char_in_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            (
                (
                    EventSpec.gameedit_add_move_char_to_token,
                    self.add_move_char_to_token,
                ),
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_button_events(
                buttonpress1=self.go_to_token, buttonpress3=self.post_move_menu
            ),
            switch=switch,
        )

    # Should self.set_edit_symbol_mode_bindings() be used?
    def bind_for_rav_start(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = RAV_START_TAG
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_start_rav_menu_at_top_left,
            popup_pointer=self.post_start_rav_menu,
        )
        # self.set_event_bindings_score((
        #    (EventSpec.gameedit_add_char_to_token,
        #     self.press_break),
        #    ), switch=switch)
        self.set_keypress_binding(
            function=self.insert_rav_after_rav_start,
            bindings=(EventSpec.gameedit_insert_rav_after_rav_start,),
            switch=switch,
        )
        self.set_keypress_binding(
            function=self.insert_rav_after_rav_start_move_or_rav,
            bindings=(
                EventSpec.gameedit_insert_rav_after_rav_start_move_or_rav,
            ),
            switch=switch,
        )
        self.set_keypress_binding(
            function=self.insert_rav_after_rav_end,
            bindings=(EventSpec.gameedit_insert_rav_after_rav_end,),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )

    # Should self.set_edit_symbol_mode_bindings() be used?
    def bind_for_rav_end(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = RAV_END_TAG
        self.set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self.post_end_rav_menu_at_top_left,
            popup_pointer=self.post_end_rav_menu,
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.press_break),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )

    def bind_for_no_current_token(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.NO_CURRENT_TOKEN
        self.set_event_bindings_score(
            self.get_button_events(
                buttonpress1=self.go_to_token,
                buttonpress3=self.post_comment_menu,
            ),
            switch=switch,
        )

    def bind_for_unrecognised_edit_token(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.DEFAULT_BINDINGS
        self.set_event_bindings_score(
            (
                (EventSpec.alt_buttonpress_1, ""),
                (EventSpec.buttonpress_1, ""),
                (EventSpec.buttonpress_3, self.post_comment_menu),
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.press_break),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigate_score_events(), switch=switch
        )

    def bind_for_initial_state(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def bind_for_no_editable_tags(self, switch=True):
        pass

    def bind_for_current_without_tags(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.CURRENT_NO_TAGS
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_add_move_char_to_token, self.press_break),
                (EventSpec.gameedit_insert_castle_queenside, self.press_break),
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_delete_char_in_move_events(), False
        )

    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = {
        EDIT_GLYPH: bind_for_edit_glyph,
        EDIT_RESULT: bind_for_edit_game_termination,
        EDIT_PGN_TAG_NAME: bind_for_edit_pgn_tag_name,
        EDIT_PGN_TAG_VALUE: bind_for_edit_pgn_tag_value,
        EDIT_COMMENT: bind_for_edit_comment,
        EDIT_RESERVED: bind_for_edit_reserved,
        EDIT_COMMENT_EOL: bind_for_edit_comment_eol,
        EDIT_ESCAPE_EOL: bind_for_edit_escape_eol,
        EDIT_MOVE_ERROR: bind_for_edit_move_error,
        EDIT_MOVE: bind_for_edit_move,
        INSERT_RAV: bind_for_insert_rav,
        MOVE_EDITED: bind_for_move_edited,
        RAV_END_TAG: bind_for_rav_end,
        RAV_START_TAG: bind_for_rav_start,
        NonTagBind.NO_CURRENT_TOKEN: bind_for_no_current_token,
        NonTagBind.DEFAULT_BINDINGS: bind_for_unrecognised_edit_token,
        NonTagBind.INITIAL_BINDINGS: bind_for_initial_state,
        NonTagBind.NO_EDITABLE_TAGS: bind_for_no_editable_tags,
        NonTagBind.CURRENT_NO_TAGS: bind_for_current_without_tags,
        NonTagBind.SELECT_VARIATION: Game.bind_for_select_variation,
    }

    def delete_char_right(self, event):
        """ """
        self.delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
        return "break"

    def delete_char_left(self, event):
        """ """
        self.delete_char_next_to_insert_mark(START_EDIT_MARK, tkinter.INSERT)
        return "break"

    def delete_move_char_right(self, event):
        """ """
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
            self.process_move()
        elif self.is_game_or_rav_valid_without_move():
            self.delete_empty_move()
        return "break"

    def delete_move_char_left(self, event):
        """ """
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(
                START_EDIT_MARK, tkinter.INSERT
            )
            self.process_move()
        elif self.is_game_or_rav_valid_without_move():
            self.delete_empty_move()
        return "break"

    def delete_token_char_right(self, event):
        """ """
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(tkinter.INSERT, END_EDIT_MARK)
        else:
            self.delete_empty_token()
        return "break"

    def delete_token_char_left(self, event):
        """ """
        if text_count(self.score, START_EDIT_MARK, END_EDIT_MARK) > 1:
            self.delete_char_next_to_insert_mark(
                START_EDIT_MARK, tkinter.INSERT
            )
        else:
            self.delete_empty_token()
        return "break"

    # Not sure if this will be needed.
    # Maybe use to handle text edit mode
    def edit_gamescore(self, event):
        """Edit game score on keyboard event."""
        if not self.is_game_in_text_edit_mode():
            return

    def map_game(self):
        """Extend to set insertion cursor at start of moves."""
        super().map_game()
        # Is INSERT_TOKEN_MARK redundant now?  Let's see.
        self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)

    def insert_comment(self, event=None):
        """Insert comment in game score after current."""
        if self.current:
            if not self.is_current_in_movetext():
                return "break"
        return self.show_item(new_item=self.insert_empty_comment())

    def insert_comment_to_eol(self, event=None):
        """Insert comment to eol in game score after current."""
        if self.current:
            if not self.is_current_in_movetext():
                return "break"
        return self.show_item(new_item=self.insert_empty_comment_to_eol())

    def insert_escape_to_eol(self, event=None):
        """Insert escape to eol in game score after current."""
        if self.current:
            if not self.is_current_in_movetext():
                return "break"
        return self.show_item(new_item=self.insert_empty_escape_to_eol())

    def insert_glyph(self, event=None):
        """Insert glyph in game score after current."""
        if self.current:
            if not self.is_current_in_movetext():
                return "break"
        return self.show_item(new_item=self.insert_empty_glyph())

    def insert_pgn_tag(self, event=None):
        """Insert a single empty pgn tag in game score after current."""
        if self.current:
            if self.is_current_in_movetext():
                return "break"
        self.insert_empty_pgn_tag()
        if self.current:
            return self.show_next_pgn_tag_field_name()
        elif self.score.compare(tkinter.INSERT, "<", START_SCORE_MARK):
            self.score.mark_set(
                tkinter.INSERT,
                self.score.index(tkinter.INSERT + " linestart -1 lines"),
            )
            return self.show_next_token()
        else:
            return self.show_prev_pgn_tag_field_name()

    def insert_pgn_seven_tag_roster(self, event=None):
        """Insert an empty pgn seven tag roster in game score after current."""
        if self.current:
            if self.is_current_in_movetext():
                return "break"
        self.insert_empty_pgn_seven_tag_roster()
        if self.current:
            return self.show_next_pgn_tag_field_name()
        elif self.score.compare(tkinter.INSERT, "<", START_SCORE_MARK):
            self.score.mark_set(
                tkinter.INSERT,
                self.score.index(tkinter.INSERT + " linestart -7 lines"),
            )
            return self.show_next_token()
        else:
            return self.show_prev_pgn_tag_field_name()

    def insert_rav(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the move following the current move, and
        before any existing RAVs in that place.

        KeyPress events are bound to insert_rav() when a move is the current
        token, except for the last move in the game or a RAV when these are
        bound to insert_move().  When no moves exist, either incomplete or
        illegal, KeyPress events are bound to insert_rav().

        KeyPress events are bound to insert_move() when the first character
        has been processed.

        """
        if not self.is_at_least_one_move_in_movetext():
            return self.insert_move(event)
        if not event.char:
            return "break"
        if event.char in _MOVECHARS:
            inserted_move = self.insert_empty_rav_after_next_move(
                event.char.translate(_FORCECASE)
            )
            while not self.is_move_start_of_variation(
                inserted_move, self.step_one_variation(self.current)
            ):
                pass
            self.colour_variation(self.current)
            # self.set_current() already called
        return "break"

    def insert_rav_after_rav_start(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the current RAV start marker, '(', and
        before any existing move or RAVs in that place.

        <Alt KeyPress> events are bound to insert_rav_after_rav_start() when
        a RAV start marker is the current token.

        KeyPress events are bound to insert_move() when the first character
        has been processed.

        """
        if not event.char:
            return "break"
        move = self.get_implied_current_move()
        if event.char in _MOVECHARS:
            inserted_move = self.insert_empty_rav_after_rav_start(
                event.char.translate(_FORCECASE)
            )
            while not self.is_move_start_of_variation(
                inserted_move, self.step_one_variation(move)
            ):
                pass
            self.colour_variation(move)
        return "break"

    def insert_rav_after_rav_start_move_or_rav(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the first move, or RAV, after the current
        RAV start marker, '('.

        <Shift KeyPress> events are bound to
        insert_rav_after_rav_start_move_or_rav() when a RAV start marker is
        the current token.

        KeyPress events are bound to insert_move() when the first character
        has been processed.

        """
        if not event.char:
            return "break"
        move = self.get_implied_current_move()
        if event.char in _MOVECHARS:
            inserted_move = self.insert_empty_rav_after_rav_start_move_or_rav(
                event.char.translate(_FORCECASE)
            )
            while not self.is_move_start_of_variation(
                inserted_move, self.step_one_variation(move)
            ):
                pass
            self.colour_variation(move)
        return "break"

    def insert_rav_after_rav_end(self, event):
        """Insert first character of first move in new RAV in game score.

        The RAV is inserted after the RAV end marker, ')', paired with the
        current RAV start marker, '('.

        <KeyPress> events are bound to insert_rav_after_rav_end() when a RAV
        start marker is the current token.

        KeyPress events are bound to insert_move() when the first character
        has been processed.

        """
        if not event.char:
            return "break"
        move = self.get_implied_current_move()
        if event.char in _MOVECHARS:
            inserted_move = self.insert_empty_rav_after_rav_end(
                event.char.translate(_FORCECASE)
            )
            while not self.is_move_start_of_variation(
                inserted_move, self.step_one_variation(move)
            ):
                pass
            self.colour_variation(move)
        return "break"

    def get_implied_current_move(self):
        """Return implied current if self.current refers to a RAV start or
        self.current if not.

        """
        assert self.current
        widget = self.score
        tr = widget.tag_ranges(self.current)
        if widget.get(*tr) == START_RAV:
            move = None
            for n in widget.tag_names(tr[0]):
                if n.startswith(PRIOR_MOVE):
                    for m in widget.tag_names(widget.tag_ranges(n)[0]):
                        if m.startswith(POSITION):
                            move = m
                            break
                    break
        else:
            move = self.current
        return move

    def add_move_to_moves_played_colouring_tag(self, move):
        """Extend. Allow for '(' as surrogate for move when placing RAVs."""
        widget = self.score
        tr = widget.tag_ranges(move)
        if widget.get(*tr) == START_RAV:
            for n in widget.tag_names(tr[0]):
                if n.startswith(PRIOR_MOVE):
                    for m in widget.tag_names(widget.tag_ranges(n)[0]):
                        if m.startswith(POSITION):
                            move = m
                            break
                    break
        super().add_move_to_moves_played_colouring_tag(move)

    def insert_rav_command(self, event=None):
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
        if not self.is_at_least_one_move_in_movetext():
            return self.insert_move_castle_queenside(event)
        if not event.char:
            return "break"
        if not self.current:
            move = self.current
        else:
            move = self.get_implied_current_move()
        inserted_move = self.insert_empty_rav_after_next_move("O-O-O")
        while not self.is_move_start_of_variation(
            inserted_move, self.step_one_variation(move)
        ):
            pass
        self.colour_variation(move)
        self.process_move()
        return "break"

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
                    start = str(tt[-4]) + "+1c"
                    self.score.delete(start, tt[-3])
                    self.score.insert(start, v)
                    ntt = self.score.tag_ranges(TERMINATION_TAG)
                    end = str(ntt[-2]) + "-1c"
                    for t in self.score.tag_names(tt[-4]):
                        self.score.tag_add(t, ntt[-3], end)
        if er:
            self.score.insert(er[0], v)
            ner = self.score.tag_ranges(EDIT_RESULT)
            for tn in self.score.tag_names(ner[0]):
                self.score.tag_add(tn, er[0], ner[0])
            self.score.delete(*ner)
        return "break"

    def insert_result_draw(self, event=None):
        """Set 1/2-1/2 as the game termination sequence and PGN Result Tag."""
        self.insert_result(DRAW)

    def insert_result_event(self, event=None):
        """Insert or edit the game termination sequence and PGN Result Tag."""
        self.insert_result(_TERMINATION_MAP.get(event.keysym))

    def insert_result_loss(self, event=None):
        """Set 0-1 as the game termination sequence and PGN Result Tag."""
        self.insert_result(BLACK_WIN)

    def insert_result_termination(self, event=None):
        """Set * as the game termination sequence and PGN Result Tag."""
        self.insert_result(UNKNOWN_RESULT)

    def insert_result_win(self, event=None):
        """Set 1-0 as the game termination sequence and PGN Result Tag."""
        self.insert_result(WHITE_WIN)

    def insert_reserved(self, event=None):
        """Insert reserved in game score after current."""
        if self.current:
            if not self.is_current_in_movetext():
                return "break"
        return self.show_item(new_item=self.insert_empty_reserved())

    def insert_castle_queenside_command(self):
        """Insert or edit the O-O-O movetext."""
        ria = self.is_at_least_one_move_in_movetext()
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
            self.insert_empty_move_after_currentmove("O-O-O")
            self.show_next_in_line()
            self.process_move()
            return "break"
        inserted_move = self.insert_empty_rav_after_next_move("O-O-O")
        while not self.is_move_start_of_variation(
            inserted_move, self.step_one_variation(self.current)
        ):
            pass
        self.colour_variation(self.current)
        self.process_move()
        return "break"

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
                    self.score.tag_ranges(prior)[0]
                )
            except IndexError:
                current = None
        else:
            current = self.select_prev_move_in_line()
        self.edit_move_context[self.current] = self.create_edit_move_context(
            current
        )
        self.tagpositionmap[self.current] = self.tagpositionmap[current]
        self.set_current()
        self.set_game_board()
        return self.delete_move_char_left(event)

    def insert_move(self, event):
        """Insert characters of new moves in game score.

        KeyPress events are bound to insert_move() when the last move in the
        game or a RAV is the current token.  When no moves exist, either
        incomplete or illegal, KeyPress events are bound to insert_rav().

        KeyPress events are bound to insert_move() when the first character
        has been processed by insert_rav(), or it's variants for the Alt and
        Shift modifiers.

        """
        if not event.char:
            return "break"
        if event.char in _MOVECHARS:
            self.insert_empty_move_after_currentmove(
                event.char.translate(_FORCECASE)
            )
            return self.show_next_in_line()
        return "break"

    def insert_move_castle_queenside(self, event):
        """Insert or edit the O-O-O movetext.

        If intending to type O-O-O when both O-O and O-O-O are possible the
        O-O is accepted before the chance to type the second '-' arrives.
        'Ctrl o' and the menu equivalent provide a positive way of indicating
        the O-O-O move.  A negative way of inserting O-O-O is to type O--O and
        then type the middle 'O'.

        """
        if not event.char:
            return "break"
        self.insert_empty_move_after_currentmove("O-O-O")
        self.show_next_in_line()
        self.process_move()
        return "break"

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
    # The event handler to post pgn_tag_popup menu is renamed post_pgn_tag_menu.
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
                tn = tns.intersection(_EDIT_TAGS)
                if tn:

                    # Hack to deal with PGN Tag Value tagging while these items
                    # are tagged by EDIT_PGN_TAG_VALUE and EDIT_PGN_TAG_NAME
                    tnn = tn.pop()
                    if EDIT_PGN_TAG_VALUE in tn:
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

    def set_insert_first_char_in_token(self, event):
        """ """
        self.set_insert_mark_at_start_of_token()
        return "break"

    def set_insert_last_char_in_token(self, event):
        """ """
        self.set_insert_mark_at_end_of_token()
        return "break"

    def set_insert_next_char_in_token(self, event):
        """ """
        self.set_insert_mark_right_one_char()
        return "break"

    def set_insert_next_line_in_token(self, event):
        """ """
        self.set_insert_mark_down_one_line()
        return "break"

    def set_insert_prev_char_in_token(self, event):
        """ """
        self.set_insert_mark_left_one_char()
        return "break"

    def set_insert_prev_line_in_token(self, event):
        """ """
        self.set_insert_mark_up_one_line()
        return "break"

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

    def show_move_or_item(self, new_item=None):
        """Display new item if not None."""
        if not new_item:
            return "break"
        tr = self.score.tag_ranges(new_item)
        if NAVIGATE_MOVE in self.score.tag_names(tr[0]):
            return self.go_to_move(tr[0])
        return self.show_item(new_item=new_item)

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
            return "break"
        return self.show_move_or_item(
            new_item=self.select_first_token_in_game()
        )

    def show_last_token(self, event=None):
        """Display last token in game score (usually termination, 1-0 etc)."""
        return self.show_move_or_item(
            new_item=self.select_last_token_in_game()
        )

    def show_next_token(self, event=None):
        """Display next token in game score (ignore rav structure of game).

        Return 'break' so Tk selection is not modified or set.  This event is
        fired by Shift Right.

        """
        self.show_move_or_item(new_item=self.select_next_token_in_game())
        return "break"

    def show_prev_token(self, event=None):
        """Display prev token in game score (ignore rav structure of game).

        Return 'break' so Tk selection is not modified or set.  This event is
        fired by Shift Left.

        """
        self.show_move_or_item(new_item=self.select_prev_token_in_game())
        return "break"

    def show_next_rav_start(self, event=None):
        """Display next RAV Start in game score."""
        return self.show_item(new_item=self.select_next_rav_start_in_game())

    def show_prev_rav_start(self, event=None):
        """Display previous RAV Start in game score."""
        return self.show_item(new_item=self.select_prev_rav_start_in_game())

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
        if self.score.compare(tkinter.INSERT, ">", START_SCORE_MARK):
            self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
        else:
            tr = self.score.tag_prevrange(PGN_TAG, tkinter.INSERT)
            if tr:
                self.score.mark_set(tkinter.INSERT, tr[0])
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

    def to_next_pgn_tag(self, event=None):
        """Position insertion cursor before following pgn tag in game score."""
        self.clear_moves_played_in_variation_colouring_tag()
        self.clear_choice_colouring_tag()
        self.clear_variation_colouring_tag()
        if self.score.compare(tkinter.INSERT, ">", START_SCORE_MARK):
            tr = self.score.tag_nextrange(PGN_TAG, "1.0")
        else:
            tr = self.score.tag_nextrange(PGN_TAG, tkinter.INSERT)
        if tr:
            self.score.mark_set(tkinter.INSERT, str(tr[-1]) + "+1c")
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
    def show_first_in_line_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_first_in_line(event)

    # Renamed from 'bind_and_show_first_in_game' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_first_in_game which does same thing.
    def show_first_in_game_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_first_in_game(event)

    # Renamed from 'bind_and_show_last_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_last_in_line which does same thing.
    def show_last_in_line_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_last_in_line(event)

    # Renamed from 'bind_and_show_last_in_game' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_last_in_game which does same thing.
    def show_last_in_game_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_last_in_game(event)

    # Renamed from 'bind_and_show_next_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_next_in_line which does same thing.
    def show_next_in_line_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_next_in_line(event)

    # Renamed from 'bind_and_show_next_in_var' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_next_in_variation which does same thing.
    def show_next_in_variation_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()
        return self.show_next_in_variation(event)

    # Renamed from 'bind_and_show_prev_in_var' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_prev_in_variation which does same thing.
    def show_prev_in_variation_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()

        # self.set_current() already called but return is not via a method
        # which will call self.set_game_board().
        self.set_game_board()
        return "break"

    # Renamed from 'bind_and_show_prev_in_line' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    # Replaces non_move_show_prev_in_line which does same thing.
    def show_prev_in_line_from_non_move_token(self, event=None):
        """ """
        self.set_nearest_move_to_token_as_currentmove()

        # self.set_current() already called but return is not via a method
        # which will call self.set_game_board().
        self.set_game_board()
        return "break"

    # Renamed from 'bind_and_to_prev_pgn_tag' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    def set_edit_bindings_and_to_prev_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at previous PGN tag."""
        return self.to_prev_pgn_tag()

    # Renamed from 'bind_and_to_next_pgn_tag' when 'bind_for_*' methods tied
    # to Tk Text widget tag names were introduced.
    def set_edit_bindings_and_to_next_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at next PGN tag."""
        return self.to_prev_pgn_tag()  # to start of current PGN tag if in one

    # This method may be removed because it is used in only two places, and
    # one of those needs the 'tr' value too.
    def add_move_to_editable_moves(self, variation):
        """Mark last move in variation for editing rather than insert RAV.

        This method should be called when it is known there are no more moves
        in the game or a RAV, which is at end of RAV or game termination.

        """
        widget = self.score
        tr = widget.tag_prevrange(variation, tkinter.END)

        # Is it a game score with no moves?
        if not tr:
            return

        widget.tag_add(EDIT_MOVE, *tr)
        widget.tag_remove(INSERT_RAV, *tr)

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
        widget.tag_add(PGN_TAG, start_tag, str(tkinter.INSERT) + "-1c")
        widget.mark_set(
            START_SCORE_MARK,
            widget.index(widget.tag_prevrange(PGN_TAG, tkinter.END)[-1])
            + "+1c",
        )
        for et, ts in zip(
            (EDIT_PGN_TAG_NAME, EDIT_PGN_TAG_VALUE), tag_symbols
        ):
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

    def add_text_pgntag_or_pgnvalue(self, token, tagset=(), separator=" "):
        """Add PGN Tagname or Tagvalue to game. Return POSITION tagname."""
        start, end, sepend = super().add_text_pgntag_or_pgnvalue(
            token, separator=separator
        )
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        widget = self.score
        for tag in tagset:
            widget.tag_add(tag, start, end)
        widget.mark_set(tokenmark, end)
        for tag in (NAVIGATE_TOKEN,):
            widget.tag_add(tag, start, end)
        self.add_position_tag_to_pgntag_tags(positiontag, start, end)
        return start, end, sepend

    def delete_forced_newlines_adjacent_to_rav_and_termination(self, index):
        """Delete newlines adjacent to RAV markers to fit layout rules.

        This method is called by delete_forced_newlines_adjacent_to_rav which
        is assumed to have set range_ to the final RAV end marker, ')', in a
        RAV which contained RAVs before deletion started.

        """
        widget = self.score
        while True:
            fnl = widget.tag_nextrange(FORCED_NEWLINE_TAG, index)
            if not fnl:
                break
            widget.delete(*fnl)

    def delete_forced_newlines_adjacent_to_rav(self, range_):
        """Delete newlines adjacent to RAV markers to fit layout rules.

        There will be at least one move token before the RAV being deleted,
        and possibly some other tokens, including RAV start and end markers,
        too.

        """
        widget = self.score
        nttpr = widget.tag_prevrange(NAVIGATE_TOKEN, range_[0])
        for n in widget.tag_names(nttpr[0]):
            if n == RAV_START_TAG:
                nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, range_[-1])
                nltnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, range_[-1])
                if nttnr and nltnr and widget.compare(nttnr[0], ">", nltnr[0]):
                    widget.delete(*nltnr)
                break
            if n == RAV_END_TAG:
                nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, range_[-1])
                nltnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, range_[-1])
                if nttnr:
                    while nltnr:
                        nltnnr = widget.tag_nextrange(
                            FORCED_NEWLINE_TAG, nltnr[-1]
                        )
                        if nltnnr and widget.compare(nttnr[0], ">", nltnnr[0]):
                            widget.delete(*nltnr)
                            nltnr = nltnnr
                            continue
                        break
                else:
                    while nltnr:
                        nltnnr = widget.tag_nextrange(
                            FORCED_NEWLINE_TAG, nltnr[-1]
                        )
                        if nltnnr:
                            widget.delete(*nltnr)
                        nltnr = nltnnr
                    break
        else:
            nltnr = widget.tag_nextrange(
                FORCED_NEWLINE_TAG, nttpr[-1], widget.index(tkinter.INSERT)
            )
            while nltnr:
                nltnnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, nltnr[-1])
                widget.delete(nltnr[0], widget.index(tkinter.INSERT))
                nltnr = nltnnr
                continue
            nttpr = widget.tag_prevrange(
                NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
            )
            if nttpr:
                nltpr = widget.tag_prevrange(
                    FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
                )
                while nltpr:
                    nltppr = widget.tag_prevrange(
                        FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
                    )
                    if widget.compare(nttpr[0], "<", nltppr[0]):
                        widget.delete(*nltpr)
                        nltpr = nltppr
                        continue
                    break

        # If the RAV deletion has left a sequence of less than 20 fullmoves,
        # without any non-move tokens interrupting the sequence, delete any
        # forced newlines left over from the deletion.
        nttppr = widget.tag_prevrange(
            NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
        )
        if nttppr:
            for n in widget.tag_names(nttppr[0]):
                if n == NAVIGATE_MOVE:
                    break
            else:
                if widget.tag_nextrange(NAVIGATE_TOKEN, nttppr[-1]):
                    return
                self.delete_forced_newlines_adjacent_to_rav_and_termination(
                    nttppr[0]
                )
                return
        else:
            return
        nttnnr = widget.tag_nextrange(
            NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
        )
        if nttnnr:
            for n in widget.tag_names(nttnnr[0]):
                if n == NAVIGATE_MOVE:
                    break
            else:
                if widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[-1]):
                    return
                self.delete_forced_newlines_adjacent_to_rav_and_termination(
                    widget.tag_prevrange(FORCED_NEWLINE_TAG, nttnnr[0])[0]
                )
                return
        else:
            return
        nltpr = widget.tag_prevrange(
            FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
        )
        if nltpr and widget.compare(nttppr[0], "<", nltpr[0]):
            nttppr = widget.tag_prevrange(NAVIGATE_TOKEN, nltppr[0])
        if not nttppr:
            return
        nltnr = widget.tag_nextrange(
            FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
        )
        if nltnr and widget.compare(nttnnr[0], ">", nltnr[0]):
            nttnnr = widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[0])
        if not nttnnr:
            return
        count = 0
        nttpr = nttppr
        while nttppr:
            for n in widget.tag_names(nttppr[0]):
                if n == FORCED_NEWLINE_TAG:
                    break
                if n == NAVIGATE_MOVE:
                    count += 1
                    break
            else:
                break
            nttppr = widget.tag_prevrange(NAVIGATE_TOKEN, nttppr[0])
        nttnr = nttnnr
        while nttnnr:
            for n in widget.tag_names(nttnnr[0]):
                if n == FORCED_NEWLINE_TAG:
                    break
                if n == NAVIGATE_MOVE:
                    count += 1
                    break
            else:
                break
            nttnnr = widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[-1])
        if count < FORCE_NEWLINE_AFTER_FULLMOVES:
            dfnl = widget.tag_nextrange(
                FORCED_NEWLINE_TAG, nttpr[-1], nttnr[0]
            )
            if dfnl:
                widget.delete(*dfnl)

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
            tr = widget.tag_ranges(NAVIGATE_MOVE)
            pr = fnltpr[-1]
            nr = fnltnr[0]
            for ti in tr:
                if widget.compare(ti, ">", pr) and widget.compare(ti, "<", nr):
                    tri += 1

        # Two tokens per fullmove; two index values per token. So * 4.
        if tri <= FORCE_NEWLINE_AFTER_FULLMOVES * 4:
            widget.delete(*forced_newline)

    def delete_empty_move(self):
        """Delete empty move from PGN movetext and RAV if it is empty too."""
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
                    widget.tag_ranges(prior)[0]
                )
            except IndexError:
                current = None

            # First range in choice is a move in main line relative to RAV.
            # For first move do not highlight main line when no RAVs exist
            # after deletion of this one.
            # At other moves main line does not get highlighted when any RAV
            # is deleted, because there is a move to make current before the
            # move choices.
            if current or len(widget.tag_ranges(choice)) > 4:
                self.step_one_variation_select(current)
                selection = self.get_selection_tag_for_prior(prior)
                sr = widget.tag_nextrange(
                    choice, widget.tag_ranges(selection)[1]
                )
                if sr:
                    widget.tag_add(selection, *sr)
                else:
                    widget.tag_add(
                        selection, *widget.tag_nextrange(choice, "1.0")[:2]
                    )
            delete_rav = True
        else:
            current = self.select_prev_move_in_line()
            delete_rav = False
        move_number_indicator = widget.tag_prevrange(
            MOVETEXT_MOVENUMBER_TAG,
            tr[0],
            widget.tag_ranges(current)[-1] if current else "1.0",
        )
        if delete_rav:
            ravtag = self.get_rav_tag_for_rav_moves(
                self.get_variation_tag_of_index(tr[0])
            )
            # Tkinter.Text.delete does not support multiple ranges at
            # Python 2.7.1 so call delete for each range from highest to
            # lowest.  Perhaps put a hack in workarounds?
            widget.delete(
                *widget.tag_ranges(
                    self.get_token_tag_of_index(
                        widget.tag_nextrange(
                            RAV_END_TAG,
                            widget.tag_prevrange(ravtag, tkinter.END)[0],
                        )[0]
                    )
                )
            )
            widget.delete(tr[0], tr[1])
            if move_number_indicator:
                widget.delete(*move_number_indicator)
            widget.delete(
                *widget.tag_ranges(
                    self.get_token_tag_of_index(
                        widget.tag_nextrange(ravtag, "1.0")[0]
                    )
                )
            )

            # This should be a method for newlines before and after RAV,
            # perhaps called before the two preceding deletes.
            self.delete_forced_newlines_adjacent_to_rav(tr)

        else:
            widget.delete(tr[0], tr[1])
            if move_number_indicator:
                widget.delete(*move_number_indicator)
            self.delete_forced_newline_token_prefix(NAVIGATE_MOVE, tr)
        del self.edit_move_context[self.current]
        del self.tagpositionmap[self.current]
        self.current = current
        if delete_rav:
            ci = widget.tag_nextrange(choice, "1.0")[0]
            if widget.compare(
                ci, "==", widget.tag_prevrange(choice, tkinter.END)[0]
            ):
                widget.tag_remove(
                    ALL_CHOICES, *widget.tag_nextrange(ALL_CHOICES, ci)
                )
                widget.tag_delete(
                    choice, prior, self.get_selection_tag_for_prior(prior)
                )
            self.clear_choice_colouring_tag()
            self.set_current()
            if self.current is not None and widget.tag_ranges(self.current):
                self.apply_colouring_to_variation_back_to_main_line()
        elif self.current is None:
            nttpr = widget.tag_prevrange(
                NAVIGATE_TOKEN, tkinter.END, widget.index(START_SCORE_MARK)
            )
            if nttpr:
                fnltpr = widget.tag_prevrange(
                    FORCED_NEWLINE_TAG,
                    tkinter.END,
                    widget.index(START_SCORE_MARK),
                )
                if fnltpr and widget.compare(fnltpr[0], ">", nttpr[-1]):
                    widget.delete(*fnltpr)
            self.set_current()
        else:
            start, end = widget.tag_ranges(self.current)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(INSERT_RAV, start, end)
            if widget.tag_ranges(LINE_TAG):
                widget.tag_add(LINE_END_TAG, end, end)
            self.set_current()
        self.set_game_board()

    def delete_empty_pgn_tag(self, event=None):
        """Delete empty PGN tag token."""
        widget = self.score
        start = widget.index(tkinter.INSERT + " linestart")
        tr = widget.tag_nextrange(PGN_TAG, start, START_SCORE_MARK)
        if tr:
            if widget.compare(start, "==", tr[0]):
                # Hack. Empty PGN Tag is len('[  "" ]').
                # Assume one PGN Tag per line.
                # Could change this to work like 'forced_newline', but PGN tags
                # are supposed to be preceded by a newline.
                if len(widget.get(*tr)) == 7:
                    widget.delete(*tr)
                    widget.delete(
                        tr[0] + "-1c"
                    )  # the preceding newline if any
                    # INSERT has moved to end of previous line.  Put INSERT at
                    # start of PGN tag after the deleted one.
                    self.to_prev_pgn_tag()
                    self.to_next_pgn_tag()
        return "break"

    def delete_empty_token(self):
        """Delete empty non-move token from PGN movetext."""
        widget = self.score
        if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) > 1:
            return
        tr = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if tr:
            current = self.select_prev_token_in_game()
            if not current:
                current = self.select_next_token_in_game()
            widget.delete(*tr)
            self.delete_forced_newline_token_prefix(NAVIGATE_TOKEN, tr)
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
            if widget.compare(first, "==", tkinter.INSERT):
                widget.delete(tkinter.INSERT)
            else:
                widget.delete(tkinter.INSERT + "-1 chars")
            if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) == 0:
                if (
                    self._lead
                ):  # self.current will have a range. Or test range.
                    widget.tag_add(
                        MOVE_TAG,
                        "".join(
                            (
                                str(widget.tag_ranges(self.current)[0]),
                                " +",
                                str(self._lead - 1),
                                "chars",
                            )
                        ),
                    )

    def get_rav_tag_name(self):
        """Return suffixed RAV_TAG tag name.

        The Score.get_variation_tag_name() is assumed to have been called
        to increment self.variation_number and set the name of the
        corresponding RAV_MOVES tag.

        """
        return "".join((RAV_TAG, str(self.variation_number)))

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
            nttpr = widget.tag_prevrange(NAVIGATE_TOKEN, point[0])
            widget.mark_set(
                tkinter.INSERT, widget.index(point[0]) + "-1 lines lineend"
            )
            if NAVIGATE_MOVE not in widget.tag_names(nttpr[0]):
                self.insert_forced_newline_into_text()
            return widget.index(tkinter.INSERT)
        if not next_move:
            return end_rav[0]
        if widget.compare(next_move[0], ">", end_rav[0]):
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
                if widget.get(*end_rav) == END_RAV:
                    return widget.index(end_rav[1] + "+1char")
                widget.mark_set(tkinter.INSERT, widget.index(end_rav[1]))
                self.insert_forced_newline_into_text()
                return widget.index(tkinter.INSERT)
            end_rav = nr
            token = widget.get(*nr)
            if token == START_RAV:
                depth += 1
            elif token == END_RAV:
                depth -= 1
                if depth < 0:
                    return widget.index(end_rav[1] + "-1char")

    def get_choice_tag_and_range_of_first_move(self):
        """Return choice tag name and range of first char for first move."""
        tr = self.score.tag_nextrange(NAVIGATE_MOVE, "1.0")
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
        return "".join((RAV_TAG, rav_moves[len(RAV_MOVES) :]))

    def get_rav_tag_of_index(self, index):
        """Return Tk tag name if index is in a rav_tag tag"""
        for tn in self.score.tag_names(index):
            if tn.startswith(RAV_TAG):
                return tn
        return None

    def get_token_tag_for_position(self, position):
        """Return Tk tag name for token with same suffix as position."""
        return "".join((TOKEN, position[len(POSITION) :]))

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
                            widget.tag_ranges(prior)[0]
                        )
                    )
                else:
                    return self.get_position_tag_of_index(
                        widget.tag_ranges(prior)[0]
                    )
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
                    self.score.tag_prevrange(NAVIGATE_TOKEN, tr[0])[0]
                )
            )
        else:
            return False

    def go_to_move(self, index):
        """Extend, set keyboard bindings for new pointer location."""
        if super().go_to_move(index):
            return True
        new_current = self.select_item_at_index(index)
        if new_current is None:
            return "break"
        return self.show_new_current(new_current)

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
            p = widget.tag_ranges(EDIT_RESULT)
            if p:
                widget.mark_set(
                    tkinter.INSERT, widget.index(p[0]) + "-1 lines lineend"
                )
                if widget.tag_prevrange(
                    NAVIGATE_TOKEN, p[0], widget.index(START_SCORE_MARK)
                ):
                    self.insert_forced_newline_into_text()
            else:
                widget.mark_set(tkinter.INSERT, tkinter.END)
            vartag = self.get_variation_tag_name()
            self.gamevartag = vartag
        else:
            start_current, end_current = widget.tag_ranges(self.current)
            insert_point = self.get_insertion_point_at_end_of_rav(end_current)
            if not insert_point:
                return
            vartag = self.get_variation_tag_of_index(start_current)
            widget.mark_set(tkinter.INSERT, insert_point)

        self.get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self.get_current_tag_and_mark_names()
        tpm = self.tagpositionmap
        tpm[positiontag] = tpm[self.current]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        if tpmpt[1] == FEN_WHITE_ACTIVE:
            tpr = widget.tag_prevrange(FORCED_NEWLINE_TAG, tkinter.INSERT)
            if not tpr:
                tpr = [widget.index(START_SCORE_MARK)]
            tpr = tpr[0]
            tr = widget.tag_ranges(NAVIGATE_MOVE)
            tri = 0
            for ti in tr:
                if widget.compare(ti, ">=", tkinter.INSERT):
                    break
                if widget.compare(ti, ">", tpr):
                    tri += 1
            if tri >= FORCE_NEWLINE_AFTER_FULLMOVES * 4:
                self.insert_forced_newline_into_text()
            start, end, sepend = self.insert_token_into_text(
                str(tpmpt[5]) + ".", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        for tag in (
            positiontag,
            vartag,
            NAVIGATE_MOVE,
            NAVIGATE_TOKEN,
            MOVE_EDITED,
            FORCED_INDENT_TAG,
        ):
            widget.tag_add(tag, start, end)
        if self.current is not None:
            widget.tag_remove(EDIT_MOVE, start_current, end_current)
            widget.tag_add(INSERT_RAV, start_current, end_current)
        if vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        if widget.tag_ranges(LINE_TAG):
            widget.tag_remove(LINE_END_TAG, end_current, start)
            widget.tag_add(LINE_END_TAG, end, sepend)
            widget.tag_add(LINE_TAG, start, sepend)
        self.previousmovetags[positiontag] = (current, vartag, vartag)
        self.nextmovetags[current] = [positiontag, []]

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
        t = self.add_start_comment("{}", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t[0]

    def insert_empty_comment_to_eol(self):
        """Insert ";<null>\n " sequence."""
        self.set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t = self.add_comment_to_eol(";\n", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t[0]

    def insert_empty_escape_to_eol(self):
        """Insert "\n%<null>\n " sequence.

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
        t = self.add_escape_to_eol("%\n", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t[0]

    def insert_empty_glyph(self):
        """Insert "$<null> " sequence."""
        self.set_insertion_point_before_next_token(between_newlines=False)
        t = self.add_glyph("$", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t[0]

    def insert_empty_pgn_tag(self):
        """Insert ' [ <null> "<null>" ] ' sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        self.add_pgntag_to_map("", "")

    def insert_empty_pgn_seven_tag_roster(self):
        """Insert ' [ <fieldname> "<null>" ... ] ' seven tag roster sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        for t in SEVEN_TAG_ROSTER:
            self.add_pgntag_to_map(t, "")

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
        t = self.add_start_reserved("<>", self.get_position_for_current())
        if self.current is None:
            self.set_start_score_mark_before_positiontag()
        return t[0]

    def insert_empty_rav_after_next_move(self, event_char):
        """Insert "(<event_char>)" after move after current move.

        Both the current move and the move after may already have RAVs which
        are their alternatives.  The insert is before any RAVs which are
        alternatives for the move after current move.

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
                    self.get_rav_moves_of_index(ctr[2])
                )
            )[0]
        else:
            # No existing RAVs for the next move.
            for tn in variation, RAV_END_TAG, EDIT_RESULT:
                tr = widget.tag_nextrange(tn, nextmove[1])
                if tr:
                    point = tr[0]
            else:
                # Can keep going, but both raise exception and issue warning
                # dialogue are better options here.
                point = widget.index(nextmove[1] + "+1char")
        colourvariation = "".join((RAV_SEP, variation))

        # Apply choice tags to next move if not already done, implied by
        # absence of existing RAVs for move.
        if prior is None:
            # no prior move for initial position of game.
            # Seems ok to just set these tags even if already set.
            widget.tag_add(ALL_CHOICES, *nextmove)
            widget.tag_add(choice, *nextmove)
        # Why not just test 'ctr' which is already set?
        elif not ctr:  # widget.tag_nextrange(prior, '1.0'):
            assert bool(ctr) == bool(widget.tag_nextrange(prior, "1.0"))
            # no variations exist immediately after current move so set up
            # variation choice structures.  map_insert_rav cannot do this as
            # it assumes variation structure exists, if at all, for preceding
            # moves only.
            if self.current:
                widget.tag_add(prior, *widget.tag_ranges(self.current))
            widget.tag_add(ALL_CHOICES, *nextmove)
            widget.tag_add(choice, *nextmove)

        widget.mark_set(tkinter.INSERT, point)
        # Existence of choice implies the prior forced newline is in place.
        if not ctr:
            self.insert_forced_newline_into_text()
        start, end, sepend = self.insert_token_into_text("(", SPACE_SEP)

        tpm = self.tagpositionmap
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        vartag = self.get_variation_tag_name()
        ravtag = self.get_rav_tag_name()
        if prior:
            tpm[positiontag] = tpm[self.current]
        else:
            tpm[positiontag] = tpm[None]
        widget.tag_add(tokentag, start, sepend)
        for tag in (
            ravtag,
            positiontag,
            NAVIGATE_TOKEN,
            RAV_START_TAG,
        ):
            widget.tag_add(tag, start, end)
        if prior:
            widget.tag_add(prior, start, end)
        # Insert is surrounded by tagged colourvariation text unlike add at end.
        # This breaks the sequence so rest of inserts in this method do not get
        # tagged by colourvariation as well as ravtag.
        widget.tag_remove(colourvariation, start, sepend)
        try:
            self.previousmovetags[positiontag] = (
                self.previousmovetags[current][0],
                variation,
                variation,
            )
        except KeyError:
            self.previousmovetags[positiontag] = (None, variation, variation)

        newmovetag = self.get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self.get_current_tag_and_mark_names()
        tpm[positiontag] = tpm[self.current]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        start, end, sepend = self.insert_token_into_text(
            str(tpmpt[5]) + ("." if tpmpt[1] == FEN_WHITE_ACTIVE else "..."),
            SPACE_SEP,
        )
        widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        # FORCED_INDENT_TAG is not needed, compared with
        # insert_empty_move_after_currentmove(), because this token can only
        # be first on a line due to word wrap.
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

        if vartag is self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
            LINE_TAG,
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        s, e = start, sepend
        self.previousmovetags[positiontag] = (current, vartag, variation)
        self.nextmovetags[current][1].append(positiontag)

        start, end, sepend = self.insert_token_into_text(")", SPACE_SEP)
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        tpm[positiontag] = tpm[self.nextmovetags[current][0]]
        for tag in (
            ravtag,
            positiontag,
            NAVIGATE_TOKEN,
            RAV_END_TAG,
        ):
            widget.tag_add(tag, start, end)
        if prior:
            widget.tag_add(prior, start, end)
        widget.tag_add(tokentag, start, sepend)
        self.previousmovetags[positiontag] = (current, variation, variation)
        nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, end)
        if nttnr and NAVIGATE_MOVE in widget.tag_names(nttnr[0]):
            self.insert_forced_newline_into_text()

        return newmovetag

    def insert_empty_rav_after_rav_start(self, event_char):
        """Insert "(<event_char>)" before first move or "(..)" in current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        tr = widget.tag_ranges(self.current)
        tn = widget.tag_names(tr[0])
        for n in tn:
            if n.startswith(TOKEN):
                insert_point = widget.tag_ranges(n)[-1]
                break
        return self.insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self.find_choice_prior_move_variation_main_move(tn),
            newline_before_rav=False
        )

    def insert_empty_rav_after_rav_start_move_or_rav(self, event_char):
        """Insert "(<event_char>)" after first move or "(..)" in current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        insert_point = None
        tr = widget.tag_ranges(self.current)
        tn = widget.tag_names(tr[0])
        nmtnr = widget.tag_nextrange(NAVIGATE_MOVE, tr[-1])
        rstnr = widget.tag_nextrange(RAV_START_TAG, tr[-1])
        if rstnr and widget.compare(nmtnr[0], ">", rstnr[0]):
            insert_after = False
            for n in widget.tag_names(rstnr[0]):
                if n.startswith(RAV_TAG):
                    for en in widget.tag_names(widget.tag_ranges(n)[-1]):
                        if en.startswith(TOKEN):
                            insert_point = widget.tag_ranges(en)[-1]
                            break
                    break
        else:
            for n in widget.tag_names(nmtnr[0]):
                if n.startswith(TOKEN):
                    insert_point = widget.tag_ranges(n)[-1]
                    break
            insert_after = widget.tag_nextrange(NAVIGATE_TOKEN, insert_point)
        if insert_after:
            for n in widget.tag_names(insert_after[0]):
                if n.startswith(RAV_END_TAG):
                    insert_after = False
                    break
        return self.insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self.find_choice_prior_move_variation_main_move(tn),
            newline_after_rav=bool(insert_after)
        )

    def insert_empty_rav_after_rav_end(self, event_char):
        """Insert "(<event_char>)" after ")" for current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        tn = widget.tag_names(widget.tag_ranges(self.current)[0])
        insert_point = None
        for n in tn:
            if n.startswith(RAV_TAG):
                for en in widget.tag_names(widget.tag_ranges(n)[-1]):
                    if en.startswith(TOKEN):
                        insert_point = widget.tag_ranges(en)[-1]
                        break
                break
        return self.insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self.find_choice_prior_move_variation_main_move(tn),
            newline_after_rav=False
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
        for n in tag_names:
            if n.startswith(RAV_TAG):
                rsrm = "".join((variation_prefix, n.lstrip(RAV_TAG)))
                for en in widget.tag_names(widget.tag_ranges(rsrm)[0]):
                    if en.startswith(CHOICE):
                        choice = en
                        variation_containing_choice = rsrm
                        search.remove(CHOICE)
                        break
                search_done = True
                if prior_move:
                    break
            elif n.startswith(PRIOR_MOVE):
                prior_move = n
                for en in widget.tag_names(widget.tag_ranges(prior_move)[0]):
                    if en.startswith(POSITION):
                        main_line_move = en
                        break
                if search_done:
                    break
        if prior_move is None:
            for n in widget.tag_names(
                widget.tag_nextrange(NAVIGATE_TOKEN, START_SCORE_MARK)[0]
            ):
                if n.startswith(POSITION):
                    main_line_move = n
                    break
        return choice, prior_move, variation_containing_choice, main_line_move

    def insert_rav_at_insert_point(
        self,
        event_char,
        insert_point,
        choice,
        prior_move,
        variation_containing_choice,
        main_line_move,
        newline_before_rav=True,
        newline_after_rav=True,
    ):
        """Insert RAV at insert_point with event_char as first character.

        event_char is a charcter valid in a move in movetext.
        insert_point is the index at which the RAV is to be inserted.
        choice is the tag which tags the alternative moves, including the
        main line move, at this point.  The index range of event_char is
        added to choice.
        prior_move is the tag which tags the main line move and all the
        start and end RAV markers for the alternative replies to the main
        line move.
        variation_containing_choice is the tag which tags all the moves in
        the line containing the RAV.  It can be a RAV itself.
        main_line_move tags 'm1' in '.. m1 m2 (m3 ..) (m4 ..) ..', a PGN-like
        sequence.
        newline_before_rav indicates whether to insert a newline before RAV.
        newline_after_rav indicates whether to insert a newline after RAV.

        The newline flags are intended to control newlines in sequences of
        start RAV or end RAV markers not interrupted by other tokens.

        It is assumed the choice, prior_move, variation_containing_choice,
        and main_line_move, arguments have been calculated by
        find_choice_prior_move_variation_main_move().

        """

        # If choice is not a tag name there is something wrong: do nothing.
        if not choice:
            return

        widget = self.score

        # Move insert_point over any non-move and non-RAV marker tokens
        # before nearest of next move and RAV marker tokens.
        nttpr = widget.tag_prevrange(
            NAVIGATE_TOKEN,
            self.get_nearest_in_tags_between_point_and_end(
                insert_point,
                (
                    NAVIGATE_MOVE,
                    MOVETEXT_MOVENUMBER_TAG,
                    RAV_START_TAG,
                    RAV_END_TAG,
                    EDIT_RESULT,
                ),
            ),
            insert_point,
        )
        if nttpr:
            for n in widget.tag_names(nttpr[-1]):
                if n.startswith(TOKEN):
                    insert_point = widget.tag_ranges(n)[-1]
                    break
            else:
                insert_point = nttpr[-1]

        widget.mark_set(tkinter.INSERT, insert_point)
        if newline_before_rav:
            self.insert_forced_newline_into_text()
        start, end, sepend = self.insert_token_into_text("(", SPACE_SEP)
        tpm = self.tagpositionmap
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        vartag = self.get_variation_tag_name()
        ravtag = self.get_rav_tag_name()
        tpm[positiontag] = tpm[main_line_move if prior_move else None]
        widget.tag_add(tokentag, start, sepend)
        for tag in (ravtag, positiontag, NAVIGATE_TOKEN, RAV_START_TAG):
            widget.tag_add(tag, start, end)
        if prior_move:
            widget.tag_add(prior_move, start, end)
        # Is colourvariation wrong in insert_empty_rav_after_next_move()?
        # There is no 'rsrmN' tag so colourvariation is not propogated.
        # The colourvariation stuff is missing compared with
        # insert_empty_rav_after_next_move().
        self.previousmovetags[positiontag] = (
            self.previousmovetags[main_line_move][0] if prior_move else None,
            variation_containing_choice,
            variation_containing_choice,
        )
        newmovetag = self.get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self.get_current_tag_and_mark_names()
        tpm[positiontag] = tpm[main_line_move if prior_move else None]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        start, end, sepend = self.insert_token_into_text(
            str(tpmpt[5]) + ("." if tpmpt[1] == FEN_WHITE_ACTIVE else "..."),
            SPACE_SEP,
        )
        widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        # FORCED_INDENT_TAG is not needed, compared with
        # insert_empty_move_after_currentmove(), because this token can only
        # be first on a line due to word wrap.
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

        if vartag is self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
            LINE_TAG,
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        s, e = start, sepend
        self.previousmovetags[positiontag] = (
            main_line_move,
            vartag,
            variation_containing_choice,
        )
        self.nextmovetags[main_line_move][1].append(positiontag)
        start, end, sepend = self.insert_token_into_text(")", SPACE_SEP)
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        tpm[positiontag] = tpm[self.nextmovetags[main_line_move][0]]
        for tag in (
            ravtag,
            self.get_rav_tag_for_rav_moves(variation_containing_choice),
            positiontag,
            NAVIGATE_TOKEN,
            RAV_END_TAG,
        ):
            widget.tag_add(tag, start, end)
        if prior_move:
            widget.tag_add(prior_move, start, end)
        widget.tag_add(tokentag, start, sepend)
        self.previousmovetags[positiontag] = (
            main_line_move,
            variation_containing_choice,
            variation_containing_choice,
        )
        if newline_after_rav:
            self.insert_forced_newline_into_text()

        return newmovetag

    def get_nearest_in_tags_between_point_and_end(self, point, tags):
        """Return nearest index of a tag in tags after point.

        tkinter.END is returned if no ranges are found after point in any of
        the tags.

        """
        widget = self.score
        nearest = tkinter.END
        for tag in tags:
            nr = widget.tag_nextrange(tag, point)
            if nr and widget.compare(nr[0], "<", nearest):
                nearest = nr[0]
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
        """Return True if current is not before start of movetext"""
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

    def get_range_of_prior_move(self, start):
        """Override. Return range of PRIOR_MOVE tag before start.

        The GameEdit class tags '('s with a PRIOR_MOVE tag which can be used
        directly to get the range for the prior move.

        Presence of the PRIOR_MOVE tag on '(' breaks the algorithm used in
        the Score class' version of this method.

        """
        widget = self.score
        for n in widget.tag_names(start):
            if n.startswith(CHOICE):
                return widget.tag_prevrange(
                    self.get_prior_tag_for_choice(n), start
                )
            if n.startswith(PRIOR_MOVE):
                return widget.tag_nextrange(n, START_SCORE_MARK)
        return None

    def get_range_of_main_move_for_rav(self, start):
        """Return range of move for which start index ends a RAV."""
        widget = self.score
        for n in widget.tag_names(start):
            if n.startswith(RAV_MOVES):
                return widget.tag_nextrange(
                    n, widget.tag_nextrange(n, start)[1]
                )
        raise GameEditException("Unable to find position for end RAV")

    # Unwanted tags can be inherited from surrounding characters.
    def map_move_text(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_move_text(token, position),
            self.get_current_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, INSERT_RAV),
            tag_position=False,  # already tagged by superclass method
        )
        self._token_position = self.tagpositionmap[positiontag]
        return token_indicies

    # Unwanted tags can be inherited from surrounding characters.
    def map_start_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing.

        ravtag is placed on a stack so it can be recovered when the
        matching RAV end appears for tagging.  The tag marks two of the
        places where new variations may be inserted.

        """
        token_indicies = super().map_start_rav(token, position)
        ravtag = self.get_rav_tag_name()
        self.ravstack.append(ravtag)
        prior = self.get_prior_tag_for_choice(self._choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            self._token_position = self.tagpositionmap[
                self.get_position_tag_of_index(prior_range[0])
            ]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_START_TAG, prior)
        else:
            self._token_position = self.tagpositionmap[None]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_START_TAG)
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
        """Extend to tag token for single-step navigation and game editing.

        ravtag is recovered from the stack to tag the end of RAV, one
        of the points where new variations can be inserted.

        """
        # last move in rav is editable
        self.add_move_to_editable_moves(self._vartag)
        token_indicies = super().map_end_rav(token, position)
        ravtag = self.ravstack.pop()
        prior = self.get_prior_tag_for_choice(self._choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            self._token_position = self.tagpositionmap[
                self.get_position_tag_of_index(
                    self.get_range_of_main_move_for_rav(prior_range[0])[0]
                )
            ]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_END_TAG, prior)
        else:
            self._token_position = self.tagpositionmap[None]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_END_TAG)
        positiontag, token_indicies = self.tag_token_for_editing(
            token_indicies,
            self.get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_termination(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # last move in game is editable
        self.add_move_to_editable_moves(self._vartag)
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_termination(token),
            self.get_tag_and_mark_names,
            # tag_start_to_end=(EDIT_RESULT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            tag_start_to_end=(EDIT_RESULT,),
        )
        self.tagpositionmap[positiontag] = self._token_position
        return token_indicies

    def _map_start_comment(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            self.insert_token_into_text(token, SPACE_SEP),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_COMMENT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )

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

    def map_start_comment(self, token):
        """Override to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_start_comment(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def _map_comment_to_eol(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            super()._map_comment_to_eol(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(
                EDIT_COMMENT_EOL,
                NAVIGATE_TOKEN,
                NAVIGATE_COMMENT,
            ),
        )

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

    def map_comment_to_eol(self, token):
        """Override to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_comment_to_eol(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def _map_escape_to_eol(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            super()._map_escape_to_eol(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_ESCAPE_EOL, NAVIGATE_TOKEN),
        )

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

    # The EDIT_ESCAPE_EOL entry in _TOKEN_LEAD_TRAIL has been changed from
    # (2, 0) to (1, 0) to fit the add_escape_to_eol() case.  Not sure yet
    # if this breaks the map_escape_to_eol() case, which currently cannot
    # happen because '\n%\n' tokens are not put on database even if present
    # in the PGN movetext.
    def map_escape_to_eol(self, token):
        """Override to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_escape_to_eol(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_integer(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_integer(token, position),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN,),
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_glyph(self, token, newline_prefix):
        """Tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            self.insert_token_into_text(token, SPACE_SEP),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_GLYPH, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )

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

    def map_glyph(self, token):
        """Override to tag token for single-step navigation and game editing."""

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

        positiontag, token_indicies = self._map_glyph(token, before)
        self.tagpositionmap[positiontag] = self._token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_period(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_period(token, position),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN,),
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_start_reserved(self, token, newline_prefix):
        """Tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            self.insert_token_into_text(token, SPACE_SEP),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_RESERVED, NAVIGATE_TOKEN),
        )

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

    def map_start_reserved(self, token):
        """Override to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._map_start_reserved(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
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

    def tokens_exist_between_movetext_start_and_insert_point(self):
        """Return True if tokens exist from movetext start to insert point."""
        return bool(
            self.score.tag_prevrange(
                NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
            )
        )

    def tokens_exist_between_insert_point_and_game_terminator(self):
        """Return True if tokens exist from insert point_to_game_terminator."""
        return bool(self.score.tag_nextrange(NAVIGATE_TOKEN, tkinter.INSERT))

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
            vartag = self.get_variation_tag_of_index(start)
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
            vartag = self.get_variation_tag_of_index(start)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(MOVE_EDITED, start, end)
            widget.insert(widget.index(start) + "+1 char", PGN_BISHOP)
            widget.delete(widget.index(start))
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
            self._allowed_chars_in_token = ""
            return None
        # Not sure the explicit setting is needed.
        self._allowed_chars_in_token = ""
        return None

    def select_first_item_in_game(self, item):
        """Return POSITION tag associated with first item in game"""
        widget = self.score
        tr = widget.tag_nextrange(item, "1.0")
        if not tr:
            return None
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_last_item_in_game(self, item):
        """Return POSITION tag associated with last item in game"""
        widget = self.score
        tr = widget.tag_prevrange(item, tkinter.END)
        if not tr:
            return None
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return None

    def select_next_item_in_game(self, item):
        """Return POSITION tag associated with item after current in game."""
        widget = self.score
        oldtr = widget.tag_ranges(MOVE_TAG)
        if oldtr:
            tr = widget.tag_nextrange(item, oldtr[-1])
        else:
            tr = widget.tag_nextrange(item, tkinter.INSERT)
        if not tr:
            return self.select_first_item_in_game(item)
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return self.select_first_item_in_game(item)

    def select_prev_item_in_game(self, item):
        """Return POSITION tag associated with item before current in game."""
        widget = self.score
        if self.current:
            oldtr = widget.tag_ranges(self.current)
        else:
            oldtr = widget.tag_ranges(MOVE_TAG)
        if oldtr:
            tr = widget.tag_prevrange(item, oldtr[0])
        else:
            tr = widget.tag_prevrange(item, tkinter.END)
        if not tr:
            return self.select_last_item_in_game(item)
        for tn in widget.tag_names(tr[0]):
            if tn.startswith(POSITION):
                return tn
        return self.select_last_item_in_game(item)

    def select_first_comment_in_game(self):
        """Return POSITION tag associated with first comment in game."""
        return self.select_first_item_in_game(NAVIGATE_COMMENT)

    def select_last_comment_in_game(self):
        """Return POSITION tag associated with last comment in game."""
        return self.select_last_item_in_game(NAVIGATE_COMMENT)

    def select_next_comment_in_game(self):
        """Return POSITION tag associated with comment after current in game."""
        return self.select_next_item_in_game(NAVIGATE_COMMENT)

    def select_prev_comment_in_game(self):
        """Return POSITION tag associated with comment before current in game."""
        return self.select_prev_item_in_game(NAVIGATE_COMMENT)

    def select_next_pgn_tag_field_name(self):
        """Return POSITION tag for nearest following PGN Tag field"""
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
                        str(widget.tag_ranges(self.current)[0]) + " linestart"
                    ),
                )
                for tn in widget.tag_names(index[0]):
                    if tn.startswith(POSITION):
                        return tn
            else:
                index = widget.tag_prevrange(
                    NAVIGATE_TOKEN,
                    widget.tag_prevrange(NAVIGATE_TOKEN, START_SCORE_MARK)[0],
                )
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
        """Return POSITION tag associated with first token in game."""
        return self.select_first_item_in_game(NAVIGATE_TOKEN)

    def select_last_token_in_game(self):
        """Return POSITION tag associated with last token in game."""
        return self.select_last_item_in_game(NAVIGATE_TOKEN)

    def select_next_token_in_game(self):
        """Return POSITION tag associated with token after current in game."""
        return self.select_next_item_in_game(NAVIGATE_TOKEN)

    def select_prev_token_in_game(self):
        """Return POSITION tag associated with token before current in game."""
        return self.select_prev_item_in_game(NAVIGATE_TOKEN)

    def select_next_rav_start_in_game(self):
        """Return POSITION tag associated with RAV after current in game."""
        return self.select_next_item_in_game(RAV_START_TAG)

    def select_prev_rav_start_in_game(self):
        """Return POSITION tag associated with RAV before current in game."""
        return self.select_prev_item_in_game(RAV_START_TAG)

    def set_insert_mark_at_end_of_token(self):
        """ """
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)

    def set_insert_mark_at_start_of_token(self):
        """ """
        self.score.mark_set(tkinter.INSERT, START_EDIT_MARK)

    def set_insert_mark_down_one_line(self):
        """ """
        widget = self.score
        if widget.compare(tkinter.INSERT, "<", END_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + " +1 display lines"
            )
            if widget.compare(tkinter.INSERT, ">", END_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, END_EDIT_MARK)

    def set_insert_mark_left_one_char(self):
        """ """
        widget = self.score
        if widget.compare(tkinter.INSERT, ">", START_EDIT_MARK):
            widget.mark_set(tkinter.INSERT, tkinter.INSERT + " -1 chars")

    def set_insert_mark_right_one_char(self):
        """ """
        widget = self.score
        if widget.compare(tkinter.INSERT, "<", END_EDIT_MARK):
            widget.mark_set(tkinter.INSERT, tkinter.INSERT + " +1 chars")

    def set_insert_mark_up_one_line(self):
        """ """
        widget = self.score
        if widget.compare(tkinter.INSERT, ">", START_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + " -1 display lines"
            )
            if widget.compare(tkinter.INSERT, "<", START_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, START_EDIT_MARK)

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
        """INSERT is set before next token and it's move number if any, and
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
        tr = widget.tag_nextrange(NAVIGATE_TOKEN, trc[-1])
        if not tr:
            tr = [
                widget.index(
                    widget.tag_nextrange(EDIT_RESULT, trc[-1])[0]
                    + "-1 lines lineend"
                )
            ]
        trfnl = widget.tag_prevrange(FORCED_NEWLINE_TAG, tr[0], trc[-1])
        if trfnl:
            tr = trfnl
        else:
            trmm = widget.tag_prevrange(
                MOVETEXT_MOVENUMBER_TAG, tr[0], trc[-1]
            )
            if trmm:
                tr = trmm
        widget.mark_set(tkinter.INSERT, tr[0])
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
        if self._most_recent_bindings != tokenprefix:
            self.token_bind_method[tokenprefix](self)
        self._allowed_chars_in_token = _CHARACTERS_ALLOWED_IN_TOKEN[
            tokenprefix
        ]
        start, end = tagranges
        lead_trail = _TOKEN_LEAD_TRAIL[tokenprefix]
        insert = self.get_token_insert(tagnames)
        self._lead, self._trail = lead_trail
        self._header_length = self._lead + self._trail
        if self._lead:
            sem = self.score.index(
                "".join((str(start), " +", str(self._lead), " chars"))
            )
        else:
            sem = start
        if self._trail:
            eem = self.score.index(
                "".join((str(end), " -", str(self._trail), " chars"))
            )
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

    def get_token_range(self, tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        for tn in tagnames:
            if tn.startswith(TOKEN):
                return self.score.tag_nextrange(tn, "1.0")

    def get_token_insert(self, tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        for tn in tagnames:
            if tn.startswith(TOKEN):
                return "".join((TOKEN_MARK, tn[len(TOKEN) :]))

    def get_token_text_length(self, start, end):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        return text_count(self.score, start, end)

    def set_marks_for_editing_comment_eol(self, tagnames, tagranges):
        """Set token editing bound marks from TOKEN<suffix> in tagnames"""
        start, end = tagranges
        if text_count(self.score, start, end) < 2:
            for tn in tagnames:
                if tn.startswith(TOKEN):
                    start = self.score.tag_nextrange(tn, "1.0")[0]
                    break
            else:
                return
        self.score.mark_set(START_EDIT_MARK, start)
        self.score.mark_set(END_EDIT_MARK, end)
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)
        self.set_move_tag(START_EDIT_MARK, END_EDIT_MARK)

    def set_start_score_mark_before_positiontag(self):
        """ """
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
        tag_position=True,  # assume superclass caller method has not done tag
    ):
        """Tag token for single-step navigation and game editing.

        token_indicies - the start end and separator end indicies of the token
        tag_and_mark_names - method which returns tag and mark names for token
        tag_start_to_end - state tags appropriate for editable text of token
        tag_start_to_sepend - state tags appropriate for token
        mark_for_edit - True if tokenmark returned by tag_and_mark_names is
        to be made the insert point for editing the token
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

    def create_popup(self, popup, move_navigation=None):
        assert popup is None
        assert move_navigation is not None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, move_navigation())
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self.populate_export_submenu(export_submenu)
        popup.add_cascade(label="Export", menu=export_submenu)
        database_submenu = self.create_database_submenu(popup)
        if database_submenu:
            popup.add_cascade(label="Database", menu=database_submenu)
        return popup

    # Most popups are same except for binding the popup menu attribute.
    # This does the work for the ones with identical processing.
    def create_non_move_popup(self, popup):
        popup = self.create_popup(
            popup,
            move_navigation=self.get_primary_activity_from_non_move_events,
        )
        self.add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self.add_pgn_insert_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self.create_widget_navigation_submenu_for_popup(popup)
        return popup

    def create_pgn_tag_popup(self):
        popup = self.create_popup(
            self.pgn_tag_popup,
            move_navigation=self.get_primary_activity_from_non_move_events,
        )
        self.add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self.add_pgn_insert_to_submenu_of_popup(
            popup,
            include_tags=True,
            include_movetext=False,
            index=self.export_popup_label,
        )
        self.create_widget_navigation_submenu_for_popup(popup)
        self.pgn_tag_popup = popup
        return popup

    def post_pgn_tag_menu(self, event=None):
        """Post popup menu when a PGN tag is current token."""
        return self.post_menu(
            self.pgn_tag_popup, self.create_pgn_tag_popup, event=event
        )

    def post_pgn_tag_menu_at_top_left(self, event=None):
        """Post popup menu when a PGN tag is current token."""
        return self.post_menu_at_top_left(
            self.pgn_tag_popup, self.create_pgn_tag_popup, event=event
        )

    def create_game_termination_popup(self):
        popup = self.create_popup(
            self.game_termination_popup,
            move_navigation=self.get_primary_activity_from_non_move_events,
        )
        self.add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self.create_widget_navigation_submenu_for_popup(popup)
        self.game_termination_popup = popup
        return popup

    def post_game_termination_menu(self, event=None):
        """Post popup menu when game termination is current token."""
        return self.post_menu(
            self.game_termination_popup,
            self.create_game_termination_popup,
            event=event,
        )

    def post_game_termination_menu_at_top_left(self, event=None):
        """Post popup menu when game termination is current token."""
        return self.post_menu_at_top_left(
            self.game_termination_popup,
            self.create_game_termination_popup,
            event=event,
        )

    def create_comment_popup(self):
        popup = self.create_non_move_popup(self.comment_popup)
        self.comment_popup = popup
        return popup

    def post_comment_menu(self, event=None):
        """Post popup menu when a comment is current token."""
        return self.post_menu(
            self.comment_popup, self.create_comment_popup, event=event
        )

    def post_comment_menu_at_top_left(self, event=None):
        """Post popup menu when a comment is current token."""
        return self.post_menu_at_top_left(
            self.comment_popup, self.create_comment_popup, event=event
        )

    def create_nag_popup(self):
        popup = self.create_non_move_popup(self.nag_popup)
        self.nag_popup = popup
        return popup

    def post_nag_menu(self, event=None):
        """Post popup menu when a NAG is current token."""
        return self.post_menu(
            self.nag_popup, self.create_nag_popup, event=event
        )

    def post_nag_menu_at_top_left(self, event=None):
        """Post popup menu when a NAG is current token."""
        return self.post_menu_at_top_left(
            self.nag_popup, self.create_nag_popup, event=event
        )

    def create_start_rav_popup(self):
        popup = self.create_popup(
            self.start_rav_popup,
            move_navigation=self.get_primary_activity_from_non_move_events,
        )
        self.add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self.add_pgn_insert_to_submenu_of_popup(
            popup, include_rav_start_rav=True, index=self.export_popup_label
        )
        self.create_widget_navigation_submenu_for_popup(popup)
        self.start_rav_popup = popup
        return popup

    def post_start_rav_menu(self, event=None):
        """Post popup menu when a '(', start RAV, is current token."""
        return self.post_menu(
            self.start_rav_popup, self.create_start_rav_popup, event=event
        )

    def post_start_rav_menu_at_top_left(self, event=None):
        """Post popup menu when a '(', start RAV, is current token."""
        return self.post_menu_at_top_left(
            self.start_rav_popup, self.create_start_rav_popup, event=event
        )

    def create_end_rav_popup(self):
        popup = self.create_non_move_popup(self.end_rav_popup)
        self.end_rav_popup = popup
        return popup

    def post_end_rav_menu(self, event=None):
        """Post popup menu when a ')', end RAV, is current token."""
        return self.post_menu(
            self.end_rav_popup, self.create_end_rav_popup, event=event
        )

    def post_end_rav_menu_at_top_left(self, event=None):
        """Post popup menu when a ')', end RAV, is current token."""
        return self.post_menu_at_top_left(
            self.end_rav_popup, self.create_end_rav_popup, event=event
        )

    def create_comment_to_end_of_line_popup(self):
        popup = self.create_non_move_popup(self.comment_to_end_of_line_popup)
        self.comment_to_end_of_line_popup = popup
        return popup

    def post_comment_to_end_of_line_menu(self, event=None):
        """Post popup menu when a ';...\n' comment is current token."""
        return self.post_menu(
            self.comment_to_end_of_line_popup,
            self.create_comment_to_end_of_line_popup,
            event=event,
        )

    def post_comment_to_end_of_line_menu_at_top_left(self, event=None):
        """Post popup menu when a ';...\n' comment is current token."""
        return self.post_menu_at_top_left(
            self.comment_to_end_of_line_popup,
            self.create_comment_to_end_of_line_popup,
            event=event,
        )

    def create_escape_whole_line_popup(self):
        popup = self.create_non_move_popup(self.escape_whole_line_popup)
        self.escape_whole_line_popup = popup
        return popup

    def post_escape_whole_line_menu(self, event=None):
        """Post popup menu when a '\n%...\n' escape is current token."""
        return self.post_menu(
            self.escape_whole_line_popup,
            self.create_escape_whole_line_popup,
            event=event,
        )

    def post_escape_whole_line_menu_at_top_left(self, event=None):
        """Post popup menu when a '\n%...\n' escape is current token."""
        return self.post_menu_at_top_left(
            self.escape_whole_line_popup,
            self.create_escape_whole_line_popup,
            event=event,
        )

    def create_reserved_popup(self):
        popup = self.create_non_move_popup(self.reserved_popup)
        self.reserved_popup = popup
        return popup

    def post_reserved_menu(self, event=None):
        """Post popup menu when a '<...>, reserved, is current token."""
        return self.post_menu(
            self.reserved_popup, self.create_reserved_popup, event=event
        )

    def post_reserved_menu_at_top_left(self, event=None):
        """Post popup menu when a '<...>, reserved, is current token."""
        return self.post_menu_at_top_left(
            self.reserved_popup, self.create_reserved_popup, event=event
        )

    def _add_char_to_token(self, char):
        """ """
        if not char:
            return
        if self._allowed_chars_in_token:
            if char not in self._allowed_chars_in_token:
                return
        widget = self.score
        start, end = widget.tag_ranges(self.current)
        non_empty = text_count(widget, start, end) - self._header_length
        insert = str(widget.index(tkinter.INSERT))
        copy_from_insert = widget.compare(start, "==", insert)
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
                "".join((str(start), " +", str(self._lead - 1), "chars")),
            )
        return True

    def get_score_error_escapes_removed(self):
        """Unwrap valid PGN text wrapped by '{Error:  ::{{::}' comments.

        The editor uses Game as the game_class argument to PGN but strict
        adherence to PGN is enforced when unwrapping PGN text: GameStrictPGN
        is the game_class argument to PGN.

        """
        text = self.score.get("1.0", tkinter.END)
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
            tc[e] = (
                tc[e]
                .rstrip(END_COMMENT)
                .rstrip()
                .rstrip(ESCAPE_END_COMMENT)
                .lstrip(START_COMMENT)
                .lstrip()
                .lstrip(ERROR_START_COMMENT)
                .replace(HIDE_END_COMMENT, END_COMMENT)
            )
            mtc = next(parser.read_games("".join(tc)))
            if mtc.state:
                tc[e] = t[e]
            else:
                replacements += 1
        if replacements == 0:
            return text
        return "".join(tc)

    def create_edit_move_context(self, tag):
        return (
            self.generate_fen_for_position(*self.tagpositionmap[tag]).join(
                _EDIT_MOVE_CONTEXT
            ),
            UNKNOWN_RESULT,
        )

    def populate_navigate_score_submenu(self, submenu):
        self.set_popup_bindings(submenu, self.get_navigate_score_events())

    # O-O-O is available to avoid ambiguity if both O-O and O-O-O are legal
    # when typing moves in.  When move editing is not allowed the O-O-O menu
    # option must be suppressed.
    # The addition of include_tags and include_movetext arguments gets the
    # method close to precipice of too complicated.
    def populate_pgn_submenu(
        self,
        submenu,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        include_rav_start_rav=False,
        include_move_rav=False,
    ):
        assert not (include_rav_start_rav and include_move_rav)
        if include_movetext:
            self.set_popup_bindings(
                submenu, self.get_insert_pgn_in_movetext_events()
            )
        if include_rav_start_rav:
            self.set_popup_bindings(
                submenu, self.get_insert_pgn_rav_in_movetext_events()
            )
        if include_move_rav:
            self.set_popup_bindings(
                submenu, self.get_insert_rav_in_movetext_events()
            )
        if include_tags:
            self.set_popup_bindings(
                submenu, self.get_insert_pgn_in_tags_events()
            )
        if not include_ooo:
            return
        self.set_popup_bindings(
            submenu,
            (
                (
                    EventSpec.gameedit_insert_castle_queenside,
                    self.insert_castle_queenside_command,
                ),
            ),
        )

    # This method should be in GameEdit, the nearest subclass of Score which
    # supports editing games.
    # Subclasses which need non-move PGN navigation should call this method.
    # Intended for editors.
    def add_pgn_insert_to_submenu_of_popup(
        self,
        popup,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        include_rav_start_rav=False,
        include_move_rav=False,
        index=tkinter.END,
    ):
        """Add non-move PGN insertion to a submenu of popup.

        Subclasses must provide the methods named.

        Moves, including RAVs, are inserted at current by starting to type.

        Other items, such as comments, are inserted with the options on this
        menu.

        """
        pgn_submenu = tkinter.Menu(master=popup, tearoff=False)
        self.populate_pgn_submenu(
            pgn_submenu,
            include_ooo=include_ooo,
            include_tags=include_tags,
            include_movetext=include_movetext,
            include_rav_start_rav=include_rav_start_rav,
            include_move_rav=include_move_rav,
        )
        popup.insert_cascade(index=index, label="PGN", menu=pgn_submenu)

    def get_navigate_score_events(self):
        """Return tuple of event definitions for navigating PGN.

        Going to next and previous token, comment, or PGN tag; and first and
        last token and comment is supported.

        See Score.get_primary_activity_events for next and previous moves.

        """
        return (
            (
                EventSpec.gameedit_show_previous_rav_start,
                self.show_prev_rav_start,
            ),
            (EventSpec.gameedit_show_next_rav_start, self.show_next_rav_start),
            (EventSpec.gameedit_show_previous_token, self.show_prev_token),
            (EventSpec.gameedit_show_next_token, self.show_next_token),
            (EventSpec.gameedit_show_first_token, self.show_first_token),
            (EventSpec.gameedit_show_last_token, self.show_last_token),
            (EventSpec.gameedit_show_first_comment, self.show_first_comment),
            (EventSpec.gameedit_show_last_comment, self.show_last_comment),
            (EventSpec.gameedit_show_previous_comment, self.show_prev_comment),
            (EventSpec.gameedit_show_next_comment, self.show_next_comment),
            (EventSpec.gameedit_to_previous_pgn_tag, self.to_prev_pgn_tag),
            (EventSpec.gameedit_to_next_pgn_tag, self.to_next_pgn_tag),
        )

    def get_insert_pgn_in_movetext_events(self):
        """Return tuple of event definitions for inserting PGN constructs.

        Inserting RAVs and adding of moves at end of game is allowed only when
        the current token is a move or a RAV start token.  The relevant
        characters are defined elsewhere, including the O-O-O shortcut
        convenient when both O-O-O and O-O are legal moves.

        The bindings for inserting RAVs are defined in other methods.

        """
        return (
            (EventSpec.gameedit_insert_comment, self.insert_comment),
            (EventSpec.gameedit_insert_reserved, self.insert_reserved),
            (
                EventSpec.gameedit_insert_comment_to_eol,
                self.insert_comment_to_eol,
            ),
            (
                EventSpec.gameedit_insert_escape_to_eol,
                self.insert_escape_to_eol,
            ),
            (EventSpec.gameedit_insert_glyph, self.insert_glyph),
            (EventSpec.gameedit_insert_white_win, self.insert_result_win),
            (EventSpec.gameedit_insert_draw, self.insert_result_draw),
            (EventSpec.gameedit_insert_black_win, self.insert_result_loss),
            (
                EventSpec.gameedit_insert_other_result,
                self.insert_result_termination,
            ),
        )

    # Use in creating popup menus only, where the entries exist to
    # advertise the options.
    def get_insert_pgn_rav_in_movetext_events(self):
        return (
            (
                EventSpec.gameedit_insert_rav_after_rav_end,
                self.insert_rav_command,
            ),
            (
                EventSpec.gameedit_insert_rav_after_rav_start_move_or_rav,
                self.insert_rav_command,
            ),
            (
                EventSpec.gameedit_insert_rav_after_rav_start,
                self.insert_rav_command,
            ),
        )

    # Use in creating popup menus only, where the entries exist to
    # advertise the options.
    def get_insert_rav_in_movetext_events(self):
        return ((EventSpec.gameedit_insert_rav, self.insert_rav_command),)

    def get_insert_pgn_in_tags_events(self):
        """Return tuple of event definitions for inserting PGN constructs.

        Inserting and deleting PGN tags is allowed only when the current token
        is a PGN tag.

        """
        return (
            (EventSpec.gameedit_insert_pgn_tag, self.insert_pgn_tag),
            (
                EventSpec.gameedit_insert_pgn_seven_tag_roster,
                self.insert_pgn_seven_tag_roster,
            ),
            (
                EventSpec.gameedit_delete_empty_pgn_tag,
                self.delete_empty_pgn_tag,
            ),
        )

    def get_set_insert_in_token_events(self):
        return (
            (
                EventSpec.gameedit_set_insert_previous_line_in_token,
                self.set_insert_prev_line_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_previous_char_in_token,
                self.set_insert_prev_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_next_char_in_token,
                self.set_insert_next_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_next_line_in_token,
                self.set_insert_next_line_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_first_char_in_token,
                self.set_insert_first_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_last_char_in_token,
                self.set_insert_last_char_in_token,
            ),
        )

    def get_delete_char_in_token_events(self):
        return (
            (
                EventSpec.gameedit_delete_token_char_left,
                self.delete_token_char_left,
            ),
            (
                EventSpec.gameedit_delete_token_char_right,
                self.delete_token_char_right,
            ),
            (EventSpec.gameedit_delete_char_left, self.delete_char_left),
            (EventSpec.gameedit_delete_char_right, self.delete_char_right),
        )

    def get_delete_char_in_move_events(self):
        return (
            (
                EventSpec.gameedit_delete_move_char_left_shift,
                self.delete_move_char_left,
            ),
            (
                EventSpec.gameedit_delete_move_char_right_shift,
                self.delete_move_char_right,
            ),
            (
                EventSpec.gameedit_delete_move_char_left,
                self.delete_move_char_left,
            ),
            (
                EventSpec.gameedit_delete_move_char_right,
                self.delete_move_char_right,
            ),
        )

    def get_primary_activity_from_non_move_events(self):
        return (
            (
                EventSpec.gameedit_non_move_show_previous_in_variation,
                self.show_prev_in_variation_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_previous_in_line,
                self.show_prev_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_next_in_line,
                self.show_next_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_next_in_variation,
                self.show_next_in_variation_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_first_in_line,
                self.show_first_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_last_in_line,
                self.show_last_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_first_in_game,
                self.show_first_in_game_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_last_in_game,
                self.show_last_in_game_from_non_move_token,
            ),
        )
