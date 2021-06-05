# fonts.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Make and copy chess pieces fonts for ChessTab.
"""

import tkinter
import tkinter.font

# Current practical way to determine if running on Wine, taking advantage of
# a problem found in ..core.uci which prevents UCI chess engines being used to
# do position analysis in this environment.  Here the consequence is fonts like
# 'Chess Cases' in '~/.wine/drive_c/windows/Fonts' are used as the default font
# in Font() calls, while these are not so used when put in the corresponding
# place on Microsoft Windows.
# ChessTab should be run, under Wine, by a dedicated username to avoid
# polluting the widgets of other Python programs, under Wine, with the chess
# font character set.
# The same problem occurs under Wine when these chess fonts are put in the
# /usr/local/share/fonts directory, for example, to support ChessTab on
# unix-like systems.
import multiprocessing

try:
    multiprocessing.Queue()
    _assume_wine = False
except OSError:
    _assume_wine = True
del multiprocessing

from . import constants

modify_font_attributes = ("family", "weight", "slant", "size")
modify_board_font_attributes = ("family", "weight")
integer_attributes = {"size"}


def copy_board_font_attributes(source, target):
    """Copy font attributes changeable for board from source to target."""
    _copy_font_attributes(modify_board_font_attributes, source, target)


def copy_font_attributes(source, target):
    """Copy font attributes changeable for score from source to target."""
    _copy_font_attributes(modify_font_attributes, source, target)


def make_chess_fonts(root, preferred_pieces=constants.PREFERRED_PIECES):
    """Create score and board fonts and return tuple of fonts."""
    default = _get_default_font_actual(tkinter.Text)
    moves = tkinter.font.Font(
        root=root, name=constants.MOVES_PLAYED_IN_GAME_FONT, **default
    )
    tags = tkinter.font.Font(
        root=root, name=constants.TAGS_VARIATIONS_COMMENTS_FONT, **default
    )

    # An explicit wildpieces font was not noticed to be necessary before
    # Python2.7 on Microsoft Windows.  But I had only been using 'x', for any
    # piece before and this still worked without the explicit font.
    # On FreeBSD (non-Wine) the explicit font is not needed.
    wildpieces = tkinter.font.Font(
        root=root, name=constants.WILDPIECES_ON_BOARD_FONT, **default
    )

    ff = set(tkinter.font.families())
    for pff in preferred_pieces:
        if pff in ff:
            del default["family"]
            pieces = tkinter.font.Font(
                root=root,
                name=constants.PIECES_ON_BOARD_FONT,
                family=pff,
                **default
            )
            break
    else:
        pieces = tkinter.font.Font(
            root=root, name=constants.PIECES_ON_BOARD_FONT, **default
        )
    moves.configure(weight=tkinter.font.BOLD)
    pieces.configure(weight=tkinter.font.BOLD)
    wildpieces.configure(weight=tkinter.font.BOLD)
    return moves, tags, pieces, wildpieces


def make_list_fonts(root):
    """Create game list font and return font in tuple."""
    return tkinter.font.Font(
        root=root,
        name=constants.LISTS_OF_GAMES_FONT,
        **_get_default_font_actual(tkinter.Text)
    )


def _copy_font_attributes(attributes, source, target):
    """Copy attributes from source font to target font."""
    for fa in attributes:
        if fa in source:
            target[fa] = source[fa]


def _get_default_font_actual(widget_class):
    """Return actuals for widget_class font or Courier if it does not exist."""
    if _assume_wine:
        return tkinter.font.Font(family="Courier").actual()

    # On MS Windows the named font from widget_class exists at Python2.6
    # but not at Python2.5
    try:
        return tkinter.font.nametofont(widget_class().cget("font")).actual()
    except tkinter.TclError:
        return tkinter.font.Font(family="Courier").actual()
