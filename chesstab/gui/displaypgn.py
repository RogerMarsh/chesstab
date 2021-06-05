# displaypgn.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define methods shared by classes in gamedisplay and
repertoiredisplay modules which display Portable Game Notation (PGN) text.

The gamedisplay module has two sets of classes: based on the _GameDisplay and
GameDialogue classes.

The repertoiredisplay module has an identical structure where the _GameDisplay
and _RepertoireDisplay classes have many methods in common.

All methods in the classes in this module existed as multiple copies in various
classes in the gamedisplay and repertoiredisplay modules.  They are now deleted
from those modules.

The classes in this module represent the different sets of classes with methods
in common.  Two classes could reasonably be called DisplayPGN: the choice is
consistent with the naming of InsertPGN and EditPGN.  ShowPGN was chosen for
the other class.

The ShowPGN class is populated with the methods identical in _GameDisplay
and _RepertoireDisplay, which were then removed from those two classes.

The DisplayPGN class is populated with the methods identical in
GameDisplay and RepertoireDisplay, which were then removed
from those two classes.

The InsertPGN class is populated with the methods identical in
GameDisplayInsert and RepertoireDisplayInsert, which were then removed
from those two classes.

The EditPGN class is populated with the methods identical in
GameDisplayEdit and RepertoireDisplayEdit, which were then removed
from those two classes.  It probably should be a subclass of InsertPGN, but
this depends on successful choice of method resolution order in the classes
in gamedisplay and repertoiredisplay modules.

