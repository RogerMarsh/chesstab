# analysisds.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for chess engine analysis index.

The AnalysisDS class in this module supports the DPT interface to a database.

See the ..basecore.analysisds module for the AnalysisDS class for apsw, db,
and sqlite3.

"""

from solentware_grid.dpt.datasourcecursor import DataSourceCursor

from ..basecore.analysis import Analysis


class AnalysisDS(Analysis, DataSourceCursor):

    """Combine a DPT DataSourceCursor with Analysis."""
