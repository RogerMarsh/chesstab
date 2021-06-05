# uci.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Control multiple UCI compliant chess engines."""

import tkinter
import tkinter.messagebox
import tkinter.filedialog

from solentware_grid.core.dataclient import DataSource

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from uci_net.engine import (
    ReservedOptionNames,
)

from ..core.uci import UCI as _UCI
from .enginegrid import EngineGrid
from .enginerow import make_ChessDBrowEngine
from ..core.filespec import (
    ENGINE_FILE_DEF,
    COMMAND_FIELD_DEF,
)
from .eventspec import EventSpec

import sys

_win32_platform = sys.platform == "win32"
_freebsd_platform = sys.platform.startswith("freebsd")
del sys


class UCI(ExceptionHandler):
    def __init__(self, menu_engines, menu_commands):

        self._do_toplevel = None
        self._show_engines_toplevel = None
        self.database = None
        self.base_engines = None
        self.visible_scrollbars = True

        # The chess engine definition widgets in their own Toplevel.
        # Should these be helper class responsibility as well?
        # Similar construct in .chess_ui.ChessUI too.
        self.engines_in_toplevels = set()

        self.menu_engines = menu_engines
        self.menu_commands = menu_commands

        menu_engines.add_separator()
        for accelerator, function in (
            (
                EventSpec.menu_engines_position_queues,
                self.position_queue_status,
            ),
            (EventSpec.menu_engines_show_engines, self.show_engines),
            (EventSpec.menu_engines_start_engine, self.start_engine),
            (EventSpec.menu_engines_quit_all_engines, self.quit_all_engines),
        ):
            menu_engines.add_command(
                label=accelerator[1],
                command=self.try_command(function, menu_engines),
                underline=accelerator[3],
            )
        menu_engines.add_separator()
        menu_engines.add_separator()

        menu_commands.add_separator()
        for accelerator, function in (
            (EventSpec.menu_commands_multipv, self.set_multipv),
            (EventSpec.menu_commands_depth, self.set_depth),
            (EventSpec.menu_commands_hash, self.set_hash),
        ):
            menu_commands.add_command(
                label=accelerator[1],
                command=self.try_command(function, menu_commands),
                underline=accelerator[3],
            )
        menu_commands.add_separator()

        # Must do both these commands between each move to get consistent
        # analysis between runs of ChessTab given that positions are evaluated
        # in random order.
        # menu_commands.add_command(
        #    label='Ucinewgame off',
        #    underline=0,
        #    command=self.try_command(self.set_ucinewgame_off, menu_commands))
        # menu_commands.add_command(
        #    label='Clear Hash off',
        #    underline=0,
        #    command=self.try_command(
        #        self.set_clear_hash_off, menu_commands))
        # menu_commands.add_separator()

        # Not implemented at present.
        # And possibly never will be.
        # menu_commands.add_command(
        #    label='Go infinite',
        #    underline=3,
        #    command=self.try_command(self.go_infinite, menu_commands))
        # menu_commands.add_command(
        #    label='Stop',
        #    underline=0,
        #    command=self.try_command(self.stop, menu_commands))
        # menu_commands.add_separator()
        # menu_commands.add_command(
        #    label='Isready',
        #    underline=2,
        #    command=self.try_command(self.isready, menu_commands))
        # menu_commands.add_separator()

        self.uci = _UCI()

    @property
    def show_engines_toplevel(self):
        """ """
        return self._show_engines_toplevel

    def remove_engines_and_menu_entries(self):
        """Quit all started UCI compliant Chess Engines."""
        ui_names = set(self.uci.uci_drivers)
        still_alive = self.uci.quit_all_engines()
        ui_names -= set([n for n, p in still_alive])
        dead_menu_items = []
        for i in range(self.menu_engines.index("end") + 1):
            label = self.menu_engines.entryconfigure(i).get("label")
            if label is not None:
                if label[-1] in ui_names:
                    dead_menu_items.insert(0, i)
        for dmi in dead_menu_items:
            self.menu_engines.delete(dmi)
        for name, pid in still_alive:
            tkinter.messagebox.showinfo(
                parent=self.menu_commands,
                title="Stop Engine",
                message="".join(
                    (
                        name,
                        " failed to stop.\n\nYou may have to kill",
                        " process id ",
                        str(pid),
                        " manually.",
                    )
                ),
            )

    def quit_all_engines(self):
        """Quit all started UCI compliant Chess Engines after confirmation."""
        if (
            tkinter.messagebox.askquestion(
                parent=self.menu_commands,
                title="Engines",
                message="Confirm Quit All Engines.",
            )
            == tkinter.messagebox.YES
        ):
            self.remove_engines_and_menu_entries()

    def start_engine(self):
        """Start an UCI compliant Chess Engine."""

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
        # if self.uci.uci_drivers_reply is None:
        #    tkinter.messagebox.showinfo(
        #        parent=self.menu_commands,
        #        title='Chesstab Restriction',
        #        message=' '.join(
        #            ('Starting an UCI chess engine is not allowed because',
        #             'an interface cannot be created:',
        #             'this is expected if running under Wine.')))
        #    return

        if _win32_platform:
            filetypes = (("Chess Engines", "*.exe"),)
        else:
            filetypes = ()
        filename = tkinter.filedialog.askopenfilename(
            parent=self.menu_commands,
            title="Run Chess Engine",
            filetypes=filetypes,
            initialfile="",
            initialdir="~",
        )
        if not filename:
            return

        def get(event):
            command = self._contents.get()
            if command == filename:
                self.run_engine(filename)
            elif not command.startswith(filename):
                tkinter.messagebox.showinfo(
                    parent=self._do_toplevel,
                    title="Start Engine",
                    message="Command must start with selected file name.",
                )
            else:
                command = command.replace(filename, "", 1)
                if not command.startswith(" "):
                    tkinter.messagebox.showinfo(
                        parent=self._do_toplevel,
                        title="Start Engine",
                        message="Command must start with selected file name.",
                    )
                else:
                    self.run_engine(filename, args=command.strip())
            self._cancel()

        self.do_command(
            filename,
            get,
            hint="".join(
                (
                    "\nConsult chess engine's documentation for any arguments ",
                    "which must be appended to the command.\n\nPress enter to ",
                    "run engine.\n",
                )
            ),
        )

    def _cancel(self):
        self._do_toplevel.destroy()
        self._do_toplevel = None
        del self._contents

    def do_command(self, initial_value, callback, hint=None, wraplength=None):

        if self._do_toplevel is not None:
            tkinter.messagebox.showinfo(
                parent=self.menu_commands,
                title="Engine Command",
                message="".join(
                    (
                        "A command dialogue is already active:\n\n",
                        "Cannot start another one.",
                    )
                ),
            )
            return
        self._command = initial_value.split(None, maxsplit=1)[0]
        self._do_toplevel = tkinter.Toplevel(
            master=self.menu_engines.winfo_toplevel()
        )
        if hint:
            if wraplength is None:
                wraplength = 400
            tkinter.Label(
                master=self._do_toplevel,
                text=hint,
                wraplength=wraplength,
                justify=tkinter.LEFT,
            ).pack()
        entrythingy = tkinter.Entry(self._do_toplevel)
        entrythingy.pack(fill=tkinter.BOTH)
        buttonbar = tkinter.Frame(master=self._do_toplevel)
        buttonbar.pack(fill=tkinter.X, expand=tkinter.TRUE)
        cancel = tkinter.Button(
            master=buttonbar,
            text="Cancel",
            underline=0,
            command=self.try_command(self._cancel, buttonbar),
        )
        cancel.pack(expand=tkinter.TRUE, side=tkinter.LEFT)
        self._contents = tkinter.StringVar()
        self._contents.set(initial_value)
        entrythingy["textvariable"] = self._contents
        entrythingy.bind("<Key-Return>", callback)
        entrythingy.focus_set()

    def run_engine(self, program_file_name, args=None):

        self.uci.run_engine(program_file_name, args)
        self.menu_engines.insert_command(
            self.menu_engines.index("end"),
            label=self.uci.uci_drivers_index[self.uci.engine_counter],
            command=self.make_quit_engine_command(self.uci.engine_counter),
        )

    def make_quit_engine_command(self, counter):
        def quit_engine_command():
            self.quit_engine(counter)

        return quit_engine_command

    def quit_engine(self, number):

        ui_name = self.uci.uci_drivers_index[number]
        for i in range(self.menu_engines.index("end")):
            label = self.menu_engines.entryconfigure(i).get("label")
            if label is not None:
                if label[-1] == ui_name:
                    if (
                        tkinter.messagebox.askquestion(
                            parent=self.menu_engines,
                            title="Quit Engine",
                            message="".join(
                                (
                                    "Please confirm request to quit engine\n\n",
                                    ui_name,
                                )
                            ),
                        )
                        != tkinter.messagebox.YES
                    ):
                        continue
                    if self.uci.kill_engine(number):
                        self.menu_engines.delete(i)
                    else:
                        tkinter.messagebox.showinfo(
                            parent=self.menu_engines,
                            title="Quit Engine",
                            message="".join(
                                (
                                    ui_name,
                                    " failed to quit.\n\nYou may have to kill",
                                    " process id ",
                                    str(
                                        self.uci.uci_drivers[
                                            ui_name
                                        ].driver.pid
                                    ),
                                    " manually.",
                                )
                            ),
                        )

    def send_to_all_engines(self, event):

        command = self._contents.get()
        if command.split()[0] != self._command:
            if (
                tkinter.messagebox.askquestion(
                    parent=self.menu_commands,
                    title="Send to Engine",
                    message="".join(
                        (
                            "Command is not the one used to start dialogue.\n\n",
                            "Do you want to cancel dialogue?",
                        )
                    ),
                )
                == tkinter.messagebox.YES
            ):
                del self._command
                del self._contents
                self._do_toplevel.destroy()
                self._do_toplevel = None
            return
        for ui_name, ei in self.uci.uci_drivers.items():
            try:
                ei.to_driver_queue.put(command)
            except:
                tkinter.messagebox.showinfo(
                    parent=self.menu_commands,
                    title="Send to Engine",
                    message="".join(
                        (
                            "Send command\n\n",
                            command,
                            "\n\nto\n\n",
                            ui_name,
                            "\n\nfailed.",
                        )
                    ),
                )
        del self._command
        del self._contents
        self._do_toplevel.destroy()
        self._do_toplevel = None

    def set_hash(self):
        """Set value of Hash option to use on UCI compliant Chess Engine."""

        def get(event):
            self.uci.hash_size = self._contents.get()
            self.uci.set_option_on_empty_queues.add(ReservedOptionNames.Hash)
            self._do_toplevel.destroy()
            self._do_toplevel = None
            del self._spinbox

        self.do_spinbox(
            self.uci.hash_size,
            0,
            1000,
            get,
            hint="".join(
                (
                    "\nSet the size of hash tables, in mega-bytes, within ",
                    "limits allowed by chess engines.\n\n0 (zero) means use ",
                    "the default assumed by a chess engine.\n\nPress enter to ",
                    "set value.\n",
                )
            ),
        )

    def set_multipv(self):
        """Set value of MultiPV option to use on UCI compliant Chess Engine."""

        def get(event):
            self.uci.multipv = self._contents.get()
            self._do_toplevel.destroy()
            self._do_toplevel = None
            del self._spinbox

        self.do_spinbox(
            self.uci.multipv,
            0,
            100,
            get,
            hint="".join(
                (
                    "\nSet the number of variations returned by chess engines ",
                    "which support the MultiPV option.\n\n0 (zero) means use ",
                    "the default assumed by a chess engine.\n\nPress enter to ",
                    "set value.\n",
                )
            ),
        )

    def set_depth(self):
        """Set depth to use in go commands to UCI compliant Chess Engine."""

        def get(event):
            self.uci.go_depth = self._contents.get()
            self._do_toplevel.destroy()
            self._do_toplevel = None
            del self._spinbox

        self.do_spinbox(
            self.uci.go_depth,
            0,
            200,
            get,
            hint="".join(
                (
                    "\nSet the length of variations, in half-moves, returned ",
                    "by chess engines.\n\nPress enter to set value.\n",
                )
            ),
        )

    def _modify_command_menu_item(self, old, new, command):
        for i in range(self.menu_commands.index("end")):
            label = self.menu_commands.entryconfigure(i).get("label")
            if label is not None:
                if label[-1] == old:
                    self.menu_commands.entryconfigure(
                        i,
                        label=new,
                        command=self.try_command(command, self.menu_commands),
                    )

    def set_ucinewgame_off(self):
        """Set to not use ucinewgame command when navigating games."""
        if (
            tkinter.messagebox.askquestion(
                parent=self.menu_commands,
                title="Ucinewgame OFF",
                message="".join(
                    (
                        "Turn use of ucinewgame command OFF when navigating in or ",
                        "between game scores?\n\n",
                        "Consult engine documentation for implications of using, ",
                        "or not using, the ucinewgame command.\n\n",
                        "UCI specification states new GUIs should support ucinewgame ",
                        "command, and engines should not expect ucinewgame commands ",
                        "if the ucinewgame command is not used before the first ",
                        "position command. (August 2015)",
                    )
                ),
            )
            == tkinter.messagebox.YES
        ):
            self.uci.use_ucinewgame = False
            self._modify_command_menu_item(
                "Ucinewgame off", "Ucinewgame on", self.set_ucinewgame_on
            )

    def set_ucinewgame_on(self):
        """Set to use ucinewgame command when navigating games."""
        if (
            tkinter.messagebox.askquestion(
                parent=self.menu_commands,
                title="Ucinewgame ON",
                message="".join(
                    (
                        "Turn use of ucinewgame command ON when navigating in or ",
                        "between game scores?\n\n",
                        "Consult engine documentation for implications of using, ",
                        "or not using, the ucinewgame command.\n\n",
                        "UCI specification states new GUIs should support ucinewgame ",
                        "command, and engines should not expect ucinewgame commands ",
                        "if the ucinewgame command is not used before the first ",
                        "position command. (August 2015)",
                    )
                ),
            )
            == tkinter.messagebox.YES
        ):
            self.uci.use_ucinewgame = True
            self._modify_command_menu_item(
                "Ucinewgame on", "Ucinewgame off", self.set_ucinewgame_off
            )

    def stop(self):
        """Send stop command to UCI compliant Chess Engines."""

        tkinter.messagebox.showinfo(
            parent=self.menu_commands,
            title="Stop Command",
            message="Stop not implemented.",
        )

    def go_infinite(self):
        """Send go infinite command to UCI compliant Chess Engines."""

        tkinter.messagebox.showinfo(
            parent=self.menu_commands,
            title="Go Infinite Command",
            message="Go infinite not implemented.",
        )

    def isready(self):
        """Send isready command to UCI compliant Chess Engines."""

        tkinter.messagebox.showinfo(
            parent=self.menu_commands,
            title="Isready Command",
            message="Isready not implemented.",
        )

    def do_spinbox(
        self, initial_value, from_, to, callback, hint=None, wraplength=None
    ):

        # Comapare with show_engines() method.
        # The after() technique used in show_engines does not help here to
        # guarantee display of the new Toplevel on second and subsequent use.
        # But the problem is seen only when the X server is on a different box
        # than the ChessTab process.

        if self._do_toplevel is not None:
            tkinter.messagebox.showinfo(
                parent=self.menu_commands,
                title="Engine Command",
                message="".join(
                    (
                        "A command dialogue is already active:\n\n",
                        "Cannot start another one.",
                    )
                ),
            )
            return

        def cancel():
            self._do_toplevel.destroy()
            self._do_toplevel = None
            del self._spinbox

        def destroy(event=None):
            self._do_toplevel = None

        self._spinbox = initial_value
        self._do_toplevel = tkinter.Toplevel(
            master=self.menu_engines.winfo_toplevel()
        )
        self._do_toplevel.bind("<Destroy>", destroy)
        if hint:
            if wraplength is None:
                wraplength = 400
            tkinter.Label(
                master=self._do_toplevel,
                text=hint,
                wraplength=wraplength,
                justify=tkinter.LEFT,
            ).pack()
        entrythingy = tkinter.Spinbox(self._do_toplevel)
        entrythingy.pack(fill=tkinter.BOTH)
        buttonbar = tkinter.Frame(master=self._do_toplevel)
        buttonbar.pack(fill=tkinter.X, expand=tkinter.TRUE)
        tkinter.Button(
            master=buttonbar,
            text="Cancel",
            underline=0,
            command=self.try_command(cancel, buttonbar),
        ).pack(expand=tkinter.TRUE, side=tkinter.LEFT)
        entrythingy.configure(from_=from_, to=to, increment=1)
        self._contents = tkinter.IntVar()
        self._contents.set(initial_value)
        entrythingy["textvariable"] = self._contents
        entrythingy.bind("<Key-Return>", callback)
        entrythingy.focus_set()

    def show_engines(self):
        """Show Chess Engine Descriptions on database."""
        if self._show_engines_toplevel is not None:
            tkinter.messagebox.showinfo(
                parent=self.menu_engines,
                title="Show Engines",
                message="".join(
                    (
                        "A show engines dialogue is already active:\n\n",
                        "Cannot start another one.",
                    )
                ),
            )
            return

        def destroy(event=None):
            if self._show_engines_toplevel is not None:
                self._close_engine_grid()
            self._show_engines_toplevel = None

        self._show_engines_toplevel = tkinter.Toplevel(
            master=self.menu_engines.winfo_toplevel()
        )
        self._show_engines_toplevel.wm_title("Chess Engines")
        self._show_engines_toplevel.bind("<Destroy>", destroy)
        self._close_engine_grid()

        # The after_idle version makes it less common for the Toplevel to not
        # become visible until 'click on menubar' or 'move pointer out of
        # application window' on 'destroy or close' toplevel and 'show engine'
        # action sequences.
        # The after version gives a noticably slower response when the X server
        # is on a different machine, but has not yet needed the pointer prompt
        # to display the new toplevel.
        # The problem has not been seen yet on Microsoft Windows XP.
        # The problem happens rarely when the X server is on the same machine.
        # The problem had never been seen before in the toplevels started from
        # the other subclasses of DataGrid: but on looking it can be seen now.
        # self._open_engine_grid()
        # self._show_engines_toplevel.after_idle(self.try_command(
        #    self._open_engine_grid, self._show_engines_toplevel))
        self._show_engines_toplevel.after(
            1,
            self.try_command(
                self._open_engine_grid, self._show_engines_toplevel
            ),
        )

    def set_open_database_and_engine_classes(self, database=None):
        """Set current open database and engine specific dataset classes."""
        if self.database is not database:
            self._close_engine_grid()
            self.database = database
            self._open_engine_grid()

    def _close_engine_grid(self):
        """Close the existing EngineGrid instance."""
        if self.base_engines is not None:
            self.base_engines.get_top_widget().pack_forget()
            self.base_engines.set_data_source()
            self.base_engines = None

    def _open_engine_grid(self):
        """Open and show an EngineGrid instance."""
        if self._show_engines_toplevel is None:
            return
        if self.base_engines is None and self.database is not None:
            self.base_engines = EngineGrid(self)
            self.base_engines.set_data_source(
                DataSource(
                    self.database,
                    ENGINE_FILE_DEF,
                    COMMAND_FIELD_DEF,
                    make_ChessDBrowEngine(self),
                ),
                self.base_engines.on_data_change,
            )
            self.base_engines.set_focus()
            self.base_engines.get_top_widget().pack(
                fill=tkinter.BOTH, expand=tkinter.TRUE
            )

    def show_scrollbars(self):
        """Show the scrollbars in the engine definition display widgets."""
        self.visible_scrollbars = True
        exceptions = []
        for items in (self.engines_in_toplevels,):
            for i in items:
                try:
                    i.show_scrollbars()
                except tkinter.TclError:
                    exceptions.append(i, items)
        for i, items in exceptions:
            items.remove(i)

    def hide_scrollbars(self):
        """Show the scrollbars in the engine definition display widgets."""
        self.visible_scrollbars = False
        exceptions = []
        for items in (self.engines_in_toplevels,):
            for i in items:
                try:
                    i.hide_scrollbars()
                except tkinter.TclError:
                    exceptions.append((i, items))
        for i, items in exceptions:
            items.remove(i)

    def position_queue_status(self):
        """Display counts of position queued for analysis by engines."""
        pending_counts = []
        for engine, pending in self.uci.positions_pending.items():
            pending_counts.append(
                (engine, sum([len(p) for p in pending.values()]))
            )
        if not pending_counts:
            tkinter.messagebox.showinfo(
                parent=self.menu_commands,
                title="Position Queues",
                message="There are no queues of positions for analysis.",
            )
            return
        pce = []
        for e, pc in sorted(pending_counts):
            pce.append("\t".join((str(pc), e)))
        tkinter.messagebox.showinfo(
            parent=self.menu_commands,
            title="Position Queues",
            message="".join(
                (
                    "Number of positions queued for analysis by ",
                    "each engine are:\n\n",
                    "\n".join(pce),
                )
            ),
        )

    def set_clear_hash_off(self):
        """Set to not clear hash tables before position go command sequence."""
        if (
            tkinter.messagebox.askquestion(
                parent=self.menu_commands,
                title="Clear Hash OFF",
                message="".join(
                    (
                        "Turn OFF clear hash tables before analysing a position?\n\n",
                        "Consult engine documentation for implications of clearing ",
                        "hash tables or not.",
                    )
                ),
            )
            == tkinter.messagebox.YES
        ):
            self.uci.clear_hash = False
            self._modify_command_menu_item(
                "Clear Hash off", "Clear Hash on", self.set_clear_hash_on
            )

    def set_clear_hash_on(self):
        """Set to clear hash tables before position go command sequence."""
        if (
            tkinter.messagebox.askquestion(
                parent=self.menu_commands,
                title="Clear Hash ON",
                message="".join(
                    (
                        "Turn ON clear hash tables before analysing a position?\n\n",
                        "Consult engine documentation for implications of clearing ",
                        "hash tables or not.",
                    )
                ),
            )
            == tkinter.messagebox.YES
        ):
            self.uci.clear_hash = True
            self._modify_command_menu_item(
                "Clear Hash on", "Clear Hash off", self.set_clear_hash_off
            )
