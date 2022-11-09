# cqlnode.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Query Language (ChessQL) parameter and filter evaluator.

Evaluate a node tree built by cql package using a chesstab database.

The description of variables at CQL version 6.0.4 suggests any construct using
variables cannot be evaluated by ChessTab because indicies are used rather than
processing each game move-by-move.  The relevant passages are copied from CQL
documentation as comments in the chessql.core.statement module.

"""
import copy

from chessql.core.cql import Token
from chessql.core.constants import (
    RANGE_SEPARATOR,
    PIECE_NAMES,
    SQUARE_DESIGNATOR_SEPARATOR,
    FILE_NAMES,
    CQL_RANK_NAMES,
)
from chessql.core.node import Node
from chessql.core.piecedesignator import PieceDesignator

from ..basecore.rayfilter import RayFilter


class CQLNodeError(Exception):
    """Exception class for cqlnode module."""


class CQLNode(Node):
    """Extend ChessQL Node for ChessTab implementation of CQL statements.

    data holds the components used to build a statement which can be
    processed by the solentware_base.core where and find modules.

    """

    def __init__(self, *a, **k):
        """Delegate then initialize node state."""
        super().__init__(*a, **k)

        # May get rid of 'where' because components should not be needed again
        # after the 'where statement' has been constructed: bind the 'where
        # statement' to 'data' in other words.
        self.data = None
        self.where = None

    @staticmethod
    def transform_piece_designators(fs_filter):
        """Apply transforms to piece designators in CQL statement."""
        children = fs_filter.children
        for node in fs_filter.node.children:
            children.append(FSNode(node))
            transformation = node.transform_piece_designators(children[-1])
            if transformation:
                return transformation
        transformation = fs_filter.transform_descendant_piece_designators()
        if transformation:
            return transformation
        return None

    def expand_child_piece_designators(self):
        """Expand piece designators in child nodes.

        Expanded piece designators are made available in FSNode.designator_set,
        and cache for optimizing index access.

        """
        for node in self.children:
            node.expand_child_piece_designators()
        if self.leaf:
            if self.tokendef is Token.PIECE_DESIGNATOR:
                piece_designator = PieceDesignator(self.leaf)
                piece_designator.parse()
                piece_designator.expand_piece_designator()
                self.data = piece_designator

    # Beginning of attempt to generalize self.data to instantiate set filter.
    # Deal with ray filter in addition to piece designator.
    def expand_set_filters(self):
        """Expand set filters in child nodes.

        Expanded piece designators are made available in FSNode.designator_set,
        and cache for optimizing index access.

        """
        for node in self.children:
            node.expand_set_filters()
        if self.leaf:
            if self.tokendef is Token.PIECE_DESIGNATOR:
                piece_designator = PieceDesignator(self.leaf)
                piece_designator.parse()
                piece_designator.expand_piece_designator()
                self.data = piece_designator
            return
        if self.tokendef is Token.RAY:
            self.data = RayFilter(self)

    def get_shift_limits(self, ranklimits=None, filelimits=None):
        """Set rank and file shift limits."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            data.get_shift_limits(ranklimits, filelimits)
        for node in self.children:
            node.get_shift_limits(ranklimits=ranklimits, filelimits=filelimits)

    def shift(self, shiftfiles, shiftranks):
        """Shift shiftfiles and shiftranks for pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = data.get_squares()
            squares = "".join([shiftfiles.get(s, s) for s in squares])
            squares = "".join([shiftranks.get(s, s) for s in squares])
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = data.get_pieces()
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        for node in self.children:
            node.shift(shiftfiles, shiftranks)

    def rotate(self, rotation):
        """Rotate rotation for pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = _normalize_rotated_squares(
                "".join([rotation.get(s, s) for s in data.get_squares()])
            )
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = data.get_pieces()
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        for node in self.children:
            node.rotate(rotation)

    def reflect_horizontal(self):
        """Reflect ranks for pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = _normalize_horizontally_reflected_squares(
                "".join(
                    [
                        FSNode.REFLECT_HORIZONTAL.get(s, s)
                        for s in data.get_squares()
                    ]
                )
            )
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = data.get_pieces()
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        for node in self.children:
            node.reflect_horizontal()

    def reflect_vertical(self):
        """Reflect files for pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = _normalize_vertically_reflected_squares(
                "".join(
                    [
                        FSNode.REFLECT_VERTICAL.get(s, s)
                        for s in data.get_squares()
                    ]
                )
            )
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = data.get_pieces()
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        for node in self.children:
            node.reflect_vertical()

    def rotate_and_reflect_horizontal(self):
        """Rotate 90 and reflect ranks for pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = _normalize_rotated_squares(
                "".join(
                    [
                        FSNode.ROTATE_90_REFLECT_HORIZONTAL.get(s, s)
                        for s in data.get_squares()
                    ]
                )
            )
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = data.get_pieces()
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        for node in self.children:
            node.rotate_and_reflect_horizontal()

    def rotate_and_reflect_vertical(self):
        """Rotate 90 and reflect files for pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = _normalize_rotated_squares(
                "".join(
                    [
                        FSNode.ROTATE_90_REFLECT_VERTICAL.get(s, s)
                        for s in data.get_squares()
                    ]
                )
            )
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = data.get_pieces()
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        for node in self.children:
            node.rotate_and_reflect_vertical()

    def flip_color(self):
        """Flip the colour of pieces referenced."""
        if self.tokendef is Token.PIECE_DESIGNATOR:
            data = PieceDesignator(self.leaf)
            data.parse()
            squares = _normalize_horizontally_reflected_squares(
                "".join(
                    [
                        FSNode.REFLECT_HORIZONTAL.get(s, s)
                        for s in data.get_squares()
                    ]
                )
            )
            if data.is_compound_squares():
                squares = squares.join(("[", "]"))
            pieces = "".join(
                FSNode.FLIP_COLOR_PIECE.get(s, s) for s in data.get_pieces()
            )
            if data.is_compound_pieces():
                pieces = pieces.join(("[", "]"))
            self.leaf = pieces + squares
        elif self.name == "plain_filter":
            if self.leaf in FSNode.FLIP_COLOR_TOMOVE:
                self.leaf = FSNode.FLIP_COLOR_TOMOVE[self.leaf]
        elif self.name in FSNode.FLIP_COLOR_FILTER:
            self.name = FSNode.FLIP_COLOR_FILTER[self.name]
            return
        for node in self.children:
            node.flip_color()

    def __deepcopy__(self, memo):
        """Return a deepcopy of memo."""
        newcopy = super().__deepcopy__(memo)
        newcopy.data = None
        newcopy.where = None
        return newcopy


