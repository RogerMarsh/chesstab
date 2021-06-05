# board.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Classes to draw positions on chess boards.

The Board class is used to show positions in a game of chess.

The PartialBoard class is used to show partial positions representing criteria
for selecting games by pattern of pieces on the board.

Fonts such as Chess Merida, if installed, are used to represent pieces on the
board.

Character equivalents for the pieces if none of these fonts are installed:

l  King
w  Queen
t  Rook
v  Bishop
m  Knight
o  Pawn

PartialBoard uses additional characters:

-  no piece
?  any piece
X  any white piece
x  any black piece
   space means any or no piece: the square is ignored when selecting games.
"""

import tkinter
import tkinter.font

from solentware_misc.gui.exceptionhandler import ExceptionHandler

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

# Characters are black pieces on light square in the four Chess fonts, Cases
# Lucena Merida and Motif, by Armando H Marroquin.
# Fonts were downloaded from www.enpassant.dk/chess/fonteng.htm
_pieces = {
    NOPIECE: "",
    FEN_WHITE_KING: "l",
    FEN_WHITE_QUEEN: "w",
    FEN_WHITE_ROOK: "t",
    FEN_WHITE_BISHOP: "v",
    FEN_WHITE_KNIGHT: "m",
    FEN_WHITE_PAWN: "o",
    FEN_BLACK_KING: "l",
    FEN_BLACK_QUEEN: "w",
    FEN_BLACK_ROOK: "t",
    FEN_BLACK_BISHOP: "v",
    FEN_BLACK_KNIGHT: "m",
    FEN_BLACK_PAWN: "o",
}


class Board(ExceptionHandler):

    """Chess board widget.

    Frame containing an 8x8 grid of Text widgets representing chess board
    with a font used to denote the pieces.

    """

    litecolor = constants.LITECOLOR
    darkcolor = constants.DARKCOLOR
    whitecolor = constants.WHITECOLOR
    blackcolor = constants.BLACKCOLOR
    boardfont = constants.PIECES_ON_BOARD_FONT

    def __init__(self, master, boardborder=2, boardfont=None, ui=None):
        """Create board widget.

        The container catches application resizing and reconfigures
        Board to it's new size. The board then processes the Canvases to
        adjust fonts. Neither propagates geometry changes to it's master.

        """
        self.ui = ui
        if boardfont:
            self.boardfont = boardfont

        self.squares = dict()
        self.boardsquares = dict()
        # self.boardfont is name of named font or a font instance
        try:
            self.font = tkinter.font.nametofont(self.boardfont).copy()
        except (AttributeError, tkinter.TclError):
            self.font = self.boardfont.copy()
        self.container = tkinter.Frame(master, width=0, height=0)
        self.container.bind(
            "<Configure>", self.try_event(self.on_configure_container)
        )
        self.board = tkinter.Frame(
            self.container, borderwidth=boardborder, relief=tkinter.SUNKEN
        )
        self.board.pack(anchor=tkinter.W)
        self.board.grid_propagate(False)
        for i in range(8):
            self.board.grid_rowconfigure(i, weight=1, uniform="r")
            self.board.grid_columnconfigure(i, weight=1, uniform="c")
            for j in range(8):
                s = i * 8 + j
                if (i + j) % 2 == 0:
                    scolor = self.litecolor
                else:
                    scolor = self.darkcolor
                self.boardsquares[s] = t = tkinter.Label(
                    self.board, font=self.font, background=scolor
                )
                t.grid(column=j, row=i, sticky=tkinter.NSEW)

    def configure_font(self, side):
        """Adjust font size after container widget has been resized."""
        self.font.configure(size=-(side * 3) // 32)

    def on_configure_container(self, event=None):
        """Reconfigure board after container widget has been resized."""
        cw = self.container.winfo_width()
        ch = self.container.winfo_height()
        side = min(cw, ch)
        self.board.configure(width=side, height=side)
        self.configure_font(side)
        self.draw_board()

    def draw_board(self):
        """Set font size to match board size and redraw pieces."""
        for i in self.squares:
            p = self.squares[i]
            if p in FEN_WHITE_PIECES:
                pcolor = self.whitecolor
            elif p in FEN_BLACK_PIECES:
                pcolor = self.blackcolor
            elif p == NOPIECE:
                if i % 2 == 0:
                    pcolor = self.darkcolor
                else:
                    pcolor = self.litecolor
            else:
                continue
            self.boardsquares[i].configure(foreground=pcolor, text=_pieces[p])

    def get_top_widget(self):
        """Return top level frame of this widget."""
        return self.container

    def set_color_scheme(self):
        """Set background color for Canvas for each square."""
        for i in range(8):
            for j in range(8):
                s = i * 8 + j
                if (i + j) % 2 == 0:
                    scolor = self.darkcolor
                else:
                    scolor = self.litecolor
                self.boardsquares[s].configure(background=scolor)

    def set_board(self, board):
        """Redraw widget to display the new position in board.

        board is a list of pieces where element index maps to square.

        """
        sq = self.squares
        occupied = list(sq.keys())
        sq.clear()
        squares = Squares.squares
        for s, p in board.items():
            sq[squares[s].number] = p.name
        for s in occupied:
            if s not in sq:
                sq[s] = NOPIECE
        self.draw_board()
        for s in occupied:
            if sq[s] == NOPIECE:
                del sq[s]


class PartialBoard(Board):

    """Partial board widget.

    Customise Board to display wildpieces.

    """

    wildpiecesfont = constants.WILDPIECES_ON_BOARD_FONT

    def __init__(self, master, **ka):
        """Create partial board widget.

        Define the font for wildpieces then delegate to superclass

        """
        # self.wildpiecesfont is name of named font or a font instance
        try:
            self.wildfont = tkinter.font.nametofont(self.wildpiecesfont).copy()
        except AttributeError:
            self.wildfont = self.wildpiecesfont.copy()
        super(PartialBoard, self).__init__(master, **ka)

    def configure_font(self, side):
        """Adjust font size after container widget has been resized."""
        self.wildfont.configure(size=-(side * 3) // 32)
        super(PartialBoard, self).configure_font(side)

    def draw_board(self):
        """Set font size to match board size and redraw pieces."""

        # Obsolescent comment because board no longer shown for partial
        # position after conversion to CQL statements.

        # Explicit setting of fonts used to get Microsoft Windows to show
        # wildpiece characters on board.
        # Possibly good fortune that wildpiece characters are shown without
        # explicit action on FreeBSD.
        # As implemented the font size used does not vary with square size.
        # Perhaps try adjust font size as well but wildpiece characters may
        # look better if smaller then pieces.

        # End obsolescent comment.

        for i in self.squares:
            font = self.font
            p = self.squares[i]
            if p in FEN_WHITE_PIECES:
                pcolor = self.whitecolor
            elif p in FEN_BLACK_PIECES:
                pcolor = self.blackcolor
            elif p == NOPIECE:
                if i % 2 == 0:
                    pcolor = self.darkcolor
                else:
                    pcolor = self.litecolor
            else:
                continue
            self.boardsquares[i].configure(
                font=font, foreground=pcolor, text=_pieces.get(p, " ")
            )
