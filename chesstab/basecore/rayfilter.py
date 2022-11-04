# rayfilter.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (ChessQL) ray filter evaluator.

Examples of ray filters are 'ray ( Q n k )' and 'ray ( Q[a4,c3] n kh1-8 )'.

RayFilter expands the list of square descriptions into the particular rays,
horizontal, vertical, and diagonal, which need to be evaluated.

"""
from chessql.core import constants
from chessql.core import piecedesignator
from chessql.core.cql import Token
from chessql.core import rays

from ..core.constants import MOVE_NUMBER_KEYS
from ..core import filespec

# Longest line is eight squares.  Two end points give a maximum of six internal
# squares.  Shorter lines drop elements from the right.  May add a seventh zero
# element to avoid a len() < 8 test to work around an index error exception.
# Non-zero elements in MAP_RAY_TO_LINE[n][m] are the position of the internal
# piece designator in the ray.
# Zero elements indicate an empty square in the line.
# Thus ray ( Q n b r ) for lines of length five uses MAP_RAY_TO_LINE[2][:][:3]
# where the [:3] part contains two non-zero elements.  These are the lines
# with one empty internal square.  In this ray 'n' is represented by 1 and 'b'
# is represented by 2.
MAP_RAY_TO_LINE = [
    [[0, 0, 0, 0, 0, 0]],  # ray ( a A )
    [
        [1, 0, 0, 0, 0, 0],  # ray ( a A K )
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1],
    ],
    [
        [1, 2, 0, 0, 0, 0],  # ray ( a Q b K )
        [1, 0, 2, 0, 0, 0],
        [0, 1, 2, 0, 0, 0],
        [1, 0, 0, 2, 0, 0],
        [0, 1, 0, 2, 0, 0],
        [0, 0, 1, 2, 0, 0],
        [1, 0, 0, 0, 2, 0],
        [0, 1, 0, 0, 2, 0],
        [0, 0, 1, 0, 2, 0],
        [0, 0, 0, 1, 2, 0],
        [1, 0, 0, 0, 0, 2],
        [0, 1, 0, 0, 0, 2],
        [0, 0, 1, 0, 0, 2],
        [0, 0, 0, 1, 0, 2],
        [0, 0, 0, 0, 1, 2],
    ],
    [
        [1, 2, 3, 0, 0, 0],  # ray ( a Q b N K )
        [1, 2, 0, 3, 0, 0],
        [1, 0, 2, 3, 0, 0],
        [0, 1, 2, 3, 0, 0],
        [1, 2, 0, 0, 3, 0],
        [1, 0, 2, 0, 3, 0],
        [1, 0, 0, 2, 3, 0],
        [0, 1, 2, 0, 3, 0],
        [0, 0, 1, 2, 3, 0],
        [1, 2, 0, 0, 0, 3],
        [1, 0, 2, 0, 0, 3],
        [1, 0, 0, 2, 0, 3],
        [1, 0, 0, 0, 2, 3],
        [0, 1, 2, 0, 0, 3],
        [0, 0, 1, 2, 0, 3],
        [0, 0, 1, 0, 2, 3],
        [0, 0, 0, 1, 2, 3],
    ],
    [
        [1, 2, 3, 4, 0, 0],  # ray ( a Q b N p K )
        [1, 2, 3, 0, 4, 0],
        [1, 2, 0, 3, 4, 0],
        [1, 0, 2, 3, 4, 0],
        [0, 1, 2, 3, 4, 0],
        [1, 2, 3, 0, 0, 4],
        [1, 2, 0, 3, 0, 4],
        [1, 2, 0, 0, 3, 4],
        [1, 0, 2, 3, 0, 4],
        [1, 0, 2, 0, 3, 4],
        [1, 0, 0, 2, 3, 4],
        [0, 1, 2, 3, 0, 4],
        [0, 1, 2, 0, 3, 4],
        [0, 1, 0, 2, 3, 4],
        [0, 0, 1, 2, 3, 4],
    ],
    [
        [1, 2, 3, 4, 5, 0],  # ray ( a Q b N p p K )
        [1, 2, 3, 4, 0, 5],
        [1, 2, 3, 0, 4, 5],
        [1, 2, 0, 3, 4, 5],
        [1, 0, 2, 3, 4, 5],
        [0, 1, 2, 3, 4, 5],
    ],
    [[1, 2, 3, 4, 5, 6]],  # ray ( a Q b N p p N K )
]


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

    def __init__(self, filter_, move_number, variation_code):
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

        self.move_number = move_number
        self.variation_code = variation_code
        raycomponents = []
        mvi = move_number_str(move_number) + variation_code
        for node in filter_.children:
            designator_set = set()
            raycomponents.append(designator_set)
            stack = [node]
            while stack:
                if stack[-1].tokendef is Token.PIECE_DESIGNATOR:
                    designator_set.update(
                        piece_square_to_index(
                            stack[-1].data.designator_set, mvi
                        )
                    )
                    stack.pop()
                    continue
                topnode = stack.pop()
                for spc in topnode.children:
                    stack.append(spc)
        self.raycomponents = raycomponents
        self.emptycomponents = [set() for i in range(len(raycomponents))]
        self.empty_square_games = set()
        self.piece_square_games = set()
        self.recordset_cache = {}
        self.ray_games = {}

    def prune_end_squares(self, database, finder):
        """Remove ray-end squares with no game references."""
        anypiece = (
            constants.ANY_WHITE_PIECE_NAME + constants.ANY_BLACK_PIECE_NAME
        )
        nopiece = constants.EMPTY_SQUARE_NAME
        values_finder = database.values_finder(finder.dbset)
        move = move_number_str(self.move_number)
        nextmove = move_number_str(self.move_number + 1)
        psmwhere, smwhere = [
            database.values_selector(
                " ".join((final_element, "from", move, "below", nextmove))
            )
            for final_element in (
                filespec.PIECESQUAREMOVE_FIELD_DEF,
                filespec.SQUAREMOVE_FIELD_DEF,
            )
        ]
        for selector in psmwhere, smwhere:
            selector.lex()
            selector.parse()
            selector.evaluate(values_finder)
        moveindex = set(psmwhere.node.result + smwhere.node.result)
        for end in 0, -1:
            if nopiece in "".join(self.raycomponents[end]):
                emptyset = self.emptycomponents[end]
                empty = [
                    s[:-1] for s in self.raycomponents[end] if nopiece in s
                ]
                for piece in anypiece:
                    for square in empty:
                        if square + piece in moveindex:
                            continue
                        emptyset.add(square)
            self.raycomponents[end].intersection_update(moveindex)

    def find_games_for_end_squares(self, finder):
        """Remove middle squares in ray with no game references."""
        anywhitepiece = constants.ANY_WHITE_PIECE_NAME
        anyblackpiece = constants.ANY_BLACK_PIECE_NAME
        anypiece = anywhitepiece + anyblackpiece
        record_selector = finder.db.record_selector
        get_ray = rays.get_ray
        empty_square_games = self.empty_square_games
        piece_square_games = self.piece_square_games
        recordset_cache = self.recordset_cache
        start = self.raycomponents[0]
        final = self.raycomponents[-1]
        for start_element in start:
            start_square = start_element[-3:-1]
            for final_element in final:
                final_square = final_element[-3:-1]
                ray_squares = get_ray(start_square, final_square)
                if ray_squares is None:
                    continue
                for psqkey in (
                    start_element,
                    final_element,
                ):
                    if psqkey not in piece_square_games:
                        if psqkey[-1] in anypiece:
                            selector = record_selector(
                                " ".join(
                                    (
                                        filespec.SQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        psqkey,
                                    )
                                )
                            )
                        else:
                            selector = record_selector(
                                " ".join(
                                    (
                                        filespec.PIECESQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        psqkey,
                                    )
                                )
                            )
                        selector.lex()
                        selector.parse()
                        selector.evaluate(finder)
                        piece_square_games.add(psqkey)
                        recordset_cache[psqkey] = selector.node.result.answer
                ray_ends = start_square, final_square
                self._add_recordset_to_ray_games(
                    recordset_cache[start_element],
                    recordset_cache[final_element],
                    ray_ends,
                    finder,
                )
        start = self.emptycomponents[0]
        final = self.emptycomponents[-1]
        for start_element in start:
            start_square = start_element[-2:]
            for final_element in final:
                final_square = final_element[-2:]
                ray_squares = get_ray(start_square, final_square)
                if ray_squares is None:
                    continue
                for esqkey in (
                    start_element,
                    final_element,
                ):
                    if esqkey not in empty_square_games:
                        selector = record_selector(
                            " ".join(
                                (
                                    "not",
                                    "(",
                                    filespec.SQUAREMOVE_FIELD_DEF,
                                    "eq",
                                    esqkey + anywhitepiece,
                                    "or",
                                    esqkey + anyblackpiece,
                                    ")",
                                )
                            )
                        )
                        selector.lex()
                        selector.parse()
                        selector.evaluate(finder)
                        empty_square_games.add(esqkey)
                        recordset_cache[esqkey] = selector.node.result.answer
                ray_ends = start_square, final_square
                self._add_recordset_to_ray_games(
                    recordset_cache[start_element],
                    recordset_cache[final_element],
                    ray_ends,
                    finder,
                )
        start = self.raycomponents[0]
        final = self.raycomponents[-1]
        for start_element in self.emptycomponents[0]:
            if start_element not in empty_square_games:
                continue
            start_square = start_element[-2:]
            cached_start_element = recordset_cache[start_element]
            for final_element in final:
                cached_final_element = recordset_cache[final_element]
                final_square = final_element[-3:-1]
                ray_ends = start_square, final_square
                self._add_recordset_to_ray_games(
                    cached_start_element,
                    cached_final_element,
                    ray_ends,
                    finder,
                )
        for start_element in self.emptycomponents[-1]:
            if start_element not in empty_square_games:
                continue
            final_square = start_element[-2:]
            cached_final_element = recordset_cache[start_element]
            for component in start:
                cached_start_element = recordset_cache[component]
                start_square = component[-3:-1]
                ray_ends = start_square, final_square
                self._add_recordset_to_ray_games(
                    cached_start_element,
                    cached_final_element,
                    ray_ends,
                    finder,
                )

    def _add_recordset_to_ray_games(self, start, final, rayindex, finder):
        """Store records in both start and final under key rayindex.

        finder is not used.

        """
        del finder
        raygames = start & final
        if raygames.count_records():
            if rayindex in self.ray_games:
                self.ray_games[rayindex] |= raygames
            else:
                self.ray_games[rayindex] = raygames

    def find_games_for_middle_squares(self, finder):
        """Remove ray-end squares with no game references."""
        anywhitepiece = constants.ANY_WHITE_PIECE_NAME
        anyblackpiece = constants.ANY_BLACK_PIECE_NAME
        anypiece = anywhitepiece + anyblackpiece
        nopiece = constants.EMPTY_SQUARE_NAME
        record_selector = finder.db.record_selector
        # internal_ray_length = len(self.raycomponents) - 2
        # empty_square_games = self.empty_square_games
        # piece_square_games = self.piece_square_games
        get_ray = rays.get_ray
        recordset_cache = self.recordset_cache
        raycomponents = self.raycomponents
        internal_raycomponents = raycomponents[1:-1]
        mvi = move_number_str(self.move_number) + self.variation_code
        c_sqi = [{}]  # Maybe the empty square index values?
        for component in internal_raycomponents:
            sqi = {}
            c_sqi.append(sqi)
            for item in component:
                sqi.setdefault(item[-3:-1], set()).add(item)
        for start, final in self.ray_games:
            line = get_ray(start, final)
            if line is None:
                continue
            line = line[1:-1]
            if len(line) < len(internal_raycomponents):
                continue
            mapraytoline = MAP_RAY_TO_LINE[len(internal_raycomponents)]
            raygames = []
            for mrtl in mapraytoline:
                if len(line) < 6:  # mapraytoline[7] = 0 avoids this test.
                    if mrtl[len(line)]:
                        break
                linesets = []
                for index, item in enumerate(mrtl[: len(line)]):
                    if line[index] not in c_sqi[item]:
                        if item:
                            linesets.clear()
                            break
                        c_sqi[item][line[index]] = {
                            mvi + line[index] + nopiece
                        }
                    linesets.append(c_sqi[item][line[index]])
                linegames = []
                for gameset in linesets:
                    squareset = finder.db.recordlist_nil(finder.dbset)
                    linegames.append(squareset)
                    for item in gameset:
                        if item in recordset_cache:
                            squareset |= recordset_cache[item]
                            continue
                        if item[-1] == nopiece:
                            selector = record_selector(
                                " ".join(
                                    (
                                        "not",
                                        "(",
                                        filespec.SQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        item[:-1] + anywhitepiece,
                                        "or",
                                        item[:-1] + anyblackpiece,
                                        ")",
                                    )
                                )
                            )
                            selector.lex()
                            selector.parse()
                            selector.evaluate(finder)
                            recordset_cache[item] = selector.node.result.answer
                            squareset |= recordset_cache[item]
                            continue
                        if item[-1] in anypiece:
                            selector = record_selector(
                                " ".join(
                                    (
                                        filespec.SQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        item,
                                    )
                                )
                            )
                        else:
                            selector = record_selector(
                                " ".join(
                                    (
                                        filespec.PIECESQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        item,
                                    )
                                )
                            )
                        selector.lex()
                        selector.parse()
                        selector.evaluate(finder)
                        recordset_cache[item] = selector.node.result.answer
                        squareset |= recordset_cache[item]
                if linegames:
                    squareset = linegames.pop() & self.ray_games[start, final]
                    for gameset in linegames:
                        squareset &= gameset
                    raygames.append(squareset)
            if raygames:
                rayset = raygames.pop()
                for gameset in raygames:
                    rayset |= gameset
                self.ray_games[start, final].replace_records(rayset)
            else:
                self.ray_games[start, final].replace_records(
                    finder.db.recordlist_nil(finder.dbset)
                )


# This function belong in, and has been moved to, a chesstab module.  It came
# from chessql.core.piecedesignator.PieceDesignator, it was a staticmethod, but
# chesstab has no subclass of of PieceDesignator (yet), and rayfilter is only
# user at present.
# The alternative definitions are retained at present.
# Commented to avoid pylint function-redefined message.
# def piece_square_to_index(designator_set, index_prefix):
#    """Convert piece designator set values to index format: Qa4 to a4Q.

#    Assumed that having all index values for a square adjacent is better
#    than having index values for piece together, despite the need for
#    conversion.

#    """
#    ecs = piecedesignator.PieceDesignator.expand_composite_square
#    indexset = set()
#    for piece_square in designator_set:
#        if len(piece_square) != 1:
#            indexset.add(index_prefix + piece_square)
#        else:
#            indexset.update(
#                {
#                    index_prefix + piece_square + s
#                    for s in ecs(
#                        FILE_NAMES[0],
#                        FILE_NAMES[-1],
#                        CQL_RANK_NAMES[0],
#                        CQL_RANK_NAMES[-1],
#                    )
#                }
#            )
#    return indexset


# If 'square piece' is better order than 'piece square'
def piece_square_to_index(designator_set, index_prefix):
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
            indexset.add(index_prefix + piece_square[1:] + piece_square[0])
        else:
            indexset.update(
                {
                    index_prefix + s + piece_square
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
