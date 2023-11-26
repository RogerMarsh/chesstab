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
    SEVEN_TAG_ROSTER,
    FEN_BLACK_BISHOP,
    PGN_BISHOP,
    PGN_CAPTURE_MOVE,
    TAG_RESULT,
    TAG_FEN,
    TAG_SETUP,
    SETUP_VALUE_FEN_PRESENT,
    FEN_WHITE_ACTIVE,
)
from pgn_read.core.parser import PGN
from pgn_read.core.game import GameStrictPGN

from ..core.constants import (
    WHITE_WIN,
    BLACK_WIN,
    DRAW,
    START_RAV,
    START_COMMENT,
    ERROR_START_COMMENT,
    ESCAPE_END_COMMENT,
    HIDE_END_COMMENT,
    END_COMMENT,
    UNKNOWN_RESULT,
    END_RAV,
    END_TAG,
    START_TAG,
)
from ..core.pgn import GameDisplayMoves
from .game import Game
from .score import NonTagBind
from ._lead_trail import _LeadTrail
from .eventspec import EventSpec
from . import constants
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
    ALL_CHOICES,
    LINE_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    TOKEN_MARK,
    NAVIGATE_COMMENT,
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


class GameEditException(Exception):
    """Exception class for gameedit module."""


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

    # Indicate number of leading and trailing spaces for a token.
    _lead_trail = None

    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend with bindings to edit game score."""
        super().__init__(gameclass=gameclass, **ka)
        self.ravstack = []

        self._allowed_chars_in_token = ""  # or an iterable of characters.
        self.edit_move_context = {}

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

        # Prevent drag relocation of insertion cursor, including scrolling
        # after pointer leaves widget at top or bottom.  This avoids some
        # exceptions when inserting or editing moves.
        # Prevent drag stroking out a selection with consequential visible
        # effect on Windows.
        self.score.bind("<Button1-Motion>", self._suppress_class_binding)
        self.score.bind("<Button1-Leave>", self._suppress_class_binding)

    # These methods define event bindings.

    def _suppress_class_binding(self, event):
        """Return 'break'."""
        del event
        return "break"

    def _set_primary_activity_bindings(self, switch=True):
        """Delegate then set bindings for primary activity.

        The primary activity is inserting moves and traversing all tokens.

        Moves, including RAVs can only be inserted if the game termination
        marker is present.

        """
        super()._set_primary_activity_bindings(switch=switch)
        if self.score.tag_ranges(constants.EDIT_RESULT):
            self._set_keypress_binding(
                function=self._insert_rav,
                bindings=(EventSpec.gameedit_insert_rav,),
                switch=switch,
            )
            function = self._insert_rav_castle_queenside  # Line count.
            self.set_event_bindings_score(
                ((EventSpec.gameedit_insert_castle_queenside, function),),
                switch=switch,
            )
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    def _set_select_variation_bindings(self, switch=True):
        """Switch bindings for selecting a variation on or off."""
        super()._set_select_variation_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=False
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=False
        )

    def _set_edit_symbol_mode_bindings(
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
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )
        if include_movetext:
            self.set_event_bindings_score(
                self._get_insert_pgn_in_movetext_events(), switch=switch
            )
        if include_tags:
            self.set_event_bindings_score(
                self._get_insert_pgn_in_tags_events(), switch=switch
            )
        self.set_event_bindings_score(
            self._get_set_insert_in_token_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_delete_char_in_token_events(), switch=switch
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self._add_char_to_token),),
            switch=switch,
        )
        if include_ooo:
            function = self._insert_castle_queenside_command  # Line count.
            self.set_event_bindings_score(
                ((EventSpec.gameedit_insert_castle_queenside, function),),
                switch=switch,
            )

        # "<Control-o>" may insert a newline at the wrong place, breaking
        # things if typing newline is inhibited.
        if not include_ooo or not switch:
            self.score.bind(
                EventSpec.gameedit_insert_castle_queenside[0],
                self._suppress_class_binding,
            )

        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self._go_to_token, buttonpress3=popup_pointer
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_f10_popup_events(popup_top_left, popup_pointer),
            switch=switch,
        )
        # Allowed characters defined in _set_token_context() call

    def _bind_for_edit_glyph(self, switch=True):
        """Set bindings for EDIT_GLYPH state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_GLYPH
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_nag_menu_at_top_left,
            popup_pointer=self._post_nag_menu,
        )

    def _bind_for_edit_game_termination(self, switch=True):
        """Set bindings for EDIT_RESULT state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_RESULT
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            include_movetext=False,
            popup_top_left=self._post_game_termination_menu_at_top_left,
            popup_pointer=self._post_game_termination_menu,
        )

    def _bind_for_edit_pgn_tag_name(self, switch=True):
        """Set bindings for EDIT_PGN_TAG_NAME state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_PGN_TAG_NAME
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            include_tags=True,
            include_movetext=False,
            popup_top_left=self._post_pgn_tag_menu_at_top_left,
            popup_pointer=self._post_pgn_tag_menu,
        )

    def _bind_for_edit_pgn_tag_value(self, switch=True):
        """Set bindings for EDIT_PGN_TAG_VALUE state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_PGN_TAG_VALUE
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            include_tags=True,
            include_movetext=False,
            popup_top_left=self._post_pgn_tag_menu_at_top_left,
            popup_pointer=self._post_pgn_tag_menu,
        )

    def _bind_for_edit_comment(self, switch=True):
        """Set bindings for EDIT_COMMENT state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_COMMENT
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_comment_menu_at_top_left,
            popup_pointer=self._post_comment_menu,
        )

    def _bind_for_edit_reserved(self, switch=True):
        """Set bindings for EDIT_RESERVED state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_RESERVED
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_reserved_menu_at_top_left,
            popup_pointer=self._post_reserved_menu,
        )

    def _bind_for_edit_comment_eol(self, switch=True):
        """Set bindings for EDIT_COMMENT_EOL state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_COMMENT_EOL
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_comment_to_end_of_line_menu_at_top_left,
            popup_pointer=self._post_comment_to_end_of_line_menu,
        )

    def _bind_for_edit_escape_eol(self, switch=True):
        """Set bindings for EDIT_ESCAPE_EOL state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_ESCAPE_EOL
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_escape_whole_line_menu_at_top_left,
            popup_pointer=self._post_escape_whole_line_menu,
        )

    def _bind_for_edit_move_error(self, switch=True):
        """Set bindings for EDIT_MOVE_ERROR state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_MOVE_ERROR
        self._set_edit_symbol_mode_bindings(switch=switch)

    def _bind_for_edit_move(self, switch=True):
        """Set bindings for EDIT_MOVE state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_MOVE
        super()._set_primary_activity_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )
        function = self._insert_move_castle_queenside  # Line count.
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_insert_move, self._insert_move),
                (EventSpec.gameedit_edit_move, self._edit_move),
                (EventSpec.gameedit_insert_castle_queenside, function),
            ),
            switch=switch,
        )

    def _bind_for_insert_rav(self, switch=True):
        """Set bindings for INSERT_RAV state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.INSERT_RAV
        self._set_primary_activity_bindings(switch=switch)

    def _bind_for_move_edited(self, switch=True):
        """Set bindings for MOVE_EDITED state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.MOVE_EDITED
        super()._set_primary_activity_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_delete_char_in_move_events(), switch=switch
        )
        function = self._add_move_char_to_token  # Line count.
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_move_char_to_token, function),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self._go_to_token,
                buttonpress3=self._post_move_menu,
            ),
            switch=switch,
        )

    # Should self._set_edit_symbol_mode_bindings() be used?
    def _bind_for_rav_start(self, switch=True):
        """Set bindings for RAV_START_TAG state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.RAV_START_TAG
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_start_rav_menu_at_top_left,
            popup_pointer=self._post_start_rav_menu,
        )
        # self.set_event_bindings_score((
        #    (EventSpec.gameedit_add_char_to_token,
        #     self.press_break),
        #    ), switch=switch)
        self._set_keypress_binding(
            function=self._insert_rav_after_rav_start,
            bindings=(EventSpec.gameedit_insert_rav_after_rav_start,),
            switch=switch,
        )
        self._set_keypress_binding(
            function=self._insert_rav_after_rav_start_move_or_rav,
            bindings=(
                EventSpec.gameedit_insert_rav_after_rav_start_move_or_rav,
            ),
            switch=switch,
        )
        self._set_keypress_binding(
            function=self._insert_rav_after_rav_end,
            bindings=(EventSpec.gameedit_insert_rav_after_rav_end,),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    # Should self._set_edit_symbol_mode_bindings() be used?
    def _bind_for_rav_end(self, switch=True):
        """Set bindings for RAV_END_TAG state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.RAV_END_TAG
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_end_rav_menu_at_top_left,
            popup_pointer=self._post_end_rav_menu,
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.press_break),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    def _bind_for_no_current_token(self, switch=True):
        """Set bindings for NO_CURRENT_TOKEN state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.NO_CURRENT_TOKEN
        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self._go_to_token,
                buttonpress3=self._post_comment_menu,
            ),
            switch=switch,
        )

    def _bind_for_unrecognised_edit_token(self, switch=True):
        """Set bindings for DEFAULT_BINDINGS state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.DEFAULT_BINDINGS
        self.set_event_bindings_score(
            (
                (EventSpec.alt_buttonpress_1, ""),
                (EventSpec.buttonpress_1, ""),
                (EventSpec.buttonpress_3, self._post_comment_menu),
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.press_break),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    def bind_for_initial_state(self, switch=True):
        """Set bindings for INITIAL_BINDINGS state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def _bind_for_no_editable_tags(self, switch=True):
        """Do nothing.

        Set bindings for NO_EDITABLE_TAGS state.
        """

    def _bind_for_current_without_tags(self, switch=True):
        """Set bindings for CURRENT_NO_TAGS state."""
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
            self._get_delete_char_in_move_events(), False
        )

    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = {
        constants.EDIT_GLYPH: _bind_for_edit_glyph,
        constants.EDIT_RESULT: _bind_for_edit_game_termination,
        constants.EDIT_PGN_TAG_NAME: _bind_for_edit_pgn_tag_name,
        constants.EDIT_PGN_TAG_VALUE: _bind_for_edit_pgn_tag_value,
        constants.EDIT_COMMENT: _bind_for_edit_comment,
        constants.EDIT_RESERVED: _bind_for_edit_reserved,
        constants.EDIT_COMMENT_EOL: _bind_for_edit_comment_eol,
        constants.EDIT_ESCAPE_EOL: _bind_for_edit_escape_eol,
        constants.EDIT_MOVE_ERROR: _bind_for_edit_move_error,
        constants.EDIT_MOVE: _bind_for_edit_move,
        constants.INSERT_RAV: _bind_for_insert_rav,
        constants.MOVE_EDITED: _bind_for_move_edited,
        constants.RAV_END_TAG: _bind_for_rav_end,
        constants.RAV_START_TAG: _bind_for_rav_start,
        NonTagBind.NO_CURRENT_TOKEN: _bind_for_no_current_token,
        NonTagBind.DEFAULT_BINDINGS: _bind_for_unrecognised_edit_token,
        NonTagBind.INITIAL_BINDINGS: bind_for_initial_state,
        NonTagBind.NO_EDITABLE_TAGS: _bind_for_no_editable_tags,
        NonTagBind.CURRENT_NO_TAGS: _bind_for_current_without_tags,
        NonTagBind.SELECT_VARIATION: Game.bind_for_select_variation,
    }

    def _set_edit_bindings_and_to_prev_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at previous PGN tag."""
        del event
        return self._to_prev_pgn_tag()

    def _set_edit_bindings_and_to_next_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at next PGN tag."""
        del event
        return self._to_prev_pgn_tag()  # to start of PGN tag if in one.

    def _create_popup(self, popup, move_navigation=None):
        """Create and return popup menu with optional move navigation.

        This method is called by all the create_*_popup methods.

        """
        assert popup is None
        assert move_navigation is not None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self._set_popup_bindings(popup, move_navigation())
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_export_submenu(export_submenu)
        popup.add_cascade(label="Export", menu=export_submenu)
        # pylint message assignment-from-none is false positive.
        # However it is sensible to do an isinstance test.
        database_submenu = self._create_database_submenu(popup)
        if isinstance(database_submenu, tkinter.Menu):
            popup.add_cascade(label="Database", menu=database_submenu)
        return popup

    # Most popups are same except for binding the popup menu attribute.
    # This does the work for the ones with identical processing.
    def _create_non_move_popup(self, popup):
        """Create and return popup menu for PGN non-move tokens.

        This method is called by the create_*_popup methods for each
        non-move token.

        """
        popup = self._create_popup(
            popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        return popup

    def _create_pgn_tag_popup(self):
        """Create and return popup menu for PGN Tag token."""
        popup = self._create_popup(
            self.pgn_tag_popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup,
            include_tags=True,
            include_movetext=False,
            index=self.export_popup_label,
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        self.pgn_tag_popup = popup
        return popup

    def _post_pgn_tag_menu(self, event=None):
        """Post popup menu when a PGN tag is current token."""
        return self._post_menu(
            self.pgn_tag_popup, self._create_pgn_tag_popup, event=event
        )

    def _post_pgn_tag_menu_at_top_left(self, event=None):
        """Post popup menu when a PGN tag is current token."""
        return self.post_menu_at_top_left(
            self.pgn_tag_popup, self._create_pgn_tag_popup, event=event
        )

    def _create_game_termination_popup(self):
        """Create and return popup menu for PGN game termination token."""
        popup = self._create_popup(
            self.game_termination_popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        self.game_termination_popup = popup
        return popup

    def _post_game_termination_menu(self, event=None):
        """Post popup menu when game termination is current token."""
        return self._post_menu(
            self.game_termination_popup,
            self._create_game_termination_popup,
            event=event,
        )

    def _post_game_termination_menu_at_top_left(self, event=None):
        """Post popup menu when game termination is current token."""
        return self.post_menu_at_top_left(
            self.game_termination_popup,
            self._create_game_termination_popup,
            event=event,
        )

    def _create_comment_popup(self):
        """Create and return popup menu for PGN comment, {...}, token."""
        popup = self._create_non_move_popup(self.comment_popup)
        self.comment_popup = popup
        return popup

    def _post_comment_menu(self, event=None):
        """Post popup menu when a comment is current token."""
        return self._post_menu(
            self.comment_popup, self._create_comment_popup, event=event
        )

    def _post_comment_menu_at_top_left(self, event=None):
        """Post popup menu when a comment is current token."""
        return self.post_menu_at_top_left(
            self.comment_popup, self._create_comment_popup, event=event
        )

    def _create_nag_popup(self):
        """Create and return popup menu for PGN numeric annotation glyph."""
        popup = self._create_non_move_popup(self.nag_popup)
        self.nag_popup = popup
        return popup

    def _post_nag_menu(self, event=None):
        """Post popup menu when a NAG is current token."""
        return self._post_menu(
            self.nag_popup, self._create_nag_popup, event=event
        )

    def _post_nag_menu_at_top_left(self, event=None):
        """Post popup menu when a NAG is current token."""
        return self.post_menu_at_top_left(
            self.nag_popup, self._create_nag_popup, event=event
        )

    def _create_start_rav_popup(self):
        """Create and return popup menu for PGN start RAV token."""
        popup = self._create_popup(
            self.start_rav_popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup, include_rav_start_rav=True, index=self.export_popup_label
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        self.start_rav_popup = popup
        return popup

    def _post_start_rav_menu(self, event=None):
        """Post popup menu when a '(', start RAV, is current token."""
        return self._post_menu(
            self.start_rav_popup, self._create_start_rav_popup, event=event
        )

    def _post_start_rav_menu_at_top_left(self, event=None):
        """Post popup menu when a '(', start RAV, is current token."""
        return self.post_menu_at_top_left(
            self.start_rav_popup, self._create_start_rav_popup, event=event
        )

    def _create_end_rav_popup(self):
        """Create and return popup menu for PGN end RAV token."""
        popup = self._create_non_move_popup(self.end_rav_popup)
        self.end_rav_popup = popup
        return popup

    def _post_end_rav_menu(self, event=None):
        """Post popup menu when a ')', end RAV, is current token."""
        return self._post_menu(
            self.end_rav_popup, self._create_end_rav_popup, event=event
        )

    def _post_end_rav_menu_at_top_left(self, event=None):
        """Post popup menu when a ')', end RAV, is current token."""
        return self.post_menu_at_top_left(
            self.end_rav_popup, self._create_end_rav_popup, event=event
        )

    def _create_comment_to_end_of_line_popup(self):
        """Create and return popup menu for PGN comment to end line token."""
        popup = self._create_non_move_popup(self.comment_to_end_of_line_popup)
        self.comment_to_end_of_line_popup = popup
        return popup

    def _post_comment_to_end_of_line_menu(self, event=None):
        r"""Post popup menu when a ';...\n' comment is current token."""
        return self._post_menu(
            self.comment_to_end_of_line_popup,
            self._create_comment_to_end_of_line_popup,
            event=event,
        )

    def _post_comment_to_end_of_line_menu_at_top_left(self, event=None):
        r"""Post popup menu when a ';...\n' comment is current token."""
        return self.post_menu_at_top_left(
            self.comment_to_end_of_line_popup,
            self._create_comment_to_end_of_line_popup,
            event=event,
        )

    def _create_escape_whole_line_popup(self):
        """Create and return popup menu for PGN escaped line token."""
        popup = self._create_non_move_popup(self.escape_whole_line_popup)
        self.escape_whole_line_popup = popup
        return popup

    def _post_escape_whole_line_menu(self, event=None):
        r"""Post popup menu when a '\n%...\n' escape is current token."""
        return self._post_menu(
            self.escape_whole_line_popup,
            self._create_escape_whole_line_popup,
            event=event,
        )

    def _post_escape_whole_line_menu_at_top_left(self, event=None):
        r"""Post popup menu when a '\n%...\n' escape is current token."""
        return self.post_menu_at_top_left(
            self.escape_whole_line_popup,
            self._create_escape_whole_line_popup,
            event=event,
        )

    def _create_reserved_popup(self):
        """Create and return popup menu for PGN reserved tokens."""
        popup = self._create_non_move_popup(self.reserved_popup)
        self.reserved_popup = popup
        return popup

    def _post_reserved_menu(self, event=None):
        """Post popup menu when a '<...>, reserved, is current token."""
        return self._post_menu(
            self.reserved_popup, self._create_reserved_popup, event=event
        )

    def _post_reserved_menu_at_top_left(self, event=None):
        """Post popup menu when a '<...>, reserved, is current token."""
        return self.post_menu_at_top_left(
            self.reserved_popup, self._create_reserved_popup, event=event
        )

    def _populate_navigate_score_submenu(self, submenu):
        """Populate popup menu with commands for navigating PGN."""
        self._set_popup_bindings(submenu, self._get_navigate_score_events())

    # O-O-O is available to avoid ambiguity if both O-O and O-O-O are legal
    # when typing moves in.  When move editing is not allowed the O-O-O menu
    # option must be suppressed.
    # The addition of include_tags and include_movetext arguments gets the
    # method close to precipice of too complicated.
    def _populate_pgn_submenu(
        self,
        submenu,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        include_rav_start_rav=False,
        include_move_rav=False,
    ):
        """Populate popup menu with commands for inserting PGN."""
        assert not (include_rav_start_rav and include_move_rav)
        if include_movetext:
            self._set_popup_bindings(
                submenu, self._get_insert_pgn_in_movetext_events()
            )
        if include_rav_start_rav:
            self._set_popup_bindings(
                submenu, self._get_insert_pgn_rav_in_movetext_events()
            )
        if include_move_rav:
            self._set_popup_bindings(
                submenu, self._get_insert_rav_in_movetext_events()
            )
        if include_tags:
            self._set_popup_bindings(
                submenu, self._get_insert_pgn_in_tags_events()
            )
        if not include_ooo:
            return
        function = self._insert_castle_queenside_command  # Line count.
        self._set_popup_bindings(
            submenu,
            ((EventSpec.gameedit_insert_castle_queenside, function),),
        )

    # This method should be in GameEdit, the nearest subclass of Score which
    # supports editing games.
    # Subclasses which need non-move PGN navigation should call this method.
    # Intended for editors.
    def _add_pgn_insert_to_submenu_of_popup(
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
        self._populate_pgn_submenu(
            pgn_submenu,
            include_ooo=include_ooo,
            include_tags=include_tags,
            include_movetext=include_movetext,
            include_rav_start_rav=include_rav_start_rav,
            include_move_rav=include_move_rav,
        )
        popup.insert_cascade(index=index, label="PGN", menu=pgn_submenu)

    def _get_navigate_score_events(self):
        """Return tuple of event definitions for navigating PGN.

        Going to next and previous token, comment, or PGN tag; and first and
        last token and comment is supported.

        See Score.get_primary_activity_events for next and previous moves.

        """
        return (
            (
                EventSpec.gameedit_show_previous_rav_start,
                self._show_prev_rav_start,
            ),
            (
                EventSpec.gameedit_show_next_rav_start,
                self._show_next_rav_start,
            ),
            (EventSpec.gameedit_show_previous_token, self._show_prev_token),
            (EventSpec.gameedit_show_next_token, self._show_next_token),
            (EventSpec.gameedit_show_first_token, self._show_first_token),
            (EventSpec.gameedit_show_last_token, self._show_last_token),
            (EventSpec.gameedit_show_first_comment, self._show_first_comment),
            (EventSpec.gameedit_show_last_comment, self._show_last_comment),
            (
                EventSpec.gameedit_show_previous_comment,
                self._show_prev_comment,
            ),
            (EventSpec.gameedit_show_next_comment, self._show_next_comment),
            (EventSpec.gameedit_to_previous_pgn_tag, self._to_prev_pgn_tag),
            (EventSpec.gameedit_to_next_pgn_tag, self._to_next_pgn_tag),
        )

    def _get_insert_pgn_in_movetext_events(self):
        """Return tuple of event definitions for inserting PGN constructs.

        Inserting RAVs and adding of moves at end of game is allowed only when
        the current token is a move or a RAV start token.  The relevant
        characters are defined elsewhere, including the O-O-O shortcut
        convenient when both O-O-O and O-O are legal moves.

        The bindings for inserting RAVs are defined in other methods.

        """
        return (
            (EventSpec.gameedit_insert_comment, self._insert_comment),
            (EventSpec.gameedit_insert_reserved, self._insert_reserved),
            (
                EventSpec.gameedit_insert_comment_to_eol,
                self._insert_comment_to_eol,
            ),
            (
                EventSpec.gameedit_insert_escape_to_eol,
                self._insert_escape_to_eol,
            ),
            (EventSpec.gameedit_insert_glyph, self._insert_glyph),
            (EventSpec.gameedit_insert_white_win, self._insert_result_win),
            (EventSpec.gameedit_insert_draw, self._insert_result_draw),
            (EventSpec.gameedit_insert_black_win, self._insert_result_loss),
            (
                EventSpec.gameedit_insert_other_result,
                self._insert_result_termination,
            ),
        )

    # Use in creating popup menus only, where the entries exist to
    # advertise the options.
    def _get_insert_pgn_rav_in_movetext_events(self):
        """Return tuple of event definitions for inserting RAVs."""
        function = self._insert_rav_command  # Line count.
        return (
            (EventSpec.gameedit_insert_rav_after_rav_end, function),
            (
                EventSpec.gameedit_insert_rav_after_rav_start_move_or_rav,
                function,
            ),
            (EventSpec.gameedit_insert_rav_after_rav_start, function),
        )

    # Use in creating popup menus only, where the entries exist to
    # advertise the options.
    def _get_insert_rav_in_movetext_events(self):
        """Return tuple of event definitions for inserting text."""
        return ((EventSpec.gameedit_insert_rav, self._insert_rav_command),)

    def _get_insert_pgn_in_tags_events(self):
        """Return tuple of event definitions for inserting PGN constructs.

        Inserting and deleting PGN tags is allowed only when the current token
        is a PGN tag.

        """
        return (
            (EventSpec.gameedit_insert_pgn_tag, self._insert_pgn_tag),
            (
                EventSpec.gameedit_insert_pgn_seven_tag_roster,
                self._insert_pgn_seven_tag_roster,
            ),
            (
                EventSpec.gameedit_delete_empty_pgn_tag,
                self._delete_empty_pgn_tag,
            ),
        )

    def _get_set_insert_in_token_events(self):
        """Return tuple of event definitions for inserting text."""
        return (
            (
                EventSpec.gameedit_set_insert_previous_line_in_token,
                self._set_insert_prev_line_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_previous_char_in_token,
                self._set_insert_prev_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_next_char_in_token,
                self._set_insert_next_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_next_line_in_token,
                self._set_insert_next_line_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_first_char_in_token,
                self._set_insert_first_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_last_char_in_token,
                self._set_insert_last_char_in_token,
            ),
        )

    def _get_delete_char_in_token_events(self):
        """Return event specification tuple for text deletion."""
        return (
            (
                EventSpec.gameedit_delete_token_char_left,
                self._delete_token_char_left,
            ),
            (
                EventSpec.gameedit_delete_token_char_right,
                self._delete_token_char_right,
            ),
            (EventSpec.gameedit_delete_char_left, self._delete_char_left),
            (EventSpec.gameedit_delete_char_right, self._delete_char_right),
        )

    def _get_delete_char_in_move_events(self):
        """Return event specification tuple for move deletion."""
        return (
            (
                EventSpec.gameedit_delete_move_char_left_shift,
                self._delete_move_char_left,
            ),
            (
                EventSpec.gameedit_delete_move_char_right_shift,
                self._delete_move_char_right,
            ),
            (
                EventSpec.gameedit_delete_move_char_left,
                self._delete_move_char_left,
            ),
            (
                EventSpec.gameedit_delete_move_char_right,
                self._delete_move_char_right,
            ),
        )

    def _get_primary_activity_from_non_move_events(self):
        """Return event specification tuple for game score navigation."""
        return (
            (
                EventSpec.gameedit_non_move_show_previous_in_variation,
                self._show_prev_in_variation_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_previous_in_line,
                self._show_prev_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_next_in_line,
                self._show_next_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_next_in_variation,
                self._show_next_in_variation_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_first_in_line,
                self._show_first_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_last_in_line,
                self._show_last_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_first_in_game,
                self._show_first_in_game_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_last_in_game,
                self._show_last_in_game_from_non_move_token,
            ),
        )

    def _add_pgn_navigation_to_submenu_of_popup(
        self, popup, index=tkinter.END
    ):
        """Add non-move PGN navigation to a submenu of popup."""
        navigate_score_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_navigate_score_submenu(navigate_score_submenu)
        popup.insert_cascade(
            index=index, label="Navigate Score", menu=navigate_score_submenu
        )

    # These methods provide event handlers.

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

    # These methods are primarely involved with moves in PGN movetext.

    def _insert_empty_move_after_currentmove(self, event_char):
        """Insert empty NAVIGATE_MOVE range after current move.

        The empty NAVIGATE_MOVE range becomes the current move but because
        the move is not there yet, or is at best valid but incomplete, the
        position displayed on board is for the old current move.

        """
        widget = self.score
        if not self._is_currentmove_in_edit_move():
            # Likely will not happen as insert RAV is allowed in this case.
            return
        # Methods used to get variation and start designed for other, more
        # general, cases.  Extra return values ignored.
        current = self.current
        if self.current is None:
            # Assume that no moves, including incomplete or illegal, exist.
            # In other words bindings prevent getting here if they do exist.
            p_q = widget.tag_ranges(EDIT_RESULT)
            if p_q:
                widget.mark_set(
                    tkinter.INSERT, widget.index(p_q[0]) + "-1 lines lineend"
                )
                if widget.tag_prevrange(
                    NAVIGATE_TOKEN, p_q[0], widget.index(START_SCORE_MARK)
                ):
                    self._insert_forced_newline_into_text()
            else:
                widget.mark_set(tkinter.INSERT, tkinter.END)
            vartag = self.get_variation_tag_name()
            self.gamevartag = vartag
        else:
            start_current, end_current = widget.tag_ranges(self.current)
            insert_point = self._get_insertion_point_at_end_of_rav(end_current)
            if not insert_point:
                return
            vartag = self._get_variation_tag_of_index(start_current)
            widget.mark_set(tkinter.INSERT, insert_point)

        self._get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self._get_current_tag_and_mark_names()
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
            tr_q = widget.tag_ranges(NAVIGATE_MOVE)
            tri = 0
            for ti_q in tr_q:
                if widget.compare(ti_q, ">=", tkinter.INSERT):
                    break
                if widget.compare(ti_q, ">", tpr):
                    tri += 1
            if tri >= FORCE_NEWLINE_AFTER_FULLMOVES * 4:
                self._insert_forced_newline_into_text()
            start, end, sepend = self._insert_token_into_text(
                str(tpmpt[5]) + ".", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self._insert_token_into_text(
            event_char, SPACE_SEP
        )

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

    def _insert_empty_rav_after_next_move(self, event_char):
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
        if self.current is None:
            # Insert RAV after first move of game.
            prior = None
            choice, range_ = self._get_choice_tag_and_range_of_first_move()
            if not choice:
                choice = self._get_choice_tag_name()
            variation = self._get_variation_tag_of_index(range_[0])
            nextmove = widget.tag_nextrange(variation, range_[0])
        else:
            # Insert RAV after move after current move.
            prior, range_ = self._get_prior_tag_and_range_of_move(self.current)
            if prior:
                choice = self.get_choice_tag_for_prior(prior)
            else:
                choice = self._get_choice_tag_name()
                prior = self.get_prior_tag_for_choice(choice)
            variation = self._get_variation_tag_of_index(range_[0])
            nextmove = widget.tag_nextrange(variation, range_[-1])

        # Figure point where the new empty RAV should be inserted.
        ctr = widget.tag_ranges(choice)
        if ctr:
            # New RAV inserted just before first existing RAV for move.
            point = widget.tag_ranges(
                self.get_rav_tag_for_rav_moves(
                    self._get_rav_moves_of_index(ctr[2])
                )
            )[0]
        else:
            # No existing RAVs for the next move.
            # New RAV inserted just after last token before move after next
            # move.  Thus non-move tokens, comments of some kind, stick to
            # their preceding move; and move numbers which precede moves
            # stick to their move; and the game termination marker stays on
            # it's own line.
            tr_q = widget.tag_nextrange(variation, nextmove[1])
            if tr_q:
                tr_q = widget.tag_prevrange(NAVIGATE_TOKEN, tr_q[0])
                point = widget.index(tr_q[1] + "+1char")
            else:
                tr_q = widget.tag_nextrange(RAV_END_TAG, nextmove[1])
                if tr_q:
                    point = tr_q[0]
                else:
                    tr_q = widget.tag_nextrange(EDIT_RESULT, nextmove[1])
                    if tr_q:
                        point = widget.index(tr_q[0] + "-1char")
                    else:
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
            self._insert_forced_newline_into_text()
        start, end, sepend = self._insert_token_into_text("(", SPACE_SEP)

        tpm = self.tagpositionmap
        positiontag, tokentag, tokenmark = self._get_tag_and_mark_names()
        vartag = self.get_variation_tag_name()
        ravtag = self._get_rav_tag_name()
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
        # Insert is surrounded by tagged colourvariation text unlike add at
        # end.  This breaks the sequence so rest of inserts in this method
        # do not get tagged by colourvariation as well as ravtag.
        widget.tag_remove(colourvariation, start, sepend)
        try:
            self.previousmovetags[positiontag] = (
                self.previousmovetags[current][0],
                variation,
                variation,
            )
        except KeyError:
            self.previousmovetags[positiontag] = (None, variation, variation)

        newmovetag = self._get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self._get_current_tag_and_mark_names()
        tpm[positiontag] = tpm[self.current]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        start, end, sepend = self._insert_token_into_text(
            str(tpmpt[5]) + ("." if tpmpt[1] == FEN_WHITE_ACTIVE else "..."),
            SPACE_SEP,
        )
        widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self._insert_token_into_text(
            event_char, SPACE_SEP
        )

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        # FORCED_INDENT_TAG is not needed, compared with
        # _insert_empty_move_after_currentmove(), because this token can only
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

        if vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
            LINE_TAG,
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        self.previousmovetags[positiontag] = (current, vartag, variation)
        self.nextmovetags[current][1].append(positiontag)

        start, end, sepend = self._insert_token_into_text(")", SPACE_SEP)
        positiontag, tokentag, tokenmark = self._get_tag_and_mark_names()
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
            self._insert_forced_newline_into_text()

        return newmovetag

    def _insert_empty_rav_after_rav_start(self, event_char):
        """Insert "(<event_char>)" before first move or "(..)" in current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        tr_q = widget.tag_ranges(self.current)
        tn_q = widget.tag_names(tr_q[0])
        for n_q in tn_q:
            if n_q.startswith(TOKEN):
                insert_point = widget.tag_ranges(n_q)[-1]
                break
        return self._insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self._find_choice_prior_move_variation_main_move(tn_q),
            newline_before_rav=False
        )

    def _insert_empty_rav_after_rav_start_move_or_rav(self, event_char):
        """Insert "(<event_char>)" after first move or "(..)" in current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        insert_point = None
        tr_q = widget.tag_ranges(self.current)
        tn_q = widget.tag_names(tr_q[0])
        nmtnr = widget.tag_nextrange(NAVIGATE_MOVE, tr_q[-1])
        rstnr = widget.tag_nextrange(RAV_START_TAG, tr_q[-1])
        if rstnr and widget.compare(nmtnr[0], ">", rstnr[0]):
            insert_after = False
            for n_q in widget.tag_names(rstnr[0]):
                if n_q.startswith(RAV_TAG):
                    for en_q in widget.tag_names(widget.tag_ranges(n_q)[-1]):
                        if en_q.startswith(TOKEN):
                            insert_point = widget.tag_ranges(en_q)[-1]
                            break
                    break
        else:
            for n_q in widget.tag_names(nmtnr[0]):
                if n_q.startswith(TOKEN):
                    insert_point = widget.tag_ranges(n_q)[-1]
                    break
            insert_after = widget.tag_nextrange(NAVIGATE_TOKEN, insert_point)
        if insert_after:
            for n_q in widget.tag_names(insert_after[0]):
                if n_q.startswith(RAV_END_TAG):
                    insert_after = False
                    break
        return self._insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self._find_choice_prior_move_variation_main_move(tn_q),
            newline_after_rav=bool(insert_after)
        )

    def _insert_empty_rav_after_rav_end(self, event_char):
        """Insert "(<event_char>)" after ")" for current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        tn_q = widget.tag_names(widget.tag_ranges(self.current)[0])
        insert_point = None
        for n_q in tn_q:
            if n_q.startswith(RAV_TAG):
                for en_q in widget.tag_names(widget.tag_ranges(n_q)[-1]):
                    if en_q.startswith(TOKEN):
                        insert_point = widget.tag_ranges(en_q)[-1]
                        break
                break
        return self._insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self._find_choice_prior_move_variation_main_move(tn_q),
            newline_after_rav=False
        )

    def _delete_empty_move(self):
        """Delete empty move from PGN movetext and RAV if it is empty too."""
        widget = self.score
        if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) > 1:
            return
        tr_q = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if not tr_q:
            return
        if self._is_currentmove_in_main_line():
            current = self._select_prev_move_in_line()
            delete_rav = False
        elif self._is_currentmove_start_of_variation():
            choice = self._get_choice_tag_of_index(tr_q[0])
            prior = self.get_prior_tag_for_choice(choice)
            try:
                current = self._get_position_tag_of_index(
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
                self._step_one_variation_select(current)
                selection = self.get_selection_tag_for_prior(prior)
                sr_q = widget.tag_nextrange(
                    choice, widget.tag_ranges(selection)[1]
                )
                if sr_q:
                    widget.tag_add(selection, *sr_q)
                else:
                    widget.tag_add(
                        selection, *widget.tag_nextrange(choice, "1.0")[:2]
                    )
            delete_rav = True
        else:
            current = self._select_prev_move_in_line()
            delete_rav = False
        move_number_indicator = widget.tag_prevrange(
            MOVETEXT_MOVENUMBER_TAG,
            tr_q[0],
            widget.tag_ranges(current)[-1] if current else "1.0",
        )
        if delete_rav:
            ravtag = self.get_rav_tag_for_rav_moves(
                self._get_variation_tag_of_index(tr_q[0])
            )
            # Tkinter.Text.delete does not support multiple ranges at
            # Python 2.7.1 so call delete for each range from highest to
            # lowest.  Perhaps put a hack in workarounds?
            widget.delete(
                *widget.tag_ranges(
                    self._get_token_tag_of_index(
                        widget.tag_nextrange(
                            RAV_END_TAG,
                            widget.tag_prevrange(ravtag, tkinter.END)[0],
                        )[0]
                    )
                )
            )
            widget.delete(tr_q[0], tr_q[1])
            if move_number_indicator:
                widget.delete(*move_number_indicator)
            widget.delete(
                *widget.tag_ranges(
                    self._get_token_tag_of_index(
                        widget.tag_nextrange(ravtag, "1.0")[0]
                    )
                )
            )

            # This should be a method for newlines before and after RAV,
            # perhaps called before the two preceding deletes.
            self._delete_forced_newlines_adjacent_to_rav(tr_q)

        else:
            widget.delete(tr_q[0], tr_q[1])
            if move_number_indicator:
                widget.delete(*move_number_indicator)
            self._delete_forced_newline_token_prefix(NAVIGATE_MOVE, tr_q)
        del self.edit_move_context[self.current]
        del self.tagpositionmap[self.current]
        self.current = current
        if delete_rav:
            ci_q = widget.tag_nextrange(choice, "1.0")[0]
            if widget.compare(
                ci_q, "==", widget.tag_prevrange(choice, tkinter.END)[0]
            ):
                widget.tag_remove(
                    ALL_CHOICES, *widget.tag_nextrange(ALL_CHOICES, ci_q)
                )
                widget.tag_delete(
                    choice, prior, self.get_selection_tag_for_prior(prior)
                )
            self._clear_choice_colouring_tag()
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

    def _insert_rav_at_insert_point(
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
        _find_choice_prior_move_variation_main_move().

        """
        # If choice is not a tag name there is something wrong: do nothing.
        if not choice:
            return None

        widget = self.score

        # Move insert_point over any non-move and non-RAV marker tokens
        # before nearest of next move and RAV marker tokens.
        nttpr = widget.tag_prevrange(
            NAVIGATE_TOKEN,
            self._get_nearest_in_tags_between_point_and_end(
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
            for n_q in widget.tag_names(nttpr[-1]):
                if n_q.startswith(TOKEN):
                    insert_point = widget.tag_ranges(n_q)[-1]
                    break
            else:
                insert_point = nttpr[-1]

        widget.mark_set(tkinter.INSERT, insert_point)
        if newline_before_rav:
            self._insert_forced_newline_into_text()
        start, end, sepend = self._insert_token_into_text("(", SPACE_SEP)
        tpm = self.tagpositionmap
        positiontag, tokentag, tokenmark = self._get_tag_and_mark_names()
        vartag = self.get_variation_tag_name()
        ravtag = self._get_rav_tag_name()
        tpm[positiontag] = tpm[main_line_move if prior_move else None]
        widget.tag_add(tokentag, start, sepend)
        for tag in (ravtag, positiontag, NAVIGATE_TOKEN, RAV_START_TAG):
            widget.tag_add(tag, start, end)
        if prior_move:
            widget.tag_add(prior_move, start, end)
        # Is colourvariation wrong in _insert_empty_rav_after_next_move()?
        # There is no 'rsrmN' tag so colourvariation is not propogated.
        # The colourvariation stuff is missing compared with
        # _insert_empty_rav_after_next_move().
        self.previousmovetags[positiontag] = (
            self.previousmovetags[main_line_move][0] if prior_move else None,
            variation_containing_choice,
            variation_containing_choice,
        )
        newmovetag = self._get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self._get_current_tag_and_mark_names()
        tpm[positiontag] = tpm[main_line_move if prior_move else None]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        start, end, sepend = self._insert_token_into_text(
            str(tpmpt[5]) + ("." if tpmpt[1] == FEN_WHITE_ACTIVE else "..."),
            SPACE_SEP,
        )
        widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self._insert_token_into_text(
            event_char, SPACE_SEP
        )

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        # FORCED_INDENT_TAG is not needed, compared with
        # _insert_empty_move_after_currentmove(), because this token can only
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

        if vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
            LINE_TAG,
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        self.previousmovetags[positiontag] = (
            main_line_move,
            vartag,
            variation_containing_choice,
        )
        self.nextmovetags[main_line_move][1].append(positiontag)
        start, end, sepend = self._insert_token_into_text(")", SPACE_SEP)
        positiontag, tokentag, tokenmark = self._get_tag_and_mark_names()
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
            self._insert_forced_newline_into_text()

        return newmovetag

    def _get_insertion_point_at_end_of_rav(self, insert_point_limit):
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
                self._insert_forced_newline_into_text()
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
        # problem until _insert_empty_rav_after_next_move() method was
        # amended with correct code on 2015-09-05.
        depth = 0
        nr_q = widget.tag_ranges(self.current)
        while True:
            nr_q = widget.tag_nextrange(NAVIGATE_TOKEN, nr_q[-1])
            if not nr_q:
                if widget.get(*end_rav) == END_RAV:
                    return widget.index(end_rav[1] + "+1char")
                widget.mark_set(tkinter.INSERT, widget.index(end_rav[1]))
                self._insert_forced_newline_into_text()
                return widget.index(tkinter.INSERT)
            end_rav = nr_q
            token = widget.get(*nr_q)
            if token == START_RAV:
                depth += 1
            elif token == END_RAV:
                depth -= 1
                if depth < 0:
                    return widget.index(end_rav[1] + "-1char")

    def _delete_forced_newlines_adjacent_to_rav(self, range_):
        """Delete newlines adjacent to RAV markers to fit layout rules.

        There will be at least one move token before the RAV being deleted,
        and possibly some other tokens, including RAV start and end markers,
        too.

        """
        widget = self.score
        nttpr = widget.tag_prevrange(NAVIGATE_TOKEN, range_[0])
        for n_q in widget.tag_names(nttpr[0]):
            if n_q == RAV_START_TAG:
                nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, range_[-1])
                nltnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, range_[-1])
                if nttnr and nltnr and widget.compare(nttnr[0], ">", nltnr[0]):
                    widget.delete(*nltnr)
                break
            if n_q == RAV_END_TAG:
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
            for n_q in widget.tag_names(nttppr[0]):
                if n_q == NAVIGATE_MOVE:
                    break
            else:
                if widget.tag_nextrange(NAVIGATE_TOKEN, nttppr[-1]):
                    return
                self._delete_forced_newlines_adjacent_to_rav_and_termination(
                    nttppr[0]
                )
                return
        else:
            return
        nttnnr = widget.tag_nextrange(
            NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
        )
        if nttnnr:
            for n_q in widget.tag_names(nttnnr[0]):
                if n_q == NAVIGATE_MOVE:
                    break
            else:
                if widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[-1]):
                    return
                self._delete_forced_newlines_adjacent_to_rav_and_termination(
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
            for n_q in widget.tag_names(nttppr[0]):
                if n_q == FORCED_NEWLINE_TAG:
                    break
                if n_q == NAVIGATE_MOVE:
                    count += 1
                    break
            else:
                break
            nttppr = widget.tag_prevrange(NAVIGATE_TOKEN, nttppr[0])
        nttnr = nttnnr
        while nttnnr:
            for n_q in widget.tag_names(nttnnr[0]):
                if n_q == FORCED_NEWLINE_TAG:
                    break
                if n_q == NAVIGATE_MOVE:
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

    def _delete_forced_newlines_adjacent_to_rav_and_termination(self, index):
        """Delete newlines adjacent to RAV markers to fit layout rules.

        This method is called by _delete_forced_newlines_adjacent_to_rav which
        is assumed to have set range_ to the final RAV end marker, ')', in a
        RAV which contained RAVs before deletion started.

        """
        widget = self.score
        while True:
            fnl = widget.tag_nextrange(FORCED_NEWLINE_TAG, index)
            if not fnl:
                break
            widget.delete(*fnl)

    # These methods are primarely involved with non-move PGN movetext.

    def _get_implied_current_move(self):
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
        return self._is_currentmove_in_edited_move()

    def is_currentmove_editable(self):
        """Return True if currentmove is one of the editable moves.

        The last move of a rav or the game is editable.  If such a move is
        being edited the move is also in the 'being edited' set.

        """
        return self._is_currentmove_in_edit_move()

    def _is_game_or_rav_valid_without_move(self):
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
        if not self._is_currentmove_in_main_line():
            if self._is_currentmove_start_of_variation():
                # Should any comments be ignored? (as done here)
                return True
        current = self.score.tag_ranges(self.current)
        next_move = self.score.tag_nextrange(NAVIGATE_MOVE, current[1])
        if next_move:
            next_rav_end = self.score.tag_nextrange(RAV_END_TAG, current[1])
            if self.score.compare(next_rav_end[0], ">", next_move[0]):
                return False
        return True

    def _set_nearest_move_to_token_as_currentmove(self):
        """Set current, if a non-move token, to prior move token in game."""
        if self.current:
            # Hack coping with Page Down, Shift + Right to end, Control + Left,
            # Page Down in an imported game with errors being edited if there
            # is a token after the termination symbol. First two actions are
            # setup and last two cause program failure.
            self.current = self._get_nearest_move_to_token(self.current)
        self.set_current()
        self.apply_colouring_to_variation_back_to_main_line()
        # Set colouring of moves. This is either correct as stands (Alt-Left
        # for example) or base for modification (Alt-Right for example).

    def add_text_pgntag_or_pgnvalue(self, token, tagset=(), separator=" "):
        """Add PGN Tagname or Tagvalue to game. Return POSITION tagname."""
        start, end, sepend = super().add_text_pgntag_or_pgnvalue(
            token, tagset=tagset, separator=separator
        )
        positiontag, tokentag, tokenmark = self._get_tag_and_mark_names()
        del tokentag
        widget = self.score
        for tag in tagset:
            widget.tag_add(tag, start, end)
        widget.mark_set(tokenmark, end)
        for tag in (NAVIGATE_TOKEN,):
            widget.tag_add(tag, start, end)
        self._add_position_tag_to_pgntag_tags(positiontag, start, end)
        return start, end, sepend

    def _delete_empty_token(self):
        """Delete empty non-move token from PGN movetext."""
        widget = self.score
        if text_count(widget, START_EDIT_MARK, END_EDIT_MARK) > 1:
            return
        tr_q = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if tr_q:
            current = self._select_prev_token_in_game()
            if not current:
                current = self._select_next_token_in_game()
            widget.delete(*tr_q)
            self._delete_forced_newline_token_prefix(NAVIGATE_TOKEN, tr_q)
            del self.tagpositionmap[self.current]
            self.current = current
            self.set_current()
            self.set_game_board()
            return

    def _delete_char_next_to_insert_mark(self, first, last):
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
        # Find the previous token then call _get_nearest_move_to_token.
        tr_q = self.score.tag_ranges(self.get_token_tag_for_position(position))
        if tr_q:
            return self._get_nearest_move_to_token(
                self._get_token_tag_of_index(
                    self.score.tag_prevrange(NAVIGATE_TOKEN, tr_q[0])[0]
                )
            )
        return False

    def _insert_empty_comment(self):
        """Insert "{<null>) " sequence."""
        self._set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self._add_start_comment("{}", self._get_position_for_current())
        if self.current is None:
            self._set_start_score_mark_before_positiontag()
        return t_q[0]

    def _insert_empty_comment_to_eol(self):
        r"""Insert ";<null>\n " sequence."""
        self._set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self._add_comment_to_eol(";\n", self._get_position_for_current())
        if self.current is None:
            self._set_start_score_mark_before_positiontag()
        return t_q[0]

    def _insert_empty_escape_to_eol(self):
        r"""Insert "\n%<null>\n " sequence.

        Leading '\n' is the PGN rule.  Here this is done as a consequence
        of putting all non-move movetext tokens on their own line.  Thus
        identical to comment to EOL except '%' not ';' at beginning.

        """
        self._set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self._add_escape_to_eol("%\n", self._get_position_for_current())
        if self.current is None:
            self._set_start_score_mark_before_positiontag()
        return t_q[0]

    def _insert_empty_glyph(self):
        """Insert "$<null> " sequence."""
        self._set_insertion_point_before_next_token(between_newlines=False)
        t_q = self._add_glyph("$", self._get_position_for_current())
        if self.current is None:
            self._set_start_score_mark_before_positiontag()
        return t_q[0]

    def _insert_empty_pgn_tag(self):
        """Insert ' [ <null> "<null>" ] ' sequence."""
        self._set_insertion_point_before_next_pgn_tag()
        self.add_pgntag_to_map("", "")

    def _insert_empty_pgn_seven_tag_roster(self):
        """Insert ' [ <fieldname> "<null>" ... ] ' seven tag roster tags."""
        self._set_insertion_point_before_next_pgn_tag()
        for t_q in SEVEN_TAG_ROSTER:
            self.add_pgntag_to_map(t_q, "")

    def _insert_empty_reserved(self):
        """Insert "<[null]>) " sequence."""
        self._set_insertion_point_before_next_token(
            between_newlines=bool(
                self.score.tag_nextrange(
                    NAVIGATE_TOKEN,
                    tkinter.INSERT,
                    self.score.tag_ranges(EDIT_RESULT)[0],
                )
            )
        )
        t_q = self._add_start_reserved("<>", self._get_position_for_current())
        if self.current is None:
            self._set_start_score_mark_before_positiontag()
        return t_q[0]

    def is_move_last_of_variation(self, move):
        """Return True if currentmove is at end of a variation tag."""
        widget = self.score
        index = widget.tag_ranges(move)[1]
        for tn_q in widget.tag_names(index):
            if tn_q.startswith(RAV_MOVES):
                return not bool(self.score.tag_nextrange(tn_q, index))
        return None

    def _is_move_start_of_variation(self, move, variation):
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
    # replaced by _is_current_in_movetext calls.
    def _is_current_in_movetext(self):
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
    def _is_at_least_one_move_in_movetext(self):
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

    def _process_move(self):
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
                mtc.piece_placement_data.copy(),
                mtc.active_color,
                mtc.castling_availability,
                mtc.en_passant_target_square,
                mtc.halfmove_clock,
                mtc.fullmove_number,
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
                mtc.piece_placement_data.copy(),
                mtc.active_color,
                mtc.castling_availability,
                mtc.en_passant_target_square,
                mtc.halfmove_clock,
                mtc.fullmove_number,
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

    def _select_item_at_index(self, index):
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

    def _select_first_comment_in_game(self):
        """Return POSITION tag associated with first comment in game."""
        return self._select_first_item_in_game(NAVIGATE_COMMENT)

    def _select_last_comment_in_game(self):
        """Return POSITION tag associated with last comment in game."""
        return self._select_last_item_in_game(NAVIGATE_COMMENT)

    def _select_next_comment_in_game(self):
        """Return POSITION tag for comment after current in game."""
        return self._select_next_item_in_game(NAVIGATE_COMMENT)

    def _select_prev_comment_in_game(self):
        """Return POSITION tag for comment before current in game."""
        return self._select_prev_item_in_game(NAVIGATE_COMMENT)

    def _select_next_pgn_tag_field_name(self):
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

    def _select_prev_pgn_tag_field_name(self):
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

    def _select_first_token_in_game(self):
        """Return POSITION tag associated with first token in game."""
        return self._select_first_item_in_game(NAVIGATE_TOKEN)

    def _select_last_token_in_game(self):
        """Return POSITION tag associated with last token in game."""
        return self._select_last_item_in_game(NAVIGATE_TOKEN)

    def _select_next_rav_start_in_game(self):
        """Return POSITION tag associated with RAV after current in game."""
        return self._select_next_item_in_game(RAV_START_TAG)

    def _select_prev_rav_start_in_game(self):
        """Return POSITION tag associated with RAV before current in game."""
        return self._select_prev_item_in_game(RAV_START_TAG)

    def _set_insert_mark_at_end_of_token(self):
        """Move insert mark to end edit mark."""
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)

    def _set_insert_mark_at_start_of_token(self):
        """Move insert mark to start edit mark."""
        self.score.mark_set(tkinter.INSERT, START_EDIT_MARK)

    def _set_insert_mark_down_one_line(self):
        """Move insert mark down one line limited by end edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, "<", END_EDIT_MARK):
            widget.mark_set(
                tkinter.INSERT, tkinter.INSERT + " +1 display lines"
            )
            if widget.compare(tkinter.INSERT, ">", END_EDIT_MARK):
                widget.mark_set(tkinter.INSERT, END_EDIT_MARK)

    def _set_insert_mark_left_one_char(self):
        """Move insert mark left one character limited by start edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, ">", START_EDIT_MARK):
            widget.mark_set(tkinter.INSERT, tkinter.INSERT + " -1 chars")

    def _set_insert_mark_right_one_char(self):
        """Move insert mark right one character limited by end edit mark."""
        widget = self.score
        if widget.compare(tkinter.INSERT, "<", END_EDIT_MARK):
            widget.mark_set(tkinter.INSERT, tkinter.INSERT + " +1 chars")

    def _set_insert_mark_up_one_line(self):
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
        if text_count(self.score, start, end) < 2:
            for tn_q in tagnames:
                if tn_q.startswith(TOKEN):
                    start = self.score.tag_nextrange(tn_q, "1.0")[0]
                    break
            else:
                return
        self.score.mark_set(START_EDIT_MARK, start)
        self.score.mark_set(END_EDIT_MARK, end)
        self.score.mark_set(tkinter.INSERT, END_EDIT_MARK)
        self._set_move_tag(START_EDIT_MARK, END_EDIT_MARK)

    def _insert_char_at_insert_point(self, char):
        """Insert char at insert point."""
        if not char:
            return None
        if self._allowed_chars_in_token:
            if char not in self._allowed_chars_in_token:
                return None
        widget = self.score
        start, end = widget.tag_ranges(self.current)
        non_empty = (
            text_count(widget, start, end) - self._lead_trail.header_length
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

    # These methods populate the widget from the PGN structure.

    def map_game(self):
        """Extend to set insertion cursor at start of moves."""
        super().map_game()
        # Is INSERT_TOKEN_MARK redundant now?  Let's see.
        self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)

    # Unwanted tags can be inherited from surrounding characters.
    def _map_move_text(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._tag_token_for_editing(
            super()._map_move_text(token, position),
            self._get_current_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, INSERT_RAV),
            tag_position=False,  # already tagged by superclass method
        )
        self._game_scaffold.token_position = self.tagpositionmap[positiontag]
        return token_indicies

    # Unwanted tags can be inherited from surrounding characters.
    def map_start_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing.

        ravtag is placed on a stack so it can be recovered when the
        matching RAV end appears for tagging.  The tag marks two of the
        places where new variations may be inserted.

        """
        scaffold = self._game_scaffold
        token_indicies = super().map_start_rav(token, position)
        ravtag = self._get_rav_tag_name()
        self.ravstack.append(ravtag)
        prior = self.get_prior_tag_for_choice(scaffold.choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            scaffold.token_position = self.tagpositionmap[
                self._get_position_tag_of_index(prior_range[0])
            ]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_START_TAG, prior)
        else:
            scaffold.token_position = self.tagpositionmap[None]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_START_TAG)
        positiontag, token_indicies = self._tag_token_for_editing(
            token_indicies,
            self._get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_end_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing.

        ravtag is recovered from the stack to tag the end of RAV, one
        of the points where new variations can be inserted.

        """
        # last move in rav is editable
        scaffold = self._game_scaffold
        self._add_move_to_editable_moves(scaffold.vartag)
        token_indicies = super().map_end_rav(token, position)
        ravtag = self.ravstack.pop()
        prior = self.get_prior_tag_for_choice(scaffold.choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            scaffold.token_position = self.tagpositionmap[
                self._get_position_tag_of_index(
                    self._get_range_of_main_move_for_rav(prior_range[0])[0]
                )
            ]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_END_TAG, prior)
        else:
            scaffold.token_position = self.tagpositionmap[None]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_END_TAG)
        positiontag, token_indicies = self._tag_token_for_editing(
            token_indicies,
            self._get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_termination(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # last move in game is editable
        self._add_move_to_editable_moves(self._game_scaffold.vartag)
        positiontag, token_indicies = self._tag_token_for_editing(
            super().map_termination(token),
            self._get_tag_and_mark_names,
            # tag_start_to_end=(EDIT_RESULT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            tag_start_to_end=(EDIT_RESULT,),
        )
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        return token_indicies

    def _map_initial_start_comment(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self._insert_forced_newline_into_text()
        return self._tag_token_for_editing(
            self._insert_token_into_text(token, SPACE_SEP),
            self._get_tag_and_mark_names,
            tag_start_to_end=(EDIT_COMMENT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )

    def _map_start_comment(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_initial_start_comment(
            token, self._tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def _map_initial_comment_to_eol(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self._insert_forced_newline_into_text()
        return self._tag_token_for_editing(
            super()._map_initial_comment_to_eol(token, newline_prefix),
            self._get_tag_and_mark_names,
            tag_start_to_end=(
                EDIT_COMMENT_EOL,
                NAVIGATE_TOKEN,
                NAVIGATE_COMMENT,
            ),
        )

    def _map_comment_to_eol(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_initial_comment_to_eol(
            token, self._tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def _map_initial_escape_to_eol(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self._insert_forced_newline_into_text()
        return self._tag_token_for_editing(
            super()._map_initial_escape_to_eol(token, newline_prefix),
            self._get_tag_and_mark_names,
            tag_start_to_end=(EDIT_ESCAPE_EOL, NAVIGATE_TOKEN),
        )

    # The EDIT_ESCAPE_EOL entry in _TOKEN_LEAD_TRAIL has been changed from
    # (2, 0) to (1, 0) to fit the _add_escape_to_eol() case.  Not sure yet
    # if this breaks the _map_escape_to_eol() case, which currently cannot
    # happen because '\n%\n' tokens are not put on database even if present
    # in the PGN movetext.
    def _map_escape_to_eol(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_initial_escape_to_eol(
            token, self._tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_integer(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._tag_token_for_editing(
            super().map_integer(token, position),
            self._get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN,),
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_initial_glyph(self, token, newline_prefix):
        """Tag token for single-step navigation and game editing."""
        if newline_prefix:
            self._insert_forced_newline_into_text()
        return self._tag_token_for_editing(
            self._insert_token_into_text(token, SPACE_SEP),
            self._get_tag_and_mark_names,
            tag_start_to_end=(EDIT_GLYPH, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )

    def _map_glyph(self, token):
        """Override to tag token for single-step navigation and editing."""
        # At present NAGs are not put on a line of their own when following
        # a move.  They would be if the NAG translations were shown too.
        # before = self._tokens_exist_between_movetext_start_and_insert_point()
        before = self.score.tag_prevrange(
            NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
        )
        if before:
            before = NAVIGATE_MOVE not in self.score.tag_names(before[0])
        else:
            before = False

        positiontag, token_indicies = self._map_initial_glyph(token, before)
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_period(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self._tag_token_for_editing(
            super().map_period(token, position),
            self._get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN,),
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_empty_start_reserved(self, token, newline_prefix):
        """Tag token for single-step navigation and game editing."""
        if newline_prefix:
            self._insert_forced_newline_into_text()
        return self._tag_token_for_editing(
            self._insert_token_into_text(token, SPACE_SEP),
            self._get_tag_and_mark_names,
            tag_start_to_end=(EDIT_RESERVED, NAVIGATE_TOKEN),
        )

    def _map_start_reserved(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_empty_start_reserved(
            token, self._tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self._create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_non_move(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # mark_for_edit is True while no EDIT_... tag is done?
        positiontag, token_indicies = self._tag_token_for_editing(
            super().map_non_move(token),
            self._get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )
        self.tagpositionmap[positiontag] = None
        return token_indicies

    def _tag_token_for_editing(
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

    def _get_range_of_main_move_for_rav(self, start):
        """Return range of move for which start index ends a RAV."""
        widget = self.score
        for n_q in widget.tag_names(start):
            if n_q.startswith(RAV_MOVES):
                return widget.tag_nextrange(
                    n_q, widget.tag_nextrange(n_q, start)[1]
                )
        raise GameEditException("Unable to find position for end RAV")

    # This method may be removed because it is used in only two places, and
    # one of those needs the 'tr_q' value too.
    def _add_move_to_editable_moves(self, variation):
        """Mark last move in variation for editing rather than insert RAV.

        This method should be called when it is known there are no more moves
        in the game or a RAV, which is at end of RAV or game termination.

        """
        widget = self.score
        tr_q = widget.tag_prevrange(variation, tkinter.END)

        # Is it a game score with no moves?
        if not tr_q:
            return

        widget.tag_add(EDIT_MOVE, *tr_q)
        widget.tag_remove(INSERT_RAV, *tr_q)

    def _tokens_exist_between_movetext_start_and_insert_point(self):
        """Return True if tokens exist from movetext start to insert point."""
        return bool(
            self.score.tag_prevrange(
                NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
            )
        )

    def _get_rav_tag_name(self):
        """Return suffixed RAV_TAG tag name.

        The Score.get_variation_tag_name() is assumed to have been called
        to increment self.variation_number and set the name of the
        corresponding RAV_MOVES tag.

        """
        return "".join((RAV_TAG, str(self.variation_number)))

    # These methods were left-over when an attempt to split GameEdit into
    # smaller classes with short, almost meaningful, names was made.
    # They ended up in a module called gameedit_misc.

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
    # Event handler to post pgn_tag_popup menu is renamed _post_pgn_tag_menu.
    # Two new ones, start_rav_popup and end_rav_popup, are needed.  It may be
    # best to have one each for all the editable tokens, in particular escaped
    # line and comment to end of line, to cope with the slight variation in
    # editing rules.
    # The _bind_for_primary_activity() call must be replaced because it may,
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
        tagranges = self._set_current_range()
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

                    # Could replace 'not self._is_current_in_movetext()' with
                    # 'PGN_TAG in tns', but a 'self._is_current_in_movetext()'
                    # just before the 'else' clause becomes wise.
                    # Maybe explicit tests for all the EDIT_* tags (Tk sense)
                    # is best.
                    self._set_token_context(tagnames, tagranges, tnn)

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
                    self._set_move_tag(*tagranges)
                elif RAV_START_TAG in tns:
                    if self._most_recent_bindings != RAV_START_TAG:
                        self.token_bind_method[RAV_START_TAG](self)
                    self.score.mark_set(tkinter.INSERT, tagranges[1])
                    self._set_move_tag(*tagranges)
                else:
                    if (
                        self._most_recent_bindings
                        != NonTagBind.DEFAULT_BINDINGS
                    ):
                        self.token_bind_method[NonTagBind.DEFAULT_BINDINGS](
                            self
                        )
                    self.score.mark_set(tkinter.INSERT, tagranges[1])
                    self._set_move_tag(*tagranges)

                return
        elif self.current is None:
            if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
                self.token_bind_method[NonTagBind.NO_EDITABLE_TAGS](self)
            self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)
            if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
                self._bind_for_primary_activity()
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

    def _add_position_tag_to_pgntag_tags(self, tag, start, end):
        """Add position tag to to PGN Tag tokens for position display.

        Navigation to non-move tokens is allowed in edit mode and the initial
        position of the game is displayed when a PGN Tag is current.

        """
        self.score.tag_add(tag, start, end)
        self.tagpositionmap[tag] = self.fen_tag_tuple_square_piece_map()

    def _delete_forced_newline_token_prefix(self, tag, range_):
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

    def _get_choice_tag_and_range_of_first_move(self):
        """Return choice tag name and range of first char for first move."""
        tr_q = self.score.tag_nextrange(NAVIGATE_MOVE, "1.0")
        if tr_q:
            return self._get_choice_tag_of_index(tr_q[0]), tr_q
        return None

    def _get_prior_tag_and_range_of_move(self, move):
        """Return prior move tag name and move range for move tag."""
        tr_q = self.score.tag_ranges(move)
        if tr_q:
            return self._get_prior_tag_of_index(tr_q[0]), tr_q
        return None

    def _get_prior_tag_of_index(self, index):
        """Return Tk tag name if index is in a choice tag."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(PRIOR_MOVE):
                return tn_q
        return None

    def _get_rav_moves_of_index(self, index):
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

    def _get_token_tag_of_index(self, index):
        """Return Tk tag name if index is in TOKEN tag."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(TOKEN):
                return tn_q
        return None

    def _get_variation_tag_of_index(self, index):
        """Return Tk tag name for variation of currentmove."""
        for tn_q in self.score.tag_names(index):
            if tn_q.startswith(RAV_MOVES):
                return tn_q
        return None

    def _get_nearest_move_to_token(self, token):
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
                return self._get_position_tag_of_index(r_q[0])
            prior = self._get_prior_tag_of_index(r_q[0])
            if prior:
                if widget.tag_nextrange(RAV_END_TAG, *r_q):
                    return self._select_next_move_in_line(
                        movetag=self._get_position_tag_of_index(
                            widget.tag_ranges(prior)[0]
                        )
                    )
                return self._get_position_tag_of_index(
                    widget.tag_ranges(prior)[0]
                )
            r_q = widget.tag_prevrange(
                NAVIGATE_TOKEN, r_q[0], START_SCORE_MARK
            )

    def _find_choice_prior_move_variation_main_move(self, tag_names):
        """Return arguments for _insert_rav derived from RAV tag in tag_names.

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

    def _get_nearest_in_tags_between_point_and_end(self, point, tags):
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

    def _is_currentmove_in_edit_move(self):
        """Return True if current move is editable.

        If there are no moves in the game current move is defined as editable.
        This allows games to be inserted.

        """
        if self.current is None:
            return not bool(self.score.tag_nextrange(NAVIGATE_MOVE, "1.0"))
        start, end = self.score.tag_ranges(self.current)
        return bool(self.score.tag_nextrange(EDIT_MOVE, start, end))

    def _is_currentmove_in_edited_move(self):
        """Return True if current move is being edited.

        If there are no moves in the game current move is not being edited.

        """
        if self.current is None:
            return bool(self.score.tag_nextrange(NAVIGATE_MOVE, "1.0"))
        start, end = self.score.tag_ranges(self.current)
        return bool(self.score.tag_nextrange(MOVE_EDITED, start, end))

    # Do the add_* methods need position even though the map_* methods do not?
    def _link_inserts_to_moves(self, positiontag, position):
        """Link inserted comments to moves for matching position display."""
        self.tagpositionmap[positiontag] = position
        if self.current:
            variation = self._get_variation_tag_of_index(
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

    def _add_start_comment(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self._tokens_exist_between_movetext_start_and_insert_point()
        after = self._tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_initial_start_comment(
            token, before
        )
        if not before and after:
            self._insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self._link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def _add_comment_to_eol(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self._tokens_exist_between_movetext_start_and_insert_point()
        after = self._tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_initial_comment_to_eol(
            token, before
        )
        if not before and after:
            self._insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self._link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def _add_escape_to_eol(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self._tokens_exist_between_movetext_start_and_insert_point()
        after = self._tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_initial_escape_to_eol(
            token, before
        )
        if not before and after:
            self._insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self._link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def _add_glyph(self, token, position):
        """Tag token for single-step navigation and game editing."""
        # At present NAGs are not put on a line of their own when following
        # a move.  They would be if the NAG translations were shown too.
        # before = self._tokens_exist_between_movetext_start_and_insert_point()
        before = self.score.tag_prevrange(
            NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
        )
        if before:
            before = NAVIGATE_MOVE not in self.score.tag_names(before[0])
        else:
            before = False

        after = self._tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_initial_glyph(token, before)
        if not before and after:
            self._insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self._link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def _add_start_reserved(self, token, position):
        """Tag token for single-step navigation and game editing."""
        before = self._tokens_exist_between_movetext_start_and_insert_point()
        after = self._tokens_exist_between_insert_point_and_game_terminator()
        positiontag, token_indicies = self._map_empty_start_reserved(
            token, before
        )
        if not before and after:
            self._insert_forced_newline_into_text()
        self.score.tag_remove(
            FORCED_NEWLINE_TAG, token_indicies[0], token_indicies[-1]
        )
        self._link_inserts_to_moves(positiontag, position)
        return positiontag, token_indicies

    def _tokens_exist_between_insert_point_and_game_terminator(self):
        """Return True if tokens exist from insert point_to_game_terminator."""
        return bool(self.score.tag_nextrange(NAVIGATE_TOKEN, tkinter.INSERT))

    def _select_first_item_in_game(self, item):
        """Return POSITION tag associated with first item in game."""
        widget = self.score
        tr_q = widget.tag_nextrange(item, "1.0")
        if not tr_q:
            return None
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return None

    def _select_last_item_in_game(self, item):
        """Return POSITION tag associated with last item in game."""
        widget = self.score
        tr_q = widget.tag_prevrange(item, tkinter.END)
        if not tr_q:
            return None
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return None

    def _select_next_item_in_game(self, item):
        """Return POSITION tag associated with item after current in game."""
        widget = self.score
        oldtr = widget.tag_ranges(MOVE_TAG)
        if oldtr:
            tr_q = widget.tag_nextrange(item, oldtr[-1])
        else:
            tr_q = widget.tag_nextrange(item, tkinter.INSERT)
        if not tr_q:
            return self._select_first_item_in_game(item)
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return self._select_first_item_in_game(item)

    def _select_prev_item_in_game(self, item):
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
            return self._select_last_item_in_game(item)
        for tn_q in widget.tag_names(tr_q[0]):
            if tn_q.startswith(POSITION):
                return tn_q
        return self._select_last_item_in_game(item)

    def _select_next_token_in_game(self):
        """Return POSITION tag associated with token after current in game."""
        return self._select_next_item_in_game(NAVIGATE_TOKEN)

    def _select_prev_token_in_game(self):
        """Return POSITION tag associated with token before current in game."""
        return self._select_prev_item_in_game(NAVIGATE_TOKEN)

    # Adding between_newlines argument seemed a good idea at first, but when
    # the _insert_empty_comment() method turned out to need a conditional to
    # set the argument the whole thing began to look far too complicated.
    # See the other insert_empty_*() methods, except moves, too.
    # Solution may involve a new mark with right gravity, END_SCORE_MARK,
    # set at end of line before the Game Termination Marker.  Perhaps the
    # blank line between the PGN Tags and the Game Termination Marker in the
    # new game template should be removed, if this is not forced.
    # The escaped line may continue to be a problem.
    def _set_insertion_point_before_next_token(self, between_newlines=True):
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
                self._insert_forced_newline_into_text()
                widget.mark_set(tkinter.INSERT, tkinter.INSERT + " -1 char")

    def _set_insertion_point_before_next_pgn_tag(self):
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

    def _set_token_context(self, tagnames, tagranges, tokenprefix):
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
            self._get_token_text_length(start, end) - lead_trail.header_length
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
        self._set_move_tag(start, end)

    @staticmethod
    def get_token_insert(tagnames):
        """Set token editing bound marks from TOKEN<suffix> in tagnames."""
        for tn_q in tagnames:
            if tn_q.startswith(TOKEN):
                return "".join((TOKEN_MARK, tn_q[len(TOKEN) :]))
        return None

    def _get_token_text_length(self, start, end):
        """Set token editing bound marks from TOKEN<suffix> in tagnames."""
        return text_count(self.score, start, end)

    def _set_start_score_mark_before_positiontag(self):
        """Set start score mark at start self.position_number position tag."""
        self.score.mark_set(
            START_SCORE_MARK,
            self.score.tag_ranges(
                "".join((POSITION, str(self.position_number)))
            )[0],
        )

    def _step_one_variation_select(self, move):
        """Select next variation in choices at current position."""
        # Hack of _step_one_variation with setting code removed
        if move is None:
            # No prior to variation tag exists: no move to attach it to.
            pt_q = None
            ct_q = self._get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            st_q = self.get_selection_tag_for_choice(ct_q)
        else:
            pt_q = self._get_prior_to_variation_tag_of_move(move)
            ct_q = self.get_choice_tag_for_prior(pt_q)
            st_q = self.get_selection_tag_for_prior(pt_q)
        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self._cycle_selection_tag(ct_q, st_q)
        vt_q = self._get_colouring_variation_tag_for_selection(st_q)
        self._set_variation_selection_tags(pt_q, ct_q, st_q, vt_q)
        return vt_q

    def create_edit_move_context(self, tag):
        """Return tuple of FEN (position) and * (unknown result) for tag."""
        return (
            self._generate_fen_for_position(*self.tagpositionmap[tag]).join(
                _EDIT_MOVE_CONTEXT
            ),
            UNKNOWN_RESULT,
        )
