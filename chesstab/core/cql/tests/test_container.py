# test_container.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.container module."""

import unittest

import chessql.core.querycontainer

from .. import container
from .. import symbol


class Container(unittest.TestCase):

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
            container.Container,
            *(),
        )

    def test_02___init__(self):
        self.assertRaisesRegex(
            symbol.SymbolError,
            "".join(
                (
                    r"Node's filter is not a ",
                    r"<class 'chessql.core.querycontainer.QueryContainer'>$",
                )
            ),
            container.Container,
            *(None, None),
        )

    def test_03___init__(self):
        query_container = chessql.core.querycontainer.QueryContainer(
            match_=None, container=None
        )
        item = container.Container(query_container, None)
        ae = self.assertEqual
        ae(
            item._verify_token_is(chessql.core.querycontainer.QueryContainer),
            None,
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(Container))
