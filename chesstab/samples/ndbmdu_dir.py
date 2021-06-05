# ndbmdu_dir.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with ndbm.chessndbmdu to database.

The default segment size, 4000 bytes, leads to a
'HASH: Out of overflow pages.  Increase page size'
error when importing about 2000 games split about evenly between two PGN files.

The same import succeeds if chesstab.tools.create_chesstab_database is used to
create the database with a segment size of 16 bytes.  A more reasonable size,
500 bytes, the smallest intended for production may work on the example tried
too.
"""


if __name__ == "__main__":

    from .directory_widget import DirectoryWidget
    from ..ndbm.chessndbmdu import chess_ndbmdu

    DirectoryWidget(chess_ndbmdu, "dbm.ndbm")
