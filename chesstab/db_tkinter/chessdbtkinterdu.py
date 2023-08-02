# chessdbtkinterdu.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Berkeley DB.

This module uses the tcl interface via tkinter.
"""

from solentware_base import db_tkinterdu_database

from ..shared.dbdu import Dbdu
from ..shared.alldu import chess_du, Alldu


class ChessdbtkinterduError(Exception):
    """Exception class for chessdbdu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Dbdu, db_tkinterdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with ChessdbtkinterduError as exception class."""
        super().__init__(
            DBfile,
            ChessdbtkinterduError,
            ("-create", "-recover", "-txn", "-private", "-system_mem"),
            **kargs
        )
