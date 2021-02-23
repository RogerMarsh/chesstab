# gamedisplay.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit game scores.

These three classes display games in the main window: they are used in the
gamelistgrid module.

The GameDisplay class binds events to navigate between widgets.

The DatabaseGameDisplay class adds delete record to the GameDisplay class.

The DatabaseGameInsert class adds insert record to the DatabaseGameDisplay
class but does not bind delete record to any events.

The DatabaseGameEdit class adds edit record to the DatabaseGameInsert class
but does not bind delete record to any events.

These three classes display games in their own Toplevel widget: they are used
in the gamedbdelete, gamedbedit, and gamedbshow, modules.

The GameDialogue class binds events to navigate between widgets.

The DialogueGameDisplay class adds insert and delete record to the GameDialogue
class.

The DialogueGameEdit class adds insert and edit record to the GameDialogue
class.

"""

import tkinter
import tkinter.messagebox

from solentware_misc.workarounds import dialogues

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from .game import Game
from .gameedit import GameEdit
from ..core.chessrecord import ChessDBrecordGameUpdate
from .constants import STATUS_SEVEN_TAG_ROSTER_PLAYERS
from .chessexception import ChessException
from .eventspec import EventSpec
from .display import Display


class GameDisplay(ChessException, Display):
    
    """Manage UI interaction with database for particular displayed game.

    GameDisplay is a subclass of DataNotify so that modifications to
    the database record outside an instance prevent database update using
    the instance.  This class provides methods to update the database from
    the instance; to switch to other displayed games; and update list of
    games matching current position in game after traversing the game score.

    Subclasses provide the widget to display the game.
    
    """

    binding_labels = tuple(
        [b[1:] for b in (
            EventSpec.gamedisplay_to_position_grid,
            EventSpec.gamedisplay_to_previous_game,
            EventSpec.gamedisplay_analysis_to_game,
            EventSpec.gamedisplay_to_next_game,
            EventSpec.gamedisplay_to_game_grid,
            EventSpec.gamedisplay_game_to_analysis,
            EventSpec.gamedisplay_to_repertoire_grid,
            EventSpec.gamedisplay_to_active_repertoire,
            EventSpec.gamedisplay_to_repertoire_game_grid,
            EventSpec.gamedisplay_to_partial_grid,
            EventSpec.gamedisplay_to_active_partial,
            EventSpec.gamedisplay_to_partial_game_grid,
            EventSpec.gamedisplay_to_selection_rule_grid,
            EventSpec.gamedisplay_to_active_selection_rule,
            EventSpec.tab_traverse_backward,
            EventSpec.tab_traverse_forward,
            )])

    def __init__(self, sourceobject=None, **ka):
        """Extend and link game to database.

        sourceobject - link to database.

        """
        super(GameDisplay, self).__init__(**ka)
        self.blockchange = False
        if self.ui.base_games.datasource:
            self.set_data_source(self.ui.base_games.get_data_source())
        self.sourceobject = sourceobject

    def _bind_for_board_navigation(self):
        """Set bindings to navigate game score on pointer click."""
        self.bind_board_pointer_for_board_navigation(True)
        if self.score is self.takefocus_widget:
            self.bind_score_pointer_for_board_navigation(True)
            self.analysis.bind_score_pointer_for_board_navigation(False)
        else:
            self.bind_score_pointer_for_board_navigation(False)
            self.analysis.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)

    def bind_for_widget_navigation(self):
        """Set bindings to give focus to this game on pointer click."""
        self.bind_score_pointer_for_widget_navigation(True)
        self.bind_board_pointer_for_widget_navigation(True)

    def bind_off(self):
        """Disable all bindings."""
        
        # Replicate structure of __bind_on for deleting bindings.
        for sequence, function in (
            (EventSpec.gamedisplay_to_repertoire_grid, ''),
            (EventSpec.gamedisplay_to_active_repertoire, ''),
            (EventSpec.gamedisplay_to_repertoire_game_grid, ''),
            (EventSpec.gamedisplay_to_partial_grid, ''),
            (EventSpec.gamedisplay_to_active_partial, ''),
            (EventSpec.gamedisplay_to_partial_game_grid, ''),
            (EventSpec.gamedisplay_to_position_grid, ''),
            (EventSpec.gamedisplay_to_game_grid, ''),
            (EventSpec.gamedisplay_to_selection_rule_grid, ''),
            (EventSpec.gamedisplay_to_active_selection_rule, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
            self.analysis.score.bind(sequence[0], function)
        for sequence, function, widget in (
            (EventSpec.gamedisplay_game_to_analysis,
             '',
             self.score),
            (EventSpec.gamedisplay_to_previous_game,
             '',
             self.score),
            (EventSpec.gamedisplay_to_next_game,
             '',
             self.score),
            (EventSpec.gamedisplay_analysis_to_game,
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
        self.__bind_on()

        # No traverse_round because Alt-F8 already bound.
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
        self.bind_score_pointer_for_widget_navigation(True)
        for sequence, function in (
            (EventSpec.gamedisplay_to_repertoire_grid,
             self.set_focus_repertoire_grid),
            (EventSpec.gamedisplay_to_active_repertoire,
             self.set_focus_repertoirepanel_item),
            (EventSpec.gamedisplay_to_repertoire_game_grid,
             self.set_focus_repertoire_game_grid),
            (EventSpec.gamedisplay_to_partial_grid,
             self.set_focus_partial_grid),
            (EventSpec.gamedisplay_to_active_partial,
             self.set_focus_partialpanel_item),
            (EventSpec.gamedisplay_to_partial_game_grid,
             self.set_focus_partial_game_grid),
            (EventSpec.gamedisplay_to_position_grid,
             self.set_focus_position_grid),
            (EventSpec.gamedisplay_to_game_grid,
             self.set_focus_game_grid),
            (EventSpec.gamedisplay_to_selection_rule_grid,
             self.set_focus_selection_rule_grid),
            (EventSpec.gamedisplay_to_active_selection_rule,
             self.set_focus_selectionpanel_item),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)
            self.analysis.score.bind(sequence[0], function)
        for sequence, function, widget in (
            (EventSpec.gamedisplay_game_to_analysis,
             self.analysis_current_item,
             self.score),
            (EventSpec.gamedisplay_to_previous_game,
             self.prior_item,
             self.score),
            (EventSpec.gamedisplay_to_next_game,
             self.next_item,
             self.score),
            (EventSpec.gamedisplay_analysis_to_game,
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
        """Select next game on display."""
        items = self.ui.game_items
        losefocus = items.active_item
        losefocus.bind_for_widget_navigation()
        items.cycle_active_item(prior=prior)
        self.ui.configure_game_grid()
        gainfocus = items.active_item
        gainfocus.set_game_list()
        gainfocus._bind_for_board_navigation()
        gainfocus.takefocus_widget.focus_set()
        gainfocus.set_statusbar_text()

    def give_focus_to_widget(self, event=None):
        """Select game on display by mouse click."""
        self.ui.set_bindings_on_item_losing_focus_by_pointer_click()
        losefocus, gainfocus = self.ui.game_items.give_focus_to_widget(
            event.widget)
        if losefocus is not gainfocus:
            self.ui.configure_game_grid()
            gainfocus.set_game_list()
        return 'break'

    def delete_item_view(self, event=None):
        """Remove game item from screen."""
        self.set_data_source()
        self.ui.delete_game_view(self)
        
    def game_updater(self, text):
        """Make and return a chess record containing a single game."""
        updater = ChessDBrecordGameUpdate()
        updater.value.load(text)
        return updater
        
    def insert_game_database(self, event=None):
        """Add game to database on request from game display."""
        if self.ui.game_items.active_item is None:
            dialogues.showerror(
                title='Insert Game',
                message='No active game to insert into database.')
            return

        # This should see if game with same PGN Tags already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            dialogues.showinfo(
                title='Insert Game',
                message='Cannot add game:\n\nNo database open.')
            return
        
        datasource = self.ui.base_games.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Insert Game',
                message='Cannot add game:\n\Game list hidden.')
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Insert Game',
            message='Confirm request to add game to database'):
            dialogues.showinfo(
                title='Insert Game',
                message='Add game to database abandonned.')
            return
        updater = self.game_updater(repr(self.score.get('1.0', tkinter.END)))
        if not updater.value.collected_game.is_pgn_valid():
            if tkinter.messagebox.YES != dialogues.askquestion(
                title='Insert Game',
                message=''.join(
                    ('The new game score contains at least one illegal move ',
                     'in PGN.\n\nPlease re-confirm request to insert game.',
                     ))):
                return
            updater.value.set_game_source('Editor')
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        datasource.dbhome.mark_partial_positions_to_be_recalculated()
        updater.key.recno = None
        editor.put()
        tags = updater.value.collected_game._tags
        dialogues.showinfo(
            title='Insert Game',
            message=''.join(('Game "',
                             '  '.join(
                                 [tags.get(k, '')
                                  for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS]),
                             '" added to database.')))
        return True

    def next_item(self, event=None):
        """Select next game on display."""
        if self.ui.game_items.count_items_in_stack() > 1:
            self._cycle_item(prior=False)

    def on_game_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            if (instance.key == self.sourceobject.key and
                self.datasource.dbname == self.sourceobject.dbname and
                self.datasource.dbset == self.sourceobject.dbset):
                self.blockchange = True
            if self.ui.game_items.is_item_panel_active(self):
                # Patch data structure to look as though the edited record has
                # been read from disk.  That means DataGrid, DisplayItems, and
                # this GameDisplay instances.
                # self.sourceobject is DataGrid.get_visible_record(<key>), the
                # record prior to editing.
                # instance adds index structures to match those which should be
                # on database.
                # instance.newrecord is edited record including index stuff.
                key = None
                p = self.ui.game_games
                for e, k in enumerate(p.keys):
                    if instance.key.recno != k[0]:
                        key = k
                        break
                p.close_client_cursor()
                p.datasource.get_full_position_games(self.get_position_key())
                p.fill_view(currentkey=key, exclude=False)

    def prior_item(self, event=None):
        """Select previous game on display."""
        if self.ui.game_items.count_items_in_stack() > 1:
            self._cycle_item(prior=True)

    def set_insert_or_delete(self):
        """Convert edit display to insert display.

        Games displayed for editing from a database are not closed if the
        database is closed.  They are converted to insert displays and can
        be used to add new records to databases opened later.
        
        """
        self.sourceobject = None

    def analysis_current_item(self, event=None):
        """Select current game analysis."""
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
        """Select current game on display."""

        # cuigs should be referencing self given use of current_item() method,
        # but style of sibling *_item() methods is followed.
        items = self.ui.game_items
        if items.count_items_in_stack():
            cuigs = items.active_item
            self.analysis.clear_current_range()
            self.analysis.clear_moves_played_in_variation_colouring_tag()
            if cuigs.current is None:
                cuigs.board.set_board(cuigs.fen_tag_square_piece_map())
            else:
                cuigs.board.set_board(cuigs.tagpositionmap[cuigs.current][0])
            cuigs.set_game_list()
            cuigs.analysis.bind_score_pointer_for_board_navigation(False)
            cuigs.bind_score_pointer_for_board_navigation(True)
            cuigs.bind_score_pointer_for_toggle_game_analysis(True)
            self.takefocus_widget = self.score
            cuigs.takefocus_widget.focus_set()
            cuigs.set_statusbar_text()
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for GameDisplay instance."""
        navigation_map = {
            EventSpec.gamedisplay_to_position_grid[1]:
            self.set_focus_position_grid,
            EventSpec.gamedisplay_to_game_grid[1]:
            self.set_focus_game_grid,
            EventSpec.gamedisplay_to_repertoire_grid[1]:
            self.set_focus_repertoire_grid,
            EventSpec.gamedisplay_to_active_repertoire[1]:
            self.set_focus_repertoirepanel_item_command,
            EventSpec.gamedisplay_to_repertoire_game_grid[1]:
            self.set_focus_repertoire_game_grid,
            EventSpec.gamedisplay_to_partial_grid[1]:
            self.set_focus_partial_grid,
            EventSpec.gamedisplay_to_active_partial[1]:
            self.set_focus_partialpanel_item_command,
            EventSpec.gamedisplay_to_partial_game_grid[1]:
            self.set_focus_partial_game_grid,
            EventSpec.gamedisplay_to_selection_rule_grid[1]:
            self.set_focus_selection_rule_grid,
            EventSpec.gamedisplay_to_active_selection_rule[1]:
            self.set_focus_selectionpanel_item_command,
            EventSpec.tab_traverse_backward[1]:
            self.traverse_backward,
            EventSpec.tab_traverse_forward[1]:
            self.traverse_forward,
            }
        for nm, widget in (
            ({EventSpec.gamedisplay_to_previous_game[1]: self.prior_item,
              EventSpec.gamedisplay_to_next_game[1]: self.next_item,
              EventSpec.gamedisplay_game_to_analysis[1]:
              self.analysis_current_item,
              },
             self),
            ({EventSpec.gamedisplay_analysis_to_game[1]: self.current_item,
              },
             self.analysis)):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)

    def traverse_backward(self, event=None):
        """Give focus to previous widget type in traversal order."""
        self.bind_board_pointer_for_widget_navigation(True)
        self.bind_score_pointer_for_widget_navigation(True)
        self.ui.give_focus_backward(self.ui.game_items)
        return 'break'

    def traverse_forward(self, event=None):
        """Give focus to next widget type in traversal order."""
        self.bind_board_pointer_for_widget_navigation(True)
        self.bind_score_pointer_for_widget_navigation(True)
        self.ui.give_focus_forward(self.ui.game_items)
        return 'break'
        

