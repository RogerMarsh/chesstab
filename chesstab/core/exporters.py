# exporters.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess game, repertoire, and partial position exporters.
"""

import os

from pgn_read.core.parser import PGN

from . import chessrecord, filespec
from .cqlstatement import CQLStatement


def export_all_games_text(database, filename):
    """Export games in database to text file in internal record format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGameText()
    rr.set_database(database)
    gamesout = open(filename, "w", encoding="iso-8859-1")
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            gamesout.write(rr.get_srvalue())
            gamesout.write("\n")
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
    return True


def export_all_games_pgn(database, filename):
    """Export all database games in PGN export format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write("\n")
                    gamesout.write(gfd[2])
                    gamesout.write("\n")
                    gamesout.write(gfd[1])
                    gamesout.write("\n\n")
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid_export_format():
                games_for_date.append(
                    rr.value.collected_game.get_export_pgn_elements()
                )
                if all_games_output is None:
                    all_games_output = True
                    no_games_output = False
            elif all_games_output:
                if not no_games_output:
                    all_games_output = False
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write("\n")
            gamesout.write(gfd[2])
            gamesout.write("\n")
            gamesout.write(gfd[1])
            gamesout.write("\n\n")
    finally:
        cursor.close()
        gamesout.close()
    return all_games_output


def export_all_games_pgn_import_format(database, filename):
    """Export all database games in a PGN inport format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    all_games_output = None
    no_games_output = True
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            try:
                rr.load_record(r)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid_export_format():
                gamesout.write(
                    get_game_pgn_import_format(rr.value.collected_game)
                )
                if all_games_output is None:
                    all_games_output = True
                    no_games_output = False
            elif all_games_output:
                if not no_games_output:
                    all_games_output = False
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
    return all_games_output


def export_all_games_pgn_no_comments(database, filename):
    """Export all database games in PGN export format excluding comments."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write("\n")
                    gamesout.write(gfd[2])
                    gamesout.write("\n")
                    gamesout.write(gfd[1])
                    gamesout.write("\n\n")
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid_export_format():
                games_for_date.append(
                    rr.value.collected_game.get_export_pgn_rav_elements()
                )
                if all_games_output is None:
                    all_games_output = True
                    no_games_output = False
            elif all_games_output:
                if not no_games_output:
                    all_games_output = False
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write("\n")
            gamesout.write(gfd[2])
            gamesout.write("\n")
            gamesout.write(gfd[1])
            gamesout.write("\n\n")
    finally:
        cursor.close()
        gamesout.close()
    return all_games_output


def export_all_games_pgn_no_comments_no_ravs(database, filename):
    """Export all database games in PGN export format excluding comments and
    RAVs.

    """
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write("\n")
                    gamesout.write(gfd[2])
                    gamesout.write("\n")
                    gamesout.write(gfd[1])
                    gamesout.write("\n\n")
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            cg = rr.value.collected_game
            if cg.is_pgn_valid_export_format():
                strt = cg.get_seven_tag_roster_tags()
                nstrt = cg.get_non_seven_tag_roster_tags()
                am = cg.get_archive_movetext()
                games_for_date.append((strt, am, nstrt))
                if all_games_output is None:
                    all_games_output = True
                    no_games_output = False
            elif all_games_output:
                if not no_games_output:
                    all_games_output = False
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write("\n")
            gamesout.write(gfd[2])
            gamesout.write("\n")
            gamesout.write(gfd[1])
            gamesout.write("\n\n")
    finally:
        cursor.close()
        gamesout.close()
    return all_games_output


def export_all_games_pgn_reduced_export_format(database, filename):
    """Export all database games in PGN reduced export format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
    )
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write("\n")
                    gamesout.write(gfd[1])
                    gamesout.write("\n\n")
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid_export_format():
                games_for_date.append(
                    rr.value.collected_game.get_archive_pgn_elements()
                )
                if all_games_output is None:
                    all_games_output = True
                    no_games_output = False
            elif all_games_output:
                if not no_games_output:
                    all_games_output = False
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write("\n")
            gamesout.write(gfd[1])
            gamesout.write("\n\n")
    finally:
        cursor.close()
        gamesout.close()
    return all_games_output


