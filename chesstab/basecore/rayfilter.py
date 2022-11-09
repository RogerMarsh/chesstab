# rayfilter.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (ChessQL) ray filter evaluator.

Examples of ray filters are 'ray ( Q n k )' and 'ray ( Q[a4,c3] n kh1-8 )'.

RayFilter expands the list of square descriptions into the particular rays,
horizontal, vertical, and diagonal, which need to be evaluated.

The CQL definition of ray filter allows any set filter, not just piece
designators, in the ray filter.  For example ray ( Q up 1 n k).

The RayFilter class ignores, at best, other set filters: in the example
'up 1 n' is treated as 'n' ignoring the 'up' filter.

"""
from chessql.core import constants
from chessql.core import piecedesignator
from chessql.core.cql import Token
from chessql.core import rays

from ..core.constants import MOVE_NUMBER_KEYS


class RayFilterError(Exception):
    """Exception class for rayfilter module."""


class RayFilter:
    """ChessQL ray filter evaluator.

    The ray filter has a list of square specifiers, piece designators
    usually, which define the rays to be evaluated.

    This class assumes the caller has expanded the piece designator parameters
    to the ray or between filter; and applied any transforms.

    Use this class like:
    C(RayFilter)

    Subclasses must implement the database interface specific methods defined
    in this class which raise RayFilterError('Not implemented')
    exceptions.

    """

    def __init__(self, filter_):
        """Initialize to apply filter_ on move_number."""
        if filter_.tokendef is not Token.RAY:
            raise RayFilterError(
                "".join(
                    (
                        "Filter '",
                        filter_.name,
                        "' is not a ray filter.",
                    )
                )
            )

        if len(filter_.children) < 2:
            raise RayFilterError(
                "".join(
                    (
                        "Filter '",
                        filter_.name,
                        "' must have at least two arguments.",
                    )
                )
            )

        raysets = []
        for node in filter_.children:
            designator_set = set()
            raysets.append(designator_set)
            stack = [node]
            while stack:
                if stack[-1].tokendef is Token.PIECE_DESIGNATOR:
                    designator_set.update(
                        piece_square_to_index(stack[-1].data.designator_set)
                    )
                    stack.pop()
                    continue
                topnode = stack.pop()
                for spc in topnode.children:
                    stack.append(spc)
        raysets = tuple(tuple(i) for i in raysets)
        raycomponents = []
        size = tuple(len(i) for i in raysets)
        count = 1
        for elementsize in size:
            count *= elementsize
        looper = [i - 1 for i in size]
        while count:
            count -= 1
            self._append_linear_rayitem_to_raycomponents(
                [raysets[e][i] for e, i in enumerate(looper)], raycomponents
            )
            for element, item in enumerate(looper):
                if not item:
                    continue
                looper[element] -= 1
                if element:
                    for looperitem in range(element):
                        looper[looperitem] = size[looperitem] - 1
                break
        self.raycomponents = raycomponents

    @staticmethod
    def _append_linear_rayitem_to_raycomponents(rayitem, raycomponents):
        """Add linear rayitem to raycomponents list for evaluation.

        The empty square specifications, if any, are added.

        """
        start_square = rayitem[0][:-1]
        final_square = rayitem[-1][:-1]
        ray_squares = rays.get_ray(start_square, final_square)
        if ray_squares is None:
            return
        rayitem_set = set(r[:-1] for r in rayitem[1:-1])
        ray_squares_set = set(ray_squares[1:-1])
        if rayitem_set.difference(ray_squares_set):
            return
        for square in ray_squares_set.difference(rayitem_set):
            rayitem.append(square + constants.EMPTY_SQUARE_NAME)
        if start_square > final_square:
            raycomponents.append(list(reversed(sorted(rayitem))))
        else:
            raycomponents.append(sorted(rayitem))

    def find_games(self, movenumber, variation, evaluator):
        """Find games fitting ray for movenumber and variation."""
        recordset_cache = {}
        recordset_count_cache = {}
        prefix = move_number_str(movenumber) + variation
        for item in self.raycomponents:
            raycomponent = [prefix + i for i in item]
            for mvsp in raycomponent:
                if mvsp not in recordset_cache:
                    recordset_cache[mvsp] = evaluator(mvsp)
                    recordset_count_cache[mvsp] = recordset_cache[
                        mvsp
                    ].count_records()
        for count in recordset_count_cache.values():
            if not count:
                return {}
        return recordset_cache


# This function belong in, and has been moved to, a chesstab module.  It came
# from chessql.core.piecedesignator.PieceDesignator, it was a staticmethod, but
# chesstab has no subclass of of PieceDesignator (yet), and rayfilter is only
# user at present.
# The function may go back to chessql now that the movenumber and variation
# elements have been removed: these are chesstab implementation details and
# what remains is properly chessql stuff.
# The alternative commented definition with the <piece square> order has been
# removed because the <square piece> order is more convenient for sorting
# ray components into square order too.
# The designator set names <piece squares> because that is how they are
# expressed in CQL statements.
def piece_square_to_index(designator_set):
    """Convert piece designator set values to index format: Qa4 to a4Q.

    Assumed that having all index values for a square adjacent is better
    than having index values for piece together, despite the need for
    conversion.

    """
    file_names = constants.FILE_NAMES
    rank_names = constants.CQL_RANK_NAMES
    ecs = piecedesignator.PieceDesignator.expand_composite_square
    indexset = set()
    for piece_square in designator_set:
        if len(piece_square) != 1:
            indexset.add(piece_square[1:] + piece_square[0])
        else:
            indexset.update(
                {
                    s + piece_square
                    for s in ecs(
                        file_names[0],
                        file_names[-1],
                        rank_names[0],
                        rank_names[-1],
                    )
                }
            )
    return indexset


def move_number_str(move_number):
    """Return hex(move_number) values prefixed with string length.

    A '0x' prefix is removed first.

    """
    # Adapted from module pgn_read.core.parser method add_move_to_game().
    try:
        return MOVE_NUMBER_KEYS[move_number]
    except IndexError:
        base16 = hex(move_number)
        return str(len(base16) - 2) + base16[2:]
