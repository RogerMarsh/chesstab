# read_pgn.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Read a PGN file and calculate all indexing."""

from pgn_read.samples._utilities import main

from ..core.pgn import GameUpdate


if __name__ == "__main__":

    main(game_class=GameUpdate, samples_title="Sample ChessTab Update Report")