def export_all_repertoires_pgn(database, filename):
    """Export all repertoires in PGN export format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            if rr.value.collected_game.is_pgn_valid():
                gamesout.write(rr.value.collected_game.get_repertoire_pgn())
                gamesout.write("\n\n")
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
    return True


def export_all_repertoires_pgn_no_comments(database, filename):
    """Export all repertoires in PGN export format without comments."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            if rr.value.collected_game.is_pgn_valid():
                gamesout.write(
                    rr.value.collected_game.get_repertoire_pgn_no_comments()
                )
                gamesout.write("\n\n")
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
    return True


def export_all_repertoires_pgn_import_format(database, filename):
    """Export all repertoires in a PGN import format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            if rr.value.collected_game.is_pgn_valid():
                gamesout.write(
                    get_game_pgn_import_format(rr.value.collected_game)
                )
                gamesout.write("\n\n")
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
    return True


def export_all_repertoires_text(database, filename):
    """Export repertoires in database to text file in internal record format."""
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordGameText()
    rr.set_database(database)
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            gamesout.write(rr.get_srvalue())
            gamesout.write("\n")
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
    return True


def export_all_positions(database, filename):
    """Export CQL statements in database to text file in internal record
    format.

    """
    if filename is None:
        return True
    rr = chessrecord.ChessDBrecordPartial()
    rr.set_database(database)
    gamesout = open(filename, "w")
    cursor = database.database_cursor(
        filespec.PARTIAL_FILE_DEF, filespec.PARTIAL_FILE_DEF
    )
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            gamesout.write(rr.get_srvalue())
            gamesout.write("\n")
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, b[0 if primary else 1]
                )
            )
            if rr.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    get_game_pgn_import_format(rr.value.collected_game)
                )
            else:
                all_games_output = False
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(rr.value.collected_game)
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()

        # For all grids except ones displayed via 'Select | Rule | List Games'
        # the 'r = cursor.next()' can be immediately after the 'while True:'
        # statement, and the 'r = cursor.first()' statement is redundant.
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
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(rr.value.collected_game)
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()

    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in games:
            gamesout.write(g)
            gamesout.write("\n\n")
    finally:
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, b[0 if primary else 1]
                )
            )
            if rr.value.collected_game.is_pgn_valid_export_format():
                games.append(rr.value.collected_game.get_export_pgn_elements())
            else:
                all_games_output = False
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        rr.value.collected_game.get_export_pgn_elements()
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()

        # For all grids except ones displayed via 'Select | Rule | List Games'
        # the 'r = cursor.next()' can be immediately after the 'while True:'
        # statement, and the 'r = cursor.first()' statement is redundant.
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
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        rr.value.collected_game.get_export_pgn_elements()
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()

    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write("\n")
            gamesout.write(g[2])
            gamesout.write("\n")
            gamesout.write(g[1])
            gamesout.write("\n\n")
    finally:
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, b[0 if primary else 1]
                )
            )
            if rr.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    rr.value.collected_game.get_export_pgn_rav_elements()
                )
            else:
                all_games_output = False
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        rr.value.collected_game.get_export_pgn_rav_elements()
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        rr.value.collected_game.get_export_pgn_rav_elements()
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write("\n")
            gamesout.write(g[2])
            gamesout.write("\n")
            gamesout.write(g[1])
            gamesout.write("\n\n")
    finally:
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, b[0 if primary else 1]
                )
            )
            cg = rr.value.collected_game
            if cg.is_pgn_valid_export_format():
                strt = cg.get_seven_tag_roster_tags()
                nstrt = cg.get_non_seven_tag_roster_tags()
                am = cg.get_archive_movetext()
                games.append((strt, am, nstrt))
            else:
                all_games_output = False
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                cg = rr.value.collected_game
                if cg.is_pgn_valid_export_format():
                    strt = cg.get_seven_tag_roster_tags()
                    nstrt = cg.get_non_seven_tag_roster_tags()
                    am = cg.get_archive_movetext()
                    games.append((strt, am, nstrt))
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                cg = rr.value.collected_game
                if cg.is_pgn_valid_export_format():
                    strt = cg.get_seven_tag_roster_tags()
                    nstrt = cg.get_non_seven_tag_roster_tags()
                    am = cg.get_archive_movetext()
                    games.append((strt, am, nstrt))
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write("\n")
            gamesout.write(g[2])
            gamesout.write("\n")
            gamesout.write(g[1])
            gamesout.write("\n\n")
    finally:
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, b[0 if primary else 1]
                )
            )
            if rr.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    rr.value.collected_game.get_archive_pgn_elements()
                )
            else:
                all_games_output = False
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        rr.value.collected_game.get_archive_pgn_elements()
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        rr.value.collected_game.get_archive_pgn_elements()
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write("\n")
            gamesout.write(g[1])
            gamesout.write("\n\n")
    finally:
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.GAMES_FILE_DEF, b[0 if primary else 1]
                )
            )
            games.append(rr.get_srvalue())
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                games.append(rr.get_srvalue())
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.GAMES_FILE_DEF, r[0 if primary else 1]
                    )
                )
                games.append(rr.get_srvalue())
                r = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in games:
            gamesout.write(g)
            gamesout.write("\n")
    finally:
        gamesout.close()
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
        rr = chessrecord.ChessDBrecordRepertoire()
        rr.set_database(database)
        gamesout = open(filename, "w")
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, b[0]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    gamesout.write(
                        rr.value.collected_game.get_repertoire_pgn()
                    )
            gamesout = open(filename, "w")
        finally:
            gamesout.close()
        return True
    else:
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
        rr = chessrecord.ChessDBrecordRepertoire()
        rr.set_database(database)
        gamesout = open(filename, "w")
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, b[0]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    gamesout.write(
                        rr.value.collected_game.get_repertoire_pgn_no_comments()
                    )
            gamesout = open(filename, "w")
        finally:
            gamesout.close()
        return
    else:
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
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    games = []
    all_games_output = True
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.REPERTOIRE_FILE_DEF, b[0 if primary else 1]
                )
            )
            if rr.value.collected_game.is_pgn_valid_export_format():
                games.append(
                    get_game_pgn_import_format(rr.value.collected_game)
                )
            else:
                all_games_output = False
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(rr.value.collected_game)
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, r[0 if primary else 1]
                    )
                )
                if rr.value.collected_game.is_pgn_valid_export_format():
                    games.append(
                        get_game_pgn_import_format(rr.value.collected_game)
                    )
                else:
                    all_games_output = False
                r = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in games:
            gamesout.write(g)
            gamesout.write("\n\n")
    finally:
        gamesout.close()
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
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    games = []
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(
                    filespec.REPERTOIRE_FILE_DEF, b[0 if primary else 1]
                )
            )
            games.append(rr.get_srvalue())
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial)
                )
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, r[0 if primary else 1]
                    )
                )
                games.append(rr.get_srvalue())
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            r = cursor.first()
            while True:
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, r[0 if primary else 1]
                    )
                )
                games.append(rr.get_srvalue())
                r = cursor.next()
        finally:
            cursor.close()
    if len(games) == 0:
        return None
    gamesout = open(filename, "w")
    try:
        for g in games:
            gamesout.write(g)
            gamesout.write("\n")
    finally:
        gamesout.close()
    return True


def export_selected_positions(grid, filename):
    """Export CQL statements in grid to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordPartial()
        rr.set_database(database)
        gamesout = open(filename, "w")
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.PARTIAL_FILE_DEF, b[0]
                    )
                )
                gamesout.write(rr.get_srvalue())
                gamesout.write("\n")
            gamesout = open(filename, "w")
        finally:
            gamesout.close()
        return
    else:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordPartial()
        rr.set_database(database)
        gamesout = open(filename, "w")
        cursor = database.database_cursor(
            filespec.PARTIAL_FILE_DEF, filespec.PARTIAL_FILE_DEF
        )
        try:
            r = cursor.first()
            while r:
                rr.load_record(r)
                gamesout.write(rr.get_srvalue())
                gamesout.write("\n")
                r = cursor.next()
        finally:
            cursor.close()
            gamesout.close()
        return


