# dptdu_dir.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with dpt.chessdptdu to database."""


if __name__ == "__main__":

    from .directory_widget import DirectoryWidget
    from ..dpt.chessdptdu import chess_dptdu

    DirectoryWidget(chess_dptdu, "dpt")
