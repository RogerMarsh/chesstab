# chessdbtkinter.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using Berkeley DB.

The Berkeley DB interface has significantly worse performance than DPT when
doing multi-index searches.  However it is retained since DPT became available
because tracking down problems in the chess logic using IDLE can be easier
in the *nix environment.
"""

import os

from solentware_base import db_tkinter_database

from ..core.filespec import (
    FileSpec,
    DB_ENVIRONMENT_GIGABYTES,
    DB_ENVIRONMENT_BYTES,
    DB_ENVIRONMENT_MAXLOCKS,
)
from ..basecore import database


class ChessDatabase(database.Database, db_tkinter_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = os.path.join(
        os.path.basename(os.path.dirname(__file__)), "runchessdbtkinterdu.py"
    )

    def __init__(self, DBfile, **kargs):
        """Define chess database.

        **kargs
        Arguments are passed through to superclass __init__.

        """
        dbnames = FileSpec(**kargs)

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
        }

        super().__init__(
            dbnames, folder=DBfile, environment=environment, **kargs
        )

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        return (self.database_file, self._get_log_dir_name())
