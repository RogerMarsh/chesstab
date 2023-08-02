# chesssqlite3du.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Sqlite 3.

This module uses the sqlite3 interface.
"""

from solentware_base import sqlite3du_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class Chesssqlite3duError(Exception):
    """Exception class for chesssqlite3du module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Litedu, sqlite3du_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with Chesssqlite3duError as exception class."""
        super().__init__(sqlite3file, Chesssqlite3duError, **kargs)
