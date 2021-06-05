# runchessapswdu.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for sqlite3.

Run as a new process from the chess GUI.

The customisation is null, and will remain so unless the journals enabling
transaction rollback can be disabled (well then it will not be a customisation
but use of an sqlite3 feature).  DPT deferred update requires that it's
rollback journals are disabled.

"""

if __name__ == "__main__":

    # run by subprocess.popen from ../core/chess.py
    import sys
    import os
    import importlib

    if sys.platform.startswith("openbsd"):

        # The default user class is limited to 512Mb memory but imports need
        # ~550Mb at Python3.6 for sqlite3.
        # Processes running for users in some login classes are allowed to
        # increase their memory limit, unlike the default class, and the limit
        # is doubled if the process happens to be running for a user in one of
        # these login classes.  The staff login class is one of these.
        # At time of writing the soft limit is doubled from 512Mb to 1024Mb.
        try:
            b" " * 1000000000
        except MemoryError:
            import resource

            soft, hard = resource.getrlimit(resource.RLIMIT_DATA)
            try:
                resource.setrlimit(
                    resource.RLIMIT_DATA, (min(soft * 2, hard), hard)
                )
            except:
                try:
                    chesssdu.write_error_to_log()
                except:
                    # Maybe the import is small enough to get away with
                    # limited memory (~500Mb).
                    pass
            del resource

    try:
        # If module not loaded from Python site-packages put the folder
        # containing chesstab at front of sys.path on the assumption all the
        # sibling packages are there too.
        try:
            sp = sys.path[-1].replace("\\\\", "\\")
            packageroot = os.path.dirname(os.path.dirname(__file__))
            if sp != packageroot:
                sys.path.insert(0, os.path.dirname(packageroot))
            chessapswdu = importlib.import_module(
                os.path.basename(packageroot) + ".apsw.chessapswdu"
            )
            chessdu = importlib.import_module(
                os.path.basename(packageroot) + ".gui.chessdu"
            )
        except NameError as msg:
            # When run in the py2exe generated executable the module will
            # not have the __file__ attribute.
            # But the siblings can be assumed to be in the right place.
            if " '__file__' " not in str(msg):
                raise
            from . import chessapswdu
            from ..gui import chessdu

        cdu = chessdu.ChessDeferredUpdate(
            deferred_update_method=chessapswdu.chess_sqlite3du,
            database_class=chessapswdu.ChessDatabase,
        )
    except:
        try:
            chessdu.write_error_to_log()
        except:
            # Assume that parent process will report the failure
            pass
        sys.exit(1)
