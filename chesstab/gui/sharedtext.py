# sharedtext.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define navigation methods and bindings.

The classes are SharedText, SharedTextEngineText, and SharedTextScore.
"""

import tkinter

from .eventspec import EventSpec


class SharedText:
    """Provide navigation bindings for subclasses.

    Methods with the same name are used in one or both enginetext.EngineText
    and score.Score, but the internals are different.

    """

    def _set_primary_activity_bindings(self, switch=True):
        """Switch bindings for traversing query statement on or off."""
        self.set_event_bindings_score(
            self.get_f10_popup_events(
                self._post_active_menu_at_top_left, self._post_active_menu
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_button_events(buttonpress3=self._post_active_menu),
            switch=switch,
        )

    def set_score_pointer_item_navigation_bindings(self, switch):
        """Set or unset pointer bindings for game navigation."""
        self.set_event_bindings_score(
            self._get_button_events(buttonpress3=self._post_active_menu),
            switch=switch,
        )

    @staticmethod
    def get_primary_activity_events():
        """Return null tuple of navigation keypresses and callbacks."""
        return ()


class SharedTextEngineText:
    """Provide keypress and pointer navigation methods for subclasses.

    This is a separate hierarchy from SharedTextScore because the engine
    stuff is in a Toplevel instance not the main application widget.
    """

    @staticmethod
    def _get_modifier_buttonpress_suppression_events():
        """Return empty tuple of event binding definitions.

        These events suppress buttonpress with Control, Shift, or Alt.

        """
        return ()

    def _post_active_menu(self, event=None):
        """Show the popup menu for chess engine definition navigation."""
        return self._post_menu(
            self.primary_activity_popup,
            self._create_primary_activity_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )

    def _post_active_menu_at_top_left(self, event=None):
        """Show the popup menu for chess engine definition navigation."""
        return self.post_menu_at_top_left(
            self.primary_activity_popup,
            self._create_primary_activity_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )


class SharedTextScore:
    """Provide keypress and pointer navigation methods for subclasses.

    This is a separate hierarchy from SharedTextEngineText because the
    engine stuff is in a Toplevel instance not the main application
    widget.
    """

    def _add_cascade_menu_to_popup(
        self, label, popup, bindings=None, order=None, index=tkinter.END
    ):
        """Add cascade_menu, and bindings, to popup if not already present.

        The index is used as the label on the popup menu when visible.

        The bindings are not applied if cascade_menu is alreay in popup menu.

        """
        # Cannot see a way of asking 'Does entry exist?' other than:
        try:
            popup.index(label)
        except tkinter.TclError:
            cascade_menu = tkinter.Menu(master=popup, tearoff=False)
            popup.insert_cascade(label=label, menu=cascade_menu, index=index)
            if order is None:
                order = ()
            if bindings is None:
                bindings = {}
            for definition in order:
                function = bindings.get(definition)
                if function is not None:
                    cascade_menu.add_command(
                        label=definition[1],
                        command=self.try_command(function, cascade_menu),
                        accelerator=definition[2],
                    )

    # Subclasses which need widget navigation in their popup menus should
    # call this method.
    def _create_widget_navigation_submenu_for_popup(self, popup):
        """Create and populate a submenu of popup for widget navigation.

        The commands in the submenu should switch focus to another widget.

        Subclasses should define a generate_popup_navigation_maps method and
        binding_labels iterable suitable for allowed navigation.

        """
        navigation_map, local_map = self.generate_popup_navigation_maps()
        local_map.update(navigation_map)
        self._add_cascade_menu_to_popup(
            "Navigation", popup, bindings=local_map, order=self.binding_labels
        )

    # Subclasses which need dismiss widget in a menu should call this method.
    def _add_close_item_entry_to_popup(self, popup):
        """Add option to dismiss widget entry to popup.

        Subclasses must provide a delete_item_view method.

        """
        self._set_popup_bindings(popup, self._get_close_item_events())

    def _create_inactive_popup(self):
        """Create popup menu for an inactive widget."""
        assert self.inactive_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self._set_popup_bindings(popup, self._get_inactive_events())
        self._init_inactive_popup(popup)
        return popup

    def _get_inactive_button_events(self):
        """Return pointer event specifications for an inactive widget."""
        return self._get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_1, self.give_focus_to_widget),
            (EventSpec.buttonpress_3, self.post_inactive_menu),
        )

    def post_inactive_menu(self, event=None):
        """Show the popup menu for a game score in an inactive item."""
        return self._post_menu(
            self.inactive_popup, self._create_inactive_popup, event=event
        )

    def post_inactive_menu_at_top_left(self, event=None):
        """Show the popup menu for a game score in an inactive item."""
        return self.post_menu_at_top_left(
            self.inactive_popup, self._create_inactive_popup, event=event
        )

    def _get_inactive_events(self):
        """Return keypress event specifications for an inactive widget."""
        return (
            (EventSpec.display_make_active, self.set_focus_panel_item_command),
            (EventSpec.display_dismiss_inactive, self.delete_item_view),
        )
