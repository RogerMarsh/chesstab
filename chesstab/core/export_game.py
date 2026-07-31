# export_game.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess game exporters.

THe exporters do not, yet, resort to temporary files for sorting so
the size of an output is limited by memory.

A box with 8Gb memory will likely cope with sorting 50 million games
for output, and possibly up to 100 million games depending on how much
memory other processes need.
"""

import ast
import os
from operator import methodcaller
import io

from solentware_base.core.wherevalues import ValuesClause

from pgn_read.core.parser import PGN

from . import chessrecord, filespec, lexer, pgnify, cqlpgnify, count_export
from .export_pgn_import_format import export_pgn_import_format
from ..basecore.selectionds import SelectionDS

# PGN specification states ascii but these export functions used the
# default encoding before introduction of _ENCODING attribute.
# PGN files were read as "iso-8859-1" encoding when _ENCODING attribute
# was introduced.
# _ENCODING = "ascii"
# _ENCODING = "iso-8859-1"
_ENCODING = "utf-8"

# A convenient way of testing the path through code for the three cases
# defined by _MEMORY_SORT_LIMIT is set it to a low value, such as 1.
# Games with moves like Qa7c5 are not output for low values: these are
# the games which have to be reparsed to generate Qa7c5 from the Qa7-c5
# stored on the database record.
# This occurs for the databases tried: one set each for games in
# twic1372g.zip and twic1397g.zip with about 10,000 and 5,000 games
# respectively.  In both sets these games are not output for
# _MEMORY_SORT_LIMIT <= 17 but are for _MEMORY_SORT_LIMIT >= 18.
# The previous game is repeated.
# The behaviour is seen with file IO and bytes IO.
# The Qa7c5-like games are output for _MEMORY_SORT_LIMIT = 10 if
# _BYTESIO_FACTOR is set to 300000 so it seems the product matters.
# _MEMORY_SORT_LIMIT * _BYTESIO_FACTOR > 173 seems to be the codition
# for including games with moves like Qa7c5 in the output.

# This value avoids swapping on 8Gb memory test box with TWIC 1-1500.
# Values more than double this hit problems with games sorted by result
# with the menu 'Select | Index | Result' option.
_MEMORY_SORT_LIMIT = 300000

# When more than _MEMORY_SORT_LIMIT games need processing the sorted
# game keys are output to a BytesIO object which is allowed to hold up to
# _MEMORY_SORT_LIMIT * _BYTESIO_FACTOR keys.
# A list of these BytesIO objects increases the number of game keys
# supported, limited by available memory.
_BYTESIO_FACTOR = 10

# Encoding the integer keys in 4 bytes allows, at present, for a database
# containing about four years of monthly game files from LiChess.
# If there is room for a larger database change _KEY_SIZE_BYTES to 5,
# which is enough for 1000 years of games at current rate of play.
_KEY_SIZE_BYTES = 4

# Name of directory, relative to database directory, for temporary files
# when sorting large numbers of records in PGN collation order.
_EXPORT_SORT_DIRECTORY = "_export_sort_directory"


def export_all_games_text(database, filename, statusbar):
    """Export games in database to text file in internal record format."""
    if filename is None:
        return
    statusbar.status.update()
    statusbar.set_status_text("Started: internal format")
    statusbar.status.update_idletasks()
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    gamesout.write(literal_eval(instance.get_srvalue()[0]))
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
                + " in internal format"
            )
    finally:
        database.end_read_only_transaction()
    return


def export_all_games_pgn(database, filename, statusbar):
    """Export all database games in PGN export format."""
    _export_all_games(
        database, filename, statusbar, "export format", _export_pgn_elements
    )


def export_all_games_pgn_import_format(database, filename, statusbar):
    """Export all database games in a PGN inport format."""
    _export_all_games(
        database,
        filename,
        statusbar,
        "import format",
        _export_pgn_import_format,
    )


def export_all_games_pgn_no_comments(database, filename, statusbar):
    """Export all database games in PGN export format excluding comments."""
    _export_all_games(
        database,
        filename,
        statusbar,
        "export format no comments",
        _export_pgn_rav_elements,
    )


def export_all_games_pgn_no_structured_comments(database, filename, statusbar):
    """Export database games in PGN export format without {[%]} comments."""
    _export_all_games(
        database,
        filename,
        statusbar,
        "export format without '[%]' in comments",
        _export_pgn_rav_no_structured_comments,
    )


def export_all_games_pgn_no_comments_no_ravs(database, filename, statusbar):
    """Export all database games, tags and moves only, in PGN export format.

    Comments and RAVs are excluded from the export.

    """
    _export_all_games(
        database,
        filename,
        statusbar,
        "export format tags and moves played",
        _export_pgn_no_comments_no_ravs,
    )


def export_all_games_pgn_reduced_export_format(database, filename, statusbar):
    """Export all database games in PGN reduced export format."""
    _export_all_games(
        database,
        filename,
        statusbar,
        "reduced export format",
        _export_pgn_reduced_export_format,
    )


def export_selected_games_pgn_import_format(grid, filename):
    """Export selected records in a PGN import format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    data_source = grid.get_data_source()
    if isinstance(data_source, SelectionDS):
        export_games_pgn_import_format(grid, filename)
        return
    (
        _export_selected_games
        if data_source.dbhome.is_primary(data_source.dbset, data_source.dbname)
        else _export_selected_games_index_order
    )(grid, filename, "import format", _export_pgn_import_format)


