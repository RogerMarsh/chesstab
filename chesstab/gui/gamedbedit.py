# gamedbedit.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert chess game record."""

import ast
import tkinter

from solentware_grid.gui.dataedit import DataEdit

from pgn_read.core.parser import PGN
from pgn_read.core.constants import TAG_WHITE, TAG_BLACK

from ..core import constants
from .gametoplevel import GameToplevel, GameToplevelEdit
from .toplevelpgn import EditPGNToplevel
from .constants import EMPTY_SEVEN_TAG_ROSTER
from ..core import utilities
from ..cql import runcql


class GameDbEdit(EditPGNToplevel, DataEdit):
    """Edit PGN text for game on database, or insert a new record.

    parent is used as the master argument in GameToplevel calls.

    ui is used as the ui argument in GameToplevel calls.

    newobject, parent, oldobject, and the one or two GameToplevel instances
    created, are used as arguments in the super.__init__ call.

    showinitial determines whether a GameToplevel is created for oldobject if
    there is one.

    Attribute pgn_score_name provides the name used in widget titles and
    message text.

    Attribute pgn_score_tags provides empty PGN tags to present when creating
    an insert Toplevel.  It is the empty PGN Seven Tag Roster.

    Attribute pgn_score_source provides the error key value to index a PGN
    game score with errors.

    Methods _get_title_for_object and _set_item, and properties ui_base_table;
    ui_items_in_toplevels; and ui, allow similar methods in various classes
    to be expressed identically and defined once.

    """

    pgn_score_name = "Game"
    pgn_score_tags = EMPTY_SEVEN_TAG_ROSTER
    pgn_score_source = ""

    def __init__(
        self,
        newobject=None,
        parent=None,
        oldobject=None,
        showinitial=True,
        ui=None,
    ):
        """Extend and create dialogue widget to edit or insert chess game."""
        if not oldobject:
            showinitial = False
        super().__init__(
            newobject=newobject,
            parent=parent,
            oldobject=oldobject,
            newview=GameToplevelEdit(master=parent, ui=ui),
            title="",
            oldview=(
                GameToplevel(master=parent, ui=ui)
                if showinitial
                else showinitial
            ),
        )
        self._initialize()
        if utilities.is_game_import_in_progress_txn(
            self.ui.database, self.newobject
        ):
            tkinter.messagebox.showinfo(
                parent=parent,
                title="Game import not complete",
                message="".join(
                    (
                        "The selected game is displayed but attempts ",
                        "to save edits to the game will be ",
                        "rejected because some stages of importing this ",
                        "game have not been completed.",
                    )
                ),
            )
            self.blockchange = True

    @property
    def ui_base_table(self):
        """Return the User Interface TagRosterGrid object."""
        return self.ui.base_games

    @property
    def ui_items_in_toplevels(self):
        """Return the User Interface objects in Toplevels."""
        return self.ui.games_and_repertoires_in_toplevels

    @property
    def ui(self):
        """Return the User Interface object from 'editable' view."""
        return self.newview.ui

    def _set_item(self, view, object_):
        """Populate view with the game extracted from object_."""
        self._set_default_source_for_object(object_)
        view.set_position_analysis_data_source()
        view.collected_game = next(
            PGN(game_class=view.gameclass).read_games(
                ast.literal_eval(object_.get_srvalue()[0])
            )
        )
        view.set_and_tag_item_text()

    def _get_title_for_object(self, object_=None):
        """Return title for Toplevel containing a Game object_.

        Default value of object_ is oldobject attribute from DataEdit class.

        """
        if object_ is None:
            object_ = self.oldobject
        if object_:
            tags = object_.value.collected_game.pgn_tags
            try:
                return "  ".join(
                    (
                        self.pgn_score_name.join(("Edit ", ":")),
                        " - ".join((tags[TAG_WHITE], tags[TAG_BLACK])),
                    )
                )
            except TypeError:
                return self.pgn_score_name.join(
                    ("Edit ", " - names unknown or invalid")
                )
            except KeyError:
                return self.pgn_score_name.join(
                    ("Edit ", " - names unknown or invalid")
                )
        else:
            return "".join(("Insert ", self.pgn_score_name))

    def _set_default_source_for_object(self, object_=None):
        """Set default source for Toplevel containing a Game object_.

        Default value of object_ is oldobject attribute from DataEdit class.

        Currently do nothing for games.  Originally used for games with PGN
        errors, where it was the name of the PGN file containing the game.

        Now present for compatibility with Repertoires.

        """

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    # mark...recalculated starts and commits a transaction unconditionally.
    # No harm in using the same default as the 'super()' method.
    def put(self, commit=True):
        """Mark CQL query records for recalculation and return key.

        If commit evaluates False caller is responsible for evaluating
        CQL queries on the changes.

        """
        self.datasource.dbhome.mark_games_evaluated(
            allexceptkey=(
                self.newobject.key.recno
                if self.newobject is not None
                else None
            )
        )
        self.datasource.dbhome.mark_all_cql_statements_not_evaluated()
        super().put(commit=commit)
        if commit:
            runcql.make_runcql(self.datasource.dbhome, self.ui, False)
            if self.ui.partial_items.count_items_in_stack():
                active_item = self.ui.partial_items.active_item
                active_item.refresh_game_list(
                    key_recno=active_item.sourceobject.key.recno
                )

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    # mark...recalculated starts and commits a transaction unconditionally.
    # No harm in using the same default as the 'super()' method.
    def edit(self, commit=True):
        """Mark CQL query records for recalculation and return key.

        If commit evaluates False caller is responsible for evaluating
        CQL queries on the changes.

        """
        self.datasource.dbhome.mark_games_evaluated(
            allexceptkey=(
                self.oldobject.key.recno
                if self.oldobject is not None
                else None
            )
        )
        self.datasource.dbhome.mark_all_cql_statements_not_evaluated()
        super().edit(commit=commit)
        if commit:
            runcql.make_runcql(self.datasource.dbhome, self.ui, False)
            if self.ui.partial_items.count_items_in_stack():
                active_item = self.ui.partial_items.active_item
                active_item.refresh_game_list(
                    key_recno=active_item.sourceobject.key.recno
                )

    # This method forced by addition of second list element in Game record
    # value, which breaks the 'class <Repertoire>(<Game>)' relationship in
    # in classes in chessrecord module.
    # Nowhere to put this in common with GameDisplayEdit.
    def _construct_record_value(self, reference):
        """Return record value for Game record."""
        # Record value becomes {"file": "/", "game": ""} because the "file"
        # value cannot be length zero when used as a key in a LMDB database.
        # When "file" is a file name the "game" values will be 1, 2, 3,
        # and so forth.
        if reference[constants.GAME]:
            game_number = ""
        else:
            game_number = reference[constants.GAME]
        return repr(
            [
                repr(self.newview.get_score_error_escapes_removed()),
                {constants.FILE: "/", constants.GAME: game_number},
            ]
        )
