# berkeleydbdu_file_fpd_backup.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with berkeleydb.database_du with backup and fpd.

fpd: one file for each database.
"""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..berkeleydb import database_du

    class Database(database_du.Database):
        """Customise Berkeley DB database for backup before import."""

    FileWidget(Database, "berkeleydb", file_per_database=True)
