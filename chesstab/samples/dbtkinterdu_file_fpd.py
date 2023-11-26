# dbtkinterdu_file_fpd.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN with db_tkinter.chessdbtkinterdu to one file per database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..db_tkinter.chessdbtkinterdu import ChessDatabase

    FileWidget(ChessDatabase, "db_tcl", file_per_database=True)
