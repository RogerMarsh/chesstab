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

from ..core import filespec
from ..core import chessrecord
from .. import ERROR_LOG, APPLICATION_NAME


def du_extract(
    cdb,
    pgnpaths,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from pgnpaths into open database cdb.

    Return True if import is completed, or False if import fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    pgnpaths    List of file names containing PGN game scores to be imported.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be updated.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    increases   <obsolete>? <for DPT only> <pre-import table size increases>
                intention is increase data and index sizes during import,
                especially if it is possible to recover from Table D full
                conditions simply by increasing the index size and repeating
                the import without adding any records (and re-applying any
                left over deferred index updates).
                Increase during import is allowed only if no recordsets,
                cursors, and so forth, are open on the table (DPT file)
                being updated.

    """
    del increases
    importer = chessrecord.ChessDBrecordGameStore()
    for key in cdb.table.keys():
        if key == file:
            # if increases is None:
            #    counts = [0, 0]
            # else:
            #    counts = [increases[0], increases[1]]
            # cdb.increase_database_record_capacity(files={key: counts})
            # _du_report_increases(reporter, key, counts)
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
        return False
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Import started.")
    if indexing:
        cdb.set_defer_update()
    else:
        cdb.start_transaction()
    try:
        for pgnfile in pgnpaths:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "Check file encoding is utf-8 or iso-8859-1."
                )
            encoding = _try_file_encoding(pgnfile)
            if encoding is None:
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text(
                        "".join(
                            (
                                "Unable to read ",
                                os.path.basename(pgnfile),
                                " as utf-8 or iso-8859-1 ",
                                "encoding.",
                            )
                        )
                    )
                cdb.backout()
                return False
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("".join(("Encoding is ", encoding, ".")))
            with open(pgnfile, mode="r", encoding=encoding) as source:
                if not importer.import_pgn(
                    cdb,
                    source,
                    os.path.basename(pgnfile),
                    reporter=reporter,
                    quit_event=quit_event,
                ):
                    cdb.backout()
                    return False
        if reporter is not None:
            reporter.append_text("Finishing extract: please wait.")
            reporter.append_text_only("")
        if indexing:
            cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # Put games just stored on database on indexing queues.
    file_games = cdb.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=cdb.encode_record_selector(filespec.IMPORT_FIELD_DEF),
    )
    for index in (
        filespec.POSITIONS_FIELD_DEF,
        filespec.PIECESQUAREMOVE_FIELD_DEF,
    ):
        key = cdb.encode_record_selector(index)
        index_games = cdb.recordlist_key(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            key=key,
        )
        index_games |= file_games
        cdb.file_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            index_games,
            key,
        )
        index_games.close()
    file_games.close()

    # DPT database engine needs the test for empty queue because all the
    # deferred index updates are applied in the Close() method called when
    # closing the file on completion of the task (well after exit from
    # do_deferred_update), in particular the C++ code in the dptapi extension,
    # so the queued reports have to be processed before entering that code to
    # avoid an unresponsive GUI; and no indication of progress.
    # The other database engines do not cause the GUI to become unresponsive
    # in the absence of the test for an empty queue.
    if indexing:
        dsize = _pre_unset_file_records_under_reports(cdb, file, reporter)
        cdb.unset_defer_update()
        _post_unset_file_records_under_reports(cdb, file, reporter, dsize)
        if reporter is not None:
            while not reporter.empty():
                pass
    else:
        if reporter is not None:
            while not reporter.empty():
                pass
        cdb.commit()
    return True


def du_index_pgn_tags(
    cdb,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Index games not yet indexed by PGN Tags in open database cdb.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be updated.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    increases   <obsolete>? <for DPT only> <pre-import table size increases>
                intention is increase data and index sizes during import,
                especially if it is possible to recover from Table D full
                conditions simply by increasing the index size and repeating
                the import without adding any records (and re-applying any
                left over deferred index updates).
                Increase during import is allowed only if no recordsets,
                cursors, and so forth, are open on the table (DPT file)
                being updated.

    """
    del increases
    importer = chessrecord.ChessDBrecordGamePGNTags()
    for key in cdb.table.keys():
        if key == file:
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to index PGN Tags '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return False

    if indexing:
        cdb.set_defer_update()
    else:
        cdb.start_transaction()
    index_games = cdb.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=cdb.encode_record_selector(filespec.IMPORT_FIELD_DEF),
    )
    index_games_count = index_games.count_records()
    if index_games_count == 0:
        if reporter is not None:
            reporter.append_text(
                "No games need indexing by PGN tags in Seven Tag Roster."
            )
            reporter.append_text_only("")
        cdb.backout()
        return True
    if reporter is not None:
        reporter.append_text("Index PGN Tags started.")
        reporter.append_text(
            "".join(
                (
                    str(index_games_count),
                    " game needs" if index_games_count == 1 else " games need",
                    " indexing by PGN tags in Seven Tag Roster.",
                )
            )
        )
        reporter.append_text_only(
            " ".join(
                (
                    "This takes about thiteen minutes per million",
                    "games indexed.",
                )
            )
        )
    if not importer.index_pgn_tags(
        cdb,
        index_games,
        reporter=reporter,
        quit_event=quit_event,
    ):
        cdb.backout()
        return False
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Finishing PGN tag indexing: please wait.")
        reporter.append_text_only("")
    # if indexing:
    #    cdb.do_final_segment_deferred_updates(write_ebm=False)

    # DPT database engine needs the test for empty queue because all the
    # deferred index updates are applied in the Close() method called when
    # closing the file on completion of the task (well after exit from
    # do_deferred_update), in particular the C++ code in the dptapi extension,
    # so the queued reports have to be processed before entering that code to
    # avoid an unresponsive GUI; and no indication of progress.
    # The other database engines do not cause the GUI to become unresponsive
    # in the absence of the test for an empty queue.
    if indexing:
        dsize = _pre_unset_file_records_under_reports(cdb, file, reporter)
        cdb.unset_defer_update()
        _post_unset_file_records_under_reports(cdb, file, reporter, dsize)
        if reporter is not None:
            while not reporter.empty():
                pass
    else:
        if reporter is not None:
            while not reporter.empty():
                pass
        cdb.commit()
    return True