def export_selected_games_pgn(grid, filename):
    """Export selected records in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    data_source = grid.get_data_source()
    if isinstance(data_source, SelectionDS):
        export_games_pgn(grid, filename)
        return
    (
        _export_selected_games
        if data_source.dbhome.is_primary(data_source.dbset, data_source.dbname)
        else _export_selected_games_index_order
    )(grid, filename, "export format", _export_pgn_elements)


def export_selected_games_pgn_no_comments(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    data_source = grid.get_data_source()
    if isinstance(data_source, SelectionDS):
        export_games_pgn_no_comments(grid, filename)
        return
    (
        _export_selected_games
        if data_source.dbhome.is_primary(data_source.dbset, data_source.dbname)
        else _export_selected_games_index_order
    )(
        grid,
        filename,
        "export format without comments",
        _export_pgn_rav_elements,
    )


def export_selected_games_pgn_no_structured_comments(grid, filename):
    """Export selected records in export format excluding {[%]} comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    data_source = grid.get_data_source()
    if isinstance(data_source, SelectionDS):
        export_games_pgn_no_structured_comments(grid, filename)
        return
    (
        _export_selected_games
        if data_source.dbhome.is_primary(data_source.dbset, data_source.dbname)
        else _export_selected_games_index_order
    )(
        grid,
        filename,
        "export format without '[%]' in comments",
        _export_pgn_rav_no_structured_comments,
    )


