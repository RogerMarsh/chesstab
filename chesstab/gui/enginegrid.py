# enginegrid.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for listing details of chess engines enabled for chess database."""

import tkinter
import tkinter.messagebox
from urllib.parse import urlunsplit

from solentware_grid.datagrid import DataGrid

from ..core.chessrecord import ChessDBrecordEngine
from .enginerow import ChessDBrowEngine
from .eventspec import EventSpec
from .display import Display
from ..shared.allgrid import AllGrid


class EngineListGrid(AllGrid, DataGrid, Display):
    """A DataGrid for lists of chess engine definition.

    Subclasses provide navigation and extra methods appropriate to list use.

    """

    def __init__(self, parent):
        """Extend with link to user interface object.

        parent - see superclass

        """
        super().__init__(parent=parent)
        self._configure_frame()

    def set_properties(self, key, dodefaultaction=True):
        """Return True if chess engine definition properties set or False."""
        if super().set_properties(key, dodefaultaction=False):
            return True
        if dodefaultaction:
            self.objects[key].set_background_normal(self.get_row_widgets(key))
            self.set_row_under_pointer_background(key)
            return True
        return False

    def set_row(self, key, dodefaultaction=True, **kargs):
        """Return row widget for chess engine definition key or None."""
        row = super().set_row(key, dodefaultaction=False, **kargs)
        if row is not None:
            return row
        if key not in self.keys:
            return None
        if dodefaultaction:
            return self.objects[key].grid_row_normal(**kargs)
        return None

    def launch_delete_record(self, key, modal=True):
        """Create delete dialogue."""
        oldobject = ChessDBrecordEngine()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_delete_dialog(
            self.objects[key],
            oldobject,
            modal,
            title="Delete Engine Definition",
        )

    def launch_edit_record(self, key, modal=True):
        """Create edit dialogue."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordEngine(),
            ChessDBrecordEngine(),
            False,
            modal,
            title="Edit Engine Definition",
        )

    def launch_edit_show_record(self, key, modal=True):
        """Create edit dialogue including reference copy of original."""
        self.create_edit_dialog(
            self.objects[key],
            ChessDBrecordEngine(),
            ChessDBrecordEngine(),
            True,
            modal,
            title="Edit Engine Definition",
        )

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
            title="New Engine Definition",
        )

    def launch_show_record(self, key, modal=True):
        """Create show dialogue."""
        oldobject = ChessDBrecordEngine()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
        self.create_show_dialog(
            self.objects[key], oldobject, modal, title="Show Engine Definition"
        )

    def _fill_view_from_top_hack(self):
        # Hack to display newly inserted record.
        # Acceptable because there will likely be two or three records at
        # most in the engine grid.
        self.fill_view_from_top()

    def set_focus(self):
        """Give focus to this widget."""
        self.frame.focus_set()

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
    """Customized EngineListGrid for list of enabled chess engines."""

    def __init__(self, ui):
        """Extend with definition and bindings for selection rules on grid.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.show_engines_toplevel)
        self.ui = ui
        self.make_header(ChessDBrowEngine.header_specification)
        self.__bind_on()
        for accelerator, function in (
            (EventSpec.engine_grid_run, self.run_engine),
        ):
            self.menupopup.insert_command(
                0,
                label=accelerator[1],
                command=self.try_command(function, self.menupopup),
                accelerator=accelerator[2],
            )

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self._set_event_bindings_frame(((EventSpec.engine_grid_run, ""),))

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self._set_event_bindings_frame(
            ((EventSpec.engine_grid_run, self.run_engine),)
        )

    def on_partial_change(self, instance):
        """Delegate to superclass if database is open otherwise do nothing."""
        # may turn out to be just to catch datasource is None
        if self.get_data_source() is None:
            return
        super().on_data_change(instance)

    def set_selection_text(self):
        """Set status bar to display selection rule name."""

    @staticmethod
    def is_visible():
        """Return True if list of selection rules is displayed."""
        # return str(self.get_frame()) in self.ui.selection_rules_pw.panes()
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
            tkinter.messagebox.showinfo(
                parent=self.parent,
                title="Insert Engine Definition Workaround",
                message="".join(
                    (
                        "All records have same name on this display.\n\nThe ",
                        "new record has been inserted but you need to Hide, ",
                        "and then Show, the display to see the record in ",
                        "the list.",
                    )
                ),
            )

    def run_engine(self, event=None):
        """Run chess engine."""
        del event
        self._launch_chess_engine(self.pointer_popup_selection)
        # self.move_selection_to_popup_selection()

    def _launch_chess_engine(self, key, modal=True):
        """Launch a chess engine."""
        del modal
        oldobject = ChessDBrecordEngine()
        oldobject.load_record(
            (self.objects[key].key.pack(), self.objects[key].srvalue)
        )
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
        # if self.ui.uci.uci_drivers_reply is None:
        #    tkinter.messagebox.showinfo(
        #        parent=self.parent,
        #        title='Chesstab Restriction',
        #        message=' '.join(
        #            ('Starting an UCI chess engine is not allowed because',
        #             'an interface cannot be created:',
        #             'this is expected if running under Wine.')))
        #    return

        url = definition.engine_url_or_error_message()
        if isinstance(url, str):
            tkinter.messagebox.showerror(
                parent=self.parent, title="Run Engine", message=url
            )
            return
        if url.query:
            self.ui.run_engine(urlunsplit(url))
        elif url.path:
            command = url.path.split(" ", 1)
            if len(command) == 1:
                self.ui.run_engine(command[0])
            else:
                self.ui.run_engine(command[0], args=command[1].strip())
        else:
            tkinter.messagebox.showerror(
                parent=self.parent,
                title="Run Engine",
                message="".join(
                    (
                        "Unable to run engine for\n\n",
                        definition.get_engine_command_text(),
                    )
                ),
            )
