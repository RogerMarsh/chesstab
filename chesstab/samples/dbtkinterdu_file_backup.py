# dbtkinterdu_file_backup.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with db_tkinter.chessdbtkinterdu with backup and fpd.

fpd: one file for each database.
"""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..db_tkinter import chessdbtkinterdu

    class ChessDatabase(chessdbtkinterdu.ChessDatabase):
        """Customise Berkeley DB database for one file per database."""

        _take_backup_before_deferred_update = True

    FileWidget(ChessDatabase, "db_tcl")
