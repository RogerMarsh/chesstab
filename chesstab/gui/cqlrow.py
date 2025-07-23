# cqlrow.py
# Copyright 2016, 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets to display Chess Query Language (ChessQL) statement.

Adapt chesstab.gui._cqlrow.ChessDBrowCQL class to use chesstab version
of CQLDbEdit class.
"""

from . import _cqlrow
from .cqldbedit import CQLDbEdit


class ChessDBrowCQL(_cqlrow.ChessDBrowCQL):
    """Define row in list of ChessQL statements.

    Add row methods to the ChessQL statement record definition.

    """

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a CQLDbEdit dialog for instance.

        dialog - a Toplevel
        newobject - a ChessDBrecordPartial containing original data to be
                    edited
        oldobject - a ChessDBrecordPartial containing original data
        showintial == True - show both original and edited data

        """
        return CQLDbEdit(
            newobject=newobject,
            parent=dialog,
            oldobject=oldobject,
            showinitial=showinitial,
            ui=self.ui,
        )


def chess_db_row_cql(chessui):
    """Return function that returns ChessDBrowCQL instance for chessui.

    chessui is a chess_ui.ChessUI instance.

    The returned function takes a Database instance as it's argument.
    """

    def make_selection(database=None):
        return ChessDBrowCQL(database=database, ui=chessui)

    return make_selection
