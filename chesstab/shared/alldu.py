# alldu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions, and Alldu class for methods, used by most database interfaces.

'Most' means all database interfaces except DPT.
"""
import os
import traceback
import datetime
import shutil

from solentware_base.core.segmentsize import SegmentSize
from solentware_base.core.constants import (
    FILEDESC,
    SECONDARY,
)

from ..core import filespec
from ..core import chessrecord
from ..core import utilities
from ..core import constants
from .. import ERROR_LOG, APPLICATION_NAME

# Two million is chosen because it is close to the number of positions in
# the 32,000 games held in a single default sized segment, assuming each
# game has nearly 40 moves (80 positions).  In direct imports a commit is
# done for each segment.
_MERGE_COMMIT_INTERVAL = 2000000

# The piecesquare index fills the chosen map size increment for Symas LMDB
# well before 2000000 entries added.  It also takes about 10 times as long
# to process these entries compared with most other indicies.
_SHORT_MERGE_COMMIT_INTERVAL = 200000


def du_extract(
    cdb,
    pgnpaths,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    reload=False,
    **kwargs,
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
    reload      By default the update is done directly segment-by-segment.
                Index entries are created to show none of the index tasks
                have been run against the newly added records.
                'reload=True' means dump the existing indicies to a set of
                sorted files, and the indicies for the new records too.
                The existing indicies are deleted and repopulated from the
                sorted files.

    """
    del kwargs
    cdb.start_read_only_transaction()
    try:
        expected_pgnpaths = cdb.get_import_pgn_file_tuple()
        if expected_pgnpaths and set(expected_pgnpaths) != set(pgnpaths):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "Unexpected PGN file names in import list"
                )
                reporter.append_text_only("")
            return False
    finally:
        cdb.end_read_only_transaction()
    if not expected_pgnpaths:
        cdb.start_transaction()
        try:
            cdb.set_import_pgn_file_tuple(pgnpaths)
        finally:
            cdb.commit()
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
    # Put games just stored on database on indexing queues, or on the
    # reload queue if the new games are being indexed by dump, sort new,
    # and reload (the primary field name is used for the reload queue).
    if reload:
        indicies = (filespec.GAME_FIELD_DEF,)
    else:
        indicies = (
            filespec.POSITIONS_FIELD_DEF,
            filespec.PIECESQUARE_FIELD_DEF,
        )
    file_games = cdb.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=cdb.encode_record_selector(filespec.IMPORT_FIELD_DEF),
    )
    for index in indicies:
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
    pgnpaths,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    **kwargs,
):
    """Index games not yet indexed by PGN Tags in open database cdb.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    pgnpaths    List of file names containing imported PGN game scores.
                The basenames are used as keys for games with errors.
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

    """
    del kwargs
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
                "No games need indexing by selected PGN tags."
            )
            reporter.append_text_only("")
        cdb.backout()
        return True
    error_games = _get_error_games(cdb, pgnpaths)
    if error_games.count_records():
        index_games.remove_recordset(error_games)
        index_games_count = index_games.count_records()
        if index_games_count == 0:
            cdb.unfile_records_under(
                filespec.GAMES_FILE_DEF,
                filespec.IMPORT_FIELD_DEF,
                cdb.encode_record_selector(filespec.IMPORT_FIELD_DEF),
            )
            if reporter is not None:
                reporter.append_text(
                    "No games need indexing by selected PGN tags."
                )
                reporter.append_text_only("")
            cdb.commit()
            return True
        cdb.file_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            index_games,
            cdb.encode_record_selector(filespec.IMPORT_FIELD_DEF),
        )
    if reporter is not None:
        reporter.append_text("Index PGN Tags started.")
        reporter.append_text(
            "".join(
                (
                    str(index_games_count),
                    " game needs" if index_games_count == 1 else " games need",
                    " indexing by selected PGN tags.",
                )
            )
        )
        reporter.append_text_only("")
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
    pgnpaths,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    **kwargs,
):
    """Index games not yet indexed by positions in open database cdb.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    pgnpaths    List of file names containing imported PGN game scores.
                The basenames are used as keys for games with errors.
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

    """
    del kwargs
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
            reporter.append_text_only("")
        cdb.backout()
        return True
    error_games = _get_error_games(cdb, pgnpaths)
    if error_games.count_records():
        index_games.remove_recordset(error_games)
        index_games_count = index_games.count_records()
        if index_games_count == 0:
            cdb.unfile_records_under(
                filespec.GAMES_FILE_DEF,
                filespec.IMPORT_FIELD_DEF,
                cdb.encode_record_selector(filespec.POSITIONS_FIELD_DEF),
            )
            if reporter is not None:
                reporter.append_text("No games need indexing by positions.")
                reporter.append_text_only("")
            cdb.commit()
            return True
        cdb.file_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            index_games,
            cdb.encode_record_selector(filespec.POSITIONS_FIELD_DEF),
        )
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
        reporter.append_text_only("")
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


