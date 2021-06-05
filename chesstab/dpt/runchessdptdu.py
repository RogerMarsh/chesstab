# runchessdptdu.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using DPT single-step deferred update.

Run as a new process from the chess GUI.

"""

if __name__ == "__main__":

    # run by subprocess.popen from ../core/chess.py
    import sys
    import os

    try:
        # If module not loaded from Python site-packages put the folder
        # containing chesstab at front of sys.path on the assumption all the
        # sibling packages are there too.
        try:
            sp = sys.path[-1].replace("\\\\", "\\")
            packageroot = os.path.dirname(
                os.path.dirname(os.path.dirname(__file__))
            )
            if sp != packageroot:
                sys.path.insert(0, packageroot)
        except NameError as msg:
            # When run in the py2exe generated executable the module will
            # not have the __file__ attribute.
            # But the siblings can be assumed to be in the right place.
            if " '__file__' " not in str(msg):
                raise

        # sys.path should now contain correct chesstab modules
        from chesstab.dpt import chessdptdu
        from chesstab.gui import chessdu

        cdu = chessdu.ChessDeferredUpdate(
            deferred_update_method=chessdptdu.chess_dptdu,
            database_class=chessdptdu.ChessDatabase,
        )
    except:
        try:
            chessdu.write_error_to_log()
        except:
            # Assume that parent process will report the failure
            pass
        sys.exit(1)
