# sqlite3du_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with sqlite.database_du to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..sqlite.database_du import database_du
    from ..core.filespec import GAMES_FILE_DEF

    DirectoryWidget(database_du, "sqlite3", file=GAMES_FILE_DEF)
