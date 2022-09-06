# cql_gamelist_query.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""CQLGamelistQuery class for methods shared by most *ListGrid classes.

'Most' means CQLListGrid, GameListGrid, and QueryListGrid.

See allgrid.AllGrid class for methods identical in EngineListGrid class too.
"""
import tkinter

from ..gui.eventspec import EventSpec


class CQLGameListQuery:
    """Provide methods shared by CQLListGrid, GameListGrid, and QueryGrid."""

    def set_popup_bindings(self, popup, bindings=()):
        """Set popup menu bindings for game list grid."""
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
        except tkinter.TclError:
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

    def display_selected_item(self, key):
        """Create display item for selected record."""
        selected = self.get_visible_record(key)
        if selected is None:
            return None
        self._display_selected_item(key, selected)

    def select_down(self):
        """Extend to show selection summary in status bar."""
        super().select_down()
        self.set_selection_text()

    def select_up(self):
        """Extend to show selection summary in status bar."""
        super().select_up()
        self.set_selection_text()

    def cancel_selection(self):
        """Extend to clear selection summary from status bar."""
        if self.selection:
            self.ui.statusbar.set_status_text("")
        super().cancel_selection()

    def _set_background_on_display_row_under_pointer(self, key):
        self.objects[key].set_background_on_display(self.get_row_widgets(key))
        self.set_row_under_pointer_background(key)

    def _set_background_normal_row_under_pointer(self, key):
        self.objects[key].set_background_normal(self.get_row_widgets(key))
        self.set_row_under_pointer_background(key)

    def _configure_frame_and_initial_event_bindings(self, ui):
        self._configure_frame()
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