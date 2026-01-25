# export_game.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess game exporters."""

import ast
import os
from operator import methodcaller

from solentware_base.core.wherevalues import ValuesClause

from pgn_read.core.parser import PGN

from . import chessrecord, filespec, lexer, pgnify, cqlpgnify
from .export_pgn_import_format import export_pgn_import_format

# PGN specification states ascii but these export functions used the
# default encoding before introduction of _ENCODING attribute.
# PGN files were read as "iso-8859-1" encoding when _ENCODING attribute
# was introduced.
# _ENCODING = "ascii"
# _ENCODING = "iso-8859-1"
_ENCODING = "utf-8"

_UPDATE_FREQUENCY = 1000

# This value avoids swapping on 8Gb memory test box with TWIC 1-1500.
# Values more than double this hit problems with games sorted by result
# with the menu 'Select | Inndex | Result' option.
_MEMORY_SORT_LIMIT = 300000


class _Counter:
    """Count and report records read, sorted, and output."""

    def __init__(self, total, reportbar):
        """Initialize counts and report strings."""
        formatter = str(len(str(total))).join(("{: ", "}"))
        self._reportbar = reportbar
        self.games_read = 0
        self.games_output = 0
        self._read_report = "".join(
            (formatter, " read for sort of ", str(total))
        )
        self._output_report = "".join(
            (formatter, " output sorted of ", str(total))
        )

    @property
    def read_report(self):
        """Get report count of records read for sorting."""
        return self._read_report.format(self.games_read)

    @property
    def output_report(self):
        """Get report count of sorted records output."""
        return self._output_report.format(self.games_output)

    def increment_games_output(self):
        """Incremant output count of sorted games and show in reportbar."""
        self.games_output += 1
        if not self.games_output % _UPDATE_FREQUENCY:
            self._reportbar.set_status_text(self.output_report)
            self._reportbar.status.update_idletasks()

    def increment_games_read(self):
        """Incremant read count of games to sort and show in reportbar."""
        self.games_read += 1
        if not self.games_read % _UPDATE_FREQUENCY:
            self._reportbar.set_status_text(self.read_report)
            self._reportbar.status.update_idletasks()


def export_all_games_text(database, filename, statusbar):
    """Export games in database to text file in internal record format."""
    if filename is None:
        return True
    statusbar.status.update()
    statusbar.set_status_text("Started: internal format")
    statusbar.status.update_idletasks()
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    database.start_read_only_transaction()
    try:
        counter = _Counter(_all_records_count(database), statusbar)
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
                    counter.increment_games_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
            statusbar.set_status_text(
                "Completed: "
                + counter.output_report
                + " to "
                + os.path.basename(filename)
                + " in internal format"
            )
    finally:
        database.end_read_only_transaction()
    return True


def export_all_games_pgn(database, filename, statusbar):
    """Export all database games in PGN export format."""
    return _export_all_games(
        database, filename, statusbar, "export format", _export_pgn_elements
    )


def export_all_games_pgn_import_format(database, filename, statusbar):
    """Export all database games in a PGN inport format."""
    return _export_all_games(
        database,
        filename,
        statusbar,
        "import format",
        _export_pgn_import_format,
    )


def export_all_games_pgn_no_comments(database, filename, statusbar):
    """Export all database games in PGN export format excluding comments."""
    return _export_all_games(
        database,
        filename,
        statusbar,
        "export format no comments",
        _export_pgn_rav_elements,
    )


