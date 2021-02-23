# cqldisplay.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit Chess Query Language (ChessQL) statements.

These four classes display ChessQL statements in the main window: they are used
in the querygrid module.

The CQLDisplay class binds events to navigate between widgets.

The DatabaseCQLDisplay class adds delete record to the CQLDisplay class.

The DatabaseCQLInsert class adds insert record to the DatabaseCQLDisplay
class but does not bind delete record to any events.

The DatabaseCQLEdit class adds edit record to the DatabaseCQLInsert class
but does not bind delete record to any events.

These three classes display games in their own Toplevel widget: they are used
in the gamedbdelete, gamedbedit, and gamedbshow, modules.

The CQLDialogue class binds events to navigate between widgets.

The DialogueCQLDisplay class adds insert and delete record to the
CQLDialogue class.

The DialogueCQLEdit class adds insert and edit record to the CQLDialogue
class.

"""

import tkinter
import tkinter.messagebox

from solentware_misc.workarounds import dialogues

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from .cql import CQL
from .cqledit import CQLEdit
from ..core.chessrecord import ChessDBrecordPartial
from ..core.cqlstatement import CQLStatement
from .chessexception import ChessException
from .eventspec import EventSpec
from .display import Display
from .. import APPLICATION_NAME


class CQLDisplay(ChessException, Display):
    
    """Manage UI interaction with database for displayed ChessQL statements.

    CQLDisplay is a subclass of DataNotify so that modifications to
    the database record outside an instance prevent database update using
    the instance.  This class provides methods to update the database from
    the instance; and to switch to other displayed ChessQL statements.

    Subclasses provide the widget to display the ChessQL statements.
    
    """

    binding_labels = tuple(
        [b[1:] for b in (
            EventSpec.partialdisplay_to_position_grid,
            EventSpec.partialdisplay_to_active_game,
            EventSpec.partialdisplay_to_game_grid,
            EventSpec.partialdisplay_to_repertoire_grid,
            EventSpec.partialdisplay_to_active_repertoire,
            EventSpec.partialdisplay_to_repertoire_game_grid,
            EventSpec.partialdisplay_to_partial_grid,
            EventSpec.partialdisplay_to_previous_partial,
            EventSpec.partialdisplay_to_next_partial,
            EventSpec.partialdisplay_to_partial_game_grid,
            EventSpec.partialdisplay_to_selection_rule_grid,
            EventSpec.partialdisplay_to_active_selection_rule,
            EventSpec.tab_traverse_backward,
            EventSpec.tab_traverse_forward,
            )])

    def __init__(self, sourceobject=None, **ka):
        """Extend and link ChessQL statement to database.

        sourceobject - link to database.

        """
        super().__init__(**ka)
        self.blockchange = False
        if self.ui.base_partials.datasource:
            self.set_data_source(self.ui.base_partials.get_data_source())
        self.sourceobject = sourceobject
        self.insertonly = sourceobject is None
        self.recalculate_after_edit = sourceobject

    def _bind_for_board_navigation(self):
        """Set bindings to navigate ChessQL statement on pointer click."""
        self.bind_score_pointer_for_board_navigation(True)

    def bind_for_widget_navigation(self):
        """Set bindings to give focus to ChessQL statement on pointer click.
        """
        self.bind_score_pointer_for_widget_navigation(True)

    def bind_off(self):
        """Disable all bindings."""
        
        # Replicate structure of __bind_on for deleting bindings.
        for sequence, function in (
            (EventSpec.partialdisplay_to_partial_grid, ''),
            (EventSpec.partialdisplay_to_previous_partial, ''),
            (EventSpec.partialdisplay_to_next_partial, ''),
            (EventSpec.partialdisplay_to_partial_game_grid, ''),
            (EventSpec.partialdisplay_to_repertoire_grid, ''),
            (EventSpec.partialdisplay_to_active_repertoire, ''),
            (EventSpec.partialdisplay_to_repertoire_game_grid, ''),
            (EventSpec.partialdisplay_to_position_grid, ''),
            (EventSpec.partialdisplay_to_active_game, ''),
            (EventSpec.partialdisplay_to_selection_rule_grid, ''),
            (EventSpec.partialdisplay_to_active_selection_rule, ''),
            (EventSpec.partialdisplay_to_game_grid, ''),
            (EventSpec.export_from_partialdisplay, ''),
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
            (EventSpec.partialdisplay_to_partial_grid,
             self.set_focus_partial_grid),
            (EventSpec.partialdisplay_to_previous_partial,
             self.prior_item),
            (EventSpec.partialdisplay_to_next_partial,
             self.next_item),
            (EventSpec.partialdisplay_to_partial_game_grid,
             self.set_focus_partial_game_grid),
            (EventSpec.partialdisplay_to_repertoire_grid,
             self.set_focus_repertoire_grid),
            (EventSpec.partialdisplay_to_active_repertoire,
             self.set_focus_repertoirepanel_item),
            (EventSpec.partialdisplay_to_repertoire_game_grid,
             self.set_focus_repertoire_game_grid),
            (EventSpec.partialdisplay_to_position_grid,
             self.set_focus_position_grid),
            (EventSpec.partialdisplay_to_active_game,
             self.set_focus_gamepanel_item),
            (EventSpec.partialdisplay_to_selection_rule_grid,
             self.set_focus_selection_rule_grid),
            (EventSpec.partialdisplay_to_active_selection_rule,
             self.set_focus_selectionpanel_item),
            (EventSpec.partialdisplay_to_game_grid,
             self.set_focus_game_grid),
            (EventSpec.export_from_partialdisplay,
             self.export_partial),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def _cycle_item(self, prior=False):
        """Select next ChessQL statement on display."""
        items = self.ui.partial_items
        losefocus = items.active_item
        losefocus.bind_for_widget_navigation()
        items.cycle_active_item(prior=prior)
        self.ui.configure_partial_grid()
        gainfocus = items.active_item
        gainfocus.refresh_game_list()
        gainfocus._bind_for_board_navigation()
        gainfocus.takefocus_widget.focus_set()
        gainfocus.set_statusbar_text()

    def give_focus_to_widget(self, event=None):
        """Select ChessQL statement on display by mouse click."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        losefocus, gainfocus = self.ui.partial_items.give_focus_to_widget(
            event.widget)
        if losefocus is not gainfocus:
            self.ui.configure_partial_grid()
            self.score.after(
                0,
                func=self.try_command(self.ui._set_partial_name, self.score))
            self.score.after(
                0,
                func=self.try_command(gainfocus.refresh_game_list, self.score))
        return 'break'

    def delete_item_view(self, event=None):
        """Remove ChessQL statement item from screen."""
        self.ui.delete_position_view(self)

    def insert_cql_statement_database(self, event=None):
        """Add ChessQL statement to database."""
        if self.ui.partial_items.active_item is None:
            dialogues.showinfo(
                title='Insert ChessQL Statement',
                message='No active ChessQL statement to insert into database.')
            return

        # This should see if ChessQL statement with same name already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            dialogues.showinfo(
                title='Insert ChessQL Statement',
                message='Cannot add ChessQL statement:\n\nNo database open.')
            return

        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Insert ChessQL Statement',
                message=''.join(('Cannot add ChessQL statement:\n\n',
                                 'Partial position list hidden.')))
            return
        updater = ChessDBrecordPartial()
        updater.value.process_statement(
            self.get_name_cql_statement_text())
        title = 'Insert ChessQL Statement'
        tname = title.replace('Insert ', '').replace('S', 's')
        if not len(updater.value.get_name_text()):
            dialogues.showerror(
                title=title,
                message=''.join((
                    "The '",
                    tname,
                    " has no name.\n\nPlease enter it's ",
                    "name as the first line of text.'")))
            return
        message=[
            ''.join((
                'Confirm request to add ',
                tname,
                ' named:\n\n',
                updater.value.get_name_text(),
                '\n\nto database.\n\n'))]
        if not updater.value.cql_error:
            if tkinter.messagebox.YES != dialogues.askquestion(
                title=title,
                message=''.join(message)):
                dialogues.showinfo(
                    title=title,
                    message=tname.join(('Add ',
                                        ' to database abandonned.')))
                return
        else:
            message.append(updater.value.cql_error.get_error_report())
            if tkinter.messagebox.YES != dialogues.askquestion(
                title=title,
                message=''.join(message)):
                dialogues.showinfo(
                    title=title,
                    message=tname.join(('Add ',
                                        ' to database abandonned.')))
                return
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        updater.key.recno = None#0
        editor.put()
        dialogues.showinfo(
            title=title,
            message=''.join((tname,
                             ' "',
                             updater.value.get_name_text(),
                             '" added to database.')))
        
    def next_item(self, event=None):
        """Select next ChessQL statement display.

        Call _next_cql_statement after 1 millisecond to allow message display

        """
        if self.ui.partial_items.count_items_in_stack() > 1:
            self.ui._set_find_partial_name_games(0)
            self.score.after(
                1, func=self.try_command(self._next_cql_statement, self.score))

    def _next_cql_statement(self):
        """Generate next ChessQL statement display.

        Call from next_item only.

        """
        self._cycle_item(prior=False)

    def on_game_change(self, instance):
        """Recalculate list of games for ChessQL statement after game update.

        instance is ignored: it is assumed a recalculation is needed.

        """
        if self.sourceobject is not None:
            self._get_cql_statement_games_to_grid(self.cql_statement)#.match)

    def on_partial_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if instance.newrecord:

            # Editing an existing record.
            value = instance.newrecord.value
            key = instance.newrecord.key

        else:

            # Inserting a new record or deleting an existing record.
            value = instance.value
            key = instance.key

        if self.sourceobject is not None:
            if (key == self.sourceobject.key and
                self.datasource.dbname == self.sourceobject.dbname and
                self.datasource.dbset == self.sourceobject.dbset):
                self.blockchange = True

        pds = self.ui.partial_games.datasource
        if self.sourceobject is not None and key != self.sourceobject.key:
            pass
        elif self is not self.ui.partial_items.active_item:
            pass
        elif instance.newrecord is None:
            pds.forget_cql_statement_games(instance)
        elif instance.newrecord is False:
            try:
                pds.update_cql_statement_games(instance)
            except AttributeError as exc:
                if str(exc) == "'NoneType' object has no attribute 'answer'":
                    msg = ''.join(
                        ("Unable to add ChessQL statement to database, ",
                         "probably because an 'empty square' is in the query ",
                         "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                         str(exc),
                         ))
                else:
                    msg = ''.join(
                        ("Unable to add ChessQL statement to database:\n\n",
                         "The reported error is:\n\n",
                         str(exc),
                         ))
                dialogues.showinfo(
                    title='Insert ChessQL Statement',
                    message=msg)
                return
            except Exception as exc:
                msg = ''.join(
                    ("Unable to add ChessQL statement to database:\n\n",
                     "The reported error is:\n\n",
                     str(exc),
                     ))
                dialogues.showinfo(
                    title='Insert ChessQL Statement',
                    message=msg)
                return
        else:

            # Unfortunatly the existing list will have to be recalculated if
            # one of the caught exceptions occurs.
            pds.forget_cql_statement_games(instance)
            try:
                pds.update_cql_statement_games(instance.newrecord)
            except AttributeError as exc:
                if str(exc) == "'NoneType' object has no attribute 'answer'":
                    msg = ''.join(
                        ("Unable to edit ChessQL statement on database, ",
                         "probably because an 'empty square' is in the query ",
                         "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                         str(exc),
                         ))
                else:
                    msg = ''.join(
                        ("Unable to edit ChessQL statement on database:\n\n",
                         "The reported error is:\n\n",
                         str(exc),
                         ))
                dialogues.showinfo(
                    title='Insert ChessQL Statement',
                    message=msg)
                return
            except Exception as exc:
                msg = ''.join(
                    ("Unable to edit ChessQL statement on database:\n\n",
                     "The reported error is:\n\n",
                     str(exc),
                     ))
                dialogues.showinfo(
                    title='Insert ChessQL Statement',
                    message=msg)
                return

        if self is self.ui.partial_items.active_item:
            if self.sourceobject is not None and key == self.sourceobject.key:
                
                # Maybe should create a new CQLStatement instance.
                # self.cql_statement is a CQLStatement instance.
                # value is a ChessDBvaluePartial instance.
                self.cql_statement = value
                self.set_cql_statement()
                self._get_cql_statement_games_to_grid(value)

    def prior_item(self, event=None):
        """Select previous ChessQL statement display.

        Call _prior_cql_statement after 1 millisecond to allow message display

        """
        if self.ui.partial_items.count_items_in_stack() > 1:
            self.ui._set_find_partial_name_games(-2)
            self.score.after(
                1, func=self.try_command(
                    self._prior_cql_statement, self.score))

    def _prior_cql_statement(self):
        """Generate previous ChessQL statement display.

        Call from prior_item only.

        """
        self._cycle_item(prior=True)

    def set_insert_or_delete(self):
        """Convert edit display to insert display.

        ChessQL statements displayed for editing from a database are not closed
        if the database is closed.  They are converted to insert displays and
        can be used to add new records to databases opened later.
        
        """
        self.sourceobject = None

    def get_text_for_statusbar(self):
        """"""
        return ''.join(
            ('Please wait while finding games for ChessQL statement ',
             self.cql_statement.get_name_text(),
             ))

    def get_selection_text_for_statusbar(self):
        """"""
        return self.cql_statement.get_name_text()
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for CQLDisplay instance."""
        navigation_map = {
            EventSpec.partialdisplay_to_position_grid[1]:
            self.set_focus_position_grid,
            EventSpec.partialdisplay_to_active_game[1]:
            self.set_focus_gamepanel_item_command,
            EventSpec.partialdisplay_to_game_grid[1]:
            self.set_focus_game_grid,
            EventSpec.partialdisplay_to_repertoire_grid[1]:
            self.set_focus_repertoire_grid,
            EventSpec.partialdisplay_to_active_repertoire[1]:
            self.set_focus_repertoirepanel_item_command,
            EventSpec.partialdisplay_to_repertoire_game_grid[1]:
            self.set_focus_repertoire_game_grid,
            EventSpec.partialdisplay_to_partial_grid[1]:
            self.set_focus_partial_grid,
            EventSpec.partialdisplay_to_partial_game_grid[1]:
            self.set_focus_partial_game_grid,
            EventSpec.partialdisplay_to_selection_rule_grid[1]:
            self.set_focus_selection_rule_grid,
            EventSpec.partialdisplay_to_active_selection_rule[1]:
            self.set_focus_selectionpanel_item_command,
            EventSpec.tab_traverse_backward[1]:
            self.traverse_backward,
            EventSpec.tab_traverse_forward[1]:
            self.traverse_forward,
            }
        for nm, widget in (
            ({EventSpec.partialdisplay_to_previous_partial[1]: self.prior_item,
              EventSpec.partialdisplay_to_next_partial[1]: self.next_item,
              },
             self),
            ):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)

    def set_game_list(self):
        """"""
        self.panel.after(
            0, func=self.try_command(self.ui._set_partial_name, self.panel))
        self.panel.after(
            0,
            func=self.try_command(self.refresh_game_list, self.panel))

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.ui.give_focus_backward(self.ui.partial_items)
        return 'break'

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.ui.give_focus_forward(self.ui.partial_items)
        return 'break'

    def traverse_round(self, event=None):
        """Give focus to next widget within active item in traversal order."""
        return 'break'

    def _get_cql_statement_games_to_grid(self, statement):#match):
        """Populate Partial Position games grid with games selected by match.

        "match" is named for the CQL version-1.0 keyword which started a CQL
        statement.  Usage is "(match ..." which become "cql(" no later than
        version 5.0 of CQL.  Thus "cql" is now a better name for the argument.

        """
        p = self.ui.partial_games
        if len(p.keys):
            key = p.keys[0]
        else:
            key = None
        p.close_client_cursor()
        try:
            p.datasource.get_cql_statement_games(statement, self.sourceobject)
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
            dialogues.showinfo(
                title='Delete ChessQL Statement',
                message=msg)
        except Exception as exc:
            msg = ''.join(
                ("Unable to list games for ChessQL statement:\n\n",
                 "The reported error is:\n\n",
                 str(exc),
                 ))
            dialogues.showinfo(
                title='Delete ChessQL Statement',
                message=msg)
        p.fill_view(currentkey=key, exclude=False)
        if p.datasource.not_implemented:
            dialogues.showinfo(
                title='ChessQL Statement Not Implemented',
                message=''.join(('These filters are not implemented and ',
                                 'are ignored:\n\n',
                                 '\n'.join(sorted(
                                     grid.datasource.not_implemented)))))


class DatabaseCQLDisplay(CQLDisplay, CQL, DataNotify):
    
    """Display ChessQL statement from database and allow delete and insert.

    CQL provides the widget and CQLDisplay the database interface.
    
    """

    def __init__(self, **ka):
        """Create display widget and display ChessQL statement from database.

        See superclasses for argument descriptions.

        """
        super().__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databasepartialdisplay_insert, ''),
            (EventSpec.databasepartialdisplay_delete, ''),
            (EventSpec.databasepartialdisplay_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super().initialize_bindings()

        # Here because superclass order is CQLDisplay, CQL.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)

        for function, accelerator in (
            (self.set_focus_panel_item_command,
             EventSpec.databasepartialdisplay_make_active),
            (self.delete_item_view,
             EventSpec.databasepartialdisplay_dismiss_inactive),
            ):
            self.inactive_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.inactive_popup),
                accelerator=accelerator[2])
        self.__bind_on()
        for function, accelerator in (
            (self.delete_item_view,
             EventSpec.databasepartialdisplay_dismiss),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        for function, accelerator in (
            (self.insert_cql_statement_database,
             EventSpec.databasepartialdisplay_insert),
            (self.delete_cql_statement_database,
             EventSpec.databasepartialdisplay_delete),
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
            (EventSpec.databasepartialdisplay_insert,
             self.insert_cql_statement_database),
            (EventSpec.databasepartialdisplay_delete,
             self.delete_cql_statement_database),
            (EventSpec.databasepartialdisplay_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def delete_cql_statement_database(self, event=None):
        """Remove ChessQL statement from database."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Delete ChessQL Statement',
                message=''.join(('Cannot delete ChessQL statement:\n\n',
                                 'No database open.')))
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            dialogues.showerror(
                title='Delete ChessQL Statement',
                message=''.join(('Cannot delete ChessQL statement:\n\n',
                                 'ChessQL statement list hidden.')))
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Delete ChessQL Statement',
                message=''.join(('The ChessQL statement to delete has not ',
                                 'been given.\n\nProbably because database ',
                                 'has been closed and opened since this copy ',
                                 'was displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Delete ChessQL Statement',
                message='\n'.join((
                    'Cannot delete ChessQL statement.',
                    'Record has been amended since this copy displayed.')))
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Delete ChessQL Statement',
            message='Confirm request to delete ChessQL statement.'):
            return
        s = self.cql_statement

        # Consider changing this since the call no longer ever returns None.
        if s.is_statement() is not None:
            
            v = self.sourceobject.value
            if (s.get_name_text() != v.get_name_text() or
                s.is_statement() != v.is_statement() or
                s.get_statement_text() != v.get_statement_text()):
                dialogues.showinfo(
                    title='Delete ChessQL Statement',
                    message='\n'.join((
                        'Cannot delete ChessQL statement.',
                        ' '.join((
                            'ChessQL statement on display is not same as',
                            'rule from record.')))))
                return
        editor = RecordDelete(self.sourceobject)
        editor.set_data_source(datasource, editor.on_data_change)
        editor.delete()
        dialogues.showinfo(
            title='Delete ChessQL Statement',
            message=''.join(('ChessQL statement "',
                             self.sourceobject.value.get_name_text(),
                             '" deleted from database.')))


