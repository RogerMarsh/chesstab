# export_game.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess game exporters."""

import ast

from pgn_read.core.parser import PGN

from . import chessrecord, filespec, lexer, pgnify, cqlpgnify
from .export_pgn_import_format import get_game_pgn_import_format

# PGN specification states ascii but these export functions used the
# default encoding before introduction of _ENCODING attribute.
# PGN files were read as "iso-8859-1" encoding when _ENCODING attribute
# was introduced.
# _ENCODING = "ascii"
# _ENCODING = "iso-8859-1"
_ENCODING = "utf-8"


def export_all_games_text(database, filename):
    """Export games in database to text file in internal record format."""
    if filename is None:
        return True
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    database.start_read_only_transaction()
    try:
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
                    current_record = cursor.next()
        finally:
            cursor.close()
    finally:
        database.end_read_only_transaction()
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
    database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
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
                        games_for_date.append(ivcg.get_export_pgn_elements())
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
    finally:
        database.end_read_only_transaction()
    return all_games_output


def export_all_games_pgn_import_format(database, filename):
    """Export all database games in a PGN inport format."""
    if filename is None:
        return True
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    database.start_read_only_transaction()
    try:
        export_format = database.recordlist_ebm(filespec.GAMES_FILE_DEF)
        count = export_format.count_records()
        all_games_output = bool(count > 0)
        export_format.remove_recordset(
            database.recordlist_all(
                filespec.GAMES_FILE_DEF, filespec.PGN_ERROR_FIELD_DEF
            )
        )
        if all_games_output and count != export_format.count_records():
            all_games_output = False
        cursor = export_format.create_recordsetbase_cursor()
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                pgnifier = pgnify.PGNify(gamesout)
                tokenizer = lexer.Lexer(pgnifier)
                pgnifier.set_lexer(tokenizer)
                current_record = cursor.first()
                while current_record:
                    try:
                        instance.load_record(current_record)
                    except StopIteration:
                        break
                    tokenizer.generate_tokens(
                        literal_eval(instance.get_srvalue()[0])
                    )
                    current_record = cursor.next()
        finally:
            cursor.close()
    finally:
        database.end_read_only_transaction()
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
    database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
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
                        games_for_date.append(
                            ivcg.get_export_pgn_rav_elements()
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
    finally:
        database.end_read_only_transaction()
    return all_games_output


def export_all_games_pgn_no_structured_comments(database, filename):
    """Export database games in PGN export format without {[%]} comments."""
    if filename is None:
        return True
    instance = chessrecord.ChessDBrecordGame()
    instance.set_database(database)
    all_games_output = None
    no_games_output = True
    games_for_date = []
    prev_date = None
    database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
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
                        games_for_date.append(
                            ivcg.get_export_pgn_rav_no_structured_comments()
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
    finally:
        database.end_read_only_transaction()
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
    database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
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
                        games_for_date.append(
                            (
                                collected_game.get_seven_tag_roster_tags(),
                                collected_game.get_archive_movetext(),
                                collected_game.get_non_seven_tag_roster_tags(),
                            )
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
    finally:
        database.end_read_only_transaction()
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
    database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.PGN_DATE_FIELD_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
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
    finally:
        database.end_read_only_transaction()
    return all_games_output


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
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    database.start_read_only_transaction()
    try:
        export_format = database.recordlist_ebm(filespec.GAMES_FILE_DEF)
        export_format.remove_recordset(
            database.recordlist_all(
                filespec.GAMES_FILE_DEF, filespec.PGN_ERROR_FIELD_DEF
            )
        )
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            pgnifier = pgnify.PGNify(gamesout)
            tokenizer = lexer.Lexer(pgnifier)
            pgnifier.set_lexer(tokenizer)
            all_games_output = True
            if grid.bookmarks:
                for bookmark in grid.bookmarks:
                    record_number = bookmark[0 if primary else 1]
                    if not export_format.is_record_number_in_record_set(
                        record_number
                    ):
                        all_games_output = False
                        continue
                    instance.load_record(
                        database.get_primary_record(
                            filespec.GAMES_FILE_DEF, record_number
                        )
                    )
                    tokenizer.generate_tokens(
                        literal_eval(instance.get_srvalue()[0])
                    )
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
                        record_number = current_record[0 if primary else 1]
                        if not export_format.is_record_number_in_record_set(
                            record_number
                        ):
                            all_games_output = False
                            continue
                        instance.load_record(
                            database.get_primary_record(
                                filespec.GAMES_FILE_DEF, record_number
                            )
                        )
                        tokenizer.generate_tokens(
                            literal_eval(instance.get_srvalue()[0])
                        )
                        current_record = cursor.next()
                finally:
                    cursor.close()
            else:
                cursor = grid.get_cursor()

                # Grids except ones displayed via 'Select | Rule | List Games'
                # can have the 'current_record = cursor.next()' immediately
                # after the 'while True:' statement, making the
                # 'current_record = cursor.first()' statement is redundant.
                # I think this implies a problem in the solentware_base
                # RecordsetCursor classes for each database engine since the
                # 'finally:' clause should kill the cursor.
                # The problem is only the first request outputs all the records
                # to the file.  Subsequent requests find no records to output,
                # except that doing some scrolling action resets the cursor and
                # the next request outputs all the records before the problem
                # repeats.
                # The other methods in this class with this construct are
                # affected too, but this comment is not repeated.
                try:
                    current_record = cursor.first()
                    while True:
                        if current_record is None:
                            break
                        record_number = current_record[0 if primary else 1]
                        if not export_format.is_record_number_in_record_set(
                            record_number
                        ):
                            all_games_output = False
                            continue
                        instance.load_record(
                            database.get_primary_record(
                                filespec.GAMES_FILE_DEF, record_number
                            )
                        )
                        tokenizer.generate_tokens(
                            literal_eval(instance.get_srvalue()[0])
                        )
                        current_record = cursor.next()
                finally:
                    cursor.close()

        return all_games_output
    finally:
        database.end_read_only_transaction()


def export_selected_games_pgn(grid, filename):
    """Export selected records in PGN export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
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
                    # Fix pycodestyle E501 (83 > 79 characters).
                    # black formatting applied with line-length = 79.
                    ivcg = instance.value.collected_game
                    if ivcg.is_pgn_valid_export_format():
                        games.append(ivcg.get_export_pgn_elements())
                    else:
                        all_games_output = False
                    current_record = cursor.next()
            finally:
                cursor.close()
        else:
            cursor = grid.get_cursor()

            # For grids except ones displayed via 'Select | Rule | List Games'
            # the 'current_record = cursor.next()' can be immediately after the
            # 'while True:' statement, so the 'current_record = cursor.first()'
            # statement is redundant.
            # I think this implies a problem in the solentware_base
            # RecordsetCursor classes for each database engine since the
            # 'finally:' clause should kill the cursor.
            # The problem is only the first request outputs all the records
            # to the file.  Subsequent requests find no records to output,
            # except that doing some scrolling action resets the cursor and
            # the next request outputs all the records before the problem
            # repeats.
            # The other methods in this class with this construct are affected
            # too, but this comment is not repeated.
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
                        games.append(ivcg.get_export_pgn_elements())
                    else:
                        all_games_output = False
                    current_record = cursor.next()
            finally:
                cursor.close()

        if len(games) == 0:
            return None
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for game in sorted(games):
                gamesout.write(game[0])
                gamesout.write("\n")
                gamesout.write(game[2])
                gamesout.write("\n")
                gamesout.write(game[1])
                gamesout.write("\n\n")
        return all_games_output
    finally:
        database.end_read_only_transaction()


def export_selected_games_pgn_no_comments(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
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
                # Fix pycodestyle E501 (83 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(ivcg.get_export_pgn_rav_elements())
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
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for game in sorted(games):
                gamesout.write(game[0])
                gamesout.write("\n")
                gamesout.write(game[2])
                gamesout.write("\n")
                gamesout.write(game[1])
                gamesout.write("\n\n")
        return all_games_output
    finally:
        database.end_read_only_transaction()


def export_selected_games_pgn_no_structured_comments(grid, filename):
    """Export selected records in export format excluding {[%]} comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
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
                # Fix pycodestyle E501 (83 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(
                        ivcg.get_export_pgn_rav_no_structured_comments()
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
                        games.append(
                            ivcg.get_export_pgn_rav_no_structured_comments()
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
                            filespec.GAMES_FILE_DEF,
                            current_record[0 if primary else 1],
                        )
                    )
                    # Fix pycodestyle E501 (83 > 79 characters).
                    # black formatting applied with line-length = 79.
                    ivcg = instance.value.collected_game
                    if ivcg.is_pgn_valid_export_format():
                        games.append(
                            ivcg.get_export_pgn_rav_no_structured_comments()
                        )
                    else:
                        all_games_output = False
                    current_record = cursor.next()
            finally:
                cursor.close()
        if len(games) == 0:
            return None
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for game in sorted(games):
                gamesout.write(game[0])
                gamesout.write("\n")
                gamesout.write(game[2])
                gamesout.write("\n")
                gamesout.write(game[1])
                gamesout.write("\n\n")
        return all_games_output
    finally:
        database.end_read_only_transaction()


def export_selected_games_pgn_no_comments_no_ravs(grid, filename):
    """Export selected records in PGN export format excluding comments.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
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
                    games.append(
                        (
                            collected_game.get_seven_tag_roster_tags(),
                            collected_game.get_archive_movetext(),
                            collected_game.get_non_seven_tag_roster_tags(),
                        )
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
                    collected_game = instance.value.collected_game
                    if collected_game.is_pgn_valid_export_format():
                        games.append(
                            (
                                collected_game.get_seven_tag_roster_tags(),
                                collected_game.get_archive_movetext(),
                                collected_game.get_non_seven_tag_roster_tags(),
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
                            filespec.GAMES_FILE_DEF,
                            current_record[0 if primary else 1],
                        )
                    )
                    collected_game = instance.value.collected_game
                    if collected_game.is_pgn_valid_export_format():
                        strt = collected_game.get_seven_tag_roster_tags()
                        nstrt = collected_game.get_non_seven_tag_roster_tags()
                        archive_movetext = (
                            collected_game.get_archive_movetext()
                        )
                        games.append((strt, archive_movetext, nstrt))
                    else:
                        all_games_output = False
                    current_record = cursor.next()
            finally:
                cursor.close()
        if len(games) == 0:
            return None
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for game in sorted(games):
                gamesout.write(game[0])
                gamesout.write("\n")
                gamesout.write(game[2])
                gamesout.write("\n")
                gamesout.write(game[1])
                gamesout.write("\n\n")
        return all_games_output
    finally:
        database.end_read_only_transaction()


def export_selected_games_pgn_reduced_export_format(grid, filename):
    """Export selected records in grid to PGN file in reduced export format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
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
                # Fix pycodestyle E501 (83 > 79 characters).
                # black formatting applied with line-length = 79.
                ivcg = instance.value.collected_game
                if ivcg.is_pgn_valid_export_format():
                    games.append(ivcg.get_archive_pgn_elements())
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
        with open(filename, "w", encoding=_ENCODING) as gamesout:
            for game in sorted(games):
                gamesout.write(game[0])
                gamesout.write("\n")
                gamesout.write(game[1])
                gamesout.write("\n\n")
        return all_games_output
    finally:
        database.end_read_only_transaction()


def export_selected_games_text(grid, filename):
    """Export selected records in grid to text file in internal record format.

    If any records are bookmarked just the bookmarked records are exported,
    otherwise all records selected for display in the grid are exported.

    """
    if filename is None:
        return True
    literal_eval = ast.literal_eval
    database = grid.get_data_source().dbhome
    database.start_read_only_transaction()
    try:
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
                games.append(literal_eval(instance.get_srvalue()[0]))
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
                    games.append(literal_eval(instance.get_srvalue()[0]))
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
                    games.append(literal_eval(instance.get_srvalue()[0]))
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
    finally:
        database.end_read_only_transaction()


def export_single_game_pgn_reduced_export_format(collected_game, filename):
    """Export collected_game to PGN file in reduced export format.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
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
    with open(filename, "w", encoding=_ENCODING) as gamesout:
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
    with open(filename, "w", encoding=_ENCODING) as gamesout:
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
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(
            collected_game.get_movetext_without_comments_in_pgn_export_format()
        )
        gamesout.write("\n\n")
    return True


def export_single_game_pgn_no_structured_comments(collected_game, filename):
    """Export collected_game to filename without {[%]} comments.

    Caller should test is_pgn_valid_export_format before picking filename.

    """
    if filename is None:
        return None
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(collected_game.get_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(collected_game.get_non_seven_tag_roster_tags())
        gamesout.write("\n")
        gamesout.write(
            collected_game.get_export_movetext_without_structured_comments()
        )
        gamesout.write("\n\n")
    return True


def export_single_game_pgn_import_format(collected_game, filename):
    """Export collected_game to pgn file in a PGN import format."""
    if filename is None:
        return
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(get_game_pgn_import_format(collected_game))


def export_single_game_text(collected_game, filename):
    """Export collected_game to text file in internal format."""
    if filename is None:
        return
    internal_format = next(PGN().read_games(collected_game.get_text_of_game()))
    with open(filename, "w", encoding=_ENCODING) as gamesout:
        gamesout.write(internal_format.get_text_of_game())
        gamesout.write("\n")


def export_all_games_for_cql_scan(database, filename):
    """Export all database games in a PGN inport format for CQL scan."""
    if filename is None:
        return True
    literal_eval = ast.literal_eval
    instance = chessrecord.ChessDBrecordGameText()
    instance.set_database(database)
    database.start_read_only_transaction()
    try:
        cursor = database.database_cursor(
            filespec.GAMES_FILE_DEF, filespec.GAMES_FILE_DEF
        )
        try:
            with open(filename, "w", encoding=_ENCODING) as gamesout:
                pgnifier = cqlpgnify.CQLPGNify(gamesout)
                tokenizer = lexer.Lexer(pgnifier)
                pgnifier.set_lexer(tokenizer)
                current_record = cursor.first()
                while current_record:
                    instance.load_record(current_record)
                    tokenizer.generate_tokens(
                        literal_eval(instance.get_srvalue()[0])
                    )
                    current_record = cursor.next()
        finally:
            cursor.close()
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
