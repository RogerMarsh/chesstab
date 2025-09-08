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
from ..cql import queryevaluator


# This code is adapted from exceptionhandler module where it is not
# available as an ExceptionHandler method.
def write_error_to_log(directory):
    """Write the exception to the error log with a time stamp."""
    with open(
        os.path.join(directory, ERROR_LOG),
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
        try:
            self.database.run_cql_statements_on_games_not_evaluated(
                self.root, self.report, self.forget_old
            )
        finally:
            if self.database.all_games_and_queries_evaluated():
                self.database.clear_cql_queries_pending_evaluation()
                self.database.mark_games_evaluated()
                self.database.mark_cql_statements_evaluated()


def make_runcql(database, ui, forget_old):
    """Create a RunCQL instance and evaluate marked queries and games.

    database must be a basecore.database.Database instance.
    ui must be a gui.ChessUI instance.
    forget_old determines whether to discard or append to existing answer.

    """
    cqlrunner = RunCQL(database, ui, forget_old)
    title = " - ".join((APPLICATION_NAME, "run CQL"))
    try:
        cqlrunner.run()
    except queryevaluator.QueryEvaluatorError:
        cqlrunner.report_exception(root=cqlrunner.root, title=title)
    except tkinter.TclError as error:
        if not str(error).startswith("invalid command name"):
            write_error_to_log(database.home_directory)
            tkinter.messagebox.showinfo(
                title=title,
                message="".join(
                    (
                        "Unable to show exception report\n\n",
                        "The reported reason is:\n\n",
                        str(error),
                        "\n\nAn entry has been made in the error log",
                        "\n\nThe query evaluation was probably not completed",
                        "\n\n",
                        APPLICATION_NAME,
                        " will terminate on dismissing this dialogue",
                    )
                ),
            )
            raise SystemExit(
                "Terminate after exception in CQL evaluation"
            ) from error
        # Assume the runcql widget was terminated by window manager or
        # desktop action rather than some application error.
        tkinter.messagebox.showinfo(
            title=title,
            message="".join(
                (
                    "The CQL query run was stopped\n\n",
                    "The query evaluation was probably not completed",
                )
            ),
        )
    except:
        cqlrunner.report_exception(root=cqlrunner.root, title=title)
        raise SystemExit(
            "Terminate after exception in CQL evaluation"
        ) from None
