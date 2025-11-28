# rundu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for database engine.

The rundu function is run in a new multiprocessing.Process started from the
chess GUI.

Spawn the deferred update process by the multiprocessing module.

"""
import importlib
import os
import datetime
import traceback

from .. import (
    ERROR_LOG,
    APPLICATION_NAME,
)
from ..gui import chessdu


class RunduError(Exception):
    """Exception class for rundu module."""


def write_error_to_log(directory):
    """Write the exception to the error log with a time stamp."""
    with open(
        os.path.join(directory, ERROR_LOG),  # Was sys.argv[1]
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            "".join(
                (
                    "\n\n\n",
                    " ".join(
                        (
                            APPLICATION_NAME,
                            "exception report at",
                            datetime.datetime.isoformat(
                                datetime.datetime.today()
                            ),
                        )
                    ),
                    "\n\n",
                    traceback.format_exc(),
                    "\n\n",
                )
            )
        )


def rundu(
    home_directory,
    database_module_name,
    resume,
    sort_area,
):
    """Do the deferred update using the specified database engine.

    engine_module_name and database_module_name must be absolute path
    names: 'chesstab.gui.chessdb' as engine_module_name and
    'chesstab.apsw.database_du' as database_module_name for example.

    A directory containing the chesstab package must be on sys.path.

    """
    database_module = importlib.import_module(database_module_name)
    deferred_update = chessdu.DeferredUpdate(
        deferred_update_module=database_module,
        database_class=database_module.Database,
        home_directory=home_directory,
        resume=resume,
        sort_area=sort_area,
    )
    try:
        deferred_update.root.mainloop()
    except Exception as error:
        try:
            write_error_to_log(home_directory)
        except Exception:
            # Assume that parent process will report the failure.
            raise SystemExit(
                " reporting exception in ".join(
                    ("Exception while", "doing deferred update in rundu")
                )
            ) from error
        raise SystemExit(
            "Reporting exception in rundu while doing deferred update"
        ) from error
