# chesssqlite3.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using sqlite3."""

# from sqlite3 import IntegrityError

from solentware_base import sqlite3_database
from solentware_base.core.constants import (
    FILEDESC,
)

from ..core.filespec import FileSpec
from ..basecore import database


class ChessDatabaseError(Exception):
    """Exception class for chesssqlite3 module."""


class ChessDatabase(database.Database, sqlite3_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = "chesstab.sqlite.chesssqlite3du"

    def __init__(
        self,
        sqlite3file,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        names = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        if not kargs.get("allowcreate", False):
            try:
                for table_name in names:
                    if FILEDESC in names[table_name]:
                        del names[table_name][FILEDESC]
            except Exception as error:
                if __name__ == "__main__":
                    raise
                raise ChessDatabaseError(
                    "sqlite3 description invalid"
                ) from error

        try:
            super().__init__(
                names,
                sqlite3file,
                use_specification_items=use_specification_items,
                **kargs,
            )
        except ChessDatabaseError as error:
            if __name__ == "__main__":
                raise
            raise ChessDatabaseError("sqlite3 description invalid") from error

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file,)
