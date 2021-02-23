# exporters.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess game, repertoire, and partial position exporters.
"""

import os

from pgn_read.core.parser import PGN

from .pgn import GameDisplayMoves, GameRepertoireDisplayMoves
from . import chessrecord, filespec
from .cqlstatement import CQLStatement


def export_games_as_text(database, filename):
    """Export games in database to text file in internal record format."""
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGameText()
    rr.set_database(database)
    gamesout = open(filename, 'w', encoding='iso-8859-1')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF)
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            a = rr.get_srvalue()
            gamesout.write(rr.get_srvalue())
            gamesout.write('\n')
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()


def export_games_as_pgn(database, filename):
    """Export games in database to PGN file in export format including
    comments but excluding recursive annotation variations.

    """
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games_for_date = []
    prev_date = None
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF)
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write('\n')
                    gamesout.write(gfd[2])
                    gamesout.write('\n')
                    gamesout.write(gfd[1])
                    gamesout.write('\n\n')
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid():
                games_for_date.append(
                    rr.value.collected_game.get_export_pgn_elements())
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write('\n')
            gamesout.write(gfd[2])
            gamesout.write('\n')
            gamesout.write(gfd[1])
            gamesout.write('\n\n')
    finally:
        cursor.close()
        gamesout.close()


def export_games_as_rav_pgn(database, filename):
    """Export games in database to PGN file in export format including
    recursive annotation variations.

    """
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games_for_date = []
    prev_date = None
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF)
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write('\n')
                    gamesout.write(gfd[2])
                    gamesout.write('\n')
                    gamesout.write(gfd[1])
                    gamesout.write('\n\n')
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid():
                games_for_date.append(
                    rr.value.collected_game.get_export_pgn_rav_elements())
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write('\n')
            gamesout.write(gfd[2])
            gamesout.write('\n')
            gamesout.write(gfd[1])
            gamesout.write('\n\n')
    finally:
        cursor.close()
        gamesout.close()


def export_games_as_archive_pgn(database, filename):
    """Export games in database to PGN file in reduced export format."""
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games_for_date = []
    prev_date = None
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF)
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write('\n')
                    gamesout.write(gfd[1])
                    gamesout.write('\n\n')
                prev_date = r[0]
                games_for_date = []
            g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
            try:
                rr.load_record(g)
            except StopIteration:
                break
            if rr.value.collected_game.is_pgn_valid():
                games_for_date.append(
                    rr.value.collected_game.get_archive_pgn_elements())
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write('\n')
            gamesout.write(gfd[1])
            gamesout.write('\n\n')
    finally:
        cursor.close()
        gamesout.close()


def export_repertoires_as_pgn(database, filename):
    """Export repertoires in database to PGN file in export format including
    comments but excluding recursive annotation variations.

    """
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF)
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            if rr.value.collected_game.is_pgn_valid():
                gamesout.write(
                    rr.value.collected_game.get_export_repertoire_text())
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()


def export_repertoires_as_rav_pgn(database, filename):
    """Export repertoires in database to PGN file in export format including
    recursive annotation variations.

    """
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordRepertoire()
    rr.set_database(database)
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF)
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            if rr.value.collected_game.is_pgn_valid():
                gamesout.write(
                    rr.value.collected_game.get_export_repertoire_rav_text())
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()


def export_repertoires_as_text(database, filename):
    """Export repertoires in database to text file in internal record format."""
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGameText()
    rr.set_database(database)
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.REPERTOIRE_FILE_DEF, filespec.REPERTOIRE_FILE_DEF)
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            gamesout.write(rr.get_srvalue())
            gamesout.write('\n')
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()


def export_positions(database, filename):
    """Export CQL statements in database to text file in internal record
    format.

    """
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordPartial()
    rr.set_database(database)
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.PARTIAL_FILE_DEF, filespec.PARTIAL_FILE_DEF)
    try:
        r = cursor.first()
        while r:
            rr.load_record(r)
            gamesout.write(rr.get_srvalue())
            gamesout.write('\n')
            r = cursor.next()
    finally:
        cursor.close()
        gamesout.close()


def export_grid_games_as_pgn(grid, filename):
    """Export selected records in grid to PGN file in export format including
    comments but excluding recursive annotation variations.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname)
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(filespec.GAMES_FILE_DEF,
                                            b[0 if primary else 1]))
            if rr.value.collected_game.is_pgn_valid():
                games.append(rr.value.collected_game.get_export_pgn_elements())
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial))
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(filespec.GAMES_FILE_DEF,
                                                r[0 if primary else 1]))
                if rr.value.collected_game.is_pgn_valid():
                    games.append(
                        rr.value.collected_game.get_export_pgn_elements())
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            while True:
                r = cursor.next()
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(filespec.GAMES_FILE_DEF,
                                                r[0 if primary else 1]))
                if rr.value.collected_game.is_pgn_valid():
                    games.append(
                        rr.value.collected_game.get_export_pgn_elements())
        finally:
            cursor.close()
    gamesout = open(filename, 'w')
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write('\n')
            gamesout.write(g[2])
            gamesout.write('\n')
            gamesout.write(g[1])
            gamesout.write('\n\n')
    finally:
        gamesout.close()
    return