def du_index_positions(
    cdb,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Index games not yet indexed by positions in open database cdb.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be updated.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    increases   <obsolete>? <for DPT only> <pre-import table size increases>
                intention is increase data and index sizes during import,
                especially if it is possible to recover from Table D full
                conditions simply by increasing the index size and repeating
                the import without adding any records (and re-applying any
                left over deferred index updates).
                Increase during import is allowed only if no recordsets,
                cursors, and so forth, are open on the table (DPT file)
                being updated.

    """
    del increases
    importer = chessrecord.ChessDBrecordGameTransposition()
    for key in cdb.table.keys():
        if key == file:
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    (
                        "Unable to index positions '",
                        "': not found in database.",
                    )
                )
            )
            reporter.append_text_only("")
        return False

    if indexing:
        cdb.set_defer_update()
    else:
        cdb.start_transaction()
    index_games = cdb.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=cdb.encode_record_selector(filespec.POSITIONS_FIELD_DEF),
    )
    index_games_count = index_games.count_records()
    if index_games_count == 0:
        if reporter is not None:
            reporter.append_text("No games need indexing by positions.")
        cdb.backout()
        return True
    if reporter is not None:
        reporter.append_text("Index positions started.")
        reporter.append_text(
            "".join(
                (
                    str(index_games_count),
                    " game needs" if index_games_count == 1 else " games need",
                    " indexing by positions.",
                )
            )
        )
        reporter.append_text_only(
            " ".join(
                (
                    "This takes several hours (>3) per million",
                    "games indexed.",
                )
            )
        )
    if not importer.index_positions(
        cdb,
        index_games,
        reporter=reporter,
        quit_event=quit_event,
    ):
        cdb.backout()
        return False
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Finishing position indexing: please wait.")
        reporter.append_text_only("")
    # if indexing:
    #    cdb.do_final_segment_deferred_updates(write_ebm=False)

    # DPT database engine needs the test for empty queue because all the
    # deferred index updates are applied in the Close() method called when
    # closing the file on completion of the task (well after exit from
    # do_deferred_update), in particular the C++ code in the dptapi extension,
    # so the queued reports have to be processed before entering that code to
    # avoid an unresponsive GUI; and no indication of progress.
    # The other database engines do not cause the GUI to become unresponsive
    # in the absence of the test for an empty queue.
    if indexing:
        dsize = _pre_unset_file_records_under_reports(cdb, file, reporter)
        cdb.unset_defer_update()
        _post_unset_file_records_under_reports(cdb, file, reporter, dsize)
        if reporter is not None:
            while not reporter.empty():
                pass
    else:
        if reporter is not None:
            while not reporter.empty():
                pass
        cdb.commit()
    return True


def du_index_piece_locations(
    cdb,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Index games not yet indexed by piece locations in open database cdb.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be updated.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    increases   <obsolete>? <for DPT only> <pre-import table size increases>
                intention is increase data and index sizes during import,
                especially if it is possible to recover from Table D full
                conditions simply by increasing the index size and repeating
                the import without adding any records (and re-applying any
                left over deferred index updates).
                Increase during import is allowed only if no recordsets,
                cursors, and so forth, are open on the table (DPT file)
                being updated.

    """
    del increases
    importer = chessrecord.ChessDBrecordGamePieceLocation()
    for key in cdb.table.keys():
        if key == file:
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    (
                        "Unable to index piece locations '",
                        "': not found in database.",
                    )
                )
            )
            reporter.append_text_only("")
        return False

    if indexing:
        cdb.set_defer_update()
    else:
        cdb.start_transaction()
    index_games = cdb.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=cdb.encode_record_selector(filespec.PIECESQUAREMOVE_FIELD_DEF),
    )
    index_games_count = index_games.count_records()
    if index_games_count == 0:
        if reporter is not None:
            reporter.append_text("No games need indexing by positions.")
        cdb.backout()
        return True
    if reporter is not None:
        reporter.append_text("Index piece locations started.")
        reporter.append_text(
            "".join(
                (
                    str(index_games_count),
                    " game needs" if index_games_count == 1 else " games need",
                    " indexing by piece locations.",
                )
            )
        )
        reporter.append_text_only(
            " ".join(
                (
                    "This takes many hours (>10) per million",
                    "games indexed.",
                )
            )
        )
    if not importer.index_piece_locations(
        cdb,
        index_games,
        reporter=reporter,
        quit_event=quit_event,
    ):
        cdb.backout()
        return False
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Finishing piece location indexing: please wait.")
        reporter.append_text_only("")
    # if indexing:
    #    cdb.do_final_segment_deferred_updates(write_ebm=False)

    # DPT database engine needs the test for empty queue because all the
    # deferred index updates are applied in the Close() method called when
    # closing the file on completion of the task (well after exit from
    # do_deferred_update), in particular the C++ code in the dptapi extension,
    # so the queued reports have to be processed before entering that code to
    # avoid an unresponsive GUI; and no indication of progress.
    # The other database engines do not cause the GUI to become unresponsive
    # in the absence of the test for an empty queue.
    if indexing:
        dsize = _pre_unset_file_records_under_reports(cdb, file, reporter)
        cdb.unset_defer_update()
        _post_unset_file_records_under_reports(cdb, file, reporter, dsize)
        if reporter is not None:
            while not reporter.empty():
                pass
    else:
        if reporter is not None:
            while not reporter.empty():
                pass
        cdb.commit()
    return True