class DatabaseGameDisplay(GameDisplay, Game, DataNotify):
    
    """Display a chess game from a database allowing delete and insert.

    Game provides the widget and GameDisplay the database interface.
    
    """

    def __init__(self, **ka):
        """Create game display widget and display game from database.

        See superclasses for argument descriptions.

        """
        super(DatabaseGameDisplay, self).__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super(DatabaseGameDisplay, self).bind_off()
        for sequence, function in (
            (EventSpec.databasegamedisplay_insert, ''),
            (EventSpec.databasegamedisplay_delete, ''),
            (EventSpec.databasegamedisplay_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super(DatabaseGameDisplay, self).initialize_bindings()

        # Here because superclass order is GameDisplay Game.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.analysis.inactive_popup = tkinter.Menu(
            master=self.analysis.score, tearoff=False)

        for popup in self.inactive_popup, self.analysis.inactive_popup:
            for function, accelerator in (
                (self.set_focus_panel_item_command,
                 EventSpec.databasegamedisplay_make_active),
                (self.delete_item_view,
                 EventSpec.databasegamedisplay_dismiss_inactive),
                ):
                popup.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, popup),
                    accelerator=accelerator[2])
        self.__bind_on()
        for function, accelerator in (
            (self.delete_item_view,
             EventSpec.databasegamedisplay_dismiss),
            ):
            self.viewmode_popup.add_command(
                label=accelerator[1],
                command=self.try_command(function, self.viewmode_popup),
                accelerator=accelerator[2])
        for function, accelerator in (
            (self.insert_game_database,
             EventSpec.databasegamedisplay_insert),
            (self.delete_game_database,
             EventSpec.databasegamedisplay_delete),
            ):
            self.viewmode_database_popup.add_command(
                label=accelerator[1],
                command=self.try_command(
                    function, self.viewmode_database_popup),
                accelerator=accelerator[2])
        self.bind_toplevel_navigation()

    def bind_on(self):
        """Enable all bindings."""
        super(DatabaseGameDisplay, self).bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Common to bind_on() and initialize_bindings()."""
        for sequence, function in (
            (EventSpec.databasegamedisplay_insert,
             self.insert_game_database),
            (EventSpec.databasegamedisplay_delete,
             self.delete_game_database),
            (EventSpec.databasegamedisplay_dismiss,
             self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def delete_game_database(self, event=None):
        """Remove game from database on request from game display."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Delete Game',
                message='Cannot delete game:\n\nNo database open.')
            return
        datasource = self.ui.base_games.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Delete Game',
                message='Cannot delete game:\n\nGame list hidden.')
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Delete Game',
                message='\n'.join((
                    'Cannot delete game:\n',
                    'Database has been closed since this copy displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Delete Game',
                message='\n'.join((
                    'Cannot delete game:\n',
                    'Record has been amended since this copy displayed.')))
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Delete Game',
            message='Confirm request to delete game from database'):
            return
        original = ChessDBrecordGameUpdate()
        original.load_record(
            (self.sourceobject.key.recno,
             self.sourceobject.srvalue))

        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        #original.value.set_game_source(self.sourceobject.value.gamesource)
        #original.value.set_game_source('Copy, possibly edited')
        if original.value.is_error_comment_present():
            original.value.set_game_source('Editor')

        editor = RecordDelete(original)
        editor.set_data_source(datasource, editor.on_data_change)
        datasource.dbhome.mark_partial_positions_to_be_recalculated()
        editor.delete()
        tags = original.value.collected_game._tags
        dialogues.showinfo(
            title='Delete Game',
            message=''.join(('Game "',
                             '  '.join(
                                 [tags.get(k, '')
                                  for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS]),
                             '" deleted from database.')))


