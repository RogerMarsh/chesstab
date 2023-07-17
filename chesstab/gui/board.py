# board.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Classes to draw positions on chess boards.

The Board class is used to show positions in a game of chess.

Fonts such as Chess Merida, if installed, are used to represent pieces on the
board.

Character equivalents for the pieces if none of these fonts are installed:

l  King
w  Queen
t  Rook
v  Bishop
m  Knight
o  Pawn
"""

import tkinter
import tkinter.font

from solentware_bind.gui.bindings import Bindings

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
    FEN_WHITE_PIECES,
    FEN_BLACK_PIECES,
)
from pgn_read.core.squares import Squares

from . import constants
from ..core.constants import NOPIECE

_pieces = (
    NOPIECE,
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
# Chess pieces are solid unicode piece characters or the black pieces on
# light square in the four Chess fonts, Cases, Lucena, Merida and Motif,
# by Armando H Marroquin.
# The four 'Chess *' fonts were downloaded from
# www.enpassant.dk/chess/fonteng.htm
# Which set of chess pieces are used depends on the chosen font when the
# board is drawn: sometimes the characters "l", "w", "t", "v", "m", and
# "o", will appear: only to be replaced by the next action which causes
# the board to be redrawn.
_piece_chars = (
    dict(
        zip(
            _pieces,
            (
                "",
                "l",
                "w",
                "t",
                "v",
                "m",
                "o",
                "l",
                "w",
                "t",
                "v",
                "m",
                "o",
            ),
        )
    ),  # 'Chess Cases', 'Chess Lucena', 'Chess Merida', and 'ChessMotif'.
    dict(
        zip(
            _pieces,
            (
                "",
                "\u265a",
                "\u265b",
                "\u265c",
                "\u265d",
                "\u265e",
                "\u265f",
                "\u265a",
                "\u265b",
                "\u265c",
                "\u265d",
                "\u265e",
                "\u265f",
            ),
        )
    ),  # Both solid unicode chess pieces.
    dict(
        zip(
            _pieces,
            (
                "",
                "\u265a",
                "\u265b",
                "\u265c",
                "\u265d",
                "\u265e",
                "\u265f",
                "\u2654",
                "\u2655",
                "\u2656",
                "\u2657",
                "\u2658",
                "\u2659",
            ),
        )
    ),  # White solid and black outline unicode chess pieces.
    dict(
        zip(
            _pieces,
            (
                "",
                "\u2654",
                "\u2655",
                "\u2656",
                "\u2657",
                "\u2658",
                "\u2659",
                "\u265a",
                "\u265b",
                "\u265c",
                "\u265d",
                "\u265e",
                "\u265f",
            ),
        )
    ),  # White outline and black solid unicode chess pieces.
    dict(
        zip(
            _pieces,
            (
                "",
                "\u2654",
                "\u2655",
                "\u2656",
                "\u2657",
                "\u2658",
                "\u2659",
                "\u2654",
                "\u2655",
                "\u2656",
                "\u2657",
                "\u2658",
                "\u2659",
            ),
        )
    ),  # Both outline unicode chess pieces.
)
del _pieces


class Board(Bindings):
    """Chess board widget.

    Frame containing an 8x8 grid of Text widgets representing chess board
    with a font used to denote the pieces.

    """

    litecolor = constants.LITECOLOR
    darkcolor = constants.DARKCOLOR
    whitecolor = constants.WHITECOLOR
    blackcolor = constants.BLACKCOLOR
    boardfont = constants.PIECES_ON_BOARD_FONT
    _preferred_pieces = frozenset(constants.PREFERRED_PIECES)

    def __init__(self, master, boardborder=2, boardfont=None, ui=None):
        """Create board widget.

        The container catches application resizing and reconfigures
        Board to it's new size. The board then processes the Canvases to
        adjust fonts. Neither propagates geometry changes to it's master.

        """
        super().__init__()
        self.ui = ui
        if boardfont:
            self.boardfont = boardfont

        self.squares = {}
        self.boardsquares = {}
        # self.boardfont is name of named font or a font instance
        try:
            self.font = tkinter.font.nametofont(self.boardfont).copy()
        except (AttributeError, tkinter.TclError):
            self.font = self.boardfont.copy()
        self.container = tkinter.Frame(
            master=master, cnf=dict(width=0, height=0)
        )
        self.bind(
            self.container,
            "<Configure>",
            function=self.try_event(self._on_configure_container),
        )
        self.board = tkinter.Frame(
            master=self.container,
            cnf=dict(borderwidth=boardborder, relief=tkinter.SUNKEN),
        )
        board = self.board
        boardsquares = self.boardsquares
        font = self.font
        litecolor = self.litecolor
        darkcolor = self.darkcolor
        board.pack(anchor=tkinter.W)
        board.grid_propagate(False)
        for index in range(8):
            board.grid_rowconfigure(index, weight=1, uniform="r")
            board.grid_columnconfigure(index, weight=1, uniform="c")
            for file_index in range(8):
                square = index * 8 + file_index
                if (index + file_index) % 2 == 0:
                    scolor = litecolor
                else:
                    scolor = darkcolor
                boardsquares[square] = tkinter.Label(
                    board, font=font, background=scolor
                )
                boardsquares[square].grid(
                    column=file_index, row=index, sticky=tkinter.NSEW
                )

    def _configure_font_size(self, side):
        """Adjust font size after container widget has been resized."""
        self.font.configure(size=-(side * 3) // 32)

    def _on_configure_container(self, event=None):
        """Reconfigure board after container widget has been resized."""
        del event
        side = min(self.container.winfo_width(), self.container.winfo_height())
        self.board.configure(width=side, height=side)
        self._configure_font_size(side)
        self.draw_board()

    def draw_board(self):
        """Set font size to match board size and redraw pieces."""
        if self.font.actual()["family"] in self._preferred_pieces:
            piece_chars = _piece_chars[0]
        else:
            piece_chars = _piece_chars[1]
        for index, piece in self.squares.items():
            if piece in FEN_WHITE_PIECES:
                pcolor = self.whitecolor
            elif piece in FEN_BLACK_PIECES:
                pcolor = self.blackcolor
            elif piece == NOPIECE:
                if index % 2 == 0:
                    pcolor = self.darkcolor
                else:
                    pcolor = self.litecolor
            else:
                continue
            self.boardsquares[index].configure(
                foreground=pcolor, text=piece_chars[piece]
            )

    def get_top_widget(self):
        """Return top level frame of this widget."""
        return self.container

    def set_color_scheme(self):
        """Set background color for Canvas for each square."""
        for rank_index in range(8):
            for file_index in range(8):
                square = rank_index * 8 + file_index
                if (rank_index + file_index) % 2 == 0:
                    scolor = self.darkcolor
                else:
                    scolor = self.litecolor
                self.boardsquares[square].configure(background=scolor)

    def set_board(self, board):
        """Redraw widget to display the new position in board.

        board is a list of pieces where element index maps to square.

        """
        squares = self.squares
        occupied = list(squares.keys())
        squares.clear()
        square_properties = Squares.squares
        for square, piece in board.items():
            squares[square_properties[square].number] = piece.name
        for square in occupied:
            if square not in squares:
                squares[square] = NOPIECE
        self.draw_board()
        for square in occupied:
            if squares[square] == NOPIECE:
                del squares[square]
