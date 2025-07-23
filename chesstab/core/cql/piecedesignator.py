# piecedesignator.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (ChessQL) piece designator evaluator."""
import re

import chessql.core.filters
from chessql.core.constants import (
    RANK_RANGE,
    FILE_RANGE,
)

from . import symbol
from . import all_squares
from . import unicode_map
from . import designator
from . import element
from ..constants import (
    ANY_WHITE_PIECE_NAME,
    ANY_BLACK_PIECE_NAME,
    EMPTY_SQUARE_NAME,
)

RANGE_SEPARATOR = r"-"
SQUARE_DESIGNATOR_SEPARATOR = r","
ALL_PIECES = ANY_WHITE_PIECE_NAME + ANY_BLACK_PIECE_NAME + EMPTY_SQUARE_NAME
del ANY_WHITE_PIECE_NAME
del ANY_BLACK_PIECE_NAME
del EMPTY_SQUARE_NAME

# This is used to split the piece designator to fit the processing needed.
# The constants module defines a PIECE_DESIGNATOR which consumes a piece
# designator without collecting the component parts.
_piece_designator = re.compile(
    r"".join(
        (
            r"(?:",
            r"(?:",
            r"\[",
            r"(?P<compoundsquare>[a-h][-a-h1-8]*",
            r"[1-8](?:,[a-h][-a-h1-8]*[1-8])*)",
            r"\]",
            r")",
            r"|",
            r"(?:",
            r"(?P<filerankrange>[a-h]-[a-h][1-8]-[1-8])",
            r"|",
            r"(?P<filerange>[a-h]-[a-h][1-8])",
            r"|",
            r"(?P<rankrange>[a-h][1-8]-[1-8])",
            r"|",
            r"(?P<square>[a-h][1-8])",
            r")",
            r")",
            r"|",
            r"(?:(?:(?:",
            r"(?:",
            r"\[",
            r"(?P<compoundpiece_s>[^\]]+)",
            r"\]",
            r")",
            r"|",
            r"(?P<piece_s>[QBRNKPAqbrnkpa_])",
            r"|",
            r"(?P<piece_utf8_s>[♕♗♖♘♔♙△♛♝♜♞♚♟▲□◭]+)",
            r")(?:",
            r"(?:",
            r"\[",
            r"(?P<p_compoundsquare>[a-h][-a-h1-8]*",
            r"[1-8](?:,[a-h][-a-h1-8]*[1-8])*)",
            r"\]",
            r")",
            r"|",
            r"(?:",
            r"(?P<p_filerankrange>[a-h]-[a-h][1-8]-[1-8])",
            r"|",
            r"(?P<p_filerange>[a-h]-[a-h][1-8])",
            r"|",
            r"(?P<p_rankrange>[a-h][1-8]-[1-8])",
            r"|",
            r"(?P<p_square>[a-h][1-8])",
            r")",
            r"))",
            r"|",
            r"(?:",
            r"(?:",
            r"\[",
            r"(?P<compoundpiece>[^\]]+)",
            r"\]",
            r")",
            r"|",
            r"(?P<piece>[QBRNKPAqbrnkpa_])",
            r"|",
            r"(?P<piece_utf8>[♕♗♖♘♔♙△♛♝♜♞♚♟▲□◭]+)",
            r"|",
            r"(?P<anysquare>\.)",
            r"|",
            r"(?P<anysquare_utf8>▦)",
            r")",
            r")",
        )
    )
)


