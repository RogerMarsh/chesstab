# selectionds.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for selection rules index.

The SelectionDS class in this module supports the DPT interface to a database.

See the ..basecore.selectionds module for the SelectionDS class for apsw,
db, and sqlite3.

"""

from solentware_grid.dpt.datasourcecursor import DataSourceCursor

from ..basecore.selection import Selection


class SelectionDS(Selection, DataSourceCursor):

    """Combine a DPT DataSourceCursor with Selection."""
