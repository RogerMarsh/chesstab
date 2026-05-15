# database_one_step_du.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

# Restored from ChessTab-7.1.3 chessdptdu module and renamed.

"""Chess database update using DPT single-step deferred update.

This module on Windows only.  Use multi-step module on Wine because Wine
support for a critical function used by single-step is not reliable. There
is no sure way to spot that module is running on Wine.

See www.dptoolkit.com for details of DPT

"""
import os
import multiprocessing
import sys
import traceback
import datetime

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
    FUNLOAD_DEFAULT,
)

from solentware_base import dpt_database
from solentware_base import dptdu_database
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    TABLE_B_SIZE,
    DPT_SYSFL_FOLDER,
    BTOD_FACTOR,
    PRIMARY,
    SECONDARY,
    FIELDS,
)
from solentware_base.core.segmentsize import SegmentSize

from .. import ERROR_LOG, APPLICATION_NAME
from ..core import filespec
from ..core.filespec import (
    GAMES_FILE_DEF,
    PIECES_PER_POSITION,
    POSITIONS_PER_GAME,
    PIECES_TYPES_PER_POSITION,
    BYTES_PER_GAME,
)
from ..basecore import database as basecore_database
from ..core import chessrecord
from ..shared.alldu import get_filespec
from ..core.constants import FILE, GAME

# The DPT segment size is 65280 because 32 bytes are reserved and 8160 bytes of
# the 8192 byte page are used for the bitmap.
# TABLE_B_SIZE value is necessarily the same byte size, and already defined.
_DEFERRED_UPDATE_POINTS = (TABLE_B_SIZE * 8 - 1,)
del TABLE_B_SIZE


# Restored from ChessTab-7.1.3 shared.alldu module and modified to fit.
def _chess_du_report_increases(reporter, file, size_increases):
    """Report size increases for file if any and there is a reporter.

    All elements of size_increases will be 0 (zero) if explicit increase
    in file size is not supported, or if not required when it is
    supported.

    """
    if reporter is None:
        return
    if sum(size_increases) == 0:
        return
    reporter.append_text_only("")
    reporter.append_text(file.join(("Increase size of '", "' file.")))
    label = ("Data", "Index")
    for item, size in enumerate(size_increases):
        reporter.append_text_only(
            " ".join(
                (
                    "Applied increase in",
                    label[item],
                    "pages:",
                    str(size),
                )
            )
        )


