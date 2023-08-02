# chessberkeleydbdu.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Berkeley DB.

This module uses the berkeleydb interface.
"""

import berkeleydb.db

from solentware_base import berkeleydbdu_database

from ..shared.dbdu import Dbdu
from ..shared.alldu import chess_du, Alldu


class ChessberkeleydbduError(Exception):
    """Exception class for chessberkeleydbdu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Dbdu, berkeleydbdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with ChessberkeleydbduError as exception class."""
        super().__init__(
            DBfile,
            ChessberkeleydbduError,
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
