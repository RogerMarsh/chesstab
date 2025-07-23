# partition.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Classes to partition squares into full rows and rows with holes."""

from pgn_read.core.constants import FILE_NAMES

from chessql.core.constants import CQL_RANK_NAMES

from . import transform_map

_full_file = {f: frozenset(f + r for r in CQL_RANK_NAMES) for f in FILE_NAMES}
_full_rank = {r: frozenset(f + r for f in FILE_NAMES) for r in CQL_RANK_NAMES}


class _PartitionRow:
    """Partition the square mappings implied by the 'shift*' filters.

    Where a complete file or rank of squares is specified by a piece
    designator that file or rank is not changed by applying single square
    shifts along the file or rank.  For example 'a8' maps to 'a1' on an
    'up' shift if all eight 'a' squares are spicified but to nothing if
    any squares are missing.

    For the 'shifthorizontal' and 'shiftvertical' filters individual
    square transforms are needed only for squares in partly filled rows.

    For the 'shift' filter less individual square transforms may be needed
    with one of the directions as the outer loop.
    """

    def __init__(self, squares):
        """Initialize squares, rows, row names, and rows with holes."""
        self._squares = squares
        self._full_rows = set()
        self._full_row_names = set()
        self._part_row_squares = set()

    @property
    def full_rows(self):
        """Retuen self._full_rows, the squares in full rows."""
        return self._full_rows

    @property
    def full_row_names(self):
        """Retuen self._full_row_names, the names of full rows."""
        return self._full_row_names

    @property
    def part_row_squares(self):
        """Retuen self._part_row_squares, the squares in rows with holes."""
        return self._part_row_squares

    def _partition_row(self, lines):
        """Split squares into full rows and squares on rows with holes.

        lines should be a dict of files or ranks where the key is the
        file or rank name, and the value is the set of squares in that row.

        """
        squares = self._squares
        rows = self._full_rows
        names = self._full_row_names
        for name, line in lines.items():
            if not line.difference(squares):
                rows.update(line)
                names.add(name)
        self._part_row_squares.update(squares.difference(rows))

    def populate_transform(self, direction, base):
        """Update self with base transformed one square in direction.

        The updated sets are assumed empty before update.

        """
        self.full_rows.update(base.full_rows)
        self.full_row_names.update(base.full_row_names)
        self.part_row_squares.update(
            set(direction.get(square) for square in base.part_row_squares)
        )
        self.part_row_squares.discard(None)

    @classmethod
    def inner_base(cls, base):
        """Return cls instance with base expanded to squares."""
        return cls(base.part_row_squares.union(base.full_rows))


class HorizontalPartition(_PartitionRow):
    """Partition the squares horizontally."""

    def partition_row(self):
        """Split squares into full ranks and squares on ranks with holes."""
        self._partition_row(_full_rank)

    @classmethod
    def left_one(cls, base):
        """Return cls instance with base transformed left one."""
        item = cls(set())
        item.populate_transform(transform_map.left, base)
        return item

    @classmethod
    def right_one(cls, base):
        """Return cls instance with base transformed right one."""
        item = cls(set())
        item.populate_transform(transform_map.right, base)
        return item


class VerticalPartition(_PartitionRow):
    """Partition the squares vertically."""

    def partition_row(self):
        """Split squares into full files and squares on files with holes."""
        self._partition_row(_full_file)

    @classmethod
    def up_one(cls, base):
        """Return cls instance with base transformed up one."""
        item = cls(set())
        item.populate_transform(transform_map.up, base)
        return item

    @classmethod
    def down_one(cls, base):
        """Return cls instance with base transformed down one."""
        item = cls(set())
        item.populate_transform(transform_map.down, base)
        return item


class PartitionRows:
    """Partition the squares horizontally and vertically.

    This provides file, rank, and square, counts to assist decision on
    whether horizontal or vertical transform should be the outer loop
    in 'shift' transforms.  The 'shifthorizontal' and 'shiftvertical'
    transforms do not need this decision.
    """

    def __init__(self, squares):
        """Initialize squares."""
        self._squares = squares
        self._horizontal_partition = None
        self._vertical_partition = None

    @property
    def full_files(self):
        """Retuen the squares in full files."""
        return self._vertical_partition.full_rows

    @property
    def full_file_names(self):
        """Return the names of full files."""
        return self._vertical_partition.full_row_names

    @property
    def part_file_squares(self):
        """Return the squares in files with holes."""
        return self._vertical_partition.part_row_squares

    @property
    def full_ranks(self):
        """Return the squares in full ranks."""
        return self._horizontal_partition.full_rows

    @property
    def full_rank_names(self):
        """Return the names of full ranks."""
        return self._horizontal_partition.full_row_names

    @property
    def part_rank_squares(self):
        """Return the squares in ranks with holes."""
        return self._horizontal_partition.part_row_squares

    def partition_horizontally_and_vertically(self):
        """Split squares into full rows and squares on rows with holes.

        This is done for files and ranks.

        """
        self._horizontal_partition = HorizontalPartition(self._squares)
        self._vertical_partition = VerticalPartition(self._squares)
        self._horizontal_partition.partition_row()
        self._vertical_partition.partition_row()
