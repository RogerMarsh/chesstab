# database_du.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for dbm.gnu."""

from solentware_base import gnudu_database

from ..shared import litedu
from ..shared import alldu


class DbmGnuDatabaseduError(Exception):
    """Exception class for gnu.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, gnudu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, gnufile, **kargs):
        """Delegate with DbmGnuDatabaseduError as exception class."""
        super().__init__(gnufile, DbmGnuDatabaseduError, **kargs)