class DatabaseGameInsert(GameDisplay, GameEdit, DataNotify):
    
    """Display a chess game from a database allowing insert.

    GameEdit provides the widget and GameDisplay the database interface.
    
    """

    def __init__(self, **ka):
        """Create game editor widget and display game from database.

        See superclasses for argument descriptions.

        """
        super().__init__(**ka)
        self.initialize_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databasegameedit_insert, ''),
            (EventSpec.databasegameedit_dismiss, ''),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    # This method exists because the bindings cannot be done until all __init__
    # methods in superclasses have been called.
    def initialize_bindings(self):
        """Initialize all bindings."""
        super().initialize_bindings()

        # Here because superclass order is GameDisplay GameEdit.
        self.inactive_popup = tkinter.Menu(master=self.score, tearoff=False)
        self.analysis.inactive_popup = tkinter.Menu(
            master=self.analysis.score, tearoff=False)

        for popup in self.inactive_popup, self.analysis.inactive_popup:
            for function, accelerator in (
                (self.set_focus_panel_item_command,
                 EventSpec.databasegameedit_make_active),
                (self.delete_item_view,
                 EventSpec.databasegameedit_dismiss_inactive),
                ):
                popup.add_command(
                    label=accelerator[1],
                    command=self.try_command(function, popup),
                    accelerator=accelerator[2])
        self.__bind_on()
        display_bindings = (
            (self.delete_item_view,
             EventSpec.databasegameedit_dismiss),
            )
        database_bindings = (
            (self.insert_game_database,
             EventSpec.databasegameedit_insert),
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
        """Common to bind_on() and initialize_bindings()."""
        for sequence, function in (
            (EventSpec.databasegameedit_insert, self.insert_game_database),
            (EventSpec.databasegameedit_dismiss, self.delete_item_view),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)


class DatabaseGameEdit(DatabaseGameInsert):
    
    """Display a chess game from a database allowing edit and insert.

    GameEdit provides the widget and GameDisplay the database interface.
    
    """

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        for sequence, function in (
            (EventSpec.databasegameedit_update, ''),
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
             EventSpec.databasegameedit_update),
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
        """Common to bind_on() and initialize_bindings()."""
        for sequence, function in (
            (EventSpec.databasegameedit_update, self.update_game_database),
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def update_game_database(self, event=None):
        """Modify existing game record."""
        if self.ui.database is None:
            dialogues.showinfo(
                title='Edit Game',
                message='Cannot edit game:\n\nNo database open.')
            return
        datasource = self.ui.base_games.get_data_source()
        if datasource is None:
            dialogues.showinfo(
                title='Edit Game',
                message='Cannot edit game:\n\nGame list hidden.')
            return
        if self.sourceobject is None:
            dialogues.showinfo(
                title='Edit Game',
                message='\n'.join((
                    'Cannot edit game:\n',
                    'Database has been closed since this copy displayed.')))
            return
        if self.blockchange:
            dialogues.showinfo(
                title='Edit Game',
                message='\n'.join((
                    'Cannot edit game:\n',
                    'Record has been amended since this copy displayed.')))
            return
        if tkinter.messagebox.YES != dialogues.askquestion(
            title='Edit Game',
            message='Confirm request to edit game'):
            return
        original = ChessDBrecordGameUpdate()
        original.load_record(
            (self.sourceobject.key.recno,
             self.sourceobject.srvalue))
        
        # currently attracts "AttributeError: 'ChessDBvalueGameTags' has
        # no attribute 'gamesource'.
        #original.value.set_game_source(self.sourceobject.value.gamesource)
        #original.value.set_game_source('Copy, possibly edited')
        if original.value.is_error_comment_present():
            original.value.set_game_source('Editor')

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
                    ('The edited game score contains at least one illegal ',
                     'move in PGN.\n\nPlease re-confirm request to edit game.',
                     ))):
                return
            updater.value.set_game_source('Editor')
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        datasource.dbhome.mark_partial_positions_to_be_recalculated()
        editor.edit()
        if self is self.ui.game_items.active_item:
            newkey = self.ui.game_items.adjust_edited_item(updater)
            if newkey:
                self.ui.set_properties_on_all_game_grids(newkey)
        tags = original.value.collected_game._tags
        dialogues.showinfo(
            title='Edit Game',
            message=''.join(('Game "',
                             '  '.join(
                                 [tags.get(k, '')
                                  for k in STATUS_SEVEN_TAG_ROSTER_PLAYERS]),
                             '" amended on database.')))


