# transforms.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Classes to evaluate transform filters.

The transform filters are: flip ('✵'), flipcolor ('⬓'), fliphorizontal,
flipvertical, reversecolor, rotate45, rotate90, shift, shifthorizontal,
shifrtvertical, and notransform.
"""

import chessql.core.filters

from . import symbol
from . import transform_map
from . import partition


class _Transform(symbol.Symbol):
    """Note transform for application to child filters."""

    @property
    def designator_set(self):
        """Return the piece designator set for the transform filter."""
        return self.master.children[-1].node.designator_set

    @property
    def designator_squares(self):
        """Return the set of squares represented by the transform filter."""
        return self.master.children[-1].node.designator_squares

    def prepare_to_evaluate_symbol(self):
        """Add self to stack of transforms then delegate then remove."""
        super().prepare_to_evaluate_symbol()
        targets = []
        for child in self.master.children:
            child.node.collect_transform_targets(targets)
        self._generate_transforms(targets)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Delegate to child symbols then do own evaluation.

        Arguments are passed to superclass method.  This method combines
        the results found by child filters evaluated via super().

        """
        super().evaluate_symbol(
            cqlfinder, movenumber, cache, constraint=constraint
        )
        self._data = self.master.children[-1].node.data

    def _generate_transforms(self, targets):
        """Do nothing.  Subclasses should override as needed."""
        print([f.signature for f in targets])

    @staticmethod
    def _create_orbit_elements(transformed, targets, transforms_done):
        """Create orbit elements for transforms."""
        frozen = tuple(
            (frozenset(t.full_row_names), frozenset(t.part_row_squares))
            for t in transformed
        )
        if frozen not in transforms_done:
            transforms_done.add(frozen)
            for target, new in zip(targets, transformed):
                target.orbit.append(new)

    def _calculate_row_transforms(
        self, base, directions, targets, transforms_done=None
    ):
        """Calculate horizontal or vertical shift transforms.

        base is the square sets in targets partitioned horizontally or
        vertically.
        directions is the pair of directions appropriate to partitioning.
        targets is the piece designators to be transformed.
        transforms_done should be a set to note duplicate transforms as
        they arise.  It defaults to an empty set.

        """
        if transforms_done is None:
            transforms_done = set()
        for item in base:
            item.partition_row()
        for direction in directions:
            transformed = base.copy()
            while True:
                transformed = [direction(t) for t in transformed]
                if True in {
                    not t.full_row_names and not t.part_row_squares
                    for t in transformed
                }:
                    break
                self._create_orbit_elements(
                    transformed, targets, transforms_done
                )

    def _calculate_transforms(
        self,
        base,
        directions,
        inner,
        inner_directions,
        targets,
        transforms_done=None,
    ):
        """Calculate horizontal or vertical shift transforms.

        base is the square sets in targets partitioned horizontally or
        vertically.
        directions is the pair of directions appropriate to partitioning.
        targets is the piece designators to be transformed.
        transforms_done should be a set to note duplicate transforms as
        they arise.  It defaults to an empty set.

        """
        if transforms_done is None:
            transforms_done = set()
        for item in base:
            item.partition_row()
        for direction in directions:
            transformed = base.copy()
            while True:
                transformed = [direction(t) for t in transformed]
                if True in {
                    not t.full_row_names and not t.part_row_squares
                    for t in transformed
                }:
                    break
                self._create_orbit_elements(
                    transformed, targets, transforms_done
                )
                self._calculate_row_transforms(
                    [inner.inner_base(t) for t in transformed],
                    inner_directions,
                    targets,
                    transforms_done=transforms_done,
                )


class Flip(_Transform):
    """Evaluate flip filter."""

    def __init__(self, *args):
        """Initialise a Flip instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Flip)


class FlipColor(_Transform):
    """Evaluate flipcolor filter."""

    def __init__(self, *args):
        """Initialise a FlipColor instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.FlipColor)


class FlipHorizontal(_Transform):
    """Evaluate fliphorizontal filter."""

    def __init__(self, *args):
        """Initialise a FlipHorizontal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.FlipHorizontal)


class FlipVertical(_Transform):
    """Evaluate flipvertical filter."""

    def __init__(self, *args):
        """Initialise a FlipVertical instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.FlipVertical)


class ReverseColor(_Transform):
    """Evaluate reversecolor filter."""

    def __init__(self, *args):
        """Initialise a ReverseColor instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.ReverseColor)


class Rotate45(_Transform):
    """Evaluate rotate45 filter."""

    def __init__(self, *args):
        """Initialise a Rotate45 instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Rotate45)


class Rotate90(_Transform):
    """Evaluate rotate90 filter."""

    def __init__(self, *args):
        """Initialise a Rotate90 instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Rotate90)


class Shift(_Transform):
    """Evaluate shift filter."""

    def __init__(self, *args):
        """Initialise a Shift instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Shift)

    def _generate_transforms(self, targets):
        """Generate horizontal and vertical transforms."""
        hpart = partition.HorizontalPartition
        vpart = partition.VerticalPartition
        transforms_done = set()
        self._calculate_row_transforms(
            [vpart(t.designator_squares) for t in targets],
            (vpart.up_one, vpart.down_one),
            targets,
            transforms_done=transforms_done,
        )
        self._calculate_transforms(
            [hpart(t.designator_squares) for t in targets],
            (hpart.left_one, hpart.right_one),
            vpart,
            (vpart.up_one, vpart.down_one),
            targets,
            transforms_done=transforms_done,
        )


class ShiftHorizontal(_Transform):
    """Evaluate shifthorizontal filter."""

    def __init__(self, *args):
        """Initialise a ShiftHorizontal instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.ShiftHorizontal)

    def _generate_transforms(self, targets):
        """Generate horizontal (left and right) transforms."""
        part = partition.HorizontalPartition
        self._calculate_row_transforms(
            [part(t.designator_squares) for t in targets],
            (part.left_one, part.right_one),
            targets,
            transforms_done=set(),
        )


class ShiftVertical(_Transform):
    """Evaluate shiftvertical filter."""

    def __init__(self, *args):
        """Initialise a ShiftVertical instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.ShiftVertical)

    def _generate_transforms(self, targets):
        """Generate vertical (up and down) transforms."""
        part = partition.VerticalPartition
        self._calculate_row_transforms(
            [part(t.designator_squares) for t in targets],
            (part.up_one, part.down_one),
            targets,
            transforms_done=set(),
        )


class NoTransform(_Transform):
    """Evaluate notransform filter."""

    def __init__(self, *args):
        """Initialise a NoTransform instance."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.NoTransform)