def du_index_piece_squares(
    cdb,
    pgnpaths,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    **kwargs,
):
    """Index games not yet indexed by piece movement in open database cdb.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the deferred updates.
    pgnpaths    List of file names containing imported PGN game scores.
                The basenames are used as keys for games with errors.
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

    """
    del kwargs
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
                        "Unable to index piece squares '",
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
        key=cdb.encode_record_selector(filespec.PIECESQUARE_FIELD_DEF),
    )
    index_games_count = index_games.count_records()
    if index_games_count == 0:
        if reporter is not None:
            reporter.append_text("No games need indexing by piece squares.")
            reporter.append_text_only("")
        cdb.backout()
        return True
    error_games = _get_error_games(cdb, pgnpaths)
    if error_games.count_records():
        index_games.remove_recordset(error_games)
        index_games_count = index_games.count_records()
        if index_games_count == 0:
            cdb.unfile_records_under(
                filespec.GAMES_FILE_DEF,
                filespec.IMPORT_FIELD_DEF,
                cdb.encode_record_selector(filespec.PIECESQUARE_FIELD_DEF),
            )
            if reporter is not None:
                reporter.append_text(
                    "No games need indexing by piece movement."
                )
                reporter.append_text_only("")
            cdb.commit()
            return True
        cdb.file_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            index_games,
            cdb.encode_record_selector(filespec.PIECESQUARE_FIELD_DEF),
        )
    if reporter is not None:
        reporter.append_text("Index piece movement started.")
        reporter.append_text(
            "".join(
                (
                    str(index_games_count),
                    " game needs" if index_games_count == 1 else " games need",
                    " indexing by piece movement.",
                )
            )
        )
        reporter.append_text_only("")
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
        reporter.append_text("Finishing piece square indexing: please wait.")
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


def _dump_index(
    cdb,
    file,
    index,
    dump_directory,
    reporter=None,
    quit_event=None,
):
    """Dump index for file in open database cdb.

    Return True if dump is completed, or False if dump fails or is
    interrupted before it is completed.

    cdb         Database instance which does the dump.
    file        name of table in database to be dumped.
    index       name of index in table in database to be dumped.
    dump_directory   name of directory for index dump files.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.

    """
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text(
            "".join(
                (
                    "Dump '",
                    file,
                    "' file index '",
                    index,
                    "'.",
                )
            )
        )
    index_directory = os.path.join(dump_directory, index)
    try:
        os.mkdir(index_directory)
    except FileExistsError:
        if not os.path.isdir(index_directory):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "".join(
                        (
                            "Unable to dump '",
                            index,
                            "' index because ",
                            index_directory,
                            " is not a directory.",
                        )
                    )
                )
            return False
    if os.path.exists(os.path.join(index_directory, "-1")):
        if reporter is not None:
            reporter.append_text_only(
                "Dump index not needed: load is already done."
            )
        return True
    dump_path = os.path.join(index_directory, index)
    if os.path.exists(dump_path):
        if reporter is not None:
            reporter.append_text_only(
                index.join(
                    (
                        "Existing dump for index '",
                        "' is kept unchanged.",
                    )
                )
            )
        return True
    with open(dump_path, mode="w", encoding="utf-8") as dump_file:
        for record in cdb.find_value_segments(index, file):
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Import stopped.")
                return False
            dump_file.write(repr(record) + "\n")
    return True


