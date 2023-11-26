# dptfastload_dir.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with dpt.chessdptfastload to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from .chessdptfastload import chess_dptfastload

    DirectoryWidget(chess_dptfastload, "dpt fastload")
