# database_du.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using DPT single-step deferred update.

This module on Windows only.  Use multi-step module on Wine because Wine
support for a critical function used by single-step is not reliable. There
is no sure way to spot that module is running on Wine.

See www.dptoolkit.com for details of DPT

"""
import os

from solentware_base import dptdu_database

from ..shared import litedu
from ..shared import alldu


class DPTDatabaseduError(Exception):
    """Exception class for dpt.database_du module."""


def database_du(dbpath, *args, **kwargs):
    """Open database, import games and close database."""
    # sysfolder argument defaults to DPT_SYSDU_FOLDER in dptdu_database.
    alldu.do_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


# Possibly cannot doe this for DPT since segments are managed internally.
def database_reload_du(dbpath, *args, **kwargs):
    """Open database, import games, reload indicies, and close database."""
    # sysfolder argument defaults to DPT_SYSDU_FOLDER in dptdu_database.
    alldu.do_reload_deferred_update(
        Database(dbpath, allowcreate=True), *args, **kwargs
    )


class Database(alldu.Alldu, litedu.Litedu, dptdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, databasefolder, **kargs):
        """Delegate with DPTDatabaseduError as exception class."""
        super().__init__(databasefolder, DPTDatabaseduError, **kargs)

    # Set default parameters for normal use.
    # This is also in solentware_base.core._dpt.Database but overridden in
    # dptdu_database.Database class.
    def create_default_parms(self):
        """Create default parms.ini file for normal mode.

        This means transactions are enabled and a large number of DPT buffers.

        """
        if not os.path.exists(self.parms):
            with open(self.parms, "w", encoding="iso-8859-1") as parms:
                parms.write("MAXBUF=10000 " + os.linesep)

    def edit_instance(self, dbset, instance):
        """Edit an instance is available in deferred update mode.

        ChessTab is not using the deferred update OpenContext methods
        and is using edit_instance in the deferred_update path.

        """
        super(dptdu_database.Database, self).edit_instance(dbset, instance)

    def _dptfileclass(self):
        return DPTFile


class DPTFile(dptdu_database.DPTFile):
    """This class is used to access files in a DPT database.

    Instances are created as necessary by a Database.open_database() call.

    Some methods in dptdu_database.DPTFile are overridden to provide normal
    update mode instead of single-step deferred update mode.

    """

    # Call dbenv.OpenContext by default.
    # This is also in solentware_base.core._dpt.DPTFile but overridden in
    # dptdu_database.DPTFile class.
    def _open_context(self, dbenv, context_specification):
        return dbenv.OpenContext(context_specification)

    def edit_instance(self, instance):
        """Edit an existing instance on database.

        ChessTab is not using the deferred update OpenContext methods
        and is using edit_instance in the deferred_update path.

        """
        super(dptdu_database.DPTFile, self).edit_instance(instance)
