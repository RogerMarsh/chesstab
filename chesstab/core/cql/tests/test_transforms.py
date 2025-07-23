# test_transforms.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.transforms module."""

import unittest
import re

import chessql

from . import verify
from .. import transforms
from ... import cqlstatement

_orbit_element_re = re.compile(
    r"(?:<OrbitElement.+?<CompoundNode(.+?)CompoundNode>.+?OrbitElement>)",
    flags=re.DOTALL,
)
_square_list_re = re.compile(r"(?:\[((?:[a-h][1-8])*)\])")
_square_re = re.compile(r"[a-h][1-8]")


class _Transform(verify.Verify):

    def _verify_designators(self, query, targets, length):
        """Verify orbit in targets against orbit from CQL parse of query."""
        ae = self.assertEqual
        orbits = set()
        for item in _orbit_element_re.finditer(
            (self.verify_capture_cql_output(query))
        ):
            orbits.add(
                tuple(
                    frozenset(
                        i.group() for i in _square_re.finditer(s.group())
                    )
                    for s in _square_list_re.finditer(item.group())
                )
            )
        elements = set()
        elements.add(tuple(frozenset(t.designator_squares) for t in targets))
        size = set(len(t.orbit) for t in targets)
        ae(len(size), 1)
        size = size.pop()
        torbit = [t.orbit for t in targets]
        for index in range(size):
            elements.add(
                tuple(
                    frozenset(
                        item[index].full_rows.union(
                            item[index].part_row_squares
                        )
                    )
                    for item in torbit
                )
            )
        ae(len(elements), length + 1)
        ae(len(orbits), length + 1)
        ae(elements, orbits)

    def test_01___init___bad_arguments(self):
        self.assertRaisesRegex(
            TypeError,
            "".join(
                (
                    r"Symbol\.__init__\(\) ",
                    r"missing 2 required positional arguments: ",
                    r"'token' and 'master'$",
                )
            ),
            transforms._Transform,
            *(),
        )

    def test_02___init___good_arguments(self):
        ae = self.assertEqual
        for query, designators in (("_ ray(R B) K", ("_", "R", "B", "K")),):
            with self.subTest(query=query, designators=designators):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                targets = []
                for child in statement.query_evaluator.node.master.children:
                    child.node.collect_transform_targets(targets)
                for target, designator in zip(targets, designators):
                    ae(target.token.match_.group(), designator)

    def test_03_explicit_shiftvertical_generate_transforms(self):
        ae = self.assertEqual
        bfile = {"b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"}
        empty = set()
        bset = set(["b"])
        for query, designators, length, base in (
            (
                "shiftvertical{_b1-8 [d1,d8]}",
                (
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d2"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d3"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d4"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d5"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d6"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d7"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d8"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d1"])),
                    ),
                ),
                8,
                (
                    (empty, bfile, bset, empty),
                    (empty, empty, empty, set(["d1", "d8"])),
                ),
            ),
        ):
            with self.subTest(
                query=query,
                designators=designators,
                length=length,
                base=base,
            ):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                root = statement.query_evaluator.node.master
                targets = []
                for child in root.children:
                    child.node.collect_transform_targets(targets)
                shift_vertical = root.children[-1].children[-1].node
                ae(isinstance(shift_vertical, transforms.ShiftVertical), True)
                shift_vertical._generate_transforms(targets)
                ae(len(targets[0].orbit), length)
                ae(len(targets[1].orbit), length)
                ae(len(designators), length)
                for des1, des2, ans in zip(
                    targets[0].orbit, targets[1].orbit, designators
                ):
                    ans1, ans2 = ans
                    ae(des1._squares, ans1[0])
                    ae(des1.full_rows, ans1[1])
                    ae(des1.full_row_names, ans1[2])
                    ae(des1.part_row_squares, ans1[3])
                    ae(des2._squares, ans2[0])
                    ae(des2.full_rows, ans2[1])
                    ae(des2.full_row_names, ans2[2])
                    ae(des2.part_row_squares, ans2[3])
                ae(targets[0].designator_squares, base[0][1])
                ae(targets[1].designator_squares, base[1][3])
                self._verify_designators(query, targets, length)

    def test_04_explicit_shifthorizontal_generate_transforms(self):
        ae = self.assertEqual
        empty = set()
        for query, designators, length, base in (
            (
                "shifthorizontal{_b1-8 [d1,d8]}",
                (
                    (
                        (
                            empty,
                            empty,
                            empty,
                            set(
                                ("a1", "a2", "a3", "a4")
                                + ("a5", "a6", "a7", "a8")
                            ),
                        ),
                        (empty, empty, empty, set(["c1", "c8"])),
                    ),
                    (
                        (
                            empty,
                            empty,
                            empty,
                            set(
                                ("c1", "c2", "c3", "c4")
                                + ("c5", "c6", "c7", "c8")
                            ),
                        ),
                        (empty, empty, empty, set(["e1", "e8"])),
                    ),
                    (
                        (
                            empty,
                            empty,
                            empty,
                            set(
                                ("d1", "d2", "d3", "d4")
                                + ("d5", "d6", "d7", "d8")
                            ),
                        ),
                        (empty, empty, empty, set(["f1", "f8"])),
                    ),
                    (
                        (
                            empty,
                            empty,
                            empty,
                            set(
                                ("e1", "e2", "e3", "e4")
                                + ("e5", "e6", "e7", "e8")
                            ),
                        ),
                        (empty, empty, empty, set(["g1", "g8"])),
                    ),
                    (
                        (
                            empty,
                            empty,
                            empty,
                            set(
                                ("f1", "f2", "f3", "f4")
                                + ("f5", "f6", "f7", "f8")
                            ),
                        ),
                        (empty, empty, empty, set(["h1", "h8"])),
                    ),
                ),
                5,
                (
                    (
                        empty,
                        empty,
                        empty,
                        set(("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8")),
                    ),
                    (empty, empty, empty, set(["d1", "d8"])),
                ),
            ),
        ):
            with self.subTest(
                query=query,
                designators=designators,
                length=length,
                base=base,
            ):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                root = statement.query_evaluator.node.master
                targets = []
                for child in root.children:
                    child.node.collect_transform_targets(targets)
                shift_horizontal = root.children[-1].children[-1].node
                ae(
                    isinstance(shift_horizontal, transforms.ShiftHorizontal),
                    True,
                )
                shift_horizontal._generate_transforms(targets)
                ae(len(targets[0].orbit), length)
                ae(len(targets[1].orbit), length)
                ae(len(designators), length)
                for des1, des2, ans in zip(
                    targets[0].orbit, targets[1].orbit, designators
                ):
                    ans1, ans2 = ans
                    ae(des1._squares, ans1[0])
                    ae(des1.full_rows, ans1[1])
                    ae(des1.full_row_names, ans1[2])
                    ae(des1.part_row_squares, ans1[3])
                    ae(des2._squares, ans2[0])
                    ae(des2.full_rows, ans2[1])
                    ae(des2.full_row_names, ans2[2])
                    ae(des2.part_row_squares, ans2[3])
                ae(targets[0].designator_squares, base[0][3])
                ae(targets[1].designator_squares, base[1][3])
                self._verify_designators(query, targets, length)

    def test_05_explicit_shift_generate_transforms(self):
        ae = self.assertEqual
        empty = set()
        afile = {"a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8"}
        aset = set(["a"])
        bfile = {"b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"}
        bset = set(["b"])
        cfile = {"c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"}
        cset = set(["c"])
        dfile = {"d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8"}
        dset = set(["d"])
        efile = {"e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"}
        eset = set(["e"])
        ffile = {"f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"}
        fset = set(["f"])
        for query, designators, length, base in (
            (
                "shift{_b1-8 [d1,d8]}",
                (
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d2"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d3"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d4"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d5"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d6"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d7"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d8"])),
                    ),
                    (
                        (empty, bfile, bset, empty),
                        (empty, empty, empty, set(["d1"])),
                    ),
                    (
                        (empty, empty, empty, afile),
                        (empty, empty, empty, set(["c1", "c8"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c2"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c3"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c4"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c5"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c6"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c7"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c8"])),
                    ),
                    (
                        (empty, afile, aset, empty),
                        (empty, empty, empty, set(["c1"])),
                    ),
                    (
                        (empty, empty, empty, cfile),
                        (empty, empty, empty, set(["e1", "e8"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e2"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e3"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e4"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e5"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e6"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e7"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e8"])),
                    ),
                    (
                        (empty, cfile, cset, empty),
                        (empty, empty, empty, set(["e1"])),
                    ),
                    (
                        (empty, empty, empty, dfile),
                        (empty, empty, empty, set(["f1", "f8"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f2"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f3"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f4"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f5"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f6"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f7"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f8"])),
                    ),
                    (
                        (empty, dfile, dset, empty),
                        (empty, empty, empty, set(["f1"])),
                    ),
                    (
                        (empty, empty, empty, efile),
                        (empty, empty, empty, set(["g1", "g8"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g2"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g3"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g4"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g5"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g6"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g7"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g8"])),
                    ),
                    (
                        (empty, efile, eset, empty),
                        (empty, empty, empty, set(["g1"])),
                    ),
                    (
                        (empty, empty, empty, ffile),
                        (empty, empty, empty, set(["h1", "h8"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h2"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h3"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h4"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h5"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h6"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h7"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h8"])),
                    ),
                    (
                        (empty, ffile, fset, empty),
                        (empty, empty, empty, set(["h1"])),
                    ),
                ),
                53,
                (
                    (empty, empty, empty, bfile),
                    (empty, empty, empty, set(["d1", "d8"])),
                ),
            ),
        ):
            with self.subTest(
                query=query,
                designators=designators,
                length=length,
                base=base,
            ):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                root = statement.query_evaluator.node.master
                targets = []
                for child in root.children:
                    child.node.collect_transform_targets(targets)
                shift = root.children[-1].children[-1].node
                ae(isinstance(shift, transforms.Shift), True)
                shift._generate_transforms(targets)
                ae(len(targets[0].orbit), length)
                ae(len(targets[1].orbit), length)
                ae(len(designators), length)
                for des1, des2, ans in zip(
                    targets[0].orbit, targets[1].orbit, designators
                ):
                    ans1, ans2 = ans
                    ae(des1._squares, ans1[0])
                    ae(des1.full_rows, ans1[1])
                    ae(des1.full_row_names, ans1[2])
                    ae(des1.part_row_squares, ans1[3])
                    ae(des2._squares, ans2[0])
                    ae(des2.full_rows, ans2[1])
                    ae(des2.full_row_names, ans2[2])
                    ae(des2.part_row_squares, ans2[3])
                ae(targets[0].designator_squares, base[0][3])
                ae(targets[1].designator_squares, base[1][3])
                self._verify_designators(query, targets, length)

    def test_06_shiftvertical_generate_transforms(self):
        ae = self.assertEqual
        for query, length in (
            (
                "shiftvertical{_b1-8 [d1,d8]}",
                8,
            ),
            (
                "shiftvertical{_b1-8 [d1,d8] ray(c4 f7)}",
                4,
            ),
        ):
            with self.subTest(query=query, length=length):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                root = statement.query_evaluator.node.master
                targets = []
                for child in root.children:
                    child.node.collect_transform_targets(targets)
                shift_vertical = root.children[-1].children[-1].node
                ae(isinstance(shift_vertical, transforms.ShiftVertical), True)
                shift_vertical._generate_transforms(targets)
                for target in targets:
                    ae(len(target.orbit), length)
                self._verify_designators(query, targets, length)

    def test_07_shifthorizontal_generate_transforms(self):
        ae = self.assertEqual
        for query, length in (
            (
                "shifthorizontal{_b1-8 [d1,d8]}",
                5,
            ),
            (
                "shifthorizontal{_b1-8 [d1,d8] ray(c4 f7)}",
                3,
            ),
        ):
            with self.subTest(query=query, length=length):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                root = statement.query_evaluator.node.master
                targets = []
                for child in root.children:
                    child.node.collect_transform_targets(targets)
                shift_horizontal = root.children[-1].children[-1].node
                ae(
                    isinstance(shift_horizontal, transforms.ShiftHorizontal),
                    True,
                )
                shift_horizontal._generate_transforms(targets)
                for target in targets:
                    ae(len(target.orbit), length)
                self._verify_designators(query, targets, length)

    def test_08_shift_generate_transforms(self):
        ae = self.assertEqual
        for query, length in (
            (
                "shift{_b1-8 [d1,d8]}",
                53,
            ),
            (
                "shift{_b1-8 [d1,d8] ray(c4 f7)}",
                19,
            ),
        ):
            with self.subTest(query=query, length=length):
                statement = cqlstatement.CQLStatement()
                statement.prepare_cql_statement("cql()" + query)
                statement.query_evaluator.node.expand_symbol()
                root = statement.query_evaluator.node.master
                targets = []
                for child in root.children:
                    child.node.collect_transform_targets(targets)
                shift = root.children[-1].children[-1].node
                ae(isinstance(shift, transforms.Shift), True)
                shift._generate_transforms(targets)
                for target in targets:
                    ae(len(target.orbit), length)
                self._verify_designators(query, targets, length)


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(_Transform))
