# dbtkinterdu_file.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with db_tkinter.database_du module."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..db_tkinter.database_du import Database

    FileWidget(Database, "db_tcl")