class DatabaseCQLInsert(CQLDisplay, CQLEdit, DataNotify):
    
    """Display ChessQL statement from database allowing insert.

    CQLEdit provides the widget and CQLDisplay the database
    interface.
    
    """

    def __init__(self, **ka):
        """Create editor widget and display ChessQL statement from database.

        See superclasses for argument descriptions.

        """
        super().__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databasepartialedit_show_game_list, ''),
            (EventSpec.databasepartialedit_insert, ''),
            (EventSpec.databasepartialedit_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super().initialize_bindings()

        # Here because superclass order is CQLDisplay, CQLEdit.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)

        for function, accelerator in (
            (self.set_focus_panel_item_command,
             EventSpec.databasepartialedit_make_active),
            (self.delete_item_view,
             EventSpec.databasepartialedit_dismiss_inactive),
            ):
            self.inactive_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.inactive_popup),
                accelerator=accelerator[2])
        self.__bind_on()
        for function, accelerator in (
            (self.process_and_set_cql_statement_list,
             EventSpec.databasepartialedit_show_game_list),
            (self.delete_item_view,
             EventSpec.databasepartialedit_dismiss),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        for function, accelerator in (
            (self.insert_cql_statement_database,
             EventSpec.databasepartialedit_insert),
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
            (EventSpec.databasepartialedit_show_game_list,
             self.process_and_set_cql_statement_list),
            (EventSpec.databasepartialedit_insert,
             self.insert_cql_statement_database),
            (EventSpec.databasepartialedit_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def process_and_set_cql_statement_list(self, event=None):
        """Display games with position matching edited ChessQL statement."""
        s = CQLStatement()
        # Not sure this is needed or wanted.
        #s.dbset = self.ui.base_games.datasource.dbset
        s.process_statement(
            self.get_name_cql_statement_text())
        self.cql_statement = s
        try:
            self.refresh_game_list()
        except AttributeError as exc:
            if str(exc) == "'NoneType' object has no attribute 'answer'":
                msg = ''.join(
                    ("Unable to list games for ChessQL statement, probably ",
                     "because an 'empty square' is in the query ",
                     "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                     str(exc),
                     ))
            else:
                msg = ''.join(
                    ("Unable to list games for ChessQL statement:\n\n",
                     "The reported error is:\n\n",
                     str(exc),
                     ))
            dialogues.showinfo(
                title='ChessQL Statement',
                message=msg)
        except Exception as exc:
            msg = ''.join(
                ("Unable to list games for ChessQL statement:\n\n",
                 "The reported error is:\n\n",
                 str(exc),
                 ))
            dialogues.showinfo(
                title='ChessQL Statement',
                message=msg)
        return 'break'

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


class DatabaseCQLEdit(DatabaseCQLInsert):
    
    """Display ChessQL statement from database allowing edit and insert.

    DatabaseCQLInsert adds insert to the database interface.
    
    """

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databasepartialedit_update, ''),
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
            (self.update_cql_statement_database,
             EventSpec.databasepartialedit_update),
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
            (EventSpec.databasepartialedit_update,
             self.update_cql_statement_database),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def update_cql_statement_database(self, event=None):
        """Modify existing ChessQL statement record."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Edit ChessQL Statement',
                message='Cannot edit ChessQL statement:\n\nNo database open.')
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Edit ChessQL Statement',
                message=''.join(('Cannot edit ChessQL statement:\n\n',
                                 'Partial position list hidden.')))
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Edit ChessQL Statement',
                message=''.join(('The ChessQL statement to edit has not ',
                                 'been given.\n\nProbably because database ',
                                 'has been closed and opened since this copy ',
                                 'was displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Edit ChessQL Statement',
                message='\n'.join((
                    'Cannot edit ChessQL statement.',
                    'It has been amended since this copy was displayed.')))
            return
        original = ChessDBrecordPartial()
        original.load_record(
            (self.sourceobject.key.recno,
             self.sourceobject.srvalue))

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        updater = ChessDBrecordPartial()
        updater.value.process_statement(
            self.get_name_cql_statement_text())
        title = 'Edit ChessQL Statement'
        tname = title.replace('Edit ', '').replace('S', 's')
        if not len(updater.value.get_name_text()):
            dialogues.showerror(
                title=title,
                message=''.join((
                    "The '",
                    tname,
                    " has no name.\n\nPlease enter it's ",
                    "name as the first line of text.'")))
            return
        message=[
            ''.join((
                'Confirm request to edit ',
                tname,
                ' named:\n\n',
                updater.value.get_name_text(),
                '\n\non database.\n\n'))]
        if not updater.value.cql_error:
            if tkinter.messagebox.YES != dialogues.askquestion(
                title=title,
                message=''.join(message)):
                dialogues.showinfo(
                    title=title,
                    message=tname.join(('Edit ',
                                        ' on database abandonned.')))
                return
        else:
            message.append(updater.value.cql_error.get_error_report())
            if tkinter.messagebox.YES != dialogues.askquestion(
                title=title,
                message=''.join(message)):
                dialogues.showinfo(
                    title=title,
                    message=tname.join(('Edit ',
                                        ' on database abandonned.')))
                return
        editor = RecordEdit(updater, original)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        editor.edit()
        dialogues.showinfo(
            title=title,
            message=''.join((tname,
                             ' "',
                             updater.value.get_name_text(),
                             '" amended on database.')))


class CQLDialogue(ChessException):
    
    """Manage UI interaction with database for a displayed ChessQL statement.

    Subclasses provide the widget to display the ChessQL statement.
    
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
        """Set bindings for popup menu for CQLDialogue instance."""

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


class DialogueCQLDisplay(CQL, CQLDialogue):
    
    """Display a ChessQL statement from a database allowing delete and insert.
    """

    def __init__(self, **ka):
        """Extend and link ChessQL statement to database.
        """
        super().__init__(**ka)
        self.initialize_bindings()


class DialogueCQLEdit(CQLEdit, CQLDialogue):
    
    """Display a ChessQL statement from a database allowing edit and insert.
    """

    def __init__(self, **ka):
        """Extend and link ChessQL statement to database.

        """
        super().__init__(**ka)
        self.initialize_bindings()
