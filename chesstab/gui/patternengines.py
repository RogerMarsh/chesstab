# patternengines.py
# Copyright 2025 Roger Marsh
# License: See LICENSE.TXT (BSD license)
"""Edit file listing available chess and pattern engines for a database.

Stockfish is a chess engine and CQL is a pattern engine.

The file name will be the name of the file containing the database with
'-engines' suffix.
"""

import sys
import tkinter
import tkinter.messagebox
import tkinter.filedialog

from solentware_bind.gui.bindings import Bindings

from ..core import enginecommands

EDIT = "edit"
TITLE = "title"
TITLE_DATA = "titledata"
TITLE_COLOR = "thistle"
DEFAULT = "default"
DEFAULT_DATA = "defaultdata"
DEFAULT_COLOR = "yellow"
TEXT = "text"
TEXT_DATA = "textdata"
TEXT_COLOR = "wheat"
ELIDE_SPLIT = "elidesplit"
ELIDE_NAME = "elidename"
ELIDE_DEFAULT = "elidedefault"
DESCRIPTION = "description"
_title_tags = [TITLE_DATA, TITLE, EDIT]
_default_tags = [DEFAULT_DATA, DEFAULT]
_text_tags = [TEXT_DATA, TEXT, EDIT]

_WIN32_PLATFORM = sys.platform == "win32"