"""
import tkinter
import tkinter.messagebox

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete

from .eventspec import EventSpec
from .score import NonTagBind, ScoreNoGameException
from .scorepgn import ScorePGN
from .displaytext import ShowText, DisplayText, EditText, InsertText


# ShowPGN because DisplayPGN fits GameDisplay (and *Repertoire*)
# ShowText before ScorePGN because identical methods in ShowPGN and ShowText
# are deleted from ShowPGN.
class ShowPGN(ShowText, ScorePGN):

    """Mixin providing methods shared by the gamedisplay._GameDisplay and
    repertoiredisplay.RepertoreDisplay classes.

    Provide focus switching and widget visibility methods for widgets which
    display Portable Game Notation (PGN) text.

    The gamedisplay.GameDialogue and repertoire.RepertoireDialogue classes
    are used in a Toplevel which displays one game or repertoire.  The focus
    switching provided here is not needed.

    """

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    def bind_for_item_navigation(self):
        """Set bindings to navigate PGN score on pointer click."""
        if self.score is self.takefocus_widget:
            super().bind_for_item_navigation()
            self.set_board_pointer_move_bindings(True)
            self.analysis.set_score_pointer_item_navigation_bindings(False)
            self.set_score_pointer_to_score_bindings(False)
            self.set_analysis_score_pointer_to_analysis_score_bindings(True)
        else:
            self.analysis.set_board_pointer_move_bindings(True)
            self.set_score_pointer_item_navigation_bindings(False)
            self.analysis.set_score_pointer_item_navigation_bindings(True)
            self.set_score_pointer_to_score_bindings(True)
            self.set_analysis_score_pointer_to_analysis_score_bindings(False)
        self.set_toggle_game_analysis_bindings(True)

    def bind_for_widget_navigation(self):
        """Set bindings to give focus to this PGN score on pointer click."""
        super().bind_for_widget_navigation()
        self.set_board_pointer_widget_navigation_bindings(True)
        self.set_analysis_score_pointer_to_analysis_score_bindings(False)
        self.set_analysis_score_pointer_to_analysis_score_bindings(False)

    # Probably becomes set_item(), but stays here rather than moved to each
    # subclass: see displaytext.ShowText version.
    def set_and_tag_item_text(self, reset_undo=False):
        """Delegate to superclass method and set PGN score inactive."""

        # Superclass may set self._most_recent_bindings but test below must be
        # against current value.
        mrb = self._most_recent_bindings

        try:
            super().set_and_tag_item_text(reset_undo=reset_undo)
        except ScoreNoGameException:
            return
        if mrb != NonTagBind.NO_EDITABLE_TAGS:
            for es in (self.get_inactive_button_events(),):
                self.set_event_bindings_score(es, switch=True)

    def set_select_variation_bindings(self, switch=True):
        """Delegate to toggle other relevant bindings and toggle bindings for
        database actions, navigation to other widgets, and close widget.

        """
        super().set_select_variation_bindings(switch=switch)
        self.set_database_navigation_close_item_bindings(switch=switch)

    # The methods identical except for docstrings, and references to
    # self.ui.game_items or self.ui.repertoire_items replaced by property
    # self.ui_displayed_items.

    def next_item(self, event=None):
        """Select next PGN score on display."""
        if self.ui_displayed_items.count_items_in_stack() > 1:
            self.cycle_item(prior=False)

    def prior_item(self, event=None):
        """Select previous PGN score on display."""
        if self.ui_displayed_items.count_items_in_stack() > 1:
            self.cycle_item(prior=True)

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.set_board_pointer_widget_navigation_bindings(True)
        return super().traverse_backward(event=event)

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.set_board_pointer_widget_navigation_bindings(True)
        return super().traverse_forward(event=event)

    def give_focus_to_widget(self, event=None):
        """Select PGN score on display by mouse click."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        losefocus, gainfocus = self.ui_displayed_items.give_focus_to_widget(
            event.widget
        )
        if losefocus is not gainfocus:
            self.ui_configure_item_list_grid()
            gainfocus.set_game_list()
        return "break"

    # The insert_game_database method, coerced into sameness from the methods
    # in gamedisplay._GameDisplay and repertoiredisplay._RepertoireDisplay with
    # class attibutes pgn_score_name, pgn_score_source_name, pgn_score_tags,
    # and method mark_partial_positions_to_be_recalculated, and property
    # ui_base_table.  The clarity of both common bits and differences
    # seems to justify the extra syntactic complexity.

    # Probably becomes insert_item_database(), but stays here rather than moved
    # to each subclass: see displaytext.ShowText version.
    def insert_item_database(self, event=None):
        """Add PGN score to database on request from item display."""
        title = " ".join(("Insert", self.pgn_score_name.title()))
        mt = self.pgn_score_name
        if self.ui_displayed_items.active_item is None:
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("No active ", " to insert into database.")),
            )
            return

        # This should see if game with same PGN Tags already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Cannot add ", ":\n\nNo database open.")),
            )
            return

        datasource = self.ui_base_table.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Cannot add ", ":\n\n", " list hidden.")),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message=mt.join(("Confirm request to add ", " to database")),
        ):
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Add ", " to database abandonned.")),
            )
            return
        updater = self.game_updater(repr(self.score.get("1.0", tkinter.END)))
        if not updater.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(
                    (
                        "The new ",
                        "".join(
                            (
                                " score contains at least one illegal move in ",
                                "PGN.\n\nPlease re-confirm request to insert ",
                            )
                        ),
                        ".",
                    )
                ),
            ):
                return
            updater.value.set_game_source(self.pgn_score_source_name)
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        self.mark_partial_positions_to_be_recalculated(datasource=datasource)
        updater.key.recno = None
        editor.put()
        tags = updater.value.collected_game._tags
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    mt.title(),
                    ' "',
                    "  ".join([tags.get(k, "") for k in self.pgn_score_tags]),
                    '" added to database.',
                )
            ),
        )
        return True


