# cqlgames.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Evaluate a ChessQL query using database indicies."""

from solentware_base.core.find import Find

from . import cqlbase


class ChessQLGames(cqlbase.ChessQLBase):
    """Represent subset of games that match a Chess Query Language query."""

    def __init__(self, *a, **k):
        """Delete then create Find instance for queries."""
        super().__init__(*a, **k)

        # recordclass argument must be used to support non-index field finds.
        # Empty square searches can be transformed into equivalent occupied
        # square searches, but it does not work yet.
        # ChessDBrecordGameUpdate is the closest class to that needed.
        # No update capability is needed, and a different set of 'per move'
        # attributes might be better.
        # The 'try ...' statements in .gui.cqldisplay and .gui.cqltext fit the
        # version of Find(...) call with the recordclass argument.
        # self.cqlfinder = Find(
        #    self.dbhome, self.dbset, recordclass=ChessDBrecordGameUpdate)
        self.cqlfinder = Find(self.dbhome, self.dbset)

    def _get_games_matching_filters(self, query, games, commit=True):
        """Select the games which meet the ChessQL cql() ... filters.

        Walk node tree for every movenumber and combine evaluated game sets.

        """
        query.query_container.evaluator.node.expand_symbol()
        query.query_container.evaluator.node.prepare_to_evaluate_symbol()
        query.query_container.evaluator.node.evaluate_symbol(
            self.cqlfinder, commit=commit
        )
        return query.query_container.evaluator.node.data & games
