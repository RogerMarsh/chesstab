# gametoplevel.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Toplevel widgets to display and edit game scores.

These two classes display games in their own Toplevel widget: they are used
in the gamedbdelete, gamedbedit, and gamedbshow, modules.

"""
from .game import Game
from .gameedit import GameEdit
from .toplevelpgn import ToplevelPGN


class GameToplevel(ToplevelPGN, Game):

    """Customize Game to be the single instance in a Toplevel widget."""


class GameToplevelEdit(ToplevelPGN, GameEdit):

    """Customize GameEdit to be the single instance in a Toplevel widget."""

    def create_primary_activity_popup(self):
        popup = super().create_primary_activity_popup()
        self.add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.analyse_popup_label
        )
        self.add_pgn_insert_to_submenu_of_popup(
            popup,
            include_ooo=True,
            include_move_rav=True,
            index=self.analyse_popup_label,
        )
        return popup
