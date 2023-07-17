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

_OPTIONS_FILENAME = "options"


def get_saved_options(folder):
    """Return dictionary of colour and font defaults from options file.

    Return None if options file cannot be read or does not exist.

    """
    optionsfilename = os.path.join(folder, _OPTIONS_FILENAME)
    if not os.path.isfile(optionsfilename):
        return None
    try:
        with open(optionsfilename, "r", encoding="utf-8") as optionsfile:
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
    optionsfilename = os.path.join(folder, _OPTIONS_FILENAME)
    if os.path.exists(optionsfilename):
        if not os.path.isfile(optionsfilename):
            return
    with open(optionsfilename, "a+", encoding="utf-8") as optionsfile:
        defaults = _extract_options(optionsfile)
        olddefaults, newdefaults = changes
        for key, value in olddefaults.items():
            if key in font_names:
                for vikey, vivalue in value.items():
                    if vivalue == newdefaults[key][vikey]:
                        del newdefaults[key][vikey]
                    elif defaults[key].get(vikey) == newdefaults[key][vikey]:
                        del newdefaults[key][vikey]
                if not newdefaults[key]:
                    del newdefaults[key]
            elif value == newdefaults[key]:
                del newdefaults[key]
            elif defaults.get(key) == newdefaults[key]:
                del newdefaults[key]
        newlines = []
        for key, value in newdefaults.items():
            if key in font_names:
                newlines.append("".join((key, "\n")))
                for vikey, vivalue in value.items():
                    if vikey in fonts.integer_attributes:
                        newlines.append(
                            "".join((vikey, "=", str(vivalue), "\n"))
                        )
                    else:
                        newlines.append("".join((vikey, "=", vivalue, "\n")))
            else:
                newlines.append("".join((key, "=", value, "\n")))
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
        constants.MOVES_PLAYED_IN_GAME_FONT: {},
        constants.PIECES_ON_BOARD_FONT: {},
        constants.WILDPIECES_ON_BOARD_FONT: {},
        constants.LISTS_OF_GAMES_FONT: {},
        constants.TAGS_VARIATIONS_COMMENTS_FONT: {},
    }
    for attr in fonts.modify_font_attributes:
        defaults[attr] = None
    font_details = False
    for line in fileid.readlines():
        text = line.strip()
        if text.startswith("#"):
            continue
        try:
            key_string, value_string = text.split("=", 1)
        except ValueError:
            key_string, value_string = text, ""
        key = key_string.strip()
        if key in defaults:
            if key in fonts.modify_font_attributes:
                if font_details:
                    defaults[font_details][key] = value_string.strip()
                continue
            if font_details:
                font_attributes = defaults[font_details]
                for attr in fonts.modify_font_attributes:
                    if defaults[attr]:
                        font_attributes[attr] = defaults[attr]
                        defaults[attr] = None
                font_details = False
            if key in font_names:
                font_details = key
            else:
                defaults[key] = value_string.strip()
    for attr in fonts.modify_font_attributes:
        del defaults[attr]
    return defaults
