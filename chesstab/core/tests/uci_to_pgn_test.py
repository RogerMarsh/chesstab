# uci_to_pgn_test.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""uci_to_pgn tests"""

import unittest

from pgn_read.core.constants import (
    FEN_WHITE_KING,
    FEN_WHITE_QUEEN,
    FEN_WHITE_ROOK,
    FEN_WHITE_BISHOP,
    FEN_WHITE_KNIGHT,
    FEN_WHITE_PAWN,
    FEN_BLACK_KING,
    FEN_BLACK_QUEEN,
    FEN_BLACK_ROOK,
    FEN_BLACK_BISHOP,
    FEN_BLACK_KNIGHT,
    FEN_BLACK_PAWN,
    PGN_QUEEN,
    PGN_ROOK,
    PGN_BISHOP,
    PGN_KNIGHT,
    PGN_PAWN,
    PGN_KING,
    )

from ..uci_to_pgn import (
    _PIECE_TO_PGN,
    _PROMOTE,
    _CASTLES,
    _CASTLEKEY,
    generate_pgn_for_uci_moves_in_position,
    )
from ..constants import NOPIECE


class ModuleAssumptions(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__assumptions(self):
        msg = 'Failure of this test invalidates all other tests'
        self.assertEqual(NOPIECE, '', msg)
        self.assertEqual(FEN_WHITE_KING, 'K', msg)
        self.assertEqual(FEN_WHITE_QUEEN, 'Q', msg)
        self.assertEqual(FEN_WHITE_ROOK, 'R', msg)
        self.assertEqual(FEN_WHITE_BISHOP, 'B', msg)
        self.assertEqual(FEN_WHITE_KNIGHT, 'N', msg)
        self.assertEqual(FEN_WHITE_PAWN, 'P', msg)
        self.assertEqual(FEN_BLACK_KING, 'k', msg)
        self.assertEqual(FEN_BLACK_QUEEN, 'q', msg)
        self.assertEqual(FEN_BLACK_ROOK, 'r', msg)
        self.assertEqual(FEN_BLACK_BISHOP, 'b', msg)
        self.assertEqual(FEN_BLACK_KNIGHT, 'n', msg)
        self.assertEqual(FEN_BLACK_PAWN, 'p', msg)
        self.assertEqual(PGN_KING, 'K', msg)
        self.assertEqual(PGN_QUEEN, 'Q', msg)
        self.assertEqual(PGN_ROOK, 'R', msg)
        self.assertEqual(PGN_BISHOP, 'B', msg)
        self.assertEqual(PGN_KNIGHT, 'N', msg)
        self.assertEqual(PGN_PAWN, '', msg)


class ModuleConstants(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test____constants(self):
        self.assertEqual(
            _PIECE_TO_PGN,
            {'K': 'K',
             'Q': 'Q',
             'R': 'R',
             'B': 'B',
             'N': 'N',
             'P': '',
             'k': 'K',
             'q': 'Q',
             'r': 'R',
             'b': 'B',
             'n': 'N',
             'p': '',
             })
        self.assertEqual(
            _PROMOTE,
            {'q': '=Q',
             'r': '=R',
             'b': '=B',
             'n': '=N',
             '': '',
             })
        self.assertEqual(
            _CASTLES,
            {'e1g1': 'O-O', 'e8g8': 'O-O', 'e1c1': 'O-O-O', 'e8c8': 'O-O-O'})
        self.assertEqual(
            _CASTLEKEY,
            {'e1g1': 'K', 'e8g8': 'k', 'e1c1': 'K', 'e8c8': 'k'})


class Generate_pgn_for_uci_illegal_moves(unittest.TestCase):

    def setUp(self):
        self.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_illegal_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position([], self.fen),
            "{'[]' cannot be a move, 'Yz0' inserted.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('', self.fen),
            "{'' is not a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'zzzz',
                'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKRRR w KQkq - 0 1'),
            ''.join((
                "{'Forsyth-Edwards Notation sets an illegal position. ",
                "Move 'Yz0' inserted.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('zzzz', self.fen),
            "{'zzzz' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('zzzz e7e5', self.fen),
            ''.join(("{'zzzz' cannot be a move, 'Yz0' inserted. Rest 'e7e5' ",
                     "ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('x9', self.fen),
            "{'x9' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_07(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('x9y0', self.fen),
            "{'x9y0' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_08(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('2e4e', self.fen),
            "{'2e4e' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_09(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f3f4', self.fen),
            ''.join(("{'f3f4' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_10(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7g8', self.fen),
            ''.join(("{'e7g8' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_11(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e2g1q', self.fen),
            "{'e2g1q' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    # *_12 to *_21 are acceptable pawn move specifications, although only *_20
    # and *_21 are legal in the position used in these tests.

    def test_generate_pgn_for_uci_illegal_moves_12(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7e6', self.fen),
            ''.join(("{'e7e6' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_13(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7e5', self.fen),
            ''.join(("{'e7e5' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_14(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7e8', self.fen),
            ''.join(("{'e7e8' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_15(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7f8', self.fen),
            ''.join(("{'e7f8' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_16(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e2e1', self.fen),
            "{'e2e1' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_17(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e2f1', self.fen),
            "{'e2f1' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_18(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7f8q', self.fen),
            ''.join(("{'e7f8q' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_19(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e2f1r', self.fen),
            "{'e2f1r' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_20(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e2e3', self.fen),
            "e3")

    def test_generate_pgn_for_uci_illegal_moves_21(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e2e4', self.fen),
            "e4")

    # *_22 to *_27 are impossible non-pawn piece moves.

    def test_generate_pgn_for_uci_illegal_moves_22(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f1f5', self.fen),
            "{'f1f5' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_23(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e8e6', self.fen),
            ''.join(("{'e8e6' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_24(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d8c6', self.fen),
            ''.join(("{'d8c6' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_25(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b1b3', self.fen),
            "{'b1b3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_26(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h1e4', self.fen),
            "{'h1e4' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_27(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h1f1', self.fen),
            "{'h1f1' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    # *_28 to *_36 are unambigous, but illegal, non-pawn piece moves.
    # In *_30, Rh3 is unambigous because h1 contains a white rook and h8 a
    # black rook; but if the pawns on h2 and h7 are removed, the PGN move
    # becomes legal whichever side has the move and remains unambiguous.
    # Finding a move to be illegal is a side-effect of disambiguating the move
    # in this function.

    def test_generate_pgn_for_uci_illegal_moves_28(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h1g1', self.fen),
            "{'h1g1' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_29(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h1h2', self.fen),
            "{'h1h2' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_30(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h1h3', self.fen),
            "{'h1h3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_31(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h1h7', self.fen),
            "{'h1h7' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_32(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d8f8', self.fen),
            ''.join(("{'d8f8' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_33(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d8c8', self.fen),
            ''.join(("{'d8c8' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    def test_generate_pgn_for_uci_illegal_moves_34(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d1d8', self.fen),
            "{'d1d8' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_35(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c1b2', self.fen),
            "{'c1b2' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_illegal_moves_36(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b8a6', self.fen),
            ''.join(("{'b8a6' does not refer to a piece of the active side, ",
                     "'Yz0' inserted. Rest '' ignored.}Yz0")))

    # *_37 is one of the four legal non-pawn moves in the start position.

    def test_generate_pgn_for_uci_illegal_moves_37(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g1f3', self.fen),
            "Nf3")


class Generate_pgn_for_uci_file_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '4r3/8/4r3/k7/4R3/K7/8/4R3 w - - 0 1'
        self.fenb = '4r3/8/4r3/k7/4R3/K7/8/4R3 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_file_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e1e2', self.fenw),
            "R1e2")

    def test_generate_pgn_for_uci_file_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e2', self.fenw),
            "R4e2")

    def test_generate_pgn_for_uci_file_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e5', self.fenw),
            "Re5")

    def test_generate_pgn_for_uci_file_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e6e5', self.fenb),
            "Re5")

    def test_generate_pgn_for_uci_file_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e6e7', self.fenb),
            "R6e7")

    def test_generate_pgn_for_uci_file_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e8e7', self.fenb),
            "R8e7")


class Generate_pgn_for_uci_rank_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/1K4k1/8/8/8/r2r1R1R/8/8 w - - 0 1'
        self.fenb = '8/1K4k1/8/8/8/r2r1R1R/8/8 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_rank_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('a3b3', self.fenb),
            "Rab3")

    def test_generate_pgn_for_uci_rank_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d3c3', self.fenb),
            "Rdc3")

    def test_generate_pgn_for_uci_rank_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d3e3', self.fenb),
            "Re3")

    def test_generate_pgn_for_uci_rank_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f3e3', self.fenw),
            "Re3")

    def test_generate_pgn_for_uci_rank_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f3g3', self.fenw),
            "Rfg3")

    def test_generate_pgn_for_uci_rank_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h3g3', self.fenw),
            "Rhg3")


class Generate_pgn_for_uci_diagonal_moves_square(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/2k4B/8/5B2/8/3b2K1/8/1b6 w - - 0 1'
        self.fenb = '8/2k4B/8/5B2/8/3b2K1/8/1b6 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_diagonal_moves_square_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b1c2', self.fenb),
            "Bbc2")

    def test_generate_pgn_for_uci_diagonal_moves_square_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d3c2', self.fenb),
            "Bdc2")

    def test_generate_pgn_for_uci_diagonal_moves_square_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d3e4', self.fenb),
            "Be4")

    def test_generate_pgn_for_uci_diagonal_moves_square_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f5e4', self.fenw),
            "Be4")

    def test_generate_pgn_for_uci_diagonal_moves_square_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f5g6', self.fenw),
            "Bfg6")

    def test_generate_pgn_for_uci_diagonal_moves_square_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('h7g6', self.fenw),
            "Bhg6")


class Generate_pgn_for_uci_diagonal_moves_stretched_square(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/2b3B1/8/8/8/2b3B1/8/1k5K w - - 0 1'
        self.fenb = '8/2b3B1/8/8/8/2b3B1/8/1k5K b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_diagonal_moves_stretched_square_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c3e5', self.fenb),
            "B3e5")

    def test_generate_pgn_for_uci_diagonal_moves_stretched_square_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3e5', self.fenw),
            "B3e5")

    def test_generate_pgn_for_uci_diagonal_moves_stretched_square_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c7e5', self.fenb),
            "B7e5")

    def test_generate_pgn_for_uci_diagonal_moves_stretched_square_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7e5', self.fenw),
            "B7e5")


class Generate_two_token_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/2B3B1/8/8/8/2B3B1/8/1k5K w - - 0 1'

    def tearDown(self):
        pass

    def test_generate_two_token_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c3e5', self.fenw),
            "Bc3e5")

    def test_generate_two_token_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3e5', self.fenw),
            "Bg3e5")

    def test_generate_two_token_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c7e5', self.fenw),
            "Bc7e5")

    def test_generate_two_token_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7e5', self.fenw),
            "Bg7e5")


class Generate_queen_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/2Q3Q1/8/8/8/2Q3Q1/8/1k5K w - - 0 1'

    def tearDown(self):
        pass

    def test_generate_queen_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c3e5', self.fenw),
            "Qc3e5")

    def test_generate_queen_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3e5', self.fenw),
            "Qg3e5")

    def test_generate_queen_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c7e5', self.fenw),
            "Qc7e5")

    def test_generate_queen_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7e5', self.fenw),
            "Qg7e5")


