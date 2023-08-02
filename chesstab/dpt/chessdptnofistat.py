# chessdptnofistat.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess games database using DPT database via dptdb.dptapi."""

from solentware_base import dpt_database
from solentware_base.core.constants import FILEDESC

from .filespec import FileSpec
from ..basecore import database


class ChessdptError(Exception):
    """Exception class for chessdptnofistat module."""


class ChessDatabase(database.Database, dpt_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = "chesstab.dpt.chessdptdu"

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
        try:
            sysprint = kargs.pop("sysprint")
        except KeyError:
            sysprint = "CONSOLE"
        ddnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        if not kargs.get("allowcreate", False):
            try:
                for dd_name in ddnames:
                    if FILEDESC in ddnames[dd_name]:
                        del ddnames[dd_name][FILEDESC]
            except Exception as error:
                if __name__ == "__main__":
                    raise
                raise ChessdptError("DPT description invalid") from error

        try:
            super().__init__(
                ddnames, databasefolder, sysprint=sysprint, **kargs
            )
        except ChessdptError as error:
            if __name__ == "__main__":
                raise
            raise ChessdptError("DPT description invalid") from error

        self._broken_sizes = {}
