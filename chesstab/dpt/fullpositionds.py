# fullpositionds.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for full position index.

The FullPositionDS class in this module supports the apsw, db, and sqlite3,
interfaces to a database.

See the ..basecore.fullposition module for the FullPositionDS class for apsw,
db, and sqlite3.

"""

from solentware_grid.dpt.datasourcecursor import DataSourceCursor

from ..basecore.fullposition import FullPosition


class FullPositionDS(FullPosition, DataSourceCursor):

    """Combine a DPT DataSourceCursor with FullPosition."""