class Generate_bishop_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/2B3B1/8/8/8/6B1/1B6/1k5K w - - 0 1'

    def tearDown(self):
        pass

    def test_generate_bishop_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2e5', self.fenw),
            "Bbe5")

    def test_generate_bishop_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3e5', self.fenw),
            "B3e5")

    def test_generate_bishop_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c7e5', self.fenw),
            "Bce5")

    def test_generate_bishop_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7e5', self.fenw),
            "Bg7e5")


class Generate_knight_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/8/1N6/4n1n1/1N6/8/8/1k5K w - - 0 1'
        self.fenb = '8/8/1N6/4n1n1/1N6/8/8/1k5K b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_knight_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b4d5', self.fenw),
            "N4d5")

    def test_generate_knight_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6d5', self.fenw),
            "N6d5")

    def test_generate_knight_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e5f3', self.fenb),
            "Nef3")

    def test_generate_knight_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g5f3', self.fenb),
            "Ngf3")

    def test_generate_knight_move_pgn_for_uci_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6c8', self.fenw),
            "Nc8")

    def test_generate_knight_move_pgn_for_uci_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g5h3', self.fenb),
            "Nh3")


class Generate_three_queen_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenb = '8/8/2q5/8/2q1q3/8/7K/5k2 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_three_queen_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4e6', self.fenb),
            "Qc4e6")

    def test_generate_three_queen_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c6e6', self.fenb),
            "Q6e6")

    def test_generate_three_queen_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e6', self.fenb),
            "Qee6")

    def test_generate_three_queen_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4a2', self.fenb),
            "Qa2")


