# dbdu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with db.chessdbdu to database."""


if __name__ == "__main__":

    from .directory_widget import DirectoryWidget
    from ..db.chessdbdu import chess_dbdu

    DirectoryWidget(chess_dbdu, "db")
