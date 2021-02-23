# enginegrid.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of chess engines enabled for chess database.
"""

import tkinter
from urllib.parse import urlsplit, parse_qs

from solentware_misc.workarounds import dialogues

from solentware_grid.datagrid import DataGrid

from ..core.chessrecord import ChessDBrecordEngine
from .enginerow import ChessDBrowEngine
from .chessexception import ChessException
from .eventspec import EventSpec, DummyEvent
from .display import Display


class EngineListGrid(ChessException, DataGrid, Display):

    """A DataGrid for lists of chess engine definition.

    Subclasses provide navigation and extra methods appropriate to list use.

    """

    def __init__(self, parent):
        '''Extend with link to user interface object.

        parent - see superclass

        '''
        super(EngineListGrid, self).__init__(parent=parent)
        self.gcanvas.configure(takefocus=tkinter.FALSE)
        self.data.configure(takefocus=tkinter.FALSE)
        self.frame.configure(takefocus=tkinter.FALSE)
        self.hsbar.configure(takefocus=tkinter.FALSE)
        self.vsbar.configure(takefocus=tkinter.FALSE)
        
    def set_properties(self, key, dodefaultaction=True):
        """Return True if chess engine definition properties set or False."""
        if super(EngineListGrid, self).set_properties(
            key, dodefaultaction=False):
            return True
        if dodefaultaction:
            self.objects[key].set_background_normal(self.get_row_widgets(key))
            self.set_row_under_pointer_background(key)
            return True
        return False

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for chess engine definition key or None."""
        row = super(EngineListGrid, self).set_row(
            key, dodefaultaction=False, **kargs)
        if row is not None:
            return row
        if key not in self.keys:
            return None
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        else:
            return None

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordEngine()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue))
        self.create_delete_dialog(
            self.objects[key],
            oldobject,
            modal,
            title='Delete Engine Definition')

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordEngine(),
            ChessDBrecordEngine(),
            False,
            modal,
            title='Edit Engine Definition')

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordEngine(),
            ChessDBrecordEngine(),
            True,
            modal,
            title='Edit Engine Definition')

    def launch_insert_new_record(self, modal=True):
        """Create insert dialogue."""
        newobject = ChessDBrecordEngine()
        instance = self.datasource.new_row()
        instance.srvalue = instance.value.pack_value()
        self.create_edit_dialog(
            instance,
            newobject,
            None,
            False,
            modal,
            title='New Engine Definition')

    def launch_show_record(self, key, modal=True):
        """Create show dialogue."""
        oldobject = ChessDBrecordEngine()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue))
        self.create_show_dialog(
            self.objects[key],
            oldobject,
            modal,
            title='Show Engine Definition')
        
    def create_edit_dialog(
        self, instance, newobject, oldobject, showinitial, modal, title=''):
        """Extend to do chess initialization"""
        for x in (newobject, oldobject):
            if x:
                x.load_record((instance.key.pack(), instance.srvalue))
        super(EngineListGrid, self).create_edit_dialog(
            instance, newobject, oldobject, showinitial, modal, title=title)

    def fill_view(
        self,
        currentkey=None,
        down=True,
        topstart=True,
        exclude=True,
        ):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.
        
        if self.get_database() is not None:
            super(EngineListGrid, self).fill_view(
                currentkey=currentkey,
                down=down,
                topstart=topstart,
                exclude=exclude,
                )

    def load_new_index(self):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.
        
        if self.get_database() is not None:
            super(EngineListGrid, self).load_new_index()

    def load_new_partial_key(self, key):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.
        
        if self.get_database() is not None:
            super(EngineListGrid, self).load_new_partial_key(key)

    def on_configure_canvas(self, event=None):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.
        
        if self.get_database() is not None:
            super(EngineListGrid, self).on_configure_canvas(event=event)

    def on_data_change(self, instance):
        """Delegate to superclass if database is open otherwise do nothing."""

        # Intend to put this in superclass but must treat the DataClient objects
        # being scrolled as a database to do this properly.  Do this when these
        # objects have been given a database interface used when the database
        # is not open.  (One problem is how to deal with indexes.)

        # Used to deal with temporary closure of database to do Imports of games
        # from PGN files; which can take many hours.
        
        if self.get_database() is not None:
            super(EngineListGrid, self).on_data_change(instance)

            # Hack to display newly inserted record.
            # Acceptable because there will likely be two or three records at
            # most in the engine grid.
            self.fill_view_from_top()

    def set_focus(self):
        """Give focus to this widget."""
        self.frame.focus_set()

    def is_payload_available(self):
        """Return True if grid is connected to a database."""
        ds = self.get_data_source()
        if ds is None:
            return False
        if ds.get_database() is None:

            # Avoid exception scrolling visible grid not connected to database.
            # Make still just be hack to cope with user interface activity
            # while importing data.
            self.clear_grid_keys()

            return False
        return True

    def bind_for_widget_without_focus(self):
        """Return True if this item has the focus about to be lost."""
        if self.get_frame().focus_displayof() != self.get_frame():
            return False

        # Nothing to do on losing focus.
        return True
        
    def get_top_widget(self):
        """Return topmost widget for game display.

        The topmost widget is put in a container widget in some way

        """
        # Superclass DataGrid.get_frame() method returns the relevant widget.
        # Name, get_top_widget, is compatible with Game and Partial names.
        return self.get_frame()
        

