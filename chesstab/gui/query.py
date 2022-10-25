# query.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a game selection rule.

A game selection rule is a query language statement used to select games which
match the conditions stated in the statement.

The query language syntax is defined in module solentware_base.core.where.

The Query class displays a game selection rule.

An instance of this class fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

The queryedit module provides a subclass which allows editing in the main
application window.

The querydbshow and querydbedit modules provide subclasses used in a
new toplevel widget to display or edit game selection rules.

The querydbdelete module provides a subclass used in a new toplevel widget
to allow deletion of game selection rules from a database.

"""

import tkinter

from .querytext import QueryText
from .eventspec import EventSpec
from .eventbinding import EventBinding


class Query(QueryText, EventBinding):
    """Game selection rule widget.

    master is used as the master argument for the tkinter Frame widget passed
    to superclass.

    boardfont is no longer used.

    See superclass for ui, items_manager, and itemgrid, arguments.  These may
    be, or have been, absorbed into **ka argument.

    """

    def __init__(
        self,
        master=None,
        boardfont=None,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka
    ):
        """Create Frame , delegate to superclass, and set geometry manager."""
        del boardfont
        panel = tkinter.Frame(
            master=master, cnf=dict(borderwidth=2, relief=tkinter.RIDGE)
        )
        panel.grid_propagate(False)
        super().__init__(
            panel, ui=ui, items_manager=items_manager, itemgrid=itemgrid, **ka
        )
        self.scrollbar.grid(column=1, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.score.grid(column=0, row=0, rowspan=1, sticky=tkinter.NSEW)
        if not ui.visible_scrollbars:
            panel.after_idle(self.hide_scrollbars)
        self.bind(
            panel, "<Configure>", function=self.try_event(self._on_configure)
        )
        self._configure_selection_widget()

        # The popup menus specific to Query (placed same as Game equivalent)

        # self.primary_activity_popup.add_cascade(
        #    label='Database', menu=self.database_popup)

        # For compatibility with Game when testing if item has focus.
        self.takefocus_widget = self.score

    def destroy_widget(self):
        """Destroy the widget displaying game selection rule."""
        self.panel.destroy()

    def get_top_widget(self):
        """Return topmost widget for game selection rule display.

        The topmost widget is put in a container widget in some way
        """
        return self.panel

    def _on_configure(self, event=None):
        """Reconfigure widget after container has been resized."""
        del event
        self._configure_selection_widget()

    def _configure_selection_widget(self):
        """Configure widgets for a game selection rule display."""
        self.panel.grid_rowconfigure(0, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_columnconfigure(1, weight=0)

    def hide_scrollbars(self):
        """Hide the scrollbars in the game selection rule display widgets."""
        self.scrollbar.grid_remove()
        self.score.grid_configure(columnspan=2)
        self._configure_selection_widget()

    def show_scrollbars(self):
        """Show the scrollbars in the game selection rule display widgets."""
        self.score.grid_configure(columnspan=1)
        self.scrollbar.grid_configure()
        self._configure_selection_widget()

    def takefocus(self, take=True):
        """Configure game widget takefocus option."""
        # Hack because I misunderstood meaning of takefocus: FALSE does not
        # stop the widget taking focus, just stops tab traversal.
        if take:
            # self.takefocus_widget.configure(takefocus=tkinter.TRUE)
            self.takefocus_widget.configure(takefocus=tkinter.FALSE)
        else:
            self.takefocus_widget.configure(takefocus=tkinter.FALSE)

    def set_score_pointer_widget_navigation_bindings(self, switch):
        """Set or unset pointer bindings for widget navigation."""
        self.set_event_bindings_score(
            (
                (EventSpec.control_buttonpress_1, ""),
                (EventSpec.buttonpress_1, self.give_focus_to_widget),
                (EventSpec.buttonpress_3, self.post_inactive_menu),
            ),
            switch=switch,
        )

    def set_colours(self, sbg, bbg, bfg):
        """Set colours and fonts used to display game selection rule.

        sbg == True - set game score colours
        bbg == True - set board square colours
        bfg == True - set board piece colours

        """

    def _create_primary_activity_popup(self):
        """Delegate then add close command to popup and return popup menu."""
        popup = super()._create_primary_activity_popup()
        self._create_widget_navigation_submenu_for_popup(popup)
        return popup
