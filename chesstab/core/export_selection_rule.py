# export_selection_rule.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess selection rule exporters."""

from . import chessrecord, filespec

_ENCODING = "utf-8"


def export_selected_selection_rules(grid, filename):
    """Export selected selection rule statements to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        instance = chessrecord.ChessDBrecordQuery()
        instance.set_database(database)
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for bookmark in sorted(grid.bookmarks):
                instance.load_record(
                    database.get_primary_record(
                        filespec.SELECTION_FILE_DEF, bookmark[0]
                    )
                )
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
        return
    database = grid.get_data_source().dbhome
    instance = chessrecord.ChessDBrecordQuery()
    instance.set_database(database)
    cursor = database.database_cursor(
        filespec.SELECTION_FILE_DEF, filespec.SELECTION_FILE_DEF
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
