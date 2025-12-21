# chessdu.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define User Interface for deferred update process."""

import os
import datetime
import tkinter
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog
import queue
import multiprocessing
import multiprocessing.dummy
import shutil

from solentware_misc.gui.logtextbase import LogTextBase

from solentware_bind.gui.bindings import Bindings

from pgn_read.core.tagpair_parser import PGNTagPair, GameCount

from solentware_base.core.constants import (
    BRECPPG,
    DEFAULT_RECORDS,
)

from ..core import constants
from ..core import utilities
from .. import (
    ERROR_LOG,
    APPLICATION_NAME,
)
from ..core.filespec import (
    GAMES_FILE_DEF,
    PGNFILE_FIELD_DEF,
    BTOD_FACTOR,
    IMPORT_FIELD_DEF,
    GAME_FIELD_DEF,
    POSITIONS_FIELD_DEF,
    PIECESQUARE_FIELD_DEF,
)

_GAMECOUNT_REPORT_INTERVAL = 1000000


class _FileLogTextBase(LogTextBase):
    """Save log text on logfile."""

    def __init__(self, logfile=None, **kargs):
        super().__init__(**kargs)
        if logfile is None:
            self.logfile = None
            return
        self.logfile = os.path.join(
            logfile, os.path.basename(logfile) + "-log.txt"
        )
        with open(self.logfile, "w", encoding="utf-8") as file:
            del file

    def append_bytestring(self, *args, **kargs):
        """Delegate then write to _logfile if requested."""
        end = self.index(tkinter.END + "-1l")
        super().append_bytestring(*args, **kargs)
        self._add_to_logfile(end)

    def append_text(self, *args, **kargs):
        """Delegate then write to _logfile if requested."""
        end = self.index(tkinter.END + "-1l")
        super().append_text(*args, **kargs)
        self._add_to_logfile(end)

    def append_raw_text(self, *args, **kargs):
        """Delegate then write to _logfile if requested."""
        end = self.index(tkinter.END + "-1l")
        super().append_raw_text(*args, **kargs)
        self._add_to_logfile(end)

    def _add_to_logfile(self, end):
        if self.logfile is None:
            return
        with open(self.logfile, "a", encoding="utf-8") as file:
            file.write(self.get(end, tkinter.END + "-1c"))


class _Reporter:
    """Helper class to keep 'LogText' API for adding text to log.

    Not used in dptcompatdu module but is used in dpt.database_du module.

    """

    def __init__(self, append_text, append_text_only, empty):
        """Note the timestamp plus text, and text only, append methods."""
        self.append_text = append_text
        self.append_text_only = append_text_only
        self.empty = empty


