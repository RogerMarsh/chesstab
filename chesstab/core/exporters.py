# exporters.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess game, repertoire, and partial position exporters."""

from pgn_read.core.parser import PGN

from . import chessrecord, filespec
from .cqlstatement import CQLStatement


def export_all_games_text(database, filename):
    """Export games in database to text file in internal record format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
    )
    try:
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_all_games_pgn(database, filename):
    """Export all database games in PGN export format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                if current_record[0] != prev_date:
                    for gfd in sorted(games_for_date):
                        gamesout.write(gfd[0])
                        gamesout.write("\n")
                        gamesout.write(gfd[2])
                        gamesout.write("\n")
                        gamesout.write(gfd[1])
                        gamesout.write("\n\n")
                    prev_date = current_record[0]
                    games_for_date = []
                game = database.get_primary_record(
                    filespec.GAMES_FILE_DEF, current_record[1]
                )
                try:
                    instance.load_record(game)
                except StopIteration:
                    break
                if instance.value.collected_game.is_pgn_valid_export_format():
                    games_for_date.append(
                        instance.value.collected_game.get_export_pgn_elements()
                    )
                    if all_games_output is None:
                        all_games_output = True
                        no_games_output = False
                elif all_games_output:
                    if not no_games_output:
                        all_games_output = False
                current_record = cursor.next()
            for gfd in sorted(games_for_date):
                gamesout.write(gfd[0])
                gamesout.write("\n")
                gamesout.write(gfd[2])
                gamesout.write("\n")
                gamesout.write(gfd[1])
                gamesout.write("\n\n")
    finally:
        cursor.close()
    return all_games_output


def export_all_games_pgn_import_format(database, filename):
    """Export all database games in a PGN inport format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
    )
    try:
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                try:
                    instance.load_record(current_record)
                except StopIteration:
                    break
                if instance.value.collected_game.is_pgn_valid_export_format():
                    gamesout.write(
                        get_game_pgn_import_format(
                            instance.value.collected_game
                        )
                    )
                    if all_games_output is None:
                        all_games_output = True
                        no_games_output = False
                elif all_games_output:
                    if not no_games_output:
                        all_games_output = False
                current_record = cursor.next()
    finally:
        cursor.close()
    return all_games_output


def export_all_games_pgn_no_comments(database, filename):
    """Export all database games in PGN export format excluding comments."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                if current_record[0] != prev_date:
                    for gfd in sorted(games_for_date):
                        gamesout.write(gfd[0])
                        gamesout.write("\n")
                        gamesout.write(gfd[2])
                        gamesout.write("\n")
                        gamesout.write(gfd[1])
                        gamesout.write("\n\n")
                    prev_date = current_record[0]
                    games_for_date = []
                game = database.get_primary_record(
                    filespec.GAMES_FILE_DEF, current_record[1]
                )
                try:
                    instance.load_record(game)
                except StopIteration:
                    break
                # Fix pycodestyle E501 (83 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games_for_date.append(ivcg.get_export_pgn_rav_elements())
                    if all_games_output is None:
                        all_games_output = True
                        no_games_output = False
                elif all_games_output:
                    if not no_games_output:
                        all_games_output = False
                current_record = cursor.next()
            for gfd in sorted(games_for_date):
                gamesout.write(gfd[0])
                gamesout.write("\n")
                gamesout.write(gfd[2])
                gamesout.write("\n")
                gamesout.write(gfd[1])
                gamesout.write("\n\n")
    finally:
        cursor.close()
    return all_games_output


def export_all_games_pgn_no_comments_no_ravs(database, filename):
    """Export all database games, tags and moves only, in PGN export format.

    Comments and RAVs are excluded from the export.

    """
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                if current_record[0] != prev_date:
                    for gfd in sorted(games_for_date):
                        gamesout.write(gfd[0])
                        gamesout.write("\n")
                        gamesout.write(gfd[2])
                        gamesout.write("\n")
                        gamesout.write(gfd[1])
                        gamesout.write("\n\n")
                    prev_date = current_record[0]
                    games_for_date = []
                game = database.get_primary_record(
                    filespec.GAMES_FILE_DEF, current_record[1]
                )
                try:
                    instance.load_record(game)
                except StopIteration:
                    break
                collected_game = instance.value.collected_game
                if collected_game.is_pgn_valid_export_format():
                    strt = collected_game.get_seven_tag_roster_tags()
                    nstrt = collected_game.get_non_seven_tag_roster_tags()
                    archive_movetext = collected_game.get_archive_movetext()
                    games_for_date.append((strt, archive_movetext, nstrt))
                    if all_games_output is None:
                        all_games_output = True
                        no_games_output = False
                elif all_games_output:
                    if not no_games_output:
                        all_games_output = False
                current_record = cursor.next()
            for gfd in sorted(games_for_date):
                gamesout.write(gfd[0])
                gamesout.write("\n")
                gamesout.write(gfd[2])
                gamesout.write("\n")
                gamesout.write(gfd[1])
                gamesout.write("\n\n")
    finally:
        cursor.close()
    return all_games_output


