# cqldisplaybase.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Base class for widgets to display and edit CQL statements.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

CQLDisplayBase provides behaviour shared by classes which display, modify,
insert, and delete, CQL statements.
"""

import tkinter
import tkinter.messagebox

from solentware_grid.core.dataclient import DataNotify

from solentware_bind.gui.bindings import Bindings

from .cql import CQL
from .eventspec import EventSpec
from .display import Display
from .displaytext import (
    ShowText,
    DisplayText,
)


class CQLDisplayBase(
    ShowText, DisplayText, CQL, Display, Bindings, DataNotify
):
    """Extend and link ChessQL statement to database.

    sourceobject - link to database.

    Attribute binding_labels specifies the order navigation bindings appear
    in popup menus.

    Method _insert_item_database allows records to be inserted into a database
    from any CQL widget.

    """

    binding_labels = (
        EventSpec.navigate_to_position_grid,
        EventSpec.navigate_to_active_game,
        EventSpec.navigate_to_game_grid,
        EventSpec.navigate_to_repertoire_grid,
        EventSpec.navigate_to_active_repertoire,
        EventSpec.navigate_to_repertoire_game_grid,
        EventSpec.navigate_to_partial_grid,
        EventSpec.partialdisplay_to_previous_partial,
        EventSpec.partialdisplay_to_next_partial,
        EventSpec.navigate_to_partial_game_grid,
        EventSpec.navigate_to_selection_rule_grid,
        EventSpec.navigate_to_active_selection_rule,
        EventSpec.tab_traverse_backward,
        EventSpec.tab_traverse_forward,
    )

    def __init__(self, sourceobject=None, **ka):
        """Extend and link ChessQL statement to database."""
        super().__init__(**ka)
        self.blockchange = False
        if self.ui.base_partials.datasource:
            self.set_data_source(self.ui.base_partials.get_data_source())
        self.sourceobject = sourceobject
        self.insertonly = sourceobject is None

    @property
    def ui_displayed_items(self):
        """Return manager of widgets displaying a CQL query record."""
        return self.ui.partial_items

    @property
    def ui_configure_item_list_grid(self):
        """Return function to configure CQL query grid to fit text."""
        return self.ui.configure_partial_grid

    @property
    def ui_set_item_name(self):
        """Return function to set status bar text to name of active query."""
        return self.ui.set_partial_name

    @property
    def ui_set_find_item_games(self):
        """Return function to set status bar text."""
        return self.ui.set_find_partial_name_games

    def _get_navigation_events(self):
        """Return event description tuple for navigation from query."""
        return (
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (EventSpec.partialdisplay_to_previous_partial, self._prior_item),
            (EventSpec.partialdisplay_to_next_partial, self._next_item),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (EventSpec.navigate_to_active_game, self.set_focus_gamepanel_item),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (EventSpec.export_from_partialdisplay, self._export_partial),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_round, self.traverse_round),
        )

    def delete_item_view(self, event=None):
        """Remove ChessQL statement item from screen."""
        del event
        self.ui.delete_position_view(self)

    def on_game_change(self, instance):
        """Recalculate list of games for ChessQL statement after game update.

        instance is ignored: it is assumed a recalculation is needed.

        """
        del instance
        if self.sourceobject is not None:
            self._get_cql_statement_games_to_grid(
                self.cql_statement
            )  # .match)

    def generate_popup_navigation_maps(self):
        """Return genenal and current widget navigation binding maps."""
        navigation_map = dict(self._get_navigation_events())
        local_map = {}
        return navigation_map, local_map

    def _create_primary_activity_popup(self):
        """Delegate then add close command to popup and return popup menu."""
        popup = super()._create_primary_activity_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def on_partial_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if instance.newrecord:
            # Editing an existing record.
            key = instance.newrecord.key

        else:
            # Inserting a new record or deleting an existing record.
            key = instance.key

        if self.sourceobject is not None:
            if (
                key == self.sourceobject.key
                and self.datasource.dbname == self.sourceobject.dbname
                and self.datasource.dbset == self.sourceobject.dbset
            ):
                self.blockchange = True

        # Code to refresh list of matching games removed because the
        # recalculation is done by CQL program in separate processes
        # after the change is committed.

    def get_text_for_statusbar(self):
        """Return 'Please wait ..' message for status bar."""
        return "".join(
            (
                "Please wait while finding games for ChessQL statement ",
                self.cql_statement.get_name_text(),
            )
        )

    def get_selection_text_for_statusbar(self):
        """Return CQL query name text for display in status bar."""
        return self.cql_statement.get_name_text()

    def set_game_list(self):
        """Delegate to refresh_game_list via 'after(...) call."""
        self.panel.after(
            0, func=self.try_command(self.ui.set_partial_name, self.panel)
        )
        self.panel.after(
            0, func=self.try_command(self._refresh_game_list, self.panel)
        )

    def _refresh_game_list(self):
        """Call refresh_game_list in a try_command() call.."""
        self.refresh_game_list(
            key_recno=(
                self.sourceobject.key.recno
                if self.sourceobject is not None
                else None
            )
        )

    def _get_cql_statement_games_to_grid(self, statement):  # match):
        """Populate Partial Position games grid with games selected by match.

        "match" is named for the CQL version-1.0 keyword which started a CQL
        statement.  Usage is "(match ..." which become "cql(" no later than
        version 5.0 of CQL.  Thus "cql" is now a better name for the argument.

        """
        pgd = self.ui.partial_games
        if len(pgd.keys):
            key = pgd.keys[0]
        else:
            key = None
        pgd.close_client_cursor()
        try:
            pgd.datasource.get_cql_statement_games(
                statement,
                (
                    self.sourceobject.key.recno
                    if self.sourceobject is not None
                    else None
                ),
            )
        except AttributeError as exc:
            if str(exc) == "'NoneType' object has no attribute 'answer'":
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement, ",
                        "probably because an 'empty square' is in the query ",
                        "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                        str(exc),
                    )
                )
            else:
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement:\n\n",
                        "The reported error is:\n\n",
                        str(exc),
                    )
                )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message=msg,
            )
            return
        pgd.fill_view(currentkey=key, exclude=False)
