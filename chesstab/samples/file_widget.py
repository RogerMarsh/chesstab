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
from ..core.filespec import GAMES_FILE_DEF


def file_du(database, dbpath, pgnpath, **kwargs):
    """Open database, import games and close database."""
    # The name argument in the archive() and delete_archive() calls is
    # needed if 'file_per_database=True' is in **kwargs, it is ignored
    # otherwise.
    cdb = database(dbpath, allowcreate=True, **kwargs)
    importer = ChessDBrecordGameImport()
    cdb.open_database()
    if cdb.take_backup_before_deferred_update:
        cdb.archive(name=GAMES_FILE_DEF)
    cdb.set_defer_update()
    s = open(pgnpath, "r", encoding="iso-8859-1")
    importer.import_pgn(cdb, s, os.path.basename(pgnpath))
    s.close()
    cdb.do_final_segment_deferred_updates()
    cdb.unset_defer_update()
    if cdb.take_backup_before_deferred_update:
        cdb.delete_archive(name=GAMES_FILE_DEF)
    cdb.close_database()


class FileWidget:
    """Provide select PGN game file dialogue and import from selected file."""

    def __init__(self, database, engine_name, **kwargs):
        """Import games into database using engine_name database engine."""
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
                    file_du(database, dbdir, filename, **kwargs)
        root.destroy()
