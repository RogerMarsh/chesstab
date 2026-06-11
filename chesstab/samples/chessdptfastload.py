# chessdptfastload.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using DPT fastload.

This module on Windows only.

See www.dptoolkit.com for details of DPT.

"""

import os
import multiprocessing  # Removed later by 'del multiprocessing'.

import tkinter
import tkinter.messagebox

# pylint will always give import-error message on non-Microsoft Windows
# systems.
# Wine counts as a Microsft Windows system.
# It is reasonable to not install 'dpt_dbms.dptapi'.
# The importlib module is used to import database_du if needed.
from dpt_dbms.dptapi import FISTAT_DEFERRED_UPDATES

from solentware_base import dptfastload_database
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    TABLE_B_SIZE,
)

from ..core.filespec import (
    make_filespec,
    GAMES_FILE_DEF,
    PIECES_PER_POSITION,
    POSITIONS_PER_GAME,
)

# The DPT segment size is 65280 because 32 bytes are reserved and 8160 bytes of
# the 8192 byte page are used for the bitmap.
# DB_SEGMENT_SIZE has no effect on processing apart from report points.
DB_SEGMENT_SIZE = 65280
_DEFERRED_UPDATE_POINTS = (DB_SEGMENT_SIZE - 1,)
del DB_SEGMENT_SIZE


class ChessdptfastloadError(Exception):
    """Exception class for chessdptfastload module."""


class Database(dptfastload_database.Database):
    """Provide fast load deferred methods for a database of games of chess.

    Subclasses must include a subclass of dptbase.Database as a superclass.

    """

    # deferred_update_points is the existing name but here it signifies
    # the interval at which a fastload call updates the database.
    # The number is arbitrary in relation to segment sizes since there may
    # be gaps in the record number sequence due to long games preventing
    # all slots in a page being used.
    deferred_update_points = frozenset(_DEFERRED_UPDATE_POINTS)

    def __init__(
        self,
        databasefolder,
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
        ddnames = make_filespec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )
        # Deferred update for games file only
        # for ddname in list(ddnames.keys()):
        #     if ddname != GAMES_FILE_DEF:
        #         del ddnames[ddname]

        if not kargs.get("allowcreate", False):
            try:
                for ddname in ddnames:
                    if FILEDESC in ddnames[ddname]:
                        del ddnames[ddname][FILEDESC]
            except Exception as error:
                if __name__ == "__main__":
                    raise
                raise ChessdptfastloadError(
                    "DPT description invalid"
                ) from error

        try:
            super().__init__(ddnames, databasefolder, **kargs)
        except ChessdptfastloadError as error:
            if __name__ == "__main__":
                raise
            raise ChessdptfastloadError("DPT description invalid") from error

        # Methods passed by UI to populate report widgets
        self._reporter = None

    def open_database(self, files=None):
        """Delegate then return None if database in deferred update mode.

        Close the database and raise ChessdptfastloadError exception if the
        database FISTAT parameter is not equal FISTAT_DEFERRED_UPDATES.

        """
        super().open_database(files=files)
        viewer = self.dbenv.Core().GetViewerResetter()
        for dbo in self.table.values():
            if viewer.ViewAsInt("FISTAT", dbo.opencontext):
                break
        else:
            if files is None:
                files = dict()
            self.increase_database_size(files=files)
            return
        self.close_database()
        raise ChessdptfastloadError("A file is not in deferred update mode")
