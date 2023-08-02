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
import sys

# pylint will always give import-error message on non-Microsoft Windows
# systems.
# Wine counts as a Microsft Windows system.
# It is reasonable to not install 'dptdb.dptapi'.
# The importlib module is used to import chessdptdu if needed.
from dptdb.dptapi import (
    FISTAT_DEFERRED_UPDATES,
    FISTAT_PHYS_BROKEN,
    FIFLAGS_FULL_TABLEB,
    FIFLAGS_FULL_TABLED,
    FLOAD_DEFAULT,
)

from solentware_base import dptdu_database
from solentware_base.core.archivedudpt import ArchiveduDPT
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    TABLE_B_SIZE,
    DPT_SYSFL_FOLDER,
    BTOD_FACTOR,
)

from .filespec import FileSpec
from ..core.filespec import (
    GAMES_FILE_DEF,
    PIECES_PER_POSITION,
    POSITIONS_PER_GAME,
    PIECES_TYPES_PER_POSITION,
    BYTES_PER_GAME,
)
from ..shared.alldu import (
    chess_du_import,
    chess_du_backup_before_import,
    chess_du_delete_backup_after_import,
)
from . import chessdptnofistat

# The DPT segment size is 65280 because 32 bytes are reserved and 8160 bytes of
# the 8192 byte page are used for the bitmap.
# TABLE_B_SIZE value is necessarily the same byte size, and already defined.
_DEFERRED_UPDATE_POINTS = (TABLE_B_SIZE * 8 - 1,)
del TABLE_B_SIZE


class DPTFileSpecError(Exception):
    """File definition problem in ChessDatabase initialisation."""


class DPTFistatError(Exception):
    """Attempt to open a file when not in deferred update mode."""


class DPTSizingError(Exception):
    """Unable to plan file size increases from PGN import estimates."""


def chess_database_du(
    dbpath, *args, file=None, reporter=None, increases=None, **kwargs
):
    """Open database, import games and close database."""
    files = (file,) if file is not None else None

    # Take a backup of games file by fast dump.
    bu_process = multiprocessing.Process(
        target=chess_database_import_backup,
        args=(dbpath, files),
        kwargs=dict(file=file, reporter=reporter, increases=increases),
    )
    bu_process.start()
    bu_process.join()
    if bu_process.exitcode != 0:
        return
    del bu_process

    # Import to games file.
    import_process = multiprocessing.Process(
        target=chess_database_import,
        args=(dbpath, files, *args),
        kwargs=dict(
            file=file, reporter=reporter, increases=increases, **kwargs
        ),
    )
    import_process.start()
    import_process.join()
    if import_process.exitcode != 0:
        return
    del import_process

    # Recover games file from backup if import failed.
    recover_process = multiprocessing.Process(
        target=chess_database_status_after_import,
        args=(dbpath, files),
        kwargs=dict(
            file=file, reporter=reporter, increases=increases, **kwargs
        ),
    )
    recover_process.start()
    recover_process.join()
    if recover_process.exitcode != 0:
        return
    del recover_process

    # Assume the import succeeded if backup is not present.
    if not os.path.exists(
        os.path.join(dbpath, dptdu_database.Database.import_backup_directory)
    ):
        return

    # Assume recovery from failed import also failed if games file is broken.
    if _games_file_is_broken(dbpath, files, file=file):
        if reporter is not None:
            reporter.append_text("Import not done.")
            reporter.append_text_only("")
        return

    # Try the import once more: table B and table D increases already applied.
    import_process = multiprocessing.Process(
        target=chess_database_import,
        args=(dbpath, files, *args),
        kwargs=dict(file=file, reporter=reporter, increases=None, **kwargs),
    )
    import_process.start()
    import_process.join()
    if import_process.exitcode != 0:
        return
    del import_process

    # Recover games file from backup if re-tried import failed.
    recover_process = multiprocessing.Process(
        target=chess_database_status_after_import,
        args=(dbpath, files),
        kwargs=dict(
            file=file, reporter=reporter, increases=increases, **kwargs
        ),
    )
    recover_process.start()
    recover_process.join()
    del recover_process

    # Assume the import succeeded if backup is not present.
    if not os.path.exists(
        os.path.join(dbpath, dptdu_database.Database.import_backup_directory)
    ):
        return

    # Does not matter how recovery from re-tried import failure turns out.
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Import not done.")
        reporter.append_text_only("")


