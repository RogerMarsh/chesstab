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


class Database(alldu.Alldu, litedu.Litedu, dptdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, databasefolder, **kargs):
        """Delegate with DPTDatabaseduError as exception class."""
        super().__init__(databasefolder, DPTDatabaseduError, **kargs)
