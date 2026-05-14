# unqlitedu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with unqlite.database_du to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..unqlite.database_du import database_du
    from ..core.filespec import GAMES_FILE_DEF

    DirectoryWidget(database_du, "unqlite", file=GAMES_FILE_DEF)