class GameDialogue(ChessException):
    
    """Manage UI interaction with database for particular displayed game.

    Subclasses provide the widget to display the game.
    
    """

    binding_labels = tuple(
        [b[1:] for b in (
            EventSpec.gamedialogue_analysis_to_game,
            EventSpec.gamedialogue_game_to_analysis,
            )])

    def initialize_bindings(self):
        """Enable all bindings."""
        self.bind_board_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_board_navigation(True)
        self.bind_score_pointer_for_toggle_game_analysis(True)
        self.bind_toplevel_navigation()
        self.__bind_on()
        
    def bind_toplevel_navigation(self):
        """Set bindings for popup menu for GameDialogue instance."""
        navigation_map = {}
        for nm, widget in (
            ({EventSpec.gamedialogue_game_to_analysis[1]:
              self.analysis_current_item,
              },
             self),
            ({EventSpec.gamedialogue_analysis_to_game[1]:
              self.current_item,
              },
             self.analysis)):
            nm.update(navigation_map)
            widget.add_navigation_to_viewmode_popup(
                bindings=nm, order=self.binding_labels)

    def analysis_current_item(self, event=None):
        """Select current game analysis."""
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
        """Select current game on display."""
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
            (EventSpec.gamedialogue_game_to_analysis,
             self.analysis_current_item,
             self.score),
            (EventSpec.gamedialogue_analysis_to_game,
             self.current_item,
             self.analysis.score),
            ):
            if function:
                function = self.try_event(function)
            widget.bind(sequence[0], function)