def export_selected_games_pgn_no_comments_no_ravs(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    data_source = grid.get_data_source()
    if isinstance(data_source, SelectionDS):
        export_games_pgn_no_comments_no_ravs(grid, filename)
        return
    (
        _export_selected_games
        if data_source.dbhome.is_primary(data_source.dbset, data_source.dbname)
        else _export_selected_games_index_order
    )(
        grid,
        filename,
        "export format tags and moves played",
        _export_pgn_no_comments_no_ravs,
    )


def export_selected_games_pgn_reduced_export_format(grid, filename):
    """Export selected records in grid to PGN file in reduced export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    data_source = grid.get_data_source()
    if isinstance(data_source, SelectionDS):
        export_games_pgn_reduced_export_format(grid, filename)
        return
    (
        _export_selected_games
        if data_source.dbhome.is_primary(data_source.dbset, data_source.dbname)
        else _export_selected_games_index_order
    )(
        grid,
        filename,
        "reduced export format",
        _export_pgn_reduced_export_format,
    )


def export_selected_games_text(grid, filename):
    """Export selected records in grid to text file in internal record format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    literal_eval = ast.literal_eval
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    data_source = grid.get_data_source()
    database = data_source.dbhome
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        primary = database.is_primary(data_source.dbset, data_source.dbname)
        instance = chessrecord.ChessDBrecordGame()
        instance.set_database(database)
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            statusbar.set_status_text("Started (bookmark): internal format")
            statusbar.status.update_idletasks()
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for bookmark in grid.bookmarks:
                    instance.load_record(
                        database.get_primary_record(
                            filespec.GAMES_FILE_DEF,
                            bookmark[0 if primary else 1],
                        )
                    )
                    gamesout.write(literal_eval(instance.get_srvalue()[0]))
                    gamesout.write("\n")
                    counter.increment_items_output()
        elif grid.partial:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (key): internal format")
            statusbar.status.update_idletasks()
            cursor = grid.get_cursor()
            try:
                if primary:
                    current_record = cursor.first()
                    if current_record is None:
                        return
                else:
                    current_record = cursor.nearest(
                        database.encode_record_selector(grid.partial)
                    )
                    if not current_record[0].startswith(grid.partial):
                        return
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    while current_record:
                        if not primary:
                            if not current_record[0].startswith(grid.partial):
                                break
                        instance.load_record(
                            database.get_primary_record(
                                filespec.GAMES_FILE_DEF,
                                current_record[0 if primary else 1],
                            )
                        )
                        gamesout.write(literal_eval(instance.get_srvalue()[0]))
                        gamesout.write("\n")
                        counter.increment_items_output()
                        current_record = cursor.next()
            finally:
                cursor.close()
        else:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (all): internal format")
            statusbar.status.update_idletasks()
            cursor = grid.get_cursor()
            try:
                current_record = cursor.first()
                if current_record is None:
                    return
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    while True:
                        instance.load_record(
                            database.get_primary_record(
                                filespec.GAMES_FILE_DEF,
                                current_record[0 if primary else 1],
                            )
                        )
                        gamesout.write(literal_eval(instance.get_srvalue()[0]))
                        gamesout.write("\n")
                        counter.increment_items_output()
                        current_record = cursor.next()
                        if current_record is None:
                            break
            finally:
                cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " in internal format"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_games_pgn_import_format(grid, filename):
    """Export records in a PGN import format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    _export_games(grid, filename, "import format", _export_pgn_import_format)


def export_games_pgn(grid, filename):
    """Export records in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    _export_games(grid, filename, "export format", _export_pgn_elements)


def export_games_pgn_no_comments(grid, filename):
    """Export records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    _export_games(
        grid,
        filename,
        "export format without comments",
        _export_pgn_rav_elements,
    )


def export_games_pgn_no_structured_comments(grid, filename):
    """Export records in export format excluding {[%]} comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    _export_games(
        grid,
        filename,
        "export format without '[%]' in comments",
        _export_pgn_rav_no_structured_comments,
    )


def export_games_pgn_no_comments_no_ravs(grid, filename):
    """Export records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    _export_games(
        grid,
        filename,
        "export format tags and moves played",
        _export_pgn_no_comments_no_ravs,
    )


def export_games_pgn_reduced_export_format(grid, filename):
    """Export records in grid to PGN file in reduced export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    _export_games(
        grid,
        filename,
        "reduced export format",
        _export_pgn_reduced_export_format,
    )


def export_games_text(grid, filename):
    """Export records in grid to text file in internal record format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    literal_eval = ast.literal_eval
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    counter = count_export.create_counter(statusbar)
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        primary = database.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        instance = chessrecord.ChessDBrecordGame()
        instance.set_database(database)
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            statusbar.set_status_text("Started (bookmark): internal format")
            statusbar.status.update_idletasks()
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for bookmark in grid.bookmarks:
                    instance.load_record(
                        database.get_primary_record(
                            filespec.GAMES_FILE_DEF,
                            bookmark[0 if primary else 1],
                        )
                    )
                    gamesout.write(literal_eval(instance.get_srvalue()[0]))
                    gamesout.write("\n")
                    counter.increment_items_output()
        elif grid.partial:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (key): internal format")
            statusbar.status.update_idletasks()
            cursor = grid.get_cursor()
            try:
                if primary:
                    current_record = cursor.first()
                    if current_record is None:
                        return
                else:
                    current_record = cursor.nearest(
                        database.encode_record_selector(grid.partial)
                    )
                    if not current_record[0].startswith(grid.partial):
                        return
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    while current_record:
                        if not primary:
                            if not current_record[0].startswith(grid.partial):
                                break
                        instance.load_record(
                            database.get_primary_record(
                                filespec.GAMES_FILE_DEF,
                                current_record[0 if primary else 1],
                            )
                        )
                        gamesout.write(literal_eval(instance.get_srvalue()[0]))
                        gamesout.write("\n")
                        counter.increment_items_output()
                        current_record = cursor.next()
            finally:
                cursor.close()
        else:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (all): internal format")
            statusbar.status.update_idletasks()
            cursor = grid.get_cursor()
            try:
                current_record = cursor.first()
                if current_record is None:
                    return
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    while True:
                        instance.load_record(
                            database.get_primary_record(
                                filespec.GAMES_FILE_DEF,
                                current_record[0 if primary else 1],
                            )
                        )
                        gamesout.write(literal_eval(instance.get_srvalue()[0]))
                        gamesout.write("\n")
                        counter.increment_items_output()
                        current_record = cursor.next()
                        if current_record is None:
                            break
            finally:
                cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " in internal format"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_single_game_pgn_reduced_export_format(collected_game, filename):
    """Export collected_game to PGN file in reduced export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_reduced_export_format(gamesout, collected_game)


def export_single_game_pgn(collected_game, filename):
    """Export collected_game to filename in PGN export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_elements(gamesout, collected_game)


def export_single_game_pgn_no_comments_no_ravs(collected_game, filename):
    """Export collected_game tags and moves to filename in PGN export format.

    No comments or RAVs are included in the export (PGN Tags and moves
    played only).

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_no_comments_no_ravs(gamesout, collected_game)
    return


def export_single_game_pgn_no_comments(collected_game, filename):
    """Export collected_game to filename in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_rav_elements(gamesout, collected_game)
    return


def export_single_game_pgn_no_structured_comments(collected_game, filename):
    """Export collected_game to filename without {[%]} comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_rav_no_structured_comments(gamesout, collected_game)
    return


def export_single_game_pgn_import_format(collected_game, filename):
    """Export collected_game to pgn file in a PGN import format."""
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(
            export_pgn_import_format(collected_game, tag_separator="\n")
        )


def export_single_game_text(collected_game, filename):
    """Export collected_game to text file in internal format."""
    if filename is None:
        return
    internal_format = next(PGN().read_games(collected_game.get_text_of_game()))
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(internal_format.get_text_of_game())
        gamesout.write("\n")


def export_all_games_import_format_database_order(
    database, filename, statusbar
):
    """Export all games in database order in a PGN inport format."""
    if filename is None:
        return
    statusbar.set_status_text("Started: import format in database order")
    statusbar.status.update()
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                pgnifier = pgnify.PGNify(gamesout)
                tokenizer = lexer.Lexer(pgnifier)
                pgnifier.set_lexer(tokenizer)
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    tokenizer.generate_tokens(
                        literal_eval(instance.get_srvalue()[0])
                    )
                    counter.increment_items_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
            statusbar.set_status_text(
                "Completed: "
                + counter.completed_report()
                + " to "
                + os.path.basename(filename)
                + " in import format in database order"
            )
    finally:
        database.end_read_only_transaction()
    return


def export_games_for_cql_scan(
    database, recordset, filename, limit=100000, commit=True
):
    """Export up to limit recordset games in recordmap in PGN format.

    A PGN import format accepted by CQL program is used.  The game numbers
    in the PGN file are mapped to the source record number and the map is
    placed in recordmap.

    """
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    record_map = {}
    if commit:
        database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF,
            filespec.GAMES_FILE_DEF,
            recordset=recordset,
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                pgnifier = cqlpgnify.CQLPGNify(gamesout)
                tokenizer = lexer.Lexer(pgnifier)
                pgnifier.set_lexer(tokenizer)
                current_record = cursor.first()
                while current_record:
                    record_number = current_record[0]
                    record_map[len(record_map) + 1] = record_number
                    instance.load_record(current_record)
                    tokenizer.generate_tokens(
                        literal_eval(instance.get_srvalue()[0])
                    )
                    if len(record_map) > limit:
                        break
                    current_record = cursor.next()
        finally:
            cursor.close()
    finally:
        if commit:
            database.end_read_only_transaction()
    return record_map


def _export_all_games(database, filename, statusbar, report_text, exporter):
    """Export all database games in PGN export format."""
    if filename is None:
        return
    record_limit_exceeded = False
    statusbar.set_status_text("Started: " + report_text)
    statusbar.status.update()
    instance = chessrecord.ChessDBrecordGameExport()
    instance.set_database(database)
    dbset = filespec.GAMES_FILE_DEF
    valuespec = ValuesClause()
    valuespec.field = filespec.PGN_DATE_FIELD_DEF
    selector = database.encode_record_selector
    games_for_date = []
    prev_date = None
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(dbset)
        counter.items_selected = counter.items_database
        if counter.items_database > _MEMORY_SORT_LIMIT:
            for key in database.find_values_ascending(valuespec, dbset):
                selected = database.recordlist_key(
                    dbset, valuespec.field, key=selector(key)
                )
                try:
                    selected_count = selected.count_records()
                    if selected_count > _MEMORY_SORT_LIMIT:
                        record_limit_exceeded = True
                        break
                finally:
                    selected.close()
        if not record_limit_exceeded:
            cursor = database.database_cursor(
                dbset, filespec.PGN_DATE_FIELD_DEF
            )
            try:
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    current_record = cursor.first()
                    while current_record:
                        if current_record[0] != prev_date:
                            games_for_date.sort(
                                key=methodcaller("get_collation")
                            )
                            for gfd in games_for_date:
                                exporter(gamesout, gfd)
                                counter.increment_items_output()
                            prev_date = current_record[0]
                            games_for_date = []
                        counter.increment_items_read()
                        game = database.get_primary_record(
                            dbset, current_record[1]
                        )
                        instance.load_record(game)
                        # Fix pycodestyle E501 (83 > 79 characters).
                        # black formatting applied with line-length = 79.
                        ivcg = instance.value.collected_game
                        if ivcg.is_pgn_valid_export_format():
                            games_for_date.append(ivcg)
                        else:
                            ivcg = _full_parse(instance)
                            if ivcg.is_pgn_valid_export_format():
                                games_for_date.append(ivcg)
                        current_record = cursor.next()
                    games_for_date.sort(key=methodcaller("get_collation"))
                    for gfd in games_for_date:
                        exporter(gamesout, gfd)
                        counter.increment_items_output()
            finally:
                cursor.close()
        else:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for key in database.find_values_ascending(valuespec, dbset):
                    selected = database.recordlist_key(
                        dbset, valuespec.field, key=selector(key)
                    )
                    try:
                        _export_all_games_tag_order(
                            selected,
                            gamesout,
                            instance,
                            exporter,
                            counter,
                            None,
                        )
                    finally:
                        selected.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " in "
            + report_text
        )
    finally:
        database.end_read_only_transaction()
    return


