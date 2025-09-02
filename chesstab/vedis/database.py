# database.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using vedis."""

from solentware_base import vedis_database

from ..core import filespec
from ..basecore import database


class Database(database.Database, vedis_database.Database):
    """Provide access to a vedis database of games of chess."""

    _deferred_update_module_name = "chesstab.vedis.database_du"

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
            self.database_file,
            self.database_file + "-lock",
            self.database_file + "_vedis_journal",
        )
