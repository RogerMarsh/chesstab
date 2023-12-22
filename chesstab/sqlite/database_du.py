# database_du.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Sqlite 3.

This module uses the sqlite3 interface.
"""

from solentware_base import sqlite3du_database

from ..shared import litedu
from ..shared import alldu


class Sqlite3DatabaseduError(Exception):
    """Exception class for sqlite.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, sqlite3du_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with Sqlite3DatabaseduError as exception class."""
        super().__init__(sqlite3file, Sqlite3DatabaseduError, **kargs)
