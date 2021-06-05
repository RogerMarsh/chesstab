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

from ..core.constants import MOVE_NUMBER_KEYS
from ..core import filespec

# Longest line is eight squares.  Two end points give a maximum of six internal
# squares.  Shorter lines drop elements from the right.  May add a seventh zero
# element to avoid a len() < 8 test to work around an index error exception.
# ray ( Q n b r ) for lines of length five uses MAP_RAY_TO_LINE[2][:][:3] where
# the [:3] part contains two non-zero elements.  These are the lines with one
# empty internal square.
# Non-zero elements in MAP_RAY_TO_LINE[n][m] are the internal piece designator
# in the ray.
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
    pass


class RayFilter:
    """ChessQL ray filter evaluator.

    The ray and between filters have a list of square specifiers, usually piece
    designators, which define the rays to be evaluated.

    This class assumes the caller has expanded the piece designator parameters
    to the ray or between filter; and applied any transforms.

    Use this class like:
    C(RayFilter)

    Subclasses must implement the database interface specific methods defined
    in this class which raise RayFilterError('Not implemented')
    exceptions.

    """

    def __init__(self, filter_, move_number, variation_code):
        """ """
        if filter_.tokendef not in {Token.BETWEEN, Token.RAY}:
            raise RayFilterError(
                "".join(
                    (
                        "Filter '",
                        filter_.name,
                        "' does not support rays.",
                    )
                )
            )

        # Is this really needed!
        if len(filter_.children) != 1:
            raise RayFilterError(
                "".join(
                    (
                        "Filter '",
                        filter_.name,
                        "' format not correct.",
                    )
                )
            )
        if filter_.children[0].tokendef is not Token.LEFTPARENTHESIS:
            raise RayFilterError(
                "".join(
                    (
                        "Filter '",
                        filter_.name,
                        "' format not correct.",
                    )
                )
            )

        self.move_number = move_number
        self.variation_code = variation_code
        raycomponents = []
        mvi = move_number_str(move_number) + variation_code
        for c in filter_.children[0].children:
            designator_set = set()
            raycomponents.append(designator_set)
            stack = [c]
            while stack:
                if stack[-1].tokendef is Token.PIECE_DESIGNATOR:
                    designator_set.update(
                        piece_square_to_index(
                            stack[-1].data.designator_set, mvi
                        )
                    )
                    stack.pop()
                    continue
                sp = stack.pop()
                for spc in sp.children:
                    stack.append(spc)
        self.raycomponents = raycomponents
        self.emptycomponents = [set() for i in range(len(raycomponents))]
        self.empty_square_games = set()
        self.piece_square_games = set()
        self.recordset_cache = {}
        self.ray_games = {}

    def prune_end_squares(self, database):
        """Remove ray-end squares with no game references"""
        anypiece = (
            constants.ANY_WHITE_PIECE_NAME + constants.ANY_BLACK_PIECE_NAME
        )
        nopiece = constants.EMPTY_SQUARE_NAME
        fd = filespec.PIECESQUAREMOVE_FIELD_DEF, filespec.SQUAREMOVE_FIELD_DEF
        values_finder = database.values_finder(finder.dbset)
        move = move_number_str(self.move_number)
        nextmove = move_number_str(self.move_number + 1)
        psmwhere, smwhere = [
            database.values_selector(
                " ".join((f, "from", move, "below", nextmove))
            )
            for f in fd
        ]
        for w in psmwhere, smwhere:
            w.lex()
            w.parse()
            w.evaluate(values_finder)
        moveindex = set(psmwhere.node.result + smwhere.node.result)
        for end in 0, -1:
            if nopiece in "".join(self.raycomponents[end]):
                emptyset = self.emptycomponents[end]
                empty = [
                    s[:-1] for s in self.raycomponents[end] if nopiece in s
                ]
                for p in anypiece:
                    for e in empty:
                        if e + p in moveindex:
                            continue
                        emptyset.add(e)
            self.raycomponents[end].intersection_update(moveindex)

    def find_games_for_end_squares(self, finder):
        """Remove ray-end squares with no game references"""
        anywhitepiece = constants.ANY_WHITE_PIECE_NAME
        anyblackpiece = constants.ANY_BLACK_PIECE_NAME
        anypiece = anywhitepiece + anyblackpiece
        record_selector = finder.db.record_selector
        rays = constants.RAYS
        empty_square_games = self.empty_square_games
        piece_square_games = self.piece_square_games
        recordset_cache = self.recordset_cache
        start = self.raycomponents[0]
        final = self.raycomponents[-1]
        for s in start:
            start_square = s[-3:-1]
            rs = rays[start_square]
            for f in final:
                final_square = f[-3:-1]
                if final_square not in rs:
                    continue
                for ps in (
                    s,
                    f,
                ):
                    if ps not in piece_square_games:
                        if ps[-1] in anypiece:
                            w = record_selector(
                                " ".join(
                                    (
                                        filespec.SQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        ps,
                                    )
                                )
                            )
                        else:
                            w = record_selector(
                                " ".join(
                                    (
                                        filespec.PIECESQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        ps,
                                    )
                                )
                            )
                        w.lex()
                        w.parse()
                        w.evaluate(finder)
                        piece_square_games.add(ps)
                        recordset_cache[ps] = w.node.result.answer
                i = start_square, final_square
                self._add_recordset_to_ray_games(
                    recordset_cache[s], recordset_cache[f], i, finder
                )
        start = self.emptycomponents[0]
        final = self.emptycomponents[-1]
        for s in start:
            start_square = s[-2:]
            rs = rays[start_square]
            for f in final:
                final_square = f[-2:]
                if final_square not in rs:
                    continue
                for ps in (
                    s,
                    f,
                ):
                    if ps not in empty_square_games:
                        w = record_selector(
                            " ".join(
                                (
                                    "not",
                                    "(",
                                    filespec.SQUAREMOVE_FIELD_DEF,
                                    "eq",
                                    ps + anywhitepiece,
                                    "or",
                                    ps + anyblackpiece,
                                    ")",
                                )
                            )
                        )
                        w.lex()
                        w.parse()
                        w.evaluate(finder)
                        empty_square_games.add(ps)
                        recordset_cache[ps] = w.node.result.answer
                i = start_square, final_square
                self._add_recordset_to_ray_games(
                    recordset_cache[s], recordset_cache[f], i, finder
                )
        start = self.raycomponents[0]
        final = self.raycomponents[-1]
        for e in self.emptycomponents[0]:
            if e not in empty_square_games:
                continue
            start_square = e[-2:]
            sc = recordset_cache[e]
            for f in final:
                fc = recordset_cache[f]
                final_square = f[-3:-1]
                i = start_square, final_square
                self._add_recordset_to_ray_games(sc, fc, i, finder)
        for e in self.emptycomponents[-1]:
            if e not in empty_square_games:
                continue
            final_square = e[-2:]
            fc = recordset_cache[e]
            for s in start:
                sc = recordset_cache[s]
                start_square = s[-3:-1]
                i = start_square, final_square
                self._add_recordset_to_ray_games(sc, fc, i, finder)

    def _add_recordset_to_ray_games(self, start, final, rayindex, finder):
        """Remove ray-end squares with no game references"""
        rg = start & final
        if rg.count_records():
            if rayindex in self.ray_games:
                self.ray_games[rayindex] |= rg
            else:
                self.ray_games[rayindex] = rg

    def find_games_for_middle_squares(self, finder):
        """Remove ray-end squares with no game references"""
        anywhitepiece = constants.ANY_WHITE_PIECE_NAME
        anyblackpiece = constants.ANY_BLACK_PIECE_NAME
        anypiece = anywhitepiece + anyblackpiece
        nopiece = constants.EMPTY_SQUARE_NAME
        record_selector = finder.db.record_selector
        internal_ray_length = len(self.raycomponents) - 2
        empty_square_games = self.empty_square_games
        piece_square_games = self.piece_square_games
        recordset_cache = self.recordset_cache
        raycomponents = self.raycomponents
        internal_raycomponents = raycomponents[1:-1]
        mvi = move_number_str(self.move_number) + self.variation_code
        c_sqi = [{}]  # Maybe the empty square index values?
        for e, rc in enumerate(internal_raycomponents):
            sqi = {}
            c_sqi.append(sqi)
            for i in rc:
                sqi.setdefault(i[-3:-1], set()).add(i)
        for start, final in self.ray_games:
            line = constants.RAYS[start][final][1:-1]
            if len(line) < len(internal_raycomponents):
                continue
            mapraytoline = MAP_RAY_TO_LINE[len(internal_raycomponents)]
            raygames = []
            for mrtl in mapraytoline:
                if len(line) < 6:  # mapraytoline[7] = 0 avoids this test.
                    if mrtl[len(line)]:
                        break
                linesets = []
                for e, v in enumerate(mrtl[: len(line)]):
                    if line[e] not in c_sqi[v]:
                        if v:
                            linesets.clear()
                            break
                        c_sqi[v][line[e]] = {mvi + line[e] + nopiece}
                    linesets.append(c_sqi[v][line[e]])
                linegames = []
                for lg in linesets:
                    squareset = finder.db.recordlist_nil(finder.dbset)
                    linegames.append(squareset)
                    for i in lg:
                        if i in recordset_cache:
                            squareset |= recordset_cache[i]
                            continue
                        if i[-1] == nopiece:
                            w = record_selector(
                                " ".join(
                                    (
                                        "not",
                                        "(",
                                        filespec.SQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        i[:-1] + anywhitepiece,
                                        "or",
                                        i[:-1] + anyblackpiece,
                                        ")",
                                    )
                                )
                            )
                            w.lex()
                            w.parse()
                            w.evaluate(finder)
                            recordset_cache[i] = w.node.result.answer
                            squareset |= recordset_cache[i]
                            continue
                        if i[-1] in anypiece:
                            w = record_selector(
                                " ".join(
                                    (
                                        filespec.SQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        i,
                                    )
                                )
                            )
                        else:
                            w = record_selector(
                                " ".join(
                                    (
                                        filespec.PIECESQUAREMOVE_FIELD_DEF,
                                        "eq",
                                        i,
                                    )
                                )
                            )
                        w.lex()
                        w.parse()
                        w.evaluate(finder)
                        recordset_cache[i] = w.node.result.answer
                        squareset |= recordset_cache[i]
                if linegames:
                    squareset = linegames.pop() & self.ray_games[index]
                    for lg in linegames:
                        squareset &= lg
                    raygames.append(squareset)
            if raygames:
                rayset = raygames.pop()
                for rg in raygames:
                    rayset |= rg
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
def piece_square_to_index(designator_set, index_prefix):
    """Convert piece designator set values to index format: Qa4 to a4Q.

    Assumed that having all index values for a square adjacent is better
    than having index values for piece together, despite the need for
    conversion.

    """
    ecs = piecedesignator.PieceDesignator._expand_composite_square
    ds = set()
    for ps in designator_set:
        if len(ps) != 1:
            ds.add(index_prefix + ps)
        else:
            ds.update(
                {
                    index_prefix + ps + s
                    for s in ecs(
                        FILE_NAMES[0],
                        FILE_NAMES[-1],
                        RANK_NAMES[0],
                        RANK_NAMES[-1],
                    )
                }
            )
    return ds


# If 'square piece' is better order than 'piece square'
def piece_square_to_index(designator_set, index_prefix):
    """Convert piece designator set values to index format: Qa4 to a4Q.

    Assumed that having all index values for a square adjacent is better
    than having index values for piece together, despite the need for
    conversion.

    """
    ecs = piecedesignator.PieceDesignator._expand_composite_square
    ds = set()
    for ps in designator_set:
        if len(ps) != 1:
            ds.add(index_prefix + ps[1:] + ps[0])
        else:
            ds.update(
                {
                    index_prefix + s + ps
                    for s in ecs(
                        FILE_NAMES[0],
                        FILE_NAMES[-1],
                        RANK_NAMES[0],
                        RANK_NAMES[-1],
                    )
                }
            )
    return ds


def move_number_str(move_number):
    """Return hex(move_number) values without leading '0x' but prefixed with
    string length.
    """
    # Adapted from module pgn_read.core.parser method add_move_to_game().
    try:
        return MOVE_NUMBER_KEYS[move_number]
    except IndexError:
        c = hex(move_number)
        return str(len(c) - 2) + c[2:]
