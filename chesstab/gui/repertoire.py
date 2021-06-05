# repertoire.py
# Copyright 2008, 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display an opening repertoire.

The display contains the game score, a board with the current position in the
game, and any analysis of the current position by chess engines.

The Repertoire class displays PGN text representing an opening repertoire.

Repertoire is a subclass of Game.

An instance of Repertoire fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

from ..core.pgn import (
    GameDisplayMoves,
    GameRepertoireDisplayMoves,
)
from .eventspec import EventSpec
from ..core.constants import REPERTOIRE_TAG_ORDER
from .game import Game


class Repertoire(Game):

    """Chess repertoire game widget composed from Board and Text widgets.

    gameclass is passed to the superclass as the gameclass argument.  It
    defaults to GameDisplayMoves.

    Attribute tags_displayed_last is the PGN tags, in order, to be displayed
    immediately before the movetext.  It exists so Game*, Repertoire*, and
    AnalysisScore*, instances can use identical code to display PGN tags.  It
    is the PGN repertoire tags defined in ChessTab.

    Attribute pgn_export_type is a tuple with the name of the type of data and
    the class used to generate export PGN.  It exists so Game*, Repertoire*,
    and AnalysisScore*, instances can use identical code to display PGN tags.
    It is ('Repertoire', GameRepertoireDisplayMoves).

    """

    # Override methods referring to Seven Tag Roster

    tags_displayed_last = REPERTOIRE_TAG_ORDER
    pgn_export_type = "Repertoire", GameRepertoireDisplayMoves

    # gameclass=GameRepertoireDisplayMoves surely?
    # Then maybe do not need pgn_export_type for 'export_..' methods in Score.
    # Otherwise there is no point to this __init__ method.
    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend to display repertoire game."""
        super(Repertoire, self).__init__(gameclass=gameclass, **ka)

    # There is no point to a repertoire without RAVs so the options suppressing
    # RAVs are absent.
    def get_all_export_events(self):
        return (
            (
                EventSpec.pgn_export_format_no_comments,
                self.export_pgn_no_comments,
            ),
            (EventSpec.pgn_export_format, self.export_pgn),
            (EventSpec.pgn_import_format, self.export_pgn_import_format),
            (EventSpec.text_internal_format, self.export_text),
        )
