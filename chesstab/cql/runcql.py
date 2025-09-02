# runcql.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Run evaluation of CQL queries on database against games on database.

The queries and games marked evaluated are ignored in the run.

"""
import os
import datetime
import traceback
import tkinter

from solentware_misc.gui.logtextbase import LogTextBase

from solentware_bind.gui.bindings import Bindings

from .. import (
    ERROR_LOG,
    APPLICATION_NAME,
)


class RuncqlError(Exception):
    """Exception class for runcql module."""


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


class RunCQL(Bindings):
    """Do the CQL run for connection defined in datasource and ui.

    database must be a basecore.database.Database instance.

    ui must be a gui.ChessUI instance.
    """

    def __init__(self, database, ui, forget_old):
        """Create the CQL runner User Interface objects."""
        super().__init__()
        self.database = database
        self.ui = ui
        self.forget_old = forget_old
        self.root = tkinter.Toplevel()
        self.root.wm_title(
            " - ".join(
                (
                    " ".join((APPLICATION_NAME, "run CQL")),
                    os.path.basename(database.home_directory),
                )
            )
        )
        self.report = LogTextBase(
            master=self.root,
            cnf={"wrap": tkinter.WORD, "undo": tkinter.FALSE},
        )

    def run(self):
        """Run the CQL runner."""
        self.database.run_cql_statements_on_games_not_evaluated(
            self.root, self.report, self.forget_old
        )
        self.database.mark_games_evaluated()
        self.database.mark_cql_statements_evaluated()


def make_runcql(database, ui, forget_old):
    """Create a RunCQL instance and evaluate marked queries and games.

    database must be a basecore.database.Database instance.
    ui must be a gui.ChessUI instance.
    forget_old determines whether to discard or append to existing answer.

    """
    cqlrunner = RunCQL(database, ui, forget_old)
    try:
        cqlrunner.run()
    except Exception as error:
        try:
            write_error_to_log(database.home_directory)
        except Exception:
            # Assume that parent process will report the failure.
            raise SystemExit(
                " reporting exception in ".join(
                    ("Exception while", "doing CQL evaluation in runcql")
                )
            ) from error
        raise SystemExit(
            "Reporting exception in runcql while doing CQL evaluation"
        ) from error