class Generate_three_queen_pinned_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenb = '8/8/B1q5/8/2q1q3/8/7K/5k2 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_three_queen_pinned_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4e6', self.fenb),
            "{'c4e6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_three_queen_pinned_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c6e6', self.fenb),
            "Qce6")

    def test_generate_three_queen_pinned_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e6', self.fenb),
            "Qee6")

    def test_generate_three_queen_pinned_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4a2', self.fenb),
            "{'c4a2' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")


class Generate_three_queen_block_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenb = '8/8/2q5/3r4/2q1q3/8/7K/5k2 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_three_queen_block_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4e6', self.fenb),
            "{'c4e6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_three_queen_block_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c6e6', self.fenb),
            "Qce6")

    def test_generate_three_queen_block_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e6', self.fenb),
            "Qee6")

    def test_generate_three_queen_block_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4a2', self.fenb),
            "Qa2")


class Generate_pawn_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/8/8/8/1NPPP3/8/7K/1k6 w - - 0 1'

    def tearDown(self):
        pass

    def test_generate_pawn_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4d5', self.fenw),
            "{'c4d5' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pawn_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d4d5', self.fenw),
            "d5")

    def test_generate_pawn_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4d5', self.fenw),
            "{'e4d5' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pawn_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b4d5', self.fenw),
            "Nd5")


