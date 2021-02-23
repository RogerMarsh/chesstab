# cqlscore.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display a Chess Query Language (ChessQL) statement.

"""

import tkinter

from solentware_misc.workarounds import dialogues

from .chessexception import ChessException
from ..core.cqlstatement import CQLStatement
from .eventspec import EventSpec
from .displayitems import DisplayItemsStub
    

class CQLScore(ChessException):

    """ChessQL statement widget built from Text and Scrollbar widgets.
    """

    # True means ChessQL statement can be edited.
    _is_cql_query_editable = False

    def __init__(
        self,
        panel,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Create widgets to display ChessQL statement.

        """
        super().__init__(**ka)
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

        # The popup menus for the ChessQL statement.

        self.viewmode_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.viewmode_database_popup = tkinter.Menu(
            master=self.viewmode_popup, tearoff=False)
        self.inactive_popup = None
        self.viewmode_navigation_popup = None

        # Selection rule parser instance to process text.
        self.cql_statement = CQLStatement()
        # Not sure this is needed or wanted.
        #self.cql_statement.dbset = ui.base_games.datasource.dbset

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
        """Set keyboard bindings for ChessQL statement display."""

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
        """Set or unset pointer bindings for ChessQL statement navigation."""
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
        
    def set_cql_statement(self, reset_undo=False):
        """Display the ChessQL statement as text.
        
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a ChessQL statement for editing so that repeated
        Ctrl-Z in text editing mode recovers the original ChessQL statement.
        
        """
        if not self._is_cql_query_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_cql_statement()
        if not self._is_cql_query_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()
        
    def set_statusbar_text(self):
        """Set status bar to display ChessQL statement name."""
        self.ui.statusbar.set_status_text(self.cql_statement.get_name_text())

    def get_name_cql_statement_text(self):
        """"""
        text = self.score.get('1.0', tkinter.END).strip()
        return text

    def map_cql_statement(self):
        """"""
        # No mapping of tokens to text in widget (yet).
        self.score.insert(tkinter.INSERT,
                          self.cql_statement.get_name_statement_text())
        
    def popup_inactive_menu(self, event=None):
        """Show the popup menu for a ChessQL statement in an inactive item.

        Subclasses may have particular entries to be the default which is
        implemented by overriding this method.

        """
        self.inactive_popup.tk_popup(*self.score.winfo_pointerxy())
        
    def popup_viewmode_menu(self, event=None):
        """Show the popup menu for ChessQL statement actions.

        Subclasses define particular entries for this menu.  This class adds
        no items to the menu.

        """
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return 'break'
        self.viewmode_popup.tk_popup(*self.score.winfo_pointerxy())
        
    def get_partial_key_cql_statement(self):
        """Return ChessQL statement for use as partial key."""
        if self.cql_statement.is_statement():

            # Things must be arranged so a tuple, not a list, can be returned.
            #return tuple(self.cql_statement.position)
            return self.cql_statement.get_statement_text() # Maybe!
        
        else:
            return False

    def refresh_game_list(self):
        """Display games with position matching selected ChessQL statement."""
        grid = self.itemgrid
        if grid is None:
            return
        if grid.get_database() is None:
            return
        cqls = self.cql_statement
        if cqls.cql_error:
            grid.datasource.get_cql_statement_games(None, None)
        else:
            try:
                if self._is_cql_query_editable:
                    grid.datasource.get_cql_statement_games(cqls, None)
                else:
                    grid.datasource.get_cql_statement_games(
                        cqls, self.recalculate_after_edit)
            except AttributeError as exc:
                if str(exc) == "'NoneType' object has no attribute 'answer'":
                    msg = ''.join(
                        ("Unable to list games for ChessQL statement, ",
                         "probably because an 'empty square' is in the query ",
                         "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                         str(exc),
                         ))
                else:
                    msg = ''.join(
                        ("Unable to list games for ChessQL statement:\n\n",
                         "The reported error is:\n\n",
                         str(exc),
                         ))
                grid.datasource.get_cql_statement_games(None, None)
                dialogues.showinfo(
                    title='ChessQL Statement',
                    message=msg)
            except Exception as exc:
                msg = ''.join(
                    ("Unable to list games for ChessQL statement:\n\n",
                     "The reported error is:\n\n",
                     str(exc),
                     ))
                grid.datasource.get_cql_statement_games(None, None)
                dialogues.showinfo(
                    title='ChessQL Statement',
                    message=msg)
        grid.partial = self.get_partial_key_cql_statement()
        #grid.rows = 1
        grid.load_new_index()

        # Get rid of the 'Please wait ...' status text.
        self.ui.statusbar.set_status_text()

        if cqls.cql_error:
            if self.ui.database is None:
                dialogues.showinfo(
                    title='ChessQL Statement Error',
                    message=cqls.cql_error.get_error_report())
            else:
                dialogues.showinfo(
                    title='ChessQL Statement Error',
                    message=cqls.cql_error.add_error_report_to_message(
                        ('An empty game list will be displayed.')))
        elif grid.datasource.not_implemented:
            dialogues.showinfo(
                title='ChessQL Statement Not Implemented',
                message=''.join(('These filters are not implemented and ',
                                 'are ignored:\n\n',
                                 '\n'.join(sorted(
                                     grid.datasource.not_implemented)))))

    def disable_keyboard(self):
        """"""
        self.score.bind(EventSpec.partialscore_disable_keypress[0],
                        lambda e: 'break')
