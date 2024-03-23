# database.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using sqlite3."""

# from apsw import ConstraintError

from solentware_base import apsw_database

from ..core.filespec import FileSpec
from ..basecore import database


class Database(database.Database, apsw_database.Database):
    """Provide access to a database of games of chess via apsw."""

    _deferred_update_process = "chesstab.apsw.database_du"

    def __init__(
        self,
        sqlite3file,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        names = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            names,
            sqlite3file,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file,)