class Generate_pawn_capture_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = '8/8/8/3p4/1NPPP3/8/7K/1k6 w - - 0 1'

    def tearDown(self):
        pass

    def test_generate_pawn_capture_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4d5', self.fenw),
            "cxd5")

    def test_generate_pawn_capture_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d4d5', self.fenw),
            "{'d4d5' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pawn_capture_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4d5', self.fenw),
            "exd5")

    def test_generate_pawn_capture_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b4d5', self.fenw),
            "Nxd5")


class Generate_castles_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'
        self.fenb = 'r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1'

    def tearDown(self):
        pass

    def test_generate_castles_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e1g1', self.fenw),
            "O-O")

    def test_generate_castles_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e8g8', self.fenb),
            "O-O")

    def test_generate_castles_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e1c1', self.fenw),
            "O-O-O")

    def test_generate_castles_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e8c8', self.fenb),
            "O-O-O")

    def test_generate_castles_pgn_for_uci_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e1f1', self.fenw),
            "Kf1")

    def test_generate_castles_pgn_for_uci_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e8f8', self.fenb),
            "Kf8")


class Generate_king_move_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = 'r2k3r/8/8/8/8/8/8/R4K1R w - - 0 1'
        self.fenb = 'r2k3r/8/8/8/8/8/8/R4K1R b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_king_move_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f1g1', self.fenw),
            "Kg1")

    def test_generate_king_move_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f1f2', self.fenw),
            "Kf2")

    def test_generate_king_move_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d8c8', self.fenb),
            "Kc8")

    def test_generate_king_move_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d8e8', self.fenb),
            "Ke8")


