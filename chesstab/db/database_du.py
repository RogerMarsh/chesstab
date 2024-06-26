# database_du.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update chess database indicies from PGN in stages on Berkeley DB.

This module uses the bsddb3 interface.
"""

# pylint gives import-error message, E0401, if bsddb3 is not installed.
# It is reasonable to not install bsddb3.
# The importlib module is used elsewhere to import bsddb3 if needed.
import bsddb3.db

from solentware_base import bsddb3du_database

from ..shared import dbdu
from ..shared import alldu


class Bsddb3DatabaseduError(Exception):
    """Exception class for db.database_du module."""


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


class Database(alldu.Alldu, dbdu.Dbdu, bsddb3du_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with Bsddb3DatabaseduError as exception class."""
        super().__init__(
            DBfile,
            Bsddb3DatabaseduError,
            (
                bsddb3.db.DB_CREATE
                | bsddb3.db.DB_RECOVER
                | bsddb3.db.DB_INIT_MPOOL
                | bsddb3.db.DB_INIT_LOCK
                | bsddb3.db.DB_INIT_LOG
                | bsddb3.db.DB_INIT_TXN
                | bsddb3.db.DB_PRIVATE
            ),
            **kargs
        )
