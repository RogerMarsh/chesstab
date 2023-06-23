# file_widget_fastunload.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Try fast unload of a ChessTab database.

Purpose is to verify fast unload functions correctly for at least one
ChessTab database, and generate sets of 'TAPE' files to test fast load.

The attempt to write a fast load input files generator for PGN files from
the description of file formats in DPT DBA Guide failed: so see if there
is a way fast load works and copy that.
"""

import tkinter
import os
import time

import tkinter.messagebox
import tkinter.filedialog

import dptdb.dptapi

from ..dpt.chessdpt import ChessDatabase


def file_fastunload(dbpath, outputdir):
    """Open database, fast unload Games file, and close database."""
    print(time.ctime())
    cdb = ChessDatabase(dbpath, allowcreate=True)
    cdb.open_database()
    for table in cdb.table.values():
        # Unload accepts positional arguments only.
        # Want 'dir' argument as 'dbpath', not the default '#FASTIO' via
        # definition of FUNLOAD_DIR.
        # So have to specify options where FUNLOAD_DEFAULT, itself defined
        # via FUNLOAD_ALLINFO (at time of writing) which is required option,
        # is the default option.
        table.opencontext.Unload(
            dptdb.dptapi.FUNLOAD_DEFAULT, None, None, outputdir
        )
    cdb.close_database()
    print(time.ctime())


class FileWidget:
    """Select ChessTab database to fast unload."""

    def __init__(self):
        """Import games into database using engine_name database engine."""
        root = tkinter.Tk()
        root.wm_title("Fast Unload ChessTab Database")
        root.wm_iconify()
        dbdir = tkinter.filedialog.askdirectory(
            title="Fast Unload ChessTab Database"
        )
        if dbdir:
            outputdir = tkinter.filedialog.askdirectory(
                title="Fast Unload Output Directory"
            )
            if outputdir:
                if tkinter.messagebox.askyesno(
                    title="Fast Unload Games",
                    message="Proceed with Fast Unload",
                ):
                    file_fastunload(dbdir, outputdir)
        root.destroy()


if __name__ == "__main__":
    FileWidget()
