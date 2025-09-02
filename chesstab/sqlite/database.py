# database.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using sqlite3."""

# from sqlite3 import IntegrityError

from solentware_base import sqlite3_database

from ..core import filespec
from ..basecore import database


class Database(database.Database, sqlite3_database.Database):
    """Provide access to a database of games of chess via sqlite3."""

    _deferred_update_module_name = "chesstab.sqlite.database_du"

    def __init__(
        self,
        sqlite3file,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        Arguments are passed through to superclass __init__.

        """
        names = filespec.make_filespec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            names,
            sqlite3file,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete.

        A *-lock file was not seen while updating a test database, but
        one was seen while trying apsw so include that here too just in
        case sqlite3 gets to delete a database handled by apsw.

        """
        return (
            self.database_file,
            self.database_file + "-lock",
            self.database_file + "-journal",
        )
