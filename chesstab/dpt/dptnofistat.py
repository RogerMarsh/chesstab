# dptnofistat.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess games database using DPT database via dptdb.dptapi."""

from solentware_base import dpt_database

from ..core import filespec
from ..basecore import database


class Database(database.Database, dpt_database.Database):
    """Provide access to a dpt database of games of chess."""

    _deferred_update_module_name = "chesstab.dpt.database_du"

    def __init__(
        self,
        databasefolder,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        Arguments are passed through to superclass __init__.

        """
        try:
            sysprint = kargs.pop("sysprint")
        except KeyError:
            sysprint = "CONSOLE"
        ddnames = filespec.make_filespec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            ddnames,
            databasefolder,
            sysprint=sysprint,
            use_specification_items=use_specification_items,
            **kargs,
        )

        self._broken_sizes = {}
