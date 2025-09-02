# __init__.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""View a database of chess games created from data in PGN format.

Run "python -m chesstab.chessgames" assuming chesstab is in site-packages and
Python3.3 or later is the system Python.

PGN is "Portable Game Notation", the standard non-proprietary format for files
of chess game scores.

Sqlite3 via the apsw or sqlite packages, Berkeley DB via the db package, or DPT
via the dpt package, can be used as the database engine.

When importing games while running under Wine it will probably be necessary to
use the module "chessgames_winedptchunk".  The only known reason to run under
Wine is to use the DPT database engine on a platform other than Microsoft
Windows.
"""

from solentware_base.core.constants import (
    BERKELEYDB_MODULE,
    BSDDB3_MODULE,
    DPT_MODULE,
    SQLITE3_MODULE,
    APSW_MODULE,
    UNQLITE_MODULE,
    VEDIS_MODULE,
    GNU_MODULE,
    NDBM_MODULE,
    DB_TCL_MODULE,
    LMDB_MODULE,
)

APPLICATION_NAME = "ChessTab"
ERROR_LOG = "ErrorLog"

# berkeleydb interface module name
_BERKELEYDBCHESS = __name__ + ".berkeleydb.database"

# bsddb3 interface module name
_DBCHESS = __name__ + ".db.database"

# DPT interface module name
_DPTCHESS = __name__ + ".dpt.database"

# sqlite3 interface module name
_SQLITE3CHESS = __name__ + ".sqlite.database"

# apsw interface module name
_APSWCHESS = __name__ + ".apsw.database"

# unqlite interface module name
_UNQLITECHESS = __name__ + ".unqlite.database"

# vedis interface module name
_VEDISCHESS = __name__ + ".vedis.database"

# dbm.gnu interface module name
_GNUCHESS = __name__ + ".gnu.database"

# dbm.ndbm interface module name
_NDBMCHESS = __name__ + ".ndbm.database"

# tkinter.tcl Berkeley DB interface module name
_DB_TCLCHESS = __name__ + ".db_tkinter.database"

# lmdb interface module name
_LMDBCHESS = __name__ + ".lmdb.database"

# Map database module names to application module
APPLICATION_DATABASE_MODULE = {
    BERKELEYDB_MODULE: _BERKELEYDBCHESS,
    BSDDB3_MODULE: _DBCHESS,
    SQLITE3_MODULE: _SQLITE3CHESS,
    APSW_MODULE: _APSWCHESS,
    DPT_MODULE: _DPTCHESS,
    UNQLITE_MODULE: _UNQLITECHESS,
    VEDIS_MODULE: _VEDISCHESS,
    GNU_MODULE: _GNUCHESS,
    NDBM_MODULE: _NDBMCHESS,
    DB_TCL_MODULE: _DB_TCLCHESS,
    LMDB_MODULE: _LMDBCHESS,
}

# Default CQL query dataset module name
_DEFAULTCQLQUERY = __name__ + ".basecore.cqlds"

# Map database module names to CQL query dataset module
CQL_QUERY_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTCQLQUERY,
    BSDDB3_MODULE: _DEFAULTCQLQUERY,
    SQLITE3_MODULE: _DEFAULTCQLQUERY,
    APSW_MODULE: _DEFAULTCQLQUERY,
    DPT_MODULE: _DEFAULTCQLQUERY,
    UNQLITE_MODULE: _DEFAULTCQLQUERY,
    VEDIS_MODULE: _DEFAULTCQLQUERY,
    GNU_MODULE: _DEFAULTCQLQUERY,
    NDBM_MODULE: _DEFAULTCQLQUERY,
    DB_TCL_MODULE: _DEFAULTCQLQUERY,
    LMDB_MODULE: _DEFAULTCQLQUERY,
}

# Default full position dataset module name
_DEFAULTFULLPOSITION = __name__ + ".basecore.fullpositionds"

# Map database module names to full position dataset module
FULL_POSITION_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTFULLPOSITION,
    BSDDB3_MODULE: _DEFAULTFULLPOSITION,
    SQLITE3_MODULE: _DEFAULTFULLPOSITION,
    APSW_MODULE: _DEFAULTFULLPOSITION,
    DPT_MODULE: _DEFAULTFULLPOSITION,
    UNQLITE_MODULE: _DEFAULTFULLPOSITION,
    VEDIS_MODULE: _DEFAULTFULLPOSITION,
    GNU_MODULE: _DEFAULTFULLPOSITION,
    NDBM_MODULE: _DEFAULTFULLPOSITION,
    DB_TCL_MODULE: _DEFAULTFULLPOSITION,
    LMDB_MODULE: _DEFAULTFULLPOSITION,
}

# Default analysis dataset module name
_DEFAULTANALYSIS = __name__ + ".basecore.analysisds"

# Map database module names to analysis dataset module
ANALYSIS_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTANALYSIS,
    BSDDB3_MODULE: _DEFAULTANALYSIS,
    SQLITE3_MODULE: _DEFAULTANALYSIS,
    APSW_MODULE: _DEFAULTANALYSIS,
    DPT_MODULE: _DEFAULTANALYSIS,
    UNQLITE_MODULE: _DEFAULTANALYSIS,
    VEDIS_MODULE: _DEFAULTANALYSIS,
    GNU_MODULE: _DEFAULTANALYSIS,
    NDBM_MODULE: _DEFAULTANALYSIS,
    DB_TCL_MODULE: _DEFAULTANALYSIS,
    LMDB_MODULE: _DEFAULTANALYSIS,
}

# Default selection rules dataset module name
_DEFAULTSELECTION = __name__ + ".basecore.selectionds"

# Map database module names to selection rules dataset module
SELECTION_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTSELECTION,
    BSDDB3_MODULE: _DEFAULTSELECTION,
    SQLITE3_MODULE: _DEFAULTSELECTION,
    APSW_MODULE: _DEFAULTSELECTION,
    DPT_MODULE: _DEFAULTSELECTION,
    UNQLITE_MODULE: _DEFAULTSELECTION,
    VEDIS_MODULE: _DEFAULTSELECTION,
    GNU_MODULE: _DEFAULTSELECTION,
    NDBM_MODULE: _DEFAULTSELECTION,
    DB_TCL_MODULE: _DEFAULTSELECTION,
    LMDB_MODULE: _DEFAULTSELECTION,
}