class IncreaseDataProcess:
    """Define a process to do an increase data size (table B) process."""

    def __init__(self, database, report_queue, quit_event):
        """Provide queues for communication with GUI."""
        self.database = database
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.process = multiprocessing.Process(
            target=self._increase_data_size,
            args=(),
        )
        self.stop_thread = None

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        hms = hms.split(".")[0]
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _increase_data_size(self):
        """Increase data size."""
        self.stop_thread = multiprocessing.dummy.DummyProcess(
            target=self._wait_for_quit_event
        )
        self.stop_thread.start()
        self._increase()
        self.quit_event.set()

    def _wait_for_quit_event(self):
        """Wait for quit event."""
        self.quit_event.wait()

    def _increase(self):
        """Increase data size in DPT games file."""
        database = self.database
        files = (GAMES_FILE_DEF,)
        database.open_context_prepare_import(files=files)
        try:
            parameter = database.get_database_parameters(files=files)[
                GAMES_FILE_DEF
            ]
            bsize = parameter["BSIZE"]
            bused = max(0, parameter["BHIGHPG"])
            bfree = bsize - bused
            dsize = parameter["DSIZE"]
            dused = parameter["DPGSUSED"]
            dfree = dsize - dused
            table = database.table[GAMES_FILE_DEF]
            specification = database.specification[GAMES_FILE_DEF]
            default_records = specification[DEFAULT_RECORDS]
            btod_factor = specification[BTOD_FACTOR]
            brecppg = table.filedesc[BRECPPG]
            bdefault = database.get_pages_for_record_counts(
                (default_records, default_records)
            )[0]
            bfree_recs = bfree * brecppg
            dfree_recs = (dfree * brecppg) // btod_factor
            blow = bfree + min(bdefault, bfree)
            bhigh = bfree + max(bdefault, bfree)
            blowrecs = bfree_recs + min(default_records, bfree_recs)
            bhighrecs = bfree_recs + max(default_records, bfree_recs)
            if len(table.get_extents()) % 2 == 0:
                if not tkinter.messagebox.askokcancel(
                    title="Increase Data Size",
                    message="".join(
                        (
                            "At present it is better to do index ",
                            "increases first for this file, if any ",
                            "are needed.\n\nIt is estimated the ",
                            "current index size can cope with an ",
                            "estimated extra ",
                            str(dfree_recs),
                            " games.\n\nPlease confirm you wish to ",
                            "continue with data increase.",
                        )
                    ),
                ):
                    return
            if blow != bhigh:
                choice = tkinter.messagebox.askyesnocancel(
                    title="Increase Data Size",
                    message="".join(
                        (
                            "Please choose between a data size increase ",
                            "to cope with an estimated extra ",
                            str(blowrecs),
                            " or ",
                            str(bhighrecs),
                            " games.\n\nThe current data size can cope ",
                            "with an estimated extra ",
                            str(bfree_recs),
                            " games.\n\nDo you want to increase the data ",
                            "size for the smaller number of games?",
                        )
                    ),
                )
                if choice is True:  # Yes
                    bincrease = blow - bfree
                    bextrarecs = blowrecs
                elif choice is False:  # No
                    bincrease = bhigh - bfree
                    bextrarecs = bhighrecs
                else:  # Cancel assumed (choice is None).
                    return
            else:
                choice = tkinter.messagebox.askokcancel(
                    title="Increase Data Size",
                    message="".join(
                        (
                            "Please confirm a data size increase ",
                            "to cope with an estimated extra ",
                            str(blowrecs),
                            " games.\n\nThe current data size can cope ",
                            "with an estimated extra ",
                            str(bfree_recs),
                            " games.",
                        )
                    ),
                )
                if choice is True:  # Yes
                    bincrease = blow - bfree
                    bextrarecs = blowrecs
                else:  # Cancel assumed (choice is None).
                    return
            table.opencontext.Increase(bincrease, False)
            self._report_to_log_text_only("")
            self._report_to_log("Data size increased.")
            self._report_to_log_text_only(
                " ".join(
                    (
                        "Estimate of standard profile games which fit:",
                        str(bextrarecs),
                    )
                )
            )
        finally:
            database.close_database()


