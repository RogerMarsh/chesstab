# dptdu_file.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with dpt.chessdptdu to database.

Cannot use the file_widget module because we are too close to the differences
between DPT and the others.  Specifically DPT deals with segments internally
so function file_du's do_final_segment_deferred_updates() call does not
exist.

dbdu_dir is a step further away and can use the stuff in the directory_widget
module like all the other engines.
"""


if __name__ == "__main__":

    import tkinter
    import os

    import tkinter.messagebox
    import tkinter.filedialog

    from ..dpt.chessdptdu import ChessDatabase
    from ..core.chessrecord import ChessDBrecordGameImport

    def file_du(database, dbpath, pgnpath):
        """Open database, import games and close database.

        Compared with chessdptdu.chess_dptdu function the FileWidget class
        does nothing with the return value, so do not bother to calculate it.

        """
        cdb = database(dbpath, allowcreate=True)
        importer = ChessDBrecordGameImport()
        cdb.open_database()
        s = open(pgnpath, "r", encoding="iso-8859-1")
        importer.import_pgn(cdb, s, pgnpath)
        s.close()
        cdb.close_database_contexts()

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

    FileWidget(ChessDatabase, "dpt")
