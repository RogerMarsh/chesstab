# chessdu.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define User Interface for deferred update process."""

import sys
import os
import traceback
import datetime
import tkinter
import tkinter.font
import tkinter.messagebox
import queue
import time
import multiprocessing
import multiprocessing.dummy
import time

from solentware_misc.gui.logtextbase import LogTextBase

from solentware_bind.gui.bindings import Bindings

from pgn_read.core.parser import PGN

from ..core.pgn import GameUpdateEstimate
from .. import (
    ERROR_LOG,
    APPLICATION_NAME,
)
from ..core.filespec import GAMES_FILE_DEF

# Time taken to parse a sample of a PGN file is measured.
# Number of games in file is estimated from number of bytes used in game scores
# compared with number of bytes in file.
# _DATABASE_UPDATE_FACTOR is set from measuring time taken to import a PGN file
# containing a large number of games to an empty database.  Large means over a
# million games.
# This factor is a big under-estimate when number of games is less than segment
# size.  In practice the difference will be noticed when importing less than
# 131072 games to a database which already has games: the new games will span
# up to three segments when imported.
# Available memory has a big impact because it determines how long the runs of
# sequential updates to indexes can be.  The factor 5 is appropriate when at
# least 1.5Gb is available.  A default build of FreeBSD 10.1 on a PC with 2Gb
# installed passes this test; but Microsoft Windows XP, and later presumably,
# needs more memory to do so.  A default build of OpenBSD 5.9 restricts user
# processes to 0.5Gb.  The situation is not known for OS X or any Linux
# distribution.
# Factor changed from 3 to 5 when CQL5.1 syntax introduced to implement partial
# position searches, due to extra index updates.
_DATABASE_UPDATE_FACTOR = 5


class _Reporter:
    """Helper class to keep 'LogText' API for adding text to log.

    Not used in dptcompatdu module but is used in chessdptdu module.

    """

    def __init__(self, append_text, append_text_only):
        """Note the timestamp plus text, and text only, append methods."""
        self.append_text = append_text
        self.append_text_only = append_text_only


