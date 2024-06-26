# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update chess database indicies from PGN in stages for Symas LMDB."""

from solentware_base import lmdbdu_database

from ..shared import litedu
from ..shared import alldu


class LmdbDatabaseduError(Exception):
    """Exception class for lmdb.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


def database_reload_du(dbpath, *args, **kwargs):
    """Open database, import games, reload indicies, and close database."""
    alldu.do_reload_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, lmdbdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, DBfile, **kargs):
        """Delegate with LmdbDatabaseduError as exception class."""
        super().__init__(DBfile, LmdbDatabaseduError, **kargs)

        # Assume DEFAULT_MAP_PAGES * 100 is enough for adding 64000 normal
        # sized games: the largest segment size holds 64000 games and a
        # commit is done after every segment.
        self._set_map_blocks_above_used_pages(100)

    def deferred_update_housekeeping(self):
        """Override to check map size and pages used expected page usage.

        The checks are done here because housekeeping happens when segments
        become full, a convenient point for commit and database resize.

        """
        self._set_map_size_above_used_pages_between_transactions(100)
