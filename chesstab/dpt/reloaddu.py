# reloaddu.py
# Copyright 2026 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions, and Reloaddu class for methods, used by DPT database interface.

The do_reload_deferred_update() method in shared.alldu module cannot be used
because DPT manages segments internally.

"""
import os

from solentware_base.core.constants import (
    SECONDARY,
)
from solentware_base.core import merge
from solentware_base.core import sortsequential

from ..core import utilities
from ..shared import alldu
from ..core import filespec


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
            "_".join(
                (os.path.basename(cdb.generate_database_file_name(file)), file)
            ),
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
        if alldu.index_load_already_done(index_directory, reporter):
            continue
        # Cannot delete the index here in DPT like in the alldu version of
        # load_indicies method.
        writer = cdb.merge_writer(file, index)
        if index == filespec.PIECESQUARE_FIELD_DEF:
            commit_interval = alldu.SHORT_MERGE_COMMIT_INTERVAL
        else:
            commit_interval = alldu.MERGE_COMMIT_INTERVAL
        for count, item in enumerate(merge.next_sorted_item(index_directory)):
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Merge index stopped.")
                if reporter is not None:
                    while not reporter.empty():
                        pass
                writer.close_recordlist()
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
                    writer.flush_key_to_index()
                    writer.close_recordlist()
                    cdb.commit()
                    cdb.deferred_update_housekeeping()
                    cdb.start_transaction()
                    writer.new_recordlist()
            writer.write(item)
        writer.flush_key_to_index()
        writer.close_recordlist()
        if not os.path.basename(index_directory) == "-1":
            try:
                with open(os.path.join(index_directory, "-1"), mode="wb"):
                    pass
            except FileExistsError:
                pass
        alldu.delete_sorted_index_files(index_directory, reporter)

    # DPT database engine needs the test for empty queue because all the
    # deferred index updates are applied in the Close() method called when
    # closing the file on completion of the task (well after exit from
    # do_deferred_update), in particular the C++ code in the dptapi extension,
    # so the queued reports have to be processed before entering that code to
    # avoid an unresponsive GUI; and no indication of progress.
    # The other database engines do not cause the GUI to become unresponsive
    # in the absence of the test for an empty queue.
    if indexing:
        dsize = alldu.pre_unset_file_records_under_reports(cdb, file, reporter)
        cdb.unset_defer_update()
        alldu.post_unset_file_records_under_reports(cdb, file, reporter, dsize)
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
        alldu.delete_sorted_index_directory(index_directory)
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
            if not alldu.du_extract(
                cdb, *args, reporter=reporter, file=file, reload=True, **kwargs
            ):
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text(
                        "Import and index reload not completed."
                    )
                return
        extract_done = alldu.write_indicies_for_extracted_games(
            cdb,
            *args,
            reporter=reporter,
            file=file,
            ignore=ignore,
            sorter=sortsequential.SortDPTIndiciesToSequentialFiles,
            **kwargs,
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
        # The existing indicies are not dumped because a convenient way of
        # deleting an index does not exist: apart from reorganizing the
        # file.
        # The load_indicies method will merge new values for an existing
        # key.  Many updates will insert keys in the middle of the B-tree
        # slowing things down, despite the keys being added in ascending
        # order.
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
            alldu.report_du_exception(cdb, reporter, exc)
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
        alldu.report_database_size_on_import_finish(cdb, reporter)
