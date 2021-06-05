# displaytext.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define methods shared by classes in cqldisplay and
querydisplay modules which display plain text.

The cqldisplay module has two sets of classes: based on the _CQLDisplay and
CQLDialogue classes.

The querydisplay module has an identical structure where the _CQLDisplay
and _QueryDisplay classes have many methods in common.

All methods in the classes in this module existed as multiple copies in various
classes in the cqldisplay and querydisplay modules.  They are now deleted
from those modules.

The classes in this module represent the different sets of classes with methods
in common.  Two classes could reasonably be called DisplayText: the choice is
consistent with the naming of InsertText and EditText.  ShowText was chosen for
the other class.

The ShowText class is populated with the methods identical in _CQLDisplay
and _QueryDisplay, which were then removed from those two classes.

The DisplayText class is populated with the methods identical in CQLDisplay
and QueryDisplay, which were then removed from those two classes.

The InsertText class is populated with the methods identical in
CQLDisplayInsert and QueryDisplayInsert, which were then removed from those
two classes.

The EditText class is populated with the methods identical in
CQLDisplayEdit and QueryDisplayEdit, which were then removed from those two
classes.  It probably should be a subclass of InsertText, but this depends on
successful choice of method resolution order in the classes in cqldisplay and
querydisplay modules.

