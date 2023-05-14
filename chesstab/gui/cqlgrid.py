# cqlgrid.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for lists of Chess Query Language (ChessQL) statements on database."""

import tkinter.messagebox

from solentware_grid.datagrid import DataGrid

from ..core.chessrecord import ChessDBrecordPartial
from .cqldisplay import CQLDisplay, CQLDisplayEdit
from .cqlrow import ChessDBrowCQL
from ..core import export_chessql
from .eventspec import EventSpec
from .display import Display
from ..shared.cql_gamelist_query import CQLGameListQuery
from ..shared.allgrid import AllGrid


class CQLListGrid(AllGrid, CQLGameListQuery, DataGrid, Display):
    """A DataGrid for lists of ChessQL statements.

    Subclasses provide navigation and extra methods appropriate to list use.

    """

    def __init__(self, parent, ui):
        """Extend with link to user interface object.

        parent - see superclass
        ui - container for user interface widgets and methods.

        """
        super().__init__(parent=parent)
        self.ui = ui
        self._configure_frame_and_initial_event_bindings()

    def _display_selected_item_kind(self, key, selected):
        """Create CQLDisplay for ChessQL statement."""
        # Should the Frame containing board and position be created here and
        # passed to CQLDisplay. (Needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # CQLDisplay is to be put.
        selection = self.make_display_widget(selected)
        self.ui.add_partial_position_to_display(selection)
        self.ui.partial_items.increment_object_count(key)
        self.ui.partial_items.set_itemmap(selection, key)
        self.set_properties(key)
        return selection

    def make_display_widget(self, sourceobject):
        """Return a CQLDisplay for sourceobject."""
        selection = CQLDisplay(
            master=self.ui.view_partials_pw,
            ui=self.ui,
            items_manager=self.ui.partial_items,
            itemgrid=self.ui.partial_games,
            sourceobject=sourceobject,
        )
        #    sourceobject.get_srvalue())
        selection.cql_statement.process_statement(sourceobject.get_srvalue())
        return selection

    def _edit_selected_item(self, key):
        """Create a CQLDisplayEdit for ChessQL statement."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and position be created here and
        # passed to CQLDisplayEdit. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # CQLDisplayEdit is to be put.
        selection = self.make_edit_widget(selected)
        self.ui.add_partial_position_to_display(selection)
        self.ui.partial_items.increment_object_count(key)
        self.ui.partial_items.set_itemmap(selection, key)
        self.set_properties(key)
        return selection

    def make_edit_widget(self, sourceobject):
        """Return a CQLDisplayEdit for sourceobject."""
        selection = CQLDisplayEdit(
            master=self.ui.view_partials_pw,
            ui=self.ui,
            items_manager=self.ui.partial_items,
            itemgrid=self.ui.partial_games,
            sourceobject=sourceobject,
        )
        #    sourceobject.get_srvalue())
        selection.cql_statement.process_statement(sourceobject.get_srvalue())
        return selection

    def set_properties(self, key, dodefaultaction=True):
        """Return True if properties for ChessQL statement key set or False."""
        if super().set_properties(key, dodefaultaction=False):
            return True
        if self.ui.partial_items.object_display_count(key):
            self._set_background_on_display_row_under_pointer(key)
            return True
        if dodefaultaction:
            self._set_background_normal_row_under_pointer(key)
            return True
        return False

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for ChessQL statement key or None."""
        row = super().set_row(key, dodefaultaction=False, **kargs)
        if row is not None:
            return row
        if key not in self.keys:
            return None
        if self.ui.partial_items.object_display_count(key):
            return self.objects[key].grid_row_on_display(**kargs)
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        return None

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordPartial()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_delete_dialog(
            self.objects[key],
            oldobject,
            modal,
            title="Delete ChessQL Statement",
        )

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordPartial(),
            ChessDBrecordPartial(),
            False,
            modal,
            title="Edit ChessQL Statement",
        )

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordPartial(),
            ChessDBrecordPartial(),
            True,
            modal,
            title="Edit ChessQL Statement",
        )

    def launch_insert_new_record(self, modal=True):
        """Create insert dialogue."""
        instance = self.datasource.new_row()

        # Later process_statement() causes display of empty title and
        # query lines.
        instance.srvalue = repr("")

        self.create_edit_dialog(
            instance,
            ChessDBrecordPartial(),
            None,
            False,
            modal,
            title="New ChessQL Statement",
        )

    def launch_show_record(self, key, modal=True):
        """Create show dialogue."""
        oldobject = ChessDBrecordPartial()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_show_dialog(
            self.objects[key], oldobject, modal, title="Show ChessQL Statement"
        )

    def _export_partial(self, event=None):
        """Export selected partial position definitions."""
        del event
        export_chessql.export_selected_positions(
            self, self.ui.get_export_filename("Partial Positions", pgn=False)
        )


