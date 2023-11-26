# left_trim_pgn_file.py
# Copyright 2023 Roger Marsh
# Licence: See LICENSE.txt (BSD licence)

"""Create new file by removing a number of characters from start of file.

The number of characters is expected to be the one reported in the final
'Game <g>, to character <number> in PGN, ...' before an import failed or
was stopped.  The new file can be imported by ChessTab to complete the
original import.
"""
import os
import tkinter
import tkinter.ttk
import tkinter.filedialog


class LeftTrimPGNFile:
    """Select existing, and new, PGN files, trim location, then create new."""

    _START_TEXT = "".join(
        (
            "Location should be the final 'to character' number reported ",
            "in an import of PGN file which failed or was stopped.",
        )
    )
    _SAMPLE_SIZE = 5000
    _READ_CHUNK = 20000000
    SOURCE = "source"
    HEADING = "heading"
    TRIMMED = "trimmed"
    SOURCE_COLOR = "light grey"
    HEADING_COLOR = "yellow"
    TRIMMED_COLOR = "cyan"

    def __init__(self):
        """Build the user interface."""
        self._bindings = {}
        root = tkinter.Tk()
        root.wm_title("Left Trim PGN File")
        root.wm_resizable(width=tkinter.FALSE, height=tkinter.FALSE)
        root.columnconfigure(1, uniform="a")
        root.columnconfigure(2, uniform="a")
        root.columnconfigure(3, uniform="a")
        tkinter.ttk.Label(master=root, text="Trimmed PGN file").grid(
            row=0, column=0
        )
        tkinter.ttk.Label(master=root, text="PGN file").grid(row=1, column=0)
        tkinter.ttk.Label(master=root, text="Location in PGN file").grid(
            row=2, column=0
        )
        tkinter.ttk.Label(
            master=root,
            text="Preferably new",
        ).grid(row=0, column=3, columnspan=2)
        tkinter.ttk.Label(
            master=root,
            text="Must exist",
        ).grid(row=1, column=3, columnspan=2)
        tkinter.ttk.Label(
            master=root,
            text="Character position at which trimmed file starts",
        ).grid(row=2, column=2, columnspan=3)
        tkinter.ttk.Label(master=root, text="Log").grid(
            row=6, column=1, pady=5
        )
        tkinter.ttk.Label(master=root, text=self._START_TEXT).grid(
            row=5, column=0, pady=5, columnspan=4, padx=10
        )
        tkinter.ttk.Label(master=root, text="Right-click for menu").grid(
            row=6, column=2, pady=5, sticky="e"
        )
        trimmedpgn = tkinter.ttk.Entry(master=root)
        trimmedpgn.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        trimmedfile = tkinter.StringVar(root, "")
        trimmedpgn["textvariable"] = trimmedfile
        sourcepgn = tkinter.ttk.Entry(master=root)
        sourcepgn.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        sourcefile = tkinter.StringVar(root, "")
        sourcepgn["textvariable"] = sourcefile
        location = tkinter.ttk.Entry(master=root)
        location.grid(row=2, column=1, columnspan=1, sticky="ew", pady=5)
        locationvar = tkinter.StringVar(root, "")
        location["textvariable"] = locationvar
        frame = tkinter.ttk.Frame(master=root)
        frame.grid(row=7, column=0, columnspan=4, sticky="ew")
        text = tkinter.Text(master=frame, wrap=tkinter.WORD)
        scrollbar = tkinter.ttk.Scrollbar(
            master=frame, orient=tkinter.VERTICAL, command=text.yview
        )
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        text.pack(fill=tkinter.BOTH)
        self.menu = tkinter.Menu(master=frame, tearoff=False)
        self.__menu = self.menu
        self.__xy = None
        self.root = root
        self.text = text
        self.sourcepgn = sourcepgn
        self.sourcefile = sourcefile
        self.trimmedpgn = trimmedpgn
        self.trimmedfile = trimmedfile
        self.location = location
        self.locationvar = locationvar
        self.location_value = None
        self.sourcefile_value = None
        self.trimmedfile_value = None
        self.set_menu_and_entry_events_for_create_trimmed_pgn_file()
        location.focus_set()
        if self.HEADING:
            self.text.tag_configure(
                self.HEADING, background=self.HEADING_COLOR
            )
        if self.SOURCE:
            self.text.tag_configure(self.SOURCE, background=self.SOURCE_COLOR)
        if self.TRIMMED:
            self.text.tag_configure(
                self.TRIMMED, background=self.TRIMMED_COLOR
            )
        self._displayed = None

    def insert_text(self, text, tag=None):
        """Wrap Text widget insert with Enable and Disable state configure."""
        if tag:
            self.text.insert(tkinter.END, text, tag)
        else:
            self.text.insert(tkinter.END, text)

    def report_action_or_error(self, msg, error=True):
        """Report outcome of action by adding msg to widget and by dialogue."""
        self.insert_text("\n\n")
        self.insert_text("".join(msg))
        if error:
            tkinter.messagebox.showerror(
                master=self.root, message="\n".join(msg)
            )
        else:
            tkinter.messagebox.showinfo(
                master=self.root, message="\n".join(msg)
            )

    def show_menu(self, event=None):
        """Show the popup menu for widget."""
        self.__menu.tk_popup(*event.widget.winfo_pointerxy())
        self.__xy = event.x, event.y
        self.__menu = self.menu

    def is_request_valid(self, query_overwrite=True):
        """Create PGN file by trimming source PGN file."""
        location = self.locationvar.get().strip()
        sourcefile = self.sourcefile.get().strip()
        trimmedfile = self.trimmedfile.get().strip()
        if not sourcefile and not trimmedfile and not location:
            msg = "Please specify all three items"
        elif not trimmedfile and not location:
            msg = "Please specify trimmed PGN file name and location"
        elif not sourcefile and not location:
            msg = "Please specify PGN file name and location"
        elif not sourcefile and not trimmedfile:
            msg = "Please specify trimmed PGN file name and PGN file name"
        elif not sourcefile:
            msg = "Please specify PGN file name"
        elif not trimmedfile:
            msg = "Please specify trimmed PGN file name"
        elif not location:
            msg = "Please specify location"
        elif not location.isdigit():
            msg = "Location must be an integer"
        else:
            msg = None
        if msg:
            tkinter.messagebox.showinfo(master=self.root, message=msg)
            return False
        if not os.path.isfile(sourcefile):
            tkinter.messagebox.showinfo(
                master=self.root,
                message=sourcefile.join(("PGN file ", " does not exist")),
            )
            return False
        if os.path.isdir(trimmedfile):
            tkinter.messagebox.showinfo(
                master=self.root,
                message=trimmedfile.join(
                    ("Trimmed PGN file name ", " is a directory")
                ),
            )
            return False
        if query_overwrite and os.path.isfile(trimmedfile):
            if not tkinter.messagebox.askyesno(
                master=self.root,
                message=trimmedfile.join(
                    (
                        "Trimmed PGN file name ",
                        " exists.\n\nDo you wish to overwrite it?",
                    )
                ),
            ):
                return False
        self.location_value = location
        self.sourcefile_value = sourcefile
        self.trimmedfile_value = trimmedfile
        return True

    def _seek_start_location(self, file, location):
        """Skip the first 'location' characters of file."""
        # Not file.seek(...) because location is counted in characters.
        # open(<file name>) was "r" not "rb".
        while True:
            location = location - self._READ_CHUNK
            if location <= 0:
                file.read(self._READ_CHUNK + location)
                break
            file.read(self._READ_CHUNK)

    def display_text_around_location(self, event=None):
        """Create PGN file by trimming source PGN file."""
        if not self.is_request_valid(query_overwrite=False):
            return
        with open(self.sourcefile_value, encoding="iso-8859-1") as source:
            self._seek_start_location(
                source,
                max(0, int(self.location_value) - self._SAMPLE_SIZE),
            )
            self.insert_text("\n\n")
            self.insert_text("Before start trim location.", tag=self.HEADING)
            self.insert_text("\n")
            self.insert_text(self.sourcefile_value, tag=self.HEADING)
            self.insert_text("\n\n")
            self.insert_text(source.read(self._SAMPLE_SIZE), tag=self.SOURCE)
            self.insert_text("\n\n")
            self.insert_text("After start trim location.", tag=self.HEADING)
            self.insert_text("\n")
            see = self.text.index(tkinter.END)
            self.insert_text(self.sourcefile_value, tag=self.HEADING)
            self.insert_text("\n\n")
            self.insert_text(source.read(self._SAMPLE_SIZE), tag=self.TRIMMED)
            self.insert_text("\n\n")
            self.insert_text("End of start trim sample.", tag=self.HEADING)
            self.insert_text("\n")
            self.insert_text(self.sourcefile_value, tag=self.HEADING)
            self.insert_text("\n\n")
            self.text.see(see)
            self.text.focus_set()
        self._displayed = True
        self.location_value = None
        self.sourcefile_value = None
        self.trimmedfile_value = None

    def create_trimmed_pgn_file(self, event=None):
        """Create PGN file by trimming source PGN file."""
        if not self.is_request_valid(query_overwrite=True):
            return
        if not self._displayed:
            tkinter.messagebox.showinfo(
                master=self.root,
                message="Display text around location to verify boundary",
            )
            return
        with open(self.sourcefile_value, encoding="iso-8859-1") as source:
            self._seek_start_location(source, int(self.location_value))
            with open(
                self.trimmedfile_value, "w", encoding="iso-8859-1"
            ) as output:
                while True:
                    read_chunk = source.read(self._READ_CHUNK)
                    if not read_chunk:
                        break
                    output.write(read_chunk)
        self.insert_text("\n\n")
        self.insert_text("Trimmed PGN file written to", tag=self.HEADING)
        self.insert_text("\n")
        self.insert_text(self.trimmedfile_value, tag=self.HEADING)
        self.insert_text("\n\n")
        self.text.see(tkinter.END)
        self._displayed = False
        self.location_value = None
        self.sourcefile_value = None
        self.trimmedfile_value = None
        self.locationvar.set("")
        self.sourcefile.set("")
        self.trimmedfile.set("")

    def select_source_pgn_file(self, event=None):
        """Select source PGN file (which must exist)."""
        initialdir = (
            os.path.dirname(self.sourcefile.get())
            or os.path.dirname(self.trimmedfile.get())
            or "~"
        )
        localfilename = tkinter.filedialog.askopenfilename(
            parent=self.text,
            title="Select PGN file to be trimmed",
            filetypes=(("PGN files", "*.pgn"), ("All files", "*")),
            initialdir=initialdir,
        )
        if localfilename:
            self.sourcefile.set(localfilename)
            self._displayed = False

    def select_trimmed_pgn_file(self, event=None):
        """Select trimmed PGN file (which may be a new file)."""
        sourcefile = self.sourcefile.get()
        if sourcefile:
            initialbase, initialext = os.path.splitext(
                os.path.basename(sourcefile)
            )
            initialfile = "_trimmed".join((initialbase, initialext))
        else:
            initialfile = ""
        initialdir = (
            os.path.dirname(self.trimmedfile.get())
            or os.path.dirname(sourcefile)
            or "~"
        )
        localfilename = tkinter.filedialog.asksaveasfilename(
            parent=self.text,
            title="Select trimmed file",
            filetypes=(("PGN files", "*.pgn"), ("All files", "*.*")),
            initialdir=initialdir,
            initialfile=initialfile,
            defaultextension=".pgn",
        )
        if localfilename:
            self.trimmedfile.set(localfilename)
            self._displayed = False

    def set_menu_and_entry_events_for_create_trimmed_pgn_file(self):
        """Turn events for opening a URL on if active is True otherwise off."""
        menu = self.menu
        menu.add_separator()
        menu.add_command(
            label="Create Trimmed PGN File",
            command=self.create_trimmed_pgn_file,
            accelerator="Alt F4",
        )
        menu.add_separator()
        menu.add_command(
            label="Select Source PGN File",
            command=self.select_source_pgn_file,
            accelerator="Alt F5",
        )
        menu.add_separator()
        menu.add_command(
            label="Select Trimmed PGN File",
            command=self.select_trimmed_pgn_file,
            accelerator="Alt F6",
        )
        menu.add_separator()
        menu.add_command(
            label="Display Text Around Location",
            command=self.display_text_around_location,
            accelerator="Alt F7",
        )
        menu.add_separator()
        for entry in (self.text,):
            self._bind_for_scrolling_only(entry)
        sequence_map = (
            ("<Alt-KeyPress-F7>", self.display_text_around_location),
            ("<Alt-KeyPress-F6>", self.select_trimmed_pgn_file),
            ("<Alt-KeyPress-F5>", self.select_source_pgn_file),
            ("<Alt-KeyPress-F4>", self.create_trimmed_pgn_file),
            ("<KeyPress-Return>", self.create_trimmed_pgn_file),
        )
        bindings = self._bindings
        for entry in (
            self.sourcepgn,
            self.trimmedpgn,
            self.location,
            self.text,
        ):
            for sequence, function in sequence_map:
                key = (entry, sequence)
                if key in bindings:
                    entry.unbind(sequence, funcid=bindings[key])
                bindings[key] = entry.bind(sequence, function)
            bindings[entry, "<ButtonPress-3>"] = entry.bind(
                "<ButtonPress-3>", self.show_menu
            )

    def _bind_for_scrolling_only(self, widget):
        bindings = self._bindings
        for sequence, return_ in (
            ("<KeyPress>", "break"),
            ("<Home>", None),
            ("<Left>", None),
            ("<Up>", None),
            ("<Right>", None),
            ("<Down>", None),
            ("<Prior>", None),
            ("<Next>", None),
            ("<End>", None),
        ):
            key = (widget, sequence)
            if key in bindings:
                widget.unbind(sequence, funcid=bindings[key])
            bindings[key] = widget.bind(sequence, lambda e: return_)


if __name__ == "__main__":
    LeftTrimPGNFile().root.mainloop()
