# querytext.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display a game selection rule.
"""

import tkinter

from solentware_misc.workarounds import dialogues

from .chessexception import ChessException
from .constants import (
    START_SELECTION_RULE_MARK,
    )
from ..core.querystatement import QueryStatement
from .eventspec import EventSpec
from .displayitems import DisplayItemsStub
from .gamerow import make_ChessDBrowGame
from ..core.chessrecord import ChessDBrecordGameTags
    

class QueryText(ChessException):

    """Game selection rule widget built from Text and Scrollbar widgets.
    """

    # True means selection rule can be edited
    _is_query_editable = False

    def __init__(
        self,
        panel,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Create widgets to display game selection rule.

        """
        super(QueryText, self).__init__(**ka)
        self.ui = ui

        # May be worth using a Null() instance for these two attributes.
        if items_manager is None:
            items_manager = DisplayItemsStub()
        self.items = items_manager
        self.itemgrid = itemgrid

        self.panel = panel
        self.score = tkinter.Text(
            master=self.panel,
            width=0,
            height=0,
            takefocus=tkinter.FALSE,
            undo=True,
            wrap=tkinter.WORD)
        self.scrollbar = tkinter.Scrollbar(
            master=self.panel,
            orient=tkinter.VERTICAL,
            takefocus=tkinter.FALSE,
            command=self.score.yview)
        self.score.configure(yscrollcommand=self.scrollbar.set)

        # Keyboard actions do nothing by default.
        self.disable_keyboard()

        # The popup menus for the selection rule

        self.viewmode_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.viewmode_database_popup = tkinter.Menu(
            master=self.viewmode_popup, tearoff=False)
        self.inactive_popup = None
        self.viewmode_navigation_popup = None

        # Selection rule parser instance to process text.
        self.query_statement = QueryStatement()
        if ui.base_games.datasource:
            self.query_statement.dbset = ui.base_games.datasource.dbset

    def add_navigation_to_viewmode_popup(self, **kwargs):
        '''Add 'Navigation' entry to popup if not already present.'''

        # Cannot see a way of asking 'Does entry exist?' other than:
        try:
            self.viewmode_popup.index('Navigation')
        except:
            self.viewmode_navigation_popup = tkinter.Menu(
                master=self.viewmode_popup, tearoff=False)
            self.viewmode_popup.add_cascade(
                label='Navigation', menu=self.viewmode_navigation_popup)
            self.bind_navigation_for_viewmode_popup(**kwargs)
        
    def bind_for_viewmode(self):
        """Set keyboard bindings for game selection rule display."""

    def bind_navigation_for_viewmode_popup(self, bindings=None, order=None):
        """Set popup bindings for toplevel navigation."""
        if order is None:
            order = ()
        if bindings is None:
            bindings = {}
        for label, accelerator in order:
            function = bindings.get(label)
            if function is not None:
                self.viewmode_navigation_popup.add_command(
                    label=label,
                    command=self.try_command(
                        function, self.viewmode_navigation_popup),
                    accelerator=accelerator)

    def bind_score_pointer_for_board_navigation(self, switch):
        """Set or unset pointer bindings for game selection rule navigation."""
        ste = self.try_event
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', ''),
            ('<ButtonPress-3>', ste(self.popup_viewmode_menu)),
            ):
            self.score.bind(sequence, '' if not switch else function)

    def give_focus_to_widget(self, event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return 'break'
        
    def set_query_statement(self, reset_undo=False):
        """Display the game selection rule as text.
        
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a selection rule for editing so that repeated
        Ctrl-Z in text editing mode recovers the original selection rule.
        
        """
        if not self._is_query_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_query_statement()
        if not self._is_query_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()
        
    def set_statusbar_text(self):
        """Set status bar to display game selection rule name."""
        self.ui.statusbar.set_status_text(self.query_statement.get_name_text())

    def get_name_query_statement_text(self):
        """"""
        text = self.score.get('1.0', tkinter.END).strip()
        return text

    def map_query_statement(self):
        """"""
        # No mapping of tokens to text in widget (yet).
        self.score.insert(tkinter.INSERT,
                          self.query_statement.get_name_query_statement_text())
        
    def popup_inactive_menu(self, event=None):
        """Show the popup menu for a game selection rule in an inactive item.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        self.inactive_popup.tk_popup(*self.score.winfo_pointerxy())
        
    def popup_viewmode_menu(self, event=None):
        """Show the popup menu for game selection rule actions.

        Subclasses define particular entries for this menu.  This class adds
        no items to the menu.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return 'break'
        self.viewmode_popup.tk_popup(*self.score.winfo_pointerxy())

    def refresh_game_list(self):
        """Display games matching game selection rule, empty on errors."""
        grid = self.itemgrid
        if grid is None:
            return
        if grid.get_database() is None:
            return
        self.ui.base_games.set_data_source(
            self.ui.selectionds(
                grid.datasource.dbhome,
                self.ui.base_games.datasource.dbset,
                self.ui.base_games.datasource.dbset,
                make_ChessDBrowGame(self.ui)),
            self.ui.base_games.on_data_change)
        qs = self.query_statement
        if qs.where_error:
            self.ui.base_games.datasource.get_selection_rule_games(None)
            self.ui.base_games.load_new_index()
            dialogues.showerror(
                'Display Game Selection Rule',
                qs.where_error.get_error_report(grid.datasource),
                )
        elif qs.where:
            qs.where.evaluate(
                grid.datasource.dbhome.record_finder(
                    grid.datasource.dbset,
                    ChessDBrecordGameTags))

            # Workaround problem with query ''.  See Where.evaluate() also.
            r = qs.where.node.get_root().result
            if r is None:
                self.ui.base_games.datasource.get_selection_rule_games(None)
            else:
                self.ui.base_games.datasource.get_selection_rule_games(
                    r.answer)
            self.ui.base_games.load_new_index()

        elif qs.get_query_statement_text():
            self.ui.base_games.load_new_index()
        #else:
        #    dialogues.showinfo(
        #        'Display Game Selection Rule',
        #        ''.join(('Game list not changed because active query ',
        #                 'has not yet been evaluated.',
        #                 )))

        # Get rid of the 'Please wait ...' status text.
        self.ui.statusbar.set_status_text()

    def disable_keyboard(self):
        """"""
        self.score.bind(EventSpec.selectiontext_disable_keypress[0],
                        lambda e: 'break')
