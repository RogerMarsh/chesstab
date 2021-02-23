# cql.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display a Chess Query Language (ChessQL) statement.

ChessQL statements define patterns of chess pieces used to select games which
match the conditions stated in the statement.

The ChessQL syntax is defined in:
https://web.archive.org/web/20140130143815/http://www.rbnn.com/cql/
(www.rbnn.com is no longer availabable).

The CQL class displays a ChessQL statement.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

The cqledit module provides a subclass which allows editing in the main
application window.

The cqldbshow and cqldbedit modules provide subclasses used in a
new toplevel widget to display or edit ChessQL statements.

The cqldbdelete module provides a subclass used in a new toplevel widget
to allow deletion of ChessQL statements from a database.

"""

import tkinter

from .cqlscore import CQLScore
    

class CQL(CQLScore):

    """ChessQL statement widget.
    """

    def __init__(
        self,
        master=None,
        boardfont=None,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Create widgets to display ChessQL statement.

        Create Frame in toplevel and add Canvas and Text.
        Text width and height set to zero so widget fit itself into whatever
        space Frame has available.
        Canvas must be square leaving Text at least half the Frame.

        """

        panel = tkinter.Frame(
            master,
            borderwidth=2,
            relief=tkinter.RIDGE)
        panel.bind('<Configure>', self.try_event(self.on_configure))
        panel.grid_propagate(False)
        super().__init__(
            panel,
            ui=ui,
            items_manager=items_manager,
            itemgrid=itemgrid,
            **ka)
        self.scrollbar.grid(column=1, row=0, rowspan=1, sticky=tkinter.NSEW)
        self.score.grid(column=0, row=0, rowspan=1, sticky=tkinter.NSEW)
        if not ui.visible_scrollbars:
            panel.after_idle(self.hide_scrollbars)
        self.configure_cql_statement_widget()

        # The popup menus specific to CQL (placed same as Game equivalent)

        self.viewmode_popup.add_cascade(
            label='Database', menu=self.viewmode_database_popup)

        # For compatibility with Game when testing if item has focus.
        self.takefocus_widget = self.score
        
    def destroy_widget(self):
        """Destroy the widget displaying ChessQL statement."""
        self.panel.destroy()

    def get_top_widget(self):
        """Return topmost widget for ChessQL statement display.

        The topmost widget is put in a container widget in some way
        """
        return self.panel

    def on_configure(self, event=None):
        """Reconfigure widget after container has been resized."""
        self.configure_cql_statement_widget()
        
    def configure_cql_statement_widget(self):
        """Configure widgets for a ChessQL statement display."""
        self.panel.grid_rowconfigure(0, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_columnconfigure(1, weight=0)

    def hide_scrollbars(self):
        """Hide the scrollbars in the ChessQL statement display widgets."""
        self.scrollbar.grid_remove()
        self.score.grid_configure(columnspan=2)
        self.configure_cql_statement_widget()

    def show_scrollbars(self):
        """Show the scrollbars in the ChessQL statement display widgets."""
        self.score.grid_configure(columnspan=1)
        self.scrollbar.grid_configure()
        self.configure_cql_statement_widget()

    def takefocus(self, take=True):
        """Configure game widget takefocus option."""

        # Hack because I misunderstood meaning of takefocus: FALSE does not
        # stop the widget taking focus, just stops tab traversal.
        if take:
            #self.takefocus_widget.configure(takefocus=tkinter.TRUE)
            self.takefocus_widget.configure(takefocus=tkinter.FALSE)
        else:
            self.takefocus_widget.configure(takefocus=tkinter.FALSE)

    def bind_score_pointer_for_widget_navigation(self, switch):
        """Set or unset pointer bindings for widget navigation."""
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', self.try_event(self.give_focus_to_widget)),
            ('<ButtonPress-3>', self.try_event(self.popup_inactive_menu)),
            ):
            self.score.bind(sequence, '' if not switch else function)

    def set_colours(self, sbg, bbg, bfg):
        """Set colours and fonts used to display ChessQL statement.

        sbg == True - set game score colours
        bbg == True - set board square colours
        bfg == True - set board piece colours

        """

    def export_partial(self, event=None):
        """Export displayed partial position definition."""
        exporters.export_single_position(
            self.score.get('1.0', tkinter.END),
            self.ui.get_export_filename_for_single_item(
                'Partial Position', pgn=False))
