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
)

APPLICATION_NAME = "ChessTab"
ERROR_LOG = "ErrorLog"

# bsddb3 interface module name
_BERKELEYDBCHESS = __name__ + ".berkeleydb.chessberkeleydb"

# bsddb3 interface module name
_DBCHESS = __name__ + ".db.chessdb"

# DPT interface module name
_DPTCHESS = __name__ + ".dpt.chessdpt"

# sqlite3 interface module name
_SQLITE3CHESS = __name__ + ".sqlite.chesssqlite3"

# apsw interface module name
_APSWCHESS = __name__ + ".apsw.chessapsw"

# unqlite interface module name
_UNQLITECHESS = __name__ + ".unqlite.chessunqlite"

# vedis interface module name
_VEDISCHESS = __name__ + ".vedis.chessvedis"

# dbm.gnu interface module name
_GNUCHESS = __name__ + ".gnu.chessgnu"

# dbm.ndbm interface module name
_NDBMCHESS = __name__ + ".ndbm.chessndbm"

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
}

# Default partial position dataset module name
_DEFAULTPARTIALPOSITION = __name__ + ".basecore.cqlds"

# DPT partial position dataset module name
_DPTPARTIALPOSITION = __name__ + ".dpt.cqlds"

# Map database module names to partial position dataset module
PARTIAL_POSITION_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTPARTIALPOSITION,
    BSDDB3_MODULE: _DEFAULTPARTIALPOSITION,
    SQLITE3_MODULE: _DEFAULTPARTIALPOSITION,
    APSW_MODULE: _DEFAULTPARTIALPOSITION,
    DPT_MODULE: _DPTPARTIALPOSITION,
    UNQLITE_MODULE: _DEFAULTPARTIALPOSITION,
    VEDIS_MODULE: _DEFAULTPARTIALPOSITION,
    GNU_MODULE: _DEFAULTPARTIALPOSITION,
    NDBM_MODULE: _DEFAULTPARTIALPOSITION,
}

# Default full position dataset module name
_DEFAULTFULLPOSITION = __name__ + ".basecore.fullpositionds"

# DPT full dataset module name
_DPTFULLPOSITION = __name__ + ".dpt.fullpositionds"

# Map database module names to full position dataset module
FULL_POSITION_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTFULLPOSITION,
    BSDDB3_MODULE: _DEFAULTFULLPOSITION,
    SQLITE3_MODULE: _DEFAULTFULLPOSITION,
    APSW_MODULE: _DEFAULTFULLPOSITION,
    DPT_MODULE: _DPTFULLPOSITION,
    UNQLITE_MODULE: _DEFAULTFULLPOSITION,
    VEDIS_MODULE: _DEFAULTFULLPOSITION,
    GNU_MODULE: _DEFAULTFULLPOSITION,
    NDBM_MODULE: _DEFAULTFULLPOSITION,
}

# Default analysis dataset module name
_DEFAULTANALYSIS = __name__ + ".basecore.analysisds"

# DPT analysis dataset module name
_DPTANALYSIS = __name__ + ".dpt.analysisds"

# Map database module names to analysis dataset module
ANALYSIS_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTANALYSIS,
    BSDDB3_MODULE: _DEFAULTANALYSIS,
    SQLITE3_MODULE: _DEFAULTANALYSIS,
    APSW_MODULE: _DEFAULTANALYSIS,
    DPT_MODULE: _DPTANALYSIS,
    UNQLITE_MODULE: _DEFAULTANALYSIS,
    VEDIS_MODULE: _DEFAULTANALYSIS,
    GNU_MODULE: _DEFAULTANALYSIS,
    NDBM_MODULE: _DEFAULTANALYSIS,
}

# Default selection rules dataset module name
_DEFAULTSELECTION = __name__ + ".basecore.selectionds"

# DPT selection rules dataset module name
_DPTSELECTION = __name__ + ".dpt.selectionds"

# Map database module names to selection rules dataset module
SELECTION_MODULE = {
    BERKELEYDB_MODULE: _DEFAULTSELECTION,
    BSDDB3_MODULE: _DEFAULTSELECTION,
    SQLITE3_MODULE: _DEFAULTSELECTION,
    APSW_MODULE: _DEFAULTSELECTION,
    DPT_MODULE: _DPTSELECTION,
    UNQLITE_MODULE: _DEFAULTSELECTION,
    VEDIS_MODULE: _DEFAULTSELECTION,
    GNU_MODULE: _DEFAULTSELECTION,
    NDBM_MODULE: _DEFAULTSELECTION,
}
