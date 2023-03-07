# chesslmdbdu.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Symas LMMD."""

from solentware_base import lmdbdu_database
from solentware_base.core.constants import DEFAULT_MAP_PAGES

from ..shared.lmdbdudb import LmdbduDb
from ..shared.lmdbdu import Lmdbdu
from ..shared.alldu import chess_du, Alldu
from ..core import filespec


class ChesslmdbduError(Exception):
    """Exception class for chesslmdbdu module."""


def chess_database_du(dbpath, *args, estimated_number_of_games=0, **kwargs):
    """Open database, import games and close database."""
    chess_du(
        ChessDatabase(
            dbpath,
            allowcreate=True,
            estimated_number_of_games=estimated_number_of_games,
        ),
        *args,
        **kwargs,
    )

    # There are no recoverable file full conditions for Symas LMMD (see DPT).
    return True


class ChessDatabase(Alldu, LmdbduDb, Lmdbdu, lmdbdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, estimated_number_of_games=0, **kargs):
        """Delegate with ChesslmdbduError as exception class."""
        super().__init__(
            DBfile,
            ChesslmdbduError,
            **kargs,
        )
        self.open_database()
        (
            map_bytes, map_pages, used_bytes, used_pages, stats
        ) = self.database_stats_summary()
        self.close_database()
        mfpas = filespec.LMMD_MINIMUM_FREE_PAGES_AT_START
        if map_pages - used_pages < mfpas:
            short = mfpas + map_pages - used_pages
        else:
            short = 0
        self.map_blocks = (
            1
            + (map_pages + short) // DEFAULT_MAP_PAGES
            + estimated_number_of_games // 1000
        )
