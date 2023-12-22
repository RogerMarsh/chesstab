# database_du.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for unqlite."""

from solentware_base import unqlitedu_database

from ..shared import litedu
from ..shared import alldu


class UnqliteDatabaseduError(Exception):
    """Exception class for unqlite.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, unqlitedu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, unqlitefile, **kargs):
        """Delegate with UnqliteDatabaseduError as exception class."""
        super().__init__(unqlitefile, UnqliteDatabaseduError, **kargs)