# directory_widget.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The widget to drive import of PGN files in a directory."""

import tkinter
import os

import tkinter.messagebox
import tkinter.filedialog


class DirectoryWidget:
    def __init__(self, import_method, engine_name):
        root = tkinter.Tk()
        root.wm_title(
            string=" - ".join((engine_name, "Import PGN from folder"))
        )
        root.wm_iconify()
        dbdir = tkinter.filedialog.askdirectory(
            title=" - ".join((engine_name, "Open ChessTab database"))
        )
        if dbdir:
            folder = tkinter.filedialog.askdirectory(
                title="Directory of PGN files of Games"
            )
            if folder:
                if tkinter.messagebox.askyesno(
                    title="Import Games", message="Proceed with import"
                ):
                    import_method(
                        dbdir,
                        [os.path.join(folder, p) for p in os.listdir(folder)],
                        None,
                    )
        root.destroy()
