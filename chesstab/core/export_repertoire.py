# export_repertoire.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess repertoire exporters."""

import os

from . import chessrecord, filespec, count_export
from .export_pgn_import_format import get_game_pgn_import_format

_ENCODING = "utf-8"


def export_all_repertoires_pgn(database, filename, statusbar):
    """Export all repertoires in PGN export format."""
    if filename is None:
        return
    statusbar.status.update()
    statusbar.set_status_text("Started: repertoire PGN format")
    statusbar.status.update_idletasks()
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.REPERTOIRE_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    if instance.value.collected_game.is_pgn_valid():
                        gamesout.write(
                            instance.value.collected_game.get_repertoire_pgn()
                        )
                        gamesout.write("\n\n")
                        counter.increment_items_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " of repertoires in export format"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_all_repertoires_pgn_no_comments(database, filename, statusbar):
    """Export all repertoires in PGN export format without comments."""
    if filename is None:
        return
    statusbar.status.update()
    statusbar.set_status_text("Started: repertoire PGN format no comments")
    statusbar.status.update_idletasks()
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.REPERTOIRE_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    game = (
                        instance.value.collected_game
                    )  # pycodestyle line too long.
                    if game.is_pgn_valid():
                        gamesout.write(game.get_repertoire_pgn_no_comments())
                        gamesout.write("\n\n")
                        counter.increment_items_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " of repertoires in export format without comments"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_all_repertoires_pgn_import_format(database, filename, statusbar):
    """Export all repertoires in a PGN import format."""
    if filename is None:
        return
    statusbar.status.update()
    statusbar.set_status_text("Started: repertoire PGN import format")
    statusbar.status.update_idletasks()
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.REPERTOIRE_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    if instance.value.collected_game.is_pgn_valid():
                        gamesout.write(
                            get_game_pgn_import_format(
                                instance.value.collected_game
                            )
                        )
                        gamesout.write("\n\n")
                        counter.increment_items_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " of repertoires in import format"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_all_repertoires_text(database, filename, statusbar):
    """Export repertoires in database to text file in internal format."""
    if filename is None:
        return
    statusbar.status.update()
    statusbar.set_status_text("Started: repertoire internal format")
    statusbar.status.update_idletasks()
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.REPERTOIRE_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    gamesout.write(instance.get_srvalue())
                    gamesout.write("\n")
                    counter.increment_items_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " of repertoires in internal format"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_selected_repertoires_pgn(grid, filename):
    """Export selected repertoires in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    if grid.bookmarks:
        statusbar.status.update()
        statusbar.set_status_text("Started: repertoire PGN export format")
        statusbar.status.update_idletasks()
        database = grid.get_data_source().dbhome
        primary = database.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        instance = chessrecord.ChessDBrecordRepertoire()
        instance.set_database(database)
        counter = count_export.create_counter(statusbar)
        database.start_read_only_transaction()
        try:
            counter.items_database = database.count_all_records(
                filespec.REPERTOIRE_FILE_DEF
            )
            counter.items_selected = len(grid.bookmarks)
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for bookmark in sorted(grid.bookmarks):
                    instance.load_record(
                        database.get_primary_record(
                            filespec.REPERTOIRE_FILE_DEF,
                            bookmark[0 if primary else 1],
                        )
                    )
                    collected_game = instance.value.collected_game
                    if collected_game.is_pgn_valid_export_format():
                        gamesout.write(collected_game.get_repertoire_pgn())
                        counter.increment_items_output()
            statusbar.set_status_text(
                "Completed: "
                + counter.completed_report()
                + " to "
                + os.path.basename(filename)
                + " of repertoires in export format"
            )
        finally:
            database.end_read_only_transaction()
        return
    export_all_repertoires_pgn(
        grid.get_data_source().dbhome, filename, statusbar
    )
    return


def export_selected_repertoires_pgn_no_comments(grid, filename):
    """Export selected repertoires in PGN export format without comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    if grid.bookmarks:
        statusbar.status.update()
        statusbar.set_status_text("Started: repertoire PGN format no comments")
        statusbar.status.update_idletasks()
        database = grid.get_data_source().dbhome
        primary = database.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        instance = chessrecord.ChessDBrecordRepertoire()
        instance.set_database(database)
        counter = count_export.create_counter(statusbar)
        database.start_read_only_transaction()
        try:
            counter.items_database = database.count_all_records(
                filespec.REPERTOIRE_FILE_DEF
            )
            counter.items_selected = len(grid.bookmarks)
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for bookmark in sorted(grid.bookmarks):
                    instance.load_record(
                        database.get_primary_record(
                            filespec.REPERTOIRE_FILE_DEF,
                            bookmark[0 if primary else 1],
                        )
                    )
                    collected_game = instance.value.collected_game
                    if collected_game.is_pgn_valid_export_format():
                        gamesout.write(
                            collected_game.get_repertoire_pgn_no_comments()
                        )
                        counter.increment_items_output()
            statusbar.set_status_text(
                "Completed: "
                + counter.completed_report()
                + " to "
                + os.path.basename(filename)
                + " of repertoires in export format without comments"
            )
        finally:
            database.end_read_only_transaction()
        return
    export_all_repertoires_pgn_no_comments(
        grid.get_data_source().dbhome, filename, statusbar
    )
    return