class EngineGrid(EngineListGrid):

    """Customized EngineListGrid for list of enabled chess engines.
    """

    def __init__(self, ui):
        '''Extend with definition and bindings for selection rules on grid.

        ui - container for user interface widgets and methods.

        '''
        super(EngineGrid, self).__init__(ui.show_engines_toplevel)
        self.ui = ui
        self.make_header(ChessDBrowEngine.header_specification)
        self.__bind_on()
        for function, accelerator in (
            (self.run_engine,
             EventSpec.engine_grid_run),
            ):
            self.menupopup.insert_command(
                0,
                label=accelerator[1],
                command=self.try_command(function, self.menupopup),
                accelerator=accelerator[2])

    def bind_off(self):
        """Disable all bindings."""
        super(EngineGrid, self).bind_off()
        for function, accelerator in (
            ('',
             EventSpec.engine_grid_run),
            ):
            if function:
                function = self.try_event(function)
            self.frame.bind(accelerator[0], function)

    def bind_on(self):
        """Enable all bindings."""
        super(EngineGrid, self).bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        for function, accelerator in (
            (self.run_engine,
             EventSpec.engine_grid_run),
            ):
            if function:
                function = self.try_event(function)
            self.frame.bind(accelerator[0], function)
        
    def on_partial_change(self, instance):
        """Delegate to superclass if database is open otherwise do nothing."""

        # may turn out to be just to catch datasource is None
        if self.get_data_source() is None:
            return
        super(EngineGrid, self).on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display selection rule name."""

    def is_visible(self):
        """Return True if list of selection rules is displayed."""
        #return str(self.get_frame()) in self.ui.selection_rules_pw.panes()
        return True

    def set_selection(self, key):
        """Hack to fix edge case when inserting records using apsw or sqlite3.
        
        Workaround a KeyError exception when a record is inserted while a grid
        keyed by a secondary index with only one key value in the index is on
        display.
        
        """
        try:
            super().set_selection(key)
        except KeyError:
            dialogues.showinfo(
                title='Insert Engine Definition Workaround',
                message=''.join(
                    ('All records have same name on this display.\n\nThe new ',
                     'record has been inserted but you need to Hide, and then ',
                     'Show, the display to see the record in the list.',
                     )))

    def run_engine(self, event=None):
        """Run chess engine."""
        self.launch_chess_engine(self.pointer_popup_selection)
        #self.move_selection_to_popup_selection()

    def launch_chess_engine(self, key, modal=True):
        """Launch a chess engine."""
        oldobject = ChessDBrecordEngine()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue))
        definition = oldobject.value

        # Avoid "OSError: [WinError 535] Pipe connected"  at Python3.3 running
        # under Wine on FreeBSD 10.1 by disabling the UCI functions.
        # Assume all later Pythons are affected because they do not install
        # under Wine at time of writing.
        # The OSError stopped happening by wine-2.0_3,1 on FreeBSD 10.1 but
        # get_nowait() fails to 'not wait', so ChessTab never gets going under
        # wine at present.  Leave alone because it looks like the problem is
        # being shifted constructively.
        # At Python3.5 running under Wine on FreeBSD 10.1, get() does not wait
        # when the queue is empty either, and ChessTab does not run under
        # Python3.3 because it uses asyncio: so no point in disabling.
        #if self.ui.uci.uci_drivers_reply is None:
        #    dialogues.showinfo(
        #        'Chesstab Restriction',
        #        ' '.join(('Starting an UCI chess engine is not allowed because',
        #                  'an interface cannot be created:',
        #                  'this is expected if running under Wine.')))
        #    return

        url = urlsplit(definition.get_engine_command_text())
        try:
            url.port
        except ValueError as exc:
            dialogues.showerror(
                title='Run Engine',
                message=''.join(('The port in the chess engine definition is ',
                                 'invalid.\n\n',
                                 'The reported error for the port is:\n\n',
                                 str(exc),
                                 )))
            return
        if not definition.get_engine_command_text():
            dialogues.showinfo(
                title='Run Engine',
                message=''.join((
                    'The engine definition does not have a command to ',
                    'run chess engine.',
                    )))
            return
        elif not (url.port or url.hostname):
            if not definition.is_run_engine_command():
                dialogues.showinfo(
                    title='Run Engine',
                    message=''.join((
                        'The engine definition command to run a chess engine ',
                        'does not name a file.',
                        )))
                return
        if url.hostname or url.port:
            if url.path and url.query:
                dialogues.showerror(
                    title='Run Engine',
                    message=''.join(
                        ('Engine must be query with hostname or port.\n\n',
                         "Path is: '", url.path, "'.\n\n",
                         "Query is: '", url.query, "'.\n",
                         )))
                return
            elif url.path:
                dialogues.showerror(
                    title='Run Engine',
                    message=''.join(
                        ('Engine must be query with hostname or port.\n\n',
                         "Path is: '", url.path, "'.\n",
                         )))
                return
            elif not url.query:
                dialogues.showerror(
                    title='Run Engine',
                    message='Engine must be query with hostname or port.\n\n')
                return
            else:
                try:
                    query = parse_qs(url.query, strict_parsing=True)
                except ValueError as exc:
                    dialogues.showerror(
                        title='Run Engine',
                        message=''.join(
                            ("Problem in chess engine specification.  ",
                             "The reported error is:\n\n'",
                             str(exc), "'.\n",
                             )))
                    return
                if len(query) > 1:
                    dialogues.showerror(
                        title='Run Engine',
                        message=''.join(
                            ("Engine must be single 'key=value' or ",
                             "'value'.\n\n",
                             "Query is: '", url.query, "'.\n",
                             )))
                    return
                elif len(query) == 1:
                    for k, v in query.items():
                        if k != 'name':
                            dialogues.showerror(
                                title='Run Engine',
                                message=''.join(
                                    ("Engine must be single 'key=value' or ",
                                     "'value'.\n\n",
                                     "Query is: '", url.query, "'\n\nand use ",
                                     "'name' as key.\n",
                                     )))
                            return
                        elif len(v) > 1:
                            dialogues.showerror(
                                title='Run Engine',
                                message=''.join(
                                    ("Engine must be single 'key=value' or ",
                                     "'value'.\n\n",
                                     "Query is: '", url.query, "' with more ",
                                     "than one 'value'\n",
                                     )))
                            return
        elif url.path and url.query:
            dialogues.showerror(
                title='Run Engine',
                message=''.join(
                    ('Engine must be path without hostname or port.\n\n',
                     "Path is: '", url.path, "'.\n\n",
                     "Query is: '", url.query, "'.\n",
                     )))
            return
        elif url.query:
            dialogues.showerror(
                title='Run Engine',
                message=''.join(
                    ('Engine must be path without hostname or port.\n\n',
                     "Query is: '", url.query, "'.\n",
                     )))
            return
        elif not url.path:
            dialogues.showerror(
                title='Run Engine',
                message='Engine must be path without hostname or port.\n')
            return
        self.ui.run_engine(definition.get_engine_command_text())
