# lmdbdudb.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The LmdbduDb class for lmdb interface to Symas LMMD.

This module uses the solentware_base.core._lmdb Database class.

"""

from solentware_base.core._lmdb import Database

from .dptcompatdu import DptCompatdu


class LmdbduDb(DptCompatdu, Database):
    """Provide deferred update methods shared by Symas LMMD interfaces."""
