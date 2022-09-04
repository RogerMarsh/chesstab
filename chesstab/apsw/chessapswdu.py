# chessapswdu.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for sqlite3."""

from solentware_base import apswdu_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class ChessapswduError(Exception):
    """Exception class for chessapswdu module."""


def chess_sqlite3du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)

    # There are no recoverable file full conditions for sqlite3 (see DPT).
    return True


# 'def chess_sqlite3du' will be changed to 'def chess_database_du' some time.
chess_database_du = chess_sqlite3du


class ChessDatabase(Alldu, Litedu, apswdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with ChessapswduError as exception class."""
        super().__init__(sqlite3file, ChessapswduError, **kargs)