def _games_file_is_broken(dbpath, files, file=None):
    """Return True if games file is broken, False otherwise."""
    fistat_process = multiprocessing.Process(
        target=chess_database_current_status,
        args=(dbpath, files),
        kwargs=dict(file=file),
    )
    fistat_process.start()
    fistat_process.join()
    return fistat_process.exitcode != 0


class ChessDatabase(dptdu_database.Database, ArchiveduDPT):
    """Provide deferred update methods for a database of games of chess.

    Subclasses must include a subclass of dptbase.Database as a superclass.

    """

    # ChessDatabase.deferred_update_points is not needed in DPT, like
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
            # Previous algorithm called self.increase_database_size here.
            # Now the increase is done in chess_du_import call from
            # chess_database_du function.
            return
        self.close_database()
        raise DPTFistatError("A file is not in deferred update mode")

    def open_context_prepare_import(self, files=None):
        """Open all files normally."""
        super().open_database(files=files)

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
            files = {}
        filesize = {}
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

    def report_plans_for_estimate(self, estimates, reporter, increases):
        """Calculate and report file size adjustments to do import.

        Note the reporter and headline methods for initial report and possible
        later recalculations.

        Pass estimates through to self._report_plans_for_estimate

        """
        # See comment near end of class definition Chess in relative module
        # ..gui.chess for explanation of this change.
        self._reporter = reporter
        try:
            self._report_plans_for_estimate(
                estimates=estimates,
                increases=increases,
            )
        except DPTSizingError:
            if reporter:
                reporter.append_text_only("")
                reporter.append_text(
                    "No estimates available to calculate file size increase."
                )
        reporter.append_text_only("")
        reporter.append_text("Ready to start import.")

    def _report_plans_for_estimate(self, estimates=None, increases=None):
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
        free = {}
        sizes, increments = self._get_database_table_sizes(
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
        b_pages, d_pages = self.get_pages_for_record_counts(nr_count)
        append_text_only("")
        append_text("File space needed for import.")
        append_text_only(
            " ".join(("Estimated pages needed for data:", str(b_pages)))
        )
        append_text_only(
            " ".join(("Estimated pages needed for indexing:", str(d_pages)))
        )
        b_incr, d_incr = increments[GAMES_FILE_DEF]
        b_free, d_free = free[GAMES_FILE_DEF]

        # Save table B and D increases for import process to do later.
        # Save table B and D free for import process in case increase is not
        # enough and an adjustment has to be estimated if increase is 0.
        if increases is not None:
            increases[0] = b_incr
            increases[1] = d_incr
            increases[2] = b_free
            increases[3] = d_free

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

    # The attempt to generate a bz2 archive of the games database with
    # Python's builtin 'open' method fails because of a PermissionError.
    # The attempt to generate a DPT fast unload dump of the games
    # database fails because it is open in deferred update mode, and
    # attempting to open it temporarely in normal mode fails because the
    # audit file already exists (the database has to be closed down more
    # thoroughly than is convenient given need to keep other database
    # engines in play in the shared code).
    # Converting the archive to 'fast unload'  depend on being able to
    # produce a reliable crafted 'fast load' implementation to do the
    # import.  Till then the algorithm derived from 'text export' will
    # have to do.


class ChessDatabaseImportBackup(chessdptnofistat.ChessDatabase, ArchiveduDPT):
    """Access chess database to take backup before import."""

    # Set default parameters for fastload and fastunload use.
    def create_default_parms(self):
        """Create default parms.ini file for fast load/unload normal mode.

        This means transactions are disabled and a small number of buffers.

        """
        if not os.path.exists(self.parms):
            with open(self.parms, "w", encoding="iso-8859-1") as parms:
                parms.write("RCVOPT=X'00' " + os.linesep)
                parms.write("MAXBUF=100 " + os.linesep)


def chess_database_import_backup(
    dbpath, files, file=None, reporter=None, increases=None
):
    """Backup file before import to file."""
    budb = ChessDatabaseImportBackup(
        dbpath,
        allowcreate=True,
        sysfolder=os.path.join(dbpath, DPT_SYSFL_FOLDER),
    )
    budb.open_database(files=files)
    try:
        chess_du_backup_before_import(
            budb, file=file, reporter=reporter, increases=increases
        )
    finally:
        budb.close_database()


def chess_database_import(
    dbpath, files, *args, file=None, reporter=None, increases=None, **kwargs
):
    """Import to file."""
    cdb = ChessDatabase(dbpath, allowcreate=True)
    cdb.open_database(files=files)

    # Running out of table B pages gets a RuntimeError exception.
    # Running out of table D pages does not get an exception.
    # Both set the file as broken.
    try:
        chess_du_import(
            cdb,
            *args,
            file=file,
            reporter=reporter,
            increases=increases,
            **kwargs,
        )
    except RuntimeError as exc:
        if str(exc) != "File is full":
            raise

    # Necessary to update 'FISTAT' and 'FIFLAGS' information.
    cdb.close_database_contexts(files=files)
    cdb.open_database_contexts(files=files)

    try:
        for key in cdb.specification.keys():
            if key != file:
                continue
            parameters = cdb.table[key].get_file_parameters(cdb.dbenv)
            if parameters["FISTAT"][0] != FISTAT_DEFERRED_UPDATES:
                if reporter is not None:
                    reporter.append_text(
                        hex(FISTAT_DEFERRED_UPDATES).join(
                            (
                                "File broken during import (status not '",
                                "')",
                            )
                        )
                    )
                    reporter.append_text_only(parameters["FISTAT"][1])
                    reporter.append_text_only("")

            # Either table B or table D, but not both, may be marked full:
            # whichever happens first will cause the update to stop.
            # FISTAT bits can be turned off, but not on (1 to 0 is allowed).
            # FIFLAGS bits cannot be reset (1 to 0 or 0 to 1).
            if parameters["FIFLAGS"] & FIFLAGS_FULL_TABLEB:
                if reporter is not None:
                    reporter.append_text("File full: increase data size.")
                    reporter.append_text_only(
                        " ".join(
                            (
                                "Data size (too small) is",
                                str(parameters["BSIZE"]),
                                "pages.",
                            )
                        )
                    )
                if increases is None:
                    if reporter is not None:
                        reporter.append_text_only(
                            "Data size not changed: no increase specified."
                        )
                    reporter.append_text_only("")
                    break
                increment = increases[0] // 10
                if not increment:
                    increment = increases[2] // 10
                if not increment:
                    increment = increases[2]
                cdb.table[key].opencontext.Increase(increment, False)
                dinc = round(increment * cdb.specification[key][BTOD_FACTOR])
                cdb.table[key].opencontext.Increase(dinc, True)
                if reporter is not None:
                    viewer_resetter = cdb.dbenv.Core().GetViewerResetter()
                    reporter.append_text_only(
                        " ".join(
                            (
                                "Data size increased by",
                                str(increment),
                                "to",
                                viewer_resetter.View(
                                    "BSIZE", cdb.table[key].opencontext
                                ),
                                "pages.",
                            )
                        )
                    )
                    reporter.append_text_only(
                        " ".join(
                            (
                                "Index size increased by",
                                str(dinc),
                                "to",
                                viewer_resetter.View(
                                    "DSIZE", cdb.table[key].opencontext
                                ),
                                "pages to fit data size.",
                            )
                        )
                    )
                    reporter.append_text_only("File status is now:")
                    reporter.append_text_only(
                        viewer_resetter.View(
                            "FISTAT", cdb.table[key].opencontext
                        ),
                    )
                    reporter.append_text_only("")
            elif parameters["FIFLAGS"] & FIFLAGS_FULL_TABLED:
                if reporter is not None:
                    reporter.append_text("File full: increase index size.")
                    reporter.append_text_only(
                        " ".join(
                            (
                                "Index size (too small) is",
                                str(parameters["DSIZE"]),
                                "pages.",
                            )
                        )
                    )
                if increases is None:
                    if reporter is not None:
                        reporter.append_text_only(
                            "Index size not changed: no increase specified."
                        )
                    reporter.append_text_only("")
                    break
                viewer_resetter = cdb.dbenv.Core().GetViewerResetter()
                viewer_resetter.Reset(
                    "FISTAT",
                    str(parameters["FISTAT"][0] - FISTAT_PHYS_BROKEN),
                    cdb.table[key].opencontext,
                )
                increment = increases[1] // 10
                if not increment:
                    increment = increases[3] // 10
                if not increment:
                    increment = increases[3]
                cdb.table[key].opencontext.Increase(increment, True)
                if reporter is not None:
                    reporter.append_text_only(
                        " ".join(
                            (
                                "Index size increased by",
                                str(increment),
                                "to",
                                viewer_resetter.View(
                                    "DSIZE", cdb.table[key].opencontext
                                ),
                                "pages.",
                            )
                        )
                    )
                    reporter.append_text_only("File status is now:")
                    reporter.append_text_only(
                        viewer_resetter.View(
                            "FISTAT", cdb.table[key].opencontext
                        ),
                    )
                    reporter.append_text_only("")

            break

        else:
            if reporter is not None:
                reporter.append_text("File not open: status not checked.")
                reporter.append_text_only("")
    finally:
        cdb.close_database_contexts(files=files)


def chess_database_status_after_import(
    dbpath, files, file=None, reporter=None, increases=None, **kwargs
):
    """Recover games file from backup if file is broken."""
    budb = ChessDatabaseImportBackup(
        dbpath,
        allowcreate=True,
        sysfolder=os.path.join(dbpath, DPT_SYSFL_FOLDER),
    )
    if not os.path.exists(
        ".".join((os.path.join(dbpath, budb.import_backup_directory), "grd"))
    ):
        if reporter is not None:
            reporter.append_text("Backup '.grd' file does not exist.")
            reporter.append_text_only("Is backup, if it exists, trusted?")
            reporter.append_text_only("Backup, if it exists, is not deleted.")
            reporter.append_text_only("Database not recovered from backup.")
            reporter.append_text_only("")
        sys.exit(2)
    budb.open_database(files=files)
    try:
        games = budb.table[file]
        opencontext = games.opencontext
        viewer_resetter = budb.dbenv.Core().GetViewerResetter()
        if viewer_resetter.ViewAsInt("FISTAT", opencontext) == 0:  # Normal
            chess_du_delete_backup_after_import(
                budb,
                file=file,
                reporter=reporter,
                increases=increases,
                **kwargs,
            )
            return
        if reporter is not None:
            reporter.append_text("Initialize broken file.")
            reporter.append_text_only("")
        opencontext.Initialize()
        if reporter is not None:
            reporter.append_text("Recovering file from backup.")
            reporter.append_text_only("")

        # Does this step, working or not, belong in archivedudpt module?
        try:
            games.opencontext.Load(
                FLOAD_DEFAULT,
                0,
                None,
                os.path.join(
                    budb.home_directory, budb.import_backup_directory
                ),
            )
        except RuntimeError:
            fistat = viewer_resetter.ViewAsInt("FISTAT", games.opencontext)
            if (fistat & FIFLAGS_FULL_TABLEB) or (
                fistat & FIFLAGS_FULL_TABLED
            ):
                if reporter is not None:
                    reporter.append_text(
                        "File broken during recovery (status not '0x00')."
                    )
                    reporter.append_text_only("File status is now:")
                    reporter.append_text_only(
                        viewer_resetter.View(
                            "FISTAT", budb.table[file].opencontext
                        ),
                    )
                    reporter.append_text_only("")
                return
            raise

        if reporter is not None:
            reporter.append_text("File recovered.")
    finally:
        budb.close_database()


def chess_database_current_status(dbpath, files, file=None):
    """Exit process with non-zero code if games file is broken."""
    exit_code = 2
    budb = ChessDatabaseImportBackup(
        dbpath,
        allowcreate=True,
        sysfolder=os.path.join(dbpath, DPT_SYSFL_FOLDER),
    )
    budb.open_database(files=files)
    try:
        games = budb.table[file]
        opencontext = games.opencontext
        viewer_resetter = budb.dbenv.Core().GetViewerResetter()
        if viewer_resetter.ViewAsInt("FISTAT", opencontext) == 0:  # Normal
            exit_code = 0
        del opencontext
        budb.close_database_contexts(files=files)
    finally:
        budb.close_database()
    sys.exit(exit_code)