def export_grid_games_as_rav_pgn(grid, filename):
    """Export selected records in grid to PGN file in export format including
    recursive annotation variations.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname)
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(filespec.GAMES_FILE_DEF,
                                            b[0 if primary else 1]))
            if rr.value.collected_game.is_pgn_valid():
                games.append(
                    rr.value.collected_game.get_export_pgn_rav_elements())
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial))
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(filespec.GAMES_FILE_DEF,
                                                r[0 if primary else 1]))
                if rr.value.collected_game.is_pgn_valid():
                    games.append(
                        rr.value.collected_game.get_export_pgn_rav_elements())
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            while True:
                r = cursor.next()
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(filespec.GAMES_FILE_DEF,
                                                r[0 if primary else 1]))
                if rr.value.collected_game.is_pgn_valid():
                    games.append(
                        rr.value.collected_game.get_export_pgn_rav_elements())
        finally:
            cursor.close()
    gamesout = open(filename, 'w')
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write('\n')
            gamesout.write(g[2])
            gamesout.write('\n')
            gamesout.write(g[1])
            gamesout.write('\n\n')
    finally:
        gamesout.close()
    return


def export_grid_games_as_archive_pgn(grid, filename):
    """Export selected records in grid to PGN file in reduced export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    database = grid.get_data_source().dbhome
    primary = database.is_primary(
        grid.get_data_source().dbset, grid.get_data_source().dbname)
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games = []
    if grid.bookmarks:
        for b in grid.bookmarks:
            rr.load_record(
                database.get_primary_record(filespec.GAMES_FILE_DEF,
                                            b[0 if primary else 1]))
            if rr.value.collected_game.is_pgn_valid():
                games.append(rr.value.collected_game.get_archive_pgn_elements())
    elif grid.partial:
        cursor = grid.get_cursor()
        try:
            if primary:
                r = cursor.first()
            else:
                r = cursor.nearest(
                    database.encode_record_selector(grid.partial))
            while r:
                if not primary:
                    if not r[0].startswith(grid.partial):
                        break
                rr.load_record(
                    database.get_primary_record(filespec.GAMES_FILE_DEF,
                                                r[0 if primary else 1]))
                if rr.value.collected_game.is_pgn_valid():
                    games.append(
                        rr.value.collected_game.get_archive_pgn_elements())
                r = cursor.next()
        finally:
            cursor.close()
    else:
        cursor = grid.get_cursor()
        try:
            while True:
                r = cursor.next()
                if r is None:
                    break
                rr.load_record(
                    database.get_primary_record(filespec.GAMES_FILE_DEF,
                                                r[0 if primary else 1]))
                if rr.value.collected_game.is_pgn_valid():
                    games.append(
                        rr.value.collected_game.get_archive_pgn_elements())
        finally:
            cursor.close()
    gamesout = open(filename, 'w')
    try:
        for g in sorted(games):
            gamesout.write(g[0])
            gamesout.write('\n')
            gamesout.write(g[1])
            gamesout.write('\n\n')
    finally:
        gamesout.close()
    return


