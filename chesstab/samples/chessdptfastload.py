# chessdptfastload.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using DPT fastload.

This module on Windows only.

See www.dptoolkit.com for details of DPT.

"""

import os
import multiprocessing  # Removed later by 'del multiprocessing'.

import tkinter
import tkinter.messagebox

# pylint will always give import-error message on non-Microsoft Windows
# systems.
# Wine counts as a Microsft Windows system.
# It is reasonable to not install 'dptdb.dptapi'.
# The importlib module is used to import chessdptdu if needed.
from dptdb.dptapi import FISTAT_DEFERRED_UPDATES

from solentware_base import dptfastload_database
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    TABLE_B_SIZE,
)

from ..dpt.filespec import FileSpec
from ..core.filespec import (
    GAMES_FILE_DEF,
    PIECES_PER_POSITION,
    POSITIONS_PER_GAME,
)
from ..shared.alldu import chess_du_import

# The DPT segment size is 65280 because 32 bytes are reserved and 8160 bytes of
# the 8192 byte page are used for the bitmap.
# DB_SEGMENT_SIZE has no effect on processing apart from report points.
DB_SEGMENT_SIZE = 65280
_DEFERRED_UPDATE_POINTS = (DB_SEGMENT_SIZE - 1,)
del DB_SEGMENT_SIZE


class ChessdptfastloadError(Exception):
    """Exception class for chessdptfastload module."""


def chess_dptfastload(
    dbpath, pgnpaths, file_records=None, reporter=None, quit_event=None
):
    """Open database, import games and close database."""
    cdb = ChessDatabase(dbpath, allowcreate=True)
    cdb.open_database(files=file_records)

    # Intend to start a process, via multiprocessing, to do the database
    # update.  That process will do the reporting, not the one running
    # this method.
    chess_du_import(cdb, pgnpaths, reporter=reporter, quit_event=quit_event)

    cdb.close_database_contexts(files=file_records)
    cdb.open_database_contexts(files=file_records)
    status = True
    for file in (
        cdb.specification.keys() if file_records is None else file_records
    ):
        if cdb.table[file].get_file_parameters(cdb.dbenv)["FISTAT"][0]:
            status = False
    cdb.close_database_contexts()
    return status


class ChessDatabase(dptfastload_database.Database):
    """Provide fast load deferred methods for a database of games of chess.

    Subclasses must include a subclass of dptbase.Database as a superclass.

    """

    # deferred_update_points is the existing name but here it signifies
    # the interval at which a fastload call updates the database.
    # The number is arbitrary in relation to segment sizes since there may
    # be gaps in the record number sequence due to long games preventing
    # all slots in a page being used.
    deferred_update_points = frozenset(_DEFERRED_UPDATE_POINTS)

    # Override
    # dptfastload_database.Database._take_backup_before_deferred_update
    # while DPT archive() and delete_archive() methods absent.
    _take_backup_before_deferred_update = False

    def __init__(
        self,
        databasefolder,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        ddnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )
        # Deferred update for games file only
        for ddname in list(ddnames.keys()):
            if ddname != GAMES_FILE_DEF:
                del ddnames[ddname]

        if not kargs.get("allowcreate", False):
            try:
                for ddname in ddnames:
                    if FILEDESC in ddnames[ddname]:
                        del ddnames[ddname][FILEDESC]
            except Exception as error:
                if __name__ == "__main__":
                    raise
                raise ChessdptfastloadError(
                    "DPT description invalid"
                ) from error

        try:
            super().__init__(ddnames, databasefolder, **kargs)
        except ChessdptfastloadError as error:
            if __name__ == "__main__":
                raise
            raise ChessdptfastloadError("DPT description invalid") from error

        # Retain import estimates for increase size by button actions
        self._import_estimates = None
        self._notional_record_counts = None
        # Methods passed by UI to populate report widgets
        self._reporter = None

    def open_database(self, files=None):
        """Delegate then return None if database in deferred update mode.

        Close the database and raise ChessdptfastloadError exception if the
        database FISTAT parameter is not equal FISTAT_DEFERRED_UPDATES.

        """
        super().open_database(files=files)
        viewer = self.dbenv.Core().GetViewerResetter()
        for dbo in self.table.values():
            if viewer.ViewAsInt("FISTAT", dbo.opencontext):
                break
        else:
            if files is None:
                files = dict()
            self.increase_database_size(files=files)
            return
        self.close_database()
        raise ChessdptfastloadError("A file is not in deferred update mode")

    def open_context_prepare_import(self):
        """Open all files normally."""
        super().open_database()

    def get_pages_for_record_counts(self, counts=(0, 0)):
        """Return Table B and Table D pages needed for record counts."""
        brecppg = self.table[GAMES_FILE_DEF].filedesc[BRECPPG]
        return (
            counts[0] // brecppg,
            (counts[1] * self.table[GAMES_FILE_DEF].btod_factor) // brecppg,
        )

    def _get_database_table_sizes(self, files=None):
        """Return Table B and D size and usage in pages for files."""
        if files is None:
            files = dict()
        filesize = dict()
        for key, value in self.get_database_parameters(
            files=list(files.keys())
        ).items():
            filesize[key] = (
                value["BSIZE"],
                value["BHIGHPG"],
                value["DSIZE"],
                value["DPGSUSED"],
            )
        increase = self.get_database_increase(files=files)
        self.close_database_contexts()
        return filesize, increase

    def add_import_buttons(
        self,
        master,
        try_command_wrapper,
        try_event_wrapper,
        bind,
        widget,
        *args,
    ):
        """Add button actions for DPT to Import dialogue.

        Increase data and index space available.

        """
        index = tkinter.Button(
            master=master,
            text="Increase Index",
            underline=13,
            command=try_command_wrapper(self._increase_index, master),
        )
        index.pack(side=tkinter.RIGHT, padx=12)
        bind(widget, "<Alt-x>", try_event_wrapper(self._increase_index))
        data = tkinter.Button(
            master=master,
            text="Increase Data",
            underline=9,
            command=try_command_wrapper(self._increase_data, master),
        )
        data.pack(side=tkinter.RIGHT, padx=12)
        bind(widget, "<Alt-d>", try_event_wrapper(self._increase_data))

    def _increase_data(self, event=None):
        """Add maximum of current free space and default size to Table B.

        event is ignored and is present for compatibility between button click
        and keypress,

        """
        del event
        self.open_database_contexts(files=(GAMES_FILE_DEF,))
        increase_done = False
        for key, value in self.get_database_parameters(
            files=(GAMES_FILE_DEF,)
        ).items():
            bsize = value["BSIZE"]
            bused = max(0, value["BHIGHPG"])
            bneeded = self.get_pages_for_record_counts(
                self._notional_record_counts[key]
            )[0]
            bincrease = min(bneeded * 2, bsize - bused)
            message = "".join(
                (
                    "The free data size of the ",
                    key,
                    " file will be increased from ",
                    str(bsize - bused),
                    " pages to ",
                    str(bincrease + bsize - bused),
                    " pages.",
                )
            )
            if len(self.table[key].get_extents()) % 2 == 0:
                message = "".join(
                    (
                        message,
                        "\n\nAt present it is better to do index increases ",
                        "first for this file, if you need to do any, because ",
                        "a new extent (fragment) would not be needed.",
                    )
                )
            if tkinter.messagebox.askyesno(
                title="Increase Data Size",
                message="".join(
                    (
                        message,
                        "\n\nDo you want to increase the data size?",
                    )
                ),
            ):
                increase_done = True
                self.table[key].opencontext.Increase(bincrease, False)
        if increase_done:
            self._reporter.append_text(
                " ".join(
                    (
                        "Recalculation of planned database size increases",
                        "after data size increase by user action.",
                    )
                )
            )
            self._reporter.append_text_only("")
            self._report_plans_for_estimate()
        self.close_database_contexts()

    def _increase_index(self, event=None):
        """Add maximum of current free space and default size to Table D.

        event is ignored and is present for compatibility between button click
        and keypress,

        """
        del event
        self.open_database_contexts(files=(GAMES_FILE_DEF,))
        increase_done = False
        for key, value in self.get_database_parameters(
            files=(GAMES_FILE_DEF,)
        ).items():
            dsize = value["DSIZE"]
            dused = value["DPGSUSED"]
            dneeded = self.get_pages_for_record_counts(
                self._notional_record_counts[key]
            )[1]
            dincrease = min(dneeded * 2, dsize - dused)
            message = "".join(
                (
                    "The free index size of the ",
                    key,
                    " file will be increased from ",
                    str(dsize - dused),
                    " pages to ",
                    str(dincrease + dsize - dused),
                    " pages.",
                )
            )
            if len(self.table[key].get_extents()) % 2 != 0:
                message = "".join(
                    (
                        message,
                        "\n\nAt present it is better to do data increases ",
                        "first for this file, if you need to do any, because ",
                        "a new extent (fragment) would not be needed.",
                    )
                )
            if tkinter.messagebox.askyesno(
                title="Increase Index Size",
                message="".join(
                    (
                        message,
                        "\n\nDo you want to increase the index size?",
                    )
                ),
            ):
                increase_done = True
                self.table[key].opencontext.Increase(dincrease, True)
        if increase_done:
            self._reporter.append_text(
                " ".join(
                    (
                        "Recalculation of planned database size increases",
                        "after index size increase by user action.",
                    )
                )
            )
            self._reporter.append_text_only("")
            self._report_plans_for_estimate()
        self.close_database_contexts()

    def get_file_sizes(self):
        """Return dictionary of notional record counts for data and index."""
        return self._notional_record_counts

    def report_plans_for_estimate(self, estimates, reporter):
        """Calculate and report file size adjustments to do import.

        Note the reporter and headline methods for initial report and possible
        later recalculations.

        Pass estimates through to self._report_plans_for_estimate

        """
        # See comment near end of class definition Chess in relative module
        # ..gui.chess for explanation of this change.
        self._reporter = reporter
        self._report_plans_for_estimate(estimates=estimates)

    def _report_plans_for_estimate(self, estimates=None):
        """Recalculate and report file size adjustments to do import.

        Create dictionary of effective game counts for sizing Games file.
        This will be passed to the import job which will increase Table B and
        Table D according to file specification.

        The counts for Table B and Table D can be different.  If the average
        data bytes per game is greater than Page size / Records per page the
        count must be increased to allow for the unused record numbers.  If
        the average positions per game or pieces per position are not the
        values used to calculate the steady-state ratio of Table B to Table D
        the count must be adjusted to compensate.

        """
        append_text = self._reporter.append_text
        append_text_only = self._reporter.append_text_only
        if estimates is not None:
            self._import_estimates = estimates
        (
            gamecount,
            bytes_per_game,
            positions_per_game,
            pieces_per_game,
        ) = self._import_estimates[:4]
        brecppg = self.table[GAMES_FILE_DEF].filedesc[BRECPPG]
        d_count = (gamecount * (positions_per_game + pieces_per_game)) // (
            POSITIONS_PER_GAME * (1 + PIECES_PER_POSITION)
        )
        if bytes_per_game > (TABLE_B_SIZE // brecppg):
            b_count = int(
                (gamecount * bytes_per_game) / (TABLE_B_SIZE / brecppg)
            )
        else:
            b_count = gamecount
        self._notional_record_counts = {
            GAMES_FILE_DEF: (b_count, d_count),
        }
        append_text("Current file size and free space:")
        free = dict()
        sizes, increases = self._get_database_table_sizes(
            files=self._notional_record_counts
        )
        for filename, bdsize in sizes.items():
            bsize, bused, dsize, dused = bdsize
            bused = max(0, bused)
            free[filename] = (bsize - bused, dsize - dused)
            append_text_only(filename)
            append_text_only(
                " ".join(("Current data area size", str(bsize), "pages"))
            )
            append_text_only(
                " ".join(("Current index area size", str(dsize), "pages"))
            )
            append_text_only(
                " ".join(
                    ("Current data area free", str(bsize - bused), "pages")
                )
            )
            append_text_only(
                " ".join(
                    ("Current index area free", str(dsize - dused), "pages")
                )
            )
        append_text_only("")
        append_text("File space needed for import:")
        for filename, nr_count in self._notional_record_counts.items():
            append_text_only(filename)
            b_pages, d_pages = self.get_pages_for_record_counts(nr_count)
            append_text_only(
                " ".join(("Estimated", str(b_pages), "pages needed for data"))
            )
            append_text_only(
                " ".join(
                    ("Estimated", str(d_pages), "pages needed for indexes")
                )
            )
        append_text_only("")
        append_text("File size increases planned and free space when done:")
        for filename, increments in increases.items():
            b_incr, d_incr = increments
            b_free, d_free = free[filename]
            append_text_only(filename)
            append_text_only(
                " ".join(("Data area increase", str(b_incr), "pages"))
            )
            append_text_only(
                " ".join(("Index area increase", str(d_incr), "pages"))
            )
            append_text_only(
                " ".join(("Data area free", str(b_incr + b_free), "pages"))
            )
            append_text_only(
                " ".join(("Index area free", str(d_incr + d_free), "pages"))
            )
        append_text_only("")
        append_text_only(
            "".join(
                (
                    "Comparison of the required and free data or index ",
                    "space may justify using the Increase Data and, or, ",
                    "Increase Index actions to get more space immediately ",
                    "given your knowledge of the PGN file being imported.",
                )
            )
        )
        append_text_only("")
        append_text_only("")
