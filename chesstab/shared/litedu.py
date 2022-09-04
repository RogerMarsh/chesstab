# litedu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The Litedu class for methods shared by <*>lite and dbm interface modules.

Most of the interface modules that can use the Litedu module have 'lite' in
their name.

This module is relevant to the apsw and sqlite3 interfaces to Sqlite3, and
to the gnu, ndbm, unqlite, and vedis, interfaces to their respective
'key:value' databases.

"""

import os

from .archivedu import Archivedu
from .alldu import get_filespec
from .dptcompatdu import DptCompatdu


class Litedu(DptCompatdu, Archivedu):
    """Provide deferred update methods shared by various interfaces.

    All the supported engines put the whole database in a single file so
    can use the same methods to manage temporary backups which may exist
    while opening and checking the database.
    """

    def __init__(self, databasefile, exception_class, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        assert issubclass(exception_class, Exception)
        try:
            names = get_filespec(**kargs)
        except Exception:
            if __name__ == "__main__":
                raise
            raise exception_class("database description invalid")

        try:
            super().__init__(names, databasefile, **kargs)
        except Exception:
            if __name__ == "__main__":
                raise
            raise exception_class("unable to initialize database object")

    def open_context_prepare_import(self):
        """Return True.

        No preparation actions thet need database open for vedis.

        """
        return True

    def get_archive_names(self, files=()):
        """Return vedis database file and existing operating system files."""
        names = [self.database_file]
        exists = [
            os.path.basename(n)
            for n in names
            if os.path.exists(".".join((n, "bz2")))
        ]
        return (names, exists)