def dump_indicies(
    cdb,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    ignore=None,
    **kwargs,
):
    """Dump indicies for file in open database cdb, except those in ignore.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the dump.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be dumped.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    ignore      Indicies to ignore for dump and reload.

    """
    del kwargs
    for key in cdb.table.keys():
        if key == file:
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    (
                        "Unable to dump indicies '",
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
    indicies = set(cdb.specification[file][SECONDARY])
    if ignore is not None:
        indicies.difference_update(ignore)
    dump_directory = os.path.join(
        cdb.get_merge_import_sort_area(),
        "_".join((os.path.basename(cdb.database_file), file)),
    )
    try:
        os.mkdir(dump_directory)
    except FileExistsError:
        if os.path.isdir(dump_directory):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "Existing index file dumps will be kept as found in:"
                )
                reporter.append_text_only(dump_directory)
        else:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "".join(
                        (
                            "Unable to dump '",
                            file,
                            "' indicies because ",
                            dump_directory,
                            " is not a directory.",
                        )
                    )
                )
            while not reporter.empty():
                pass
            cdb.backout()
            return False
    for index in indicies:
        if not _dump_index(
            cdb,
            file,
            index,
            dump_directory,
            reporter=reporter,
            quit_event=quit_event,
        ):
            try:
                os.remove(os.path.join(dump_directory, index))
            except FileNotFoundError:
                pass
            finally:
                if reporter is not None:
                    reporter.append_text_only(
                        index.join(
                            (
                                "Incomplete dump of index '",
                                "' deleted.",
                            )
                        )
                    )
                    while not reporter.empty():
                        pass
                cdb.backout()
            return False

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
            volfree = utilities.bytesize_to_str(
                shutil.disk_usage(cdb.database_file).free
            )
            dbsize = utilities.bytesize_to_str(
                os.path.getsize(cdb.database_file)
            )
            reporter.append_text_only("")
            reporter.append_text("Database size before index rebuild.")
            reporter.append_text_only(
                "".join((volfree, " is available after index dump."))
            )
            reporter.append_text_only(
                "".join((dbsize, " is size of database before index reload."))
            )
    else:
        if reporter is not None:
            while not reporter.empty():
                pass
        cdb.commit()
    return True


def write_indicies_for_extracted_games(
    cdb,
    pgnpaths,
    file=None,
    reporter=None,
    quit_event=None,
    **kwargs,
):
    """Dump indicies for new games in database cdb, except those in ignore.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the dump.
    pgnpaths    List of file names containing imported PGN game scores.
                The basenames are used as keys for games with errors.
    file        name of table in database to be dumped.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.

    """
    del kwargs
    importer = chessrecord.ChessDBrecordGameSequential(
        valueclass=chessrecord.ChessDBvaluePGNMergeUpdate
    )
    for key in cdb.table.keys():
        if key == file:
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    (
                        "Unable to merge index games '",
                        "': not found in database.",
                    )
                )
            )
            reporter.append_text_only("")
        return False

    cdb.start_transaction()
    index_games = cdb.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=cdb.encode_record_selector(filespec.GAME_FIELD_DEF),
    )
    index_games_count = index_games.count_records()
    if index_games_count == 0:
        if reporter is not None:
            reporter.append_text(
                "No games need indexing via merge index games."
            )
            reporter.append_text_only("")
        cdb.backout()
        return None
    error_games = _get_error_games(cdb, pgnpaths)
    if error_games.count_records():
        index_games.remove_recordset(error_games)
        index_games_count = index_games.count_records()
        if index_games_count == 0:
            cdb.unfile_records_under(
                filespec.GAMES_FILE_DEF,
                filespec.IMPORT_FIELD_DEF,
                cdb.encode_record_selector(filespec.GAME_FIELD_DEF),
            )
            if reporter is not None:
                reporter.append_text(
                    "".join(
                        (
                            "No games without errors need indexing ",
                            "via merge index games.",
                        )
                    )
                )
                reporter.append_text_only("")
            cdb.commit()
            return None
        cdb.file_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            index_games,
            cdb.encode_record_selector(filespec.GAME_FIELD_DEF),
        )
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Dump indicies for extracted games started.")
        reporter.append_text(
            "".join(
                (
                    str(index_games_count),
                    " game needs" if index_games_count == 1 else " games need",
                    " indexing via merge index.",
                )
            )
        )
    guard_file = os.path.join(
        cdb.get_merge_import_sort_area(),
        "_".join(
            (os.path.basename(cdb.database_file), filespec.GAMES_FILE_DEF)
        ),
        "0",
    )
    if os.path.exists(guard_file):
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "Index dumps for extracted games assumed to exist."
            )
            reporter.append_text_only(
                "Guard file '0' exists in dump directory:"
            )
            reporter.append_text_only(os.path.dirname(guard_file))
        cdb.commit()
        return True
    _remove_games_in_sequential_files_from_index_games(
        cdb, index_games, reporter=reporter
    )
    if not importer.write_index_entries_to_sequential_files(
        cdb,
        index_games,
        reporter=reporter,
        quit_event=quit_event,
    ):
        cdb.backout()
        return False
    if reporter is not None:
        # Thought to be necessary with DPT in some circumstances.
        while not reporter.empty():
            pass
    cdb.commit()
    return True


