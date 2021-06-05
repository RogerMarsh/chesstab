# gnudu_file.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with gnu.chessgnudu to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..gnu.chessgnudu import ChessDatabase

    FileWidget(ChessDatabase, "dbm.gnu")