def export_all_games_pgn_no_structured_comments(database, filename, statusbar):
    """Export database games in PGN export format without {[%]} comments."""
    return _export_all_games(
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
    return _export_all_games(
        database,
        filename,
        statusbar,
        "export format no comments or variations",
        _export_pgn_no_comments_no_ravs,
    )


def export_all_games_pgn_reduced_export_format(database, filename, statusbar):
    """Export all database games in PGN reduced export format."""
    return _export_all_games(
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
    return (
        _export_selected_games
        if grid.get_data_source().dbhome.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        else _export_selected_games_index_order
    )(grid, filename, "import format", _export_pgn_import_format)


def export_selected_games_pgn(grid, filename):
    """Export selected records in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    return (
        _export_selected_games
        if grid.get_data_source().dbhome.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        else _export_selected_games_index_order
    )(grid, filename, "export format", _export_pgn_elements)


def export_selected_games_pgn_no_comments(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    return (
        _export_selected_games
        if grid.get_data_source().dbhome.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
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
    return (
        _export_selected_games
        if grid.get_data_source().dbhome.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
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
    return (
        _export_selected_games
        if grid.get_data_source().dbhome.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        else _export_selected_games_index_order
    )(
        grid,
        filename,
        "export format no comments or variations",
        _export_pgn_no_comments_no_ravs,
    )


def export_selected_games_pgn_reduced_export_format(grid, filename):
    """Export selected records in grid to PGN file in reduced export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    return (
        _export_selected_games
        if grid.get_data_source().dbhome.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
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
        return True
    literal_eval = ast.literal_eval
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        primary = database.is_primary(
            grid.get_data_source().dbset, grid.get_data_source().dbname
        )
        instance = chessrecord.ChessDBrecordGame()
        instance.set_database(database)
        if grid.bookmarks:
            counter = _Counter(_bookmarked_records_count(grid), statusbar)
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
                    counter.increment_games_output()
        elif grid.partial:
            counter = _Counter(_selected_records_count(grid), statusbar)
            statusbar.set_status_text("Started (key): internal format")
            statusbar.status.update_idletasks()
            cursor = grid.get_cursor()
            try:
                if primary:
                    current_record = cursor.first()
                    if current_record is None:
                        return None
                else:
                    current_record = cursor.nearest(
                        database.encode_record_selector(grid.partial)
                    )
                    if not current_record[0].startswith(grid.partial):
                        return None
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
                        counter.increment_games_output()
                        current_record = cursor.next()
            finally:
                cursor.close()
        else:
            counter = _Counter(_all_records_count(database), statusbar)
            statusbar.set_status_text("Started (all): internal format")
            statusbar.status.update_idletasks()
            cursor = grid.get_cursor()
            try:
                current_record = cursor.first()
                if current_record is None:
                    return None
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
                        counter.increment_games_output()
                        current_record = cursor.next()
                        if current_record is None:
                            break
            finally:
                cursor.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.output_report
            + " to "
            + os.path.basename(filename)
            + " in internal format"
        )
    finally:
        database.end_read_only_transaction()
    return True


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
        return None
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_no_comments_no_ravs(gamesout, collected_game)
    return True


def export_single_game_pgn_no_comments(collected_game, filename):
    """Export collected_game to filename in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return None
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_rav_elements(gamesout, collected_game)
    return True


def export_single_game_pgn_no_structured_comments(collected_game, filename):
    """Export collected_game to filename without {[%]} comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return None
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        _export_pgn_rav_no_structured_comments(gamesout, collected_game)
    return True


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
    """Export all database games in a PGN inport format for CQL scan."""
    if filename is None:
        return True
    statusbar.set_status_text("Started: import format for CQL scan")
    statusbar.status.update()
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    database.start_read_only_transaction()
    try:
        counter = _Counter(_all_records_count(database), statusbar)
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
                    counter.increment_games_output()
                    current_record = cursor.next()
        finally:
            cursor.close()
            statusbar.set_status_text(
                "Completed: "
                + counter.output_report
                + " to "
                + os.path.basename(filename)
                + " in import format for CQL scan"
            )
    finally:
        database.end_read_only_transaction()
    return True


def export_games_for_cql_scan(recordset, filename, limit=100000, commit=True):
    """Export up to limit recordset games in recordmap in PGN format.

    A PGN import format accepted by CQL program is used.  The game numbers
    in the PGN file are mapped to the source record number and the map is
    placed in recordmap.

    """
    literal_eval = ast.literal_eval
    database = recordset.dbhome
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


def _all_records_count(database):
    """Return total records for statusbar reports.

    Function must be called with a transaction 'try ... finally'.

    """
    return database.recordlist_ebm(filespec.GAMES_FILE_DEF).count_records()


def _bookmarked_records_count(grid):
    """Return total records for statusbar reports.

    Function must be called with a transaction 'try ... finally'.

    """
    return len(grid.bookmarks)


def _selected_records_count(grid):
    """Return total records for statusbar reports.

    Function must be called with a transaction 'try ... finally'.

    """
    database = grid.get_data_source().dbhome
    return database.recordlist_key_startswith(
        grid.datasource.dbset,
        grid.datasource.dbname,
        keystart=database.encode_record_selector(grid.partial),
    ).count_records()


def _export_all_games(database, filename, statusbar, report_text, exporter):
    """Export all database games in PGN export format."""
    if filename is None:
        return True
    statusbar.set_status_text("Started: " + report_text)
    statusbar.status.update()
    instance = chessrecord.ChessDBrecordGameExport()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    database.start_read_only_transaction()
    try:
        counter = _Counter(_all_records_count(database), statusbar)
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                current_record = cursor.first()
                while current_record:
                    if current_record[0] != prev_date:
                        games_for_date.sort(key=methodcaller("get_collation"))
                        for gfd in games_for_date:
                            exporter(gamesout, gfd)
                            counter.increment_games_output()
                        prev_date = current_record[0]
                        games_for_date = []
                    counter.increment_games_read()
                    game = database.get_primary_record(
                        filespec.GAMES_FILE_DEF, current_record[1]
                    )
                    instance.load_record(game)
                    # Fix pycodestyle E501 (83 > 79 characters).
                    # black formatting applied with line-length = 79.
                    ivcg = instance.value.collected_game
                    if ivcg.is_pgn_valid_export_format():
                        games_for_date.append(ivcg)
                        if all_games_output is None:
                            all_games_output = True
                            no_games_output = False
                    elif all_games_output:
                        if not no_games_output:
                            all_games_output = False
                    current_record = cursor.next()
                games_for_date.sort(key=methodcaller("get_collation"))
                for gfd in games_for_date:
                    exporter(gamesout, gfd)
                    counter.increment_games_output()
        finally:
            cursor.close()
            statusbar.set_status_text(
                "Completed: "
                + counter.output_report
                + " to "
                + os.path.basename(filename)
                + " in "
                + report_text
            )
    finally:
        database.end_read_only_transaction()
    return all_games_output


def _export_selected_games(grid, filename, report_text, exporter):
    """Export selected games in PGN format.

    Partial key is not supported for the arbitrary record number key.

    """
    if filename is None:
        return True
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        instance = chessrecord.ChessDBrecordGameExport()
        instance.set_database(database)
        all_games_output = True
        if grid.bookmarks:
            counter = _Counter(_bookmarked_records_count(grid), statusbar)
            statusbar.set_status_text("Started (bookmark): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            keyset = database.recordlist_nil(dbset)
            try:
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    for bookmark in grid.bookmarks:
                        keyset.place_record_number(bookmark[0])
                    all_games_output = all_games_output and (
                        _export_selected_games_index_order_date(
                            keyset, gamesout, instance, exporter, counter
                        )
                    )
            finally:
                keyset.close()
        else:
            counter = _Counter(_all_records_count(database), statusbar)
            statusbar.set_status_text("Started (all grid): " + report_text)
            statusbar.status.update_idletasks()
            valuespec = ValuesClause()
            valuespec.field = filespec.PGN_DATE_FIELD_DEF
            dbset = grid.get_data_source().dbset
            selector = database.encode_record_selector
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for key in database.find_values_ascending(valuespec, dbset):
                    dateset = database.recordlist_key(
                        dbset, valuespec.field, key=selector(key)
                    )
                    try:
                        dateset_count = dateset.count_records()
                        if dateset_count > _MEMORY_SORT_LIMIT:
                            all_games_output = all_games_output and (
                                _export_selected_games_index_order_event(
                                    dateset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                        else:
                            all_games_output = all_games_output and (
                                _export_selected_games_pgn_collation_order(
                                    dateset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                    finally:
                        dateset.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.output_report
            + " to "
            + os.path.basename(filename)
            + " in "
            + report_text
        )
    finally:
        database.end_read_only_transaction()
    return all_games_output


def _export_selected_games_pgn_collation_order(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    all_games_output = True
    games_for_date = []
    prev_date = None
    cursor = selected.create_recordsetbase_cursor()
    try:
        while True:
            current_record = cursor.next()
            if current_record is None:
                break
            counter.increment_games_read()
            instance.load_record(current_record)
            ivcg = instance.value.collected_game
            if ivcg.is_pgn_valid_export_format():
                current_date = ivcg.pgn_tags["Date"]
                if current_date != prev_date:
                    games_for_date.sort(key=methodcaller("get_collation"))
                    for gfd in games_for_date:
                        exporter(gamesout, gfd)
                        counter.increment_games_output()
                    games_for_date = []
                    prev_date = current_date
                games_for_date.append(ivcg)
            else:
                all_games_output = False
        if games_for_date:
            games_for_date.sort(key=methodcaller("get_collation"))
            for gfd in games_for_date:
                exporter(gamesout, gfd)
                counter.increment_games_output()
    finally:
        cursor.close()
    return all_games_output


def _export_selected_games_database_order(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in database order."""
    all_games_output = True
    cursor = selected.create_recordsetbase_cursor()
    try:
        while True:
            current_record = cursor.next()
            if current_record is None:
                break
            counter.increment_games_read()
            instance.load_record(current_record)
            ivcg = instance.value.collected_game
            if ivcg.is_pgn_valid_export_format():
                exporter(gamesout, ivcg)
                counter.increment_games_output()
            else:
                all_games_output = False
    finally:
        cursor.close()
    return all_games_output


def _export_selected_games_index_order(grid, filename, report_text, exporter):
    """Export selected games in PGN format in index order."""
    if filename is None:
        return True
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        instance = chessrecord.ChessDBrecordGameExport()
        instance.set_database(database)
        all_games_output = True
        if grid.bookmarks:
            counter = _Counter(_bookmarked_records_count(grid), statusbar)
            statusbar.set_status_text("Started (bookmark): " + report_text)
            statusbar.status.update_idletasks()
            dbset = grid.get_data_source().dbset
            prev_key = None
            keyset = database.recordlist_nil(dbset)
            try:
                with open(filename, "w", encoding=_ENCODING) as gamesout:
                    for bookmark in grid.bookmarks:
                        if prev_key != bookmark[0]:
                            all_games_output = all_games_output and (
                                _export_selected_games_index_order_bookmark(
                                    keyset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                            keyset.clear_recordset()
                            prev_key = bookmark[0]
                        keyset.place_record_number(bookmark[1])
                    all_games_output = all_games_output and (
                        _export_selected_games_index_order_bookmark(
                            keyset, gamesout, instance, exporter, counter
                        )
                    )
                    keyset.clear_recordset()
            finally:
                keyset.close()
        elif grid.partial:
            counter = _Counter(_selected_records_count(grid), statusbar)
            statusbar.set_status_text("Started (key): " + report_text)
            statusbar.status.update_idletasks()
            valuespec = ValuesClause()
            valuespec.field = grid.get_data_source().dbname
            valuespec.from_value = grid.partial
            dbset = grid.get_data_source().dbset
            selector = database.encode_record_selector
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for key in database.find_values_ascending(valuespec, dbset):
                    if not key.startswith(grid.partial):
                        break
                    keyset = database.recordlist_key(
                        dbset, valuespec.field, key=selector(key)
                    )
                    try:
                        if keyset.count_records() > _MEMORY_SORT_LIMIT:
                            all_games_output = all_games_output and (
                                _export_selected_games_index_order_date(
                                    keyset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                        else:
                            all_games_output = all_games_output and (
                                _export_selected_games_index_order_value(
                                    keyset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                    finally:
                        keyset.close()
        else:
            counter = _Counter(_all_records_count(database), statusbar)
            statusbar.set_status_text("Started (all grid): " + report_text)
            statusbar.status.update_idletasks()
            valuespec = ValuesClause()
            valuespec.field = grid.get_data_source().dbname
            dbset = grid.get_data_source().dbset
            selector = database.encode_record_selector
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for key in database.find_values_ascending(valuespec, dbset):
                    keyset = database.recordlist_key(
                        dbset, valuespec.field, key=selector(key)
                    )
                    try:
                        if keyset.count_records() > _MEMORY_SORT_LIMIT:
                            all_games_output = all_games_output and (
                                _export_selected_games_index_order_date(
                                    keyset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                        else:
                            all_games_output = all_games_output and (
                                _export_selected_games_index_order_value(
                                    keyset,
                                    gamesout,
                                    instance,
                                    exporter,
                                    counter,
                                )
                            )
                    finally:
                        keyset.close()
        statusbar.set_status_text(
            "Completed: "
            + counter.output_report
            + " to "
            + os.path.basename(filename)
            + " in "
            + report_text
        )
    finally:
        database.end_read_only_transaction()
    return all_games_output


def _export_selected_games_index_order_bookmark(
    keyset, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    count = keyset.count_records()
    if count > _MEMORY_SORT_LIMIT:
        return _export_selected_games_index_order_date(
            keyset, gamesout, instance, exporter, counter
        )
    if count > 0:  # essential when prev_key is None.
        return _export_selected_games_index_order_value(
            keyset, gamesout, instance, exporter, counter
        )
    return True


def _export_selected_games_index_order_result(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.RESULT_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        resultset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            resultset_count = resultset.count_records()
            if resultset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_database_order(
                        resultset, gamesout, instance, exporter, counter
                    )
                )
            elif resultset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        resultset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            resultset.close()
    return all_games_output


def _export_selected_games_index_order_black(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.BLACK_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        blackset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            blackset_count = blackset.count_records()
            if blackset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_index_order_result(
                        blackset, gamesout, instance, exporter, counter
                    )
                )
            elif blackset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        blackset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            blackset.close()
    return all_games_output


def _export_selected_games_index_order_white(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.WHITE_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        whiteset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            whiteset_count = whiteset.count_records()
            if whiteset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_index_order_black(
                        whiteset, gamesout, instance, exporter, counter
                    )
                )
            elif whiteset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        whiteset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            whiteset.close()
    return all_games_output


def _export_selected_games_index_order_round(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.ROUND_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        roundset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            roundset_count = roundset.count_records()
            if roundset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_index_order_white(
                        roundset, gamesout, instance, exporter, counter
                    )
                )
            elif roundset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        roundset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            roundset.close()
    return all_games_output


def _export_selected_games_index_order_site(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.SITE_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        siteset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            siteset_count = siteset.count_records()
            if siteset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_index_order_round(
                        siteset, gamesout, instance, exporter, counter
                    )
                )
            elif siteset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        siteset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            siteset.close()
    return all_games_output


def _export_selected_games_index_order_event(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.EVENT_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        eventset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            eventset_count = eventset.count_records()
            if eventset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_index_order_site(
                        eventset, gamesout, instance, exporter, counter
                    )
                )
            elif eventset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        eventset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            eventset.close()
    return all_games_output


def _export_selected_games_index_order_date(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    valuespec = ValuesClause()
    valuespec.field = filespec.PGN_DATE_FIELD_DEF
    database = selected.recordset.dbhome
    dbset = selected.recordset.dbset
    selector = database.encode_record_selector
    all_games_output = True
    for key in database.find_values_ascending(valuespec, dbset):
        dateset = (
            database.recordlist_key(dbset, valuespec.field, key=selector(key))
            & selected
        )
        try:
            dateset_count = dateset.count_records()
            if dateset_count > _MEMORY_SORT_LIMIT:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_index_order_event(
                        dateset, gamesout, instance, exporter, counter
                    )
                )
            elif dateset_count > 0:
                all_games_output = (
                    all_games_output
                    and _export_selected_games_pgn_collation_order(
                        dateset, gamesout, instance, exporter, counter
                    )
                )
        finally:
            dateset.close()
    return all_games_output


def _export_selected_games_index_order_value(
    selected, gamesout, instance, exporter, counter
):
    """Export selected games in PGN format in PGN collation order."""
    all_games_output = True
    games_for_value = []
    cursor = selected.create_recordsetbase_cursor()
    try:
        while True:
            current_record = cursor.next()
            if current_record is None:
                games_for_value.sort(key=methodcaller("get_collation"))
                for gfv in games_for_value:
                    exporter(gamesout, gfv)
                    counter.increment_games_output()
                break
            counter.increment_games_read()
            instance.load_record(current_record)
            ivcg = instance.value.collected_game
            if ivcg.is_pgn_valid_export_format():
                games_for_value.append(ivcg)
            else:
                all_games_output = False
    finally:
        cursor.close()
    return all_games_output


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
