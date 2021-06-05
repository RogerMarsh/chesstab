# dptdumulti.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file using DPT multi-step deferred update."""


if __name__ == "__main__":

    import tkinter

    import tkinter.messagebox
    import tkinter.filedialog

    from chesstab.dpt.chessdptdumulti import chess_dptdu

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
                chess_dptdu(dbdir, (filename,), {})
    root.destroy()
