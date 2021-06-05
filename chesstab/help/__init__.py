# __init__.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Help files for ChessTab.

The options in the Help menu are named in the DATA section below.  Each is
backed by an "rst" file, displayed by invoking the menu option, and a "html"
file generated by "rst2html".

The two file names which are not obvious when viewing the directory "help" are
"keyboard", associated with ACTIONS, and "chesstab", associated with NOTES.
"""

import os

ABOUT = "About"
FILESIZE = "FileSize"
GUIDE = "Guide"
NOTES = "Notes"
SELECTION = "Selection"

_textfile = {
    ABOUT: ("aboutchesstab",),
    FILESIZE: ("filesize",),
    GUIDE: ("guide",),
    NOTES: ("chesstab",),
    SELECTION: ("selection",),
}

# Usually help files are in .../site_packages/chesstab/help but when running
# an executable generated by py2exe installed by Inno installer this module
# is in .../ChessTab/library.zip/chesstab while the help files are in
# .../ChessTab/help
folder = os.path.dirname(__file__).replace(
    os.path.join("ChessTab", "library.zip", "chesstab"), "ChessTab"
)

for k in list(_textfile.keys()):
    _textfile[k] = tuple(
        [os.path.join(folder, ".".join((n, "rst"))) for n in _textfile[k]]
    )

del folder, k, os
