# querydisplay.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit game selection rules.

These four classes display game selection rules in the main window: they are
used in the querygrid module.

The QueryDisplay class binds events to navigate between widgets.

The DatabaseQueryDisplay class adds delete record to the QueryDisplay
class.

The DatabaseQueryInsert class adds insert record to the
DatabaseQueryDisplay class but does not bind delete record to any events.

The DatabaseQueryEdit class adds edit record to the DatabaseQueryInsert
class but does not bind delete record to any events.

These three classes display games in their own Toplevel widget: they are used
in the gamedbdelete, gamedbedit, and gamedbshow, modules.

The QueryDialogue class binds events to navigate between widgets.

The DialogueQueryDisplay class adds insert and delete record to the
QueryDialogue class.

The DialogueQueryEdit class adds insert and edit record to the
QueryDialogue class.

"""

import tkinter
import tkinter.messagebox

from solentware_misc.workarounds import dialogues
from solentware_base.core.where import WhereError

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from ..core.querystatement import QueryStatement
from .query import Query
from .queryedit import QueryEdit
from ..core.chessrecord import ChessDBrecordQuery
from .chessexception import ChessException
from .eventspec import EventSpec
from .display import Display
from .. import APPLICATION_NAME


class QueryDisplay(ChessException, Display):
    
    """Manage UI interaction with database for displayed game selection rules.

    QueryDisplay is a subclass of DataNotify so that modifications to
    the database record outside an instance prevent database update using
    the instance.  This class provides methods to update the database from
    the instance; and to switch to other displayed game selection rules.

    Subclasses provide the widget to display the game selection rules.
    
    """

    binding_labels = tuple(
        [b[1:] for b in (
            EventSpec.selectiondisplay_to_position_grid,
            EventSpec.selectiondisplay_to_active_game,
            EventSpec.selectiondisplay_to_game_grid,
            EventSpec.selectiondisplay_to_repertoire_grid,
            EventSpec.selectiondisplay_to_active_repertoire,
            EventSpec.selectiondisplay_to_repertoire_game_grid,
            EventSpec.selectiondisplay_to_partial_grid,
            EventSpec.selectiondisplay_to_selection_rule_grid,
            EventSpec.selectiondisplay_to_previous_selection,
            EventSpec.selectiondisplay_to_next_selection,
            EventSpec.selectiondisplay_to_partial_game_grid,
            EventSpec.tab_traverse_backward,
            EventSpec.tab_traverse_forward,
            )])

    def __init__(self, sourceobject=None, **ka):
        """Extend and link game selection rule to database.

        sourceobject - link to database.

        """
        super(QueryDisplay, self).__init__(**ka)
        self.blockchange = False
        if self.ui.base_selections.datasource:
            self.set_data_source(self.ui.base_selections.get_data_source())
        self.sourceobject = sourceobject
        self.insertonly = sourceobject is None
        self.recalculate_after_edit = sourceobject

    def _bind_for_board_navigation(self):
        """Set bindings to navigate game selection rule on pointer click."""
        self.bind_score_pointer_for_board_navigation(True)

    def bind_for_widget_navigation(self):
        """Set bindings to give focus to this selection rule on pointer click.
        """
        self.bind_score_pointer_for_widget_navigation(True)

    def bind_off(self):
        """Disable all bindings."""
        
        # Replicate structure of __bind_on for deleting bindings.
        for sequence, function in (
            (EventSpec.selectiondisplay_to_partial_grid, ''),
            (EventSpec.selectiondisplay_to_selection_rule_grid, ''),
            (EventSpec.selectiondisplay_to_previous_selection, ''),
            (EventSpec.selectiondisplay_to_next_selection, ''),
            (EventSpec.selectiondisplay_to_selection_game_grid, ''),
            (EventSpec.selectiondisplay_to_repertoire_grid, ''),
            (EventSpec.selectiondisplay_to_active_repertoire, ''),
            (EventSpec.selectiondisplay_to_repertoire_game_grid, ''),
            (EventSpec.selectiondisplay_to_position_grid, ''),
            (EventSpec.selectiondisplay_to_active_game, ''),
            (EventSpec.selectiondisplay_to_game_grid, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        self.__bind_on()
        for sequence, function in (
            (EventSpec.tab_traverse_forward,
             self.traverse_forward),
            (EventSpec.tab_traverse_backward,
             self.traverse_backward),
            (EventSpec.tab_traverse_round,
             self.traverse_round),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_on(self):
        """Enable all bindings."""
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""

        # Same bindings in initialize_bindings() and bind_on() in this class.
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', self.try_event(self.give_focus_to_widget)),
            ('<ButtonPress-3>', self.try_event(self.popup_inactive_menu)),
            ):
            self.score.bind(sequence, function)
        for sequence, function in (
            (EventSpec.selectiondisplay_to_partial_grid,
             self.set_focus_partial_grid),
            (EventSpec.selectiondisplay_to_selection_rule_grid,
             self.set_focus_selection_rule_grid),
            (EventSpec.selectiondisplay_to_previous_selection,
             self.prior_item),
            (EventSpec.selectiondisplay_to_next_selection,
             self.next_item),
            (EventSpec.selectiondisplay_to_partial_game_grid,
             self.set_focus_partial_game_grid),
            (EventSpec.selectiondisplay_to_repertoire_grid,
             self.set_focus_repertoire_grid),
            (EventSpec.selectiondisplay_to_active_repertoire,
             self.set_focus_repertoirepanel_item),
            (EventSpec.selectiondisplay_to_repertoire_game_grid,
             self.set_focus_repertoire_game_grid),
            (EventSpec.selectiondisplay_to_position_grid,
             self.set_focus_position_grid),
            (EventSpec.selectiondisplay_to_active_game,
             self.set_focus_gamepanel_item),
            (EventSpec.selectiondisplay_to_game_grid,
             self.set_focus_game_grid),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def _cycle_item(self, prior=False):
        """Select next game selection rule on display."""
        items = self.ui.selection_items
        losefocus = items.active_item
        losefocus.bind_for_widget_navigation()
        items.cycle_active_item(prior=prior)
        self.ui.configure_selection_grid()
        gainfocus = items.active_item
        gainfocus.refresh_game_list()
        gainfocus._bind_for_board_navigation()
        gainfocus.takefocus_widget.focus_set()
        gainfocus.set_statusbar_text()

    def give_focus_to_widget(self, event=None):
        """Select game selection rule on display by mouse click."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        losefocus, gainfocus = self.ui.selection_items.give_focus_to_widget(
            event.widget)
        if losefocus is not gainfocus:
            self.ui.configure_selection_grid()
            self.score.after(
                0,
                func=self.try_command(self.ui._set_selection_name, self.score))
            self.score.after(
                0,
                func=self.try_command(gainfocus.refresh_game_list, self.score))
        return 'break'

    def delete_item_view(self, event=None):
        """Remove game selection rule item from screen."""
        self.ui.delete_selection_rule_view(self)

    def insert_selection_rule_database(self, event=None):
        """Add game selection rule to database."""
        if self.ui.selection_items.active_item is None:
            dialogues.showinfo(
                title='Insert Game Selection Rule',
                message='No active game selection rule to insert into database.')
            return

        # This should see if game selection rule with same name already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            dialogues.showinfo(
                title='Insert Game Selection Rule',
                message='Cannot add game selection rule:\n\nNo database open.')
            return

        datasource = self.ui.base_selections.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Insert Game Selection Rule',
                message='Cannot add game selection rule:\n\nRule list hidden.')
            return
        updater = ChessDBrecordQuery()
        updater.value.set_database(datasource.dbhome)
        updater.value.dbset = self.ui.base_games.datasource.dbset
        uvpqs = updater.value.process_query_statement(
            self.get_name_query_statement_text())
        if not len(updater.value.get_name_text()):
            dialogues.showerror(
                title='Insert Game Selection Rule',
                message=''.join((
                    "The selection rule has no name.\n\nPlease enter it's ",
                    "name as the first line of text.'")))
            return
        if not uvpqs:
            if not updater.value.where_error:
                if tkinter.messagebox.YES != dialogues.askquestion(
                    title='Insert Game Selection Rule',
                    message=''.join((
                        'Confirm request to add game selection rule named:\n\n',
                        updater.value.get_name_text(),
                        '\n\nto database.\n\n',
                        'Note validation of the statement failed but no ',
                        'information is available.',
                        ))):
                    dialogues.showinfo(
                        title='Insert Game Selection Rule',
                        message=''.join(('Add game selection rule to ',
                                         'database abandonned.')))
                    return
            elif tkinter.messagebox.YES != dialogues.askquestion(
                title='Insert Game Selection Rule',
                message=''.join((
                    'Confirm request to add game selection rule named:\n\n',
                    updater.value.get_name_text(),
                    '\n\nto database.\n\n',
                    updater.value.where_error.get_error_report(
                        self.ui.base_games.get_data_source())))):
                dialogues.showinfo(
                    title='Insert Game Selection Rule',
                    message=''.join(('Add game selection rule to ',
                                     'database abandonned.')))
                return
        elif tkinter.messagebox.YES != dialogues.askquestion(
            title='Insert Game Selection Rule',
            message=''.join((
                'Confirm request to add game selection rule named:\n\n',
                updater.value.get_name_text(),
                '\n\nto database.',))):
            dialogues.showinfo(
                title='Insert Game Selection Rule',
                message='Add game selection rule to database abandonned.')
            return
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        updater.key.recno = None#0
        editor.put()
        dialogues.showinfo(
            title='Insert Game Selection Rule',
            message=''.join(('Game selection rule "',
                             updater.value.get_name_text(),
                             '" added to database.')))
        
    def next_item(self, event=None):
        """Select next game selection rule display.

        Call _next_selection_rule after 1 millisecond to allow message display

        """
        if self.ui.selection_items.count_items_in_stack() > 1:
            self.ui._set_find_selection_name_games(0)
            self.score.after(
                1, func=self.try_command(self._next_selection_rule, self.score))

    def _next_selection_rule(self):
        """Generate next game selection rule display.

        Call from next_item only.

        """
        self._cycle_item(prior=False)

    # on_game_change() is not called, but do nothing if it is.
    def on_game_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            pass

    def on_selection_change(self, instance):
        """Prevent update from self if instance refers to same record.

        The list of games is updated by the 'List Games' popup menu option,
        but not as a consequence of updating the database.
        """
        if instance.newrecord:

            # Editing an existing record.
            value = instance.newrecord.value
            key = instance.newrecord.key

        else:

            # Inserting a new record.
            value = instance.value
            key = instance.key

        if self.sourceobject is not None:
            if (key == self.sourceobject.key and
                self.datasource.dbname == self.sourceobject.dbname and
                self.datasource.dbset == self.sourceobject.dbset):
                self.blockchange = True

    def prior_item(self, event=None):
        """Select previous game selection rule display.

        Call _prior_selection_rule after 1 millisecond to allow message display

        """
        if self.ui.selection_items.count_items_in_stack() > 1:
            self.ui._set_find_selection_name_games(-2)
            self.score.after(
                1, func=self.try_command(
                    self._prior_selection_rule, self.score))

    def _prior_selection_rule(self):
        """Generate previous game selection rule display.

        Call from prior_item only.

        """
        self._cycle_item(prior=True)

    def set_insert_or_delete(self):
        """Convert edit display to insert display.

        Selection rules displayed for editing from a database are not closed
        if the database is closed.  They are converted to insert displays and
        can be used to add new records to databases opened later.
        
        """
        self.sourceobject = None

    def get_text_for_statusbar(self):
        """"""
        return ''.join(
            ('Please wait while finding games for game selection rule ',
             self.query_statement.get_name_text(),
             ))

    def get_selection_text_for_statusbar(self):
        """"""
        return self.query_statement.get_name_text()
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for QueryDisplay instance."""
        navigation_map = {
            EventSpec.selectiondisplay_to_position_grid[1]:
            self.set_focus_position_grid,
            EventSpec.selectiondisplay_to_active_game[1]:
            self.set_focus_gamepanel_item_command,
            EventSpec.selectiondisplay_to_game_grid[1]:
            self.set_focus_game_grid,
            EventSpec.selectiondisplay_to_repertoire_grid[1]:
            self.set_focus_repertoire_grid,
            EventSpec.selectiondisplay_to_active_repertoire[1]:
            self.set_focus_repertoirepanel_item_command,
            EventSpec.selectiondisplay_to_partial_grid[1]:
            self.set_focus_partial_grid,
            EventSpec.selectiondisplay_to_active_partial[1]:
            self.set_focus_partialpanel_item_command,
            EventSpec.selectiondisplay_to_repertoire_game_grid[1]:
            self.set_focus_repertoire_game_grid,
            EventSpec.selectiondisplay_to_partial_grid[1]:
            self.set_focus_partial_grid,
            EventSpec.selectiondisplay_to_partial_game_grid[1]:
            self.set_focus_partial_game_grid,
            EventSpec.tab_traverse_backward[1]:
            self.traverse_backward,
            EventSpec.tab_traverse_forward[1]:
            self.traverse_forward,
            }
        for nm, widget in (
            ({EventSpec.selectiondisplay_to_previous_selection[1]:
              self.prior_item,
              EventSpec.selectiondisplay_to_next_selection[1]: self.next_item,
              },
             self),
            ):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.ui.give_focus_backward(self.ui.selection_items)
        return 'break'

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.ui.give_focus_forward(self.ui.selection_items)
        return 'break'

    def traverse_round(self, event=None):
        """Give focus to next widget within active item in traversal order."""
        return 'break'

    def process_and_set_selection_rule_list(self, event=None):
        """Display games matching edited game selection rule."""
        if self.ui.base_games.datasource:
            self.query_statement.set_database(
                self.ui.base_games.datasource.dbhome)
        try:
            self.query_statement.process_query_statement(
                self.score.get('1.0', tkinter.END))
        except WhereError as exc:
            dialogues.showinfo(
                title=' '.join(('Game Selection Rule Error')),
                message=str(exc))
            return 'break'
        finally:
            self.query_statement.set_database()
        self.refresh_game_list()
        return 'break'


class DatabaseQueryDisplay(QueryDisplay, Query, DataNotify):
    
    """Display game selection rule from database and allow delete and insert.

    Query provides the widget and QueryDisplay the database interface.
    
    """

    def __init__(self, **ka):
        """Create display widget and display game selection rule from database.

        See superclasses for argument descriptions.

        """
        super(DatabaseQueryDisplay, self).__init__(**ka)
        self.initialize_bindings()

        # Copied from QueryEdit class in queryedit module on assumption the
        # code should be here too.
        # It is needed if a query is displayed by F11, then the database is
        # closed and it, or anothr one, is opened.
        self.selection_token_checker = QueryStatement()
        if self.ui.base_games.datasource:
            self.selection_token_checker.dbset = self.ui.base_games.datasource.dbset

    def bind_off(self):
        """Disable all bindings."""
        super(DatabaseQueryDisplay, self).bind_off()
        for sequence, function in (
            (EventSpec.databaseselectiondisplay_show_game_list, ''),
            (EventSpec.databaseselectiondisplay_insert, ''),
            (EventSpec.databaseselectiondisplay_delete, ''),
            (EventSpec.databaseselectiondisplay_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super(DatabaseQueryDisplay, self).initialize_bindings()

        # Here because superclass order is QueryDisplay, Query.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)

        for function, accelerator in (
            (self.set_focus_panel_item_command,
             EventSpec.databaseselectiondisplay_make_active),
            (self.delete_item_view,
             EventSpec.databaseselectiondisplay_dismiss_inactive),
            ):
            self.inactive_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.inactive_popup),
                accelerator=accelerator[2])
        self.__bind_on()
        for function, accelerator in (
            (self.process_and_set_selection_rule_list,
             EventSpec.databaseselectiondisplay_show_game_list),
            (self.delete_item_view,
             EventSpec.databaseselectiondisplay_dismiss),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        for function, accelerator in (
            (self.insert_selection_rule_database,
             EventSpec.databaseselectiondisplay_insert),
            (self.delete_selection_rule_database,
             EventSpec.databaseselectiondisplay_delete),
            ):
            self.viewmode_database_popup.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.viewmode_database_popup),
                accelerator=accelerator[2])
        self.bind_toplevel_navigation()

    def bind_on(self):
        """Enable all bindings."""
        super(DatabaseQueryDisplay, self).bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()"""
        for sequence, function in (
            (EventSpec.databaseselectiondisplay_show_game_list,
             self.process_and_set_selection_rule_list),
            (EventSpec.databaseselectiondisplay_insert,
             self.insert_selection_rule_database),
            (EventSpec.databaseselectiondisplay_delete,
             self.delete_selection_rule_database),
            (EventSpec.databaseselectiondisplay_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def delete_selection_rule_database(self, event=None):
        """Remove game selection rule from database."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Delete Game Selection Rule',
                message=''.join(('Cannot delete game selection rule:\n\n',
                                 'No database open.')))
            return
        datasource = self.ui.base_selections.get_data_source()
        if datasource is None:
            dialogues.showerror(
                title='Delete Game Selection Rule',
                message=''.join(('Cannot delete game selection rule:\n\n',
                                 'Rule list hidden.')))
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Delete Game Selection Rule',
                message=''.join(('The game selection rule to delete has not ',
                                 'been given.\n\nProbably because database ',
                                 'has been closed and opened since this copy ',
                                 'was displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Delete Game Selection Rule',
                message='\n'.join((
                    'Cannot delete game selection rule.',
                    'Record has been amended since this copy displayed.')))
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Delete Game Selection Rule',
            message='Confirm request to delete game selection rule.'):
            return
        s = self.query_statement
        if s.where_error is not None:
            v = self.sourceobject.value
            if (s.get_name_text() != v.get_name_text() or
                s.where_error != v.where_error or
                s.get_query_statement_text() != v.get_query_statement_text()):
                dialogues.showinfo(
                    title='Delete Game Selection Rule',
                    message='\n'.join((
                        'Cannot delete game selection rule.',
                        ' '.join((
                            'Rule on display is not same as',
                            'rule from record.')))))
                return
        editor = RecordDelete(self.sourceobject)
        editor.set_data_source(datasource, editor.on_data_change)
        editor.delete()
        dialogues.showinfo(
            title='Delete Game Selection Rule',
            message=''.join(('Game selection rule "',
                             self.sourceobject.value.get_name_text(),
                             '" deleted from database.')))


class DatabaseQueryInsert(QueryDisplay, QueryEdit, DataNotify):
    
    """Display game selection rule from database allowing insert.

    QueryEdit provides the widget and QueryDisplay the database
    interface.
    
    """

    def __init__(self, **ka):
        """Create editor widget and display game selection rule from database.

        See superclasses for argument descriptions.

        """
        super().__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databaseselectionedit_show_game_list, ''),
            (EventSpec.databaseselectionedit_insert, ''),
            (EventSpec.databaseselectionedit_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super().initialize_bindings()

        # Here because superclass order is QueryDisplay, QueryEdit.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)

        for function, accelerator in (
            (self.set_focus_panel_item_command,
             EventSpec.databaseselectionedit_make_active),
            (self.delete_item_view,
             EventSpec.databaseselectionedit_dismiss_inactive),
            ):
            self.inactive_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.inactive_popup),
                accelerator=accelerator[2])
        self.__bind_on()
        for function, accelerator in (
            (self.process_and_set_selection_rule_list,
             EventSpec.databaseselectionedit_show_game_list),
            (self.delete_item_view,
             EventSpec.databaseselectionedit_dismiss),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        for function, accelerator in (
            (self.insert_selection_rule_database,
             EventSpec.databaseselectionedit_insert),
            ):
            self.viewmode_database_popup.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.viewmode_database_popup),
                accelerator=accelerator[2])
        self.bind_toplevel_navigation()

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()"""
        for sequence, function in (
            (EventSpec.databaseselectionedit_show_game_list,
             self.process_and_set_selection_rule_list),
            (EventSpec.databaseselectionedit_insert,
             self.insert_selection_rule_database),
            (EventSpec.databaseselectionedit_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def insert_char_to_right(self, char):
        """"""
        r = super().insert_char_to_right(char)
        if r is None:
            return None
        elif r:
            return True
        else:
            self.recalculate_after_edit = None
            return None

    def delete_char_left(self, event):
        """"""
        if not self.current:
            return 'break'
        self.recalculate_after_edit = None
        return super().delete_char_left(event)

    def delete_char_right(self, event):
        """"""
        if not self.current:
            return 'break'
        self.recalculate_after_edit = None
        return super().delete_char_right(event)


class DatabaseQueryEdit(DatabaseQueryInsert):
    
    """Display game selection rule from database allowing edit and insert.

    DatabaseQueryEdit adds insert to the database interface.
    
    """

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databaseselectionedit_update, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super().initialize_bindings()
        self.__bind_on()
        for function, accelerator in (
            (self.update_selection_rule_database,
             EventSpec.databaseselectionedit_update),
            ):
            self.viewmode_database_popup.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.viewmode_database_popup),
                accelerator=accelerator[2])

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()"""
        for sequence, function in (
            (EventSpec.databaseselectionedit_update,
             self.update_selection_rule_database),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def update_selection_rule_database(self, event=None):
        """Modify existing game selection rule record."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Edit Game Selection Rule',
                message='Cannot edit repertoire:\n\nNo database open.')
            return
        datasource = self.ui.base_selections.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Edit Game Selection Rule',
                message='Cannot edit game selection rule:\n\nRule list hidden.')
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Edit Game Selection Rule',
                message=''.join(('The game selection rule to edit has not ',
                                 'been given.\n\nProbably because database ',
                                 'has been closed and opened since this copy ',
                                 'was displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Edit Game Selection Rule',
                message='\n'.join((
                    'Cannot edit game selection rule.',
                    'Rule has been amended since this copy was displayed.')))
            return
        original = ChessDBrecordQuery()
        original.set_database(datasource.dbhome)
        original.load_record(
            (self.sourceobject.key.recno,
             self.sourceobject.srvalue))

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        updater = ChessDBrecordQuery()
        updater.value.set_database(datasource.dbhome)
        updater.value.dbset = self.ui.base_games.datasource.dbset
        uvpqs = updater.value.process_query_statement(
            self.get_name_query_statement_text())
        if not len(updater.value.get_name_text()):
            dialogues.showerror(
                title='Edit Game Selection Rule',
                message=''.join((
                    "The selection rule has no name.\n\nPlease enter it's ",
                    "name as the first line of text.'")))
            return
        if not uvpqs:
            if not updater.value.where_error:
                if tkinter.messagebox.YES != dialogues.askquestion(
                    title='Edit Game Selection Rule',
                    message=''.join((
                        'Confirm request to edit game selection rule ',
                        'named:\n\n',
                        updater.value.get_name_text(),
                        '\n\nto database.\n\n',
                        'Note validation of the statement failed but no ',
                        'information is available.',
                        ))):
                    dialogues.showinfo(
                        title='Edit Game Selection Rule',
                        message=''.join(('Edit game selection rule to ',
                                         'database abandonned.')))
                    return
            elif tkinter.messagebox.YES != dialogues.askquestion(
                title='Edit Game Selection Rule',
                message=''.join((
                    'Confirm request to edit game selection rule named:\n\n',
                    updater.value.get_name_text(),
                    '\n\nto database.\n\n',
                    updater.value.where_error.get_error_report(
                        self.ui.base_games.get_data_source())))):
                dialogues.showinfo(
                    title='Edit Game Selection Rule',
                    message=''.join(('Edit game selection rule to ',
                                     'database abandonned.')))
                return
        elif tkinter.messagebox.YES != dialogues.askquestion(
            title='Edit Game Selection Rule',
            message=''.join((
                'Confirm request to edit game selection rule named:\n\n',
                updater.value.get_name_text(),
                '\n\non database.',))):
            dialogues.showinfo(
                title='Edit Game Selection Rule',
                message='Edit game selection rule to database abandonned.')
            return
        editor = RecordEdit(updater, original)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        editor.edit()
        dialogues.showinfo(
            title='Edit Game Selection Rule',
            message=''.join(('Game selection rule "',
                             updater.value.get_name_text(),
                             '" amended on database.')))


class QueryDialogue(ChessException):
    
    """Manage UI interaction with database for a displayed game selection rule.

    Subclasses provide the widget to display the game selection rule.
    
    """

    # Formally the same as GameDialogue in gamedisplay module.
    # Follow whatever style of assignment is used there if this binding_labels
    # needs to be non-empty.
    binding_labels = tuple()

    def initialize_bindings(self):
        """Enable all bindings."""
        self.bind_score_pointer_for_board_navigation(True)
        self.bind_toplevel_navigation()
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for QueryDialogue instance."""

        # Formally the same as GameDialogue in gamedisplay module.
        # The effect is add no bindings to an empty bindings map.
        navigation_map = {}
        for nm, widget in (
            ({},
             self),
            ):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)


class DialogueQueryDisplay(Query, QueryDialogue):
    
    """Display a game selection rule from a database allowing delete and insert.
    """

    def __init__(self, **ka):
        """Extend and link game selection rule to database.
        """
        super(DialogueQueryDisplay, self).__init__(**ka)
        self.initialize_bindings()


class DialogueQueryEdit(QueryEdit, QueryDialogue):
    
    """Display a game selection rule from a database allowing edit and insert.
    """

    def __init__(self, **ka):
        """Extend and link game selection rule to database.

        """
        super(DialogueQueryEdit, self).__init__(**ka)
        self.initialize_bindings()
