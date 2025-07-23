# all_squares.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define set of all squares."""

from pgn_read.core.constants import FILE_NAMES

from chessql.core.constants import CQL_RANK_NAMES


def _build():
    """Return frozenset of square names."""
    allsquares = set()
    for file in FILE_NAMES:
        for rank in CQL_RANK_NAMES:
            allsquares.add(file + rank)
    return frozenset(allsquares)


ALL_SQUARES = _build()
del _build
del FILE_NAMES
del CQL_RANK_NAMES
