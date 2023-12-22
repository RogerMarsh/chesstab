# apswdu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with apsw.database_du to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..apsw.database_du import database_du

    DirectoryWidget(database_du, "apsw")
