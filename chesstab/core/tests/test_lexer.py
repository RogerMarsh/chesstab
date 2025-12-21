# test_lexer.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Unittests for lexer module."""

import unittest
import re

from .. import lexer


class Lexer(unittest.TestCase):
    def test_01_constants_imported_from_pgn_read(self):
        ae = self.assertEqual
        for name, value in (
            (lexer.PGN_TAG, r'\[[^"]*"(?:[^\\"]*(?:\\.[^\\"]*)*)"[^\]]*\]'),
            (
                lexer.GAME_TERMINATION,
                r"(?#Game termination)(1-0|1/2-1/2|0-1|\*)",
            ),
            (lexer.START_RAV, r"(?#Start RAV)(\()"),
            (lexer.END_RAV, r"(?#End RAV)(\))"),
            (
                lexer.NAG,
                r"".join(
                    (
                        r"(?#Numeric Annotation Glyph)",
                        r"(\$",
                        r"(?:",
                        r"(?:[1-9][0-9](?:(?=[01][-/])|[0-9]))",
                        r"|(?:[1-9](?:(?=[01][-/])|[0-9]))|",
                        r"(?:[1-9])",
                        r")",
                        r")",
                    )
                ),
            ),
            (lexer.EOL_COMMENT, r"(?#EOL comment)(;(?:[^\n]*))(?=\n)"),
            (lexer.COMMENT, r"(?#Comment)(\{[^}]*\})"),
            (lexer.RESERVED, r"(?#Reserved)(<[^>]*>)"),
        ):
            with self.subTest(name=name, value=value):
                ae(name, value)

    def test_02_constants_defined_in_lexer(self):
        ae = self.assertEqual
        for name, value in (
            (
                lexer.PAWN_MOVE,
                r"(?#Pawn move)([a-h](?:x[a-h])?[1-8](?:=[QRBN])?(?:[+#])?)",
            ),
            (lexer.CASTLES, r"(?#Castles)((?:O-O-O|O-O)(?:[+#])?)"),
            (
                lexer.PIECE_MOVE_FULL,
                "".join(
                    (
                        r"(?#Piece move full)",
                        r"([QBN][a-h][1-8][x-][a-h][1-8](?:[+#])?)",
                    )
                ),
            ),
            (
                lexer.PIECE_MOVE,
                r"(?#Piece move)([QRBN][a-h1-8]?x?[a-h][1-8](?:[+#])?)",
            ),
            (lexer.KING_MOVE, r"(?#King move)(Kx?[a-h][1-8](?:[+#])?)"),
            (lexer.MATCH_STARTER, r"(?#Match starter)([KQRBNa-h10O[{<;$])"),
            (
                lexer.ANYTHING_ELSE,
                r"(?#Anything else)([^KQRBNa-h10*O[{<;()$]+)",
            ),
            (
                lexer.GAME_PATTERN,
                "".join(
                    (
                        r'(\[[^"]*"(?:[^\\"]*(?:\\.[^\\"]*)*)"[^\]]*\])',
                        r"|",
                        r"(?#Pawn move)",
                        r"([a-h](?:x[a-h])?[1-8](?:=[QRBN])?(?:[+#])?)",
                        r"|",
                        r"(?#Piece move full)",
                        r"([QBN][a-h][1-8][x-][a-h][1-8](?:[+#])?)",
                        r"|",
                        r"(?#Piece move)",
                        r"([QRBN][a-h1-8]?x?[a-h][1-8](?:[+#])?)",
                        r"|",
                        r"(?#King move)",
                        r"(Kx?[a-h][1-8](?:[+#])?)",
                        r"|",
                        r"(?#Castles)",
                        r"((?:O-O-O|O-O)(?:[+#])?)",
                        r"|",
                        r"(?#Game termination)",
                        r"(1-0|1/2-1/2|0-1|\*)",
                        r"|",
                        r"(?#Start RAV)",
                        r"(\()",
                        r"|",
                        r"(?#End RAV)",
                        r"(\))",
                        r"|",
                        r"(?#Numeric Annotation Glyph)",
                        r"(\$",
                        r"(?:",
                        r"(?:[1-9][0-9](?:(?=[01][-/])|[0-9]))",
                        r"|(?:[1-9](?:(?=[01][-/])|[0-9]))|",
                        r"(?:[1-9])",
                        r")",
                        r")",
                        r"|",
                        r"(?#Comment)",
                        r"(\{[^}]*\})",
                        r"|",
                        r"(?#EOL comment)",
                        r"(;(?:[^\n]*))(?=\n)",
                        r"|",
                        r"(?#Reserved)",
                        r"(<[^>]*>)",
                        r"|",
                        r"(?#Match starter)",
                        r"([KQRBNa-h10O[{<;$])",
                        r"|",
                        r"(?#Anything else)",
                        r"([^KQRBNa-h10*O[{<;()$]+)",
                    )
                ),
            ),
        ):
            with self.subTest(name=name, value=value):
                ae(name, value)

    def test_03_pattern_is_valid_re(self):
        self.assertEqual(
            isinstance(re.compile(lexer.GAME_PATTERN), re.Pattern), True
        )

    def test_04_patterns_detected(self):
        ae = self.assertEqual
        pattern = re.compile(lexer.GAME_PATTERN)
        for string, lastindex in (
            ('[Tag"value"]', 1),
            ('[ Tag "value" ]', 1),
            ("a4", 2),
            ("a4+", 2),
            ("a4#", 2),
            ("a4=Q", 2),
            ("a4=Q+", 2),
            ("a4=Q#", 2),
            ("axb4", 2),
            ("axb4+", 2),
            ("axb4#", 2),
            ("axb4=Q", 2),
            ("axb4=Q+", 2),
            ("axb4=Q#", 2),
            ("Qc4-e6", 3),
            ("Qc4-e6+", 3),
            ("Qc4-e6#", 3),
            ("Qc4xe6", 3),
            ("Qc4xe6+", 3),
            ("Qc4xe6#", 3),
            ("Bc4-e6", 3),
            ("Bc4-e6+", 3),
            ("Bc4-e6#", 3),
            ("Bc4xe6", 3),
            ("Bc4xe6+", 3),
            ("Bc4xe6#", 3),
            ("Nc4-e6", 3),
            ("Nc4-e6+", 3),
            ("Nc4-e6#", 3),
            ("Nc4xe6", 3),
            ("Nc4xe6+", 3),
            ("Nc4xe6#", 3),
            ("Qd6", 4),
            ("Qd6+", 4),
            ("Qd6#", 4),
            ("Qxd6", 4),
            ("Qxd6+", 4),
            ("Qxd6#", 4),
            ("Qad6", 4),
            ("Qad6+", 4),
            ("Qad6#", 4),
            ("Qaxd6", 4),
            ("Qaxd6+", 4),
            ("Qaxd6#", 4),
            ("Q3d6", 4),
            ("Q3d6+", 4),
            ("Q3d6#", 4),
            ("Q3xd6", 4),
            ("Q3xd6+", 4),
            ("Q3xd6#", 4),
            ("Rd6", 4),
            ("Rd6+", 4),
            ("Rd6#", 4),
            ("Rxd6", 4),
            ("Rxd6+", 4),
            ("Rxd6#", 4),
            ("Rad6", 4),
            ("Rad6+", 4),
            ("Rad6#", 4),
            ("Raxd6", 4),
            ("Raxd6+", 4),
            ("Raxd6#", 4),
            ("R3d6", 4),
            ("R3d6+", 4),
            ("R3d6#", 4),
            ("R3xd6", 4),
            ("R3xd6+", 4),
            ("R3xd6#", 4),
            ("Bd6", 4),
            ("Bd6+", 4),
            ("Bd6#", 4),
            ("Bxd6", 4),
            ("Bxd6+", 4),
            ("Bxd6#", 4),
            ("Bad6", 4),
            ("Bad6+", 4),
            ("Bad6#", 4),
            ("Baxd6", 4),
            ("Baxd6+", 4),
            ("Baxd6#", 4),
            ("B3d6", 4),
            ("B3d6+", 4),
            ("B3d6#", 4),
            ("B3xd6", 4),
            ("B3xd6+", 4),
            ("B3xd6#", 4),
            ("Nd6", 4),
            ("Nd6+", 4),
            ("Nd6#", 4),
            ("Nxd6", 4),
            ("Nxd6+", 4),
            ("Nxd6#", 4),
            ("Nad6", 4),
            ("Nad6+", 4),
            ("Nad6#", 4),
            ("Naxd6", 4),
            ("Naxd6+", 4),
            ("Naxd6#", 4),
            ("N3d6", 4),
            ("N3d6+", 4),
            ("N3d6#", 4),
            ("N3xd6", 4),
            ("N3xd6+", 4),
            ("N3xd6#", 4),
            ("Kd6", 5),
            ("Kd6+", 5),
            ("Kd6#", 5),
            ("Kxd6", 5),
            ("Kxd6+", 5),
            ("Kxd6#", 5),
            ("O-O-O", 6),
            ("O-O", 6),
            ("O-O-O+", 6),
            ("O-O+", 6),
            ("O-O-O#", 6),
            ("O-O#", 6),
            ("1-0", 7),
            ("0-1", 7),
            ("1/2-1/2", 7),
            ("*", 7),
            ("(", 8),
            (")", 9),
            ("$1", 10),
            ("{comment}", 11),
            (";eol comment\n", 12),
            ("<reserved>", 13),
            ("K", 14),
            ("Q", 14),
            ("R", 14),
            ("B", 14),
            ("N", 14),
            ("a", 14),
            ("b", 14),
            ("c", 14),
            ("d", 14),
            ("e", 14),
            ("f", 14),
            ("g", 14),
            ("h", 14),
            ("1", 14),
            ("0", 14),
            ("O", 14),
            ("[", 14),
            ("{", 14),
            ("<", 14),
            (";", 14),
            ("$", 14),
            ("stop", 15),
        ):
            with self.subTest(string=string, lastindex=lastindex):
                token = pattern.match(string)
                ae(token.group(), string)
                ae(token.lastindex, lastindex)

    def test_04_patterns_detected(self):
        ae = self.assertEqual
        pattern = re.compile(lexer.GAME_PATTERN)
        for string, lastindex, found in (
            ("Rc4-e6", 4, "Rc4"),
            ("Rc4-e6+", 4, "Rc4"),
            ("Rc4-e6#", 4, "Rc4"),
            ("Rc4xe6", 4, "Rc4"),
            ("Rc4xe6+", 4, "Rc4"),
            ("Rc4xe6#", 4, "Rc4"),
            ("Kc4-e6", 5, "Kc4"),
            ("Kc4-e6+", 5, "Kc4"),
            ("Kc4-e6#", 5, "Kc4"),
            ("Kc4xe6", 5, "Kc4"),
            ("Kc4xe6+", 5, "Kc4"),
            ("Kc4xe6#", 5, "Kc4"),
            ("c4-e6", 2, "c4"),
            ("c4-e6+", 2, "c4"),
            ("c4-e6#", 2, "c4"),
            ("c4xe6", 2, "c4"),
            ("c4xe6+", 2, "c4"),
            ("c4xe6#", 2, "c4"),
            ("Kcd6", 14, "K"),
            ("Kcd6+", 14, "K"),
            ("Kcd6#", 14, "K"),
            ("Kcxd6", 14, "K"),
            ("Kcxd6+", 14, "K"),
            ("Kcxd6#", 14, "K"),
            ("K5d6", 14, "K"),
            ("K5d6+", 14, "K"),
            ("K5d6#", 14, "K"),
            ("K5xd6", 14, "K"),
            ("K5xd6+", 14, "K"),
            ("K5xd6#", 14, "K"),
            ("{comment no end", 14, "{"),
            (";eol comment no eol", 14, ";"),
            ("<reserved no end", 14, "<"),
            ("stopper", 15, "stopp"),
        ):
            with self.subTest(string=string, lastindex=lastindex, found=found):
                token = pattern.match(string)
                ae(token.group(), found)
                ae(token.lastindex, lastindex)


if __name__ == "__main__":
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(Lexer))
