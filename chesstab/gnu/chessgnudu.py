# chessgnudu.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for dbm.gnu."""

from solentware_base import gnudu_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class ChessgnuduError(Exception):
    """Exception class for chessgnudu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Litedu, gnudu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, gnufile, **kargs):
        """Delegate with ChessgnuduError as exception class."""
        super().__init__(gnufile, ChessgnuduError, **kargs)