def export_all_games_pgn_reduced_export_format(database, filename):
    """Export all database games in PGN reduced export format."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                if current_record[0] != prev_date:
                    for gfd in sorted(games_for_date):
                        gamesout.write(gfd[0])
                        gamesout.write("\n")
                        gamesout.write(gfd[1])
                        gamesout.write("\n\n")
                    prev_date = current_record[0]
                    games_for_date = []
                game = database.get_primary_record(
                    filespec.GAMES_FILE_DEF, current_record[1]
                )
                try:
                    instance.load_record(game)
                except StopIteration:
                    break
                # Fix pycodestyle E501 (80 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games_for_date.append(ivcg.get_archive_pgn_elements())
                    if all_games_output is None:
                        all_games_output = True
                        no_games_output = False
                elif all_games_output:
                    if not no_games_output:
                        all_games_output = False
                current_record = cursor.next()
            for gfd in sorted(games_for_date):
                gamesout.write(gfd[0])
                gamesout.write("\n")
                gamesout.write(gfd[1])
                gamesout.write("\n\n")
    finally:
        cursor.close()
    return all_games_output


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
        with open(filename, "w") as gamesout:
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
        with open(filename, "w") as gamesout:
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
        with open(filename, "w") as gamesout:
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
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


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
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return True


def export_selected_games_pgn_import_format(grid, filename):
    """Export selected records in a PGN import format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, bookmark[0 if primary else 1]
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
                        filespec.GAMES_FILE_DEF,
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

        # For all grids except ones displayed via 'Select | Rule | List Games'
        # the 'current_record = cursor.next()' can be immediately after the
        # 'while True:' statement, and the 'current_record = cursor.first()'
        # statement is redundant.
        # I think this implies a problem in the solentware_base RecordsetCursor
        # classes for each database engine since the 'finally:' clause should
        # kill the cursor.
        # The problem is only the first request outputs all the records to the
        # file.  Subsequent requests find no records to output, except that
        # doing some scrolling action resets the cursor and the next request
        # outputs all the records before the problem repeats.
        # The other methods in this class with this construct are affected too,
        # but this comment is not repeated.
        try:
            current_record = cursor.first()
            while True:
                if current_record is None:
                    break
                instance.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF,
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
    with open(filename, "w") as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n\n")
    return all_games_output


