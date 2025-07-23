# test_piecedesignator.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for chesstab.core.cql.piecedesignator module."""

import unittest
import re

import chessql.core.filters
import chessql.core.querycontainer

# Warning: this module works with this import replacing the two chessql.*
# imports above because the piecedesignator import below imports the
# chessql.core.filters and chessql.core.querycontainer modules.
# This module does not work without some sort of chessql import at all.
# (Comment the two chessql imports above too, but not just one of them.)
# import chessql

from chessql.core.parser import parse

from .. import piecedesignator
from .. import symbol
from .. import all_squares


class PieceDesignator(unittest.TestCase):

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
            piecedesignator.PieceDesignator,
            *(),
        )

    def test_02___init__(self):
        self.assertRaisesRegex(
            symbol.SymbolError,
            "".join(
                (
                    r"Node's filter is not a ",
                    r"<class 'chessql.core.filters.PieceDesignator'>$",
                )
            ),
            piecedesignator.PieceDesignator,
            *(None, None),
        )

    def test_03___init__(self):
        piece_designator = chessql.core.filters.PieceDesignator(
            match_=re.match(".", "a"),
            container=chessql.core.querycontainer.QueryContainer(),
        )
        node = piecedesignator.PieceDesignator(
            piece_designator, piece_designator.container
        )
        ae = self.assertEqual
        ae(node._verify_token_is(chessql.core.filters.PieceDesignator), None)

    def test_10_expand_piece_designator_01_designators(self):
        all_any = {
            "a1": {"_a1", "Aa1", "aa1"},
            "a2": {"_a2", "Aa2", "aa2"},
            "a3": {"_a3", "Aa3", "aa3"},
            "a4": {"_a4", "Aa4", "aa4"},
            "a5": {"_a5", "Aa5", "aa5"},
            "a6": {"_a6", "Aa6", "aa6"},
            "a7": {"_a7", "Aa7", "aa7"},
            "a8": {"_a8", "Aa8", "aa8"},
            "b1": {"_b1", "Ab1", "ab1"},
            "b2": {"_b2", "Ab2", "ab2"},
            "b3": {"_b3", "Ab3", "ab3"},
            "b4": {"_b4", "Ab4", "ab4"},
            "b5": {"_b5", "Ab5", "ab5"},
            "b6": {"_b6", "Ab6", "ab6"},
            "b7": {"_b7", "Ab7", "ab7"},
            "b8": {"_b8", "Ab8", "ab8"},
            "c1": {"_c1", "Ac1", "ac1"},
            "c2": {"_c2", "Ac2", "ac2"},
            "c3": {"_c3", "Ac3", "ac3"},
            "c4": {"_c4", "Ac4", "ac4"},
            "c5": {"_c5", "Ac5", "ac5"},
            "c6": {"_c6", "Ac6", "ac6"},
            "c7": {"_c7", "Ac7", "ac7"},
            "c8": {"_c8", "Ac8", "ac8"},
            "d1": {"_d1", "Ad1", "ad1"},
            "d2": {"_d2", "Ad2", "ad2"},
            "d3": {"_d3", "Ad3", "ad3"},
            "d4": {"_d4", "Ad4", "ad4"},
            "d5": {"_d5", "Ad5", "ad5"},
            "d6": {"_d6", "Ad6", "ad6"},
            "d7": {"_d7", "Ad7", "ad7"},
            "d8": {"_d8", "Ad8", "ad8"},
            "e1": {"_e1", "Ae1", "ae1"},
            "e2": {"_e2", "Ae2", "ae2"},
            "e3": {"_e3", "Ae3", "ae3"},
            "e4": {"_e4", "Ae4", "ae4"},
            "e5": {"_e5", "Ae5", "ae5"},
            "e6": {"_e6", "Ae6", "ae6"},
            "e7": {"_e7", "Ae7", "ae7"},
            "e8": {"_e8", "Ae8", "ae8"},
            "f1": {"_f1", "Af1", "af1"},
            "f2": {"_f2", "Af2", "af2"},
            "f3": {"_f3", "Af3", "af3"},
            "f4": {"_f4", "Af4", "af4"},
            "f5": {"_f5", "Af5", "af5"},
            "f6": {"_f6", "Af6", "af6"},
            "f7": {"_f7", "Af7", "af7"},
            "f8": {"_f8", "Af8", "af8"},
            "g1": {"_g1", "Ag1", "ag1"},
            "g2": {"_g2", "Ag2", "ag2"},
            "g3": {"_g3", "Ag3", "ag3"},
            "g4": {"_g4", "Ag4", "ag4"},
            "g5": {"_g5", "Ag5", "ag5"},
            "g6": {"_g6", "Ag6", "ag6"},
            "g7": {"_g7", "Ag7", "ag7"},
            "g8": {"_g8", "Ag8", "ag8"},
            "h1": {"_h1", "Ah1", "ah1"},
            "h2": {"_h2", "Ah2", "ah2"},
            "h3": {"_h3", "Ah3", "ah3"},
            "h4": {"_h4", "Ah4", "ah4"},
            "h5": {"_h5", "Ah5", "ah5"},
            "h6": {"_h6", "Ah6", "ah6"},
            "h7": {"_h7", "Ah7", "ah7"},
            "h8": {"_h8", "Ah8", "ah8"},
            "": {"_", "A", "a"},
        }
        all_empty = {
            "a1": set(["_a1"]),
            "a2": set(["_a2"]),
            "a3": set(["_a3"]),
            "a4": set(["_a4"]),
            "a5": set(["_a5"]),
            "a6": set(["_a6"]),
            "a7": set(["_a7"]),
            "a8": set(["_a8"]),
            "b1": set(["_b1"]),
            "b2": set(["_b2"]),
            "b3": set(["_b3"]),
            "b4": set(["_b4"]),
            "b5": set(["_b5"]),
            "b6": set(["_b6"]),
            "b7": set(["_b7"]),
            "b8": set(["_b8"]),
            "c1": set(["_c1"]),
            "c2": set(["_c2"]),
            "c3": set(["_c3"]),
            "c4": set(["_c4"]),
            "c5": set(["_c5"]),
            "c6": set(["_c6"]),
            "c7": set(["_c7"]),
            "c8": set(["_c8"]),
            "d1": set(["_d1"]),
            "d2": set(["_d2"]),
            "d3": set(["_d3"]),
            "d4": set(["_d4"]),
            "d5": set(["_d5"]),
            "d6": set(["_d6"]),
            "d7": set(["_d7"]),
            "d8": set(["_d8"]),
            "e1": set(["_e1"]),
            "e2": set(["_e2"]),
            "e3": set(["_e3"]),
            "e4": set(["_e4"]),
            "e5": set(["_e5"]),
            "e6": set(["_e6"]),
            "e7": set(["_e7"]),
            "e8": set(["_e8"]),
            "f1": set(["_f1"]),
            "f2": set(["_f2"]),
            "f3": set(["_f3"]),
            "f4": set(["_f4"]),
            "f5": set(["_f5"]),
            "f6": set(["_f6"]),
            "f7": set(["_f7"]),
            "f8": set(["_f8"]),
            "g1": set(["_g1"]),
            "g2": set(["_g2"]),
            "g3": set(["_g3"]),
            "g4": set(["_g4"]),
            "g5": set(["_g5"]),
            "g6": set(["_g6"]),
            "g7": set(["_g7"]),
            "g8": set(["_g8"]),
            "h1": set(["_h1"]),
            "h2": set(["_h2"]),
            "h3": set(["_h3"]),
            "h4": set(["_h4"]),
            "h5": set(["_h5"]),
            "h6": set(["_h6"]),
            "h7": set(["_h7"]),
            "h8": set(["_h8"]),
            "": set(["_"]),
        }
        all_white_n = {  # Just to avoid the name 'all_N'.
            "a1": set(["Na1"]),
            "a2": set(["Na2"]),
            "a3": set(["Na3"]),
            "a4": set(["Na4"]),
            "a5": set(["Na5"]),
            "a6": set(["Na6"]),
            "a7": set(["Na7"]),
            "a8": set(["Na8"]),
            "b1": set(["Nb1"]),
            "b2": set(["Nb2"]),
            "b3": set(["Nb3"]),
            "b4": set(["Nb4"]),
            "b5": set(["Nb5"]),
            "b6": set(["Nb6"]),
            "b7": set(["Nb7"]),
            "b8": set(["Nb8"]),
            "c1": set(["Nc1"]),
            "c2": set(["Nc2"]),
            "c3": set(["Nc3"]),
            "c4": set(["Nc4"]),
            "c5": set(["Nc5"]),
            "c6": set(["Nc6"]),
            "c7": set(["Nc7"]),
            "c8": set(["Nc8"]),
            "d1": set(["Nd1"]),
            "d2": set(["Nd2"]),
            "d3": set(["Nd3"]),
            "d4": set(["Nd4"]),
            "d5": set(["Nd5"]),
            "d6": set(["Nd6"]),
            "d7": set(["Nd7"]),
            "d8": set(["Nd8"]),
            "e1": set(["Ne1"]),
            "e2": set(["Ne2"]),
            "e3": set(["Ne3"]),
            "e4": set(["Ne4"]),
            "e5": set(["Ne5"]),
            "e6": set(["Ne6"]),
            "e7": set(["Ne7"]),
            "e8": set(["Ne8"]),
            "f1": set(["Nf1"]),
            "f2": set(["Nf2"]),
            "f3": set(["Nf3"]),
            "f4": set(["Nf4"]),
            "f5": set(["Nf5"]),
            "f6": set(["Nf6"]),
            "f7": set(["Nf7"]),
            "f8": set(["Nf8"]),
            "g1": set(["Ng1"]),
            "g2": set(["Ng2"]),
            "g3": set(["Ng3"]),
            "g4": set(["Ng4"]),
            "g5": set(["Ng5"]),
            "g6": set(["Ng6"]),
            "g7": set(["Ng7"]),
            "g8": set(["Ng8"]),
            "h1": set(["Nh1"]),
            "h2": set(["Nh2"]),
            "h3": set(["Nh3"]),
            "h4": set(["Nh4"]),
            "h5": set(["Nh5"]),
            "h6": set(["Nh6"]),
            "h7": set(["Nh7"]),
            "h8": set(["Nh8"]),
            "": set(["N"]),
        }
        for text, answer in (
            ("Rd4", {"d4": set(["Rd4"]), "": set(["Rd4"])}),
            ("[RB]d4", {"d4": {"Rd4", "Bd4"}, "": {"Rd4", "Bd4"}}),
            ("N", all_white_n),
            (
                "Nc-e3-5",
                {
                    "c3": set(["Nc3"]),
                    "c4": set(["Nc4"]),
                    "c5": set(["Nc5"]),
                    "d3": set(["Nd3"]),
                    "d4": set(["Nd4"]),
                    "d5": set(["Nd5"]),
                    "e3": set(["Ne3"]),
                    "e4": set(["Ne4"]),
                    "e5": set(["Ne5"]),
                    "": set(
                        [
                            "Nc3",
                            "Nc4",
                            "Nc5",
                            "Nd3",
                            "Nd4",
                            "Nd5",
                            "Ne3",
                            "Ne4",
                            "Ne5",
                        ]
                    ),
                },
            ),
            ("_", all_empty),
            (".", all_any),
            ("♜d4", {"d4": set(["rd4"]), "": set(["rd4"])}),
            ("♜♗d4", {"d4": {"rd4", "Bd4"}, "": {"rd4", "Bd4"}}),
            ("♘", all_white_n),
            (
                "♘c-e3-5",
                {
                    "c3": set(["Nc3"]),
                    "c4": set(["Nc4"]),
                    "c5": set(["Nc5"]),
                    "d3": set(["Nd3"]),
                    "d4": set(["Nd4"]),
                    "d5": set(["Nd5"]),
                    "e3": set(["Ne3"]),
                    "e4": set(["Ne4"]),
                    "e5": set(["Ne5"]),
                    "": set(
                        [
                            "Nc3",
                            "Nc4",
                            "Nc5",
                            "Nd3",
                            "Nd4",
                            "Nd5",
                            "Ne3",
                            "Ne4",
                            "Ne5",
                        ]
                    ),
                },
            ),
            ("□", all_empty),
            ("▦", all_any),
        ):
            with self.subTest(text=text, answer=answer):
                con = parse("cql()" + text)
                node = piecedesignator.PieceDesignator(
                    con.children[-1].children[-1], con
                )
                node.parse()
                node.expand_piece_designator()
                self.assertEqual(len(node.designator_set), len(answer))
                self.assertEqual(node.designator_set, answer)

    def test_10_expand_piece_designator_02_squares(self):
        for text, answer in (
            ("Rd4", set(["d4"])),
            ("[RB]d4", set(["d4"])),
            ("N", all_squares.ALL_SQUARES),
            (
                "Nc-e3-5",
                {"c3", "c4", "c5", "d3", "d4", "d5", "e3", "e4", "e5"},
            ),
            ("_", all_squares.ALL_SQUARES),
            (".", all_squares.ALL_SQUARES),
            ("♜d4", set(["d4"])),
            ("♜♗d4", set(["d4"])),
            ("♘", all_squares.ALL_SQUARES),
            (
                "♘c-e3-5",
                {"c3", "c4", "c5", "d3", "d4", "d5", "e3", "e4", "e5"},
            ),
            ("□", all_squares.ALL_SQUARES),
            ("▦", all_squares.ALL_SQUARES),
        ):
            with self.subTest(text=text, answer=answer):
                con = parse("cql()" + text)
                node = piecedesignator.PieceDesignator(
                    con.children[-1].children[-1], con
                )
                node.parse()
                node.expand_piece_designator()
                self.assertEqual(node.designator_squares, answer)

    def test_11_get_pieces(self):
        for text, answer in (
            ("Rd4", {"R"}),
            ("[RB]d4", {"R", "B"}),
            ("N", {"N"}),
            ("Nc-e3-5", {"N"}),
            ("_", {"_"}),
            (".", {"_", "A", "a"}),
            ("♜d4", {"r"}),
            ("♖♗d4", {"R", "B"}),
            ("♘", {"N"}),
            ("♘c-e3-5", {"N"}),
            ("□", {"_"}),
            ("▦", {"_", "A", "a"}),
        ):
            with self.subTest(text=text, answer=answer):
                con = parse("cql()" + text)
                node = piecedesignator.PieceDesignator(
                    con.children[-1].children[-1], con
                )
                node.parse()
                pieces = node.get_pieces()
                self.assertEqual(set(pieces), answer)

    def test_13_get_squares(self):
        for text, answer in (
            ("Rd4", ["d4"]),
            ("[RB]d4", ["d4"]),
            ("N", [""]),
            ("Nc-e3-5", ["c-e3-5"]),
            ("_", [""]),
            (".", ["a-h1-8"]),
            ("♜d4", ["d4"]),
            ("♖♗d4", ["d4"]),
            ("♘", [""]),
            ("♘c-e3-5", ["c-e3-5"]),
            ("□", [""]),
            ("▦", ["a-h1-8"]),
            ("B[d-e4-5,b7,g-h2,a2-3]", ["d-e4-5", "b7", "g-h2", "a2-3"]),
        ):
            with self.subTest(text=text, answer=answer):
                con = parse("cql()" + text)
                node = piecedesignator.PieceDesignator(
                    con.children[-1].children[-1], con
                )
                node.parse()
                squares = node.get_squares()
                self.assertEqual(squares, answer)


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(PieceDesignator))
