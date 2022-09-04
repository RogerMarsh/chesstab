# chessberkeleydbdu.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Berkeley DB."""

from solentware_base import berkeleydbdu_database

from ..shared.dbdu import Dbdu
from ..shared.alldu import chess_du, Alldu


class ChessberkeleydbduError(Exception):
    """Exception class for chessberkeleydbdu module."""


def chess_dbdu():
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)

    # There are no recoverable file full conditions for Berkeley DB (see DPT).
    return True


class ChessDatabase(Alldu, Dbdu, berkeleydbdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with ChessberkeleydbduError as exception class."""
        super().__init__(DBfile, ChessberkeleydbduError, **kargs)
