# database.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using dbm.ndbm."""

from solentware_base import ndbm_database

from ..core import filespec
from ..basecore import database


class Database(database.Database, ndbm_database.Database):
    """Provide access to a dbm.ndbm database of games of chess."""

    _deferred_update_module_name = "chesstab.ndbm.database_du"

    def __init__(
        self,
        nosqlfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        Arguments are passed through to superclass __init__.

        """
        names = filespec.make_filespec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            names,
            nosqlfile,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (
            self.database_file + ".db",
            self.database_file + ".db.commit",
        )
