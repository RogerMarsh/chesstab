# ndbmdu_file.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with ndbm.chessndbmdu to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..ndbm.chessndbmdu import ChessDatabase

    FileWidget(ChessDatabase, "dbm.ndbm")