class FSNode:
    """Scaffolding to evaluate CQLNodes created by the cql package."""

    INITIAL_RANK_LIMITS = CQL_RANK_NAMES[-1], CQL_RANK_NAMES[0]
    INITIAL_FILE_LIMITS = FILE_NAMES[-1], FILE_NAMES[0]

    ROTATE_90 = dict(
        zip(
            CQL_RANK_NAMES + FILE_NAMES,
            (
                "".join(z for z in reversed(FILE_NAMES))
                + "".join(z for z in CQL_RANK_NAMES)
            ),
        )
    )

    # This comprehension construct did not work at Python3.6.1 at this place.
    # ROTATE_180 = {x:ROTATE_90[ROTATE_90[x]]
    # for x in CQL_RANK_NAMES + FILE_NAMES}

    ROTATE_180 = {}
    for x in CQL_RANK_NAMES + FILE_NAMES:
        ROTATE_180[x] = ROTATE_90[ROTATE_90[x]]
    ROTATE_270 = {}
    for x in CQL_RANK_NAMES + FILE_NAMES:
        ROTATE_270[x] = ROTATE_90[ROTATE_180[x]]
    REFLECT_HORIZONTAL = dict(
        zip(CQL_RANK_NAMES, "".join(z for z in reversed(CQL_RANK_NAMES)))
    )
    REFLECT_VERTICAL = dict(
        zip(FILE_NAMES, "".join(z for z in reversed(FILE_NAMES)))
    )

    # These rotate-reflect combinations are not defined by CQL but are used to
    # generate the diagonal reflections needed to complete the flip transform.
    ROTATE_90_REFLECT_HORIZONTAL = {}
    ROTATE_90_REFLECT_VERTICAL = {}
    for x in CQL_RANK_NAMES + FILE_NAMES:
        y = ROTATE_90[x]
        ROTATE_90_REFLECT_HORIZONTAL[x] = REFLECT_HORIZONTAL.get(y, y)
        ROTATE_90_REFLECT_VERTICAL[x] = REFLECT_VERTICAL.get(y, y)
    del x, y

    FLIP_COLOR_PIECE = dict(
        zip(
            PIECE_NAMES,
            "".join(
                (
                    PIECE_NAMES[6:12],
                    PIECE_NAMES[0:6],
                    PIECE_NAMES[13],
                    PIECE_NAMES[12],
                    PIECE_NAMES[14],
                )
            ),
        )
    )
    FLIP_COLOR_TOMOVE = {
        Token.WTM.name: Token.BTM.name,
        Token.BTM.name: Token.WTM.name,
    }
    FLIP_COLOR_FILTER = {
        Token.WHITE.name: Token.BLACK.name,
        Token.BLACK.name: Token.WHITE.name,
    }

    def __init__(self, node):
        """Note node and initialize child nodes to empty list."""
        self.node = node
        self.children = []

    # Put this stuff in cql.core.statement because the piece designator text is
    # modified, not the expansion into database keys?
    def transform_descendant_piece_designators(self):
        """Apply transform to descendant piece designators.

        Some points from http://www.gadycosteff.com/cql/doc/transform.html for
        cql5.0 are:

        'flipvertical Pa1-8' is equivalent to 'Ph1-8 or Pa1-8'.  Replacing a
        single piece designator by a sequence of piece designators in an 'or'
        clause is valid for all the transform filters.

        The transform filters are: flipvertical, fliphorizontal, flipdihedral,
        flip, rotate90, rotate45, flipcolor, shifthorizontal, shiftvertical,
        and shift.  They are applied recursively to constituent filters:

        'flipvertical attack (Rg6 K)' and 'attack (Rg6 k) or attack (Rb6 k)'
        are equivalent.

        Each transform filter is in one of the categories: dihedral, rotate45,
        color, and shift.

        Ranges in transform filters specify the count of the transforms of the
        argument filter which must match for the transform filter to match.

        Comments on shift copied temporarely in full:

        shiftvertical shifts its argument 0 or more squares vertically:

        shiftvertical g6
        ≡ g1 or g2 or... or g8
        ≡ g1-8

        Likewise:

        shiftvertical [g2,g4]
        ≡ g1-8

        When a square is shifted off the board it normally disappears. Piece
        designators with empty square sets eliminate the entire transform:

        shiftvertical {Kb1 kg6}
        ≡
        {Kb1 Kg6} or {Kb2 Kg7} or {Kb3 Kg8}

        There is no downward shift of kg6 because doing so would eliminate the
        b1 square for the K.

        shifthorizontal works likewise.

        shift is equivalent to shifthorizontal shiftvertical. Using the example
        above:

        shift {Kb1 kg6}
        ≡ shifthorizontal shiftvertical {Kb1 kg6}
        ≡ shifthorizontal {Kb1 kg6} or
          shifthorizontal {Kb2 kg7} or
          shifthorizontal {Kb3 kg8}
        ≡ {Kb1 kg6} or {Ka1 kf6} or {Kc1 kh6} or
          {Kb2 kg7} or {Ka2 kf7} or {Kc2 kh7} or
          {Kb3 kg8} or {Ka3 kf8} or {Kc3 kh8}

        This also means that

        shift Ka2 ≡ K

        wraparound As a special rule, shiftvertical does not alter a file of 8
        squares:

        shiftvertical {Kd1-8 Ba2}
        ≡ {Kd1-8 Ba2} or
          {Kd1-8 Ba3} or
          {Kd1-8 Ba4} or
          {Kd1-8 Ba5} or
          {Kd1-8 Ba6} or
          {Kd1-8 Ba7} or
          {Kd1-8 Ba8} or
          {Kd1-8 Ba1}

        which turns out to be equivalent to

        {Kd1-8 Ba1-8}

        But

        shiftvertical {Kd2-8 Ba2}
        ≡ {Kd2-8 Ba2} or
          {Kd3-8 Ba3} or
          {Kd4-8 Ba4} or
          {Kd5-8 Ba5} or
          {Kd6-8 Ba6} or
          {Kd7-8 Ba7} or
          {Kd8 Ba8} or
          {Kd1-7 Ba1}

        which is entirely different. Similarly, shifthorizontal does not change
        ranks with 8 squares:

        shifthorizontal {Ka-h2 Ba4}
        ≡ {Ka-h2 Ba-h4}

        The shift transform doesn't change full ranks or files in the direction
        of its shift:

        shift {Ka-h2 Ba4}
        ≡ {Ka-h2 Ba-h4} or
          {Ka-h3 Ba-h5} or
          {Ka-h4 Ba-h6} or
          {Ka-h5 Ba-h7} or
          {Ka-h6 Ba-h8} or
          {Ka-h1 Ba-h3}

        Note that any transform applied to a piece designator without an
        explicit square qualifier leaves the piece designator unchanged:

        shift K
        ≡ K

        and likewise

        flip K
        ≡ K

        """
        for node in self.children:
            transformed = self._transform.get(
                node.node.tokendef, lambda s: None
            )(node)
            if transformed:
                return transformed
        return None

    def _flip(self):
        ranklow, rankhigh, filelow, filehigh = self._get_transform_limits()
        if (ranklow, rankhigh) == FSNode.INITIAL_RANK_LIMITS and (
            filelow,
            filehigh,
        ) == FSNode.INITIAL_FILE_LIMITS:
            return
        transforms = []
        for transformed in (
            FSNode.ROTATE_90,
            FSNode.ROTATE_180,
            FSNode.ROTATE_270,
        ):
            transforms.extend(self._generate_rotated_filters(transformed))
        transforms.extend(self._generate_vertical_reflection_filters())
        transforms.extend(self._generate_horizontal_reflection_filters())
        transforms.extend(
            self._generate_rotate_90_vertical_reflection_filters()
        )
        transforms.extend(
            self._generate_rotate_90_horizontal_reflection_filters()
        )
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _fliphorizontal(self):
        ranklow, rankhigh, filelow, filehigh = self._get_transform_limits()
        if (ranklow, rankhigh) == FSNode.INITIAL_RANK_LIMITS and (
            filelow,
            filehigh,
        ) == FSNode.INITIAL_FILE_LIMITS:
            return
        transforms = self._generate_horizontal_reflection_filters()
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _flipvertical(self):
        ranklow, rankhigh, filelow, filehigh = self._get_transform_limits()
        if (ranklow, rankhigh) == FSNode.INITIAL_RANK_LIMITS and (
            filelow,
            filehigh,
        ) == FSNode.INITIAL_FILE_LIMITS:
            return
        transforms = self._generate_vertical_reflection_filters()
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _rotate90(self):
        ranklow, rankhigh, filelow, filehigh = self._get_transform_limits()
        if (ranklow, rankhigh) == FSNode.INITIAL_RANK_LIMITS and (
            filelow,
            filehigh,
        ) == FSNode.INITIAL_FILE_LIMITS:
            return
        transforms = []
        for transformed in (
            FSNode.ROTATE_90,
            FSNode.ROTATE_180,
            FSNode.ROTATE_270,
        ):
            transforms.extend(self._generate_rotated_filters(transformed))
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _rotate45(self):
        ranklow, rankhigh, filelow, filehigh = self._get_transform_limits()
        if (ranklow, rankhigh) != FSNode.INITIAL_RANK_LIMITS or (
            filelow,
            filehigh,
        ) != FSNode.INITIAL_FILE_LIMITS:
            return "rotate45 on specific squares"
        return "rotate45 not implemented"

    def _flipcolor(self):
        """Apply flipcolor transform to filter.

        Some points from http://www.gadycosteff.com/cql/doc/transform.html for
        cql5.0 are:

        The flipcolor transform applied to filter is the 'or' of filter with
        the new filter formed from the filter as follows:

            the colors of any piece designators in filter are changed;
            'wtm' is changed to 'btm' and vice versa;
            'player white' is changed to 'player black' and vice versa;
            'elo white' is changed to 'elo black' and vice versa
            'result 0-1' is changed to 'result 1-0' and vice versa
            All piece designators in filter are reflected about the horizontal
            bisector of the board.

        """
        transforms = self._generate_flipped_color_filters()
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _shift(self):
        ranklow, rankhigh, filelow, filehigh = self._get_transform_limits()
        if (ranklow, rankhigh) == FSNode.INITIAL_RANK_LIMITS and (
            filelow,
            filehigh,
        ) == FSNode.INITIAL_FILE_LIMITS:
            # No shifts needed.
            # Change self.node.tokendef from 'shift' to '{' or leave alone so
            # meaning of self.node.range is clear?
            # Evaluation of query must treat this node as '{' rather than 'or'.
            # Is single child sufficient to decide this?
            # Same applies to all the other transform filters.
            return
        sourcefiles = list(FILE_NAMES)
        fileshifts = []
        limit_range = (
            sourcefiles.index(filelow) + 8 - sourcefiles.index(filehigh)
        )
        for count in range(sourcefiles.index(filelow)):
            sourcefiles.append(sourcefiles.pop(0))
        for count in range(limit_range):
            fileshifts.append(dict(zip(sourcefiles, FILE_NAMES)))
            sourcefiles.insert(0, sourcefiles.pop())
        # pylint message unused-variable.
        # Find a way of doing without count in this method's loops.
        del count
        sourceranks = list(CQL_RANK_NAMES)
        rankrange = (
            sourceranks.index(ranklow) + 8 - sourceranks.index(rankhigh)
        )
        for count in range(sourceranks.index(ranklow)):
            sourceranks.append(sourceranks.pop(0))
        transforms = []
        for count in range(rankrange):
            rankshifts = dict(zip(sourceranks, CQL_RANK_NAMES))
            for fshift in fileshifts:
                if (
                    fshift[filelow] != filelow
                    or rankshifts[ranklow] != ranklow
                ):
                    transforms.extend(
                        self._generate_shifted_filters(fshift, rankshifts)
                    )
            sourceranks.insert(0, sourceranks.pop())
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _shiftvertical(self):
        ranklimits = list(FSNode.INITIAL_RANK_LIMITS)
        self.node.get_shift_limits(ranklimits=ranklimits)
        if tuple(ranklimits) == FSNode.INITIAL_RANK_LIMITS:
            return
        self._shift_one_direction(ranklimits, CQL_RANK_NAMES, FILE_NAMES)

    def _shifthorizontal(self):
        filelimits = list(FSNode.INITIAL_FILE_LIMITS)
        self.node.get_shift_limits(filelimits=filelimits)
        if tuple(filelimits) == FSNode.INITIAL_FILE_LIMITS:
            return
        self._shift_one_direction(filelimits, FILE_NAMES, CQL_RANK_NAMES)

    _transform = {
        Token.FLIP: _flip,
        Token.FLIPHORIZONTAL: _fliphorizontal,
        Token.FLIPVERTICAL: _flipvertical,
        Token.ROTATE90: _rotate90,
        Token.ROTATE45: _rotate45,
        Token.FLIPCOLOR: _flipcolor,
        Token.SHIFT: _shift,
        Token.SHIFTHORIZONTAL: _shifthorizontal,
        Token.SHIFTVERTICAL: _shiftvertical,
    }

    def _get_transform_limits(self):
        ranklimit = list(FSNode.INITIAL_RANK_LIMITS)
        filelimit = list(FSNode.INITIAL_FILE_LIMITS)
        self.node.get_shift_limits(ranklimits=ranklimit, filelimits=filelimit)
        return ranklimit[0], ranklimit[1], filelimit[0], filelimit[1]

    def _shift_one_direction(self, limits, shiftsource, staticsource):
        """Extend children with one-direction transformed filters.

        Caller has specified transformation rules in a baseline square, limits,
        and rank and square shifts, shiftsource and staticsource depending on
        transform direction.

        self will be a transformation filter node so the transformed filters
        are appended to self.children.

        """
        source = list(shiftsource)
        shifts = []
        limit_range = source.index(limits[0]) + 8 - source.index(limits[1])
        for count in range(source.index(limits[0])):
            source.append(source.pop(0))
        for count in range(limit_range):
            shifts.append(dict(zip(source, shiftsource)))
            source.insert(0, source.pop())
        # pylint message unused-variable.
        # Find a way of doing without count in this method's loops.
        del count
        static = dict(zip(staticsource, staticsource))
        transforms = []
        for tshift in shifts:
            if tshift[limits[0]] != limits[0]:
                transforms.extend(
                    self._generate_shifted_filters(tshift, static)
                )
        for tnode in transforms:
            self.node.children.append(tnode.node)

    def _generate_shifted_filters(self, shiftfiles, shiftranks):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.shift(shiftfiles, shiftranks)
        return transforms

    def _generate_rotated_filters(self, rotation):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.rotate(rotation)
        return transforms

    def _generate_horizontal_reflection_filters(self):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.reflect_horizontal()
        return transforms

    def _generate_vertical_reflection_filters(self):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.reflect_vertical()
        return transforms

    def _generate_rotate_90_horizontal_reflection_filters(self):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.rotate_and_reflect_horizontal()
        return transforms

    def _generate_rotate_90_vertical_reflection_filters(self):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.rotate_and_reflect_vertical()
        return transforms

    def _generate_flipped_color_filters(self):
        transforms = []
        for node in self.children:
            transforms.append(copy.deepcopy(node))
            transforms[-1].node.flip_color()
        return transforms


