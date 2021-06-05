# cqlds.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database partial position index using ChessQL.

The ChessQueryLanguageDS class represents a subset of games which match a Chess
Query Language query.

The ChessQueryLanguageDS class in this module supports the apsw, db, and
sqlite3, interfaces to a database.

See the ..dpt.cqlds module for the ChessQueryLanguageDS class for DPT.

"""

from solentware_grid.core.datasourcecursor import DataSourceCursor

from .cqlgames import ChessQLGames


class ChessQueryLanguageDS(ChessQLGames, DataSourceCursor):

    """Combine a standard DataSourceCursor with ChessQLGames."""
