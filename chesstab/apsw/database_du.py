# database_du.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update chess database indicies from PGN in stages on Sqlite 3.

This module uses the apsw interface.
"""

from solentware_base import apswdu_database

from ..shared import litedu
from ..shared import alldu


class ApswDatabaseduError(Exception):
    """Exception class for apsw.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


def database_reload_du(dbpath, *args, **kwargs):
    """Open database, import games, reload indicies, and close database."""
    alldu.do_reload_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, apswdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with ApswDatabaseduError as exception class."""
        super().__init__(sqlite3file, ApswDatabaseduError, **kargs)
