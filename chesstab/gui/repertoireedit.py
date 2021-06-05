# repertoireedit.py
# Copyright 2008, 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to edit an opening repertoire.

The RepertoireEdit class displays PGN text representing an opening repertoire
and allows editing.  It is a subclass of GameEdit.

This class does not allow deletion of repertoires from a database.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

from ..core.constants import REPERTOIRE_TAG_ORDER
from ..core.pgn import GameDisplayMoves, GameRepertoireDisplayMoves
from .eventspec import EventSpec
from .gameedit import GameEdit


class RepertoireEdit(GameEdit):

    """Display a repertoire with editing allowed.

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

    tags_displayed_last = REPERTOIRE_TAG_ORDER
    pgn_export_type = "Repertoire", GameRepertoireDisplayMoves

    # gameclass=GameRepertoireDisplayMoves surely?
    # Then maybe do not need pgn_export_type for 'export_..' methods in Score.
    # Otherwise there is no point to this __init__ method.
    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend with bindings to edit repertoire score."""
        super(RepertoireEdit, self).__init__(gameclass=gameclass, **ka)

    def insert_empty_pgn_seven_tag_roster(self):
        """Insert ' [ <fieldname> "<null>" ... ] ' seven tag roster sequence."""
        self.set_insertion_point_before_next_pgn_tag()
        for t in REPERTOIRE_TAG_ORDER:
            self.add_pgntag_to_map(t, "")

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
