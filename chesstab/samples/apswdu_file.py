# apswdu_file.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with apsw.chessapswdu to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..apsw.chessapswdu import ChessDatabase

    FileWidget(ChessDatabase, "apsw")
