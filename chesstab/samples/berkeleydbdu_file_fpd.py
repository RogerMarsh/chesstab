# berkeleydbdu_file_fpd.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with berkeleydb.database_du to one file per database."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..berkeleydb.database_du import Database

    FileWidget(Database, "berkeleydb", file_per_database=True)
