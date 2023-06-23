# alldu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions, and Alldu class for methods, used by most database interfaces.

'Most' means all database interfaces except DPT.
"""
import os
import traceback
import datetime

from solentware_base.core.segmentsize import SegmentSize
from solentware_base.core.constants import FILEDESC

from ..core.filespec import FileSpec
from ..core.chessrecord import ChessDBrecordGameImport
from .. import ERROR_LOG, APPLICATION_NAME


def chess_du_import(cdb, pgnpaths, reporter=None, quit_event=None):
    """Import games from pgnpaths into open database cdb."""
    importer = ChessDBrecordGameImport()
    cdb.set_defer_update()
    try:
        for pgnfile in pgnpaths:
            with open(pgnfile, "r", encoding="iso-8859-1") as source:
                if not importer.import_pgn(
                    cdb,
                    source,
                    pgnfile,
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
        errorlog_written = True
        try:
            with open(
                os.path.join(cdb.home_directory, ERROR_LOG),
                "a",
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
        except:
            errorlog_written = False
        if reporter is not None:
            reporter.append_text("An exception has occured during import:")
            reporter.append_text_only("")
            reporter.append_text_only(str(exc))
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
        raise
    cdb.unset_defer_update()
    if reporter is not None:
        reporter.append_text("Import finished.")
        reporter.append_text_only("")


def chess_du(cdb, pgnpaths, file_records=None, reporter=None, quit_event=None):
    """Open database, import games and close database."""
    del file_records
    cdb.open_database()
    chess_du_import(cdb, pgnpaths, reporter=reporter, quit_event=quit_event)
    cdb.close_database()


def get_filespec(**kargs):
    """Return FileSpec instance with FILEDESCs removed at **kargs request.

    The FILEDESCs are deleted if allowcreate is False, the default.
    """
    names = FileSpec(**kargs)
    if not kargs.get("allowcreate", False):
        for table_name in names:
            if FILEDESC in names[table_name]:
                del names[table_name][FILEDESC]
    return names


class Alldu:
    """Provide deferred update methods shared by all interfaces.

    All the supported engines follow DPT in dividing the numeric primary
    keys into fixed-size segments.  When importing games a large amount of
    memory is required depending on number of games.  Some operating
    systems limit the memory available to a process.  The class attribute
    deferred_update_points is set when the segment size is greater than
    32768 in an attempt to avoid a MemoryError exception.
    """

    # The optimum chunk size is the segment size.
    # Assuming 2Gb memory:
    # A default FreeBSD user process will not cause a MemoryError exception for
    # segment sizes up to 65536 records, so the optimum chunk size defined in
    # the superclass will be selected.
    # A MS Windows XP process will cause the MemoryError exeption which selects
    # the 32768 game chunk size.
    # A default OpenBSD user process will cause the MemoryError exception which
    # selects the 16384 game chunk size.
    # The error log problem fixed at chesstab-0.41.9 obscured what was actually
    # happening: OpenBSD gives a MemoryError exception but MS Windows XP heads
    # for thrashing swap space in some runs with a 65536 chunk size (depending
    # on order of processing indexes I think). Windows 10 Task Manager display
    # made this obvious.
    # The MemoryError exception or swap space thrashing will likely not occur
    # for a default OpenBSD user process or a MS Windows XP process with
    # segment sizes up to 32768 records. Monitoring with Top and Task Manager
    # suggests it gets close with OpenBSD.

    # pylint comparison-with-callable report is false positive.
    # Perhaps because db_segment_size is a property and the last statement
    # in segmentsize module is 'SegmentSize = SegmentSize()'.
    if SegmentSize.db_segment_size > 32768:
        for f, m in ((4, 700000000), (2, 1400000000)):
            try:
                b" " * m
            except MemoryError:

                # Override the value in the superclass.
                deferred_update_points = frozenset(
                    i
                    for i in range(
                        65536 // f - 1,
                        SegmentSize.db_segment_size,
                        65536 // f,
                    )
                )

                break
        del f, m

    def do_final_segment_deferred_updates(self):
        """Extend to report number of games in final segment."""
        super().do_final_segment_deferred_updates()
