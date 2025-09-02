# cqlds.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database CQL query index using ChessQL.

The ChessQueryLanguageDS class represents a subset of games which match a Chess
Query Language query.

The ChessQueryLanguageDS class in this module supports the apsw, db, and
sqlite3, interfaces to a database.

"""

from solentware_grid.core.datasourcecursor import DataSourceCursor

from ..core import filespec


class ChessQueryLanguageDS(DataSourceCursor):
    """Combine a standard DataSourceCursor with ChessQLGames."""

    def get_cql_statement_games(self, query, recno, commit=True):
        """Find game records matching ChessQL statement.

        query is detail extracted from query statement.
        recno is previously calculated answer.  Set to None to force
        recalculation from query (after editing query statement usually).
        initial_recordset is games to which query is applied.

        """
        del commit
        if query is None or recno is None:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return
        self.dbhome.start_read_only_transaction()
        try:
            games = self.dbhome.recordlist_key(
                self.dbset,
                filespec.CQL_QUERY_FIELD_DEF,
                key=self.dbhome.encode_record_number(recno),
            )

            # Hand the list of games over to the user interface.
            self.set_recordset(games)
        finally:
            self.dbhome.end_read_only_transaction()
