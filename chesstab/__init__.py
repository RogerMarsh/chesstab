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
    BSDDB_MODULE,
    BSDDB3_MODULE,
    DPT_MODULE,
    SQLITE3_MODULE,
    APSW_MODULE,
    )

APPLICATION_NAME = 'ChessTab'
ERROR_LOG = 'ErrorLog'

# Berkeley DB interface module name
_DBCHESS = __name__ + '.db.chessdb'

# DPT interface module name
_DPTCHESS = __name__ + '.dpt.chessdpt'

# sqlite3 interface module name
_SQLITE3CHESS = __name__ + '.sqlite.chesssqlite3'

# apsw interface module name
_APSWCHESS = __name__ + '.apsw.chessapsw'

# Map database module names to application module
APPLICATION_DATABASE_MODULE = {
    BSDDB_MODULE: _DBCHESS,
    BSDDB3_MODULE: _DBCHESS,
    SQLITE3_MODULE: _SQLITE3CHESS,
    APSW_MODULE: _APSWCHESS,
    DPT_MODULE: _DPTCHESS,
    }

# Berkeley DB partial position dataset module name
_DBPARTIALPOSITION = __name__ + '.basecore.cqlds'

# DPT partial position dataset module name
_DPTPARTIALPOSITION = __name__ + '.dpt.cqlds'

# sqlite3 partial position dataset module name
_SQLITE3PARTIALPOSITION = __name__ + '.basecore.cqlds'

# apsw partial position dataset module name
_APSWPARTIALPOSITION = __name__ + '.basecore.cqlds'

# Map database module names to partial position dataset module
PARTIAL_POSITION_MODULE = {
    BSDDB_MODULE: _DBPARTIALPOSITION,
    BSDDB3_MODULE: _DBPARTIALPOSITION,
    SQLITE3_MODULE: _SQLITE3PARTIALPOSITION,
    APSW_MODULE: _APSWPARTIALPOSITION,
    DPT_MODULE: _DPTPARTIALPOSITION,
    }

# Berkeley DB full position dataset module name
_DBFULLPOSITION = __name__ + '.basecore.fullpositionds'

# DPT full dataset module name
_DPTFULLPOSITION = __name__ + '.dpt.fullpositionds'

# sqlite3 full dataset module name
_SQLITE3FULLPOSITION = __name__ + '.basecore.fullpositionds'

# apsw full dataset module name
_APSWFULLPOSITION = __name__ + '.basecore.fullpositionds'

# Map database module names to full position dataset module
FULL_POSITION_MODULE = {
    BSDDB_MODULE: _DBFULLPOSITION,
    BSDDB3_MODULE: _DBFULLPOSITION,
    SQLITE3_MODULE: _SQLITE3FULLPOSITION,
    APSW_MODULE: _APSWFULLPOSITION,
    DPT_MODULE: _DPTFULLPOSITION,
    }

# Berkeley DB analysis dataset module name
_DBANALYSIS = __name__ + '.basecore.analysisds'

# DPT analysis dataset module name
_DPTANALYSIS = __name__ + '.dpt.analysisds'

# sqlite3 analysis dataset module name
_SQLITE3ANALYSIS = __name__ + '.basecore.analysisds'

# apsw analysis dataset module name
_APSWANALYSIS = __name__ + '.basecore.analysisds'

# Map database module names to analysis dataset module
ANALYSIS_MODULE = {
    BSDDB_MODULE: _DBANALYSIS,
    BSDDB3_MODULE: _DBANALYSIS,
    SQLITE3_MODULE: _SQLITE3ANALYSIS,
    APSW_MODULE: _APSWANALYSIS,
    DPT_MODULE: _DPTANALYSIS,
    }

# Berkeley DB selection rules dataset module name
_DBSELECTION = __name__ + '.basecore.selectionds'

# DPT selection rules dataset module name
_DPTSELECTION = __name__ + '.dpt.selectionds'

# sqlite3 selection rules dataset module name
_SQLITE3SELECTION = __name__ + '.basecore.selectionds'

# apsw selection rules dataset module name
_APSWSELECTION = __name__ + '.basecore.selectionds'

# Map database module names to selection rules dataset module
SELECTION_MODULE = {
    BSDDB_MODULE: _DBSELECTION,
    BSDDB3_MODULE: _DBSELECTION,
    SQLITE3_MODULE: _SQLITE3SELECTION,
    APSW_MODULE: _APSWSELECTION,
    DPT_MODULE: _DPTSELECTION,
    }
