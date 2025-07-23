# test_ray_squares.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.ray_squares module."""

import unittest

from .. import ray_squares
from .. import directions


class RaySquares(unittest.TestCase):

    def test_01_get_ray_squares_01_missing_arguments(self):
        self.assertEqual(ray_squares.get_ray_squares(), ())

    def test_01_get_ray_squares_02_too_many_arguments(self):
        self.assertEqual(
            ray_squares.get_ray_squares(None, None, None, None), ()
        )

    def test_01_get_ray_squares_03_unknown_keyword_argument(self):
        self.assertRaisesRegex(
            TypeError,
            "".join(
                (
                    r"get_ray_squares\(\) got an unexpected ",
                    r"keyword argument 'unknown'$",
                )
            ),
            ray_squares.get_ray_squares,
            *(None, None, None),
            **{"unknown": None},
        )

    def test_01_get_ray_squares_04_invalid_keyword_argument(self):
        self.assertRaisesRegex(
            KeyError,
            "True$",
            ray_squares.get_ray_squares,
            *(None, None, None),
            **{"direction_parameters": [True]},
        )

    def test_01_get_ray_squares_05_invalid_direction_key(self):
        self.assertEqual(
            ray_squares.get_ray_squares(
                None, None, None, direction_parameters=[directions.Up]
            ),
            (),
        )

    def test_01_get_ray_squares_06_default_direction_key(self):
        self.assertEqual(ray_squares.get_ray_squares(None, None), ())

    def test_01_get_ray_squares_07_unknown_ray_ends(self):
        self.assertEqual(ray_squares.get_ray_squares(None, None), ())

    def test_01_get_ray_squares_08_known_ends_not_a_ray(self):
        self.assertEqual(ray_squares.get_ray_squares("c2", "e3"), ())

    def test_01_get_ray_squares_09_ends_ray_01_northeast(self):
        self.assertEqual(
            ray_squares.get_ray_squares("c2", "e4"), ("c2", "d3", "e4")
        )

    def test_01_get_ray_squares_09_ends_ray_02_southwest(self):
        self.assertEqual(
            ray_squares.get_ray_squares("e4", "c2"), ("e4", "d3", "c2")
        )

    def test_01_get_ray_squares_09_ends_ray_03_direction_01_list_args(self):
        self.assertRaisesRegex(
            TypeError,
            "unhashable type: 'list'$",
            ray_squares.get_ray_squares,
            *(None, None, [directions.AnyDirection]),
        )

    def test_01_get_ray_squares_09_ends_ray_03_direction_02_tuple_args(self):
        self.assertEqual(
            ray_squares.get_ray_squares(
                None, None, (directions.AnyDirection,)
            ),
            (),
        )

    def test_01_get_ray_squares_10_ends_ray_04_right_direction_01_basic(self):
        self.assertEqual(
            ray_squares.get_ray_squares(
                "e4", "c2", direction_parameters=[directions.Southwest]
            ),
            ("e4", "d3", "c2"),
        )

    def test_01_get_ray_squares_10_ends_ray_04_right_direction_02_compound(
        self,
    ):
        self.assertEqual(
            ray_squares.get_ray_squares(
                "e4", "c2", direction_parameters=[directions.Diagonal]
            ),
            ("e4", "d3", "c2"),
        )

    def test_01_get_ray_squares_11_ends_ray_05_wrong_direction_01_basic(self):
        self.assertEqual(
            ray_squares.get_ray_squares(
                "e4", "c2", direction_parameters=[directions.Northeast]
            ),
            (),
        )

    def test_01_get_ray_squares_11_ends_ray_05_wrong_direction_02_compound(
        self,
    ):
        self.assertEqual(
            ray_squares.get_ray_squares(
                "e4", "c2", direction_parameters=[directions.Orthogonal]
            ),
            (),
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(RaySquares))
