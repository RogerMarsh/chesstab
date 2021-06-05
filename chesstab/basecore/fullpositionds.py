# fullpositionds.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for full position index.

The FullPositionDS class in this module supports the apsw, db, and sqlite3,
interfaces to a database.

See the ..dpt.fullpositionds module for the FullPositionDS class for DPT.

"""
from solentware_grid.core.datasourcecursor import DataSourceCursor

from .fullposition import FullPosition


class FullPositionDS(FullPosition, DataSourceCursor):

    """Combine a standard DataSourceCursor with FullPosition."""
