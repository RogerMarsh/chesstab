# dbtkinterdu_dir.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with db_tkinter.chessdbtkinterdu module."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..db_tkinter.chessdbtkinterdu import chess_database_du

    DirectoryWidget(chess_database_du, "db_tcl")
