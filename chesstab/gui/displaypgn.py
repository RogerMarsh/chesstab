# displaypgn.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define set bindings and navigation methods.

The methods in these classes are shared by classes in gamedisplay and
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

from .score import NonTagBind, ScoreNoGameException
from .scorepgn import ScorePGN
from .displaytext import ShowText, DisplayText, EditText, InsertText


# ShowPGN because DisplayPGN fits GameDisplay (and *Repertoire*)
# ShowText before ScorePGN because identical methods in ShowPGN and ShowText
# are deleted from ShowPGN.
class ShowPGN(ShowText, ScorePGN):
    """Provide methods to set bindinds and traverse visible items."""

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
        self._set_board_pointer_widget_navigation_bindings(True)
        self.set_analysis_score_pointer_to_analysis_score_bindings(False)
        self.set_analysis_score_pointer_to_analysis_score_bindings(False)

    # Probably becomes _set_item(), but stays here rather than moved to each
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
            for event_spec in (self._get_inactive_button_events(),):
                self.set_event_bindings_score(event_spec, switch=True)

    def _set_select_variation_bindings(self, switch=True):
        """Delegate then set navigation and close item bindings."""
        super()._set_select_variation_bindings(switch=switch)
        self._set_database_navigation_close_item_bindings(switch=switch)

    # The methods identical except for docstrings, and references to
    # self.ui.game_items or self.ui.repertoire_items replaced by property
    # self.ui_displayed_items.

    def _next_item(self, event=None):
        """Select next PGN score on display."""
        if self.ui_displayed_items.count_items_in_stack() > 1:
            self._cycle_item(prior=False)

    def _prior_item(self, event=None):
        """Select previous PGN score on display."""
        if self.ui_displayed_items.count_items_in_stack() > 1:
            self._cycle_item(prior=True)

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self._set_board_pointer_widget_navigation_bindings(True)
        return super().traverse_backward(event=event)

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self._set_board_pointer_widget_navigation_bindings(True)
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
    # class attibutes pgn_score_name, pgn_score_source, pgn_score_tags,
    # and method mark_partial_positions_to_be_recalculated, and property
    # ui_base_table.  The clarity of both common bits and differences
    # seems to justify the extra syntactic complexity.

    # Probably becomes _insert_item_database(), but stays here rather than
    # moved to each subclass: see displaytext.ShowText version.
    def _insert_item_database(self, event=None):
        """Add PGN score to database on request from item display."""
        del event
        title = " ".join(("Insert", self.pgn_score_name.title()))
        psn = self.pgn_score_name
        if self.ui_displayed_items.active_item is None:
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("No active ", " to insert into database.")),
            )
            return None

        # This should see if game with same PGN Tags already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Cannot add ", ":\n\nNo database open.")),
            )
            return None

        datasource = self.ui_base_table.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Cannot add ", ":\n\n", " list hidden.")),
            )
            return None
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message=psn.join(("Confirm request to add ", " to database")),
        ):
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Add ", " to database abandonned.")),
            )
            return None
        updater = self._game_updater(repr(self.score.get("1.0", tkinter.END)))
        if not updater.value.collected_game.is_pgn_valid():
            msg = [
                "Please re-confirm request to insert ",
                psn,
                ".",
            ]
            if not updater.value.collected_game.is_movetext_valid():
                msg.extend(["\n\nErrors exist in the Movetext."])
            if not updater.value.collected_game.is_tag_roster_valid():
                msg.extend(
                    [
                        "\n\nEither a mandatory Tag Pair is missing,",
                        '\n\nor a Tag Pair has value "" if this is ',
                        "not allowed.",
                    ]
                )
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(msg),
            ):
                return None
            updater.value.set_game_source(self.pgn_score_source)
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        self.mark_partial_positions_to_be_recalculated(datasource=datasource)
        updater.key.recno = None
        editor.put()
        tags = updater.value.collected_game.pgn_tags
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    psn.title(),
                    ' "',
                    "  ".join([tags.get(k, "") for k in self.pgn_score_tags]),
                    '" added to database.',
                )
            ),
        )
        return True


