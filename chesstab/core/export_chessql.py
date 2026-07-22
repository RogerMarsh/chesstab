# export_chessql.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess chessql (CQL query) exporters."""

import os

from . import chessrecord, filespec, count_export
from .cqlstatement import CQLStatement

_ENCODING = "utf-8"


def export_all_positions(database, filename, statusbar):
    """Export CQL statements in database to text file in internal format."""
    if filename is None:
        return
    statusbar.status.update()
    statusbar.set_status_text("Started: CQL statement")
    statusbar.status.update_idletasks()
    instance = chessrecord.ChessDBrecordPartial()
    instance.set_database(database)
    counter = count_export.create_counter(statusbar)
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.CQL_FILE_DEF
        )
        counter.items_selected = counter.items_database
        cursor = database.database_cursor(
            filespec.CQL_FILE_DEF, filespec.CQL_FILE_DEF
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
            + " of CQL statements"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_selected_positions(grid, filename):
    """Export CQL statements in grid to textfile."""
    if filename is None:
        return
    statusbar = grid.ui.statusbar
    statusbar.status.update()
    statusbar.set_status_text("Started: CQL statement")
    statusbar.status.update_idletasks()
    counter = count_export.create_counter(statusbar)
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        database.start_read_only_transaction()
        try:
            counter.items_database = database.count_all_records(
                filespec.CQL_FILE_DEF
            )
            counter.items_selected = len(grid.bookmarks)
            primary = database.is_primary(
                grid.get_data_source().dbset, grid.get_data_source().dbname
            )
            instance = chessrecord.ChessDBrecordPartial()
            instance.set_database(database)
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                for bookmark in sorted(grid.bookmarks):
                    instance.load_record(
                        database.get_primary_record(
                            filespec.CQL_FILE_DEF,
                            bookmark[0 if primary else 1],
                        )
                    )
                    gamesout.write(instance.get_srvalue())
                    gamesout.write("\n")
                    counter.increment_items_output()
            statusbar.set_status_text(
                "Completed: "
                + counter.completed_report()
                + " to "
                + os.path.basename(filename)
                + " of CQL statements"
            )
        finally:
            database.end_read_only_transaction()
        return
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
        counter.items_database = database.count_all_records(
            filespec.CQL_FILE_DEF
        )
        instance = chessrecord.ChessDBrecordPartial()
        instance.set_database(database)
        counter.items_selected = grid.record_count
        cursor = database.database_cursor(
            filespec.CQL_FILE_DEF, filespec.CQL_FILE_DEF
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
            + " of CQL statements"
        )
    finally:
        database.end_read_only_transaction()
    return


def export_single_position(partialposition, filename):
    """Export CQL statement to textfile."""
    if filename is None:
        return
    cql_statement = CQLStatement()
    cql_statement.prepare_cql_statement(partialposition)
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(cql_statement.get_statement_text())
