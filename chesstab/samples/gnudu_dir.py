# gnudu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with gnu.database_du to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..gnu.database_du import database_du

    DirectoryWidget(database_du, "dbm.gnu")
