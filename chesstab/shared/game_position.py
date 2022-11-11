# game_position.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide class for ChessDBrowGame and ChessDBrowPosition shared methods."""

from ..gui.gamedbedit import GameDbEdit
from ..gui.gamedbdelete import GameDbDelete
from ..gui.gamedbshow import GameDbShow


class GamePosition:
    """Provide methods shared by ChessDBrowGame and ChessDBrowPosition."""

    def show_row(self, dialog, oldobject):
        """Return a GameDbShow toplevel for oldobject record.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return GameDbShow(dialog, oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a GameDbDelete toplevel for oldobject record.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return GameDbDelete(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a GameDbEdit toplevel for newobject and oldobject records.

        dialog - a Toplevel
        newobject - a ChessDBrecordGame containing original data to be edited
        oldobject - a ChessDBrecordGame containing original data
        showintial == True - show both original and edited data

        """
        return GameDbEdit(
            newobject, dialog, oldobject, showinitial=showinitial, ui=self.ui
        )