class DisplayPGN(DisplayText):
    """Provide method to delete an item from database."""

    def _delete_item_database(self, event=None):
        """Remove PGN score from database on request from item display."""
        del event
        title = " ".join(("Delete", self.pgn_score_name.title()))
        psn = self.pgn_score_name
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Cannot delete ", ":\n\nNo database open.")),
            )
            return
        datasource = self.ui_base_table.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Cannot delete ", ":\n\n", " list hidden.")),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(
                    (
                        "Cannot delete ",
                        "".join(
                            (
                                ":\n\nDatabase has been closed since ",
                                "this copy displayed.",
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
                message=psn.join(
                    (
                        "Cannot delete ",
                        "".join(
                            (
                                ":\n\nRecord has been amended since ",
                                "this copy displayed.",
                            )
                        ),
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message=psn.join(("Confirm request to delete ", " from database")),
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
        tags = original.value.collected_game.pgn_tags
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    psn.title(),
                    ' "',
                    "  ".join([tags.get(k, "") for k in self.pgn_score_tags]),
                    '" deleted from database.',
                )
            ),
        )


class InsertPGN(InsertText):
    """Provide methods to generate popup menus for inserting PGN scores."""

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    def _create_primary_activity_popup(self):
        """Delegate then set bindings for navigation and insert PGN."""
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
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_select_move_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_select_move_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_pgn_tag_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_pgn_tag_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_comment_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_comment_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_nag_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_nag_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_start_rav_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_start_rav_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_end_rav_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_end_rav_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_comment_to_end_of_line_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_comment_to_end_of_line_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_escape_whole_line_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_escape_whole_line_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _create_reserved_popup(self):
        """Delegate then set bindings for close item."""
        popup = super()._create_reserved_popup()
        self._add_close_item_entry_to_popup(popup)
        return popup

    def _set_edit_symbol_mode_bindings(self, switch=True, **ka):
        """Delegate then set bindings for navigation and close item."""
        super()._set_edit_symbol_mode_bindings(switch=switch, **ka)
        self._set_database_navigation_close_item_bindings(switch=switch)


class EditPGN(EditText):
    """Provide methods to generate popup menus for editing PGN scores."""

    def _update_item_database(self, event=None):
        """Modify existing PGN score record."""
        del event
        title = " ".join(("Edit", self.pgn_score_name.title()))
        psn = self.pgn_score_name
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Cannot edit ", ":\n\nNo database open.")),
            )
            return
        datasource = self.ui_base_table.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(("Cannot edit ", ":\n\n", " list hidden.")),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=title,
                message=psn.join(
                    (
                        "Cannot edit ",
                        "".join(
                            (
                                ":\n\nDatabase has been closed since ",
                                "this copy displayed.",
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
                message=psn.join(
                    (
                        "Cannot edit ",
                        "".join(
                            (
                                ":\n\nRecord has been amended since ",
                                "this copy displayed.",
                            )
                        ),
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title=title,
            message=psn.join(("Confirm request to edit ", ".")),
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
        updater = self._game_updater(repr(text))
        editor = RecordEdit(updater, original)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        if not updater.value.collected_game.is_pgn_valid():
            msg = [
                "Please re-confirm request to edit ",
                psn,
                ".",
            ]
            if not updater.value.collected_game.is_movetext_valid():
                msg.extend(["\n\nErrors exist in the Movetext."])
            if not updater.value.collected_game.is_tag_roster_valid():
                msg.extend(
                    [
                        "\n\nEither a mandatory Tag Pair is missing,",
                        '\n\nor a Tag Pair has value "" if this is ',
                        "not allowed.",
                    ]
                )
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(msg),
            ):
                return
            updater.value.set_game_source(self.pgn_score_source)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        self.mark_partial_positions_to_be_recalculated(datasource=datasource)
        editor.edit()
        if self is self.ui_displayed_items.active_item:
            newkey = self.ui_displayed_items.adjust_edited_item(updater)
            if newkey:
                self._set_properties_on_grids(newkey)
        tags = original.value.collected_game.pgn_tags
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    psn.title(),
                    ' "',
                    "  ".join([tags.get(k, "") for k in self.pgn_score_tags]),
                    '" amended on database.',
                )
            ),
        )
