# display.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide focus switching and widget visibility methods shared by widgets.
"""

import tkinter

from .eventspec import DummyEvent


class Display(object):

    """Mixin providing focus switching and widget visibility methods.

    The User Interface has sets of related widgets: each set has a widget to:
        Display a list of similar records on the database.
        Dlsplay detail of selected records from the list.
        Display a list of records matching some condition on the active detail.

    Widgets are displayed when needed, or sometimes on request, so the focus
    switchers check the target is available before switching.  Transitions
    exist where this is not strictly necessary, but it is assumed cheaper to
    ask anyway than check if asking is essential first as well.

    """

    def bind_for_widget_navigation(self):
        """Subclasses shall override this method if necessary.

        Set pointer bindings for this widget to become the active item of it's
        type and regain the focus.

        An active item will have specific bindings, such as to traverse a game
        score and display the corresponding board position.

        An inactive item has bindings allowing it to take focus, and possibly
        other more general actions.  This method is intended to switch to these
        bindings when an active item becomes inactive.

        An inactive item never has the focus, but an active item does not have
        the focus necessarily: the active repertoire may have the focus which
        implies the active game does not, for example.

        The widgets displaying list of records are probably always active since
        there is not an alternative list displayed concurrently: in the sense
        this game is the active game, not that one.

        """

    def has_focus(self):
        """Return True if the item's takefocus widget has the focus."""
        return self.takefocus_widget.focus_displayof() == self.takefocus_widget

    def set_focus_game_grid(self, event=None):
        """Give widget displaying list of games on database the focus."""
        if not self.ui.base_games.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_game_grid(event=event)

    def set_focus_partial_game_grid(self, event=None):
        """Give widget displaying list of games for partial position focus."""
        if not self.ui.partial_games.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_partial_game_grid(event=event)

    def set_focus_partial_grid(self, event=None):
        """Give widget displaying list of partial positions the focus."""
        if not self.ui.base_partials.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_partial_grid(event=event)

    def set_focus_partialpanel_item(self, event=None):
        """Give partial position at top of stack the focus."""
        if self.ui.partial_items.active_item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_partialpanel_item(event=event)

    def set_focus_partialpanel_item_command(self):
        """Give partial position at top of stack the focus."""
        item = self.ui.partial_items.active_item
        if item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_partialpanel_item(
            event=DummyEvent(item.get_top_widget())
        )

    def set_focus_gamepanel_item(self, event=None):
        """Give game at top of stack the focus."""
        if self.ui.game_items.active_item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_gamepanel_item(event=event)

    def set_focus_gamepanel_item_command(self):
        """Give repertoire game at top of stack the focus."""
        items = self.ui.game_items
        if items.active_item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_gamepanel_item(
            event=DummyEvent(items.get_active_item_top_widget())
        )

    # The alternative name set_focus_game_game_grid fits style of other names.
    def set_focus_position_grid(self, event=None):
        """Give widget displaying list of games matching position the focus."""
        if not self.ui.game_games.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_position_grid(event=event)

    def set_focus_repertoire_game_grid(self, event=None):
        """Give widget displaying list of games for repertoire focus."""
        if not self.ui.repertoire_games.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_repertoire_game_grid(event=event)

    def set_focus_repertoire_grid(self, event=None):
        """Give focus to widget displaying list of database repertoire games."""
        if not self.ui.base_repertoires.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_repertoire_grid(event=event)

    def set_focus_repertoirepanel_item(self, event=None):
        """Give repertoire game at top of stack the focus."""
        if self.ui.repertoire_items.active_item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_repertoirepanel_item(event=event)

    def set_focus_repertoirepanel_item_command(self):
        """Give repertoire game at top of stack the focus."""
        item = self.ui.repertoire_items.active_item
        if item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_repertoirepanel_item(
            event=DummyEvent(item.get_top_widget())
        )

    def set_focus_panel_item_command(self):
        """Give self the focus."""
        self.give_focus_to_widget(event=DummyEvent(self.get_top_widget()))

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order.

        Subclasses shall override if required."""
        # Do nothing.
        return "break"

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order.

        Subclasses shall override if required."""
        # Do nothing.
        return "break"

    def traverse_round(self, event=None):
        """Give focus to next widget within active item in traversal order.

        Subclasses shall override if required."""
        # Do nothing.
        return "break"

    def forget_payload(self, parent):
        """Remove payload widget from it's parent panedwindow."""
        parent.forget(self.get_frame())

    def insert_payload(self, parent):
        """Insert payload widget in it's parent panedwindow."""
        parent.insert(tkinter.END, self.get_frame(), weight=1)

    def set_focus_selection_rule_grid(self, event=None):
        """Give widget displaying list of selection_rules the focus."""
        if not self.ui.base_selections.is_visible():
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_selection_rule_grid(event=event)

    def set_focus_selectionpanel_item(self, event=None):
        """Give selection_rule at top of stack the focus."""
        if self.ui.selection_items.active_item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_selectionpanel_item(event=event)

    def set_focus_selectionpanel_item_command(self):
        """Give selection rule at top of stack the focus."""
        item = self.ui.selection_items.active_item
        if item is None:
            return
        self.bind_for_widget_navigation()
        return self.ui.set_focus_selectionpanel_item(
            event=DummyEvent(item.get_top_widget())
        )