def _remove_games_in_sequential_files_from_index_games(
    cdb, index_games, reporter=None
):
    """Remove games fully referenced in sequential files from index_games.

    Assume no games are fully refernced if maximum number of files in an
    index directory is 1.

    """
    sort_area = os.path.join(
        cdb.get_merge_import_sort_area(),
        "_".join(
            (os.path.basename(cdb.database_file), filespec.GAMES_FILE_DEF)
        ),
    )
    if not os.path.isdir(sort_area):
        return
    indicies = set(cdb.specification[filespec.GAMES_FILE_DEF][SECONDARY])
    directories = os.listdir(sort_area)
    if indicies.difference(
        directories + ["pgnfile", "cqleval", "import", "pgnerror", "cqlquery"]
    ):
        if reporter is not None:
            reporter.append_text(
                "Writing index entries for first segment was not completed."
            )
            reporter.append_text_only("")
        return
    segments = set()
    for index in directories:
        segments |= set(os.listdir(os.path.join(sort_area, index)))
    if len(segments) < 2:
        if reporter is not None:
            reporter.append_text(
                "Writing index entries for second segment was not started."
            )
            reporter.append_text_only("")
        return
    written = cdb.recordlist_record_number_range(
        filespec.GAMES_FILE_DEF,
        keyend=max(int(i) for i in segments) * SegmentSize.db_segment_size - 1,
    )
    try:
        index_games.remove_recordset(written)
        if reporter is not None:
            reporter.append_text_only(
                "Index entries for first "
                + str(written.count_records())
                + " records already writtem to sequential files."
            )
    finally:
        written.close()


def _delete_sorted_index_directory(index_directory):
    """Delete sorted index files in index_directory.

    A "-1" file is assumed to contain sorted index entries.

    """
    index = os.path.basename(index_directory)
    for dumpfile in os.listdir(index_directory):
        if dumpfile.isdigit() or dumpfile == index:
            try:
                os.remove(os.path.join(index_directory, dumpfile))
            except FileNotFoundError:
                pass


def _delete_sorted_index_files(index_directory, reporter):
    """Delete sorted index files if basename of index_directory is not '-1'.

    File '-1' is created on completion of load index.  If it exists delete
    the sorted index files.

    """
    if os.path.basename(index_directory) == "-1":
        if reporter is not None:
            reporter.append_text(
                "Cannot tell if index load is done because '-1' is an index."
            )
            reporter.append_text_only(
                "Files of sorted index entries are not deleted."
            )
        return
    if not os.path.exists(os.path.join(index_directory, "-1")):
        if reporter is not None:
            reporter.append_text("Guard file '-1' does not exist.")
            reporter.append_text_only(
                "Files of sorted index entries are not deleted."
            )
        return
    _delete_sorted_index_directory(index_directory)


def _index_load_already_done(index_directory, reporter):
    """Return True if file '-1' is in index_directory and is not basename.

    Return False otherwise.

    File '-1' is created on completion of load index, followed by deleting
    all the sorted files of index entries.  A failure while doing these
    deletions will leave some still existing, so do the deletion step here
    too.

    Return False if the basename of index_directory is '-1' because that
    implies the file '-1' contains index entries for the '-1' index.

    """
    if os.path.basename(index_directory) == "-1":
        if reporter is not None:
            reporter.append_text(
                "Cannot tell if index load is done because '-1' is an index."
            )
        return False
    if not os.path.exists(os.path.join(index_directory, "-1")):
        return False
    _delete_sorted_index_files(index_directory, None)
    if reporter is not None:
        reporter.append_text("Load is already done.")
    return True


