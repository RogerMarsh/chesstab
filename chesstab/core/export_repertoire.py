# export_repertoire.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess repertoire exporters."""

from . import chessrecord, filespec
from .export_pgn_import_format import get_game_pgn_import_format

_ENCODING = "utf-8"


def export_all_repertoires_pgn(database, filename):
    """Export all repertoires in PGN export format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
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
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_all_repertoires_pgn_no_comments(database, filename):
    """Export all repertoires in PGN export format without comments."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
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
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_all_repertoires_pgn_import_format(database, filename):
    """Export all repertoires in a PGN import format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
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
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_all_repertoires_text(database, filename):
    """Export repertoires in database to text file in internal format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
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
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_selected_repertoires_pgn(grid, filename):
    """Export selected repertoires in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        instance = chessrecord.ChessDBrecordRepertoire()
        instance.set_database(database)
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for bookmark in sorted(grid.bookmarks):
                instance.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, bookmark[0]
                    )
                )
                if instance.value.collected_game.is_pgn_valid_export_format():
                    gamesout.write(
                        instance.value.collected_game.get_repertoire_pgn()
                    )
        return True
    export_all_repertoires_pgn(grid.get_data_source().dbhome, filename)
    return True


def export_selected_repertoires_pgn_no_comments(grid, filename):
    """Export selected repertoires in PGN export format without comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        instance = chessrecord.ChessDBrecordRepertoire()
        instance.set_database(database)
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for bookmark in sorted(grid.bookmarks):
                instance.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, bookmark[0]
                    )
                )
                if instance.value.collected_game.is_pgn_valid_export_format():
                    rvcg = instance.value.collected_game  # For line length.
                    gamesout.write(rvcg.get_repertoire_pgn_no_comments())
        return
    export_all_repertoires_pgn_no_comments(
        grid.get_data_source().dbhome, filename
    )
    return


def export_selected_repertoires_pgn_import_format(grid, filename):
    """Export selected repertoires in a PGN import format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.REPERTOIRE_FILE_DEF, bookmark[0 if primary else 1]
                )
            )
            if instance.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    get_game_pgn_import_format(instance.value.collected_game)
                )
            else:
                all_games_output = False
    elif grid.partial:
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
                if instance.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(
                            instance.value.collected_game
                        )
                    )
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()
    else:
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
                if instance.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(
                            instance.value.collected_game
                        )
                    )
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n\n")
    return all_games_output


def export_selected_repertoires_text(grid, filename):
    """Export selected repertoires to text file in internal record format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordRepertoire()
    instance.set_database(database)
    games = []
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.REPERTOIRE_FILE_DEF, bookmark[0 if primary else 1]
                )
            )
            games.append(instance.get_srvalue())
    elif grid.partial:
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
    if len(games) == 0:
        return None
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n")
    return True


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
