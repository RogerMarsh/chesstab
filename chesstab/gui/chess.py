# chess.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define menu of database export functions.

Add options to export chess games and related data to the menu bar.

This module used to have all the stuff now in the classes defined in the
chess_import, chess_database, and chess_widget, modules.

"""

from ..core import export_game
from ..core import export_repertoire
from ..core import export_chessql
from . import chess_import


class Chess(chess_import.Chess):
    """Allow export from a chess database."""

    def export_all_games_pgn_reduced_export_format(self):
        """Export all database games in PGN reduced export format."""
        self.ui.export_report(
            export_game.export_all_games_pgn_reduced_export_format(
                self.opendatabase,
                self.ui.get_export_filename(
                    "Games (reduced export format)", pgn=True
                ),
            ),
            "Games (reduced export format)",
        )

    def export_all_games_pgn_no_comments_no_ravs(self):
        """Export games in PGN export format excluding comments and RAVs."""
        self.ui.export_report(
            export_game.export_all_games_pgn_no_comments_no_ravs(
                self.opendatabase,
                self.ui.get_export_filename(
                    "Games (no comments no ravs)", pgn=True
                ),
            ),
            "Games (no comments no ravs)",
        )

    def export_all_games_pgn_no_comments(self):
        """Export all games in PGN export format excluding comments."""
        self.ui.export_report(
            export_game.export_all_games_pgn_no_comments(
                self.opendatabase,
                self.ui.get_export_filename("Games (no comments)", pgn=True),
            ),
            "Games (no comments)",
        )

    def export_all_games_pgn(self):
        """Export all database games in PGN export format."""
        self.ui.export_report(
            export_game.export_all_games_pgn(
                self.opendatabase,
                self.ui.get_export_filename("Games", pgn=True),
            ),
            "Games",
        )

    def export_all_games_pgn_import_format(self):
        """Export all database games in a PGN import format."""
        self.ui.export_report(
            export_game.export_all_games_pgn_import_format(
                self.opendatabase,
                self.ui.get_export_filename("Games (import format)", pgn=True),
            ),
            "Games (import format)",
        )

    def export_all_games_text(self):
        """Export all games as a text file."""
        export_game.export_all_games_text(
            self.opendatabase,
            self.ui.get_export_filename("Games (internal format)", pgn=False),
        )

    def export_all_repertoires_pgn_no_comments(self):
        """Export all repertoires in PGN export format without comments."""
        export_repertoire.export_all_repertoires_pgn_no_comments(
            self.opendatabase,
            self.ui.get_export_filename("Repertoires (no comments)", pgn=True),
        )

    def export_all_repertoires_pgn(self):
        """Export all repertoires in PGN export format."""
        export_repertoire.export_all_repertoires_pgn(
            self.opendatabase,
            self.ui.get_export_filename("Repertoires", pgn=True),
        )

    def export_all_repertoires_pgn_import_format(self):
        """Export all repertoires in a PGN import format."""
        export_repertoire.export_all_repertoires_pgn_import_format(
            self.opendatabase,
            self.ui.get_export_filename(
                "Repertoires (import format)", pgn=True
            ),
        )

    def export_all_repertoires_text(self):
        """Export all repertoires as a text file."""
        export_repertoire.export_all_repertoires_text(
            self.opendatabase,
            self.ui.get_export_filename(
                "Repertoires (internal format)", pgn=False
            ),
        )

    def export_positions(self):
        """Export all positions as a text file."""
        export_chessql.export_all_positions(
            self.opendatabase,
            self.ui.get_export_filename("Partial Positions", pgn=False),
        )