def export_selected_games_pgn(grid, filename):
    """Export selected records in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, bookmark[0 if primary else 1]
                )
            )
            if instance.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    instance.value.collected_game.get_export_pgn_elements()
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                if instance.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        instance.value.collected_game.get_export_pgn_elements()
                    )
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()

        # For all grids except ones displayed via 'Select | Rule | List Games'
        # the 'current_record = cursor.next()' can be immediately after the
        # 'while True:' statement, and the 'current_record = cursor.first()'
        # statement is redundant.
        # I think this implies a problem in the solentware_base RecordsetCursor
        # classes for each database engine since the 'finally:' clause should
        # kill the cursor.
        # The problem is only the first request outputs all the records to the
        # file.  Subsequent requests find no records to output, except that
        # doing some scrolling action resets the cursor and the next request
        # outputs all the records before the problem repeats.
        # The other methods in this class with this construct are affected too,
        # but this comment is not repeated.
        try:
            current_record = cursor.first()
            while True:
                if current_record is None:
                    break
                instance.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                if instance.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        instance.value.collected_game.get_export_pgn_elements()
                    )
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()

    if len(games) == 0:
        return None
    with open(filename, "w") as gamesout:
        for game in sorted(games):
            gamesout.write(game[0])
            gamesout.write("\n")
            gamesout.write(game[2])
            gamesout.write("\n")
            gamesout.write(game[1])
            gamesout.write("\n\n")
    return all_games_output


def export_selected_games_pgn_no_comments(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, bookmark[0 if primary else 1]
                )
            )
            if instance.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    instance.value.collected_game.get_export_pgn_rav_elements()
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                # Fix pycodestyle E501 (83 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(ivcg.get_export_pgn_rav_elements())
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                # Fix pycodestyle E501 (83 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(ivcg.get_export_pgn_rav_elements())
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    with open(filename, "w") as gamesout:
        for game in sorted(games):
            gamesout.write(game[0])
            gamesout.write("\n")
            gamesout.write(game[2])
            gamesout.write("\n")
            gamesout.write(game[1])
            gamesout.write("\n\n")
    return all_games_output


def export_selected_games_pgn_no_comments_no_ravs(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, bookmark[0 if primary else 1]
                )
            )
            collected_game = instance.value.collected_game
            if collected_game.is_pgn_valid_export_format():
                strt = collected_game.get_seven_tag_roster_tags()
                nstrt = collected_game.get_non_seven_tag_roster_tags()
                archive_movetext = collected_game.get_archive_movetext()
                games.append((strt, archive_movetext, nstrt))
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                collected_game = instance.value.collected_game
                if collected_game.is_pgn_valid_export_format():
                    strt = collected_game.get_seven_tag_roster_tags()
                    nstrt = collected_game.get_non_seven_tag_roster_tags()
                    archive_movetext = collected_game.get_archive_movetext()
                    games.append((strt, archive_movetext, nstrt))
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                collected_game = instance.value.collected_game
                if collected_game.is_pgn_valid_export_format():
                    strt = collected_game.get_seven_tag_roster_tags()
                    nstrt = collected_game.get_non_seven_tag_roster_tags()
                    archive_movetext = collected_game.get_archive_movetext()
                    games.append((strt, archive_movetext, nstrt))
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    with open(filename, "w") as gamesout:
        for game in sorted(games):
            gamesout.write(game[0])
            gamesout.write("\n")
            gamesout.write(game[2])
            gamesout.write("\n")
            gamesout.write(game[1])
            gamesout.write("\n\n")
    return all_games_output


def export_selected_games_pgn_reduced_export_format(grid, filename):
    """Export selected records in grid to PGN file in reduced export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, bookmark[0 if primary else 1]
                )
            )
            if instance.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    instance.value.collected_game.get_archive_pgn_elements()
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                # Fix pycodestyle E501 (80 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(ivcg.get_archive_pgn_elements())
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                # Fix pycodestyle E501 (80 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(ivcg.get_archive_pgn_elements())
                else:
                    all_games_output = False
                current_record = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    with open(filename, "w") as gamesout:
        for game in sorted(games):
            gamesout.write(game[0])
            gamesout.write("\n")
            gamesout.write(game[1])
            gamesout.write("\n\n")
    return all_games_output


def export_selected_games_text(grid, filename):
    """Export selected records in grid to text file in internal record format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname
    )
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    games = []
    if grid.bookmarks:
        for bookmark in grid.bookmarks:
            instance.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, bookmark[0 if primary else 1]
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
                        filespec.GAMES_FILE_DEF,
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
                        filespec.GAMES_FILE_DEF,
                        current_record[0 if primary else 1],
                    )
                )
                games.append(instance.get_srvalue())
                current_record = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    with open(filename, "w") as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n")
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
        with open(filename, "w") as gamesout:
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
        with open(filename, "w") as gamesout:
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
    with open(filename, "w") as gamesout:
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
    with open(filename, "w") as gamesout:
        for game in games:
            gamesout.write(game)
            gamesout.write("\n")
    return True


def export_selected_positions(grid, filename):
    """Export CQL statements in grid to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        instance = chessrecord.ChessDBrecordPartial()
        instance.set_database(database)
        with open(filename, "w") as gamesout:
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
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return


def export_selected_selection_rules(grid, filename):
    """Export selected selection rule statements to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        instance = chessrecord.ChessDBrecordQuery()
        instance.set_database(database)
        with open(filename, "w") as gamesout:
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
        with open(filename, "w") as gamesout:
            current_record = cursor.first()
            while current_record:
                instance.load_record(current_record)
                gamesout.write(instance.get_srvalue())
                gamesout.write("\n")
                current_record = cursor.next()
    finally:
        cursor.close()
    return


def export_single_game_pgn_reduced_export_format(collected_game, filename):
    """Export collected_game to PGN file in reduced export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w") as gamesout:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_archive_movetext())
        gamesout.write("\n\n")


