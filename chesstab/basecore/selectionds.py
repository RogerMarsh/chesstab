# selectionds.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for selection rules index.

The SelectionDS class in this module supports the apsw, db, and sqlite3,
interfaces to a database.

See the ..dpt.selectionds module for the SelectionDS class for DPT.

"""

from solentware_grid.core.datasourcecursor import DataSourceCursor

from .selection import Selection


class SelectionDS(Selection, DataSourceCursor):

    """Combine a standard DataSourceCursor with Selection."""
