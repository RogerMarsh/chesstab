# unqlitedu_file.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with unqlite.database_du to database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..unqlite.database_du import Database

    FileWidget(Database, "unqlite")
