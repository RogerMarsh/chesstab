# test_partition.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.partition module."""

import unittest

from .. import partition
from .. import all_squares


class _PartitionRow(unittest.TestCase):

    def test_01___init___bad_arguments(self):
        self.assertRaisesRegex(
            TypeError,
            "".join(
                (
                    r"_PartitionRow\.__init__\(\) ",
                    r"missing 1 required positional argument: ",
                    r"'squares'$",
                )
            ),
            partition._PartitionRow,
            *(),
        )

    def test_02___init___good_arguments(self):
        ae = self.assertEqual
        item = partition._PartitionRow(all_squares.ALL_SQUARES)
        ae(
            sorted(item.__dict__),
            [
                "_full_row_names",
                "_full_rows",
                "_part_row_squares",
                "_squares",
            ],
        )
        ae(item._full_rows, set())
        ae(item._full_row_names, set())
        ae(item._part_row_squares, set())
        ae(item._squares, all_squares.ALL_SQUARES)


class HorizontalPartition(unittest.TestCase):

    def test_03_partition_horizontally(self):
        ae = self.assertEqual
        for squareset, ranks, names, parts in (
            (
                all_squares.ALL_SQUARES,
                all_squares.ALL_SQUARES,
                set("12345678"),
                set(),
            ),
            (
                set(["d4"]),
                set(),
                set(),
                set(["d4"]),
            ),
            (
                set(("d4", "a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(("a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(["2"]),
                set(["d4"]),
            ),
            (
                set(("d4", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set(),
                set(),
                set(("d4", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
            ),
            (
                set(
                    ["d4"]
                    + ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"]
                    + ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"]
                ),
                set(("a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set("2"),
                set(("d4", "b1", "b3", "b4", "b5", "b6", "b7", "b8")),
            ),
        ):
            with self.subTest(
                squareset=squareset,
                ranks=ranks,
                names=names,
                parts=parts,
            ):
                item = partition.HorizontalPartition(squareset)
                item.partition_row()
                ae(item.full_rows, ranks)
                ae(item.full_row_names, names)
                ae(item.part_row_squares, parts)


class VerticalPartition(unittest.TestCase):

    def test_04_partition_vertically(self):
        ae = self.assertEqual
        for squareset, files, names, parts in (
            (
                all_squares.ALL_SQUARES,
                all_squares.ALL_SQUARES,
                set("abcdefgh"),
                set(),
            ),
            (
                set(["d4"]),
                set(),
                set(),
                set(["d4"]),
            ),
            (
                set(("d4", "a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(),
                set(),
                set(("d4", "a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
            ),
            (
                set(("d4", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set(("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set(["b"]),
                set(["d4"]),
            ),
            (
                set(
                    ["d4"]
                    + ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"]
                    + ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"]
                ),
                set(("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set("b"),
                set(("d4", "a2", "c2", "d2", "e2", "f2", "g2", "h2")),
            ),
        ):
            with self.subTest(
                squareset=squareset,
                files=files,
                names=names,
                parts=parts,
            ):
                item = partition.VerticalPartition(squareset)
                item.partition_row()
                ae(item.full_rows, files)
                ae(item.full_row_names, names)
                ae(item.part_row_squares, parts)


class PartitionRows(unittest.TestCase):

    def test_05___init___bad_arguments(self):
        self.assertRaisesRegex(
            TypeError,
            "".join(
                (
                    r"PartitionRows\.__init__\(\) ",
                    r"missing 1 required positional argument: ",
                    r"'squares'$",
                )
            ),
            partition.PartitionRows,
            *(),
        )

    def test_06___init___good_arguments(self):
        ae = self.assertEqual
        item = partition.PartitionRows(all_squares.ALL_SQUARES)
        ae(
            sorted(item.__dict__),
            [
                "_horizontal_partition",
                "_squares",
                "_vertical_partition",
            ],
        )
        ae(item._horizontal_partition, None)
        ae(item._squares, all_squares.ALL_SQUARES)
        ae(item._vertical_partition, None)

    def test_07_partition_horizontally_and_vertically(self):
        ae = self.assertEqual
        for squareset, files, fnames, fparts, ranks, rnames, rparts in (
            (
                all_squares.ALL_SQUARES,
                all_squares.ALL_SQUARES,
                set("abcdefgh"),
                set(),
                all_squares.ALL_SQUARES,
                set("12345678"),
                set(),
            ),
            (
                set(["d4"]),
                set(),
                set(),
                set(["d4"]),
                set(),
                set(),
                set(["d4"]),
            ),
            (
                set(("d4", "a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(),
                set(),
                set(("d4", "a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(("a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(["2"]),
                set(["d4"]),
            ),
            (
                set(("d4", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set(("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set(["b"]),
                set(["d4"]),
                set(),
                set(),
                set(("d4", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
            ),
            (
                set(
                    ["d4"]
                    + ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"]
                    + ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"]
                ),
                set(("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                set("b"),
                set(("d4", "a2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set(("a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2")),
                set("2"),
                set(("d4", "b1", "b3", "b4", "b5", "b6", "b7", "b8")),
            ),
        ):
            with self.subTest(
                squareset=squareset,
                files=files,
                fnames=fnames,
                fparts=fparts,
                ranks=ranks,
                rnames=rnames,
                rparts=rparts,
            ):
                item = partition.PartitionRows(squareset)
                item.partition_horizontally_and_vertically()
                ae(item.full_files, files)
                ae(item.full_file_names, fnames)
                ae(item.part_file_squares, fparts)
                ae(item.full_ranks, ranks)
                ae(item.full_rank_names, rnames)
                ae(item.part_rank_squares, rparts)


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(_PartitionRow))
    runner().run(loader(HorizontalPartition))
    runner().run(loader(VerticalPartition))
    runner().run(loader(PartitionRows))