# Restored from ChessTab-7.1.3 shared.alldu module and modified to fit.
def _report_exception(cdb, reporter, exception):
    """Write exception to error log file, and reporter if available."""
    errorlog_written = True
    try:
        with open(
            os.path.join(cdb.home_directory, ERROR_LOG),
            "a",
            encoding="utf-8",
        ) as errorlog:
            errorlog.write(
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
    except Exception:
        errorlog_written = False
    if reporter is not None:
        reporter.append_text("An exception has occured during import:")
        reporter.append_text_only("")
        reporter.append_text_only(str(exception))
        reporter.append_text_only("")
        if errorlog_written:
            reporter.append_text_only(
                "".join(
                    (
                        "detail appended to ",
                        os.path.join(cdb.home_directory, ERROR_LOG),
                        " file.",
                    )
                )
            )
        else:
            reporter.append_text_only(
                "".join(
                    (
                        "attempt to append detail to ",
                        os.path.join(cdb.home_directory, ERROR_LOG),
                        " file failed.",
                    )
                )
            )
        reporter.append_text_only("")
        reporter.append_text(
            "Import abandonned in way depending on database engine."
        )


# Restored from ChessTab-7.1.3 shared.alldu module and modified to fit.
# This function is not absorbed in chess_du_import because the database
# has to be open for DPT backup, but not in the mode used to do an
# import.
def chess_du_backup_before_import(
    cdb,
    file=None,
    reporter=None,
    **kwargs,
):
    """Backup database cdb before import."""
    del kwargs
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Make backup before import.")
    try:
        cdb.archive(name=file)
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    if reporter is not None:
        reporter.append_text("Backup completed.")


# Restored from ChessTab-7.1.3 shared.alldu module and modified to fit.
# This function is not absorbed in chess_du_import because in DPT the
# absence of 'file full' conditions has to be confirmed before deleting
# the backups.
def chess_du_delete_backup_after_import(
    cdb,
    file=None,
    reporter=None,
    **kwargs,
):
    """Delete backup of database cdb after import."""
    del kwargs
    if reporter is not None:
        reporter.append_text("Delete backup for import.")
    cdb.delete_archive(name=file)
    if reporter is not None:
        reporter.append_text("Backup deleted.")
        reporter.append_text_only("")
        reporter.append_text("Import finished.")
        reporter.append_text_only("")


# Restored from ChessTab-7.1.3 shared.alldu module and modified to fit.
def chess_du_import(
    cdb,
    pgnpaths,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from pgnpaths into open database cdb."""
    importer = ChessDBrecordGameDUSingleStep()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _chess_du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to import to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    cdb.set_defer_update()
    try:
        for pgnfile in pgnpaths:
            with open(pgnfile, "r", encoding="iso-8859-1") as source:
                if not importer.import_pgn(
                    cdb,
                    source,
                    os.path.basename(pgnfile),
                    reporter=reporter,
                    quit_event=quit_event,
                ):
                    cdb.backout()
                    return
        if reporter is not None:
            reporter.append_text("Finishing import: please wait.")
            reporter.append_text_only("")
        cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    cdb.unset_defer_update()


# Restored from ChessTab-7.1.3 dpt.filespec module and modified to fit.
class FileSpec(filespec.FileSpec):
    """Extend to support DPT Fastload."""

    def __init__(self, **kargs):
        """Define chess database with upper case field names."""
        super().__init__(**kargs)
        for file in self.values():
            file[PRIMARY] = file[PRIMARY].upper()
            file[SECONDARY] = {
                key: key.upper() if value is None else value.upper()
                for key, value in file[SECONDARY].items()
            }
            file[FIELDS] = {
                key.upper(): value for key, value in file[FIELDS].items()
            }


# Restored from SolentwareBase-5.1 core.archivedudpt module and modified
# to fit.
class ArchiveduDPTError(Exception):
    """Raise for calls to _archive_zip or _delete_archive_zip."""


# Restored from SolentwareBase-5.1 core.archivedudpt module and modified
# to fit.
class ArchiveduDPT:
    """Provide deferred update archive methods for DPT interfaces.

    The *_zip() methods are customised to handle the files used to
    support DPT fastunload and fastload.

    The *_bz2() methods raise an exception if called.
    """

    # Restored from SolentwareBase-5.1 core._dpt.Database class.
    import_backup_directory = "__import_backup"

    def archive(self, name=None):
        """Write a backup of database file called name."""
        if name not in self.table:
            raise ArchiveduDPTError(
                str(name).join(
                    ("Import backups for file '", "' cannot be taken")
                )
            )
        for file, table in self.table.items():
            if name != file:
                continue
            # Unload accepts positional arguments only.
            # Want 'dir' argument as '__import_backup' in self.home_directory,
            # not the default '#FASTIO' via definition of FUNLOAD_DIR.
            # So have to specify options where FUNLOAD_DEFAULT, itself defined
            # via FUNLOAD_ALLINFO (at time of writing) which is required
            # option, is the default option.
            outputdir = os.path.join(
                self.home_directory, self.import_backup_directory
            )
            table.opencontext.Unload(FUNLOAD_DEFAULT, None, None, outputdir)
            with open(".".join((outputdir, "grd")), "wb"):
                pass
            break

    def delete_archive(self, name=None):
        """Delete a backup of database file called name."""
        if name not in self.table:
            raise ArchiveduDPTError(
                str(name).join(
                    ("Import backups for file '", "' cannot be deleted")
                )
            )
        outputdir = os.path.join(
            self.home_directory, self.import_backup_directory
        )
        expected_files = set(self._get_zip_archive_names_for_name(name))
        if set(os.listdir(outputdir)) != expected_files:
            raise ArchiveduDPTError(
                str(name).join(
                    ("Import backups for file '", "' are not those expected")
                )
            )
        try:
            os.remove(".".join((outputdir, "grd")))
        except FileNotFoundError:
            pass
        for file in expected_files:
            os.remove(os.path.join(outputdir, file))
        os.rmdir(outputdir)

    # Inverted lists and index trees are all in one file for DPT.
    # Thus a bz2 backup would be expected but attempts to read the file via
    # the open(...) built-in fail with a PermissionError.
    # Try doing DPT fast dump to create the backup: a zip file is needed for
    # the multiple files created, or perhaps a directory is best.  Confirm
    # the technique will work first.
    def _get_zip_archive_names_for_name(self, name):
        """Return specified files and existing operating system files."""
        name_list = []
        for file, table in self.table.items():
            if name != file:
                continue
            filename = table.ddname
            name_list.append("".join((filename, "_TAPED", ".DAT")))
            name_list.append("".join((filename, "_TAPEF", ".DAT")))
            for field in table.fields:
                if field == table.primary:
                    continue
                name_list.append("".join((filename, "_TAPEI_", field, ".DAT")))
            break
        return name_list


class ChessDBrecordGameDUSingleStep(chessrecord.ChessDBrecordGameSequential):
    """Extend with version 7.1.3 import_pgn method.

    The ChessDBrecordGameImport.import_pgn() method from ChessTab-7.1.3
    is added to support DPT single-step deferred updates.  The UI does
    not use this method in import processing but imports to DPT databases
    are a LOT faster if a non-ChessTab UI process uses this method.

    It is a little faster for the other database engines.

    However an interrupted import has to be repeated in full to the
    database after restoring it to the state, from a backup copy, before
    the interrupted import started.
    """

    def import_pgn(
        self, database, source, sourcename, reporter=None, quit_event=None
    ):
        """Update database with games read from source."""
        self.set_database(database)
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Extracting games from " + sourcename)
        ddup = database.deferred_update_points
        db_segment_size = SegmentSize.db_segment_size
        value = self.value
        value.reference = {}
        reference = value.reference
        reference[FILE] = sourcename
        game_number = 0
        for collected_game in value.read_games(source):
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Import stopped.")
                return False
            self.key.recno = None
            value.collected_game = collected_game
            game_number += 1
            reference[GAME] = str(game_number)
            self.put_record(self.database, GAMES_FILE_DEF)
            if self.key.recno % db_segment_size in ddup:
                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Game ",
                                str(game_number),
                                ", to character ",
                                str(collected_game.game_offset),
                                " in PGN, is record ",
                                str(self.key.recno),
                            )
                        )
                    )
                database.commit()
                database.deferred_update_housekeeping()
                database.start_transaction()
        if reporter is not None and value.collected_game is not None:
            reporter.append_text(
                "".join(
                    (
                        str(game_number),
                        " games, to character ",
                        str(value.collected_game.game_offset),
                        " in PGN, read from ",
                        sourcename,
                    )
                )
            )
            reporter.append_text_only("")
        return True


class DPTFileSpecError(Exception):
    """File definition problem in ChessDatabase initialisation."""


class DPTFistatError(Exception):
    """Attempt to open a file when not in deferred update mode."""


class DPTSizingError(Exception):
    """Unable to plan file size increases from PGN import estimates."""


# Renamed from chess_database_du at ChessTab-7.1.3.
def database_du(
    dbpath, *args, file=None, reporter=None, increases=None, **kwargs
):
    """Open database, import games and close database."""
    files = (file,) if file is not None else None

    # Import to games file.
    import_process = multiprocessing.Process(
        target=chess_database_import,
        args=(dbpath, files, *args),
        kwargs={
            "file": file,
            "reporter": reporter,
            "increases": increases,
            **kwargs,
        },
    )
    import_process.start()
    import_process.join()
    if import_process.exitcode != 0:
        return
    del import_process


def _games_file_is_broken(dbpath, files, file=None):
    """Return True if games file is broken, False otherwise."""
    fistat_process = multiprocessing.Process(
        target=chess_database_current_status,
        args=(dbpath, files),
        kwargs={"file": file},
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
        ddnames = get_filespec(**kargs)
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


# Restored from ChessTab-7.1.3 dpt.chessdptnofistat module and modified
# to fit.
class ChessdptError(Exception):
    """Exception class for chessdptnofistat module."""


# Restored from ChessTab-7.1.3 dpt.chessdptnofistat module and modified
# to fit.
class ChessDatabaseNoFistat(basecore_database.Database, dpt_database.Database):
    """Provide access to a database of games of chess."""

    _deferred_update_process = "chesstab.dpt.chessdptdu"

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
        try:
            sysprint = kargs.pop("sysprint")
        except KeyError:
            sysprint = "CONSOLE"
        ddnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        if not kargs.get("allowcreate", False):
            try:
                for dd_name in ddnames:
                    if FILEDESC in ddnames[dd_name]:
                        del ddnames[dd_name][FILEDESC]
            except Exception as error:
                if __name__ == "__main__":
                    raise
                raise ChessdptError("DPT description invalid") from error

        try:
            super().__init__(
                ddnames, databasefolder, sysprint=sysprint, **kargs
            )
        except ChessdptError as error:
            if __name__ == "__main__":
                raise
            raise ChessdptError("DPT description invalid") from error

        self._broken_sizes = {}


class ChessDatabaseImportBackup(ChessDatabaseNoFistat, ArchiveduDPT):
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
    dbe = {}
    for tbl in cdb.table:
        dbe[tbl] = cdb.table[tbl]._dbe
    cdb.close_database_contexts(files=files)
    for tbl in dbe:
        cdb.table[tbl]._dbe = dbe[tbl]
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