class Generate_three_queen_capture_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenb = '8/8/2q1P3/8/2q1q3/8/N6K/1k6 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_three_queen_capture_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4e6', self.fenb),
            "Qc4xe6")

    def test_generate_three_queen_capture_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c6e6', self.fenb),
            "Q6xe6")

    def test_generate_three_queen_capture_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e6', self.fenb),
            "Qexe6")

    def test_generate_three_queen_capture_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4a2', self.fenb),
            "Qxa2")


class Generate_three_queen_block_capture_pgn_for_uci_moves(unittest.TestCase):

    def setUp(self):
        self.fenb = '8/8/2q1P3/3r4/2q1q3/8/N6K/1k6 b - - 0 1'

    def tearDown(self):
        pass

    def test_generate_three_queen_block_capture_pgn_for_uci_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4e6', self.fenb),
            "{'c4e6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_three_queen_block_capture_pgn_for_uci_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c6e6', self.fenb),
            "Qcxe6")

    def test_generate_three_queen_block_capture_pgn_for_uci_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e4e6', self.fenb),
            "Qexe6")

    def test_generate_three_queen_block_capture_pgn_for_uci_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4a2', self.fenb),
            "Qxa2")


class Generate_pgn_for_uci_move_sequence(unittest.TestCase):

    def setUp(self):
        self.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_move_sequence_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                ''.join(('e2e4 c7c6 d2d4 d7d5 e4d5 c6d5 g1f3 g8f6 f1d3 e7e6 ',
                         'e1g1 f8e7 c2c3 e8g8')),
                self.fen),
            "e4 c6 d4 d5 exd5 cxd5 Nf3 Nf6 Bd3 e6 O-O Be7 c3 O-O")


class Generate_pgn_for_uci_white_pawn_moves(unittest.TestCase):

    def setUp(self):
        self.fenw = 'k4n2/4p1P1/1p6/2P5/5p2/6P1/1p1P4/2N4K w - - 0 60'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_white_pawn_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7h6', self.fenw),
            "{'g7h6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7g6', self.fenw),
            "{'g7g6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7g8', self.fenw),
            "{'g7g8' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7h8b', self.fenw),
            "{'g7h8b' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7f8q', self.fenw),
            "gxf8=Q")

    def test_generate_pgn_for_uci_white_pawn_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g7g8r', self.fenw),
            "g8=R")

    def test_generate_pgn_for_uci_white_pawn_moves_07(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3g4b', self.fenw),
            "{'g3g4b' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_08(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3g6', self.fenw),
            "{'g3g6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_09(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3g5', self.fenw),
            "{'g3g5' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_10(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3g4', self.fenw),
            "g4")

    def test_generate_pgn_for_uci_white_pawn_moves_11(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c5d6', self.fenw),
            "{'c5d6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_12(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c5c6', self.fenw),
            "c6")

    def test_generate_pgn_for_uci_white_pawn_moves_13(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c5b6', self.fenw),
            "cxb6")

    def test_generate_pgn_for_uci_white_pawn_moves_14(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g3f4', self.fenw),
            "gxf4")

    def test_generate_pgn_for_uci_white_pawn_moves_15(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d2d5', self.fenw),
            "{'d2d5' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_16(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d2d4', self.fenw),
            "d4")

    def test_generate_pgn_for_uci_white_pawn_moves_17(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d2d3', self.fenw),
            "d3")

    def test_generate_pgn_for_uci_white_pawn_moves_18(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d2c3', self.fenw),
            "{'d2c3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_moves_19(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('d2e3', self.fenw),
            "{'d2e3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")


