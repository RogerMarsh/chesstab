# chessdu.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define User Interface for deferred update process.
"""

import sys
import os
import traceback
import datetime
import tkinter
import tkinter.font
import tkinter.messagebox
import queue
import time

from solentware_misc.core import callthreadqueue
from solentware_misc.gui.tasklog import LogText
from solentware_misc.gui.exceptionhandler import ExceptionHandler

from pgn_read.core.parser import PGN

from ..core.pgn import GameUpdateEstimate
from .. import (
    ERROR_LOG,
    APPLICATION_NAME,
)
from ..core.filespec import GAMES_FILE_DEF
from .fonts import _get_default_font_actual

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


class ChessDeferredUpdate(ExceptionHandler):
    """Connect a chess database with User Interface for deferred update."""

    def __init__(
        self, deferred_update_method=None, database_class=None, sample=5000
    ):
        """Create the database and ChessUI objects.

        deferred_update_method - the method to do the import
        database_class - access the database with an instance of this class
        sample - estimate size of import from first 'sample' games in PGN file

        """
        super(ChessDeferredUpdate, self).__init__()
        self.queue = callthreadqueue.CallThreadQueue()
        self.reportqueue = queue.Queue(maxsize=1)

        self.dumethod = deferred_update_method
        self.sample = sample
        self.estimate_data = None
        self._allow_job = None
        self._import_job = None
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
        self.buttonframe = tkinter.Frame(master=frame)
        self.buttonframe.pack(side=tkinter.BOTTOM)

        # See comment near end of this class definition for explanation of this
        # change.  It was simpler to display all the buttons at once and add
        # some control logic, than wrap the things in a task queue for the main
        # thread to process.  But the presence or absence of the buttons should
        # be the control logic.
        self._quit_message = "".join(
            (
                "The import has not been started.",
                "\n\nDo you want to abandon the import?",
            )
        )
        self.cancel = tkinter.Button(
            master=self.buttonframe,
            # text='Cancel',
            text="Quit",
            underline=0,
            command=self.try_command(
                # self.quit_before_import_started, self.buttonframe))
                self.quit_import,
                self.buttonframe,
            ),
        )
        self.cancel.pack(side=tkinter.RIGHT, padx=12)
        backup = tkinter.Button(
            master=self.buttonframe,
            text="Import with Backups",
            underline=12,
            command=self.try_command(
                self.do_import_with_backup, self.buttonframe
            ),
        )
        backup.pack(side=tkinter.RIGHT, padx=12)
        import_ = tkinter.Button(
            master=self.buttonframe,
            text="Import",
            underline=0,
            command=self.try_command(
                self.do_import_without_backup, self.buttonframe
            ),
        )
        import_.pack(side=tkinter.RIGHT, padx=12)

        # See comment near end of this class definition for explanation of this
        # change.  Replacing Text by LogText fixes the majority of the problems.
        # Consequential changes, self.append_text to self.report.append_text
        # mainly, are not marked.
        # Added 07 August 2016:
        # _get_default_font_actual() value used as cnf to avoid picking fonts
        # like 'Chess Cases' as default font when running under Wine from
        # ~/.wine/drive_c/windows/Fonts or /usr/local/share/fonts.
        # The cnf is not needed under Microsoft Windows or unix-like OS.
        self.report = LogText(
            master=self.root,
            wrap=tkinter.WORD,
            undo=tkinter.FALSE,
            get_app=self,
            cnf=_get_default_font_actual(tkinter.Text),
        )
        self.report.focus_set()
        self.report.bind("<Alt-b>", self.try_event(self.do_import_with_backup))
        self.report.bind(
            "<Alt-i>", self.try_event(self.do_import_without_backup)
        )
        self.report.bind("<Alt-q>", self.try_event(self.quit_import))
        self.database.add_import_buttons(
            self.buttonframe, self.try_command, self.try_event, self.report
        )

        self.report.tag_configure(
            "margin",
            lmargin2=tkinter.font.nametofont(self.report.cget("font")).measure(
                "2010-05-23 10:20:57  "
            ),
        )
        self.tagstart = "1.0"
        self.report.append_text(
            "".join(("Importing to database ", sys.argv[1], "."))
        )
        self.report.append_text(
            "All times quoted assume no other applications running.",
            timestamp=False,
        )
        self.report.append_text_only("")
        self.report.append_text("Estimating number of games in import.")
        self.report.append_text_only("")
        self.report.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE
        )
        self.root.iconify()
        self.root.update()
        self.root.deiconify()
        self.__run_ui_task_from_queue(1000)
        self.root.after(100, self.try_command(self.run_allow, self.root))
        self.root.mainloop()

    def allow_import(self):
        """Do checks for database engine and return True if import allowed."""

        # The close_database() in finally clause used to be the first statement
        # after runjob() definition in run_import() method.  An exception was
        # raised using the sqlite3 module because run_input() is run in a
        # different thread from allow_input().  Earlier versions of chessdu did
        # not attempt to close the connection, hiding the problem.
        # The apsw module did not raise an exception, nor did modules providing
        # an interface to Berkeley DB or DPT.
        self.database.open_database()
        try:
            if not self.estimate_games_in_import():
                self.report.append_text("There are no games to import.")
                self.report.append_text_only("")
                return None
            if self.allow_time():
                self.database.report_plans_for_estimate(
                    self.get_pgn_file_estimates(), self.report
                )
                return True
            self.report.append_text("Unable to estimate time to do import.")
            self.report.append_text_only("")
            return False
        finally:
            self.database.close_database()

    def allow_time(self):
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
        self.report.append_text(
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
        self.report.append_text_only("")
        self.report.append_text(
            "".join(
                ("The import is expected to take ", " ".join(duration), ".")
            )
        )
        self.report.append_text_only("")
        return True

    def do_import_with_backup(self, event=None):
        """Run import thread if allowed and not already run.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        if self._import_job:
            return
        names, exists = self.database.get_archive_names(
            files=(GAMES_FILE_DEF,)
        )
        if exists:
            if not tkinter.messagebox.askokcancel(
                parent=self.root,
                title="Import Backup",
                message="".join(
                    (
                        "Import backups of the following files already exist.\n\n",
                        "\n".join(exists),
                        "\n\nThis may mean an earlier Import action failed and ",
                        'has not yet been resolved.\n\nClick "Ok" to delete ',
                        "these backups and create new ones before doing the ",
                        "Import.  These backups will be deleted if the Import ",
                        "succeeds.\n\nClick ",
                        '"Cancel" to leave things as they are.',
                    )
                ),
            ):
                return
            self.report.append_text(
                "Backups will be taken before doing the import."
            )
            self.report.append_text(
                "These backups will replace the existing backups.",
                timestamp=False,
            )
        elif not tkinter.messagebox.askokcancel(
            parent=self.root,
            title="Import Backup",
            message="".join(
                ("Please confirm the import is to be done with backups.",)
            ),
        ):
            return
        else:
            self.report.append_text(
                "Backups will be taken before doing the import."
            )
        self.report.append_text(
            "These backups will be deleted if the import succeeds.",
            timestamp=False,
        )
        self.report.append_text_only("")
        self.run_import(backup=True, names=names)

    def do_import_without_backup(self, event=None):
        """Run import thread if allowed and not already run.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        if self._import_job:
            return
        names, exists = self.database.get_archive_names(
            files=(GAMES_FILE_DEF,)
        )
        if exists:
            if not tkinter.messagebox.askokcancel(
                parent=self.root,
                title="Import Backup",
                message="".join(
                    (
                        "Import backups of the following files already exist.\n\n",
                        "\n".join(exists),
                        "\n\nThis may mean an earlier Import action failed and ",
                        'has not yet been resolved.\n\nClick "Ok" to delete ',
                        "these backups and create new ones before doing the ",
                        "Import.  These backups will be deleted if the Import ",
                        "succeeds.\n\nClick ",
                        '"Cancel" to leave things as they are.',
                    )
                ),
            ):
                return
            self.report.append_text(
                "The import will be done without taking backups."
            )
            self.report.append_text_only("")
            self.report.append_text(
                "Existing backups will be deleted before doing the import.",
                timestamp=False,
            )
            self.report.append_text_only("")
        elif not tkinter.messagebox.askokcancel(
            parent=self.root,
            title="Import Backup",
            message="".join(
                ("Please confirm the import is to be done without backups.",)
            ),
        ):
            return
            self.report.append_text(
                "The import will be done without taking backups."
            )
            self.report.append_text_only("")
        self.run_import(backup=False, names=names)

    def estimate_games_in_import(self):
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
        for pp in sys.argv[2:]:
            if gamecount + errorcount >= self.sample:
                estimate = True
                break
            source = open(pp, "r", encoding="iso-8859-1")
            try:
                for rcg in reader.read_games(source):
                    if gamecount + errorcount >= self.sample:
                        estimate = True
                        break
                    if len(rcg._text):
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
            finally:
                source.close()
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
            self.report.append_text(
                " ".join(("Estimated Games:", str(self.estimate_data[0])))
            )
            self.report.append_text(
                " ".join(("Estimated Errors:", str(self.estimate_data[4]))),
                timestamp=False,
            )
            self.report.append_text(
                " ".join(("Sample Games:", str(gamecount))), timestamp=False
            )
            self.report.append_text(
                " ".join(("Sample Errors:", str(errorcount))), timestamp=False
            )
        else:
            self.report.append_text(
                "The import is small so all games are counted."
            )
            self.report.append_text(
                " ".join(("Games in import:", str(gamecount))), timestamp=False
            )
            self.report.append_text(
                " ".join(("Errors in import:", str(errorcount))),
                timestamp=False,
            )
        self.report.append_text(
            " ".join(("Bytes per game:", str(bytes_per_game))), timestamp=False
        )
        self.report.append_text(
            " ".join(("Bytes per error:", str(bytes_per_error))),
            timestamp=False,
        )
        self.report.append_text(
            " ".join(("Positions per game:", str(positions_per_game))),
            timestamp=False,
        )

        # positions_per_game == 0 if there are no valid games.
        ppp = "Not a number"
        for c, t in (
            (pieces_per_game, "Pieces per position:"),
            (piecetypes_per_game, "Piece types per position:"),
        ):
            if positions_per_game:
                ppp = str(c // positions_per_game)
            self.report.append_text(" ".join((t, ppp)), timestamp=False)
        self.report.append_text("", timestamp=False)

        # Check if import can proceed
        if gamecount + errorcount == 0:
            self.report.append_text(
                "No games, or games with errors, found in import."
            )
            return False
        if errorcount == 0:
            if estimate:
                self.report.append_text("No games with errors in sample.")
                self.report.append_text(
                    " ".join(
                        (
                            "It is estimated no games with",
                            "errors exist in import.",
                        )
                    ),
                    timestamp=False,
                )
                self.report.append_text(
                    "Any found in import will be indexed only as errors.",
                    timestamp=False,
                )
            else:
                self.report.append_text("No games with errors in import.")
            self.report.append_text_only("")
        elif estimate:
            self.report.append_text(
                "Games with errors have been found in sample."
            )
            self.report.append_text(
                " ".join(
                    (
                        "The sample is the first",
                        str(self.sample),
                        "games in import.",
                    )
                ),
                timestamp=False,
            )
            self.report.append_text(
                "All found in import will be indexed only as errors.",
                timestamp=False,
            )
            self.report.append_text_only("")
        else:
            self.report.append_text(
                "Games with errors have been found in sample."
            )
            self.report.append_text(
                "All found in import will be indexed only as errors.",
                timestamp=False,
            )
            self.report.append_text_only("")
        return bool(self.estimate_data)

    # Override ChessException method as ChessUI class is not used.
    # May be wrong now solentware_misc ExceptionHandler is used.
    def get_error_file_name(self):
        """Return the exception report file name."""
        return os.path.join(sys.argv[1], ERROR_LOG)

    def get_pgn_file_estimates(self):
        return self.estimate_data

    def quit_after_import_started(self):
        """Quit process after import has started."""
        if tkinter.messagebox.askyesno(
            parent=self.root,
            title="Abandon Import",
            message="".join(
                (
                    "The import has been started.\n\n",
                    APPLICATION_NAME,
                    " will attempt ",
                    "to restore the files using the backups if they were taken.",
                    "\n\nDo you want to abandon the import?",
                )
            ),
        ):
            self.root.destroy()

    def quit_import(self, event=None):
        """Quit process.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        if tkinter.messagebox.askyesno(
            parent=self.root, title="Quit Import", message=self._quit_message
        ):
            self.root.destroy()

    def run_allow(self):
        """Run import thread if allowed and not already run."""
        if self._allow_job:
            return
        self._allow_job = True
        self.queue.put_method(self.try_thread(self.allow_import, self.root))

    def run_import(self, backup=None, names=None):
        """Invoke method to do the deferred update and display job status.

        backup - the answer given to the 'take backups' prompt
        names - the files to backup if requested

        Closing the job status widget terminates the job.

        """
        if self._import_job:
            return

        def runjob(*a):
            try:
                if backup:
                    self.report.append_text("Taking backups.")
                    if self.database.archive(flag=backup, names=names) is None:
                        self.report.append_text("Taking backups abandonned")
                        self.report.append_text(
                            "".join(
                                (
                                    "The existing backup does not look like a ",
                                    APPLICATION_NAME,
                                    " backup.",
                                )
                            ),
                            timestamp=False,
                        )
                        self.report.append_text_only("")
                        # self.cancel.configure(
                        #    command=self.try_command(
                        #        self.quit_before_import_started, self.cancel))
                        self._quit_message = "".join(
                            (
                                "The import has not been started.",
                                "\n\nDo you want to abandon the import?",
                            )
                        )
                        return
                    self.report.append_text("Backups saved.")
                    self.report.append_text_only("")
                self.report.append_text("Import started.")
                self.report.append_text_only("")
                status = False
                try:
                    status = self.dumethod(*a)
                except:
                    write_error_to_log()
                self.report.append_text("Import finished.")
                self.report.append_text_only("")
                if not status:
                    if backup:
                        self.report.append_text(
                            "".join(
                                (
                                    "Problem encountered doing import. Backups are ",
                                    "retained for recovery.",
                                )
                            )
                        )
                    else:
                        self.report.append_text(
                            "".join(
                                (
                                    "Problem encountered doing import. No backups ",
                                    "available.",
                                )
                            )
                        )
                    self.report.append_text_only(
                        "".join(("See ", ERROR_LOG, " for details."))
                    )
                elif backup:
                    self.report.append_text("Deleting backups.")
                    if (
                        self.database.delete_archive(flag=backup, names=names)
                        is None
                    ):
                        self.report.append_text("Deleting backups abandonned.")
                        self.report.append_text_only(
                            "".join(
                                (
                                    "The existing backup does not look like a ",
                                    APPLICATION_NAME,
                                    " backup.",
                                )
                            )
                        )
                    else:
                        self.report.append_text("Backups deleted.")
                # self.cancel.configure(
                #    command=self.try_command(
                #        self.quit_after_import_finished, self.cancel),
                #    text='Quit')
                self._quit_message = "".join(
                    (
                        "The import has been completed.",
                        "\n\nDo you want to dismiss the import log?",
                    )
                )
            except:
                try:
                    write_error_to_log()
                except:
                    pass

        self._import_job = True
        self.queue.put_method(
            self.try_thread(runjob, self.root),
            args=(
                sys.argv[1],
                sys.argv[2:],
                self.database.get_file_sizes(),
                self.report.append_text,
            ),
        )

    # Methods __call__, get_reportqueue, __run_ui_task_from_queue, and
    # get_thread_queue, introduced to allow this module to work if tkinter is
    # compiled without --enable-threads as in OpenBSD 5.7 i386 packages.  The
    # standard build from FreeBSD ports until early 2015 at least, when this
    # change was introduced, is compiled with --enable-threads so the unchanged
    # code worked.  Not sure if the change in compiler on FreeBSD from gcc to
    # clang made a difference.  The Microsoft Windows' Pythons seem to be
    # compiled with --enable-threads because the unchanged code works in that
    # environment.  The situation on OS X, and any GNU-Linux distribution, is
    # not known.

    # Code in the solentware_misc.gui.tasklog module already dealt with this
    # problem, so the minimum necessary was copied to here.  The classes in
    # tasklog are modified versions of code present in this module before this
    # change.

    def __call__(self):
        """ """
        return self

    def get_reportqueue(self):
        """ """
        return self.reportqueue

    def get_thread_queue(self):
        """ """
        return self.queue

    def __run_ui_task_from_queue(self, interval):
        """Do all queued tasks then wake-up after interval"""
        while True:
            try:
                method, args, kwargs = self.reportqueue.get_nowait()
                method(*args, **kwargs)
            except queue.Empty:
                self.root.after(
                    interval,
                    self.try_command(self.__run_ui_task_from_queue, self.root),
                    *(interval,)
                )
                break
            self.reportqueue.task_done()


def write_error_to_log():
    """Write the exception to the error log with a time stamp."""
    f = open(os.path.join(sys.argv[1], ERROR_LOG), "a")
    try:
        f.write(
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
    finally:
        f.close()
