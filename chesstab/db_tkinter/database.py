# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using Berkeley DB.

The Berkeley DB interface has significantly worse performance than DPT when
doing multi-index searches.  However it is retained since DPT became available
because tracking down problems in the chess logic using IDLE can be easier
in the *nix environment.
"""

from solentware_base import db_tkinter_database

from ..core.filespec import (
    make_filespec,
    DB_ENVIRONMENT_GIGABYTES,
    DB_ENVIRONMENT_BYTES,
    DB_ENVIRONMENT_MAXLOCKS,
    DB_ENVIRONMENT_MAXOBJECTS,
)
from ..basecore import database


class Database(database.Database, db_tkinter_database.Database):
    """Provide access to a database of games of chess via tkinter."""

    _deferred_update_module_name = "chesstab.db_tkinter.database_du"

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
        dbnames = make_filespec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        environment = {
            "flags": (
                "-create",
                "-recover",
                "-txn",
                "-private",
                "-system_mem",
            ),
            "gbytes": DB_ENVIRONMENT_GIGABYTES,
            "bytes": DB_ENVIRONMENT_BYTES,
            "maxlocks": DB_ENVIRONMENT_MAXLOCKS,
            "maxobjects": DB_ENVIRONMENT_MAXOBJECTS,
        }

        super().__init__(
            dbnames,
            folder=DBfile,
            environment=environment,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (
            self.database_file,
            self._get_log_dir_name(),
            self.database_file + "-lock",
        )