class DialogueGameDisplay(Game, GameDialogue):
    
    """Display a chess game from a database allowing delete and insert.
    """

    def __init__(self, **ka):
        """Extend and link game to database."""
        super(DialogueGameDisplay, self).__init__(**ka)
        self.initialize_bindings()
        
    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a game including switching from
        one game to another.
        
        """
        # Score.set_game_list() expects instance to have itemgrid attribute
        # bound to a DataGrid subclass instance, but DialogueGameDisplay
        # instance can live without this being present.
        # It may be more appropriate to override set_game_list to do nothing so
        # there is a way of deleting a game without tracking games containing
        # the same positions.
        try:
            super().set_game_list()
        except AttributeError:
            if self.itemgrid is not None:
                raise


class DialogueGameEdit(GameEdit, GameDialogue):
    
    """Display a chess game from a database allowing edit and insert.
    """

    def __init__(self, **ka):
        """Extend and link game to database."""
        super(DialogueGameEdit, self).__init__(**ka)
        self.initialize_bindings()
        
    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a game including switching from
        one game to another.
        
        """
        # Score.set_game_list() expects instance to have itemgrid attribute
        # bound to a DataGrid subclass instance, but DialogueGameEdit instance
        # can live without this being present.
        # It may be more appropriate to override set_game_list to do nothing so
        # there is a way of editing or inserting a game without tracking games
        # containing the same positions.
        try:
            super().set_game_list()
        except AttributeError:
            if self.itemgrid is not None:
                raise
