# berkeleydbdu_dir.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with berkeleydb.chessdbdu to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..berkeleydb.chessberkeleydbdu import chess_database_du

    DirectoryWidget(chess_database_du, "berkeleydb")
