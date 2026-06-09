# berkeleydbdu_dir.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with berkeleydb.database_du to database."""

if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..berkeleydb.database_du import database_du
    from ..core.filespec import GAMES_FILE_DEF

    DirectoryWidget(database_du, "berkeleydb", file=GAMES_FILE_DEF)
