# chesslmdbdu.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for Symas LMMD."""

from solentware_base import lmdbdu_database

from ..shared.litedu import Litedu
from ..shared.alldu import chess_du, Alldu


class ChesslmdbduError(Exception):
    """Exception class for chesslmdbdu module."""


def chess_database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    chess_du(ChessDatabase(dbpath, allowcreate=True), *args, **kwargs)


class ChessDatabase(Alldu, Litedu, lmdbdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with ChesslmdbduError as exception class."""
        super().__init__(DBfile, ChesslmdbduError, **kargs)

        # Assume DEFAULT_MAP_PAGES * 100 is enough for adding 64000 normal
        # sized games: the largest segment size holds 64000 games and a
        # commit is done after every segment.
        self._set_map_blocks_above_used_pages(100)

    def deferred_update_housekeeping(self):
        """Override to check map size and pages used expected page usage.

        The checks are done here because housekeeping happens when segments
        become full, a convenient point for commit and database resize.

        """
        self.commit()
        self._set_map_size_above_used_pages_between_transactions(100)
        self.start_transaction()
