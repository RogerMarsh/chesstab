# pgnupdate.py
# Copyright 2017 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Portable Game Notation (PGN) database update.

Data structures specific to ChessTab are added to the PGN class.

"""
# PGNUpdate was in the pgn package, parser module, until the introduction of
# CQL5.1 syntax to implement the partial position searches.
# Perhaps PGNUpdate always belonged in ChessTab; the explicit dependency on
# cql package along with cql dependency on pgn package for piece and board
# descriptions decided things.

from chessql.core.constants import (
    ANY_WHITE_PIECE_NAME,
    ANY_BLACK_PIECE_NAME,
    )

from pgn_read.core.constants import (
    WKING,
    WQUEEN,
    WROOK,
    WBISHOP,
    WKNIGHT,
    WPAWN,
    BKING,
    BQUEEN,
    BROOK,
    BBISHOP,
    BKNIGHT,
    BPAWN,
    IFG_TAG_SYMBOL,
    IFG_TAG_STRING_VALUE,
    MOVE_NUMBER_KEYS,
    WHITE_SIDE,
    FEN_TOMOVE,
    MAP_FEN_ORDER_TO_PGN_SQUARE_NAME,
    SQUARE_BITS,
    )
from pgn_read.core.parser import PGN

MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE = {
    WKING: ANY_WHITE_PIECE_NAME,
    WQUEEN: ANY_WHITE_PIECE_NAME,
    WROOK: ANY_WHITE_PIECE_NAME,
    WBISHOP: ANY_WHITE_PIECE_NAME,
    WKNIGHT: ANY_WHITE_PIECE_NAME,
    WPAWN: ANY_WHITE_PIECE_NAME,
    BKING: ANY_BLACK_PIECE_NAME,
    BQUEEN: ANY_BLACK_PIECE_NAME,
    BROOK: ANY_BLACK_PIECE_NAME,
    BBISHOP: ANY_BLACK_PIECE_NAME,
    BKNIGHT: ANY_BLACK_PIECE_NAME,
    BPAWN: ANY_BLACK_PIECE_NAME,
    }


class PGNUpdate(PGN):
    """Generate data structures to update a game on a database.
    
    """

    def __init__(self):
        super().__init__()
        
        '''Add structures to support update of PGN records on database'''

        self.positions = []
        self.piecesquaremoves = []
        self.piecemoves = []
        self.squaremoves = []
        self.movenumber = None
        self.variationnumber = None
        self.currentvariation = None
        self._variation = None

    def set_position_fen(self, fen=None):
        """Initialize PGN score parser with Forsyth Edwards Notation position.

        fen defaults to the starting position for a game of chess.

        """
        super().set_position_fen(fen=fen)
        if self._initial_fen:
            self.positions = []
            self.piecesquaremoves = []

            # It is assumed better to have these indicies, missing square and
            # piece components, than to process the piecesquaremoves index to
            # deduce them when required.
            self.piecemoves = []
            self.squaremoves = []

            if self.active_side == WHITE_SIDE:
                self.movenumber = [(self.fullmove_number - 1) * 2]
            else:
                self.movenumber = [self.fullmove_number * 2 - 1]
            self.variationnumber = [0]
            self._variation = ''.join(_convert_integer_to_length_hex(i)
                                      for i in self.variationnumber)

    def add_move_to_game(self):
        """Add legal move to data structures describing game.

        At present it seems better to keep this method in the PGNUpdate cless
        than requiring database specific subclasses to provide it.

        """
        super().add_move_to_game()

        # Move numbers must be n, n+1, n+2, ... with repeats for Recursive
        # Annotation Variations for a move.
        # Variation numbers must be unique for each Recursive Annotation
        # Variation, where all moves at the same level within a '()' get the
        # same unique number.
        if len(self.ravstack) != len(self.movenumber):
            while len(self.ravstack) < len(self.movenumber):
                self.movenumber.pop()
                self.variationnumber.pop()
            while len(self.ravstack) > len(self.movenumber):
                self.movenumber.append(self.movenumber[-1])
            self._variation = ''.join(_convert_integer_to_length_hex(i)
                                      for i in self.variationnumber)
        self.movenumber[-1] += 1

        movenumber = _convert_integer_to_length_hex(self.movenumber[-1])
        board = self.board
        piecesquaremoves = self.piecesquaremoves
        piecemoves = self.piecemoves
        squaremoves = self.squaremoves
        mfotpsn = MAP_FEN_ORDER_TO_PGN_SQUARE_NAME
        mp = MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE
        pieces = []
        mv = movenumber + self._variation
        for square, piece in enumerate(board):
            if piece:
                pieces.append(piece)
                #piecesquaremoves.append(mv + piece + mfotpsn[square])
                #squaremoves.append(mv + mp[piece] + mfotpsn[square])

                # If 'square piece' is better order than 'piece square'
                piecesquaremoves.append(mv + mfotpsn[square] + piece)
                squaremoves.append(mv + mfotpsn[square] + mp[piece])

        for piece in set(pieces):
            piecemoves.append(mv + piece)
        self.positions.append(
            ''.join((self.board_bitmap.to_bytes(8, 'big').decode('iso-8859-1'),
                     ''.join(pieces),
                     FEN_TOMOVE[self.active_side],
                     self.en_passant,
                     self.castling,
                     )))
        
    def collect_game_tokens(self):
        """Create snapshot of tokens extracted from PGN.

        This method is expected to be called on detection of termination token.

        """
        self.collected_game = (
            self.tags_in_order,
            {m.group(IFG_TAG_SYMBOL):m.group(IFG_TAG_STRING_VALUE)
             for m in self.tags_in_order},
            self.tokens,
            self.error_tokens,
            self.positions,
            self.piecesquaremoves,
            self.piecemoves,
            self.squaremoves)

    def _start_variation(self):
        """Delegate to superclass then append initial variation number for this
        level if it does not exist."""
        super()._start_variation()
        if len(self.ravstack) > len(self.variationnumber):
            self.variationnumber.append(0)

    def _end_variation(self):
        """Delegate to superclass then increment variation number and it's
        string form in case there is another variation at this level.  For
        example: '... Ba7 ) ( Nf4 ...'.
        """
        super()._end_variation()
        self.variationnumber[len(self.ravstack)] += 1
        self._variation = ''.join(_convert_integer_to_length_hex(i)
                                  for i in self.variationnumber)


def get_position_string(description):
    """Return position string for description of board.
    
    Format of position string is (I say bytes even though a str is returned):
    8 bytes with each set bit representing an occupied square from a8 to h1.
    n bytes corresponding to n set bits for occupied squares naming the piece
    on the square.
    1 byte value 'w' or 'b' naming side to move.
    1 or 2 bytes naming the square to which a pawn may move by capturing en
    passant. The only 1 byte value allowed is '-' meaning no en passant capture
    is possible.  The allowed 2 byte values are 'a6' to 'h6' and 'a3' to 'h3'.
    1 to 4 bytes indicating the castling moves possible if the appropriate side
    has the move.  Thus 'KQkq' means all four castling moves are possible and
    '-' indicates no casting moves are possible.  The other allowed value are
    obtained by removing one or more bytes from the original 'KQkq' without
    changing the order of those remaining.

    These values are intended as keys in an index and this structure puts keys
    for similar positions, specifically for castling and en passant differences,
    near each other.  En passant is before castling because the meaning of 'b',
    'Q', and 'q', can be decided without using the 8 byte bit pattern: piece
    name or en passant or castling or whose move.
    
    """
    board, side_to_move, castle_options, ep_square = description[:4]
    return (sum(SQUARE_BITS[e] for e, p in enumerate(board) if p
                ).to_bytes(8, 'big').decode('iso-8859-1') +
            ''.join(p for p in board) +
            FEN_TOMOVE[side_to_move] +
            ep_square +
            castle_options)

def _convert_integer_to_length_hex(i):
    """Lookup conversion table or work it out if 'i' is not in lookup table."""
    try:
        return MOVE_NUMBER_KEYS[i]
    except IndexError:
        c = hex(i)
        return str(len(c)-2) + c[2:]