def export_selected_repertoires_pgn_import_format(grid, filename):
    """Export selected repertoires in a PGN import format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    statusbar.set_status_text("Started: repertoire PGN import format")
    statusbar.status.update_idletasks()
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.REPERTOIRE_FILE_DEF
        )
        games = []
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            for bookmark in grid.bookmarks:
                instance.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF,
                        bookmark[0 if primary else 1],
                    )
                )
                if instance.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(
                            instance.value.collected_game
                        )
                    )
        elif grid.partial:
            counter.items_selected = grid.record_count
            cursor = grid.get_cursor()
            try:
                if primary:
                    current_record = cursor.first()
                else:
                    current_record = cursor.nearest(
                        database.encode_record_selector(grid.partial)
                    )
                while current_record:
                    if not primary:
                        if not current_record[0].startswith(grid.partial):
                            break
                    instance.load_record(
                        database.get_primary_record(
                            filespec.REPERTOIRE_FILE_DEF,
                            current_record[0 if primary else 1],
                        )
                    )
                    collected_game = instance.value.collected_game
                    if collected_game.is_pgn_valid_export_format():
                        games.append(
                            get_game_pgn_import_format(collected_game)
                        )
                    current_record = cursor.next()
            finally:
                cursor.close()
        else:
            counter.items_selected = grid.record_count
            cursor = grid.get_cursor()
            try:
                current_record = cursor.first()
                while True:
                    if current_record is None:
                        break
                    instance.load_record(
                        database.get_primary_record(
                            filespec.REPERTOIRE_FILE_DEF,
                            current_record[0 if primary else 1],
                        )
                    )
                    collected_game = instance.value.collected_game
                    if collected_game.is_pgn_valid_export_format():
                        games.append(
                            get_game_pgn_import_format(collected_game)
                        )
                    current_record = cursor.next()
            finally:
                cursor.close()
    finally:
        database.end_read_only_transaction()
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n\n")
            counter.increment_items_output()
    statusbar.set_status_text(
        "Completed: "
        + counter.completed_report()
        + " to "
        + os.path.basename(filename)
        + " of repertoires in import format"
    )
    return


def export_selected_repertoires_text(grid, filename):
    """Export selected repertoires to text file in internal record format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    statusbar.set_status_text("Started: repertoire PGN text format")
    statusbar.status.update_idletasks()
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.REPERTOIRE_FILE_DEF
        )
        games = []
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            for bookmark in grid.bookmarks:
                instance.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF,
                        bookmark[0 if primary else 1],
                    )
                )
                games.append(instance.get_srvalue())
        elif grid.partial:
            counter.items_selected = grid.record_count
            cursor = grid.get_cursor()
            try:
                if primary:
                    current_record = cursor.first()
                else:
                    current_record = cursor.nearest(
                        database.encode_record_selector(grid.partial)
                    )
                while current_record:
                    if not primary:
                        if not current_record[0].startswith(grid.partial):
                            break
                    instance.load_record(
                        database.get_primary_record(
                            filespec.REPERTOIRE_FILE_DEF,
                            current_record[0 if primary else 1],
                        )
                    )
                    games.append(instance.get_srvalue())
                    current_record = cursor.next()
            finally:
                cursor.close()
        else:
            counter.items_selected = grid.record_count
            cursor = grid.get_cursor()
            try:
                current_record = cursor.first()
                while True:
                    if current_record is None:
                        break
                    instance.load_record(
                        database.get_primary_record(
                            filespec.REPERTOIRE_FILE_DEF,
                            current_record[0 if primary else 1],
                        )
                    )
                    games.append(instance.get_srvalue())
                    current_record = cursor.next()
            finally:
                cursor.close()
    finally:
        database.end_read_only_transaction()
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n")
            counter.increment_items_output()
    statusbar.set_status_text(
        "Completed: "
        + counter.completed_report()
        + " to "
        + os.path.basename(filename)
        + " of repertoires in internal format"
    )
    return


def export_single_repertoire_pgn(collected_game, filename):
    """Export repertoire in import format PGN to *.pgn file.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(collected_game.get_repertoire_pgn())


def export_single_repertoire_pgn_no_comments(collected_game, filename):
    """Export repertoire in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(collected_game.get_repertoire_pgn_no_comments())
