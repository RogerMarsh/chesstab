# database_du.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Update chess database indicies from PGN in stages on vedis."""

from solentware_base import vedisdu_database

from ..shared import litedu
from ..shared import alldu


class VedisDatabaseduError(Exception):
    """Exception class for vedis.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


# Possibly cannot do this for vedis.
def database_reload_du(dbpath, *args, **kwargs):
    """Open database, import games, reload indicies, and close database."""
    alldu.do_reload_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, vedisdu_database.Database):
    """Provide custom deferred update for a database of games of chess."""

    def __init__(self, vedisfile, **kargs):
        """Delegate with VedisDatabaseduError as exception class."""
        super().__init__(vedisfile, VedisDatabaseduError, **kargs)
