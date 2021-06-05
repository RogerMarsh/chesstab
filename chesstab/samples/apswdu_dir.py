# apswdu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with apsw.chessapswdu to database."""


if __name__ == "__main__":

    from .directory_widget import DirectoryWidget
    from ..apsw.chessapswdu import chess_sqlite3du

    DirectoryWidget(chess_sqlite3du, "apsw")
