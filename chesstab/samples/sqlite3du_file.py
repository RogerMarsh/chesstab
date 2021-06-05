# sqlite3du_file.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with sqlite.chesssqlite3du to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..sqlite.chesssqlite3du import ChessDatabase

    FileWidget(ChessDatabase, "sqlite3")
