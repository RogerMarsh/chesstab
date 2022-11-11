# repertoiredbdelete.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete toplevel to delete repertoire record."""

from solentware_grid.gui.datadelete import DataDelete

from pgn_read.core.parser import PGN

from ..core.constants import TAG_OPENING
from .repertoiretoplevel import RepertoireToplevel
from .toplevelpgn import DeletePGNToplevel


class RepertoireDbDelete(DeletePGNToplevel, DataDelete):
    """Delete PGN text for repertoire from database.

    parent is used as the master argument in a RepertoireToplevel call.

    ui is used as the ui argument in a RepertoireToplevel call.

    parent, oldobject, and the RepertoireToplevel instance created, are used
    as arguments in the super.__init__ call.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    pgn_score_name = "Repertoire"

    def __init__(self, parent=None, oldobject=None, ui=None):
        """Extend and create toplevel widget for deleting chess game."""
        # Toplevel title set '' in __init__ and to proper value in _initialize.
        super().__init__(
            instance=oldobject,
            parent=parent,
            oldview=RepertoireToplevel(master=parent, ui=ui),
            title="",
        )
        self._initialize()

    @property
    def ui_base_table(self):
        """Return the User Interface RepertoireGrid object."""
        return self.ui.base_repertoires

    @property
    def ui_items_in_toplevels(self):
        """Return the User Interface objects in Toplevels."""
        return self.ui.games_and_repertoires_in_toplevels

    @property
    def ui(self):
        """Return the User Interface object from 'read-only' view."""
        return self.oldview.ui

    def _set_item(self, view, object_):
        """Populate view with the repertoire extracted from object_."""
        self._set_default_source_for_object(object_)
        view.set_position_analysis_data_source()
        view.collected_game = next(
            PGN(game_class=view.gameclass).read_games(object_.get_srvalue())
        )
        view.set_and_tag_item_text()

    def _get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a Repertoire object_.

        Default value of object_ is object attribute from DataDelete class.

        """
        if object_ is None:
            object_ = self.object
        try:
            return "  ".join(
                (
                    self.pgn_score_name.join(("Delete ", ":")),
                    object_.value.collected_game.pgn_tags[TAG_OPENING],
                )
            )
        except TypeError:
            return self.pgn_score_name.join(
                ("Delete ", " - name unknown or invalid")
            )
        except KeyError:
            return self.pgn_score_name.join(
                ("Delete ", " - name unknown or invalid")
            )

    def _set_default_source_for_object(self, object_=None):
        """Set default source for Toplevel containing a Repertoire object_.

        Default value of object_ is object attribute from DataDelete class.

        """