def _export_selected_games(grid, filename, report_text, exporter):
    """Export selected games in PGN format.

    Partial key is not supported for the arbitrary record number key.

    """
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    counter = count_export.create_counter(statusbar)
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        instance = chessrecord.ChessDBrecordGameExport()
        instance.set_database(database)
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            statusbar.set_status_text("Started (bookmark): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            selected = database.recordlist_nil(dbset)
            try:
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    for bookmark in grid.bookmarks:
                        selected.place_record_number(bookmark[0])
                    _export_all_games_tag_order(
                        selected,
                        gamesout,
                        instance,
                        exporter,
                        counter,
                        None,
                    )
            finally:
                selected.close()
        else:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (all grid): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                selected = database.recordlist_ebm(dbset)
                try:
                    _export_all_games_tag_order(
                        selected,
                        gamesout,
                        instance,
                        exporter,
                        counter,
                        None,
                    )
                finally:
                    selected.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " in "
            + report_text
        )
    finally:
        database.end_read_only_transaction()
    return


def _export_games(grid, filename, report_text, exporter):
    """Export games in PGN format.

    Partial key is not supported for the arbitrary record number key.

    """
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    counter = count_export.create_counter(statusbar)
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        instance = chessrecord.ChessDBrecordGameExport()
        instance.set_database(database)
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            statusbar.set_status_text("Started (bookmark): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                selected = database.recordlist_nil(dbset)
                try:
                    for bookmark in grid.bookmarks:
                        selected.place_record_number(bookmark[0])
                    _export_all_games_tag_order(
                        selected,
                        gamesout,
                        instance,
                        exporter,
                        counter,
                        None,
                    )
                finally:
                    selected.close()
        else:
            selected = grid.get_data_source().recordset
            selected_count = selected.count_records()
            counter.items_selected = selected_count
            statusbar.set_status_text("Started (all grid): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                _export_all_games_tag_order(
                    selected,
                    gamesout,
                    instance,
                    exporter,
                    counter,
                    None,
                )
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " in "
            + report_text
        )
    finally:
        database.end_read_only_transaction()
    return


