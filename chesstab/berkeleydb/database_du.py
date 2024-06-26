# database_du.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update chess database indicies from PGN in stages on Berkeley DB.

This module uses the berkeleydb interface.
"""

# pylint gives import-error message, E0401, if berkeleydb is not installed.
# It is reasonable to not install berkeleydb.
# The importlib module is used elsewhere to import berkeleydb if needed.
import berkeleydb.db

from solentware_base import berkeleydbdu_database

from ..shared import dbdu
from ..shared import alldu


class BerkeleydbDatabaseduError(Exception):
    """Exception class for berkeleydb.database_du module."""


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


class Database(alldu.Alldu, dbdu.Dbdu, berkeleydbdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with BerkeleydbDatabaseduError as exception class."""
        super().__init__(
            DBfile,
            BerkeleydbDatabaseduError,
            (
                berkeleydb.db.DB_CREATE
                | berkeleydb.db.DB_RECOVER
                | berkeleydb.db.DB_INIT_MPOOL
                | berkeleydb.db.DB_INIT_LOCK
                | berkeleydb.db.DB_INIT_LOG
                | berkeleydb.db.DB_INIT_TXN
                | berkeleydb.db.DB_PRIVATE
            ),
            **kargs
        )
