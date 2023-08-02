# chessndbmdu.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for dbm.ndbm."""

from solentware_base import ndbmdu_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class ChessndbmduError(Exception):
    """Exception class for chessndbmdu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Litedu, ndbmdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, ndbmfile, **kargs):
        """Delegate with ChessndbmduError as exception class."""
        super().__init__(ndbmfile, ChessndbmduError, **kargs)
