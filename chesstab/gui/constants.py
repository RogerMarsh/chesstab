# constants.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""User Interface constants.

Many of the constants are used to generate tkinter.Text tag and mark names
used when highlighting game scores in various widgets.

Assume these fonts have been downloaded and installed:

Chess Cases, Chess Lucena, Chess Merida, and Chess Motif fonts
by Armando H Marroquin.

At time of writing available from:

www.enpassant.dk/chess/fonteng.htm
"""

from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
    TAG_EVENT,
    TAG_DATE,
)

from ..core.constants import (
    REPERTOIRE_TAG_ORDER,
    UNKNOWN_RESULT,
)

# names of chess board fonts in decreasing preference order.
# The 'win32' order is my preference, but Merida and Motif are microsoft-symbol
# fonts according to description in /usr/local/share/fonts/../fonts.dir after
# installation on FreeBSD 10.1 and produce the default characters, not pieces.
import sys

if sys.platform == "win32":
    PREFERRED_PIECES = (
        "Chess Merida",
        "Chess Cases",
        "Chess Motif",
        "Chess Lucena",
    )
else:
    PREFERRED_PIECES = (
        "Chess Cases",
        "Chess Lucena",
        "Chess Merida",
        "Chess Motif",
    )
del sys

# names of Tk named fonts.
MOVES_PLAYED_IN_GAME_FONT = "moves"
PIECES_ON_BOARD_FONT = "pieces"
WILDPIECES_ON_BOARD_FONT = "wildpieces"
LISTS_OF_GAMES_FONT = "lists"
TAGS_VARIATIONS_COMMENTS_FONT = "tags"

# named colours in chessboard colour scheme.
LITECOLOR_NAME = "light squares"
DARKCOLOR_NAME = "dark squares"
WHITECOLOR_NAME = "white pieces"
BLACKCOLOR_NAME = "black pieces"
LINE_COLOR_NAME = "line"
MOVE_COLOR_NAME = "move"
ALTERNATIVE_MOVE_COLOR_NAME = "alternative move"
VARIATION_COLOR_NAME = "variation"

# default chessboard colour scheme.
LITECOLOR = "#d9eed9"
DARKCOLOR = "#c2c298"
WHITECOLOR = "#db0ee8"
BLACKCOLOR = "#181634"

# default game score colour scheme.
LINE_COLOR = "#76d9d9"  # a light blue
MOVE_COLOR = "#86d929"  # a light green
ALTERNATIVE_MOVE_COLOR = "#eb3010"  # a dark orange
VARIATION_COLOR = "#e0f113"  # a pale yellow

# names of chess score text management tags.
"""The primary tags are POSITION<suffix> and TOKEN<suffix> where suffix is a
serial number.  Every character is tagged by one TOKEN tag and for each TOKEN
tag there is a corresponding POSITION tag which tags all the non-separator
characters tagged by TOKEN.  There is always at least one trailing separator
character and there may be leading separator characters.  A TOKEN_MARK<suffix>
mark is associated with each TOKEN<suffix> and indicates the insertion point
for editing the token.  An empty token has no position range, and maybe no
POSITION tag, and the TOKEN_MARK is used to initialise the POSITION range.

The NAVIGATE_COMMENT NAVIGATE_TOKEN and NAVIGATE_MOVE tags contain the existing
POSITION ranges for the tokens of the relevant types.

RAV_SEP<suffix> is the only tag which collects TOKEN ranges which are used to
colour variations when there is a choice of moves available (recursive
annotation variations).

Each EDIT_... range indicates which tokens are currently editable.  Note that
only the last move in a line is editable.  The tag name is used to pick the
editing rules applied to the token.

An EDIT_MOVE range must be the last range in a RAV_MOVES tag that is also a
NAVIGATE_MOVE range.

Note that WHITESPACE is not used but is intended for picking out editable
whitespace and will be used, if necessary, as NAVIGATE_WHITESPACE.

