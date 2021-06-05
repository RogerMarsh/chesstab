# unqlitedu_file.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with unqlite.chessunqlitedu to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..unqlite.chessunqlitedu import ChessDatabase

    FileWidget(ChessDatabase, "unqlite")