class IncreaseIndexProcess:
    """Define a process to do an increase index size (table D) process."""

    def __init__(self, database, report_queue, quit_event):
        """Provide queues for communication with GUI."""
        self.database = database
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.process = multiprocessing.Process(
            target=self._increase_index_size,
            args=(),
        )
        self.stop_thread = None

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        hms = hms.split(".")[0]
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _increase_index_size(self):
        """Increase index size."""
        self.stop_thread = multiprocessing.dummy.DummyProcess(
            target=self._wait_for_quit_event
        )
        self.stop_thread.start()
        self._increase()
        self.quit_event.set()

    def _wait_for_quit_event(self):
        """Wait for quit event."""
        self.quit_event.wait()

    def _increase(self):
        """Increase index size in DPT games file."""
        database = self.database
        files = (GAMES_FILE_DEF,)
        database.open_context_prepare_import(files=(GAMES_FILE_DEF,))
        try:
            parameter = database.get_database_parameters(files=files)[
                GAMES_FILE_DEF
            ]
            bsize = parameter["BSIZE"]
            bused = max(0, parameter["BHIGHPG"])
            bfree = bsize - bused
            dsize = parameter["DSIZE"]
            dused = parameter["DPGSUSED"]
            dfree = dsize - dused
            table = database.table[GAMES_FILE_DEF]
            specification = database.specification[GAMES_FILE_DEF]
            default_records = specification[DEFAULT_RECORDS]
            btod_factor = specification[BTOD_FACTOR]
            brecppg = table.filedesc[BRECPPG]
            ddefault = database.get_pages_for_record_counts(
                (default_records, default_records)
            )[1]
            bfree_recs = bfree * brecppg
            dfree_recs = (dfree * brecppg) // btod_factor
            dlow = dfree + min(ddefault, dfree)
            dhigh = dfree + max(ddefault, dfree)
            dlowrecs = dfree_recs + min(default_records, dfree_recs)
            dhighrecs = dfree_recs + max(default_records, dfree_recs)
            if len(table.get_extents()) % 2 != 0:
                if not tkinter.messagebox.askokcancel(
                    title="Increase Index Size",
                    message="".join(
                        (
                            "At present it is better to do data ",
                            "increases first for this file, if any ",
                            "are needed.\n\nIt is estimated the ",
                            "current data size can cope with an ",
                            "estimated extra ",
                            str(bfree_recs),
                            " games.\n\nPlease confirm you wish to ",
                            "continue with index increase.",
                        )
                    ),
                ):
                    return
            if dlow != dhigh:
                choice = tkinter.messagebox.askyesnocancel(
                    title="Increase Index Size",
                    message="".join(
                        (
                            "Please choose between an index size increase ",
                            "to cope with an estimated extra ",
                            str(dlowrecs),
                            " or ",
                            str(dhighrecs),
                            " games.\n\nThe current index size can cope ",
                            "with an estimated extra ",
                            str(dfree_recs),
                            " games.\n\nDo you want to increase the index ",
                            "size for the smaller number of games?",
                        )
                    ),
                )
                if choice is True:  # Yes
                    dincrease = dlow - dfree
                    dextrarecs = dlowrecs
                elif choice is False:  # No
                    dincrease = dhigh - dfree
                    dextrarecs = dhighrecs
                else:  # Cancel assumed (choice is None).
                    return
            else:
                choice = tkinter.messagebox.askokcancel(
                    title="Increase Index Size",
                    message="".join(
                        (
                            "Please confirm an index size increase ",
                            "to cope with an estimated extra ",
                            str(dlowrecs),
                            " games.\n\nThe current index size can cope ",
                            "with an estimated extra ",
                            str(dfree_recs),
                            " games.",
                        )
                    ),
                )
                if choice is True:  # Yes
                    dincrease = dlow - dfree
                    dextrarecs = dlowrecs
                else:  # Cancel assumed (choice is None).
                    return
            table.opencontext.Increase(dincrease, True)
            self._report_to_log_text_only("")
            self._report_to_log("Index size increased.")
            self._report_to_log_text_only(
                " ".join(
                    (
                        "Estimate of standard profile games which fit:",
                        str(dextrarecs),
                    )
                )
            )
        finally:
            database.close_database()


class DeferredUpdateProcess:
    """Define a process to do a deferred update task."""

    def __init__(
        self,
        database,
        method,
        report_queue,
        quit_event,
        increases,
        home_directory,
        pgnfiles,
    ):
        """Provide queues for communication with GUI."""
        self.database = database
        self.method = method
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.increases = increases
        self.home_directory = home_directory
        self.pgnfiles = pgnfiles
        self.process = multiprocessing.Process(
            target=self._run_import,
            args=(),
        )

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        hms = hms.split(".")[0]
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _run_import(self):
        """Invoke method to do the deferred update and display job status."""
        self.method(
            self.home_directory,
            self.pgnfiles,
            file=GAMES_FILE_DEF,
            reporter=_Reporter(
                self._report_to_log,
                self._report_to_log_text_only,
                self.report_queue.empty,
            ),
            quit_event=self.quit_event,
            increases=self.increases,
            ignore=set((IMPORT_FIELD_DEF, PGNFILE_FIELD_DEF)),
        )


