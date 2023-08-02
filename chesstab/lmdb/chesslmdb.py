# chesslmdb.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using Symas LMMD."""

from solentware_base import lmdb_database

from ..core.filespec import FileSpec
from ..basecore import database


class ChessDatabase(database.Database, lmdb_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = "chesstab.lmdb.chesslmdbdu"

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

        # Allow space for lots of chess engine analysis.
        self._set_map_blocks_above_used_pages(200)

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file,)

    def checkpoint_before_close_dbenv(self):
        """Override.  Hijack method to set map size to file size.

        Reverse, to the extent possible, the increase in map size done
        when the database was opened.

        """
        self._set_map_size_above_used_pages_between_transactions(0)
