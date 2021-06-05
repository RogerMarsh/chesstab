# gnudu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with gnu.chessgnudu to database."""


if __name__ == "__main__":

    from .directory_widget import DirectoryWidget
    from ..gnu.chessgnudu import chess_gnudu

    DirectoryWidget(chess_gnudu, "dbm.gnu")
