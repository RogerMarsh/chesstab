# database_one_step_du.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

# Restored from ChessTab-7.1.3 chessdptdu module and renamed.

"""Chess database update using DPT single-step deferred update.

This module on Windows only.  Use multi-step module on Wine because Wine
support for a critical function used by single-step is not reliable. There
is no sure way to spot that module is running on Wine.

See www.dptoolkit.com for details of DPT.
"""

import os
import multiprocessing
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
)

from solentware_base import dptdu_database
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    TABLE_B_SIZE,
    BTOD_FACTOR,
    PRIMARY,
    SECONDARY,
    FIELDS,
)
from solentware_base.core.segmentsize import SegmentSize

from .. import ERROR_LOG, APPLICATION_NAME
from ..core import filespec
from ..core.filespec import GAMES_FILE_DEF
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


class ChessDBrecordGameDUSingleStep(chessrecord.ChessDBrecordGameSequential):
    """Extend with version 7.1.3 import_pgn method.

    The ChessDBrecordGameImport.import_pgn() method from ChessTab-7.1.3
    is added to support DPT single-step deferred updates.  The UI does
    not use this method in import processing but imports to DPT databases
    are a LOT faster if a non-ChessTab UI process uses this method.

    It is a little faster than the other database engines.

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


class ChessDBrecordGameFastload(chessrecord.ChessDBrecordGameSequential):
    """Extend with version 7.1.3 import_pgn method.

    The ChessDBrecordGameImport.import_pgn() method from ChessTab-7.1.3
    is added and modified to support DPT fastload.  The UI does not use
    this method in import processing but imports to DPT databases are a
    LOT faster if a non-ChessTab UI process uses this method.

    It is a little faster than the other database engines.

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
        db_segment_size = SegmentSize.db_segment_size * 8
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
            if game_number % db_segment_size == 0:
                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Game ",
                                str(game_number),
                                ", to character ",
                                str(collected_game.game_offset),
                                " in PGN, added to fastload TAPED",
                            )
                        )
                    )
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


class ChessDatabase(dptdu_database.Database):
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
        # for ddname in list(ddnames.keys()):
        #     if ddname != GAMES_FILE_DEF:
        #         del ddnames[ddname]

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

    def get_pages_for_record_counts(self, counts=(0, 0)):
        """Return Table B and Table D pages needed for record counts."""
        brecppg = self.table[GAMES_FILE_DEF].filedesc[BRECPPG]
        return (
            counts[0] // brecppg,
            (counts[1] * self.table[GAMES_FILE_DEF].btod_factor) // brecppg,
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
