# repertoiredbedit.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert repertoire record."""

from solentware_grid.gui.dataedit import DataEdit

from pgn_read.core.parser import PGN

from ..core.constants import TAG_OPENING
from .repertoiretoplevel import (
    RepertoireToplevel,
    RepertoireToplevelEdit,
)
from .toplevelpgn import EditPGNToplevel
from .constants import EMPTY_REPERTOIRE_GAME


class RepertoireDbEdit(EditPGNToplevel, DataEdit):
    """Edit PGN text for repertoire on database, or insert a new record.

    parent is used as the master argument in RepertoireToplevel calls.

    ui is used as the ui argument in RepertoireToplevel calls.

    newobject, parent, oldobject, and the one or two RepertoireToplevel
    instances created, are used as arguments in the super.__init__ call.

    showinitial determines whether a RepertoireToplevel is created for
    oldobject if there is one.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Attribute pgn_score_tags provides empty PGN tags to present when creating
    an insert Toplevel.  It is the empty PGN tags defined for repertoires in
    ChessTab..

    Attribute pgn_score_source provides the error key value to index a PGN
    game score with errors.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    pgn_score_name = "Repertoire"
    pgn_score_tags = EMPTY_REPERTOIRE_GAME
    pgn_score_source = "No opening name"

    def __init__(
        self,
        newobject=None,
        parent=None,
        oldobject=None,
        showinitial=True,
        ui=None,
    ):
        """Extend and create toplevel to edit or insert repertoire."""
        if not oldobject:
            showinitial = False
        super().__init__(
            newobject=newobject,
            parent=parent,
            oldobject=oldobject,
            newview=RepertoireToplevelEdit(master=parent, ui=ui),
            title="",
            oldview=RepertoireToplevel(master=parent, ui=ui)
            if showinitial
            else showinitial,
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
        """Return the User Interface object from 'editable' view."""
        return self.newview.ui

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

        Default value of object_ is oldobject attribute from DataEdit class.

        """
        if object_ is None:
            object_ = self.oldobject
        if object_:
            try:
                return "  ".join(
                    (
                        self.pgn_score_name.join(("Edit ", ":")),
                        object_.value.collected_game.pgn_tags[TAG_OPENING],
                    )
                )
            except TypeError:
                return self.pgn_score_name.join(
                    ("Edit ", " - name unknown or invalid")
                )
            except KeyError:
                return self.pgn_score_name.join(
                    ("Edit ", " - name unknown or invalid")
                )
        else:
            return "".join(("Insert ", self.pgn_score_name))

    def _set_default_source_for_object(self, object_=None):
        """Set default source for Toplevel containing a Repertoire object_.

        Default value of object_ is oldobject attribute from DataEdit class.

        """
        if object_ is None:
            object_ = self.oldobject
        if object_ is not None:
            object_.value.set_game_source(self.pgn_score_source)

    def dialog_ok(self):
        """Extend to adjust equality comparison of old and new versions.

        Selection highlighting behaviour for repertoires is made same as
        other item types.

        """
        # Problem arises because gamesource is treated differently in game
        # and repertoire items.
        # The selection highlight is removed if the referenced toplevel is
        # changed, but not if some other item (same type with or without
        # referenced toplevel) is highlighted.  This is inconsistent too,
        # but arises from poor implementation of opening up a toplevel using
        # just the pointer without affecting the selection highlight.  One
        # solution is to change the intent so the pointer does affect the
        # selection highlight when opening a toplevel, but not when closing
        # a toplevel: most of behaviour at time of writing is consistent
        # with this solution.
        if self.oldobject and self.newobject:
            oldv = self.oldobject.value
            newv = self.newobject.value
            # Force the test in DataEdit.dialog_ok to give desired outcome.
            if oldv.collected_game == newv.collected_game:
                newv.gamesource = oldv.gamesource
        return super().dialog_ok()
