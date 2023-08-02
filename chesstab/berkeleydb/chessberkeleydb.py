# chessberkeleydb.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using Berkeley DB.

The Berkeley DB interface has significantly worse performance than DPT when
doing multi-index searches.  However it is retained since DPT became available
because tracking down problems in the chess logic using IDLE can be easier
in the *nix environment.
"""

# pylint will give import-error message if berkeleydb is not installed.
# It is reasonable to not install Python package 'berkeleydb'.
# The importlib module is used to import chessberkeleydb if needed.
from berkeleydb.db import (
    DB_CREATE,
    DB_RECOVER,
    DB_INIT_MPOOL,
    DB_INIT_LOCK,
    DB_INIT_LOG,
    DB_INIT_TXN,
    DB_PRIVATE,
)

from solentware_base import berkeleydb_database

from ..core.filespec import (
    FileSpec,
    DB_ENVIRONMENT_GIGABYTES,
    DB_ENVIRONMENT_BYTES,
    DB_ENVIRONMENT_MAXLOCKS,
)
from ..basecore import database


class ChessDatabase(database.Database, berkeleydb_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = "chesstab.berkeleydb.chessberkeleydbdu"

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

        environment = {
            "flags": (
                DB_CREATE
                | DB_RECOVER
                | DB_INIT_MPOOL
                | DB_INIT_LOCK
                | DB_INIT_LOG
                | DB_INIT_TXN
                | DB_PRIVATE
            ),
            "gbytes": DB_ENVIRONMENT_GIGABYTES,
            "bytes": DB_ENVIRONMENT_BYTES,
            "maxlocks": DB_ENVIRONMENT_MAXLOCKS,
        }

        super().__init__(
            dbnames, folder=DBfile, environment=environment, **kargs
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file, self.dbenv.get_lg_dir().decode())
