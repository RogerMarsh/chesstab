# dbdu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with db.database_du to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..db.database_du import database_du
    from ..core.filespec import GAMES_FILE_DEF

    DirectoryWidget(database_du, "db", file=GAMES_FILE_DEF)
