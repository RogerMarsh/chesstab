# cqlds.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database partial position index using ChessQL.

The ChessQueryLanguageDS class represents a subset of games which match a Chess
Query Language query.

The ChessQueryLanguageDS class in this module supports the DPT interface to a
database.

See the ..basecore.cqlds module for the ChessQueryLanguageDS class for apsw,
db, and sqlite3.

"""

from solentware_grid.dpt.datasourcecursor import DataSourceCursor

from ..basecore.cqlgames import ChessQLGames


class ChessQueryLanguageDS(ChessQLGames, DataSourceCursor):

    """Combine a DPT DataSourceCursor with ChessQLGames."""