def export_selected_selection_rules(grid, filename):
    """Export selected selection rule statements to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordQuery()
        rr.set_database(database)
        gamesout = open(filename, "w")
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.SELECTION_FILE_DEF, b[0]
                    )
                )
                gamesout.write(rr.get_srvalue())
                gamesout.write("\n")
            gamesout = open(filename, "w")
        finally:
            gamesout.close()
        return
    else:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordQuery()
        rr.set_database(database)
        gamesout = open(filename, "w")
        cursor = database.database_cursor(
            filespec.SELECTION_FILE_DEF, filespec.SELECTION_FILE_DEF
        )
        try:
            r = cursor.first()
            while r:
                rr.load_record(r)
                gamesout.write(rr.get_srvalue())
                gamesout.write("\n")
                r = cursor.next()
        finally:
            cursor.close()
            gamesout.close()
        return


def export_single_game_pgn_reduced_export_format(collected_game, filename):
    """Export collected_game to PGN file in reduced export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_archive_movetext())
        gamesout.write("\n\n")
    finally:
        gamesout.close()


def export_single_game_pgn(collected_game, filename):
    """Export collected_game to filename in PGN export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_all_movetext_in_pgn_export_format())
        gamesout.write("\n\n")
    finally:
        gamesout.close()


def export_single_game_pgn_no_comments_no_ravs(collected_game, filename):
    """Export collected_game to filename in PGN export format without comments
    or RAVs.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_archive_movetext())
        gamesout.write("\n\n")
    finally:
        gamesout.close()
    return True