class CQLGrid(CQLListGrid):
    """Customized CQLListGrid for list of ChessQL statements."""

    def __init__(self, ui):
        """Extend with definition and bindings for ChessQL statements on grid.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.partials_pw, ui)
        self.make_header(ChessDBrowCQL.header_specification)
        self.__bind_on()
        self._set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self._display_cql_statement_from_popup,
                ),
                (
                    EventSpec.edit_record_from_grid,
                    self._edit_cql_statement_from_popup,
                ),
                (EventSpec.export_from_partial_grid, self._export_partial),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self._set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self._set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (
                EventSpec.navigate_to_active_partial,
                self._set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self._set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self._add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self._add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self._set_event_bindings_frame(
            (
                (EventSpec.navigate_to_active_partial, ""),
                (EventSpec.navigate_to_partial_game_grid, ""),
                (EventSpec.navigate_to_repertoire_grid, ""),
                (EventSpec.navigate_to_active_repertoire, ""),
                (EventSpec.navigate_to_repertoire_game_grid, ""),
                (EventSpec.navigate_to_position_grid, ""),
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_game_grid, ""),
                (EventSpec.navigate_to_selection_rule_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
                (EventSpec.export_from_partial_grid, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self._set_event_bindings_frame(
            (
                (
                    EventSpec.navigate_to_active_partial,
                    self.set_focus_partialpanel_item,
                ),
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
                (
                    EventSpec.navigate_to_active_game,
                    self.set_focus_gamepanel_item,
                ),
                (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
                (
                    EventSpec.navigate_to_selection_rule_grid,
                    self.set_focus_selection_rule_grid,
                ),
                (
                    EventSpec.navigate_to_active_selection_rule,
                    self.set_focus_selectionpanel_item,
                ),
                (
                    EventSpec.display_record_from_grid,
                    self._display_cql_statement,
                ),
                (EventSpec.edit_record_from_grid, self._edit_cql_statement),
                (EventSpec.export_from_partial_grid, self._export_partial),
            )
        )

    def _display_cql_statement(self, event=None):
        """Display ChessQL statement and cancel selection.

        Call _display_cql_statement_after_idle after idle tasks to allow
        message display.

        """
        del event
        if not self.get_visible_selected_key():
            return
        self._set_find_cql_statement_name_games(self.selection[0])
        self.frame.after_idle(
            self.try_command(
                self._display_cql_statement_after_idle, self.frame
            )
        )

    def _display_cql_statement_from_popup(self, event=None):
        """Display ChessQL statement selected by pointer.

        Call _display_cql_statement_after_idle after idle tasks to allow
        message display.

        """
        del event
        self._set_find_cql_statement_name_games(self.pointer_popup_selection)
        self.frame.after_idle(
            self.try_command(
                self._display_cql_statement_from_popup_after_idle, self.frame
            )
        )

    def _display_cql_statement_after_idle(self):
        """Display ChessQL statement and cancel selection.

        Call from _display_cql_statement only.

        """
        self._display_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def _display_cql_statement_from_popup_after_idle(self):
        """Display ChessQL statement selected by pointer.

        Call from _display_cql_statement_from_popup only.

        """
        self._display_selected_item(self.pointer_popup_selection)

    def _edit_cql_statement(self, event=None):
        """Display ChessQL statement allow editing and cancel selection.

        Call _edit_cql_statement_after_idle after idle tasks to allow
        message display.

        """
        del event
        if not self.get_visible_selected_key():
            return
        self._set_find_cql_statement_name_games(self.selection[0])
        self.frame.after_idle(
            self.try_command(self._edit_cql_statement_after_idle, self.frame)
        )

    def _edit_cql_statement_from_popup(self, event=None):
        """Display ChessQL statement with editing allowed selected by pointer.

        Call _edit_cql_statement_after_idle after idle tasks to allow
        message display.

        """
        del event
        self._set_find_cql_statement_name_games(self.pointer_popup_selection)
        self.frame.after_idle(
            self.try_command(
                self._edit_cql_statement_from_popup_after_idle, self.frame
            )
        )

    def _edit_cql_statement_after_idle(self):
        """Display ChessQL statement allow editing and cancel selection.

        Call from _edit_cql_statement only.

        """
        self._edit_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def _edit_cql_statement_from_popup_after_idle(self):
        """Display ChessQL statement with editing allowed selected by pointer.

        Call from _edit_cql_statement_from_popup only.

        """
        self._edit_selected_item(self.pointer_popup_selection)

    def _set_find_cql_statement_name_games(self, key):
        """Set status text to active ChessQL statement name."""
        if self.ui.partial_items.count_items_in_stack():
            # do search at this time only if no ChessQL statements displayed
            return
        self.ui.statusbar.set_status_text(
            "".join(
                (
                    "Please wait while finding games for ChessQL statement ",
                    self.objects[key].value.get_name_text(),
                )
            )
        )

    def on_partial_change(self, instance):
        # may turn out to be just to catch datasource is None
        """Refresh query grid after database update for instance."""
        if self.get_data_source() is None:
            return
        super().on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display ChessQL statement name."""
        if self.selection:
            value = self.objects[self.selection[0]].value
            self.ui.statusbar.set_status_text(
                "".join(
                    (
                        value.get_name_text(),
                        "   (",
                        value.get_statement_text(),
                        ")",
                    )
                )
            )
        else:
            self.ui.statusbar.set_status_text("")

    def is_visible(self):
        """Return True if list of ChessQL statements is displayed."""
        return str(self.get_frame()) in self.ui.partials_pw.panes()

    def make_display_widget(self, sourceobject):
        """Return a CQLDisplay for sourceobject."""
        selection = super().make_display_widget(sourceobject)
        selection.set_and_tag_item_text()
        return selection

    def make_edit_widget(self, sourceobject):
        """Return a CQLDisplayEdit for sourceobject."""
        selection = super().make_edit_widget(sourceobject)
        selection.set_and_tag_item_text(reset_undo=True)
        return selection

    def focus_set_frame(self, event=None):
        """Delegate to superclass then set toolbar widget states."""
        super().focus_set_frame(event=event)
        self.ui.set_toolbarframe_normal(
            self.ui.move_to_selection, self.ui.filter_selection
        )

    def set_selection(self, key):
        """Hack to fix edge case when inserting records using apsw or sqlite3.

        Workaround a KeyError exception when a record is inserted while a grid
        keyed by a secondary index with only one key value in the index is on
        display.

        """
        try:
            super().set_selection(key)
        except KeyError:
            tkinter.messagebox.showinfo(
                title="Insert ChessQL Statement Workaround",
                message="".join(
                    (
                        "All records have same name on this display.\n\nThe ",
                        "new record has been inserted but you need to Hide, ",
                        "and then Show, the display to see the record in ",
                        "the list.",
                    )
                ),
            )

    def on_data_change(self, instance):
        """Delegate to superclass by after_idle() if database is Symas LMMD.

        For other database engines delegate to superclass directly.

        """
        # Hack to prevent crash in _lmdb accessing Symas LMMD via lmdb.
        # The crash occurred on using the 'non-F11' options to insert, edit,
        # or delete, a ChessQL statement.
        # Problem seems to be a read-only transaction done in refresh_widgets
        # callbacks for chessql actions: which does not occur for other items.
        # There is, correctly at this point, no way to determine _lmdb is in
        # use apart from some assumption about the state of database engine.
        # The 'after_idle' route for all database engines may be fine too.
        if self.datasource.dbhome.dbenv.__class__.__name__ == "Environment":
            self.parent.after_idle(super().on_data_change, *(instance,))
        else:
            super().on_data_change(instance)
