# chessvedisdu.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for vedis."""

from solentware_base import vedisdu_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class ChessvedisduError(Exception):
    """Exception class for chessvedisdu module."""


def chess_database_du(dbpath, *args, estimated_number_of_games=0, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)

    # There are no recoverable file full conditions for vedis (see DPT).
    return True


class ChessDatabase(Alldu, Litedu, vedisdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, vedisfile, **kargs):
        """Delegate with ChessvedisduError as exception class."""
        super().__init__(vedisfile, ChessvedisduError, **kargs)
