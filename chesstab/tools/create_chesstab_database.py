# create_chesstab_database.py
# Copyright 2020 Roger Marsh
# Licence: See LICENSE.txt (BSD licence)

"""Create empty ChessTab database with chosen database engine and segment size.
"""

from solentware_base.tools import create_database

try:
    from ..unqlite import chessunqlite
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessunqlite = None
try:
    from ..vedis import chessvedis
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessvedis = None
if create_database._deny_sqlite3:
    chesssqlite3 = None
else:
    try:
        from ..sqlite import chesssqlite3
    except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
        chesssqlite3 = None
try:
    from ..apsw import chessapsw
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessapsw = None
try:
    from ..berkeleydb import chessberkeleydb
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessberkeleydb = None
try:
    from ..db import chessdb
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessdb = None
try:
    from ..dpt import chessdpt
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessdpt = None
try:
    from ..ndbm import chessndbm
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessndbm = None
try:
    from ..gnu import chessgnu
except ImportError:  # Not ModuleNotFoundError for Pythons earlier than 3.6
    chessgnu = None


class CreateChessTabDatabase(create_database.CreateDatabase):
    """Create a ChessTab database."""

    _START_TEXT = "".join(
        (
            "ChessTab would create a new database with the top-left engine, ",
            "and segment size 4000.",
        )
    )

    def __init__(self):
        """Build the user interface."""
        engines = {}
        if chessunqlite:
            engines[
                chessunqlite.unqlite_database.unqlite
            ] = chessunqlite.ChessDatabase
        if chessvedis:
            engines[chessvedis.vedis_database.vedis] = chessvedis.ChessDatabase
        if chesssqlite3:
            engines[
                chesssqlite3.sqlite3_database.sqlite3
            ] = chesssqlite3.ChessDatabase
        if chessapsw:
            engines[chessapsw.apsw_database.apsw] = chessapsw.ChessDatabase
        if chessdb:
            engines[chessdb.bsddb3_database.bsddb3] = chessdb.ChessDatabase
        if chessberkeleydb:
            engines[
                chessberkeleydb.berkeleydb_database.berkeleydb
            ] = chessberkeleydb.ChessDatabase
        if chessdpt:
            engines[chessdpt.dpt_database._dpt.dptapi] = chessdpt.ChessDatabase
        if chessndbm:
            engines[
                chessndbm.ndbm_database.ndbm_module.dbm.ndbm
            ] = chessndbm.ChessDatabase
        if chessgnu:
            engines[
                chessgnu.gnu_database.gnu_module.dbm.gnu
            ] = chessgnu.ChessDatabase
        super().__init__(title="Create ChessTab Database", engines=engines)


if __name__ == "__main__":

    CreateChessTabDatabase().root.mainloop()
