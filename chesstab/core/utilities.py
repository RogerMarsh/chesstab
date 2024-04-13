# utilities.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide functions which do not fit easily elsewhere.

is_game_import_in_progress
is_game_import_in_progress_txn

Game imports can be interrupted with stages of the import process not
completed for some, or all, games.  The edit and delete actions should not
be done on these games, while they can proceed for the other games.

Two methods in case the test is done within an existing transaction.

"""
from ..core import filespec


def is_game_import_in_progress(database, game):
    """Return True if some stages of game import to database are not done.

    database    Database instance containg the game.
    game        Record of game extracted from database.

    """
    return bool(
        (
            database.recordlist_record_number(
                filespec.GAMES_FILE_DEF, key=game.key.recno
            ) & database.recordlist_all(
                filespec.GAMES_FILE_DEF, filespec.IMPORT_FIELD_DEF
            )
        ).count_records()
    )


def is_game_import_in_progress_txn(database, game):
    """Return return value of is_game_import_in_progress() call.

    database    Database instance containg the game.
    game        Record of game extracted from database.

    """
    database.start_read_only_transaction()
    try:
        return is_game_import_in_progress(database, game)
    finally:
        database.end_read_only_transaction()