def export_single_game_pgn(collected_game, filename):
    """Export collected_game to filename in PGN export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w") as gamesout:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_all_movetext_in_pgn_export_format())
        gamesout.write("\n\n")


def export_single_game_pgn_no_comments_no_ravs(collected_game, filename):
    """Export collected_game tags and moves to filename in PGN export format.

    No comments or RAVs are included in the export (PGN Tags and moves
    played only).

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return None
    with open(filename, "w") as gamesout:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_archive_movetext())
        gamesout.write("\n\n")
    return True


def export_single_game_pgn_no_comments(collected_game, filename):
    """Export collected_game to filename in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return None
    with open(filename, "w") as gamesout:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(
            collected_game.get_movetext_without_comments_in_pgn_export_format()
        )
        gamesout.write("\n\n")
    return True


def export_single_game_pgn_import_format(collected_game, filename):
    """Export collected_game to pgn file in a PGN import format."""
    if filename is None:
        return
    with open(filename, "w") as gamesout:
        gamesout.write(get_game_pgn_import_format(collected_game))


def export_single_game_text(collected_game, filename):
    """Export collected_game to text file in internal format."""
    if filename is None:
        return
    internal_format = next(PGN().read_games(collected_game.get_text_of_game()))
    with open(filename, "w") as gamesout:
        gamesout.write(internal_format.get_text_of_game())
        gamesout.write("\n")


def export_single_repertoire_pgn(collected_game, filename):
    """Export repertoire in import format PGN to *.pgn file.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w") as gamesout:
        gamesout.write(collected_game.get_repertoire_pgn())


def export_single_repertoire_pgn_no_comments(collected_game, filename):
    """Export repertoire in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w") as gamesout:
        gamesout.write(collected_game.get_repertoire_pgn_no_comments())


def export_single_position(partialposition, filename):
    """Export CQL statement to textfile."""
    if filename is None:
        return
    cql_statement = CQLStatement()
    cql_statement.process_statement(partialposition)
    if not cql_statement.is_statement():
        return
    with open(filename, "w") as gamesout:
        gamesout.write(cql_statement.get_name_position_text())


# Derived from get_all_movetext_in_pgn_export_format method in
# pgn_read.core.game module.
# At 13 Jan 2021 on a sample of two other non-commercial open source chess
# database products both require a restricted line length to allow extraction
# of the game score.  One of them looks like it needs '\n' as tag_separator.
# The other finds all games and tags with both name_value_separator and
# tag_separator as ' ', but finds nothing with both as ''.  Both accept '\n'
# as block_separator rather than '\n\n' which puts a blank line at significant
# points. Neither accepts '', no whitespace, between movetext tokens.  Neither
# needs move numbers or black move indicators.
# Hence the choice of default values.
def get_game_pgn_import_format(
    collected_game,
    name_value_separator=" ",
    tag_separator=" ",
    movetext_separator=" ",
    block_separator="\n",
    line_length=79,
):
    """Construct game score in a PGN import format.

    This method cannot generate text which is identical to internal format
    because the movetext tokens have check and checkmate indicator suffixes
    where appropriate.

    """
    if not isinstance(line_length, int):
        return "".join(
            (
                tag_separator.join(
                    collected_game.get_tags(
                        name_value_separator=name_value_separator
                    )
                ),
                block_separator,
                movetext_separator.join(collected_game.get_movetext()),
                block_separator,
            )
        )
    _attt = _add_token_to_text
    text = []
    length = 0
    for token in collected_game.get_tags(
        name_value_separator=name_value_separator
    ):
        length = _add_token_to_text(
            token, text, line_length, tag_separator, length
        )
    text.append(block_separator)
    length = len(block_separator.split("\n")[-1])
    for token in collected_game.get_movetext():
        if token.startswith("{"):
            comment = token.split()
            length = _add_token_to_text(
                comment.pop(0), text, line_length, movetext_separator, length
            )
            for word in comment:
                length = _add_token_to_text(
                    word, text, line_length, " ", length
                )
        elif token.startswith("$"):
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
        elif token.startswith(";"):
            if len(token) + length >= line_length:
                text.append("\n")
            else:
                text.append(movetext_separator)
            text.append(token)
            length = 0
        elif token == "(":
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
        elif token == ")":
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
        else:
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
    text.append(block_separator)
    return "".join(text)


# Derived from _add_token_to_movetext method in pgn_read.core.game module.
def _add_token_to_text(token, text, line_length, token_separator, length):
    if not length:
        text.append(token)
        return len(token)
    if len(token) + length >= line_length:
        text.append("\n")
        text.append(token)
        return len(token)
    text.append(token_separator)
    text.append(token)
    return len(token) + length + len(token_separator)