class DisplayPGN(DisplayText):

    """Mixin providing methods shared by the gamedisplay.GameDisplay
    and repertoiredisplay.RepertoireDisplay classes.

    Named DisplayPGN because ShowPGN is already taken, and when created the
    only methods in the class are delete_game_database and get_database_events.
    Both were in GameDisplay and RepertoireDisplay originally.

    insert_game_database is in ShowPGN, not here, because it is also used
    in the InsertPGN line.

    """

    def delete_item_database(self, event=None):
        """Remove PGN score from database on request from item display."""
        title = " ".join(("Delete", self.pgn_score_name.title()))
        mt = self.pgn_score_name
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Cannot delete ", ":\n\nNo database open.")),
            )
            return
        datasource = self.ui_base_table.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Cannot delete ", ":\n\n", " list hidden.")),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(
                    (
                        "Cannot delete ",
                        "".join(
                            (
                                ":\n\nDatabase has been closed since this copy ",
                                "displayed.",
                            )
                        ),
                    )
                ),
            )
            return
        if self.blockchange:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(
                    (
                        "Cannot delete ",
                        ":\n\nRecord has been amended since this copy displayed.",
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message=mt.join(("Confirm request to delete ", " from database")),
        ):
            return
        original = self.pgn_score_updater()
        original.load_record(
            (self.sourceobject.key.recno, self.sourceobject.srvalue)
        )
        self.pgn_score_original_value(original.value)
        editor = RecordDelete(original)
        editor.set_data_source(datasource, editor.on_data_change)
        self.mark_partial_positions_to_be_recalculated(datasource=datasource)
        editor.delete()
        tags = original.value.collected_game._tags
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    mt.title(),
                    ' "',
                    "  ".join([tags.get(k, "") for k in self.pgn_score_tags]),
                    '" deleted from database.',
                )
            ),
        )


class InsertPGN(InsertText):

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
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_select_move_popup(self):
        popup = super().create_select_move_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_pgn_tag_popup(self):
        popup = super().create_pgn_tag_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_comment_popup(self):
        popup = super().create_comment_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_nag_popup(self):
        popup = super().create_nag_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_start_rav_popup(self):
        popup = super().create_start_rav_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_end_rav_popup(self):
        popup = super().create_end_rav_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_comment_to_end_of_line_popup(self):
        popup = super().create_comment_to_end_of_line_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_escape_whole_line_popup(self):
        popup = super().create_escape_whole_line_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def create_reserved_popup(self):
        popup = super().create_reserved_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def set_edit_symbol_mode_bindings(self, switch=True, **ka):
        """Delegate to toggle other relevant bindings and toggle bindings for
        database actions, navigation to other widgets, and close widget.

        """
        super().set_edit_symbol_mode_bindings(switch=switch, **ka)
        self.set_database_navigation_close_item_bindings(switch=switch)


class EditPGN(EditText):

    """Mixin providing methods shared by the gamedisplay.GameDisplayEdit
    and repertoiredisplay.RepertoireDisplayEdit classes.

    Provide methods involved in generating popup menus relevant to PGN score
    editing when editing records.

    """

    def update_item_database(self, event=None):
        """Modify existing PGN score record."""
        title = " ".join(("Edit", self.pgn_score_name.title()))
        mt = self.pgn_score_name
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Cannot edit ", ":\n\nNo database open.")),
            )
            return
        datasource = self.ui_base_table.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(("Cannot edit ", ":\n\n", " list hidden.")),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(
                    (
                        "Cannot edit ",
                        "".join(
                            (
                                ":\n\nDatabase has been closed since this copy ",
                                "displayed.",
                            )
                        ),
                    )
                ),
            )
            return
        if self.blockchange:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(
                    (
                        "Cannot edit ",
                        ":\n\nRecord has been amended since this copy displayed.",
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message=mt.join(("Confirm request to edit ", ".")),
        ):
            return
        original = self.pgn_score_updater()
        original.load_record(
            (self.sourceobject.key.recno, self.sourceobject.srvalue)
        )
        self.pgn_score_original_value(original.value)

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        text = self.get_score_error_escapes_removed()
        updater = self.game_updater(repr(text))
        editor = RecordEdit(updater, original)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        if not updater.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message=mt.join(
                    (
                        "The edited ",
                        "".join(
                            (
                                " score contains at least one illegal move in ",
                                "PGN.\n\nPlease re-confirm request to edit ",
                            )
                        ),
                        ".",
                    )
                ),
            ):
                return
            updater.value.set_game_source(self.pgn_score_source_name)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        self.mark_partial_positions_to_be_recalculated(datasource=datasource)
        editor.edit()
        if self is self.ui_displayed_items.active_item:
            newkey = self.ui_displayed_items.adjust_edited_item(updater)
            if newkey:
                self.set_properties_on_grids(newkey)
        tags = original.value.collected_game._tags
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    mt.title(),
                    ' "',
                    "  ".join([tags.get(k, "") for k in self.pgn_score_tags]),
                    '" amended on database.',
                )
            ),
        )
