# engine.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a chess engine definition.

A chess engine definition is the command to run a chess engine.

The Engine class displays a chess engine definition.

An instance of these classes fits into the user interface as the only item in a
new toplevel widget.

The engineedit module provides a subclass which allows editing the chess
engine definition.

The enginedbshow and enginedbedit modules provide subclasses used in a
new toplevel widget to display or edit chess engine definitions.

The enginedbdelete module provides a subclass used in a new toplevel widget
to allow deletion of chess engine definitions from a database.

"""

import tkinter

from .enginetext import EngineText


class Engine(EngineText):

    """Chess engine definition widget.

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
        """Create widgets to display chess engine definition."""

        panel = tkinter.Frame(master, borderwidth=2, relief=tkinter.RIDGE)
        panel.bind("<Configure>", self.try_event(self.on_configure))
        panel.grid_propagate(False)
        super(Engine, self).__init__(
            panel, ui=ui, items_manager=items_manager, itemgrid=itemgrid, **ka
        )
        self.scrollbar.grid(column=1, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.score.grid(column=0, row=0, rowspan=1, sticky=tkinter.NSEW)
        if not ui.visible_scrollbars:
            panel.after_idle(self.hide_scrollbars)
        self.configure_selection_widget()

        # For compatibility with Game when testing if item has focus.
        self.takefocus_widget = self.score

    def destroy_widget(self):
        """Destroy the widget displaying chess engine definition."""
        self.panel.destroy()

    def get_top_widget(self):
        """Return topmost widget for chess engine definition display.

        The topmost widget is put in a container widget in some way
        """
        return self.panel

    def on_configure(self, event=None):
        """Reconfigure widget after container has been resized."""
        self.configure_selection_widget()

    def configure_selection_widget(self):
        """Configure widgets for a chess engine definition display."""
        self.panel.grid_rowconfigure(0, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_columnconfigure(1, weight=0)

    def hide_scrollbars(self):
        """Hide the scrollbars in chess engine definition display widgets."""
        self.scrollbar.grid_remove()
        self.score.grid_configure(columnspan=2)
        self.configure_selection_widget()

    def show_scrollbars(self):
        """Show the scrollbars in chess engine definition display widgets."""
        self.score.grid_configure(columnspan=1)
        self.scrollbar.grid_configure()
        self.configure_selection_widget()

    def takefocus(self, take=True):
        """Configure game widget takefocus option."""

        # Hack because I misunderstood meaning of takefocus: FALSE does not
        # stop the widget taking focus, just stops tab traversal.
        if take:
            # self.takefocus_widget.configure(takefocus=tkinter.TRUE)
            self.takefocus_widget.configure(takefocus=tkinter.FALSE)
        else:
            self.takefocus_widget.configure(takefocus=tkinter.FALSE)