class PatternEngines(Bindings):
    """Widget to edit the file listing engines available to a database.

    master is the application instance requiring the editor.
    """

    def __init__(self, master):
        """Create the editor widget."""
        super().__init__()
        self._master = master
        self._engine_commands = enginecommands.EngineCommands(
            master.opendatabase.database_file
        )
        self.toplevel = tkinter.Toplevel(master=master.root)
        self.bind(self.toplevel, "<Destroy>", self._destroy)
        menubar = tkinter.Menu(self.toplevel)
        menu1 = tkinter.Menu(menubar, name="file", tearoff=False)
        menubar.add_cascade(label="File", menu=menu1, underline=0)
        menu1.add_command(label="Close", underline=0, command=self._close_file)
        menu1.add_separator()
        menu1.add_command(label="Save", underline=0, command=self._save_file)
        menubar.add_command(label="Insert", underline=0, command=self._insert)
        menubar.add_command(label="Remove", underline=0, command=self._remove)
        menubar.add_command(
            label="Command", underline=0, command=self._command
        )
        menubar.add_command(
            label="Default", underline=0, command=self._default
        )
        menubar.add_command(
            label="Toggle names", underline=0, command=self._toggle_names
        )
        self.toplevel.configure(menu=menubar)
        self.editor = tkinter.Text(
            self.toplevel, wrap="word", undo=tkinter.FALSE
        )
        widget = self.editor
        scrollbar = tkinter.Scrollbar(
            self.toplevel, orient=tkinter.VERTICAL, command=widget.yview
        )
        widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        widget.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        widget.tag_configure(TITLE, background=TITLE_COLOR)
        widget.tag_configure(DEFAULT, background=DEFAULT_COLOR)
        widget.tag_configure(TEXT, background=TEXT_COLOR)
        widget.tag_configure(ELIDE_SPLIT, elide=tkinter.TRUE)
        widget.tag_configure(ELIDE_NAME, elide=tkinter.TRUE)
        self.tag_bind(widget, EDIT, "<Return>", self._suppress_char)
        self.tag_bind(widget, EDIT, "<KP_Enter>", self._suppress_char)
        self.tag_bind(widget, EDIT, "<Escape>", self._suppress_char)
        self.tag_bind(widget, EDIT, "<Tab>", self._suppress_char)
        self.tag_bind(widget, EDIT, "<BackSpace>", self._backspace_char)
        self.tag_bind(widget, EDIT, "<Delete>", self._delete_char)
        self.tag_bind(widget, EDIT, "<KeyPress>", self._insert_char)
        self.bind(widget, "<ISO_Left_Tab>", self._suppress)
        self.bind(widget, "<KeyPress>", self._suppress_char)

    def _destroy(self, event):
        """Tidy up on 'Destroy' event.

        Unset flag which prevents more than one PatternEngines instance
        existing.

        """
        del event
        self._master.show_query_engines_toplevel = None

    def populate_widget(self):
        """Populate widget from file associated with database."""
        try:
            entries = self._engine_commands.read_pattern_engines()
        except FileNotFoundError:
            tkinter.messagebox.showinfo(
                master=self.editor,
                message="".join(
                    (
                        "Empty entries displayed because '",
                        self._engine_commands.filename,
                        "' does not exist",
                    )
                ),
                title="Show Query Engines",
            )
            return
        except IsADirectoryError:
            tkinter.messagebox.showerror(
                master=self.editor,
                message="".join(
                    (
                        "'",
                        self._engine_commands.filename,
                        "' is a directory not a file as expected",
                    )
                ),
                title="Show Query Engines",
            )
            return
        except SyntaxError:
            tkinter.messagebox.showerror(
                master=self.editor,
                message="".join(
                    (
                        "Empty entries displayed because evaluating '",
                        self._engine_commands.filename,
                        "' gave a SyntaxError exception",
                    )
                ),
                title="Show Query Engines",
            )
            return
        except KeyError:
            tkinter.messagebox.showerror(
                master=self.editor,
                message="".join(
                    (
                        "Empty entries displayed because '",
                        self._engine_commands.filename,
                        "' does not contain any",
                    )
                ),
                title="Show Query Engines",
            )
            return
        for default, title, text in zip(*entries):
            self._insert_entry(default, title, text)
        self.editor.edit_modified(tkinter.FALSE)

    def _close_file(self):
        """Handle menu 'File - Close' event."""
        if self.editor.edit_modified():
            message = "".join(
                (
                    "Text has been modified.\n\n",
                    "Do you wish to save edits before closing file? ",
                    "(Yes / No)\nCancel to abandon closing file.",
                )
            )
            title = "Close"
            ask = tkinter.messagebox.askyesnocancel(
                master=self.editor, message=message, title=title
            )
            if ask is None:
                return
            if ask:
                self._update_file(title)
        self.toplevel.destroy()

    def _save_file(self, title="Save"):
        """Handle menu 'File - Save' event."""
        dlg = tkinter.messagebox.askyesno(
            master=self.editor,
            message="".join(("Please confirm Save action",)),
            title=title,
        )
        if dlg:
            self._update_file(title)

    def _update_file(self, title):
        """Merge edited data into file."""
        widget = self.editor
        engines = []
        for tag, tagdata in (
            (DEFAULT, DEFAULT_DATA),
            (TITLE, TITLE_DATA),
            (TEXT, TEXT_DATA),
        ):
            entries = []
            engines.append(entries)
            start_range = "1.0"
            while True:
                tagrange = widget.tag_nextrange(tag, start_range, tkinter.END)
                if not tagrange:
                    break
                datarange = widget.tag_nextrange(tagdata, *tagrange)
                if not datarange:
                    entries.append("")
                else:
                    entries.append(widget.get(*datarange))
                start_range = tagrange[-1]
        try:
            self._engine_commands.write_pattern_engines(engines)
        except IsADirectoryError:
            tkinter.messagebox.showerror(
                master=self.editor,
                message="".join(
                    (
                        "'",
                        self._engine_commands.filename,
                        "' is a directory not a file as expected",
                    )
                ),
                title=title,
            )
            return
        self.editor.edit_modified(tkinter.FALSE)
        tkinter.messagebox.showinfo(
            master=self.editor,
            message="Available pattern engines updated",
            title=title,
        )

    def _insert(self):
        """Handle menu 'Insert' event.

        Insert a blank entry after the entry containing the Insert cursor.

        """
        self._insert_entry("", "", "")

    def _remove(self):
        """Handle menu 'Remove' event.

        Remove the entry containing the Insert cursor.

        """
        widget = self.editor
        prevrange = widget.tag_prevrange(DESCRIPTION, tkinter.INSERT)
        if not prevrange:
            return
        nextrange = widget.tag_nextrange(DESCRIPTION, tkinter.INSERT)
        if nextrange:
            remove_end = nextrange[0]
        else:
            remove_end = tkinter.END
        widget.delete(prevrange[0], remove_end)
        nextrange = widget.tag_nextrange(ELIDE_SPLIT, tkinter.INSERT)
        if nextrange:
            widget.mark_set(tkinter.INSERT, nextrange[-1])
        else:
            widget.mark_set(tkinter.INSERT, tkinter.END)
        widget.see(tkinter.INSERT)

    def _command(self):
        """Handle menu 'Command' event.

        Select a path for the entry containing the Insert cursor.

        """
        widget = self.editor
        titlerange = widget.tag_prevrange(TITLE, tkinter.INSERT)
        if not titlerange:
            tkinter.messagebox.showinfo(
                master=self.editor,
                message="No entry avaiable to update",
                title="Select Command",
            )
            return
        titlerangenext = widget.tag_nextrange(TITLE, titlerange[-1])
        textdatarange = widget.tag_nextrange(TEXT_DATA, titlerange[0])
        if _WIN32_PLATFORM:
            filetypes = (("CQL evaluator", "*.exe"),)
        else:
            filetypes = ()
        filename = tkinter.filedialog.askopenfilename(
            parent=self.toplevel,
            title="Locate CQL evaluator",
            filetypes=filetypes,
            initialfile="",
            initialdir="~",
        )
        if not filename:
            return
        if not textdatarange:
            self.__set_empty_command_entry(filename, titlerange)
            return
        if (
            titlerangenext
            and widget.compare(titlerangenext[0], ">", textdatarange[0])
            or (not titlerangenext and textdatarange)
        ):
            widget.mark_set(tkinter.INSERT, textdatarange[0])
            widget.delete(*textdatarange)
            widget.insert(tkinter.INSERT, filename, _text_tags)
            widget.see(tkinter.INSERT)
            return
        self.__set_empty_command_entry(filename, titlerange)

    def __set_empty_command_entry(self, filename, titlerange):
        """Set command in entry with empty data."""
        widget = self.editor
        textrange = widget.tag_nextrange(TEXT, titlerange[-1])
        eliderange = widget.tag_nextrange(ELIDE_SPLIT, textrange[0])
        widget.mark_set(tkinter.INSERT, eliderange[-1])
        widget.insert(tkinter.INSERT, filename, _text_tags)
        widget.see(tkinter.INSERT)

    def _default(self):
        """Handle menu 'Default' event.

        Mark the entry containing the Insert cursor as the default.

        """
        widget = self.editor
        defaultdatarange = widget.tag_prevrange(DEFAULT_DATA, tkinter.END)
        if defaultdatarange:
            defaultrange = widget.tag_prevrange(DEFAULT, defaultdatarange[-1])
        else:
            defaultrange = widget.tag_nextrange(DEFAULT, tkinter.INSERT)
        insertrange = widget.tag_prevrange(DEFAULT, tkinter.INSERT)
        if not defaultrange:
            if insertrange:
                self.__set_default(defaultrange, insertrange)
            return
        if not defaultdatarange:
            self.__set_default(defaultrange, insertrange)
            return
        if widget.compare(defaultdatarange[0], "==", insertrange[0]):
            widget.delete(*defaultdatarange)
            widget.see(tkinter.INSERT)
            return
        widget.delete(*defaultdatarange)
        defaultrange = widget.tag_nextrange(DEFAULT, tkinter.INSERT)
        self.__set_default(defaultrange, insertrange)

    def __set_default(self, defaultrange, insertrange):
        """Set the 'default entry' marker."""
        widget = self.editor
        if not defaultrange or widget.compare(
            widget.index(tkinter.INSERT), "<", defaultrange[0]
        ):
            widget.mark_set(tkinter.INSERT, insertrange[0])
        else:
            widget.mark_set(tkinter.INSERT, defaultrange[0])
        widget.insert(tkinter.INSERT, "Default: ", _default_tags)
        widget.see(tkinter.INSERT)

    def _toggle_names(self):
        """Handle menu 'Toggle Names' event.

        Show or hide entry area names.

        When entry area names are visible the pointer must not be over a
        line containing one of these names to allow typing: here it is
        assumed the Text widget has the input focus.

        """
        widget = self.editor
        if int(widget.tag_cget(ELIDE_NAME, "elide")):
            widget.tag_configure(ELIDE_NAME, elide=tkinter.FALSE)
        else:
            widget.tag_configure(ELIDE_NAME, elide=tkinter.TRUE)
        widget.see(tkinter.INSERT)

    def _insert_entry(self, default, name, file):
        """Handle menu 'Insert' event.

        Insert a blank entry after the entry containing the Insert cursor.

        """
        widget = self.editor
        nextrange = widget.tag_nextrange(DESCRIPTION, tkinter.INSERT)
        if nextrange:
            widget.mark_set(tkinter.INSERT, nextrange[0])
        else:
            widget.mark_set(tkinter.INSERT, tkinter.END)
        widget.insert(
            tkinter.INSERT, "Description\n", [ELIDE_NAME, DESCRIPTION]
        )
        widget.insert(tkinter.INSERT, " ", [ELIDE_SPLIT, DEFAULT, TITLE])
        widget.insert(tkinter.INSERT, default, _default_tags)
        widget.insert(tkinter.INSERT, " ", [ELIDE_SPLIT, TITLE])
        widget.insert(tkinter.INSERT, name, _title_tags)
        widget.insert(tkinter.INSERT, "\n", [TITLE, EDIT])
        widget.insert(tkinter.INSERT, " ", [ELIDE_SPLIT, TITLE])
        widget.insert(tkinter.INSERT, "Text\n", [ELIDE_NAME])
        widget.insert(tkinter.INSERT, " ", [ELIDE_SPLIT, TEXT])
        widget.insert(tkinter.INSERT, file, _text_tags)
        widget.insert(tkinter.INSERT, "\n", [TEXT, EDIT])
        widget.insert(tkinter.INSERT, " ", [ELIDE_SPLIT, TEXT])
        widget.insert(tkinter.INSERT, "End\n", [ELIDE_NAME])
        prevrange = widget.tag_prevrange(TITLE, tkinter.INSERT)
        if prevrange:
            nextrange = widget.tag_nextrange(ELIDE_SPLIT, prevrange[0])
            if nextrange:
                widget.mark_set(tkinter.INSERT, nextrange[-1])
        widget.focus_set()
        widget.see(tkinter.INSERT)

    def _insert_char(self, event):
        """Insert non-null character with tags for entry area."""
        if not event.char:
            return "break"
        widget = event.widget
        tags = widget.tag_names(tkinter.INSERT)
        if TEXT in tags:
            widget.insert(tkinter.INSERT, event.char, _text_tags)
        elif TITLE in tags:
            widget.insert(tkinter.INSERT, event.char, _title_tags)
        return None

    def _suppress_char(self, event):
        """Ignore non-null character and suppress other events."""
        if event.char:
            return "break"
        return None

    def _suppress(self, event):
        """Ignore character and suppress other events."""
        del event
        return "break"

    def _backspace_char(self, event):
        """Delete character to left of insert point in area tagged 'edit'."""
        widget = event.widget
        prevchar = widget.index(tkinter.INSERT + "-1c")
        prevrange = widget.tag_prevrange(EDIT, tkinter.INSERT)
        if prevrange and widget.compare(tkinter.INSERT, "<=", prevrange[-1]):
            widget.delete(prevchar)

    def _delete_char(self, event):
        """Delete character to right of insert point in area tagged 'edit'."""
        widget = event.widget
        nextchar = widget.index(tkinter.INSERT + "+1c")
        prevrange = widget.tag_prevrange(EDIT, tkinter.INSERT)
        if prevrange and widget.compare(nextchar, "<", prevrange[-1]):
            widget.delete(tkinter.INSERT)
            return
        nextrange = widget.tag_nextrange(EDIT, tkinter.INSERT)
        if (
            nextrange
            and widget.compare(
                widget.index(tkinter.INSERT), "==", nextrange[0]
            )
            and widget.compare(nextchar, "<", nextrange[-1])
        ):
            widget.delete(tkinter.INSERT)
