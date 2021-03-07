# cqltext.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a Chess Query Language (ChessQL) statement.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""
# The previous CQL syntax partially supported was version 5.1 found at:
# https://web.archive.org/web/20140130143815/http://www.rbnn.com/cql/
# (www.rbnn.com is no longer availabable).

import tkinter
import tkinter.messagebox
import enum

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from ..core.cqlstatement import CQLStatement
from .eventspec import EventSpec
from .displayitems import DisplayItemsStub


# 'Tag' in these names refers to tags in Tk Text widgets, not PGN tags.
# CQLText uses NO_EDITABLE_TAGS and INITIAL_BINDINGS.
# CQLEdit uses all the names.
# See Score.NonTagBind for the apparently missing values.
class NonTagBind(enum.Enum):
    NO_EDITABLE_TAGS = 1
    DEFAULT_BINDINGS = 3
    INITIAL_BINDINGS = 4
    

class CQLText(ExceptionHandler):

    """ChessQL statement widget.

    panel is used as the master argument for the tkinter Text and Scrollbar
    widgets created to display the statement text.

    ui is the user interface manager for an instance of CQLText, usually an
    instance of ChessUI.

    items_manager is the ui attribute which tracks which CQLText instance is
    active (as defined by ui).

    itemgrid is the ui reference to the DataGrid from which the record was
    selected.

    Subclasses are responsible for providing a geometry manager.

    Attribute _is_cql_query_editable is False meaning the statement cannot be
    edited.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    """

    # True means ChessQL statement can be edited.
    _is_cql_query_editable = False

    # Indicate the most recent set of bindings applied to score attribute.
    # Values are Tk tag names or members of NonTagBind enumeration. 
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def __init__(
        self,
        panel,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka):
        """Create widgets to display ChessQL statement."""
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
        self.set_keypress_binding(switch=False)
        self.set_event_bindings_score(self.get_menubar_events())

        # The popup menus for the ChessQL statement.
        # active_popup and score.Score.move_popup are equivalent.
        # There is no equivalent to score.Score.select_move_popup because
        # query text is plain text.
        self.active_popup = None
        self.inactive_popup = None

        # Selection rule parser instance to process text.
        self.cql_statement = CQLStatement()
        # Not sure this is needed or wanted.
        #self.cql_statement.dbset = ui.base_games.datasource.dbset

    # set_popup_bindings and add_cascade_menu_to_popup copied from score.Score.

    def set_popup_bindings(self, popup, bindings=(), index=tkinter.END):
        """Insert bindings in popup before index in popup.

        Default index is tkinter.END which seems to mean insert at end of
        popup, not before last entry in popup as might be expected from the
        way expressed in the 'Tk menu manual page' for index command.  (The
        manual page describes 'end' in the context of 'none' for 'activate'
        option.  It does make sense 'end' meaning after existing entries
        when inserting entries.)

        """
        for accelerator, function in bindings:
            popup.insert_command(
                index=index,
                label=accelerator[1],
                command=self.try_command(function, popup),
                accelerator=accelerator[2])

    def add_cascade_menu_to_popup(
        self, label, popup, bindings=None, order=None, index=tkinter.END):
        '''Add cascade_menu, and bindings, to popup if not already present.

        The index is used as the label on the popup menu when visible.

        The bindings are not applied if cascade_menu is alreay in popup menu.

        '''
        # Cannot see a way of asking 'Does entry exist?' other than:
        try:
            popup.index(label)
        except:
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
                        accelerator=definition[2])
        
    def set_event_bindings_score(self, bindings=(), switch=True):
        """Set bindings if switch is True or unset the bindings."""
        ste = self.try_event
        for sequence, function in bindings:
            self.score.bind(
                sequence[0],
                ste(function) if switch and function else '')

    def set_keypress_binding(self, function=None, bindings=(), switch=True):
        """Set bindings to function if switch is True or disable keypress."""
        if switch and function:
            stef = self.try_event(function)
            for sequence in bindings:
                self.score.bind(sequence[0], stef)
        else:
            stekb = self.try_event(self.press_break)
            for sequence in bindings:
                self.score.bind(sequence[0], stekb)

    def press_break(self, event=None):
        """Do nothing and prevent event handling by next handlers."""
        return 'break'

    def press_none(self, event=None):
        """Do nothing and allow event to be handled by next handler."""
        return None
        
    # bind_for_active and score.Score.bind_for_move are equivalent.
    def bind_for_active(self, switch=True):
        """Set keyboard bindings and popup menu for non-editing actions.

        Method exists for compatibility with score.Score way of doing things.

        The Text widget contains two tokens, the CQL statement name and the
        staement.  Both tokens are editable, or both are not, and
        the standard Text widget operations are available when editable.

        """
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.NO_EDITABLE_TAGS
        self.set_active_bindings(switch=switch)
        
    def bind_for_initial_state(self, switch=True):
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.INITIAL_BINDINGS
        
    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = {
        NonTagBind.NO_EDITABLE_TAGS: bind_for_active,
        NonTagBind.INITIAL_BINDINGS: bind_for_initial_state,
        }

    def set_active_bindings(self, switch=True):
        """Switch bindings for traversing query statement on or off."""
        self.set_event_bindings_score(
            self.get_F10_popup_events(self.post_active_menu_at_top_left,
                                      self.post_active_menu),
            switch=switch)
        self.set_event_bindings_score(
            self.get_button_events(buttonpress3=self.post_active_menu),
            switch=switch)

    # score.Score.set_select_variation_bindings in has no equivalent.

    # Renamed from bind_score_pointer_for_board_navigation to fit current use.
    def set_score_pointer_item_navigation_bindings(self, switch):
        """Set or unset pointer bindings for game navigation."""
        self.set_event_bindings_score(
            self.get_button_events(buttonpress3=self.post_active_menu),
            switch=switch)

    # set_board_pointer_select_variation_bindings and
    # set_board_pointer_move_bindings in score.Score have no equivalents.

    # score.Score.get_keypress_suppression_events has no equivalent.
        
    def get_modifier_buttonpress_suppression_events(self):
        """Return tuple of event binding definitions suppressing buttonpress
        with Control, Shift, or Alt."""
        return (
            (EventSpec.control_buttonpress_1, self.press_break),
            (EventSpec.control_buttonpress_3, self.press_break),
            (EventSpec.shift_buttonpress_1, self.press_break),
            (EventSpec.shift_buttonpress_3, self.press_break),
            (EventSpec.alt_buttonpress_1, self.press_break),
            (EventSpec.alt_buttonpress_3, self.press_break),
            )

    # The default Text widget bindings are probably what is wanted.
    def get_modifier_buttonpress_suppression_events(self):
        """Return tuple of event binding definitions suppressing buttonpress
        with Control, Shift, or Alt."""
        return ()

    def get_menubar_events(self):
        """Return tuple of event binding definitions passed for menubar."""
        return (
            (EventSpec.score_enable_F10_menubar, self.press_none),
            )

    # Perhaps replace get_select_move_button_events and get_move_button_events
    # in score.Score where there are several notes about this.
    def get_button_events(self, buttonpress1=None, buttonpress3=None):
        """Return tuple of buttonpress event bindings.

        buttonpress1 and buttonpress3 default to self.press_none().

        """
        if buttonpress1 is None:
            buttonpress1 = self.press_none
        if buttonpress3 is None:
            buttonpress3 = self.press_none
        return self.get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_1, buttonpress1),
            (EventSpec.buttonpress_3, buttonpress3),
            )

    def get_F10_popup_events(self, top_left, pointer):
        """Return tuple of event definitions to post popup menus at top left
        of focus widget and at pointer location within application widget.

        top_left and pointer are functions.

        """
        return (
            (EventSpec.score_enable_F10_popupmenu_at_top_left, top_left),
            (EventSpec.score_enable_F10_popupmenu_at_pointer, pointer),
            )

    # score.Score.get_move_button_events is replaced by get_button_events.
    # score.Score.get_select_move_button_events has no equivalent.
        
    # Subclasses with database interfaces may override method.
    def create_database_submenu(self, menu):
        return None
        
    # Subclasses which need widget navigation in their popup menus should
    # call this method.
    def create_widget_navigation_submenu_for_popup(self, popup):
        """Create and populate a submenu of popup for widget navigation.

        The commands in the submenu should switch focus to another widget.

        Subclasses should define a generate_popup_navigation_maps method and
        binding_labels iterable suitable for allowed navigation.
        
        """
        navigation_map, local_map = self.generate_popup_navigation_maps()
        local_map.update(navigation_map)
        self.add_cascade_menu_to_popup(
            'Navigation', popup,
            bindings=local_map, order=self.binding_labels)
        
    # Subclasses which need dismiss widget in a menu should call this method.
    def add_close_item_entry_to_popup(self, popup):
        """Add option to dismiss widget entry to popup.

        Subclasses must provide a delete_item_view method.

        """
        self.set_popup_bindings(popup, self.get_close_item_events())
        
    def create_active_popup(self):
        assert self.active_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_active_events())
        database_submenu = self.create_database_submenu(popup)
        if database_submenu:
            popup.add_cascade(label='Database', menu=database_submenu)
        self.active_popup = popup
        return popup
        
    def create_inactive_popup(self):
        assert self.inactive_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self.set_popup_bindings(popup, self.get_inactive_events())
        self.inactive_popup = popup
        return popup

    def get_inactive_button_events(self):
        return self.get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_1, self.give_focus_to_widget),
            (EventSpec.buttonpress_3, self.post_inactive_menu),
            )
        
    def post_menu(self,
                  menu, create_menu,
                  allowed=True,
                  event=None):
        if menu is None:
            menu = create_menu()
        if not allowed:
            return 'break'
        menu.tk_popup(*self.score.winfo_pointerxy())

        # So 'Control-F10' does not fire 'F10' (menubar) binding too.
        return 'break'
        
    def post_menu_at_top_left(self,
                              menu,
                              create_menu,
                              allowed=True,
                              event=None):
        if menu is None:
            menu = create_menu()
        if not allowed:
            return 'break'
        menu.tk_popup(event.x_root-event.x, event.y_root-event.y)

        # So 'Shift-F10' does not fire 'F10' (menubar) binding too.
        return 'break'
        
    def post_active_menu(self, event=None):
        """Show the popup menu for ChessQL statement navigation."""
        return self.post_menu(
            self.active_popup,
            self.create_active_popup,
            allowed=self.is_active_item_mapped(),
            event=event)
        
    def post_active_menu_at_top_left(self, event=None):
        """Show the popup menu for ChessQL statement navigation."""
        return self.post_menu_at_top_left(
            self.active_popup,
            self.create_active_popup,
            allowed=self.is_active_item_mapped(),
            event=event)
        
    def post_inactive_menu(self, event=None):
        """Show the popup menu for a ChessQL statement in an inactive item."""
        return self.post_menu(
            self.inactive_popup, self.create_inactive_popup, event=event)
        
    def post_inactive_menu_at_top_left(self, event=None):
        """Show the popup menu for a ChessQL statement in an inactive item."""
        return self.post_menu_at_top_left(
            self.inactive_popup, self.create_inactive_popup, event=event)

    def get_active_events(self):
        return ()

    def get_inactive_events(self):
        return (
            (EventSpec.display_make_active, self.set_focus_panel_item_command),
            (EventSpec.display_dismiss_inactive, self.delete_item_view),
            )

    def give_focus_to_widget(self, event=None):
        """Do nothing and return 'break'.  Override in subclasses as needed."""
        return 'break'
        
    def set_and_tag_item_text(self, reset_undo=False):
        """Display the ChessQL statement as text.
        
        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a ChessQL statement for editing so that repeated
        Ctrl-Z in text editing mode recovers the original ChessQL statement.
        
        """
        if not self._is_cql_query_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete('1.0', tkinter.END)
        self.map_cql_statement()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_active()
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
        
    def is_active_item_mapped(self):
        """"""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return False
        return True
        
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
                tkinter.messagebox.showinfo(
                    parent = self.ui.get_toplevel(),
                    title='ChessQL Statement',
                    message=msg)
            except Exception as exc:
                msg = ''.join(
                    ("Unable to list games for ChessQL statement:\n\n",
                     "The reported error is:\n\n",
                     str(exc),
                     ))
                grid.datasource.get_cql_statement_games(None, None)
                tkinter.messagebox.showinfo(
                    parent = self.ui.get_toplevel(),
                    title='ChessQL Statement',
                    message=msg)
        grid.partial = self.get_partial_key_cql_statement()
        #grid.rows = 1
        grid.load_new_index()

        # Get rid of the 'Please wait ...' status text.
        self.ui.statusbar.set_status_text()

        if cqls.cql_error:
            if self.ui.database is None:
                tkinter.messagebox.showinfo(
                    parent = self.ui.get_toplevel(),
                    title='ChessQL Statement Error',
                    message=cqls.cql_error.get_error_report())
            else:
                tkinter.messagebox.showinfo(
                    parent = self.ui.get_toplevel(),
                    title='ChessQL Statement Error',
                    message=cqls.cql_error.add_error_report_to_message(
                        ('An empty game list will be displayed.')))
        elif grid.datasource.not_implemented:
            tkinter.messagebox.showinfo(
                parent = self.ui.get_toplevel(),
                title='ChessQL Statement Not Implemented',
                message=''.join(('These filters are not implemented and ',
                                 'are ignored:\n\n',
                                 '\n'.join(sorted(
                                     grid.datasource.not_implemented)))))
