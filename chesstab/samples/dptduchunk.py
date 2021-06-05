# dptduchunk.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file in chunks using DPT single-step deferred update.

The chunks are are chosen so the job does not run out of memory when running
under wine.  The test for low memory usually does not work (if I recall
correctly there was one version of wine where a test, not the one used before
or since, did spot the condition allowing DPT to flush it's buffers in time).
"""


if __name__ == "__main__":

    import tkinter

    import tkinter.messagebox
    import tkinter.filedialog

    from chesstab.dpt.chessdptdu import chess_dptdu_chunks

    root = tkinter.Tk()
    root.wm_title(string="Test Import Chess Games")
    root.wm_iconify()
    dbdir = tkinter.filedialog.askdirectory(title="Open Chess database folder")
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
                chess_dptdu_chunks(dbdir, (filename,), {})
    root.destroy()
