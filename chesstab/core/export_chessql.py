# export_chessql.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess chessql (partial position) exporters."""

from . import chessrecord, filespec
from .cqlstatement import CQLStatement

_ENCODING = "utf-8"


def export_all_positions(database, filename):
    """Export CQL statements in database to text file in internal format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordPartial()
    instance.set_database(database)
    cursor = database.database_cursor(
        filespec.PARTIAL_FILE_DEF, filespec.PARTIAL_FILE_DEF
    )
    try:
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_selected_positions(grid, filename):
    """Export CQL statements in grid to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        instance = chessrecord.ChessDBrecordPartial()
        instance.set_database(database)
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for bookmark in sorted(grid.bookmarks):
                instance.load_record(
                    database.get_primary_record(
                        filespec.PARTIAL_FILE_DEF, bookmark[0]
                    )
                )
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
        return
    database = grid.get_data_source().dbhome
    instance = chessrecord.ChessDBrecordPartial()
    instance.set_database(database)
    cursor = database.database_cursor(
        filespec.PARTIAL_FILE_DEF, filespec.PARTIAL_FILE_DEF
    )
    try:
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return


def export_single_position(partialposition, filename):
    """Export CQL statement to textfile."""
    if filename is None:
        return
    cql_statement = CQLStatement()
    cql_statement.process_statement(partialposition)
    if not cql_statement.is_statement():
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(cql_statement.get_statement_text())