class DeferredUpdateEstimateProcess:
    """Define a process to do a deferred update estimate task."""

    def __init__(
        self,
        database,
        report_queue,
        quit_event,
        increases,
        pgnfiles,
    ):
        """Provide queues for communication with GUI."""
        self.database = database
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.increases = increases
        self.estimate_data = None
        self.pgnfiles = pgnfiles
        self.process = multiprocessing.Process(
            target=self._allow_import,
            args=(),
        )
        self.stop_thread = None

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        hms = hms.split(".")[0]
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

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
        database = self.database
        database.open_database()
        try:
            indicies = (
                GAME_FIELD_DEF,
                POSITIONS_FIELD_DEF,
                PIECESQUARE_FIELD_DEF,
            )
            game_count = 0
            database.start_read_only_transaction()
            try:
                for index in indicies:
                    index_games = database.recordlist_key(
                        GAMES_FILE_DEF,
                        IMPORT_FIELD_DEF,
                        key=database.encode_record_selector(index),
                    )
                    try:
                        game_count = max(
                            game_count, index_games.count_records()
                        )
                    finally:
                        index_games.close()
            finally:
                database.end_read_only_transaction()
            if game_count > 0:
                self.estimate_data = True
                self._report_to_log(
                    "Extract already done: skip count games scan."
                )
                self._report_to_log_text_only(
                    str(game_count) + " games were extracted."
                )
            elif not self._estimate_games_in_import():
                return None
            if self._allow_time():
                self.quit_event.set()
                return True
            self._report_to_log("Unable to verify import request.")
            self._report_to_log_text_only("")
            return False
        finally:
            database.close_database()

    def _estimate_games_in_import(self):
        """Estimate import size from file sizes reported by operating system.

        Method name is from earlier version which processed the first games
        found, default 5000, and assumed rest of games look similar.

        The total size is a byte count which is assumed to be not much
        larger than the character count because the PGN standard expects
        iso-8859-1 encoding.  Many files will be ascii or utf-8 encoding
        where the later will introduce some multi-byte characters.

        """
        reader = PGNTagPair(game_class=GameCount)
        self.estimate_data = False
        total_byte_size = 0
        total_char_size = 0
        total_error_byte_size = 0
        file_ok_count = 0
        gamecount = 0
        for pgnfile in self.pgnfiles:
            filebytes = os.path.getsize(pgnfile)
            for encoding in constants.ENCODINGS:
                filechars = []
                with open(pgnfile, mode="r", encoding=encoding) as source:
                    try:
                        while True:
                            chars = source.read(1024 * 1000)
                            filechars.append(len(chars))
                            if not chars:
                                file_ok_count += 1
                                break
                    except UnicodeDecodeError:
                        continue
                    total_char_size += sum(filechars)
                    total_byte_size += filebytes
                with open(pgnfile, mode="r", encoding=encoding) as source:
                    for _ in reader.read_games(source):
                        if self.quit_event.is_set():
                            self._report_to_log_text_only("")
                            self._report_to_log(
                                " ".join(
                                    (
                                        "Estimating task stopped when",
                                        format(gamecount, ","),
                                        "games found.",
                                    )
                                )
                            )
                            return False
                        gamecount += 1
                        if not gamecount % _GAMECOUNT_REPORT_INTERVAL:
                            self._report_to_log(
                                " ".join(
                                    (
                                        format(gamecount, ","),
                                        "games found. Scan continues ...",
                                    )
                                )
                            )
                if filechars:
                    break
            else:
                total_error_byte_size += filebytes
                self._report_to_log_text_only("")
                self._report_to_log(
                    " ".join(
                        (
                            "Unable to process",
                            pgnfile,
                            "as a",
                            " or ".join(constants.ENCODINGS),
                            "encoded file.",
                        )
                    )
                )
        if gamecount >= _GAMECOUNT_REPORT_INTERVAL:
            self._report_to_log_text_only("")
        if not total_error_byte_size:
            self._report_to_log(
                "".join(
                    (
                        "Import will proceed: all files ",
                        "can be processed.",
                    )
                )
            )
        self._report_to_log_text_only(
            " ".join(
                (
                    format(total_byte_size, ","),
                    "bytes will be processed.",
                )
            )
        )
        self._report_to_log_text_only(
            " ".join(
                (
                    format(total_char_size, ","),
                    "characters will be decoded from these bytes.",
                )
            )
        )
        if total_error_byte_size:
            self._report_to_log_text_only(
                " ".join(
                    (
                        format(total_error_byte_size, ","),
                        "bytes will not be processed.",
                    )
                )
            )

        # Check if import can proceed.
        if total_error_byte_size:
            self._report_to_log_text_only("")
            self._report_to_log(
                "".join(
                    (
                        "Import will not proceed: at least one file ",
                        "cannot be processed.",
                    )
                )
            )
            return False
        self._report_to_log_text_only(
            " ".join(
                (
                    format(file_ok_count, ","),
                    "file" if file_ok_count == 1 else "files",
                    "will be processed.",
                )
            )
        )
        self._report_to_log_text_only(
            " ".join(
                (
                    format(gamecount, ","),
                    "game" if gamecount == 1 else "games",
                    "found in",
                    format(len(self.pgnfiles), ","),
                    "file." if len(self.pgnfiles) == 1 else "files.",
                )
            )
        )
        database = self.database
        database.start_read_only_transaction()
        try:
            for pgnfile in self.pgnfiles:
                file_games = database.recordlist_key(
                    GAMES_FILE_DEF,
                    PGNFILE_FIELD_DEF,
                    key=database.encode_record_selector(
                        os.path.basename(pgnfile)
                    ),
                )
                file_count = file_games.count_records()
                file_games.close()
                if file_count:
                    self._report_to_log_text_only(
                        " ".join(
                            (
                                format(file_count, ","),
                                "game" if file_count == 1 else "games",
                                "from a file named",
                                os.path.basename(pgnfile),
                                "already on database.",
                            )
                        )
                    )
                    self._report_to_log_text_only(
                        "(Only missing game numbers will be copied)"
                    )
        finally:
            database.end_read_only_transaction()
        self.estimate_data = True
        return True

    def _allow_time(self):
        """Ask is deferred update to proceed if game count is estimated.

        The time taken will vary significantly depending on environment.

        """
        if not self.estimate_data:
            return False
        volfree = utilities.bytesize_to_str(
            shutil.disk_usage(self.database.database_file).free
        )
        dbsize = utilities.bytesize_to_str(
            os.path.getsize(self.database.database_file)
        )
        self._report_to_log_text_only("")
        self._report_to_log_text_only(
            "'Import' is quicker for small imports, but slower for large."
        )
        self._report_to_log_text_only(
            "".join(
                (
                    "'Merge Import' is quicker by a few minutes at 1 ",
                    "million games but by over 2 days at 10 million games.",
                )
            )
        )
        self._report_to_log_text_only(
            "(3Ghz CPU, 1600Mhz memory, <WDC WDS250G2B0A-00SM50> SSD.)"
        )
        self._report_to_log_text_only("")
        self._report_to_log_text_only(
            "".join((volfree, " is available for additions to database."))
        )
        self._report_to_log_text_only(
            "".join((dbsize, " is current size of database."))
        )
        self._report_to_log_text_only(
            "".join(
                (
                    "'Merge Import' needs space for sorting.  200 Gigabytes ",
                    "is enough for a 15 million game database, but not 30 ",
                    "million games.",
                )
            )
        )
        self._report_to_log_text_only(
            "'Import' is limited by available space."
        )
        self._report_to_log_text_only("")
        self._report_to_log_text_only(
            "Games with PGN tag or movetext errors will not be indexed."
        )
        self._report_to_log_text_only("")
        self._report_to_log("Ready to start import.")
        return True

    def _get_pgn_file_estimates(self):
        """Return the estimates of object counts for a PGN file."""
        return self.estimate_data


