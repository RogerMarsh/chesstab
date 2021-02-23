# repertoiredisplay.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit repertoires.

These four classes display repertoires in the main window: they are used in the
gamelistgrid module.

The RepertoireDisplay class binds events to navigate between widgets.

The DatabaseRepertoireDisplay class adds delete record to the
RepertoireDisplay class.

The DatabaseRepertoireInsert class adds insert record to the
DatabaseRepertoireDisplay class but does not bind delete record to any events.

The DatabaseRepertoireEdit class adds edit record to the
DatabaseRepertoireInsert class but does not bind delete record to any events.

These three classes display games in their own Toplevel widget: they are used
in the repertoiredbdelete, repertoiredbedit, and repertoiredbshow, modules.

The RepertoireDialogue class binds events to navigate between widgets.

The DialogueRepertoireDisplay class adds insert and delete record to the
RepertoireDialogue class.

The DialogueRepertoireEdit class adds insert and edit record to the
RepertoireDialogue class.

"""

import tkinter
import tkinter.messagebox

from solentware_misc.workarounds import dialogues

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from ..core.constants import TAG_OPENING
from .game import Repertoire
from .gameedit import RepertoireEdit
from ..core.chessrecord import ChessDBrecordRepertoireUpdate
from .chessexception import ChessException
from .eventspec import EventSpec
from .display import Display


class RepertoireDisplay(ChessException, Display):
    
    """Manage UI interaction with database for particular displayed repertoire.

    RepertoireDisplay is a subclass of DataNotify so that modifications to
    the database record outside an instance prevent database update using
    the instance.  This class provides methods to update the database from
    the instance; to switch to other displayed games; and update list of
    games matching current position in repertoire after traversing the
    repertoire score.

    Subclasses provide the widget to display the repertoire.
    
    """

    binding_labels = tuple(
        [b[1:] for b in (
            EventSpec.repertoiredisplay_to_position_grid,
            EventSpec.repertoiredisplay_to_active_game,
            EventSpec.repertoiredisplay_to_game_grid,
            EventSpec.repertoiredisplay_to_repertoire_grid,
            EventSpec.repertoiredisplay_to_previous_repertoire,
            EventSpec.repertoiredisplay_analysis_to_repertoire,
            EventSpec.repertoiredisplay_to_next_repertoire,
            EventSpec.repertoiredisplay_to_repertoire_game_grid,
            EventSpec.repertoiredisplay_repertoire_to_analysis,
            EventSpec.repertoiredisplay_to_partial_grid,
            EventSpec.repertoiredisplay_to_active_partial,
            EventSpec.repertoiredisplay_to_partial_game_grid,
            EventSpec.repertoiredisplay_to_selection_rule_grid,
            EventSpec.repertoiredisplay_to_active_selection_rule,
            EventSpec.tab_traverse_backward,
            EventSpec.tab_traverse_forward,
            )])

    def __init__(self, sourceobject=None, **ka):
        """Extend and link repertoire to database.

        sourceobject - link to database.

        """
        super(RepertoireDisplay, self).__init__(**ka)
        self.blockchange = False
        if self.ui.base_repertoires.datasource:
            self.set_data_source(self.ui.base_repertoires.get_data_source())
        self.sourceobject = sourceobject

    def _bind_for_board_navigation(self):
        """Set bindings to navigate repertoire score on pointer click."""
        self.bind_board_pointer_for_board_navigation(True)
        if self.score is self.takefocus_widget:
            self.bind_score_pointer_for_board_navigation(True)
            self.analysis.bind_score_pointer_for_board_navigation(False)
        else:
            self.bind_score_pointer_for_board_navigation(False)
            self.analysis.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)

    def bind_for_widget_navigation(self):
        """Set bindings to give focus to this repertoire on pointer click."""
        self.bind_score_pointer_for_widget_navigation(True)
        self.bind_board_pointer_for_widget_navigation(True)

    def bind_off(self):
        """Disable all bindings."""

        # What about ButtonPress? Or should those bindings not be set in
        # __bind_on but in initialize_bindings?
        
        # Replicate structure of __bind_on for deleting bindings.
        for sequence, function in (
            (EventSpec.repertoiredisplay_to_repertoire_grid, ''),
            (EventSpec.repertoiredisplay_to_repertoire_game_grid, ''),
            (EventSpec.repertoiredisplay_to_partial_grid, ''),
            (EventSpec.repertoiredisplay_to_active_partial, ''),
            (EventSpec.repertoiredisplay_to_partial_game_grid, ''),
            (EventSpec.repertoiredisplay_to_position_grid, ''),
            (EventSpec.repertoiredisplay_to_active_game, ''),
            (EventSpec.repertoiredisplay_to_game_grid, ''),
            (EventSpec.repertoiredisplay_to_selection_rule_grid, ''),
            (EventSpec.repertoiredisplay_to_active_selection_rule, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
            self.analysis.score.bind(sequence[0], function)
        for sequence, function, widget in (
            (EventSpec.repertoiredisplay_repertoire_to_analysis,
             '',
             self.score),
            (EventSpec.repertoiredisplay_to_previous_repertoire,
             '',
             self.score),
            (EventSpec.repertoiredisplay_to_next_repertoire,
             '',
             self.score),
            (EventSpec.repertoiredisplay_analysis_to_repertoire,
             '',
             self.analysis.score),
            ):
            if function:
                function = self.try_event(function)
            widget.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""

        # No traverse_round because Alt-F8 already bound.
        self.__bind_on()
        for sequence, function in (
            (EventSpec.tab_traverse_forward,
             self.traverse_forward),
            (EventSpec.tab_traverse_backward,
             self.traverse_backward),
            ):
            for s in self.score, self.analysis.score:
                if function:
                    function = self.try_event(function)
                s.bind(sequence[0], function)

    def __bind_on(self):
        """Enable all bindings."""

        # Same bindings in initialize_bindings() and bind_on() in this class.
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', self.try_event(self.give_focus_to_widget)),
            ('<ButtonPress-3>', self.try_event(self.popup_inactive_menu)),
            ):
            for w in self.board.boardsquares.values():
                w.bind(sequence, function)
            for w in self.score, self.analysis.score:
                w.bind(sequence, function)
        for sequence, function in (
            (EventSpec.repertoiredisplay_to_repertoire_grid,
             self.set_focus_repertoire_grid),
            (EventSpec.repertoiredisplay_to_repertoire_game_grid,
             self.set_focus_repertoire_game_grid),
            (EventSpec.repertoiredisplay_to_partial_grid,
             self.set_focus_partial_grid),
            (EventSpec.repertoiredisplay_to_active_partial,
             self.set_focus_partialpanel_item),
            (EventSpec.repertoiredisplay_to_partial_game_grid,
             self.set_focus_partial_game_grid),
            (EventSpec.repertoiredisplay_to_position_grid,
             self.set_focus_position_grid),
            (EventSpec.repertoiredisplay_to_active_game,
             self.set_focus_gamepanel_item),
            (EventSpec.repertoiredisplay_to_game_grid,
             self.set_focus_game_grid),
            (EventSpec.repertoiredisplay_to_selection_rule_grid,
             self.set_focus_selection_rule_grid),
            (EventSpec.repertoiredisplay_to_active_selection_rule,
             self.set_focus_selectionpanel_item),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
            self.analysis.score.bind(sequence[0], function)
        for sequence, function, widget in (
            (EventSpec.repertoiredisplay_repertoire_to_analysis,
             self.analysis_current_item,
             self.score),
            (EventSpec.repertoiredisplay_to_previous_repertoire,
             self.prior_item,
             self.score),
            (EventSpec.repertoiredisplay_to_next_repertoire,
             self.next_item,
             self.score),
            (EventSpec.repertoiredisplay_analysis_to_repertoire,
             self.current_item,
             self.analysis.score),
            ):
            if function:
                function = self.try_event(function)
            widget.bind(sequence[0], function)

    def bind_on(self):
        """Enable all bindings."""
        self.__bind_on()

    def _cycle_item(self, prior=False):
        """Select next repertoire on display."""
        items = self.ui.repertoire_items
        losefocus = items.active_item
        losefocus.bind_for_widget_navigation()
        items.cycle_active_item(prior=prior)
        self.ui.configure_repertoire_grid()
        gainfocus = items.active_item
        gainfocus.set_game_list()
        gainfocus._bind_for_board_navigation()
        gainfocus.takefocus_widget.focus_set()
        gainfocus.set_statusbar_text()

    def give_focus_to_widget(self, event=None):
        """Select repertoire on display by mouse click."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        losefocus, gainfocus = self.ui.repertoire_items.give_focus_to_widget(
            event.widget)
        if losefocus is not gainfocus:
            self.ui.configure_repertoire_grid()
            gainfocus.set_game_list()
        return 'break'

    def delete_item_view(self, event=None):
        """Remove repertoire item from screen."""
        self.set_data_source()
        self.ui.delete_repertoire_view(self)
        
    def game_updater(self, text):
        """Make and return a chess record containing a single repertoire."""
        updater = ChessDBrecordRepertoireUpdate()
        updater.value.load(text)
        return updater
        
    def insert_game_database(self, event=None):
        """Add repertoire to database on request from repertoire display."""
        if self.ui.repertoire_items.active_item is None:
            dialogues.showerror(
                title='Insert Repertoire',
                message='No active repertoire to insert into database.')
            return

        # This should see if repertoire with same name already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            dialogues.showinfo(
                title='Insert Repertoire',
                message='Cannot add repertoire:\n\nNo database open.')
            return

        datasource = self.ui.base_repertoires.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Insert Repertoire',
                message='Cannot add repertoire:\n\nRepertoire list hidden.')
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Insert Repertoire',
            message='Confirm request to add repertoire to database'):
            dialogues.showinfo(
                title='Insert Repertoire',
                message='Add repertoire to database abandonned.')
            return
        updater = self.game_updater(repr(self.score.get('1.0', tkinter.END)))
        if not updater.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != dialogues.askquestion(
                title='Insert Repertoire',
                message=''.join(
                    ('The new repertoire contains at least one illegal move ',
                     'in PGN.\n\nPlease re-confirm request to insert ',
                     'repertoire.',
                     ))):
                return
            updater.value.set_game_source('No opening name')
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        updater.key.recno = None
        editor.put()
        tags = updater.value.collected_game._tags
        dialogues.showinfo(
            title='Insert Repertoire',
            message=''.join(('Repertoire "',
                             '  '.join([tags.get(k, '')
                                        for k in (TAG_OPENING,)]),
                             '" added to database.')))
        return True

    def next_item(self, event=None):
        """Select next repertoire on display."""
        if self.ui.repertoire_items.count_items_in_stack() > 1:
            self._cycle_item(prior=False)

    def on_game_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            if self.ui.repertoire_items.is_item_panel_active(self):
                key = None
                p = self.ui.repertoire_games
                for e, k in enumerate(p.keys):
                    if instance.key.recno != k[0]:
                        key = k
                        break
                p.close_client_cursor()
                p.datasource.get_full_position_games(self.get_position_key())
                p.fill_view(currentkey=key, exclude=False)

    def on_repertoire_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            if (instance.key == self.sourceobject.key and
                self.datasource.dbname == self.sourceobject.dbname and
                self.datasource.dbset == self.sourceobject.dbset):
                self.blockchange = True

    def prior_item(self, event=None):
        """Select previous repertoire on display."""
        if self.ui.repertoire_items.count_items_in_stack() > 1:
            self._cycle_item(prior=True)

    def set_insert_or_delete(self):
        """Convert edit display to insert display.

        Games displayed for editing from a database are not closed if the
        database is closed.  They are converted to insert displays and can
        be used to add new records to databases opened later.
        
        """
        self.sourceobject = None

    def analysis_current_item(self, event=None):
        """Select current repertoire analysis."""
        if self.game_position_analysis:
            self.analysis.apply_colouring_to_variation_back_to_main_line()
        else:
            self.analysis.clear_current_range()
            self.analysis.clear_moves_played_in_variation_colouring_tag()
            self.analysis.current = None
        self.analysis.set_current()
        self.analysis.set_game_board()
        self.bind_score_pointer_for_board_navigation(False)
        self.analysis.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)
        self.analysis.score.focus_set()
        self.game_position_analysis = True
        self.takefocus_widget = self.analysis.score

    def current_item(self, event=None):
        """Select current repertoire on display."""

        # cuirs should be referencing self given use of current_item() method,
        # but style of sibling *_item() methods is followed.
        if self.ui.repertoire_items.count_items_in_stack():
            cuirs = self.ui.repertoire_items.active_item
            self.analysis.clear_current_range()
            self.analysis.clear_moves_played_in_variation_colouring_tag()
            if cuirs.current is None:
                cuirs.board.set_board(cuirs.fen_tag_square_piece_map())
            else:
                cuirs.board.set_board(cuirs.tagpositionmap[cuirs.current][0])
            cuirs.set_game_list()
            cuirs.analysis.bind_score_pointer_for_board_navigation(False)
            cuirs.bind_score_pointer_for_board_navigation(True)
            cuirs.bind_score_pointer_for_toggle_game_analysis(True)
            self.takefocus_widget = self.score
            cuirs.takefocus_widget.focus_set()
            cuirs.set_statusbar_text()

    def get_text_for_statusbar(self):
        """"""
        return ''.join(
            ('Please wait while finding games for repertoire position in ',
             self.pgn.tags.get(TAG_OPENING, '?'),
             ))

    def get_selection_text_for_statusbar(self):
        """"""
        return self.pgn.tags.get(TAG_OPENING, '?')
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for RepertoireDisplay instance."""
        navigation_map = {
            EventSpec.repertoiredisplay_to_position_grid[1]:
            self.set_focus_position_grid,
            EventSpec.repertoiredisplay_to_active_game[1]:
            self.set_focus_gamepanel_item_command,
            EventSpec.repertoiredisplay_to_game_grid[1]:
            self.set_focus_game_grid,
            EventSpec.repertoiredisplay_to_repertoire_grid[1]:
            self.set_focus_repertoire_grid,
            EventSpec.repertoiredisplay_to_repertoire_game_grid[1]:
            self.set_focus_repertoire_game_grid,
            EventSpec.repertoiredisplay_to_partial_grid[1]:
            self.set_focus_partial_grid,
            EventSpec.repertoiredisplay_to_active_partial[1]:
            self.set_focus_partialpanel_item_command,
            EventSpec.repertoiredisplay_to_partial_game_grid[1]:
            self.set_focus_partial_game_grid,
            EventSpec.repertoiredisplay_to_selection_rule_grid[1]:
            self.set_focus_selection_rule_grid,
            EventSpec.repertoiredisplay_to_active_selection_rule[1]:
            self.set_focus_selectionpanel_item_command,
            EventSpec.tab_traverse_backward[1]:
            self.traverse_backward,
            EventSpec.tab_traverse_forward[1]:
            self.traverse_forward,
            }
        for nm, widget in (
            ({EventSpec.repertoiredisplay_to_previous_repertoire[1]:
              self.prior_item,
              EventSpec.repertoiredisplay_to_next_repertoire[1]:
              self.next_item,
              EventSpec.repertoiredisplay_repertoire_to_analysis[1]:
              self.analysis_current_item,
              },
             self),
            ({EventSpec.repertoiredisplay_analysis_to_repertoire[1]:
              self.current_item,
              },
             self.analysis)):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.bind_board_pointer_for_widget_navigation(True)
        self.bind_score_pointer_for_widget_navigation(True)
        self.ui.give_focus_backward(self.ui.repertoire_items)
        return 'break'

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.bind_board_pointer_for_widget_navigation(True)
        self.bind_score_pointer_for_widget_navigation(True)
        self.ui.give_focus_forward(self.ui.repertoire_items)
        return 'break'
        

class DatabaseRepertoireDisplay(RepertoireDisplay, Repertoire, DataNotify):
    
    """Display a repertoire from a database allowing delete and insert.

    Repertoire provides the widget and RepertoireDisplay the database interface.
    
    """

    def __init__(self, **ka):
        """Create repertoire display widget and show repertoire from database.

        See superclasses for argument descriptions.

        """
        super(DatabaseRepertoireDisplay, self).__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super(DatabaseRepertoireDisplay, self).bind_off()
        for sequence, function in (
            (EventSpec.databaserepertoiredisplay_insert, ''),
            (EventSpec.databaserepertoiredisplay_delete, ''),
            (EventSpec.databaserepertoiredisplay_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super(DatabaseRepertoireDisplay, self).initialize_bindings()

        # Here because superclass order is RepertoireDisplay, Repertoire.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.analysis.inactive_popup = tkinter.Menu(
            master=self.analysis.score, tearoff=False)

        for popup in self.inactive_popup, self.analysis.inactive_popup:
            for function, accelerator in (
                (self.set_focus_panel_item_command,
                 EventSpec.databaserepertoiredisplay_make_active),
                (self.delete_item_view,
                 EventSpec.databaserepertoiredisplay_dismiss_inactive),
                ):
                popup.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, popup),
                    accelerator=accelerator[2])
        self.__bind_on()
        for function, accelerator in (
            (self.insert_game_database,
             EventSpec.databaserepertoiredisplay_insert),
            (self.delete_game_database,
             EventSpec.databaserepertoiredisplay_delete),
            (self.delete_item_view,
             EventSpec.databaserepertoiredisplay_dismiss),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        self.bind_toplevel_navigation()

    def bind_on(self):
        """Enable all bindings."""
        super(DatabaseRepertoireDisplay, self).bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()"""
        for sequence, function in (
            (EventSpec.databaserepertoiredisplay_insert,
             self.insert_game_database),
            (EventSpec.databaserepertoiredisplay_delete,
             self.delete_game_database),
            (EventSpec.databaserepertoiredisplay_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def delete_game_database(self, event=None):
        """Remove repertoire from database on request from display."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Delete Repertoire',
                message='Cannot delete repertoire:\n\nNo database open.')
            return
        datasource = self.ui.base_repertoires.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Delete Repertoire',
                message='Cannot delete repertoire:\n\nRepertoire list hidden.')
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Delete Repertoire',
                message='\n'.join((
                    'Cannot delete repertoire:\n',
                    'Database has been closed since this copy displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Delete Repertoire',
                message='\n'.join((
                    'Cannot delete repertoire:\n',
                    'Record has been amended since this copy displayed.')))
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Delete Repertoire',
            message='Confirm request to delete repertoire from database.'):
            return
        original = ChessDBrecordRepertoireUpdate()
        original.load_record(
            (self.sourceobject.key.recno,
             self.sourceobject.srvalue))

        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        #original.value.set_game_source(self.sourceobject.value.gamesource)
        original.value.set_game_source('No opening name')

        editor = RecordDelete(original)
        editor.set_data_source(datasource, editor.on_data_change)
        editor.delete()
        tags = original.value.collected_game._tags
        dialogues.showinfo(
            title='Delete Repertoire',
            message=''.join(('Repertoire "',
                             '  '.join([tags.get(k, '')
                                        for k in (TAG_OPENING,)]),
                             '" deleted from database.')))


class DatabaseRepertoireInsert(RepertoireDisplay, RepertoireEdit, DataNotify):
    
    """Display a repertoire from a database allowing insert.

    RepertoireEdit provides the widget and RepertoireDisplay the
    database interface.
    
    """

    def __init__(self, **ka):
        """Create repertoire editor widget and display repertoire from database.

        See superclasses for argument descriptions.

        """
        super().__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databaserepertoireedit_insert, ''),
            (EventSpec.databaserepertoireedit_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super().initialize_bindings()

        # Here because superclass order is RepertoireDisplay, RepertoireEdit.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.analysis.inactive_popup = tkinter.Menu(
            master=self.analysis.score, tearoff=False)

        for popup in self.inactive_popup, self.analysis.inactive_popup:
            for function, accelerator in (
                (self.set_focus_panel_item_command,
                 EventSpec.databaserepertoireedit_make_active),
                (self.delete_item_view,
                 EventSpec.databaserepertoireedit_dismiss_inactive),
                ):
                popup.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, popup),
                    accelerator=accelerator[2])
        self.__bind_on()
        display_bindings = (
            (self.delete_item_view,
             EventSpec.databaserepertoireedit_dismiss),
            )
        database_bindings = (
            (self.insert_game_database,
             EventSpec.databaserepertoireedit_insert),
            )
        for menupopup, bindings in (
            (self.viewmode_popup, display_bindings),
            (self.viewmode_database_popup, database_bindings),
            (self.menupopup_pgntagmode, display_bindings),
            (self.menupopup_pgntag_database, database_bindings),
            ):
            for function, accelerator in bindings:
                menupopup.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menupopup),
                    accelerator=accelerator[2])
        self.bind_toplevel_navigation()

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()"""
        for sequence, function in (
            (EventSpec.databaserepertoireedit_insert,
             self.insert_game_database),
            (EventSpec.databaserepertoireedit_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)


class DatabaseRepertoireEdit(DatabaseRepertoireInsert):
    
    """Display a repertoire from a database allowing edit and insert.

    RepertoireEdit provides the widget and RepertoireDisplay the
    database interface.
    
    """

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databaserepertoireedit_update, ''),
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
        database_bindings = (
            (self.update_game_database,
             EventSpec.databaserepertoireedit_update),
            )
        for menupopup, bindings in (
            (self.viewmode_database_popup, database_bindings),
            (self.menupopup_pgntag_database, database_bindings),
            ):
            for function, accelerator in bindings:
                menupopup.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, menupopup),
                    accelerator=accelerator[2])

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()"""
        for sequence, function in (
            (EventSpec.databaserepertoireedit_update,
             self.update_game_database),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def update_game_database(self, event=None):
        """Modify existing repertoire record."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Edit Repertoire',
                message='Cannot edit repertoire:\n\nNo database open.')
            return
        datasource = self.ui.base_repertoires.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Edit Repertoire',
                message='Cannot edit repertoire:\n\nRepertoire list hidden.')
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Edit Repertoire',
                message='\n'.join((
                    'Cannot edit repertoire:\n',
                    'Database has been closed since this copy displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Edit Repertoire',
                message='\n'.join((
                    'Cannot edit repertoire:\n',
                    'Record has been amended since this copy displayed.')))
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Edit Repertoire',
            message='Confirm request to edit repertoire on database.'):
            return
        original = ChessDBrecordRepertoireUpdate()
        original.load_record(
            (self.sourceobject.key.recno,
             self.sourceobject.srvalue))

        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        #original.value.set_game_source(self.sourceobject.value.gamesource)
        original.value.set_game_source('No opening name')

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        text = self.get_score_error_escapes_removed()
        updater = self.game_updater(repr(text))
        editor = RecordEdit(updater, original)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        if not updater.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != dialogues.askquestion(
                title='Edit Game',
                message=''.join(
                    ('The edited repertoire contains at least one illegal ',
                     'move in PGN.\n\nPlease re-confirm request to edit ',
                     'repertoire.',
                     ))):
                return
            updater.value.set_game_source('No opening name')
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        editor.edit()
        if self is self.ui.repertoire_items.active_item:
            newkey = self.ui.repertoire_items.adjust_edited_item(updater)
            if newkey:
                self.ui.base_repertoires.set_properties(newkey)
        tags = original.value.collected_game._tags
        dialogues.showinfo(
            title='Edit Repertoire',
            message=''.join(('Repertoire "',
                             '  '.join([tags.get(k, '')
                                        for k in (TAG_OPENING,)]),
                             '" amended on database.')))


