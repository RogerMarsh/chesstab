# options.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions for editing and applying font and colour options."""

import os

from . import constants
from . import fonts

font_names = {
    constants.MOVES_PLAYED_IN_GAME_FONT,
    constants.PIECES_ON_BOARD_FONT,
    constants.WILDPIECES_ON_BOARD_FONT,
    constants.LISTS_OF_GAMES_FONT,
    constants.TAGS_VARIATIONS_COMMENTS_FONT,
}

_options_filename = "options"


def get_saved_options(folder):
    """Return dictionary of colour and font defaults from options file.

    Return None if options file cannot be read or does not exist.

    """
    optionsfilename = os.path.join(folder, _options_filename)
    if not os.path.isfile(optionsfilename):
        return None
    try:
        with open(optionsfilename, "r") as optionsfile:
            return _extract_options(optionsfile)
    except OSError:
        pass
    return None


def save_options(folder, changes):
    """Save font and colour option changes in folder/<options file>.

    Changes are appended to the file.  The last occurrence of an option
    setting in the file is the one used when options file is read.

    A separate line is used for each option setting.  Format is:
    #<option>=<value>
    Leading and trailing whitespace is removed from <value> before use.

    """
    optionsfilename = os.path.join(folder, _options_filename)
    if os.path.exists(optionsfilename):
        if not os.path.isfile(optionsfilename):
            return
    with open(optionsfilename, "a+") as optionsfile:
        defaults = _extract_options(optionsfile)
        olddefaults, newdefaults = changes
        for key, v in olddefaults.items():
            if key in font_names:
                for ak, av in v.items():
                    if av == newdefaults[key][ak]:
                        del newdefaults[key][ak]
                    elif defaults[key].get(ak) == newdefaults[key][ak]:
                        del newdefaults[key][ak]
                if not newdefaults[key]:
                    del newdefaults[key]
            elif v == newdefaults[key]:
                del newdefaults[key]
            elif defaults.get(key) == newdefaults[key]:
                del newdefaults[key]
        newlines = []
        for key, v in newdefaults.items():
            if key in font_names:
                newlines.append("".join((key, "\n")))
                for ak, av in v.items():
                    if ak in fonts.integer_attributes:
                        newlines.append("".join((ak, "=", str(av), "\n")))
                    else:
                        newlines.append("".join((ak, "=", av, "\n")))
            else:
                newlines.append("".join((key, "=", v, "\n")))
        if newlines:
            optionsfile.writelines(newlines)
    return


def _extract_options(fileid):
    """Extract options from fileid and return dictionary of options.

    The last occurrence of each option in the file is returned.

    """
    defaults = {
        constants.LITECOLOR_NAME: None,
        constants.DARKCOLOR_NAME: None,
        constants.WHITECOLOR_NAME: None,
        constants.BLACKCOLOR_NAME: None,
        constants.LINE_COLOR_NAME: None,
        constants.MOVE_COLOR_NAME: None,
        constants.ALTERNATIVE_MOVE_COLOR_NAME: None,
        constants.VARIATION_COLOR_NAME: None,
        constants.MOVES_PLAYED_IN_GAME_FONT: dict(),
        constants.PIECES_ON_BOARD_FONT: dict(),
        constants.WILDPIECES_ON_BOARD_FONT: dict(),
        constants.LISTS_OF_GAMES_FONT: dict(),
        constants.TAGS_VARIATIONS_COMMENTS_FONT: dict(),
    }
    for fa in fonts.modify_font_attributes:
        defaults[fa] = None
    font_details = False
    for line in fileid.readlines():
        text = line.strip()
        if text.startswith("#"):
            continue
        try:
            key_string, v = text.split("=", 1)
        except ValueError:
            key_string, v = text, ""
        key = key_string.strip()
        if key in defaults:
            if key in fonts.modify_font_attributes:
                if font_details:
                    defaults[font_details][key] = v.strip()
                continue
            if font_details:
                font_attributes = defaults[font_details]
                for fa in fonts.modify_font_attributes:
                    if defaults[fa]:
                        font_attributes[fa] = defaults[fa]
                        defaults[fa] = None
                font_details = False
            if key in font_names:
                font_details = key
            else:
                defaults[key] = v.strip()
    for fa in fonts.modify_font_attributes:
        del defaults[fa]
    return defaults
