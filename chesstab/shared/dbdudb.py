# dbdudb.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The DbduDb class for berkeleydb and bsddb3 interfaces to Berkeley DB.

This module uses the solentware_base.core._db Database class.

"""

from solentware_base.core._db import Database

from .dptcompatdu import DptCompatdu


class DbduDb(DptCompatdu, Database):
    """Provide deferred update methods shared by Berkeley DB interfaces."""