class Generate_pgn_for_uci_black_pawn_moves(unittest.TestCase):

    def setUp(self):
        self.fenb = 'k4n2/4p1P1/1p6/2P5/5p2/6P1/1p1P4/2N4K b - - 0 60'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_black_pawn_moves_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2a3', self.fenb),
            "{'b2a3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2b3', self.fenb),
            "{'b2b3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2b1', self.fenb),
            "{'b2b1' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2a1b', self.fenb),
            "{'b2a1b' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_05(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2c1q', self.fenb),
            "bxc1=Q")

    def test_generate_pgn_for_uci_black_pawn_moves_06(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b2b1r', self.fenb),
            "b1=R")

    def test_generate_pgn_for_uci_black_pawn_moves_07(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6b5b', self.fenb),
            "{'b6b5b' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_08(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6b3', self.fenb),
            "{'b6b3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_09(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6b4', self.fenb),
            "{'b6b4' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_10(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6b5', self.fenb),
            "b5")

    def test_generate_pgn_for_uci_black_pawn_moves_11(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f4e3', self.fenb),
            "{'f4e3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_12(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f4f3', self.fenb),
            "f3")

    def test_generate_pgn_for_uci_black_pawn_moves_13(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('f4g3', self.fenb),
            "fxg3")

    def test_generate_pgn_for_uci_black_pawn_moves_14(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('b6c5', self.fenb),
            "bxc5")

    def test_generate_pgn_for_uci_black_pawn_moves_15(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7e4', self.fenb),
            "{'e7e4' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_16(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7e5', self.fenb),
            "e5")

    def test_generate_pgn_for_uci_black_pawn_moves_17(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7e6', self.fenb),
            "e6")

    def test_generate_pgn_for_uci_black_pawn_moves_18(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7f6', self.fenb),
            "{'e7f6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_moves_19(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('e7d6', self.fenb),
            "{'e7d6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")


class Generate_pgn_for_uci_white_pawn_en_passant(unittest.TestCase):

    def setUp(self):
        self.fenw = 'k7/8/1p6/1pPp2P1/8/8/8/7K w - d6 0 60'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_white_pawn_en_passant_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g5f6', self.fenw),
            "{'g5f6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_white_pawn_en_passant_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c5d6', self.fenw),
            "cxd6")

    def test_generate_pgn_for_uci_white_pawn_en_passant_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c5b6', self.fenw),
            "cxb6")

    def test_generate_pgn_for_uci_white_pawn_en_passant_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'c5d6',
                'k7/8/1p6/1pPp2P1/8/8/8/7K w - - 0 60'),
            "{'c5d6' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")


class Generate_pgn_for_uci_black_pawn_en_passant(unittest.TestCase):

    def setUp(self):
        self.fenb = 'k7/8/8/8/1PpP2p1/1P6/8/7K b - d3 0 60'

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_black_pawn_en_passant_01(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('g4f3', self.fenb),
            "{'g4f3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")

    def test_generate_pgn_for_uci_black_pawn_en_passant_02(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4d3', self.fenb),
            "cxd3")

    def test_generate_pgn_for_uci_black_pawn_en_passant_03(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position('c4b3', self.fenb),
            "cxb3")

    def test_generate_pgn_for_uci_black_pawn_en_passant_04(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'c4d3',
                'k7/8/8/8/1PpP2p1/1P6/8/7K b - - 0 60'),
            "{'c4d3' cannot be a move, 'Yz0' inserted. Rest '' ignored.}Yz0")