def _try_file_encoding(pgnpath):
    """Return encoding able to read pgnpath or None.

    The PGN specification assumes iso-8859-1 encoding but try utf-8
    encoding first.

    The iso-8859-1 will read anything at the expense of possibly making
    a mess of encoded non-ASCII characters if the utf-8 encoding fails
    to read pgnpath.

    The time taken to read the entire file just to determine the encoding
    is either small compared with the time to process the PGN content or
    just small.  The extra read implied by this function is affordable.

    """
    encoding = None
    for try_encoding in ("utf-8", "iso-8859-1"):
        with open(pgnpath, mode="r", encoding=try_encoding) as pgntext:
            try:
                while True:
                    if not pgntext.read(1024 * 1000):
                        encoding = try_encoding
                        break
            except UnicodeDecodeError:
                pass
    return encoding


# DPT database engine specific.
# Maybe will have to go into solentwre_base, but do not want the reporter
# code there.
# Non-DPT code has get_database_table_sizes() return {}.
# Problem is DPT does things in unset_defer_update which need before and
# after reports, while other engines do different things which do not
# need reports at all.
def _pre_unset_file_records_under_reports(database, file, reporter):
    """Generate reports relevant to database engine before completion."""
    if reporter is None:
        return None
    for name, sizes in database.get_database_table_sizes(
        files=set((file,))
    ).items():
        reporter.append_text(
            "".join(("Data import for ", name, " completed."))
        )
        dsize = sizes["DSIZE"]
        reporter.append_text_only(
            "Data area size after import: " + str(sizes["BSIZE"])
        )
        reporter.append_text_only(
            "".join(
                (
                    "Data pages used in import: ",
                    str(
                        sizes["BHIGHPG"]
                        - database.table[name].table_b_pages_used
                    ),
                )
            )
        )
        reporter.append_text_only(
            "Index area size before import: " + str(dsize)
        )
        reporter.append_text_only("")
        return dsize


