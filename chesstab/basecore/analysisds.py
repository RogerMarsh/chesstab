# analysisds.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for chess engine analysis index.

The AnalysisDS class in this module supports the apsw, db, and sqlite3,
interfaces to a database.

See the ..dpt.analysisds module for the AnalysisDS class for DPT.

"""
from solentware_grid.core.datasourcecursor import DataSourceCursor

from .analysis import Analysis


class AnalysisDS(Analysis, DataSourceCursor):

    """Combine a standard DataSourceCursor with Analysis."""