def _normalize_rotated_squares(squares):
    normalized_squares = []
    for designator in squares.split(SQUARE_DESIGNATOR_SEPARATOR):
        square = list(designator)
        if len(square) == 2:
            if square[0] in CQL_RANK_NAMES:
                square[0], square[1] = square[1], square[0]
        elif len(square) == 6:
            if square[0] > square[2]:
                square[0], square[2] = square[2], square[0]
            if square[3] > square[5]:
                square[3], square[5] = square[5], square[3]
            if square[0] in CQL_RANK_NAMES:
                square[0], square[2], square[3], square[5] = (
                    square[3],
                    square[5],
                    square[0],
                    square[2],
                )
        elif square[1] == RANGE_SEPARATOR:
            if square[0] > square[2]:
                square[0], square[2] = square[2], square[0]
            if square[0] in CQL_RANK_NAMES:
                square.insert(0, square.pop())
        elif square[2] == RANGE_SEPARATOR:
            if square[1] > square[3]:
                square[1], square[3] = square[3], square[1]
            if square[0] in CQL_RANK_NAMES:
                square.append(square.pop(0))
        normalized_squares.append("".join(square))
    return SQUARE_DESIGNATOR_SEPARATOR.join(normalized_squares)


def _normalize_horizontally_reflected_squares(squares):
    normalized_squares = []
    for square in squares.split(SQUARE_DESIGNATOR_SEPARATOR):
        if (
            len(square) == 6
            or len(square) == 4
            and square[2] == RANGE_SEPARATOR
        ):
            square = list(square)
            square[-3], square[-1] = square[-1], square[-3]
            square = "".join(square)
        normalized_squares.append("".join(square))
    return SQUARE_DESIGNATOR_SEPARATOR.join(normalized_squares)


def _normalize_vertically_reflected_squares(squares):
    normalized_squares = []
    for square in squares.split(SQUARE_DESIGNATOR_SEPARATOR):
        if (
            len(square) == 6
            or len(square) == 4
            and square[1] == RANGE_SEPARATOR
        ):
            square = list(square)
            square[0], square[2] = square[2], square[0]
            square = "".join(square)
        normalized_squares.append("".join(square))
    return SQUARE_DESIGNATOR_SEPARATOR.join(normalized_squares)
