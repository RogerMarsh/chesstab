# querygrid.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of selection rules on chess database.
"""

import tkinter.messagebox

from solentware_grid.datagrid import DataGrid

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from ..core.chessrecord import ChessDBrecordQuery
from .querydisplay import QueryDisplay, QueryDisplayEdit
from .queryrow import ChessDBrowQuery
from ..core import exporters
from .eventspec import EventSpec, DummyEvent
from .display import Display


class QueryListGrid(ExceptionHandler, DataGrid, Display):

    """A DataGrid for lists of game selection rules.

    Subclasses provide navigation and extra methods appropriate to list use.

    """

    def __init__(self, parent, ui):
        """Extend with link to user interface object.

        parent - see superclass
        ui - container for user interface widgets and methods.

        """
        super(QueryListGrid, self).__init__(parent=parent)
        self.gcanvas.configure(takefocus=tkinter.FALSE)
        self.data.configure(takefocus=tkinter.FALSE)
        self.frame.configure(takefocus=tkinter.FALSE)
        self.hsbar.configure(takefocus=tkinter.FALSE)
        self.vsbar.configure(takefocus=tkinter.FALSE)
        self.ui = ui
        self.set_event_bindings_frame(
            (
                (EventSpec.tab_traverse_forward, self.traverse_forward),
                (EventSpec.tab_traverse_backward, self.traverse_backward),
                (EventSpec.tab_traverse_round, self.traverse_round),
                # Remove entries when binding implemented in solentware_grid.
                (
                    EventSpec.score_enable_F10_popupmenu_at_top_left,
                    self.show_grid_or_row_popup_menu_at_top_left_by_keypress,
                ),
                (
                    EventSpec.score_enable_F10_popupmenu_at_pointer,
                    self.show_grid_or_row_popup_menu_at_pointer_by_keypress,
                ),
            )
        )

    def display_selected_item(self, key):
        """Create QueryDisplay for game selection rule."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and position be created here and
        # passed to QueryDisplay. (Needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # QueryDisplay is to be put.
        selection = self.make_display_widget(selected)
        self.ui.add_selection_rule_to_display(selection)
        self.ui.selection_items.increment_object_count(key)
        self.ui.selection_items.set_itemmap(selection, key)
        self.set_properties(key)
        return selection

    def make_display_widget(self, sourceobject):
        """Return a QueryDisplay for sourceobject."""
        selection = QueryDisplay(
            master=self.ui.view_selection_rules_pw,
            ui=self.ui,
            items_manager=self.ui.selection_items,
            itemgrid=self.ui.base_games,
            sourceobject=sourceobject,
        )
        selection.query_statement.set_database(
            self.ui.base_games.datasource.dbhome
        )
        selection.query_statement.dbset = self.ui.base_games.datasource.dbset
        selection.query_statement.process_query_statement(
            sourceobject.get_srvalue()
        )
        return selection

    def edit_selected_item(self, key):
        """Create a QueryDisplayEdit for game selection rule."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        # Should the Frame containing board and position be created here and
        # passed to QueryDisplayEdit. (Which needs 'import Tkinter' above.)
        # Rather than passing the container where the Frame created by
        # QueryDisplayEdit is to be put.
        selection = self.make_edit_widget(selected)
        self.ui.add_selection_rule_to_display(selection)
        self.ui.selection_items.increment_object_count(key)
        self.ui.selection_items.set_itemmap(selection, key)
        self.set_properties(key)
        return selection

    def make_edit_widget(self, sourceobject):
        """Return a QueryDisplayEdit for sourceobject."""
        selection = QueryDisplayEdit(
            master=self.ui.view_selection_rules_pw,
            ui=self.ui,
            items_manager=self.ui.selection_items,
            itemgrid=self.ui.base_games,
            sourceobject=sourceobject,
        )
        selection.query_statement.set_database(
            self.ui.base_games.datasource.dbhome
        )
        selection.query_statement.dbset = self.ui.base_games.datasource.dbset
        selection.query_statement.process_query_statement(
            sourceobject.get_srvalue()
        )
        return selection

    def set_properties(self, key, dodefaultaction=True):
        """Return True if properties for selection rule key set or False."""
        if super(QueryListGrid, self).set_properties(
            key, dodefaultaction=False
        ):
            return True
        if self.ui.selection_items.object_display_count(key):
            self.objects[key].set_background_on_display(
                self.get_row_widgets(key)
            )
            self.set_row_under_pointer_background(key)
            return True
        if dodefaultaction:
            self.objects[key].set_background_normal(self.get_row_widgets(key))
            self.set_row_under_pointer_background(key)
            return True
        return False

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for selection rule key or None."""
        row = super(QueryListGrid, self).set_row(
            key, dodefaultaction=False, **kargs
        )
        if row is not None:
            return row
        if key not in self.keys:
            return None
        if self.ui.selection_items.object_display_count(key):
            return self.objects[key].grid_row_on_display(**kargs)
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        else:
            return None

    def select_down(self):
        """Extend to show selection summary in status bar."""
        super(QueryListGrid, self).select_down()
        self.set_selection_text()

    def select_up(self):
        """Extend to show selection summary in status bar."""
        super(QueryListGrid, self).select_up()
        self.set_selection_text()

    def cancel_selection(self):
        """Extend to clear selection summary from status bar."""
        if self.selection:
            self.ui.statusbar.set_status_text("")
        super(QueryListGrid, self).cancel_selection()

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordQuery()
        oldobject.set_database(self.ui.base_games.datasource.dbhome)
        oldobject.value.dbset = self.ui.base_games.datasource.dbset
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_delete_dialog(
            self.objects[key], oldobject, modal, title="Delete Selection Rule"
        )

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordQuery(),
            ChessDBrecordQuery(),
            False,
            modal,
            title="Edit Selection Rule",
        )

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordQuery(),
            ChessDBrecordQuery(),
            True,
            modal,
            title="Edit Selection Rule",
        )

    def launch_insert_new_record(self, modal=True):
        """Create insert dialogue."""
        instance = self.datasource.new_row()

        # Later process_query_statement() causes display of empty title and
        # query lines.
        instance.srvalue = repr("")

        self.create_edit_dialog(
            instance,
            ChessDBrecordQuery(),
            None,
            False,
            modal,
            title="New Selection Rule",
        )

    def launch_show_record(self, key, modal=True):
        """Create show dialogue."""
        oldobject = ChessDBrecordQuery()
        oldobject.set_database(self.ui.base_games.datasource.dbhome)
        oldobject.value.dbset = self.ui.base_games.datasource.dbset
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_show_dialog(
            self.objects[key], oldobject, modal, title="Show Selection Rule"
        )

    def create_edit_dialog(
        self, instance, newobject, oldobject, showinitial, modal, title=""
    ):
        """Extend to do chess initialization."""
        for x in (newobject, oldobject):
            if x:
                x.set_database(self.ui.base_games.datasource.dbhome)
                x.value.dbset = self.ui.base_games.datasource.dbset
                x.load_record((instance.key.pack(), instance.srvalue))
        super(QueryListGrid, self).create_edit_dialog(
            instance, newobject, oldobject, showinitial, modal, title=title
        )

    def fill_view(
        self,
        currentkey=None,
        down=True,
        topstart=True,
        exclude=True,
    ):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.

        if self.get_database() is not None:
            super(QueryListGrid, self).fill_view(
                currentkey=currentkey,
                down=down,
                topstart=topstart,
                exclude=exclude,
            )

    def load_new_index(self):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.

        if self.get_database() is not None:
            super(QueryListGrid, self).load_new_index()

    def load_new_partial_key(self, key):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.

        if self.get_database() is not None:
            super(QueryListGrid, self).load_new_partial_key(key)

    def on_configure_canvas(self, event=None):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.

        if self.get_database() is not None:
            super(QueryListGrid, self).on_configure_canvas(event=event)

    def on_data_change(self, instance):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.

        if self.get_database() is not None:
            super(QueryListGrid, self).on_data_change(instance)

    def set_popup_bindings(self, popup, bindings=()):
        for accelerator, function in bindings:
            popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, popup),
                accelerator=accelerator[2],
            )

    def add_cascade_menu_to_popup(self, index, popup, bindings=None):
        """Add cascade_menu, and bindings, to popup if not already present.

        The index is used as the label on the popup menu when visible.

        The bindings are not applied if cascade_menu is alreay in popup menu.

        """
        # Cannot see a way of asking 'Does entry exist?' other than:
        try:
            popup.index(index)
        except:
            cascade_menu = tkinter.Menu(master=popup, tearoff=False)
            popup.add_cascade(label=index, menu=cascade_menu)
            if bindings is None:
                return
            self.set_popup_bindings(cascade_menu, bindings)

    def set_event_bindings_frame(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        for sequence, function in bindings:
            self.frame.bind(
                sequence[0], ste(function) if switch and function else ""
            )

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.ui.give_focus_backward(self)
        return "break"

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.ui.give_focus_forward(self)
        return "break"

    def traverse_round(self, event=None):
        """Give focus to next widget within active item in traversal order."""
        return "break"

    def set_focus(self):
        """Give focus to this widget."""
        self.frame.focus_set()
        if self.ui.single_view:
            self.ui.show_just_panedwindow_with_focus(self.frame)

    def is_payload_available(self):
        """Return True if grid is connected to a database."""
        ds = self.get_data_source()
        if ds is None:
            return False
        if ds.get_database() is None:

            # Avoid exception scrolling visible grid not connected to database.
            # Make still just be hack to cope with user interface activity
            # while importing data.
            self.clear_grid_keys()

            return False
        return True

    def export_selection_rules(self, event=None):
        """Export selected selection rule definitions."""
        exporters.export_selected_selection_rules(
            self, self.ui.get_export_filename("Selection Rules", pgn=False)
        )

    def focus_set_frame(self, event=None):
        """Adjust widget which is losing focus then delegate to superclass."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        super().focus_set_frame(event=event)

    def bind_for_widget_without_focus(self):
        """Return True if this item has the focus about to be lost."""
        if self.get_frame().focus_displayof() != self.get_frame():
            return False

        # Nothing to do on losing focus.
        return True

    def get_top_widget(self):
        """Return topmost widget for game display.

        The topmost widget is put in a container widget in some way.

        """
        # Superclass DataGrid.get_frame() method returns the relevant widget.
        # Name, get_top_widget, is compatible with Game and Partial names.
        return self.get_frame()

    def get_visible_selected_key(self):
        """Return selected key if it is visible and display dialogue if not.

        Getting the key is delegated to superclass.

        """
        key = super().get_visible_selected_key()
        if key is None:
            tkinter.messagebox.showinfo(
                parent=self.parent,
                title="Display Item",
                message="No record selected or selected record is not visible",
            )
        return key


class QueryGrid(QueryListGrid):

    """Customized QueryListGrid for list of game selection rules."""

    def __init__(self, ui):
        """Extend with definition and bindings for selection rules on grid.

        ui - container for user interface widgets and methods.

        """
        super(QueryGrid, self).__init__(ui.selection_rules_pw, ui)
        self.make_header(ChessDBrowQuery.header_specification)
        self.__bind_on()
        self.set_popup_bindings(
            self.menupopup,
            (
                (
                    EventSpec.display_record_from_grid,
                    self.display_selection_rule_from_popup,
                ),
                (
                    EventSpec.edit_record_from_grid,
                    self.edit_selection_rule_from_popup,
                ),
            ),
        )
        bindings = (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (
                EventSpec.navigate_to_active_game,
                self.set_focus_gamepanel_item_command,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item_command,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (
                EventSpec.navigate_to_active_partial,
                self.set_focus_partialpanel_item_command,
            ),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item_command,
            ),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
        )
        self.add_cascade_menu_to_popup("Navigation", self.menupopup, bindings)
        self.add_cascade_menu_to_popup(
            "Navigation", self.menupopupnorow, bindings
        )

    def bind_off(self):
        """Disable all bindings."""
        super(QueryGrid, self).bind_off()
        self.set_event_bindings_frame(
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
                (EventSpec.navigate_to_partial_grid, ""),
                (EventSpec.navigate_to_active_selection_rule, ""),
                (EventSpec.display_record_from_grid, ""),
                (EventSpec.edit_record_from_grid, ""),
            )
        )

    def bind_on(self):
        """Enable all bindings."""
        super(QueryGrid, self).bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self.set_event_bindings_frame(
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
                    EventSpec.navigate_to_partial_grid,
                    self.set_focus_partial_grid,
                ),
                (
                    EventSpec.navigate_to_active_selection_rule,
                    self.set_focus_selectionpanel_item,
                ),
                (
                    EventSpec.display_record_from_grid,
                    self.display_selection_rule,
                ),
                (EventSpec.edit_record_from_grid, self.edit_selection_rule),
            )
        )

    def display_selection_rule(self, event=None):
        """Display selection rule and cancel selection.

        Call _display_selection_rule after idle tasks to allow message display.

        """
        if not self.get_visible_selected_key():
            return
        self._set_find_selection_rule_name_games(self.selection[0])
        self.frame.after_idle(
            self.try_command(self._display_selection_rule, self.frame)
        )

    def display_selection_rule_from_popup(self, event=None):
        """Display selection rule selected by pointer.

        Call _display_selection_rule after idle tasks to allow message display.

        """
        self._set_find_selection_rule_name_games(self.pointer_popup_selection)
        self.frame.after_idle(
            self.try_command(
                self._display_selection_rule_from_popup, self.frame
            )
        )

    def _display_selection_rule(self):
        """Display selection rule and cancel selection.

        Call from display_selection_rule only.

        """
        self.display_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def _display_selection_rule_from_popup(self):
        """Display selection rule selected by pointer.

        Call from display_selection_rule_from_popup only.

        """
        self.display_selected_item(self.pointer_popup_selection)

    def edit_selection_rule(self, event=None):
        """Display selection rule allow editing and cancel selection.

        Call _edit_selection_rule after idle tasks to allow message display.

        """
        if not self.get_visible_selected_key():
            return
        self._set_find_selection_rule_name_games(self.selection[0])
        self.frame.after_idle(
            self.try_command(self._edit_selection_rule, self.frame)
        )

    def edit_selection_rule_from_popup(self, event=None):
        """Display selection rule with editing allowed selected by pointer.

        Call _edit_selection_rule after idle tasks to allow message display.

        """
        self._set_find_selection_rule_name_games(self.pointer_popup_selection)
        self.frame.after_idle(
            self.try_command(self._edit_selection_rule_from_popup, self.frame)
        )

    def _edit_selection_rule(self):
        """Display selection rule allow editing and cancel selection.

        Call from edit_selection_rule only.

        """
        self.edit_selected_item(self.get_visible_selected_key())
        self.cancel_selection()

    def _edit_selection_rule_from_popup(self):
        """Display selection rule with editing allowed selected by pointer.

        Call from edit_selection_rule_from_popup only.

        """
        self.edit_selected_item(self.pointer_popup_selection)

    def _set_find_selection_rule_name_games(self, key):
        """Set status text to active selection rule name."""
        if self.ui.selection_items.count_items_in_stack():
            # do search at this time only if no selection rules displayed
            return
        self.ui.statusbar.set_status_text(
            "".join(
                (
                    "Please wait while finding games for selection rule ",
                    self.objects[key].value.get_name_text(),
                )
            )
        )

    def on_partial_change(self, instance):
        # may turn out to be just to catch datasource is None
        if self.get_data_source() is None:
            return
        super(QueryGrid, self).on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display selection rule name."""
        if self.selection:
            p = self.objects[self.selection[0]].value
            self.ui.statusbar.set_status_text(
                "".join(
                    (
                        p.get_name_text(),
                        "   (",
                        p.get_query_statement_text(),
                        ")",
                    )
                )
            )
        else:
            self.ui.statusbar.set_status_text("")

    def is_visible(self):
        """Return True if list of selection rules is displayed."""
        return str(self.get_frame()) in self.ui.selection_rules_pw.panes()

    def make_display_widget(self, sourceobject):
        """Return a QueryDisplay for sourceobject."""
        selection = super().make_display_widget(sourceobject)
        selection.set_and_tag_item_text()
        return selection

    def make_edit_widget(self, sourceobject):
        """Return a QueryDisplayEdit for sourceobject."""
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
                parent=self.parent,
                title="Insert Selection Rule Workaround",
                message="".join(
                    (
                        "All records have same name on this display.\n\nThe new ",
                        "record has been inserted but you need to Hide, and then ",
                        "Show, the display to see the record in the list.",
                    )
                ),
            )