def load_indicies(
    cdb,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    ignore=None,
    **kwargs,
):
    """Load indicies for file in open database cdb, except those in ignore.

    Return True if indexing is completed, or False if indexing fails or is
    interrupted before it is completed.

    cdb         Database instance which does the dump.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be dumped.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    ignore      Indicies to ignore for dump and reload.

    """
    del kwargs
    for key in cdb.table.keys():
        if key == file:
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    (
                        "Unable to load indicies '",
                        "': not found in database.",
                    )
                )
            )
            reporter.append_text_only("")
        return False
    cdb.start_read_only_transaction()
    try:
        dump_directory = os.path.join(
            cdb.get_merge_import_sort_area(),
            "_".join((os.path.basename(cdb.database_file), file)),
        )
    finally:
        cdb.end_read_only_transaction()
    if not os.path.isdir(dump_directory):
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(dump_directory)
            reporter.append_text_only("does not exist or is not a directory")
            reporter.append_text_only("")
        return False

    if indexing:
        cdb.set_defer_update()
    else:
        cdb.start_transaction()
    indicies = set(cdb.specification[file][SECONDARY])
    if ignore is not None:
        indicies.difference_update(ignore)
    for index in indicies:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "".join(
                    (
                        "Load '",
                        file,
                        "' file index '",
                        index,
                        "'.",
                    )
                )
            )
        index_directory = os.path.join(dump_directory, index)
        if not os.path.isdir(index_directory):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "".join(
                        (
                            "Unable to load '",
                            index,
                            "' index because ",
                            index_directory,
                            " is not a directory.",
                        )
                    )
                )
            continue
        if _index_load_already_done(index_directory, reporter):
            continue
        cdb.delete_index(file, index)
        writer = cdb.merge_writer(file, index)
        if index == filespec.PIECESQUARE_FIELD_DEF:
            commit_interval = _SHORT_MERGE_COMMIT_INTERVAL
        else:
            commit_interval = _MERGE_COMMIT_INTERVAL
        for count, item in enumerate(cdb.next_sorted_item(index_directory)):
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Merge index stopped.")
                if reporter is not None:
                    while not reporter.empty():
                        pass
                writer.close_cursor()
                cdb.backout()
                return False
            if not count % commit_interval:
                if count:
                    if reporter is not None:
                        reporter.append_text(
                            "".join(
                                (
                                    format(count, ","),
                                    " entries added to '",
                                    index,
                                    "' index.",
                                )
                            )
                        )
                    writer.close_cursor()
                    cdb.commit()
                    cdb.deferred_update_housekeeping()
                    cdb.start_transaction()
                    writer.make_new_cursor()
            writer.write(item)
        writer.close_cursor()
        if not os.path.basename(index_directory) == "-1":
            try:
                with open(os.path.join(index_directory, "-1"), mode="wb"):
                    pass
            except FileExistsError:
                pass
        _delete_sorted_index_files(index_directory, reporter)

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

    cdb.start_transaction()
    try:
        cdb.unfile_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            cdb.encode_record_selector(filespec.GAME_FIELD_DEF),
        )
        cdb.unfile_records_under(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            cdb.encode_record_selector(filespec.IMPORT_FIELD_DEF),
        )
    finally:
        cdb.commit()
    for index in indicies:
        index_directory = os.path.join(dump_directory, index)
        if not os.path.isdir(index_directory):
            continue
        # '<index_directory>/-1' may be a guard or a file of index items.
        _delete_sorted_index_directory(index_directory)
        try:
            os.remove(os.path.join(index_directory, "-1"))
        except FileNotFoundError:
            pass

        try:
            os.rmdir(index_directory)
        except FileNotFoundError:
            pass
        except OSError:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "".join(
                        (
                            "Directory for '",
                            index,
                            "' not deleted: probably not empty.",
                        )
                    )
                )
    try:
        os.remove(os.path.join(dump_directory, "0"))
    except FileNotFoundError:
        pass
    try:
        os.rmdir(dump_directory)
    except FileNotFoundError:
        pass
    except OSError:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "".join(
                    (
                        "Dump directory '",
                        dump_directory,
                        "' not deleted: probably not empty.",
                    )
                )
            )
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
        if not utilities.is_import_without_index_reload_in_progress_txn(cdb):
            if utilities.is_import_in_progress_txn(cdb):
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Cannot do requested import:")
                    reporter.append_text_only(
                        "An import with index merge is being done."
                    )
                return
        if not du_extract(cdb, *args, reporter=reporter, file=file, **kwargs):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Import not completed.")
            return
        if not du_index_pgn_tags(
            cdb, *args, reporter=reporter, file=file, **kwargs
        ):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Import not completed.")
            return
        if not du_index_positions(
            cdb, *args, reporter=reporter, file=file, **kwargs
        ):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Import not completed.")
            return
        if not du_index_piece_squares(
            cdb, *args, reporter=reporter, file=file, **kwargs
        ):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Import not completed.")
            return
        cdb.start_transaction()
        try:
            cdb.delete_import_pgn_file_tuple()
        finally:
            cdb.commit()
    finally:
        cdb.close_database()
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Import finished.")
        _report_database_size_on_import_finish(cdb, reporter)


