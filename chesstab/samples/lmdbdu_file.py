# lmdbdu_file.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with lmdb.chessdbdu to database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..lmdb.chesslmdbdu import ChessDatabase

    FileWidget(ChessDatabase, "db")