class DeferredUpdate(Bindings):
    """Connect a chess database with User Interface for deferred update."""

    def __init__(
        self,
        deferred_update_module=None,
        database_class=None,
        home_directory=None,
        resume=None,
        sort_area=None,
    ):
        """Create the database and User Interface objects.

        deferred_update_method - the method to do the import
        database_class - access the database with an instance of this class

        The deferred update module for each database engine will have one or
        more methods to do tasks as the target method of a multiprocessing
        Process: so these methods must have the same name in each module.

        """
        super().__init__()
        self.set_error_file_name(os.path.join(home_directory, ERROR_LOG))
        self.report_queue = multiprocessing.Queue()
        self.quit_event = multiprocessing.Event()
        self.increases = multiprocessing.Array("i", [0, 0, 0, 0])
        self.home_directory = home_directory
        self.resume = resume
        self.pgnfiles = None
        self.deferred_update_module = deferred_update_module
        self._import_done = False
        self._import_job = None
        self._task_name = "estimating"
        self.database = database_class(
            home_directory,
            allowcreate=True,
            deferupdatefiles={GAMES_FILE_DEF},
        )
        self.deferred_update = None
        self.quit_thread = None

        self.root = tkinter.Tk()
        self.root.wm_title(
            " - ".join(
                (
                    " ".join((APPLICATION_NAME, "Import")),
                    os.path.basename(home_directory),
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
            command=self.try_command(self._stop_task, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Import",
            underline=0,
            command=self.try_command(self._do_import, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Merge Import",
            underline=0,
            command=self.try_command(self._do_merge_import, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Select PGN Files",
            underline=7,
            command=self.try_command(self._select_pgn_files, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)
        if self._database_looks_like_dpt():
            tkinter.Button(
                master=self.buttonframe,
                text="Increase Index",
                underline=13,
                command=self.try_command(
                    self._increase_index, self.buttonframe
                ),
            ).pack(side=tkinter.RIGHT, padx=12)
            tkinter.Button(
                master=self.buttonframe,
                text="Increase Data",
                underline=9,
                command=self.try_command(
                    self._increase_data, self.buttonframe
                ),
            ).pack(side=tkinter.RIGHT, padx=12)

        self.report = _FileLogTextBase(
            master=self.root,
            cnf={"wrap": tkinter.WORD, "undo": tkinter.FALSE},
            logfile=self.home_directory,
        )
        self.report.focus_set()
        if self._database_looks_like_dpt():
            self.bind(
                self.report,
                "<Alt-d>",
                function=self.try_event(self._increase_data),
            )
            self.bind(
                self.report,
                "<Alt-x>",
                function=self.try_event(self._increase_index),
            )
        self.bind(
            self.report,
            "<Alt-i>",
            function=self.try_event(self._do_import),
        )
        self.bind(
            self.report,
            "<Alt-m>",
            function=self.try_event(self._do_merge_import),
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

        self.report.tag_configure(
            "margin",
            lmargin2=tkinter.font.nametofont(self.report.cget("font")).measure(
                "2010-05-23 10:20:57  "
            ),
        )
        self.tagstart = "1.0"
        self._report_to_log(
            "".join(
                ("Importing to database in ", home_directory, " directory.")
            )
        )
        self._report_to_log_text_only("")
        self._report_to_log_text_only(
            "".join(
                (
                    "Merge Import sort area is in ",
                    home_directory if sort_area is None else sort_area,
                    ".",
                )
            )
        )
        self.report.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE
        )
        self.root.iconify()
        self.root.update()
        self.root.deiconify()
        self._allow_job = True
        self._add_queued_reports_to_log()

    def _database_looks_like_dpt(self):
        """Return True if database attribute signature looks like DPT.

        Check a few attriute names expected only in Database class in
        solentware_base.core._dpt module.

        """
        # This describes situation before changes to resolve problem, but
        # the return value remains relevant.
        # An alternative implementation of this difference calls a method
        # add_import_buttons() rather than add the buttons if the test
        # here returns True.  Two versions of add_import_buttons() are
        # defined in classes ..dpt.database_du.Database and
        # ..shared.dptcompatdu.DptCompatdu and the class hierarchy does
        # the test implemented here.  At present that implementation fails
        # because module pickling errors occur for the import action if
        # preceded by an increase action: but some solved problems in this
        # implementation hint at changes which might allow the alternative
        # implementation to succeed.  A practical benefit of the alternative
        # is losing the process startup overhead in the two (quite quick)
        # increase actions relevant only in DPT.
        return hasattr(self.database, "parms") and hasattr(
            self.database, "msgctl"
        )

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = datetime.datetime.isoformat(
            datetime.datetime.today()
        ).split("T")
        hms = hms.split(".")[0]
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

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

    def _increase_data(self, event=None):
        """Run Increase Data Size process."""
        del event
        if not self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Data",
                message="".join(
                    (
                        "Cannot start increase data because a task is in ",
                        "progress.\n\nThe current task must be allowed to ",
                        "finish, or be stopped, before starting task.",
                    )
                ),
            )
            return
        if self._import_done:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Data",
                message="".join(
                    (
                        "The import has been done.",
                        "\n\nIncrease data is intended for before import.",
                    )
                ),
            )
            return
        self._allow_job = False
        self._task_name = "increase data"
        self.quit_event.clear()
        self.deferred_update = IncreaseDataProcess(
            self.database,
            self.report_queue,
            self.quit_event,
        )
        self.deferred_update.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_estimate_join
        )
        self.quit_thread.start()

    def _increase_index(self, event=None):
        """Run Increase Index Size process."""
        del event
        if not self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Index",
                message="".join(
                    (
                        "Cannot start increase index because a task is in ",
                        "progress.\n\nThe current task must be allowed to ",
                        "finish, or be stopped, before starting task.",
                    )
                ),
            )
            return
        if self._import_done:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Index",
                message="".join(
                    (
                        "The import has been done.",
                        "\n\nIncrease index is intended for before import.",
                    )
                ),
            )
            return
        self._allow_job = False
        self._task_name = "increase index"
        self.quit_event.clear()
        self.deferred_update = IncreaseIndexProcess(
            self.database,
            self.report_queue,
            self.quit_event,
        )
        self.deferred_update.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_estimate_join
        )
        self.quit_thread.start()

    def _import(self, method, title, task_name):
        """Run import process with method() if allowed and not already run."""
        if not self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title=title,
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
                title=title,
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
            title=title,
            message="".join(("Please confirm the import is to be started.",)),
        ):
            return
        self._allow_job = False
        self._task_name = task_name
        self.quit_event.clear()
        self.deferred_update = DeferredUpdateProcess(
            self.database,
            method,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgnfiles,
        )
        self.deferred_update.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_join
        )
        self.quit_thread.start()

    def _do_import(self, event=None):
        """Run import process if allowed and not already run.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if self.pgnfiles is None:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Import",
                message="No PGN files selected for import",
            )
            return
        self._import(
            self.deferred_update_module.database_du, "Import", "import"
        )

    def _do_merge_import(self, event=None):
        """Run merge import process if allowed and not already run.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if self.pgnfiles is None:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Merge Import",
                message="No PGN files selected for merge import",
            )
            return
        self._import(
            self.deferred_update_module.database_reload_du,
            "Merge Import",
            "merge import",
        )

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
        askyesnocancel = tkinter.messagebox.askyesnocancel(
            parent=self.root,
            title="Dismiss",
            message="Do you want to save the import log before dismissing?",
        )
        if askyesnocancel is None:
            return
        if askyesnocancel:
            extn = "txt"
            datatype = "Import Log"
            filename = tkinter.filedialog.asksaveasfilename(
                parent=self.root,
                title="Save Log before Dismiss",
                defaultextension="".join((".", extn)),
                filetypes=((datatype, ".".join(("*", extn))),),
            )
            if not filename:
                tkinter.messagebox.showinfo(
                    parent=self.root,
                    title="Dismiss",
                    message="Log not saved to file and not dismissed",
                )
                return
            with open(filename, mode="w", encoding="utf-8") as file:
                file.write(self.report.get("1.0", tkinter.END))
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Dismiss",
                message=" ".join(("Log saved to", filename)),
            )
        if self.report.logfile is not None:
            try:
                os.remove(self.report.logfile)
            except FileNotFoundError:
                pass
        self.root.destroy()

    def _select_pgn_files(self, event=None):
        """Select PGN files to import.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if not self._allow_job:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Select PGN Files",
                message="".join(
                    (
                        "Cannot select PGN files to import because a task is ",
                        "in progress.\n\nThe current task must be allowed to ",
                        "finish, or be stopped, first.",
                    )
                ),
            )
            return
        # After the _allow_job test so the pgnfiles test does not become
        # relevant until DeferredUpdateEstimateProcess job has finished.
        if self.pgnfiles is not None:
            if self._import_done is None:
                tkinter.messagebox.showinfo(
                    parent=self.root,
                    title="Select PGN Files",
                    message="".join(
                        (
                            "PGN files for import already selected\n\n",
                            "Dismiss Log and start again to select PGN files",
                        )
                    ),
                )
                return
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Select PGN Files",
                message="".join(
                    (
                        "The import job for the selected PGN files has ",
                        "been done.\n\n",
                        "Dismiss Log and start again to select PGN files",
                    )
                ),
            )
            return
        if not self.resume:
            self.database.open_database()
            try:
                names = (
                    utilities.get_pgn_filenames_of_an_import_in_progress_txn(
                        self.database
                    )
                )
            finally:
                self.database.close_database()
            if not names:
                # Use askopenfilenames rather than askopenfilename with
                # multiple=Tkinter.TRUE because in freebsd port of Tkinter a
                # tuple is returned while at least some versions of the
                # Microsoft Windows port return a space separated string
                # (which looks a lot like a TCL list - curly brackets around
                # path names containing spaces).
                # Then only the dialogues intercept of askopenfilenames needs
                # changing as askopenfilename with default multiple argument
                # returns a string containg one path name in all cases.
                #
                # Under Wine multiple=Tkinter.TRUE has no effect at Python
                # 2.6.2 so the dialogue supports selection of a single file
                # only.
                gamefiles = tkinter.filedialog.askopenfilenames(
                    parent=self.root,
                    title="Select files containing games to import",
                    initialdir="~",
                    filetypes=[("Portable Game Notation (chess)", ".pgn")],
                )
                if not gamefiles:
                    return
                self.pgnfiles = gamefiles
            else:
                tkinter.messagebox.showinfo(
                    parent=self.root,
                    title="Select PGN Files",
                    message="Resuming an unfinished import",
                )
                self.pgnfiles = names
        else:
            self.pgnfiles = self.resume
        self._allow_job = False
        self._report_to_log_text_only("")
        self._report_to_log("Count games.")
        if isinstance(self.pgnfiles, tuple):
            self._report_to_log_text_only(
                "".join(("Files in ", os.path.dirname(self.pgnfiles[0])))
            )
            for file in self.pgnfiles:
                self._report_to_log_text_only(os.path.basename(file))
        else:
            self._report_to_log_text_only(
                "".join(("Files in ", os.path.dirname(self.pgnfiles)))
            )
            self._report_to_log_text_only(os.path.basename(self.pgnfiles))
        self._report_to_log_text_only("About 2 minutes per million games.")
        self._report_to_log_text_only("")
        self.deferred_update = DeferredUpdateEstimateProcess(
            self.database,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.pgnfiles,
        )
        self.deferred_update.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_estimate_join
        )
        self.quit_thread.start()
        self._add_queued_reports_to_log()
