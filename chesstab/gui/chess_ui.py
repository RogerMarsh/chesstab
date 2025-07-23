# chess_ui.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define the User Interface in detail.

Pick read and write versions of GamePositionGames. PartialPositionGames,
and TagRosterGrid.
"""

from . import _chess_ui
from .gamegrid import (
    TagRosterGrid,
    GamePositionGames,
    PartialPositionGames,
)
from .cqlgrid import CQLGrid
from .cqlrow import chess_db_row_cql


class ChessUI(_chess_ui.ChessUI):
    """Define widgets which form the User Interface."""

    def _create_tag_roster_grid(self):
        """Return TagRosterGrid instance."""
        return TagRosterGrid(self)

    def _create_game_position_games_grid(self):
        """Return GamePositionGames instance."""
        return GamePositionGames(self)

    def _create_partial_position_games_grid(self):
        """Return PartialPositionGames instance."""
        return PartialPositionGames(self)

    def _create_cql_grid(self):
        """Return CQLGrid instance."""
        return CQLGrid(self)

    def _create_partial_position_row(self):
        """Return ChessDBrowCQL instance."""
        return chess_db_row_cql(self)