def export_grid_repertoires_as_pgn(grid, filename):
    """Export selected records in grid to PGN file in export format including
    comments but excluding recursive annotation variations.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordRepertoire()
        rr.set_database(database)
        gamesout = open(filename, 'w')
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, b[0]))
                if rr.value.collected_game.is_pgn_valid():
                    gamesout.write(
                        rr.value.collected_game.get_export_repertoire_text())
            gamesout = open(filename, 'w')
        finally:
            gamesout.close()
        return
    else:
        export_repertoires_as_pgn(grid.get_data_source().dbhome, filename)
        return


def export_grid_repertoires_as_rav_pgn(grid, filename):
    """Export selected records in grid to PGN file in export format including
    recursive annotation variations.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordRepertoire()
        rr.set_database(database)
        gamesout = open(filename, 'w')
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.REPERTOIRE_FILE_DEF, b[0]))
                if rr.value.collected_game.is_pgn_valid():
                    gamesout.write(
                        rr.value.collected_game.get_export_repertoire_rav_text(
                            ))
            gamesout = open(filename, 'w')
        finally:
            gamesout.close()
        return
    else:
        export_repertoires_as_rav_pgn(grid.get_data_source().dbhome, filename)
        return


def export_grid_positions(grid, filename):
    """Export CQL statements in grid to textfile."""
    if filename is None:
        return
    if grid.bookmarks:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordPartial()
        rr.set_database(database)
        gamesout = open(filename, 'w')
        try:
            for b in sorted(grid.bookmarks):
                rr.load_record(
                    database.get_primary_record(
                        filespec.PARTIAL_FILE_DEF, b[0]))
                gamesout.write(rr.get_srvalue())
                gamesout.write('\n')
            gamesout = open(filename, 'w')
        finally:
            gamesout.close()
        return
    else:
        database = grid.get_data_source().dbhome
        rr = chessrecord.ChessDBrecordPartial()
        rr.set_database(database)
        gamesout = open(filename, 'w')
        cursor = database.database_cursor(
            filespec.PARTIAL_FILE_DEF, filespec.PARTIAL_FILE_DEF)
        try:
            r = cursor.first()
            while r:
                rr.load_record(r)
                gamesout.write(rr.get_srvalue())
                gamesout.write('\n')
                r = cursor.next()
        finally:
            cursor.close()
            gamesout.close()
        return


def export_partial_games_as_pgn(database, filename, partialset):
    """Export games in partialset in database to PGN file in export format
    including comments but excluding recursive annotation variations."""
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games_for_date = []
    prev_date = None
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF)
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write('\n')
                    gamesout.write(gfd[2])
                    gamesout.write('\n')
                    gamesout.write(gfd[1])
                    gamesout.write('\n\n')
                prev_date = r[0]
                games_for_date = []
            if partialset[r[1]]:
                g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
                rr.load_record(g)
                if rr.value.collected_game.is_pgn_valid():
                    games_for_date.append(
                        rr.value.collected_game.get_export_pgn_elements())
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write('\n')
            gamesout.write(gfd[2])
            gamesout.write('\n')
            gamesout.write(gfd[1])
            gamesout.write('\n\n')
    finally:
        cursor.close()
        gamesout.close()


def export_partial_games_as_rav_pgn(database, filename, partialset):
    """Export games in partialset in database to PGN file in export format
    including recursive annotation variations."""
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games_for_date = []
    prev_date = None
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF)
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write('\n')
                    gamesout.write(gfd[2])
                    gamesout.write('\n')
                    gamesout.write(gfd[1])
                    gamesout.write('\n\n')
                prev_date = r[0]
                games_for_date = []
            if partialset[r[1]]:
                g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
                rr.load_record(g)
                if rr.value.collected_game.is_pgn_valid():
                    games_for_date.append(
                        rr.value.collected_game.get_export_pgn_rav_elements())
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write('\n')
            gamesout.write(gfd[2])
            gamesout.write('\n')
            gamesout.write(gfd[1])
            gamesout.write('\n\n')
    finally:
        cursor.close()
        gamesout.close()