# Originally written to the cql1.0 definition.
# The composite piece types U, M, m, I, i, and ?, had disappeared by the cql5.0
# definition.
# The CQL syntax is very different but the piece designator syntax is the same,
# so some of this class needs to be re-written.
# A further change occurs at cql6.0 where empty square is '_', not '.'.
# The '.' represents all squares instead (like a-h1-8).
# At cql6.2 unicode piece characters are accepted (not in this pattern yet).
class PieceDesignator(designator.Designator, symbol.Symbol):
    """ChessQL piece designator filter evaluation class.

    Impossible piece square combinations are accepted, pawns on ranks 1 and 8
    for example, but later processing may make assumptions about the need to
    look at the database for them.
    """

    def __init__(self, *args):
        """Initialise a PieceDesignator instance for token."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.PieceDesignator)
        self._groups = None
        self._orbit = None

    def expand_symbol(self):
        """Delegate to child symbols then do own expanding."""
        super().expand_symbol()
        self.parse()
        self.expand_piece_designator()

    def collect_transform_targets(self, targets):
        """Append self to targets list."""
        targets.append(self)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Override, evaluate piece designator.

        constraint must be a square name or None meaning all squares.

        """
        key = (self._signature, constraint)
        data = cache.get(key)
        if data is not None:
            self._data = data
            return
        self.where_eq_piece_designator(
            movenumber,
            "0",
            self._designator_set["" if constraint is None else constraint],
        )
        self.evaluate_statement(cqlfinder)
        cache[key] = self._data

    def parse(self):
        """Extract the piece designator from this instance's token.

        The groups extracted using the piece_designator regular expression
        are made available in self._groups.

        """
        match_ = _piece_designator.match(self._token.get_match_text())
        if match_:
            self._groups = match_.groupdict(default="")

    @property
    def orbit(self):
        """Return the orbit of the piece designator set."""
        return self._orbit

    def expand_piece_designator(self):
        """Expand a piece designator into a set of simple piece designators.

        The set is available in property designator_set.

        Return None.

        """
        if self._groups is None:
            return
        squareset = set()
        # get_squares() returns [""], not [], if no squares are
        # specified.  Any "" in the returned list is ignored.
        for sqr in self.get_squares():
            if len(sqr) == 2:
                squareset.add(sqr)
            elif len(sqr) == 6:
                squareset.update(
                    self._token.expand_composite_square(
                        sqr[0], sqr[2], sqr[3], sqr[5]
                    )
                )
            elif len(sqr) == 4:
                if sqr[1] == "-":
                    squareset.update(
                        self._token.expand_composite_square(
                            sqr[0], sqr[2], sqr[3], sqr[3]
                        )
                    )
                elif sqr[2] == "-":
                    squareset.update(
                        self._token.expand_composite_square(
                            sqr[0], sqr[0], sqr[1], sqr[3]
                        )
                    )
        designator_set = {}
        all_designators = set()
        pieces = "".join(sorted(self.get_pieces()))
        self._designator_pieces = pieces
        for square in squareset:
            designator_set[square] = set(p + square for p in pieces)
            all_designators.update(designator_set[square])
        if not squareset:
            for square in all_squares.ALL_SQUARES:
                designator_set[square] = set(p + square for p in pieces)
            all_designators.update(pieces)
        elif len(squareset) == len(all_squares.ALL_SQUARES):
            all_designators.clear()
            all_designators.update(pieces)
        designator_set[""] = all_designators
        self._designator_set = designator_set
        self._signature = pieces + "".join(sorted(squareset)).join("[]")
        if not squareset or all_squares.ALL_SQUARES.issubset(squareset):
            self._designator_squares = all_squares.ALL_SQUARES
        else:
            self._designator_squares = frozenset(squareset)
        # Evaluation must be driven from the transform operator which set
        # the orbit up. May have to be a dict for 'shift ... shift ...'.
        # In 'shift ray ( Rb7 ray ( b _ ) kf-g7 )' each orbit element is
        # four piece designators wide, and the answers for the orbit
        # elements are 'or'ed to give the whole answer.
        self._orbit = []

    def get_pieces(self):
        """Return the piece type designator component of the piece designator.

        The absence of any piece type, including empty square, means any white
        or black piece.  In this case 'Aa' is returned.

        """
        groups = self._groups
        pieces = "".join(
            (
                groups["compoundpiece_s"],
                groups["piece_s"],
                groups["piece_utf8_s"].translate(unicode_map.unicode_to_str),
                groups["compoundpiece"],
                groups["piece"],
                groups["piece_utf8"].translate(unicode_map.unicode_to_str),
            )
        )
        if pieces:
            return "".join(sorted(pieces))
        return ALL_PIECES

    def get_squares(self):
        """Return list of squares in the piece designator."""
        groups = self._groups
        return "".join(
            (
                groups["compoundsquare"],
                groups["filerankrange"],
                groups["filerange"],
                groups["rankrange"],
                groups["square"],
                groups["p_compoundsquare"],
                groups["p_filerankrange"],
                groups["p_filerange"],
                groups["p_rankrange"],
                groups["p_square"],
                (
                    FILE_RANGE + RANK_RANGE
                    if groups["anysquare"] or groups["anysquare_utf8"]
                    else ""
                ),
            )
        ).split(SQUARE_DESIGNATOR_SEPARATOR)


class OrbitElement(designator.Designator, element.Element):
    """Transformed filter evaluation class."""

    def __init__(self):
        """Delegate to initialise."""
        super().__init__()