def export_single_game_pgn_no_comments(collected_game, filename):
    """Export collected_game to filename in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(
            collected_game.get_movetext_without_comments_in_pgn_export_format()
        )
        gamesout.write("\n\n")
    finally:
        gamesout.close()
    return True


def export_single_game_pgn_import_format(collected_game, filename):
    """Export collected_game to pgn file in a PGN import format."""
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(get_game_pgn_import_format(collected_game))
    finally:
        gamesout.close()


def export_single_game_text(collected_game, filename):
    """Export collected_game to text file in internal format."""
    if filename is None:
        return
    internal_format = next(PGN().read_games(collected_game.get_text_of_game()))
    gamesout = open(filename, "w")
    try:
        gamesout.write(internal_format.get_text_of_game())
        gamesout.write("\n")
    finally:
        gamesout.close()


def export_single_repertoire_pgn(collected_game, filename):
    """Export repertoire in import format PGN to *.pgn file.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(collected_game.get_repertoire_pgn())
    finally:
        gamesout.close()


def export_single_repertoire_pgn_no_comments(collected_game, filename):
    """Export repertoire in PGN export format without comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(collected_game.get_repertoire_pgn_no_comments())
    finally:
        gamesout.close()


def export_single_position(partialposition, filename):
    """Export CQL statement to textfile."""
    if filename is None:
        return
    sp = CQLStatement()
    sp.process_statement(partialposition)
    if not sp.is_statement():
        return
    gamesout = open(filename, "w")
    try:
        gamesout.write(sp.get_name_position_text())
    finally:
        gamesout.close()


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
    for t in collected_game.get_tags(
        name_value_separator=name_value_separator
    ):
        length = _add_token_to_text(
            t, text, line_length, tag_separator, length
        )
    text.append(block_separator)
    length = len(block_separator.split("\n")[-1])
    for t in collected_game.get_movetext():
        if t.startswith("{"):
            s = t.split()
            length = _add_token_to_text(
                s.pop(0), text, line_length, movetext_separator, length
            )
            for w in s:
                length = _add_token_to_text(w, text, line_length, " ", length)
        elif t.startswith("$"):
            length = _add_token_to_text(
                t, text, line_length, movetext_separator, length
            )
        elif t.startswith(";"):
            if len(t) + length >= line_length:
                text.append("\n")
            else:
                text.append(movetext_separator)
            text.append(t)
            length = 0
        elif t == "(":
            length = _add_token_to_text(
                t, text, line_length, movetext_separator, length
            )
        elif t == ")":
            length = _add_token_to_text(
                t, text, line_length, movetext_separator, length
            )
        else:
            length = _add_token_to_text(
                t, text, line_length, movetext_separator, length
            )
    text.append(block_separator)
    return "".join(text)


# Derived from _add_token_to_movetext method in pgn_read.core.game module.
def _add_token_to_text(token, text, line_length, token_separator, length):
    if not length:
        text.append(token)
        return len(token)
    elif len(token) + length >= line_length:
        text.append("\n")
        text.append(token)
        return len(token)
    else:
        text.append(token_separator)
        text.append(token)
        return len(token) + length + len(token_separator)
