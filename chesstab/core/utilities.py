# utilities.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide functions which do not fit easily elsewhere.

is_game_import_in_progress
is_game_import_in_progress_txn
is_import_in_progress
is_import_in_progress_txn
is_import_without_index_reload_in_progress
is_import_without_index_reload_in_progress_txn
is_import_with_index_reload_started
is_import_with_index_reload_started_txn

Game imports can be interrupted with stages of the import process not
completed for some, or all, games.  The edit and delete actions should not
be done on these games, while they can proceed for the other games.

The *_txn version of each exists in case the test is done within an existing
transaction.

"""
from ..core import filespec
from ..core import constants


def is_game_import_in_progress(database, game):
    """Return True if some stages of game import to database are not done.

    database    Database instance containing the game.
    game        Record of game extracted from database.

    """
    if database is None:
        return False
    if game is None:
        return False
    if is_import_with_index_reload_started(database):
        return True
    return bool(
        (
            database.recordlist_record_number(
                filespec.GAMES_FILE_DEF, key=game.key.recno
            )
            & database.recordlist_all(
                filespec.GAMES_FILE_DEF, filespec.IMPORT_FIELD_DEF
            )
        ).count_records()
    )


def is_game_import_in_progress_txn(database, game):
    """Return return value of is_game_import_in_progress() call.

    database    Database instance containing the game.
    game        Record of game extracted from database.

    """
    if database is None:
        return False
    if game is None:
        return False
    database.start_read_only_transaction()
    try:
        return is_game_import_in_progress(database, game)
    finally:
        database.end_read_only_transaction()


def is_import_in_progress(database):
    """Return True if some stages of an import to database are not done.

    database    Database instance containing the game.

    """
    if database is None:
        return False
    return bool(
        database.recordlist_all(
            filespec.GAMES_FILE_DEF, filespec.IMPORT_FIELD_DEF
        ).count_records()
    )


def is_import_in_progress_txn(database):
    """Return return value of is_import_in_progress() call.

    database    Database instance containing the game.

    """
    if database is None:
        return False
    database.start_read_only_transaction()
    try:
        return is_import_in_progress(database)
    finally:
        database.end_read_only_transaction()


def get_pgn_filenames_of_an_import_in_progress(database):
    """Return file name of first game with incomplete import.

    database    Database instance containing the game.

    """
    if database is None:
        return ()
    return database.get_application_control().get(constants.PGN_FILES, ())


def get_pgn_filenames_of_an_import_in_progress_txn(database):
    """Return file names of PGN files for incomplete import.

    database    Database instance containing the game.

    """
    if database is None:
        return ()
    database.start_read_only_transaction()
    try:
        return get_pgn_filenames_of_an_import_in_progress(database)
    finally:
        database.end_read_only_transaction()


# Written before conventional meaning of filespec.GAME_FIELD_DEF added.
# See is_import_without_index_reload_in_progress.
def is_import_without_index_reload_in_progress(database):
    """Return True if some stages of an import to database are not done.

    database    Database instance containing the game.

    """
    if database is None:
        return False
    for index in (
        filespec.POSITIONS_FIELD_DEF,
        filespec.PIECESQUARE_FIELD_DEF,
    ):
        index_games = database.recordlist_key(
            filespec.GAMES_FILE_DEF,
            filespec.IMPORT_FIELD_DEF,
            key=database.encode_record_selector(index),
        )
        try:
            if index_games.count_records():
                return True
        finally:
            index_games.close()
    return False


def is_import_without_index_reload_in_progress_txn(database):
    """Return result of is_import_without_index_reload_in_progress() call.

    database    Database instance containing the game.

    """
    if database is None:
        return False
    database.start_read_only_transaction()
    try:
        return is_import_without_index_reload_in_progress(database)
    finally:
        database.end_read_only_transaction()


def is_import_with_index_reload_started(database):
    """Return True if stages of index import to database are started.

    database    Database instance containing the game.

    """
    if database is None:
        return False
    index_games = database.recordlist_key(
        filespec.GAMES_FILE_DEF,
        filespec.IMPORT_FIELD_DEF,
        key=database.encode_record_selector(filespec.GAME_FIELD_DEF),
    )
    try:
        if index_games.count_records():
            return True
    finally:
        index_games.close()
    return False


def is_import_with_index_reload_started_txn(database):
    """Return True if stages of index import to database are started.

    database    Database instance containing the game.

    """
    if database is None:
        return False
    database.start_read_only_transaction()
    try:
        return is_import_with_index_reload_started(database)
    finally:
        database.end_read_only_transaction()


def bytesize_to_str(number):
    """Return number as Gigabytes, Megabytes, Kilobytes, or bytes, string."""
    if number > 1073741823:
        return str(divmod(number, 1073741824)[0]) + " Gigabytes"
    if number > 1048575:
        return str(divmod(number, 1048576)[0]) + " Megabytes"
    if number > 1023:
        return str(divmod(number, 1024)[0]) + " Kilobytes"
    return str(number) + " bytes"
