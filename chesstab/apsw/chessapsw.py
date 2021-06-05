# chessapsw.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database using sqlite3.
"""

import os

# from apsw import ConstraintError

from solentware_base import apsw_database
from solentware_base.core.constants import (
    FILEDESC,
)

from ..core.filespec import FileSpec
from ..basecore import database


class ChessDatabaseError(Exception):
    pass


class ChessDatabase(database.Database, apsw_database.Database):

    """Provide access to a database of games of chess."""

    _deferred_update_process = os.path.join(
        os.path.basename(os.path.dirname(__file__)), "runchessapswdu.py"
    )

    def __init__(self, sqlite3file, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        names = FileSpec(**kargs)

        if not kargs.get("allowcreate", False):
            try:
                for t in names:
                    if FILEDESC in names[t]:
                        del names[t][FILEDESC]
            except:
                if __name__ == "__main__":
                    raise
                else:
                    raise ChessDatabaseError("sqlite3 description invalid")

        try:
            super().__init__(names, sqlite3file, **kargs)
        except ChessDatabaseError:
            if __name__ == "__main__":
                raise
            else:
                raise ChessDatabaseError("sqlite3 description invalid")

    def delete_database(self):
        """Close and delete the open chess database."""
        return super().delete_database((self.database_file,))
