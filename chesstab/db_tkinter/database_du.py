# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update chess database indicies from PGN in stages on Berkeley DB.

This module uses the tcl interface via tkinter.
"""

from solentware_base import db_tkinterdu_database

from ..shared import dbdu
from ..shared import alldu


class DbtkinterDatabaseduError(Exception):
    """Exception class for db_tkinter.database_du module."""


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


class Database(alldu.Alldu, dbdu.Dbdu, db_tkinterdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with DbtkinterDatabaseduError as exception class."""
        super().__init__(
            DBfile,
            DbtkinterDatabaseduError,
            ("-create", "-recover", "-txn", "-private", "-system_mem"),
            **kargs,
        )