def _export_selected_games_database_order(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in database order."""
    cursor = selected.create_recordsetbase_cursor()
    try:
        current_record = cursor.first()
        while current_record:
            counter.increment_items_read()
            instance.load_record(current_record)
            ivcg = instance.value.collected_game
            if ivcg.is_pgn_valid_export_format():
                exporter(gamesout, ivcg)
                counter.increment_items_output()
            else:
                ivcg = _full_parse(instance)
                if ivcg.is_pgn_valid_export_format():
                    exporter(gamesout, ivcg)
                    counter.increment_items_output()
            current_record = cursor.next()
    finally:
        cursor.close()


def _export_selected_games_index_order(grid, filename, report_text, exporter):
    """Export selected games in PGN format in index order."""
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    counter = count_export.create_counter(statusbar)
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.GAMES_FILE_DEF
        )
        instance = chessrecord.ChessDBrecordGameExport()
        instance.set_database(database)
        if grid.bookmarks:
            counter.items_selected = len(grid.bookmarks)
            statusbar.set_status_text("Started (bookmark): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                selected = database.recordlist_nil(dbset)
                try:
                    for bookmark in grid.bookmarks:
                        selected.place_record_number(bookmark[1])
                    _export_all_games_tag_order(
                        selected,
                        gamesout,
                        instance,
                        exporter,
                        counter,
                        grid.get_data_source().dbname,
                    )
                finally:
                    selected.close()
        elif grid.partial:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (key): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                selected = database.recordlist_key_startswith(
                    dbset,
                    grid.get_data_source().dbname,
                    keystart=database.encode_record_selector(grid.partial),
                )
                try:
                    _export_all_games_tag_order(
                        selected,
                        gamesout,
                        instance,
                        exporter,
                        counter,
                        grid.get_data_source().dbname,
                    )
                finally:
                    selected.close()
        else:
            counter.items_selected = grid.record_count
            statusbar.set_status_text("Started (all grid): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                selected = database.recordlist_ebm(dbset)
                try:
                    _export_all_games_tag_order(
                        selected,
                        gamesout,
                        instance,
                        exporter,
                        counter,
                        grid.get_data_source().dbname,
                    )
                finally:
                    selected.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.completed_report()
            + " to "
            + os.path.basename(filename)
            + " in "
            + report_text
        )
    finally:
        database.end_read_only_transaction()
    return


def _export_selected_games_movetext_order(
    selected, gamesout, instance, exporter, counter, tag
):
    """Export selected games in PGN format in database order.

    The PGN specification requires a movetext order sort but this is
    not implemented.

    """
    del tag
    _export_selected_games_database_order(
        selected, gamesout, instance, exporter, counter
    )


def _export_all_games_tag_order(
    selected, gamesout, instance, exporter, counter, tag
):
    """Export selected games in PGN format in PGN collation order.

    Game references are put in a list and sorted for output order.  When
    the list is too large the keys are written to a BytesIO stream and
    the list is discarded.  The next level, writing the io streams to
    files and discarding the io streams, is not implemented (yet).

    """
    large_sort_limit = _MEMORY_SORT_LIMIT * _BYTESIO_FACTOR
    if counter.items_selected > large_sort_limit * _BYTESIO_FACTOR:
        streamer = _fileio_stream_of_game_keys
        sort_directory = os.path.join(
            selected.recordset.dbhome.home_directory, _EXPORT_SORT_DIRECTORY
        )
        os.mkdir(sort_directory)
    else:
        streamer = _bytesio_stream_of_game_keys
        sort_directory = None
    sorted_references = []
    references = []
    cursor = selected.create_recordsetbase_cursor()
    try:
        current_record = cursor.first()
        while current_record:
            counter.increment_items_read()
            instance.load_record(current_record)
            ivcg = instance.value.collected_game
            if ivcg.is_pgn_valid_export_format():
                references.append(
                    (
                        ivcg.pgn_tags.get(tag),
                        ivcg.get_collation()[:-2],
                        instance.key.recno,
                    )
                )
            else:
                ivcg = _full_parse(instance)
                if ivcg.is_pgn_valid_export_format():
                    references.append(
                        (
                            ivcg.pgn_tags.get(tag),
                            ivcg.get_collation()[:-2],
                            instance.key.recno,
                        )
                    )
            if len(references) > large_sort_limit:
                sorted_references.append(
                    streamer(
                        references,
                        _temporary_file_name(sort_directory),
                    )
                )
                references.clear()
            current_record = cursor.next()
    finally:
        cursor.close()
    if sorted_references:
        sorted_references.append(
            streamer(
                references,
                _temporary_file_name(sort_directory),
            )
        )
        references.clear()
        _export_all_games_sorted_references_order(
            selected,
            sorted_references,
            gamesout,
            instance,
            exporter,
            counter,
            tag,
        )
    else:
        references.sort()
        database = selected.recordset.dbhome
        dbset = selected.recordset.dbset
        for reference in references:
            current_record = database.get_primary_record(dbset, reference[-1])
            instance.load_record(current_record)
            ivcg = instance.value.collected_game
            if ivcg.is_pgn_valid_export_format():
                exporter(gamesout, ivcg)
                counter.increment_items_output()
            else:
                ivcg = _full_parse(instance)
                if ivcg.is_pgn_valid_export_format():
                    exporter(gamesout, ivcg)
                    counter.increment_items_output()


def _temporary_file_name(directory):
    """Return new file name in directory or None if directory is None."""
    if directory is None:
        return None
    return os.path.join(directory, str(len(os.listdir(directory))))


def _bytesio_stream_of_game_keys(references, filename):
    """Write encoded sorted game keys to BytesIO stream and return stream."""
    del filename
    references.sort()
    byteio = io.BytesIO()
    for item in references:
        byteio.write(item[-1].to_bytes(_KEY_SIZE_BYTES, byteorder="big"))
    return byteio


def _fileio_stream_of_game_keys(references, filename):
    """Write encoded sorted game keys to file and return filename."""
    references.sort()
    fileio = open(filename, "xb")
    for item in references:
        fileio.write(item[-1].to_bytes(_KEY_SIZE_BYTES, byteorder="big"))
    fileio.close()
    return fileio.name


def _export_all_games_sorted_references_order(
    selected, sorted_references, gamesout, instance, exporter, counter, tag
):
    """Export selected games in PGN format in PGN collation order.

    Items in sorted_references are deleted when all keys in the item have
    been processed.  If item is a file name it is deleted, and when the
    last file is deleted the directory is deleted too.

    """
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    items = []
    for stream in sorted_references:
        if isinstance(stream, str):
            stream = open(stream, "rb")
        stream.seek(0, os.SEEK_SET)
        current_record = database.get_primary_record(
            dbset,
            int.from_bytes(stream.read(_KEY_SIZE_BYTES), byteorder="big"),
        )
        instance.load_record(current_record)
        ivcg = instance.value.collected_game
        items.append(
            (
                ivcg.pgn_tags.get(tag),
                ivcg.get_collation(),
                ivcg,
                stream,
            )
        )
    items.sort()
    while True:
        try:
            ivcg, stream = items.pop(0)[-2:]
        except IndexError:
            break
        if ivcg.is_pgn_valid_export_format():
            exporter(gamesout, ivcg)
            counter.increment_items_output()
        else:
            ivcg = _full_parse(instance)
            if ivcg.is_pgn_valid_export_format():
                exporter(gamesout, ivcg)
                counter.increment_items_output()
        key_bytes = stream.read(_KEY_SIZE_BYTES)
        if not key_bytes:
            stream.close()
            if isinstance(stream, io.BufferedReader):
                os.remove(stream.name)
                sorted_references.remove(stream.name)
                if not sorted_references:
                    os.rmdir(os.path.dirname(stream.name))
            else:
                sorted_references.remove(stream)
            continue
        current_record = database.get_primary_record(
            dbset, int.from_bytes(key_bytes, byteorder="big")
        )
        instance.load_record(current_record)
        ivcg = instance.value.collected_game
        items.insert(
            0,
            (ivcg.pgn_tags.get(tag), ivcg.get_collation(), ivcg, stream),
        )
        items.sort()


def _export_pgn_elements(gamesout, collected_game):
    """Write game to file in PGN export format."""
    gamesout.write(collected_game.get_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_non_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_all_movetext_in_pgn_export_format())
    gamesout.write("\n\n")


def _export_pgn_rav_elements(gamesout, collected_game):
    """Write game to file in export format without comments."""
    gamesout.write(collected_game.get_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_non_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(
        collected_game.get_movetext_without_comments_in_pgn_export_format()
    )
    gamesout.write("\n\n")


def _export_pgn_rav_no_structured_comments(gamesout, collected_game):
    """Write game to file in export format without [%] comments."""
    gamesout.write(collected_game.get_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_non_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(
        collected_game.get_export_movetext_without_structured_comments()
    )
    gamesout.write("\n\n")


def _export_pgn_no_comments_no_ravs(gamesout, collected_game):
    """Write game to file in export format without comments or RAVs."""
    gamesout.write(collected_game.get_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_non_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_archive_movetext())
    gamesout.write("\n\n")


def _export_pgn_reduced_export_format(gamesout, collected_game):
    """Write game to file in reduced export format."""
    gamesout.write(collected_game.get_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_archive_movetext())
    gamesout.write("\n\n")


def _export_pgn_import_format(gamesout, collected_game):
    """Write game to file in a PGN import format.

    The PGN tag and movetext blocks are separated by a blank line.

    The Seven Tag Roster is output in the specified order: Event, Site,
    Date, Round, White, Black, Result.

    The remaing tags follow in alphabetical order.

    Movetext folloews without move number indicators or line breaks.

    """
    gamesout.write(collected_game.get_seven_tag_roster_tags())
    gamesout.write("\n")
    gamesout.write(collected_game.get_non_seven_tag_roster_tags())
    gamesout.write("\n\n")
    gamesout.write(" ".join(collected_game.get_movetext()))
    gamesout.write("\n\n")


def _full_parse(instance):
    """Return game extracted from instance by full parse.

    This function is used to resolve cases where the default parse of
    instance gave an error due to the presence of movetext like 'Qa7-c5'
    in the database record.  Such movetext is present only where more
    than two pieces of the same kind can legally move to a square.

    Movetext like 'Qa7-c5' is changed to 'Qa7c5' which is acceptable
    in export format PGN.

    """
    strio = io.StringIO()
    try:
        pgnifier = pgnify.PGNify(strio)
        tokenizer = lexer.Lexer(pgnifier)
        pgnifier.set_lexer(tokenizer)
        tokenizer.generate_tokens(ast.literal_eval(instance.get_srvalue()[0]))
        return next(
            chessrecord.ChessDBvalueGame().read_games(strio.getvalue())
        )
    finally:
        strio.close()
