# dptdu_dir_713.py
# Copyright 2026 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with dpt.database_one_step_du module.

The import algorithm is from ChessTab-7.1.3 but applied to the modified
database structure.
"""

if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..dpt.database_one_step_du import database_du
    from ..core.filespec import GAMES_FILE_DEF

    DirectoryWidget(database_du, "dpt", file=GAMES_FILE_DEF)
