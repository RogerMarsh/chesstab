# dbdu_file.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with db.database_du to database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..db.database_du import Database

    FileWidget(Database, "db")