def export_partial_games_as_archive_pgn(database, filename, partialset):
    """Export games in partialset in database to PGN file in reduced export
    format."""
    if filename is None:
        return
    rr = chessrecord.ChessDBrecordGame()
    rr.set_database(database)
    games_for_date = []
    prev_date = None
    gamesout = open(filename, 'w')
    cursor = database.database_cursor(
        filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF)
    try:
        r = cursor.first()
        while r:
            if r[0] != prev_date:
                for gfd in sorted(games_for_date):
                    gamesout.write(gfd[0])
                    gamesout.write('\n')
                    gamesout.write(gfd[1])
                    gamesout.write('\n\n')
                prev_date = r[0]
                games_for_date = []
            if partialset[r[1]]:
                g = database.get_primary_record(filespec.GAMES_FILE_DEF, r[1])
                rr.load_record(g)
                if rr.value.collected_game.is_pgn_valid():
                    games_for_date.append(
                        rr.value.collected_game.get_archive_pgn_elements())
            r = cursor.next()
        for gfd in sorted(games_for_date):
            gamesout.write(gfd[0])
            gamesout.write('\n')
            gamesout.write(gfd[1])
            gamesout.write('\n\n')
    finally:
        cursor.close()
        gamesout.close()


def export_single_game_as_archive_pgn(game, filename):
    """Export game to PGN file in reduced export format."""
    if filename is None:
        return
    collected_game = next(PGN(game_class=GameDisplayMoves).read_games(game))
    if not collected_game.is_pgn_valid():
        return
    g = collected_game.get_archive_pgn_elements()
    gamesout = open(filename, 'w')
    try:
        gamesout.write(g[0])
        gamesout.write('\n')
        gamesout.write(g[1])
        gamesout.write('\n\n')
    finally:
        gamesout.close()


def export_single_game_as_pgn(game, filename):
    """Export game to PGN file in export format including comments but
    excluding recersive annotation variations."""
    if filename is None:
        return
    collected_game = next(PGN(game_class=GameDisplayMoves).read_games(game))
    if not collected_game.is_pgn_valid():
        return
    g = collected_game.get_export_pgn_elements()
    gamesout = open(filename, 'w')
    try:
        gamesout.write(g[0])
        gamesout.write('\n')
        gamesout.write(g[2])
        gamesout.write('\n')
        gamesout.write(g[1])
        gamesout.write('\n\n')
    finally:
        gamesout.close()


def export_single_game_as_rav_pgn(game, filename):
    """Export game to PGN file in export format including recersive annotation
    variations."""
    if filename is None:
        return
    collected_game = next(PGN(game_class=GameDisplayMoves).read_games(game))
    if not collected_game.is_pgn_valid():
        return
    g = collected_game.get_export_pgn_rav_elements()
    gamesout = open(filename, 'w')
    try:
        gamesout.write(g[0])
        gamesout.write('\n')
        gamesout.write(g[2])
        gamesout.write('\n')
        gamesout.write(g[1])
        gamesout.write('\n\n')
    finally:
        gamesout.close()


def export_single_repertoire_as_pgn(repertoire, filename):
    """Export repertoire like PGN to textfile."""
    if filename is None:
        return
    collected_game = next(
        PGN(game_class=GameRepertoireDisplayMoves).read_games(repertoire))
    if not collected_game.is_pgn_valid():
        return
    gamesout = open(filename, 'w')
    try:
        gamesout.write(collected_game.get_export_repertoire_text())
    finally:
        gamesout.close()


def export_single_repertoire_as_rav_pgn(repertoire, filename):
    """Export repertoire like RAV PGN to textfile."""
    if filename is None:
        return
    collected_game = next(
        PGN(game_class=GameRepertoireDisplayMoves).read_games(repertoire))
    if not collected_game.is_pgn_valid():
        return
    gamesout = open(filename, 'w')
    try:
        gamesout.write(collected_game.get_export_repertoire_rav_text())
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
    gamesout = open(filename, 'w')
    try:
        gamesout.write(sp.get_name_position_text())
    finally:
        gamesout.close()
