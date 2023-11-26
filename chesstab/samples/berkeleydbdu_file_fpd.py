# berkeleydbdu_file_fpd.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with berkeleydb.chessdbdu to one file per database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..berkeleydb.chessberkeleydbdu import ChessDatabase

    FileWidget(ChessDatabase, "berkeleydb", file_per_database=True)