def do_reload_deferred_update(
    cdb, *args, reporter=None, file=None, ignore=None, **kwargs
):
    """Open database, extract and index games, and close database."""
    cdb.open_database()
    try:
        if utilities.is_import_without_index_reload_in_progress_txn(cdb):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Cannot do requested merge import:")
                reporter.append_text_only(
                    "An import without index merge is being done."
                )
            return
        if utilities.is_import_with_index_reload_started_txn(cdb):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("A merge import is already in progress.")
                reporter.append_text_only(
                    "It continues without adding games from PGN files."
                )
        else:
            if not du_extract(
                cdb, *args, reporter=reporter, file=file, reload=True, **kwargs
            ):
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text(
                        "Import and index reload not completed."
                    )
                return
        extract_done = write_indicies_for_extracted_games(
            cdb, *args, reporter=reporter, file=file, ignore=ignore, **kwargs
        )
        if extract_done is False:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "Write new indicies to sorted files not completed."
                )
            return
        if extract_done is None:
            cdb.start_transaction()
            try:
                cdb.delete_import_pgn_file_tuple()
            finally:
                cdb.commit()
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Import finished.")
            return
        if not dump_indicies(
            cdb, *args, reporter=reporter, file=file, ignore=ignore, **kwargs
        ):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text("Dump existing indicies not completed.")
            return
        try:
            if not load_indicies(
                cdb,
                *args,
                reporter=reporter,
                file=file,
                ignore=ignore,
                **kwargs,
            ):
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Load indicies not completed.")
                return
        except Exception as exc:
            _report_exception(cdb, reporter, exc)
            raise
        cdb.start_transaction()
        try:
            cdb.delete_import_pgn_file_tuple()
        finally:
            cdb.commit()
    finally:
        cdb.close_database()
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Import and index reload finished.")
        _report_database_size_on_import_finish(cdb, reporter)


def _report_database_size_on_import_finish(cdb, reporter):
    """Report database size on completing import."""
    volfree = utilities.bytesize_to_str(
        shutil.disk_usage(cdb.database_file).free
    )
    dbsize = utilities.bytesize_to_str(os.path.getsize(cdb.database_file))
    reporter.append_text_only("")
    reporter.append_text_only("Database size.")
    reporter.append_text_only("".join((volfree, " is available.")))
    reporter.append_text_only("".join((dbsize, " is size of database.")))


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
    names = filespec.make_filespec()
    if not kargs.get("allowcreate", False):
        for table_name in names:
            if FILEDESC in names[table_name]:
                del names[table_name][FILEDESC]
    return names


def _get_error_games(database, pgnpaths):
    """Return recordlist of error records for paths in pgnpaths."""
    trimmed = database.recordlist_nil(filespec.GAMES_FILE_DEF)
    for name in pgnpaths:
        trimmed |= database.recordlist_key(
            filespec.GAMES_FILE_DEF,
            filespec.PGN_ERROR_FIELD_DEF,
            key=database.encode_record_selector(os.path.basename(name)),
        )
    return trimmed


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

    def get_merge_import_sort_area(self):
        """Return sort area in application control or database directory."""
        return self.get_application_control().get(
            constants.SORT_AREA, super().get_merge_import_sort_area()
        )

    def get_import_pgn_file_tuple(self):
        """Return PGN file list in application control or empty list."""
        return self.get_application_control().get(constants.PGN_FILES, ())

    def set_import_pgn_file_tuple(self, names):
        """Return PGN file list in application control or empty list."""
        appcontrol = self.get_application_control()
        appcontrol[constants.PGN_FILES] = names
        self.set_application_control(appcontrol)

    def delete_import_pgn_file_tuple(self):
        """Delete PGN file list from application control."""
        appcontrol = self.get_application_control()
        del appcontrol[constants.PGN_FILES]
        self.set_application_control(appcontrol)
