# dbtkinterdu_dir.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with db_tkinter.database_du module."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..db_tkinter.database_du import database_du

    DirectoryWidget(database_du, "db_tcl")
