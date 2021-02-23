# uci_to_pgn.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Convert UCI Chess Engine moves to PGN.

UCI chess engines give moves as <from square><to square> and the easiest way of
handling these, given the existing PGN parser, is translate to PGN.

generate_pgn_for_uci_moves_in_position() generates the legal unambiguous PGN
description of a sequence of UCI Chess Engine move for the position it refers
to.

'Qd1f3' is always unambiguous but is the legal unambiguous description only if
more than two queens of the side with the move can legally move to 'f3'. 'Qf3'
is usually the only legal PGN description because the starting position for a
game has one queen per side. 'Qf3' is not necessarily a legal move.

"""
import re

from pgn_read.core.parser import PGNMove
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
    PGN_KING,
    PGN_QUEEN,
    PGN_ROOK,
    PGN_BISHOP,
    PGN_KNIGHT,
    PGN_PAWN,
    SPACE,
    NOPIECE,
    MAP_PGN_SQUARE_NAME_TO_FEN_ORDER,
    CAPTURE_MOVE,
    PLAIN_MOVE,
    PIECE_CAPTURE_MAP,
    PIECE_MOVE_MAP,
    SQUARE_BITS,
    SIDE_KING,
    OTHER_SIDE,
    GAPS,
    )

_PIECE_TO_PGN = {
    WKING: PGN_KING,
    WQUEEN: PGN_QUEEN,
    WROOK: PGN_ROOK,
    WBISHOP: PGN_BISHOP,
    WKNIGHT: PGN_KNIGHT,
    WPAWN: PGN_PAWN,
    BKING: PGN_KING,
    BQUEEN: PGN_QUEEN,
    BROOK: PGN_ROOK,
    BBISHOP: PGN_BISHOP,
    BKNIGHT: PGN_KNIGHT,
    BPAWN: PGN_PAWN,
    }
_PROMOTE = {
    PGN_QUEEN.lower(): ''.join(('=', PGN_QUEEN)),
    PGN_ROOK.lower(): ''.join(('=', PGN_ROOK)),
    PGN_BISHOP.lower(): ''.join(('=', PGN_BISHOP)),
    PGN_KNIGHT.lower(): ''.join(('=', PGN_KNIGHT)),
    '': '',
    }
_PROMOTE_PIECE = {
    ''.join(('8', PGN_QUEEN.lower())): WQUEEN,
    ''.join(('8', PGN_ROOK.lower())): WROOK,
    ''.join(('8', PGN_BISHOP.lower())): WBISHOP,
    ''.join(('8', PGN_KNIGHT.lower())): WKNIGHT,
    ''.join(('1', PGN_QUEEN.lower())): BQUEEN,
    ''.join(('1', PGN_ROOK.lower())): BROOK,
    ''.join(('1', PGN_BISHOP.lower())): BBISHOP,
    ''.join(('1', PGN_KNIGHT.lower())): BKNIGHT,
    }
_CASTLES = {'e1g1': 'O-O', 'e8g8': 'O-O', 'e1c1': 'O-O-O', 'e8c8': 'O-O-O'}
_CASTLEKEY = {
    'e1g1': WKING,
    'e8g8': BKING,
    'e1c1': WKING,
    'e8c8': BKING}
_FEN_SPACES = {
    '1': SPACE,
    '2': SPACE * 2,
    '3': SPACE * 3,
    '4': SPACE * 4,
    '5': SPACE * 5,
    '6': SPACE * 6,
    '7': SPACE * 7,
    '8': SPACE * 8,
    }

re_move = re.compile(''.join(('^',
                              '([a-h][1-8])',
                              '([a-h][1-8])',
                              '([qrbn]?)',
                              '$')))


def generate_pgn_for_uci_moves_in_position(moves, fen):
    """Return PGN-style movetext and update position for unambiguous moves.

    """
    pgn = PGNMove()
    text = []
    try:
        moves = moves.split()
    except:
        return ''.join(
            ("{'",
             str(moves),
             "' cannot be a move, 'Yz0' inserted.}Yz0"))
    if not moves:
        return "{'' is not a move, 'Yz0' inserted. Rest '' ignored.}Yz0"
    pgn.set_position_fen(fen)
    if not pgn._initial_fen:
        return ''.join((
            "{'Forsyth-Edwards Notation sets an illegal position. ",
            "Move 'Yz0' inserted.}Yz0"))
    for count, move in enumerate(moves):
        g = re_move.match(move)
        if not g:
            text.append(''.join(
                ("{'",
                 str(move),
                 "' cannot be a move, 'Yz0' inserted. Rest '",
                 ' '.join(moves[count+1:]),
                 "' ignored.}Yz0")))
            break
        from_square, to_square, promote_to = g.groups()
        fen_from_square = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[from_square]
        fen_to_square = MAP_PGN_SQUARE_NAME_TO_FEN_ORDER[to_square]
        gap = GAPS[fen_from_square][fen_to_square]

        # from_square must contain a piece belonging to side with the move.
        if fen_from_square not in pgn.occupied_squares[pgn.active_side]:
            text.append(''.join(
                ("{'",
                 str(move),
                 "' does not refer to a piece of the active side, ",
                 "'Yz0' inserted. Rest '",
                 ' '.join(moves[count+1:]),
                 "' ignored.}Yz0")))
            break

        piece = _PIECE_TO_PGN[pgn.board[fen_from_square]]
        promote_to = _PROMOTE[promote_to]

        # What about illegal moves specified in e2f5 format where the
        # constructed PGN move happens to be legal.

        # Castles is treated as a king move of two squares, otherwise illegal.
        if (move in _CASTLES and
            pgn.board[fen_from_square] == _CASTLEKEY.get(move)):
            pgn_move_descriptions = _CASTLES[move],

        # Pawns have moving rules different from the other pieces.
        elif piece == PGN_PAWN:

            # The distinction petween normal captures, to_square occupied, and
            # en-passant captures, to_square empty, is left to the PGN parser.
            if from_square[0] == to_square[0]:
                takes = PLAIN_MOVE
                move_map = PIECE_MOVE_MAP[pgn.board[fen_from_square]]
            else:
                takes = CAPTURE_MOVE
                move_map = PIECE_CAPTURE_MAP[pgn.board[fen_from_square]]

            # Pawn must be able to make the move: nothing in the way.
            if gap & pgn.board_bitmap or (not move_map[fen_to_square] &
                                          SQUARE_BITS[fen_from_square]):
                text.append(''.join(
                    ("{'",
                     str(move),
                     "' cannot be a move, 'Yz0' inserted. Rest '",
                     ' '.join(moves[count+1:]),
                     "' ignored.}Yz0")))
                break

            # Pawn must not be promoted to ranks othen than 1 or 8.
            if promote_to:
                if to_square[1] not in '18':
                    text.append(''.join(
                        ("{'",
                         str(move),
                         "' cannot be a move, 'Yz0' inserted. Rest '",
                         ' '.join(moves[count+1:]),
                         "' ignored.}Yz0")))
                    break

            # A pawn move description is unambigous so validation that 'move'
            # does not leave king in check is left to PGN parser.

            if takes == PLAIN_MOVE:
                pgn_move_descriptions = ''.join((to_square, promote_to)),
            else:
                pgn_move_descriptions = (
                    ''.join((from_square[0], takes, to_square, promote_to)),
                    )
        
        else:
            if pgn.board[fen_to_square] != NOPIECE:
                takes = CAPTURE_MOVE
                move_map = PIECE_CAPTURE_MAP[pgn.board[fen_from_square]]
            else:
                takes = PLAIN_MOVE
                move_map = PIECE_MOVE_MAP[pgn.board[fen_from_square]]

            # Piece must be able to make the move: nothing in the way.
            if gap & pgn.board_bitmap or (not move_map[fen_to_square] &
                                          SQUARE_BITS[fen_from_square]):
                text.append(''.join(
                    ("{'",
                     str(move),
                     "' cannot be a move, 'Yz0' inserted. Rest '",
                     ' '.join(moves[count+1:]),
                     "' ignored.}Yz0")))
                break

            # If more than one piece of a type is able to move to a square but
            # some of them are pinned against their king, the PGN description
            # of the move must not include the elements of from_square usually
            # given to distinguish the moves.
            # The piece on from_square must not be pinned against it's king
            # unless it's move does not break the pin.
            if len(pgn.piece_locations[pgn.board[fen_from_square]]) > 1:
                for active_king_square in pgn.piece_locations[
                    SIDE_KING[pgn.active_side]]:
                    pass # bind active_king_square without pop() and add()
                inactive_pieces = pgn.occupied_squares[
                    OTHER_SIDE[pgn.active_side]].copy()
                inactive_pieces.discard(fen_to_square)
                bitmap = pgn.board_bitmap & (pgn.board_bitmap ^
                                             SQUARE_BITS[fen_from_square])
                bitmap |= SQUARE_BITS[fen_to_square]
                gk = GAPS[active_king_square]
                for square in inactive_pieces:
                    if (not gk[square] & bitmap and
                        PIECE_CAPTURE_MAP[pgn.board[square]
                                          ][active_king_square] &
                        SQUARE_BITS[square]):
                        text.append(''.join(
                            ("{'",
                             str(move),
                             "' cannot be a move, 'Yz0' inserted. Rest '",
                             ' '.join(moves[count+1:]),
                             "' ignored.}Yz0")))
                        pinned = True
                        break
                else:
                    pinned = False
                if pinned:
                    break

            pgn_move_descriptions = (
                ''.join((piece, takes, to_square, promote_to)),
                ''.join((piece, from_square[0], takes, to_square, promote_to)),
                ''.join((piece, from_square[1], takes, to_square, promote_to)),
                ''.join((piece, from_square, takes, to_square, promote_to)),
                )

        # Use the first PGN move description accepted by PGN parser.
        for pgn_move in pgn_move_descriptions:
            ravstack = pgn.ravstack[-1]
            t = pgn.get_first_pgn_token(pgn_move)
            if not t:
                text.append(''.join(
                    ("{'",
                     str(move),
                     "' cannot be a move, 'Yz0' inserted. Rest '",
                     ' '.join(moves[count+1:]),
                     "' ignored.}Yz0")))
                break
            if not pgn.error_tokens:
                text.append(pgn_move)
                break
            pgn.error_tokens = []
            pgn.ravstack[-1] = ravstack
            pgn.reset_position(ravstack[-1])
        else:
            text.append(''.join(
                ("{'",
                 str(move),
                 "' cannot be a move, 'Yz0' inserted. Rest '",
                 ' '.join(moves[count+1:]),
                 "' ignored.}Yz0")))
            break

    return ' '.join(text)