RAV... tags refer to all moves between matching PGN RAV tags although only
the relevant characters for the Tk tag's purpose get tagged.
LINE... tags refer to all moves to the right of the current move until the
next unmatched PGN END RAV tag.
VARIATION... tags refer to all moves to the right of the current move until the
next unmatched PGN START RAV tag.
So moves4 and moves6 are in LINE... tags while moves4 and moves6 are in
VARIATION... tags for currentmove in the sequence:
"( moves1 ( moves2 ) moves3 currentmove moves4 ( moves5 ) moves6 )".
This sequence has three sets of RAV... tags: one for the whole sequence and
one each for the sub-sequences "( moves2 )" and "( moves5 )".
"""
# LINE... and VARIATION... got used this way in wxWidgets days so RAV... is
# borrowed from PGN terminology to do the 'whole variation' tasks.  In chess
# cirles the terms line and variation are mostly interchangable, but if talking
# about a game, variations refers to alternatives to the moves actually played.

BUILD_TAG = "bt"  # move and RAV markers (deleted after widget build)
NAVIGATE_COMMENT = "nc"  # can be selected by comment navigation
NAVIGATE_TOKEN = "nt"  # can be selected by navigation
NAVIGATE_MOVE = "nm"  # can be selected by move navigation
EDIT_GLYPH = "eg"  # can be selected for glyph editing
EDIT_RESULT = "er"  # can be selected for result editing
EDIT_PGN_TAG_NAME = "eptn"  # can be selected for PGN Tag name editing
EDIT_PGN_TAG_VALUE = "eptv"  # can be selected for PGN Tag value editing
EDIT_COMMENT = "ec"  # can be selected for comment text editing
EDIT_RESERVED = "erv"  # can be selected for reserved text editing
EDIT_COMMENT_EOL = "eolc"  # can be selected for comment to eol editing
EDIT_ESCAPE_EOL = "eole"  # can be selected for escape to eol editing
EDIT_MOVE_ERROR = "mverr"  # can be selected for move error editing
EDIT_MOVE = "em"  # can be selected for move editing
INSERT_RAV = "ir"  # can be selected for rav insertion
MOVE_EDITED = "me"  # moves that are being edited
WHITESPACE = "ws"  # can be deleted or inserted between editables
RAV_MOVES = "rm"  # prefix for line tags
CHOICE = "ch"  # prefix for line choice tags
SELECTION = "se"  # prefix for line selected choice tags
PRIOR_MOVE = "pm"  # prefix for line prior move tags
RAV_SEP = "rs"  # prefix for line tags with trailing separator
RAV_START_TAG = "rst"  # all ranges for start RAV tokens (added for edit)
RAV_END_TAG = "ret"  # all ranges for end RAV tokens
RAV_TAG = "rt"  # prefix for a variations start and end RAV tags
ALL_CHOICES = "ac"  # all the first moves of RAV_MOVES tags
POSITION = "po"  # prefix for position map tags
TOKEN = "tn"  # prefix for token tags
TOKEN_MARK = "tm"  # prefix for insertion point marks for tokens
PGN_TAG = "pt"  # all ranges for PGN Tag name and value pairs
TERMINATION_TAG = "tt"  # all ranges for values of termination tags
DESCRIPTION = "pd"  # all ranges for name of partial position
PIECE_LOCATIONS = "lo"  # all ranges for piece squares in partial position
# mark the start of the game score, which is also end of PGN tags.
START_SCORE_MARK = "scoremark"
# mark start and end points of editable range, usually range of current.
START_EDIT_MARK = "starteditmark"
END_EDIT_MARK = "endeditmark"
# move played to reach position displayed on board.
MOVE_TAG = MOVE_COLOR_NAME
# moves in selected variation to be played from position displayed on board.
LINE_TAG = LINE_COLOR_NAME
# first move in alternatives to selected variation not yet entered.
ALTERNATIVE_MOVE_TAG = ALTERNATIVE_MOVE_COLOR_NAME
# moves played from main line to reach position in which MOVE_TAG move played.
VARIATION_TAG = VARIATION_COLOR_NAME
# last character in line. Hide the LINE_TAG colour to indicate no more moves.
LINE_END_TAG = "line_end"
# mark the start of the partial position, which is also end of description.
START_POSITION_MARK = "positionmark"
# indentation tag for variations generated by Chess Engines in analysis widget
# of a Game instance.
ANALYSIS_INDENT_TAG = "indent"
# elide tag for PGN tags used in analysis score text widgets.
ANALYSIS_PGN_TAGS_TAG = "analysispgntags"
# indentation tag for wrapped game movetext.
MOVETEXT_INDENT_TAG = "movetextindent"
# elide tag for move numbers in game movetext.
MOVETEXT_MOVENUMBER_TAG = "movenumbertag"
# indentation tag for first move after forced newline in game movetext.
FORCED_INDENT_TAG = "forcedindent"
# newline characters inserted in game movetext for layout or performance.
FORCED_NEWLINE_TAG = "forcednewlinetag"

EMPTY_SEVEN_TAG_ROSTER = "".join(
    [r.join(("[", '""]')) for r in SEVEN_TAG_ROSTER]
)
GRID_HEADER_SEVEN_TAG_ROSTER = frozenset(
    (TAG_WHITE, TAG_BLACK, TAG_RESULT, TAG_EVENT, TAG_DATE)
)
STATUS_SEVEN_TAG_ROSTER_EVENT = (
    TAG_WHITE,
    TAG_RESULT,
    TAG_BLACK,
    TAG_DATE,
    TAG_EVENT,
)
STATUS_SEVEN_TAG_ROSTER_SCORE = (TAG_WHITE, TAG_RESULT, TAG_BLACK, TAG_DATE)
STATUS_SEVEN_TAG_ROSTER_PLAYERS = (TAG_WHITE, TAG_RESULT, TAG_BLACK)
EMPTY_REPERTOIRE_GAME = "".join(
    [r.join(("[", '""]')) for r in REPERTOIRE_TAG_ORDER]
)

SPACE_SEP = " "  # separator used displaying moves and so on
NEWLINE_SEP = "\n"  # separator used displaying moves and so on
NULL_SEP = ""  # separator used displaying moves and so on

# mark the start of the selection rule, which is also end of rule's name.
START_SELECTION_RULE_MARK = "rulemark"

# Force game score text widgets to display every fullmove, a white halfmove and
# a black halfmove, on a new line if the total number of fullmoves including
# variations exceeds this limit.  This is for performance reasons that become
# noticeable at about 500 fullmoves.  Repertoire displays may often exceed this
# limit.  The maximum length game, nearly 6000 fullmoves, takes more than an
# hour to display, or do a navigation operation.
# Force game score text widgets to split movetext into lines, by newline, every
# few moves.  This is for performance reasons that become noticeable at about
# 500 fullmoves.  Repertoire displays may often exceed this limit.  The maximum
# length game, nearly 6000 fullmoves, takes more than an hour to display, or do
# a navigation operation.
# 20 seems reasonable because it does not spread moves out too much and allows
# for move numbers to be inserted without generating too many extra tokens.
FORCE_NEWLINE_AFTER_FULLMOVES = 20