class DeferredUpdateProcess:
    """Define a process to do a deferred update task."""

    def __init__(self, database, method, report_queue, quit_event):
        """Provide queues for communication with GUI."""
        self.database = database
        self.method = method
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.process = multiprocessing.Process(
            target=self._run_import,
            args=(),
        )

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, time = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        time = time.split(".")[0]
        self.report_queue.put("".join((day, " ", time, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _run_import(self):
        """Invoke method to do the deferred update and display job status."""
        status = self.method(
            sys.argv[1],
            sys.argv[2:],
            self.database.get_file_sizes(),
            _Reporter(
                self._report_to_log,
                self._report_to_log_text_only,
            ),
            quit_event=self.quit_event,
        )


class DeferredUpdateEstimateProcess:
    """Define a process to do a deferred update estimate task."""

    def __init__(self, database, sample, report_queue, quit_event):
        """Provide queues for communication with GUI."""
        self.database = database
        self.sample = sample
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.estimate_data = None
        self.process = multiprocessing.Process(
            target=self._allow_import,
            args=(),
        )

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, time = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        time = time.split(".")[0]
        self.report_queue.put("".join((day, " ", time, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _wait_for_quit_event(self):
        """Wait for quit event."""
        self.quit_event.wait()

    def _allow_import(self):
        """Do checks for database engine and return True if import allowed."""
        self.stop_thread = multiprocessing.dummy.DummyProcess(
            target=self._wait_for_quit_event
        )
        self.stop_thread.start()
        # The close_database() in finally clause used to be the first statement
        # after runjob() definition in _run_import() method.  An exception was
        # raised using the sqlite3 module because run_input() is run in a
        # different thread from allow_input().  Earlier versions of chessdu did
        # not attempt to close the connection, hiding the problem.
        # The apsw module did not raise an exception, nor did modules providing
        # an interface to Berkeley DB or DPT.
        self.database.open_database()
        try:
            if not self._estimate_games_in_import():
                return None
            if self._allow_time():
                self.database.report_plans_for_estimate(
                    self._get_pgn_file_estimates(),
                    _Reporter(
                        self._report_to_log,
                        self._report_to_log_text_only,
                    ),
                )
                self.quit_event.set()
                return True
            self._report_to_log("Unable to estimate time to do import.")
            self._report_to_log_text_only("")
            return False
        finally:
            self.database.close_database()

    def _estimate_games_in_import(self):
        """Estimate import size from the first sample games in import files."""
        self.estimate_data = False
        text_file_size = sum([os.path.getsize(pp) for pp in sys.argv[2:]])
        reader = PGN(game_class=GameUpdateEstimate)
        errorcount = 0
        totallen = 0
        totalerrorlen = 0
        totalgamelen = 0
        gamecount = 0
        positioncount = 0
        piecesquaremovecount = 0
        piecemovecount = 0
        estimate = False
        time_start = time.monotonic()
        for pgnfile in sys.argv[2:]:
            if gamecount + errorcount >= self.sample:
                estimate = True
                break
            with open(pgnfile, "r", encoding="iso-8859-1") as source:
                for rcg in reader.read_games(source):
                    if self.quit_event.is_set():
                        self._report_to_log_text_only("")
                        self._report_to_log(
                            " ".join(
                                (
                                    "Estimating task stopped when",
                                    str(gamecount),
                                    "games and",
                                    str(errorcount),
                                    "games with errors found.",
                                )
                            )
                        )
                        return False
                    if gamecount + errorcount >= self.sample:
                        estimate = True
                        break
                    if len(rcg.pgn_text):
                        rawtokenlen = rcg.end_char - rcg.start_char
                    else:
                        rawtokenlen = 0
                    if rcg.state is not None:
                        errorcount += 1
                        totalerrorlen += rawtokenlen
                    else:
                        gamecount += 1
                        totalgamelen += rawtokenlen
                        positioncount += len(rcg.positionkeys)
                        piecesquaremovecount += len(rcg.piecesquaremovekeys)
                        piecemovecount += len(rcg.piecemovekeys)
                    totallen += rawtokenlen
        time_end = time.monotonic()
        if estimate:
            try:
                scale = float(text_file_size) // totallen
            except ZeroDivisionError:
                scale = 0
        else:
            scale = 1
        try:
            bytes_per_game = totalgamelen // gamecount
        except ZeroDivisionError:
            bytes_per_game = 0
        try:
            bytes_per_error = totalerrorlen // errorcount
        except ZeroDivisionError:
            bytes_per_error = 0
        try:
            positions_per_game = positioncount // gamecount
        except ZeroDivisionError:
            positions_per_game = 0
        try:
            pieces_per_game = piecesquaremovecount // gamecount
        except ZeroDivisionError:
            pieces_per_game = 0
        try:
            piecetypes_per_game = piecemovecount // gamecount
        except ZeroDivisionError:
            piecetypes_per_game = 0

        self.estimate_data = (
            int(gamecount * scale),
            bytes_per_game,
            positions_per_game,
            pieces_per_game,
            int(errorcount * scale),
            bytes_per_error,
            estimate,
            gamecount,
            errorcount,
            (time_end - time_start) / (gamecount + errorcount),
        )
        if estimate:
            self._report_to_log_text_only("")
            self._report_to_log(
                " ".join(("Estimated Games:", str(self.estimate_data[0])))
            )
            self._report_to_log_text_only(
                " ".join(("Estimated Errors:", str(self.estimate_data[4]))),
            )
            self._report_to_log_text_only(
                " ".join(("Sample Games:", str(gamecount)))
            )
            self._report_to_log_text_only(
                " ".join(("Sample Errors:", str(errorcount)))
            )
        else:
            self._report_to_log_text_only("")
            self._report_to_log(
                "The import is small so all games are counted."
            )
            self._report_to_log_text_only(
                " ".join(("Games in import:", str(gamecount)))
            )
            self._report_to_log_text_only(
                " ".join(("Errors in import:", str(errorcount))),
            )
        self._report_to_log_text_only(
            " ".join(("Bytes per game:", str(bytes_per_game)))
        )
        self._report_to_log_text_only(
            " ".join(("Bytes per error:", str(bytes_per_error))),
        )
        self._report_to_log_text_only(
            " ".join(("Positions per game:", str(positions_per_game))),
        )

        # positions_per_game == 0 if there are no valid games.
        ppp = "Not a number"
        for count, text in (
            (pieces_per_game, "Pieces per position:"),
            (piecetypes_per_game, "Piece types per position:"),
        ):
            if positions_per_game:
                ppp = str(count // positions_per_game)
            self._report_to_log_text_only(" ".join((text, ppp)))
        self._report_to_log_text_only("")

        # Check if import can proceed
        if gamecount + errorcount == 0:
            self._report_to_log(
                "No games, or games with errors, found in import."
            )
            return False
        if errorcount == 0:
            if estimate:
                self._report_to_log("No games with errors in sample.")
                self._report_to_log_text_only(
                    " ".join(
                        (
                            "It is estimated no games with",
                            "errors exist in import.",
                        )
                    ),
                )
                self._report_to_log_text_only(
                    "Any found in import will be indexed only as errors.",
                )
            else:
                self._report_to_log("No games with errors in import.")
            self._report_to_log_text_only("")
        elif estimate:
            self._report_to_log("Games with errors have been found in sample.")
            self._report_to_log_text_only(
                " ".join(
                    (
                        "The sample is the first",
                        str(self.sample),
                        "games in import.",
                    )
                ),
            )
            self._report_to_log_text_only(
                "All found in import will be indexed only as errors.",
            )
            self._report_to_log_text_only("")
        else:
            self._report_to_log("Games with errors have been found in sample.")
            self._report_to_log_text_only(
                "All found in import will be indexed only as errors.",
            )
            self._report_to_log_text_only("")
        return True

    def _allow_time(self):
        """Ask is deferred update to proceed if game count is estimated.

        The time taken will vary significantly depending on environment.

        """
        if not self.estimate_data:
            return False
        seconds = (
            (self.estimate_data[0] + self.estimate_data[4])
            * self.estimate_data[9]
            * _DATABASE_UPDATE_FACTOR
        )
        minutes, seconds = divmod(round(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        duration = []
        if days:
            duration.append(str(days))
            duration.append("days")
            if hours:
                duration.append(str(hours))
                duration.append("hours")
        elif hours:
            duration.append(str(hours))
            duration.append("hours")
            if minutes:
                duration.append(str(minutes))
                duration.append("minutes")
        elif minutes:
            duration.append(str(minutes))
            duration.append("minutes")
            if seconds:
                duration.append(str(seconds))
                duration.append("seconds")
        elif seconds > 1:
            duration.append(str(seconds))
            duration.append("seconds")
        else:
            duration.append(str(1))
            duration.append("second")
        self._report_to_log(
            "".join(
                (
                    "The estimate is the time taken to process the sample ",
                    "scaled up to the estimated number of games then ",
                    "multiplied by ",
                    str(_DATABASE_UPDATE_FACTOR),
                    ".  Expect the import to take longer if the database ",
                    "already contains games: the effect is worse for smaller "
                    "imports.  Progress reports are made if the import is ",
                    "large enough.",
                )
            )
        )
        self._report_to_log_text_only("")
        self._report_to_log(
            "".join(
                ("The import is expected to take ", " ".join(duration), ".")
            )
        )
        return True

    def _get_pgn_file_estimates(self):
        """Return the estimates of object counts for a PGN file."""
        return self.estimate_data


class ChessDeferredUpdate(Bindings):
    """Connect a chess database with User Interface for deferred update."""

    def __init__(
        self, deferred_update_method=None, database_class=None, sample=5000
    ):
        """Create the database and ChessUI objects.

        deferred_update_method - the method to do the import
        database_class - access the database with an instance of this class
        sample - estimate size of import from first 'sample' games in PGN file

        """
        super().__init__()
        self.report_queue = multiprocessing.Queue()
        self.quit_event = multiprocessing.Event()
        self.dumethod = deferred_update_method
        self.sample = sample
        self._import_done = False
        self._import_job = None
        self._task_name = "estimating"
        self.database = database_class(
            sys.argv[1], allowcreate=True, deferupdatefiles={GAMES_FILE_DEF}
        )

        self.root = tkinter.Tk()
        self.root.wm_title(
            " - ".join(
                (
                    " ".join((APPLICATION_NAME, "Import")),
                    os.path.basename(sys.argv[1]),
                )
            )
        )
        frame = tkinter.Frame(master=self.root)
        frame.pack(side=tkinter.BOTTOM)
        # Not yet sure 'self.buttonframe' should become 'buttonframe'.
        self.buttonframe = tkinter.Frame(master=frame)
        self.buttonframe.pack(side=tkinter.BOTTOM)
        tkinter.Button(
            master=self.buttonframe,
            text="Dismiss Log",
            underline=0,
            command=self.try_command(
                self._dismiss_import_log,
                self.buttonframe,
            ),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Stop Process",
            underline=0,
            command=self.try_command(
                self._stop_task,
                self.buttonframe,
            ),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Import",
            underline=0,
            command=self.try_command(self._do_import, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)

        self.report = LogTextBase(
            master=self.root,
            cnf=dict(wrap=tkinter.WORD, undo=tkinter.FALSE),
        )
        self.report.focus_set()
        self.bind(
            self.report,
            "<Alt-i>",
            function=self.try_event(self._do_import),
        )
        self.bind(
            self.report,
            "<Alt-d>",
            function=self.try_event(
                self._dismiss_import_log,
            ),
        )
        self.bind(
            self.report,
            "<Alt-s>",
            function=self.try_event(self._stop_task),
        )
        self.database.add_import_buttons(
            self.buttonframe,
            self.try_command,
            self.try_event,
            self.bind,
            self.report,
        )

        self.report.tag_configure(
            "margin",
            lmargin2=tkinter.font.nametofont(self.report.cget("font")).measure(
                "2010-05-23 10:20:57  "
            ),
        )
        self.tagstart = "1.0"
        self._report_to_log(
            "".join(("Importing to database ", sys.argv[1], "."))
        )
        self._report_to_log_text_only(
            "All times quoted assume no other applications running.",
        )
        self._report_to_log_text_only("")
        self._report_to_log("Estimating number of games in import.")
        self.report.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE
        )
        self.root.iconify()
        self.root.update()
        self.root.deiconify()
        self._allow_job = False
        self.deferred_update = DeferredUpdateEstimateProcess(
            self.database,
            self.sample,
            self.report_queue,
            self.quit_event,
        )
        self.deferred_update.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_estimate_join
        )
        self.quit_thread.start()
        self._add_queued_reports_to_log()
        self.root.mainloop()

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, time = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        time = time.split(".")[0]
        self.report_queue.put("".join((day, " ", time, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _add_queued_reports_to_log(self):
        """Check report queue every 200ms and add reports to log."""
        # Items are put on queue infrequently relative to polling, so testing
        # the unreliable qsize() value is worthwhile because it will usually
        # be 0 thus avoiding the Empty exception.
        while self.report_queue.qsize():
            try:
                self.report.append_raw_text(self.report_queue.get_nowait())
            except queue.Empty:
                pass
        self.root.after(200, self._add_queued_reports_to_log)

    def _deferred_update_estimate_join(self):
        """join() deferred_update process then allow quit."""
        self.deferred_update.process.join()
        self._allow_job = True

    def _deferred_update_join(self):
        """join() deferred_update process then allow quit."""
        self.deferred_update.process.join()
        self._allow_job = True
        self._import_done = True

    def _do_import(self, event=None):
        """Run import process if allowed and not already run.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if not self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Import",
                message="".join(
                    (
                        "Cannot start import because a task is in progress",
                        ".\n\nThe current task must be allowed to finish, ",
                        "or be stopped, before starting task.",
                    )
                ),
            )
            return
        if self._import_done:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Import",
                message="".join(
                    (
                        "The import has been done.",
                        "\n\nDismiss Log and start again to repeat it or ",
                        "do another one.",
                    )
                ),
            )
            return
        if not tkinter.messagebox.askokcancel(
            parent=self.root,
            title="Import",
            message="".join(("Please confirm the import is to be started.",)),
        ):
            return
        self._allow_job = False
        self._task_name = "import"
        self.quit_event.clear()
        self.deferred_update = DeferredUpdateProcess(
            self.database,
            self.dumethod,
            self.report_queue,
            self.quit_event,
        )
        self.deferred_update.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_join
        )
        self.quit_thread.start()

    # Override ChessException method as ChessUI class is not used.
    # May be wrong now solentware_misc Bindings is used.
    def get_error_file_name(self):
        """Return the exception report file name."""
        return os.path.join(sys.argv[1], ERROR_LOG)

    def _stop_task(self, event=None):
        """Stop task.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Stop",
                message="No task running to be stopped.",
            )
            return
        if not tkinter.messagebox.askokcancel(
            parent=self.root,
            title="Stop",
            message=self._task_name.join(
                ("Please confirm the ", " task is to be stopped.")
            ),
        ):
            return
        self.quit_event.set()

    def _dismiss_import_log(self, event=None):
        """Dismiss log display and quit process.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if not self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Dismiss",
                message="".join(
                    (
                        "Cannot dismiss because a task is in progress",
                        ".\n\nThe current task must be allowed to finish, ",
                        "or be stopped, before dismissing.",
                    )
                ),
            )
            return
        if tkinter.messagebox.askyesno(
            parent=self.root,
            title="Dismiss",
            message="Do you want to dismiss the import log?",
        ):
            self.root.destroy()


def write_error_to_log():
    """Write the exception to the error log with a time stamp."""
    with open(os.path.join(sys.argv[1], ERROR_LOG), "a") as file:
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
