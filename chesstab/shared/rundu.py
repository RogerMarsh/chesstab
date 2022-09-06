# rundu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for database engine.

The rundu function is run in a new process from the chess GUI by
subprocess.popen.

"""
import sys
import os
import importlib


def rundu(engine_module_name, database_module_name):
    """Do the deferred update using the specified database engine.

    engine_module_name and database_module_name must be absolute path
    names: 'chesstab.gui.chessdb' as engine_module_name and
    'chesstab.apsw.chessapswdu' as database_module_name for example.

    A directory containing the chesstab package must be on sys.path.

    """
    database_module = importlib.import_module(database_module_name)
    engine_module = importlib.import_module(engine_module_name)
    if sys.platform.startswith("openbsd"):
        import resource

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

            soft, hard = resource.getrlimit(resource.RLIMIT_DATA)
            try:
                resource.setrlimit(
                    resource.RLIMIT_DATA, (min(soft * 2, hard), hard)
                )
            except Exception:
                try:
                    engine_module.write_error_to_log()
                except Exception:
                    # Maybe the import is small enough to get away with
                    # limited memory (~500Mb).
                    pass

        del resource
    try:
        cdu = engine_module.ChessDeferredUpdate(
            deferred_update_method=database_module.chess_database_du,
            database_class=database_module.ChessDatabase,
        )
    except Exception:
        try:
            engine_module.write_error_to_log()
        except Exception:
            # Assume that parent process will report the failure.
            pass
        sys.exit(1)