# DPT database engine specific.
# Maybe will have to go into solentwre_base, but do not want the reporter
# code there.
# Non-DPT code has get_database_table_sizes() return {}.
# Problem is DPT does things in unset_defer_update which need before and
# after reports, while other engines do different things which do not
# need reports at all.
def _post_unset_file_records_under_reports(database, file, reporter, dsize):
    """Generate reports relevant to database engine after completion."""
    if reporter is None:
        return
    for name, sizes in database.get_database_table_sizes(
        files=set((file,))
    ).items():
        reporter.append_text("".join(("Index size status for ", name, ".")))
        new_dsize = sizes["DSIZE"]
        reporter.append_text_only("Index area size: " + str(new_dsize))
        reporter.append_text_only(
            "".join(
                (
                    "Index area size increase: ",
                    str(new_dsize - dsize),
                )
            )
        )
        reporter.append_text_only(
            "".join(
                (
                    "Index area free: ",
                    str(new_dsize - sizes["DPGSUSED"]),
                )
            )
        )
        reporter.append_text_only("")
        reporter.append_text(
            "".join(("Applying Index update for ", name, ": please wait."))
        )
        reporter.append_text_only("")


def do_deferred_update(cdb, *args, reporter=None, file=None, **kwargs):
    """Open database, extract and index games, and close database."""
    cdb.open_database()
    try:
        if not du_extract(cdb, *args, reporter=reporter, file=file, **kwargs):
            if reporter is not None:
                reporter.append_text("Import not completed.")
                reporter.append_text_only("")
            return
        if not du_index_pgn_tags(cdb, reporter=reporter, file=file, **kwargs):
            if reporter is not None:
                reporter.append_text("Import not completed.")
                reporter.append_text_only("")
            return
        if not du_index_positions(cdb, reporter=reporter, file=file, **kwargs):
            if reporter is not None:
                reporter.append_text("Import not completed.")
                reporter.append_text_only("")
            return
        if not du_index_piece_locations(
            cdb, reporter=reporter, file=file, **kwargs
        ):
            if reporter is not None:
                reporter.append_text("Import not completed.")
                reporter.append_text_only("")
            return
    finally:
        cdb.close_database()
    if reporter is not None:
        reporter.append_text("Import finished.")
        reporter.append_text_only("")


def _du_report_increases(reporter, file, size_increases):
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
    except OSError:
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


def get_filespec(**kargs):
    """Return FileSpec instance with FILEDESCs removed at **kargs request.

    The FILEDESCs are deleted if allowcreate is False, the default.
    """
    names = filespec.FileSpec(**kargs)
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
