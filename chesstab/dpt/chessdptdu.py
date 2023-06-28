# chessdptdu.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using DPT single-step deferred update.

This module on Windows only.  Use multi-step module on Wine because Wine
support for a critical function used by single-step is not reliable. There
is no sure way to spot that module is running on Wine.

See www.dptoolkit.com for details of DPT

"""

import os
import multiprocessing
import multiprocessing.dummy

import tkinter
import tkinter.messagebox

# pylint will always give import-error message on non-Microsoft Windows
# systems.
# Wine counts as a Microsft Windows system.
# It is reasonable to not install 'dptdb.dptapi'.
# The importlib module is used to import chessdptdu if needed.
from dptdb.dptapi import FISTAT_DEFERRED_UPDATES

from solentware_base import dptdu_database
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    TABLE_B_SIZE,
    DEFAULT_RECORDS,
)

from .filespec import FileSpec
from ..core.filespec import (
    GAMES_FILE_DEF,
    PIECES_PER_POSITION,
    POSITIONS_PER_GAME,
    PIECES_TYPES_PER_POSITION,
    BYTES_PER_GAME,
)
from ..shared.archivedu import Archivedu
from ..shared.alldu import chess_du_import

# The DPT segment size is 65280 because 32 bytes are reserved and 8160 bytes of
# the 8192 byte page are used for the bitmap.
# TABLE_B_SIZE value is necessarily the same byte size, and already defined.
_DEFERRED_UPDATE_POINTS = (TABLE_B_SIZE * 8 - 1,)
del TABLE_B_SIZE


class DPTFileSpecError(Exception):
    """File definition problem in ChessDatabaseDeferred initialisation."""


class DPTFistatError(Exception):
    """Attempt to open a file when not in deferred update mode."""


class DPTSizingError(Exception):
    """Unable to plan file size increases from PGN import estimates."""


def chess_database_du(
    dbpath, pgnpaths, estimates, file_records=None, **kwargs
):
    """Open database, import games and close database."""
    cdb = ChessDatabase(dbpath, allowcreate=True)
    cdb.open_database(files=file_records)
    chess_du_import(cdb, pgnpaths, **kwargs)
    cdb.close_database_contexts(files=file_records)
    cdb.open_database_contexts(files=file_records)
    status = True
    for file in (
        cdb.specification.keys() if file_records is None else file_records
    ):
        if (
            FISTAT_DEFERRED_UPDATES
            != cdb.table[file].get_file_parameters(cdb.dbenv)["FISTAT"][0]
        ):
            status = False
    cdb.close_database_contexts()
    return status


class ChessDatabaseDeferred(dptdu_database.Database):
    """Provide deferred update methods for a database of games of chess.

    Subclasses must include a subclass of dptbase.Database as a superclass.

    """

    # ChessDatabaseDeferred.deferred_update_points is not needed in DPT, like
    # the similar attribute in chessdbbitdu.ChessDatabase for example, because
    # DPT does it's own memory management for deferred updates.
    # The same attribute is provided to allow the import_pgn method called in
    # this module's chess_database_du function to report progress at regular
    # intervals.
    # The values are set differently because Wine does not give a useful answer
    # to DPT's memory usage questions.
    deferred_update_points = frozenset(_DEFERRED_UPDATE_POINTS)

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
                raise DPTFileSpecError("DPT description invalid") from error

        try:
            super().__init__(ddnames, databasefolder, **kargs)
        except Exception as error:
            if __name__ == "__main__":
                raise
            raise DPTFileSpecError("DPT description invalid") from error

        # Retain import estimates for increase size by button actions
        self._import_estimates = None
        self._notional_record_counts = None
        # Methods passed by UI to populate report widgets
        self._reporter = None

    def open_database(self, files=None):
        """Delegate then raise DPTFistatError if database not in DU mode.

        Normally return None with the database open.

        Close the database and raise DPTFistatError exception if the
        database FISTAT parameter is not equal FISTAT_DEFERRED_UPDATES.

        """
        super().open_database(files=files)
        viewer = self.dbenv.Core().GetViewerResetter()
        for dbo in self.table.values():
            if (
                viewer.ViewAsInt("FISTAT", dbo.opencontext)
                != FISTAT_DEFERRED_UPDATES
            ):
                break
        else:
            if files is None:
                files = dict()
            self.increase_database_size(files=files)
            return
        self.close_database()
        raise DPTFistatError("A file is not in deferred update mode")

    def open_context_prepare_import(self, files=None):
        """Open all files normally."""
        super().open_database(files=files)

    def get_archive_names(self, files=()):
        """Return specified files and existing operating system files."""
        specs = {f for f in files if f in self.table}
        names = [v.file for k, v in self.table.items() if k in specs]
        exists = [
            os.path.basename(n)
            for n in names
            if os.path.exists(".".join((n, "bz2")))
        ]
        return (names, exists)

    def _get_pages_for_record_counts(self, counts=(0, 0)):
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
        try:
            self._report_plans_for_estimate(estimates=estimates)
        except DPTSizingError:
            if reporter:
                reporter.append_text_only("")
                reporter.append_text(
                    "No estimates available to calculate file size increase."
                )
        reporter.append_text_only("")
        reporter.append_text("Ready to start import.")

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
        try:
            (
                gamecount,
                bytes_per_game,
                positions_per_game,
                pieces_per_game,
                piecetypes_per_game,
            ) = self._import_estimates[:5]
        except TypeError as exc:
            raise DPTSizingError("No estimates available for sizing") from exc
        for item in self._import_estimates[:5]:
            if not isinstance(item, int):
                raise DPTSizingError("Value must be an 'int' instance")
        brecppg = self.table[GAMES_FILE_DEF].filedesc[BRECPPG]

        # Calculate number of standard profile games needed to generate
        # the number of index entries implied by the estimated profile
        # and number of games.
        d_count = (
            gamecount
            * (positions_per_game + pieces_per_game + piecetypes_per_game)
        ) // (
            POSITIONS_PER_GAME
            * (1 + PIECES_PER_POSITION + PIECES_TYPES_PER_POSITION)
        )

        # Calculate number of standard profile games needed to generate
        # the number of bytes implied by the estimated profile and number
        # of games.
        if bytes_per_game > BYTES_PER_GAME:
            b_count = int((gamecount * bytes_per_game) / BYTES_PER_GAME)
        else:
            b_count = gamecount

        # Use 'dict's because self._get_database_table_sizes() method
        # needs them internally, even though this case uses one file only.
        self._notional_record_counts = {
            GAMES_FILE_DEF: (b_count, d_count),
        }
        free = dict()
        sizes, increases = self._get_database_table_sizes(
            files=self._notional_record_counts
        )

        append_text_only("")
        append_text("Standard profile game counts used in calculations.")
        append_text_only(
            " ".join(
                (
                    "Standard profile game count for data sizing:",
                    str(b_count),
                )
            )
        )
        append_text_only(
            " ".join(
                (
                    "Standard profile game count for index sizing:",
                    str(d_count),
                )
            )
        )
        append_text_only("")
        append_text_only(
            "".join(
                (
                    "A standard profile game is defined to have ",
                    str(POSITIONS_PER_GAME),
                    " positions, ",
                    str(PIECES_PER_POSITION),
                    " pieces per position, ",
                    str(PIECES_TYPES_PER_POSITION),
                    " piece types per position, and occupy ",
                    str(BYTES_PER_GAME),
                    " bytes.",
                )
            )
        )

        # Loops on sizes, increases, and free, dict objects removed because
        # this case does one file only.
        append_text_only("")
        append_text("Current file size and free space as pages.")
        bdsize = sizes[GAMES_FILE_DEF]
        bsize, bused, dsize, dused = bdsize
        bused = max(0, bused)
        free[GAMES_FILE_DEF] = (bsize - bused, dsize - dused)
        append_text_only(" ".join(("Current data area size:", str(bsize))))
        append_text_only(" ".join(("Current index area size:", str(dsize))))
        append_text_only(
            " ".join(("Current data area free:", str(bsize - bused)))
        )
        append_text_only(
            " ".join(("Current index area free:", str(dsize - dused)))
        )
        nr_count = self._notional_record_counts[GAMES_FILE_DEF]
        b_pages, d_pages = self._get_pages_for_record_counts(nr_count)
        append_text_only("")
        append_text("File space needed for import.")
        append_text_only(
            " ".join(("Estimated pages needed for data:", str(b_pages)))
        )
        append_text_only(
            " ".join(("Estimated pages needed for indexing:", str(d_pages)))
        )
        increments = increases[GAMES_FILE_DEF]
        b_incr, d_incr = increments
        b_free, d_free = free[GAMES_FILE_DEF]
        append_text_only("")
        append_text("Planned file size increase and free space before import.")
        append_text_only(
            " ".join(("Planned increase in data pages:", str(b_incr)))
        )
        append_text_only(
            " ".join(("Planned increase in index pages:", str(d_incr)))
        )
        append_text_only(
            " ".join(("Free data pages before import:", str(b_incr + b_free)))
        )
        append_text_only(
            " ".join(("Free index pages before import:", str(d_incr + d_free)))
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


class ChessDatabase(Archivedu, ChessDatabaseDeferred):
    """Provide single-step deferred update for a database of games of chess."""
