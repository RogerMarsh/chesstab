# chesslmdb.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using Symas LMMD."""

import os

from solentware_base import lmdb_database
from solentware_base.core import constants

from ..core.filespec import (
    FileSpec,
    GAMES_FILE_DEF,
    LMMD_MINIMUM_FREE_PAGES_AT_START,
)
from ..basecore import database


class ChessDatabase(database.Database, lmdb_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = os.path.join(
        os.path.basename(os.path.dirname(__file__)), "runchesslmdbdu.py"
    )

    def __init__(
        self,
        DBfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        Arguments are passed through to superclass __init__.

        """
        dbnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(dbnames, folder=DBfile, **kargs)
        self.open_database()
        (
            map_bytes, map_pages, used_bytes, used_pages, stats
        ) = self.database_stats_summary()
        self.close_database()
        self.map_blocks = map_pages // constants.DEFAULT_MAP_PAGES
        if map_pages - used_pages < LMMD_MINIMUM_FREE_PAGES_AT_START:
            short = (
                LMMD_MINIMUM_FREE_PAGES_AT_START + map_pages - used_pages
            )
        else:
            short = 0
        self.map_blocks = (
            1
            + (map_pages + short) // constants.DEFAULT_MAP_PAGES
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file,)
