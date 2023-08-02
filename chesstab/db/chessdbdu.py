# chessdbdu.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Berkeley DB.

This module uses the bsddb3 interface.
"""

import bsddb3.db

from solentware_base import bsddb3du_database

from ..shared.dbdu import Dbdu
from ..shared.alldu import chess_du, Alldu


class Chessbsddb3duError(Exception):
    """Exception class for chessdbdu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Dbdu, bsddb3du_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with Chessbsddb3duError as exception class."""
        super().__init__(
            DBfile,
            Chessbsddb3duError,
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
