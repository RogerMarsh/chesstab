# berkeleydbdu_file_fpd_backup.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with berkeleydb.chessberkeleydbdu with backup and fpd.

fpd: one file for each database.
"""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..berkeleydb import chessberkeleydbdu

    class ChessDatabase(chessberkeleydbdu.ChessDatabase):
        """Customise Berkeley DB database for backup before import."""

        _take_backup_before_deferred_update = True

    FileWidget(ChessDatabase, "berkeleydb", file_per_database=True)
