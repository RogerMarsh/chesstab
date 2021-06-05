# chessdptdumulti.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using DPT multi-step deferred update.

This module on Windows and Wine only.  This module must be used on Wine rather
than single-step because Wine support for a critical function used by
single-step is not reliable.  Multi-step takes much longer than single-step
so use of this module is not recommended on Windows.

See www.dptoolkit.com for details of DPT

"""

from dptdb.dptapi import (
    FILEDISP_OLD,
    FISTAT_DEFERRED_UPDATES,
    APIContextSpecification,
)

from solentware_base.dptdumultiapi import DPTdumultiapi

from .chessdptdu import ChessDatabaseDeferred
from ..core.chessrecord import ChessDBrecordGameImport
from ..core.filespec import GAMES_FILE_DEF


def chess_dptdu_multi(
    dbpath, pgnpaths, file_records, reporter=lambda text, timestamp=True: None
):
    """Open database, import games and close database."""
    cdb = ChessDatabase(
        dbpath, allowcreate=True, deferupdatefiles={GAMES_FILE_DEF}
    )
    importer = ChessDBrecordGameImport()
    records = file_records
    for pp in pgnpaths:
        if cdb.open_database(files=records) is True:
            s = open(pp, "r", encoding="iso-8859-1")
            importer.import_pgn(cdb, s, pp, reporter=reporter)
            s.close()
            cdb.do_deferred_updates()
        cdb.close_database()
        records = None
    if reporter is not None:
        reporter("Finishing import: please wait.")
        reporter("", timestamp=False)
    cdb.open_database_contexts(files=file_records)
    status = True
    for f in file_records:
        if (
            0
            != cdb.get_database_instance(f, None).get_file_parameters(
                cdb.dbenv
            )["FISTAT"][0]
        ):
            status = False
    cdb.close_database()
    return status


class ChessDatabase(ChessDatabaseDeferred, DPTdumultiapi):

    """Provide multi-step deferred update for a database of games of chess."""
