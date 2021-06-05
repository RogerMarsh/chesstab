# repertoiredbdelete.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise delete toplevel to delete repertoire record.
"""

from solentware_grid.gui.datadelete import DataDelete

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN

from ..core.constants import TAG_OPENING
from .repertoiretoplevel import RepertoireToplevel
from .toplevelpgn import DeletePGN


class RepertoireDbDelete(ExceptionHandler, DeletePGN, DataDelete):

    """Delete PGN text for repertoire from database.

    parent is used as the master argument in a RepertoireToplevel call.

    ui is used as the ui argument in a RepertoireToplevel call.

    parent, oldobject, and the RepertoireToplevel instance created, are used
    as arguments in the super.__init__ call.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Methods get_title_for_object and set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    pgn_score_name = "Repertoire"

    def __init__(self, parent, oldobject, ui=None):
        """Extend and create toplevel widget for deleting chess game."""
        # Toplevel title set '' in __init__ and to proper value in initialize.
        super().__init__(
            oldobject, parent, RepertoireToplevel(master=parent, ui=ui), ""
        )
        self.initialize()

    @property
    def ui_base_table(self):
        return self.ui.base_repertoires

    @property
    def ui_items_in_toplevels(self):
        return self.ui.games_and_repertoires_in_toplevels

    @property
    def ui(self):
        return self.oldview.ui

    def set_item(self, view, object_):
        self.set_default_source_for_object(object_)
        view.set_position_analysis_data_source()
        view.collected_game = next(
            PGN(game_class=view.gameclass).read_games(object_.get_srvalue())
        )
        view.set_and_tag_item_text()

    def get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a Repertoire object_.

        Default value of object_ is object attribute from DataDelete class.

        """
        if object_ is None:
            object_ = self.object
        try:
            return "  ".join(
                (
                    self.pgn_score_name.join(("Delete ", ":")),
                    object_.value.collected_game._tags[TAG_OPENING],
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

    def set_default_source_for_object(self, object_=None):
        """Set default source for Toplevel containing a Repertoire object_.

        Default value of object_ is object attribute from DataDelete class.

        """
        pass
