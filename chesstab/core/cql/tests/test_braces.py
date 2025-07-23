# test_braces.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.braces module."""

import unittest
import re

import chessql.core.querycontainer

from .. import braces
from .. import symbol


class Braces(unittest.TestCase):

    def test_01___init__(self):
        self.assertRaisesRegex(
            TypeError,
            "".join(
                (
                    r"Symbol\.__init__\(\) ",
                    r"missing 2 required positional arguments: ",
                    r"'token' and 'master'$",
                )
            ),
            braces.Braces,
            *(),
        )

    def test_02___init__(self):
        self.assertRaisesRegex(
            symbol.SymbolError,
            "".join(
                (
                    r"Node's filter is not a ",
                    r"<class 'chessql.core.filters.BraceLeft'>$",
                )
            ),
            braces.Braces,
            *(None, None),
        )

    def test_03___init__(self):
        braceleft = chessql.core.filters.BraceLeft(
            match_=re.match(".", "a"),
            container=chessql.core.querycontainer.QueryContainer(),
        )
        item = braces.Braces(braceleft, None)
        ae = self.assertEqual
        ae(item._verify_token_is(chessql.core.filters.BraceLeft), None)


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(Braces))
