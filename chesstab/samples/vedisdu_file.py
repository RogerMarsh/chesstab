# vedisdu_file.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with vedis.chessvedisdu to database."""


if __name__ == "__main__":

    from .file_widget import FileWidget
    from ..vedis.chessvedisdu import ChessDatabase

    FileWidget(ChessDatabase, "vedis")
