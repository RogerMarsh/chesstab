# cqlbase.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Access database records containing lists of games matching queries."""

from ..core.filespec import (
    NEWGAMES_FIELD_DEF,
    PARTIAL_FILE_DEF,
    NEWGAMES_FIELD_VALUE,
    PARTIALPOSITION_FIELD_DEF,
)


class ChessQLBase:
    """Represent subset of games that match a Chess Query Language query."""

    def __init__(self, *a, **k):
        """Delete then create Find instance for queries."""
        super().__init__(*a, **k)

        self.not_implemented = set()

    def forget_cql_statement_games(self, sourceobject, commit=True):
        """Forget game records matching ChessQL statement.

        sourceobject is partial position record instance for cql query.
        commit indicates if this method should start and commit transaction.

        """
        # This instruction to pylint was not needed when this method was
        # defined in cqlgames.ChessQLGames before cqlbase existed.
        # pylint: disable=no-member
        if commit:
            self.dbhome.start_transaction()
        # Forget the list of games under the query key.
        ppview = self.dbhome.recordlist_record_number(
            PARTIAL_FILE_DEF, key=sourceobject.key.recno
        )
        self.dbhome.unfile_records_under(
            self.dbset,
            PARTIALPOSITION_FIELD_DEF,
            self.dbhome.encode_record_number(sourceobject.key.recno),
        )

        # Remove query from set that needs recalculating.
        changed = self.dbhome.recordlist_key(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        changed.remove_recordset(ppview)

        self.dbhome.file_records_under(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            changed,
            self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        if commit:
            self.dbhome.commit()

    def update_cql_statement_games(
        self, sourceobject, initial_recordset=None, commit=True
    ):
        """Find game records matching ChessQL statement and store on database.

        sourceobject is partial position record instance for cql query.
        initial_recordset is games to which query is applied
        commit indicates if this method should start and commit transaction.

        """
        # This instruction to pylint was not needed when this method was
        # defined in cqlgames.ChessQLGames before cqlbase existed.
        # pylint: disable=no-member
        assert sourceobject is not None
        # Evaluate query.
        if commit:
            self.dbhome.start_read_only_transaction()
        if initial_recordset is None:
            initial_recordlist = self.dbhome.recordlist_ebm(self.dbset)
        else:
            initial_recordlist = self.dbhome.recordlist_nil(self.dbset)
            initial_recordlist |= initial_recordset
        query = sourceobject.value
        games = self._get_games_matching_filters(
            query, initial_recordlist, commit=False
        )

        # File the list of games under the query key.
        ppview = self.dbhome.recordlist_record_number(
            PARTIAL_FILE_DEF, key=sourceobject.key.recno
        )
        # The read-only transaction is added for Symas LMMD.
        # The read-write transaction start is not moved to read-only start
        # to preserve the transaction boundaries in the other database
        # engines.  (Moving it should be ok though.)
        if commit:
            self.dbhome.end_read_only_transaction()
        if commit:
            self.dbhome.start_transaction()
        self.dbhome.file_records_under(
            self.dbset,
            PARTIALPOSITION_FIELD_DEF,
            games,
            self.dbhome.encode_record_number(sourceobject.key.recno),
        )

        # Remove query from set that needs recalculating.
        changed = self.dbhome.recordlist_key(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        changed.remove_recordset(ppview)

        self.dbhome.file_records_under(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            changed,
            self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        if commit:
            self.dbhome.commit()

        # Hand the list of games over to the user interface.
        self.set_recordset(games)

    def get_cql_statement_games(
        self, query, sourceobject, initial_recordset=None, commit=True
    ):
        """Find game records matching ChessQL statement.

        query is detail extracted from query statement.
        sourceobject is previously calculated answer.  Set to None to force
        recalculation from query (after editing query statement usually).
        initial_recordset is games to which query is applied.

        """
        # This instruction to pylint was not needed when this method was
        # defined in cqlgames.ChessQLGames before cqlbase existed.
        # pylint: disable=no-member
        del commit
        if query is None:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return
        self.dbhome.start_read_only_transaction()

        # Use the previously calculated record set if possible.
        # sourceobject is set to None if query must be recalculated.
        if sourceobject is not None:
            ppview = self.dbhome.recordlist_record_number(
                PARTIAL_FILE_DEF, key=sourceobject.key.recno
            )
            pprecalc = self.dbhome.recordlist_key(
                PARTIAL_FILE_DEF,
                NEWGAMES_FIELD_DEF,
                key=self.dbhome.encode_record_selector(NEWGAMES_FIELD_VALUE),
            )
            pprecalc &= ppview
            if pprecalc.count_records() == 0:
                # At version 7.0.3.dev3 the workaround introduced at version
                # 7.0.3.dev1 was removed.
                # The problem was a missing record write in file_records_under
                # method in solentware_base's _lmdb module, not a transaction
                # design problem related to explicit read-only transactions,
                # as originally thought.
                ppcalc = self.dbhome.recordlist_key_startswith(
                    self.dbset,
                    PARTIALPOSITION_FIELD_DEF,
                    keystart=self.dbhome.encode_record_number(
                        sourceobject.key.recno
                    ),
                )

                if ppcalc.count_records() != 0:
                    games = self.dbhome.recordlist_key(
                        self.dbset,
                        PARTIALPOSITION_FIELD_DEF,
                        key=self.dbhome.encode_record_number(
                            sourceobject.key.recno
                        ),
                    )

                    # Hand the list of games over to the user interface.
                    self.set_recordset(games)

                    self.dbhome.end_read_only_transaction()
                    return

        # Evaluate query.
        # Assume record has been deleted if query.query_evaluator is None.
        # Before these changes the query was recalculated on deletion to
        # keep the list until the display is closed.  At present the query
        # is not available to recalculate when deleting.
        # Perhaps initial_recordset should be the recordset displayed at
        # time of deletion: then in can be returned as games without
        # recalculating.
        if query.query_container and query.query_container.evaluator:
            if initial_recordset is None:
                initial_recordlist = self.dbhome.recordlist_ebm(self.dbset)
            else:
                initial_recordlist = self.dbhome.recordlist_nil(self.dbset)
                initial_recordlist |= initial_recordset
            games = self._get_games_matching_filters(query, initial_recordlist)
        else:
            games = self.dbhome.recordlist_nil(self.dbset)
        self.dbhome.end_read_only_transaction()

        # Hand the list of games over to the user interface.
        self.set_recordset(games)

    def _get_games_matching_filters(self, query, games, commit=True):
        """Return games.

        Subclasses should override with a procedure to evaluate query.

        """
        del commit
        del query
        return games
