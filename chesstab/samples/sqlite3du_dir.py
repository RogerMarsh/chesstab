# sqlite3du_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with sqlite.chesssqlite3du to database."""


if __name__ == "__main__":

    from .directory_widget import DirectoryWidget
    from ..sqlite.chesssqlite3du import chess_sqlite3du

    DirectoryWidget(chess_sqlite3du, "sqlite3")
