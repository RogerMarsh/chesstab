# file_widget.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The widget to drive import of a PGN file.

This module contains FileWidget, the code common to the original *du_file
modules; and file_du, a cut-down version of the chess_*du functions in the
engine specific chess*du modules (db.chessdbdu for example).
"""

import tkinter
import os

import tkinter.messagebox
import tkinter.filedialog

from ..core.chessrecord import ChessDBrecordGameImport


def file_du(database, dbpath, pgnpath):
    """Open database, import games and close database."""
    cdb = database(dbpath, allowcreate=True)
    importer = ChessDBrecordGameImport()
    cdb.open_database()
    cdb.set_defer_update()
    s = open(pgnpath, "r", encoding="iso-8859-1")
    importer.import_pgn(cdb, s, pgnpath)
    s.close()
    cdb.do_final_segment_deferred_updates()
    cdb.unset_defer_update()
    cdb.close_database()


class FileWidget:
    def __init__(self, database, engine_name):
        root = tkinter.Tk()
        root.wm_title(string=" - ".join((engine_name, "Import PGN file")))
        root.wm_iconify()
        dbdir = tkinter.filedialog.askdirectory(
            title=" - ".join((engine_name, "Open ChessTab database"))
        )
        if dbdir:
            filename = tkinter.filedialog.askopenfilename(
                title="PGN file of Games",
                defaultextension=".pgn",
                filetypes=(("PGN Chess Games", "*.pgn"),),
            )
            if filename:
                if tkinter.messagebox.askyesno(
                    title="Import Games", message="Proceed with import"
                ):
                    file_du(database, dbdir, filename)
        root.destroy()
