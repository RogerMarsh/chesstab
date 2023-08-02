# chessunqlitedu.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for unqlite."""

from solentware_base import unqlitedu_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class ChessunqliteduError(Exception):
    """Exception class for chessunqlitedu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Litedu, unqlitedu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, unqlitefile, **kargs):
        """Delegate with ChessunqliteduError as exception class."""
        super().__init__(unqlitefile, ChessunqliteduError, **kargs)