"""
import tkinter
import tkinter.messagebox

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete

from .eventspec import EventSpec
from .score import NonTagBind


# ShowText because DisplayText fits CQLDisplay (and *Query*), but there is
# no EngineDisplay class.  ScorePGN has no equivalent in the *Text line
# because selection rules, CQL statements, and run engine commands, do not
# have 'analysis'.
class ShowText:

    """Mixin providing methods shared by the cqldisplay._CQLDisplay and
    querydisplay.QueryDisplay classes.

    Provide focus switching and widget visibility methods for widgets which
    display plain text.

    The cqldisplay.CQLDialogue and query.QueryDialogue classes are used in a
    Toplevel which displays one ChessQL or Selection Rule statement.  The
    focus switching provided here is not needed.

    """

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    # Renamed from _bind_for_board_navigation to fit current use.
    # Before introduction of querydisplay and removal of board from predecessor
    # of cqldisplay on conversion, it was a reasonable name.
    def bind_for_item_navigation(self):
        """Set bindings to navigate text statement on pointer click."""
        self.set_score_pointer_item_navigation_bindings(True)

    def bind_for_widget_navigation(self):
        """Set bindings to give focus to this text statement on pointer click."""
        self.set_score_pointer_widget_navigation_bindings(True)

    def get_close_item_events(self):
        return ((EventSpec.display_dismiss, self.delete_item_view),)

    def set_insert_or_delete(self):
        """Convert edit display to insert display.

        PGN scores displayed for editing from a database are not closed if the
        database is closed.  They are converted to insert displays and can
        be used to add new records to databases opened later.

        """
        self.sourceobject = None

    def set_and_tag_item_text(self, reset_undo=False):
        """Delegate to superclass method and set PGN score inactive."""

        # Superclass may set self._most_recent_bindings but test below must be
        # against current value.
        mrb = self._most_recent_bindings

        super().set_and_tag_item_text(reset_undo=reset_undo)
        if mrb != NonTagBind.NO_EDITABLE_TAGS:
            for es in (self.get_inactive_button_events(),):
                self.set_event_bindings_score(es, switch=True)

    def create_database_submenu(self, menu):
        submenu = tkinter.Menu(master=menu, tearoff=False)
        self.set_popup_bindings(submenu, self.get_database_events())
        return submenu

    # The only active bindings compared with displaypgn.ShowPGN.
    def set_primary_activity_bindings(self, switch=True):
        """Delegate to toggle other relevant bindings and toggle bindings for
        database actions, navigation to other widgets, and close widget.

        """
        super().set_primary_activity_bindings(switch=switch)
        self.set_database_navigation_close_item_bindings(switch=switch)

    # Not relevant away from displaypgn.ShowPGN.
    # def set_select_variation_bindings(self, switch=True):
    #    """Delegate to toggle other relevant bindings and toggle bindings for
    #    database actions, navigation to other widgets, and close widget.

    #    """
    #    super().set_select_variation_bindings(switch=switch)
    #    self.set_database_navigation_close_item_bindings(switch=switch)

    # The methods identical except for docstrings, and references to
    # self.ui.game_items or self.ui.repertoire_items replaced by property
    # self.ui_displayed_items.

    def next_item(self, event=None):
        """Select next item on display.

        Call _next_item after 1 millisecond to allow message display.

        """
        if self.ui_displayed_items.count_items_in_stack() > 1:
            self.ui_set_find_item_games(0)
            self.score.after(1, self.try_command(self.cycle_item, self.score))

    def prior_item(self, event=None):
        """Select previous item on display.

        Call _prior_item after 1 millisecond to allow message display.

        """
        if self.ui_displayed_items.count_items_in_stack() > 1:
            self.ui_set_find_item_games(-2)
            self.score.after(
                1, self.try_command(self.cycle_item, self.score), True
            )

    # What about current_pgn_score call?
    def current_item(self, event=None):
        """Select current PGN score on display."""

        # cuiai should be referencing self given use of current_item() method,
        # but style of sibling *_item() methods is followed.
        # cuiai was cuigs in gamedisplay, and cuirs in repertoiredisplay,
        # modules originally.
        items = self.ui_displayed_items
        if items.count_items_in_stack():
            cuiai = items.active_item
            self.current_pgn_score(cuiai)
            cuiai.set_statusbar_text()

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.set_score_pointer_widget_navigation_bindings(True)
        self.ui.give_focus_backward(self.ui_displayed_items)
        return "break"

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.set_score_pointer_widget_navigation_bindings(True)
        self.ui.give_focus_forward(self.ui_displayed_items)
        return "break"

    # The methods identical except for docstrings, and references to
    # self.ui.configure_game_grid or self.ui.configure_repertoire_grid
    # replaced by property self.ui_configure_item_list_grid.

    def cycle_item(self, prior=False):
        """Select next PGN score on display."""
        items = self.ui_displayed_items
        losefocus = items.active_item
        losefocus.bind_for_widget_navigation()
        items.cycle_active_item(prior=prior)
        self.ui_configure_item_list_grid()
        gainfocus = items.active_item
        gainfocus.set_game_list()
        gainfocus.bind_for_item_navigation()
        gainfocus.takefocus_widget.focus_set()
        gainfocus.set_statusbar_text()

    def give_focus_to_widget(self, event=None):
        """Select text item on display by mouse click."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        losefocus, gainfocus = self.ui_displayed_items.give_focus_to_widget(
            event.widget
        )
        if losefocus is not gainfocus:
            self.ui_configure_item_list_grid()
            self.score.after(
                0, func=self.try_command(self.ui_set_item_name, self.score)
            )
            self.score.after(
                0,
                func=self.try_command(gainfocus.refresh_game_list, self.score),
            )
        return "break"

    # The insert_game_database method, coerced into sameness from the methods
    # in gamedisplay._GameDisplay and repertoiredisplay._RepertoireDisplay with
    # class attibutes pgn_score_name, pgn_score_source_name, pgn_score_tags,
    # and method mark_partial_positions_to_be_recalculated, and property
    # ui_base_table.  The clarity of both common bits and differences
    # seems to justify the extra syntactic complexity.

    # Probably becomes insert_item_database() in each subclass like in
    # cqldbshow and all other *db* calls like it.

    # This was not going to be moved to displaypgn except insert_game_database,
    # which uses the class attribute pgn_score_updater, was moved.
    # Both game_updater and pgn_score_updater need more generic names.
    def game_updater(self, text):
        """Make and return a chess record containing a single PGN score."""
        updater = self.pgn_score_updater()
        updater.value.load(text)
        return updater

    # Code shared by on_game_change method in _GameDisplay and
    # _RepertoireDisplay.
    # Replace _pgn_score_ with _item_ to fit with displaypgn.ShowPGN perhaps,
    # but this one will be moved to subclasses.
    def patch_pgn_score_to_fit_record_change_and_refresh_grid(
        self, grid, instance
    ):
        if self.ui_displayed_items.is_item_panel_active(self):
            # Patch data structure to look as though the edited record has
            # been read from disk.  That means DataGrid, DisplayItems, and
            # this _GameDisplay or _RepertoireDisplay, instances.
            # self.sourceobject is DataGrid.get_visible_record(<key>), the
            # record prior to editing.
            # instance adds index structures to match those which should be
            # on database.
            # instance.newrecord is edited record including index stuff.
            key = None
            for e, k in enumerate(grid.keys):
                if instance.key.recno != k[0]:
                    key = k
                    break
            grid.close_client_cursor()
            grid.datasource.get_full_position_games(self.get_position_key())
            grid.fill_view(currentkey=key, exclude=False)


class DisplayText:

    """Mixin providing methods shared by the gamedisplay.GameDisplay
    and repertoiredisplay.RepertoireDisplay classes.

    Named DisplayPGN because ShowPGN is already taken, and when created the
    only methods in the class are delete_game_database and get_database_events.
    Both were in GameDisplay and RepertoireDisplay originally.

    insert_game_database is in ShowPGN, not here, because it is also used
    in the InsertPGN line.

    """

    def get_database_events(self):
        """Return event description tuple for PGN score database actions."""
        return (
            (EventSpec.display_insert, self.insert_item_database),
            (EventSpec.display_delete, self.delete_item_database),
        )


class InsertText:

    """Mixin providing methods shared by the gamedisplay.GameDisplayInsert
    and repertoiredisplay.RepertoireDisplayInsert classes.

    Provide methods involved in generating popup menus relevant to PGN score
    editing when inserting records.

    """

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    def get_database_events(self):
        """Return event description tuple for PGN score database actions."""
        return ((EventSpec.display_insert, self.insert_item_database),)


# Introduced to remove create_primary_activity_popup method from InsertText
# class: it's presence prevented displaypgn.InsertPGN being a subclass of
# InsertText.
# In the PGN classes the displayed list of games depends on which token is
# current, but in the non-PGN Text classes the displayed list of games is
# determined by evaluation of a query on demand.
# When inserting or editing a record the create_primary_activity_popup method
# of this class makes an option to demand evaluation available in a popup menu.
# When showing a record the demand is implicit in making the 'show' widget
# active.
# In the PGN classes the demand is always implicit in making a token current,
# so there is no PGN equivalent of ListGamesText.
class ListGamesText:

    """Mixin providing methods shared by the cqldisplay._CQLDisplay and
    and querydisplay._QueryDisplay classes.

    Provide methods involved in generating popup menus relevant to display
    of game lists when editing records.

    """

    def create_primary_activity_popup(self):
        popup = super().create_primary_activity_popup()
        self.add_list_games_entry_to_popup(popup)
        return popup


class EditText:

    """Mixin providing methods shared by the gamedisplay.GameDisplayEdit
    and repertoiredisplay.RepertoireDisplayEdit classes.

    Provide methods involved in generating popup menus relevant to PGN score
    editing when editing records.

    """

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    def get_database_events(self):
        """Return event description tuple for PGN score database actions."""
        return (
            (EventSpec.display_insert, self.insert_item_database),
            (EventSpec.display_update, self.update_item_database),
        )

    # update_game_database becomes update_item_database in cqldispaly and
    # querydisplay.
