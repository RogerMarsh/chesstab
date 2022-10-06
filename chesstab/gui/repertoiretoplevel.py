# repertoiretoplevel.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Toplevel widgets to display and edit repertoires.

These two classes display repertoires in their own Toplevel widget: they are
used in the repertoiredbdelete, repertoiredbedit, and repertoiredbshow,
modules.

"""
from .repertoire import Repertoire
from .repertoireedit import RepertoireEdit
from .toplevelpgn import ToplevelPGN


class RepertoireToplevel(ToplevelPGN, Repertoire):
    """Customize Repertoire seen in a ToplevelPGN widget."""


class RepertoireToplevelEdit(ToplevelPGN, RepertoireEdit):
    """Customize RepertoireEdit seen in a ToplevelPGN widget."""

    def _create_primary_activity_popup(self):
        """Create popup menu for a repertoire widget."""
        popup = super()._create_primary_activity_popup()
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.analyse_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup,
            include_ooo=True,
            include_move_rav=True,
            index=self.analyse_popup_label,
        )
        return popup