class RepertoireDialogue(ChessException):
    
    """Manage UI interaction with database for particular displayed repertoire.

    Subclasses provide the widget to display the repertoire.
    
    """

    binding_labels = tuple(
        [b[1:] for b in (
            EventSpec.repertoiredialogue_analysis_to_repertoire,
            EventSpec.repertoiredialogue_repertoire_to_analysis,
            )])

    def initialize_bindings(self):
        """Enable all bindings."""
        self.bind_board_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)
        self.bind_toplevel_navigation()
        self.__bind_on()
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for RepertoireDialogue instance."""
        navigation_map = {}
        for nm, widget in (
            ({EventSpec.repertoiredialogue_repertoire_to_analysis[1]:
              self.analysis_current_item,
              },
             self),
            ({EventSpec.repertoiredialogue_analysis_to_repertoire[1]:
              self.current_item,
              },
             self.analysis)):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)

    def analysis_current_item(self, event=None):
        """Select current repertoire analysis."""
        if self.game_position_analysis:
            self.analysis.apply_colouring_to_variation_back_to_main_line()
        else:
            self.analysis.clear_current_range()
            self.analysis.clear_moves_played_in_variation_colouring_tag()
            self.analysis.current = None
        self.analysis.set_current()
        self.analysis.set_game_board()
        self.bind_score_pointer_for_board_navigation(False)
        self.analysis.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)
        self.analysis.score.focus_set()
        self.game_position_analysis = True
        self.takefocus_widget = self.analysis.score

    def current_item(self, event=None):
        """Select current repertoire on display."""
        self.analysis.clear_current_range()
        self.analysis.clear_moves_played_in_variation_colouring_tag()
        if self.current is None:
            self.board.set_board(self.fen_tag_square_piece_map())
        else:
            self.board.set_board(self.tagpositionmap[self.current][0])
        self.set_game_list()
        self.analysis.bind_score_pointer_for_board_navigation(False)
        self.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)
        self.takefocus_widget = self.score
        self.takefocus_widget.focus_set()

    def __bind_on(self):
        """Enable all bindings."""
        for sequence, function, widget in (
            (EventSpec.repertoiredialogue_repertoire_to_analysis,
             self.analysis_current_item,
             self.score),
            (EventSpec.repertoiredialogue_analysis_to_repertoire,
             self.current_item,
             self.analysis.score),
            ):
            if function:
                function = self.try_event(function)
            widget.bind(sequence[0], function)


class DialogueRepertoireDisplay(Repertoire, RepertoireDialogue):
    
    """Display a repertoire from a database allowing delete and insert.
    """

    def __init__(self, **ka):
        """Extend and link repertoire to database."""
        super(DialogueRepertoireDisplay, self).__init__(**ka)
        self.initialize_bindings()
        
    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a repertoire including switching
        from one repertoire to another.
        
        """
        # Score.set_game_list() expects instance to have itemgrid attribute
        # bound to a DataGrid subclass instance, but DialogueRepertoireDisplay
        # instance can live without this being present.
        # It may be more appropriate to override set_game_list to do nothing so
        # there is a way of deleting a repertoire without tracking games
        # containing the same positions.
        try:
            super().set_game_list()
        except AttributeError:
            if self.itemgrid is not None:
                raise


class DialogueRepertoireEdit(RepertoireEdit, RepertoireDialogue):
    
    """Display a repertoire from a database allowing edit and insert.
    """

    def __init__(self, **ka):
        """Extend and link repertoire to database."""
        super(DialogueRepertoireEdit, self).__init__(**ka)
        self.initialize_bindings()
        
    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a repertoire including switching
        from one repertoire to another.
        
        """
        # Score.set_game_list() expects instance to have itemgrid attribute
        # bound to a DataGrid subclass instance, but DialogueRepertoireEdit
        # instance can live without this being present.
        # It may be more appropriate to override set_game_list to do nothing so
        # there is a way of editing or inserting a repertoire without
        # tracking games containing the same positions.
        try:
            super().set_game_list()
        except AttributeError:
            if self.itemgrid is not None:
                raise