class Generate_pgn_non_castle_moves_like_e1g1(unittest.TestCase):
    # e1g1, e1c1, e8g8, and e8c8, were always treated as O-O or O-O-O until
    # the identity of the piece on e1 or e8 was taken into account.

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_generate_pgn_non_castle_move_e1g1(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'e1g1',
                '4r3/k7/8/8/8/8/7K/4R3 w - - 0 1'),
            "Rg1")

    def test_generate_pgn_non_castle_move_e1c1(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'e1c1',
                '4r3/k7/8/8/8/8/7K/4R3 w - - 0 1'),
            "Rc1")

    def test_generate_pgn_non_castle_move_e8g8(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'e8g8',
                '4r3/k7/8/8/8/8/7K/4R3 b - - 0 1'),
            "Rg8")

    def test_generate_pgn_non_castle_move_e8c8(self):
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'e8c8',
                '4r3/k7/8/8/8/8/7K/4R3 b - - 0 1'),
            "Rc8")


class Generate_pgn_for_uci_real_position(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_generate_pgn_for_uci_real_position_01(self):
        # Bf5 was treated as an illegal move because PIECE_MOVE_MAP used in one
        # place, not PIECE_CAPTURE_MAP, causing a king blockading a pawn to be
        # 'in check'.
        self.assertEqual(
            generate_pgn_for_uci_moves_in_position(
                'g4h5 f5f4 h5h6 g7h8 g3e4 g8h7 d1b3 d7f5',
                ''.join(('1r2qrk1/pn1bn1b1/1p4p1/1P2ppBp/N1Pp2P1/P2P1PNP/',
                         '6B1/1R1Q1RK1 w - - 4 21'))),
            "gxh5 f4 h6 Bh8 Ne4 Kh7 Qb3 Bf5")


if __name__ == '__main__':
    runner = unittest.TextTestRunner
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    runner().run(loader(ModuleAssumptions))
    runner().run(loader(ModuleConstants))
    runner().run(loader(Generate_pgn_for_uci_illegal_moves))
    runner().run(loader(Generate_pgn_for_uci_file_moves))
    runner().run(loader(Generate_pgn_for_uci_rank_moves))
    runner().run(loader(Generate_pgn_for_uci_diagonal_moves_square))
    runner().run(loader(Generate_pgn_for_uci_diagonal_moves_stretched_square))
    runner().run(loader(Generate_two_token_pgn_for_uci_moves))
    runner().run(loader(Generate_queen_move_pgn_for_uci_moves))
    runner().run(loader(Generate_bishop_move_pgn_for_uci_moves))
    runner().run(loader(Generate_knight_move_pgn_for_uci_moves))
    runner().run(loader(Generate_three_queen_move_pgn_for_uci_moves))
    runner().run(loader(Generate_three_queen_pinned_move_pgn_for_uci_moves))
    runner().run(loader(Generate_three_queen_block_move_pgn_for_uci_moves))
    runner().run(loader(Generate_pawn_move_pgn_for_uci_moves))
    runner().run(loader(Generate_pawn_capture_pgn_for_uci_moves))
    runner().run(loader(Generate_castles_pgn_for_uci_moves))
    runner().run(loader(Generate_king_move_pgn_for_uci_moves))
    runner().run(loader(Generate_three_queen_capture_pgn_for_uci_moves))
    runner().run(loader(Generate_three_queen_block_capture_pgn_for_uci_moves))
    runner().run(loader(Generate_pgn_for_uci_move_sequence))
    runner().run(loader(Generate_pgn_for_uci_white_pawn_moves))
    runner().run(loader(Generate_pgn_for_uci_black_pawn_moves))
    runner().run(loader(Generate_pgn_for_uci_white_pawn_en_passant))
    runner().run(loader(Generate_pgn_for_uci_black_pawn_en_passant))
    runner().run(loader(Generate_pgn_non_castle_moves_like_e1g1))
    runner().run(loader(Generate_pgn_for_uci_real_position))
