"""User interface to a chess game database.

Module "chess" is the top-level module.

Module "chess_ui" controls the User Interface.

Module "chessdu" is the top-level module in sub-processes started to import
data from PGN files.

Four sets of modules provide the user interface for games, repertoires, partial
positions, and selection rules.  Some repertoire classes are defined in the
corresponding game module rather than a repertoire module.  The absence of
modules called "repertoire", "repertoireedit", and "repertoiregrid", indicates
which ones.

The remaining modules provide supporting facilities.
"""
