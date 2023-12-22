# dbtkinterdu_file_fpd.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN with db_tkinter.database_du to one file per database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..db_tkinter.database_du import Database

    FileWidget(Database, "db_tcl", file_per_database=True)
