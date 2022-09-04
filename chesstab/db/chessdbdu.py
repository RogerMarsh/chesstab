# chessdbdu.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Berkeley DB."""

from solentware_base import bsddb3du_database

from ..shared.dbdu import Dbdu
from ..shared.alldu import chess_du, Alldu


class Chessbsddb3duError(Exception):
    """Exception class for chessdbdu module."""


def chess_dbdu(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)

    # There are no recoverable file full conditions for Berkeley DB (see DPT).
    return True


class ChessDatabase(Alldu, Dbdu, bsddb3du_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with Chessbsddb3duError as exception class."""
        super().__init__(DBfile, Chessbsddb3duError, **kargs)
