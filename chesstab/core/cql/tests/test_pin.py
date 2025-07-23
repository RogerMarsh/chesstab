# test_node.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.pin module."""

import unittest
import re

import chessql

from .. import pin
from .. import symbol


class Pin(unittest.TestCase):

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
            pin.Pin,
            *(),
        )

    def test_04___init__(self):
        self.assertRaisesRegex(
            symbol.SymbolError,
            "".join(
                (
                    r"Node's filter is not a ",
                    r"<class 'chessql.core.filters.Pin'>$",
                )
            ),
            pin.Pin,
            *(None, None),
        )

    def test_07___init__(self):
        filter_ = chessql.core.filters.Pin(
            match_=re.match(".", "a"),
            container=chessql.core.querycontainer.QueryContainer(),
        )
        node = pin.Pin(filter_, filter_.container)
        ae = self.assertEqual
        ae(node._verify_token_is(chessql.core.filters.Pin), None)


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(Pin))
