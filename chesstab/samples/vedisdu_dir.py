# vedisdu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with vedis.chessvedisdu to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..vedis.chessvedisdu import chess_database_du

    DirectoryWidget(chess_database_du, "vedis")
