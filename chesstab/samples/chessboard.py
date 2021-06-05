# chessboard.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Demonstrate chess board class and methods to draw position on board."""


if __name__ == "__main__":

    import tkinter

    from pgn_read.core.piece import Piece
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
    )

    from ..gui import fonts
    from ..gui.board import Board
    from ..core.constants import NOPIECE

    root = tkinter.Tk()
    root.wm_title("Demonstrate Board")
    f = fonts.make_chess_fonts(root, preferred_pieces=("Chess Lucena",))
    b = Board(root, boardborder=10)
    del f
    b.get_top_widget().pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    b.get_top_widget().pack_propagate(False)
    b.set_board(
        {
            "a8": Piece(FEN_BLACK_ROOK, "a8"),
            "b8": Piece(FEN_BLACK_KNIGHT, "b8"),
            "c8": Piece(FEN_BLACK_BISHOP, "c8"),
            "d8": Piece(FEN_BLACK_QUEEN, "d8"),
            "e8": Piece(FEN_BLACK_KING, "e8"),
            "f8": Piece(FEN_BLACK_BISHOP, "f8"),
            "g8": Piece(FEN_BLACK_KNIGHT, "g8"),
            "h8": Piece(FEN_BLACK_ROOK, "h8"),
            "a7": Piece(FEN_BLACK_PAWN, "a7"),
            "b7": Piece(FEN_BLACK_PAWN, "b7"),
            "c7": Piece(FEN_BLACK_PAWN, "c7"),
            "d7": Piece(FEN_BLACK_PAWN, "d7"),
            "e7": Piece(FEN_BLACK_PAWN, "e7"),
            "f7": Piece(FEN_BLACK_PAWN, "f7"),
            "g7": Piece(FEN_BLACK_PAWN, "g7"),
            "h7": Piece(FEN_BLACK_PAWN, "h7"),
            "a2": Piece(FEN_WHITE_PAWN, "a2"),
            "b2": Piece(FEN_WHITE_PAWN, "b2"),
            "c2": Piece(FEN_WHITE_PAWN, "c2"),
            "d2": Piece(FEN_WHITE_PAWN, "d2"),
            "e2": Piece(FEN_WHITE_PAWN, "e2"),
            "f2": Piece(FEN_WHITE_PAWN, "f2"),
            "g2": Piece(FEN_WHITE_PAWN, "g2"),
            "h2": Piece(FEN_WHITE_PAWN, "h2"),
            "a1": Piece(FEN_WHITE_ROOK, "a1"),
            "b1": Piece(FEN_WHITE_KNIGHT, "b1"),
            "c1": Piece(FEN_WHITE_BISHOP, "c1"),
            "d1": Piece(FEN_WHITE_QUEEN, "d1"),
            "e1": Piece(FEN_WHITE_KING, "e1"),
            "f1": Piece(FEN_WHITE_BISHOP, "f1"),
            "g1": Piece(FEN_WHITE_KNIGHT, "g1"),
            "h1": Piece(FEN_WHITE_ROOK, "h1"),
        }
    )
    del b
    root.pack_propagate(False)
    root.mainloop()
