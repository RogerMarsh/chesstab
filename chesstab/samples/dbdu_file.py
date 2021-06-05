# dbdu_file.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with db.chessdbdu to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..db.chessdbdu import ChessDatabase

    FileWidget(ChessDatabase, "db")
