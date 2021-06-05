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
    PGN_KING,
    PGN_QUEEN,
    PGN_ROOK,
    PGN_BISHOP,
    PGN_KNIGHT,
    PGN_PAWN,
    OTHER_SIDE,
    FEN_WHITE_PIECES,
    FEN_BLACK_PIECES,
    FEN_WHITE_ACTIVE,
    FEN_BLACK_ACTIVE,
    PGN_CAPTURE_MOVE,
)
from pgn_read.core.parser import add_token_to_game

from .pgn import GameMove
from .constants import (
    NOPIECE,
    FEN_CONTEXT,
)

_PIECE_TO_PGN = {
    FEN_WHITE_KING: PGN_KING,
    FEN_WHITE_QUEEN: PGN_QUEEN,
    FEN_WHITE_ROOK: PGN_ROOK,
    FEN_WHITE_BISHOP: PGN_BISHOP,
    FEN_WHITE_KNIGHT: PGN_KNIGHT,
    FEN_WHITE_PAWN: PGN_PAWN,
    FEN_BLACK_KING: PGN_KING,
    FEN_BLACK_QUEEN: PGN_QUEEN,
    FEN_BLACK_ROOK: PGN_ROOK,
    FEN_BLACK_BISHOP: PGN_BISHOP,
    FEN_BLACK_KNIGHT: PGN_KNIGHT,
    FEN_BLACK_PAWN: PGN_PAWN,
}
_PROMOTE = {
    PGN_QUEEN.lower(): "".join(("=", PGN_QUEEN)),
    PGN_ROOK.lower(): "".join(("=", PGN_ROOK)),
    PGN_BISHOP.lower(): "".join(("=", PGN_BISHOP)),
    PGN_KNIGHT.lower(): "".join(("=", PGN_KNIGHT)),
    "": "",
}
_CASTLES = {"e1g1": "O-O", "e8g8": "O-O", "e1c1": "O-O-O", "e8c8": "O-O-O"}
_CASTLEKEY = {
    "e1g1": FEN_WHITE_KING,
    "e8g8": FEN_BLACK_KING,
    "e1c1": FEN_WHITE_KING,
    "e8c8": FEN_BLACK_KING,
}
_ACTIVE_PIECES = {
    FEN_WHITE_ACTIVE: FEN_WHITE_PIECES,
    FEN_BLACK_ACTIVE: FEN_BLACK_PIECES,
}

re_move = re.compile(
    "".join(("^", "([a-h][1-8])", "([a-h][1-8])", "([qrbn]?)", "$"))
)


def generate_pgn_for_uci_moves_in_position(moves, fen):
    """Return PGN-style movetext and update position for unambiguous moves."""
    game = GameMove()
    piece_placement_data = game._piece_placement_data
    text = []
    try:
        moves = moves.split()
    except:
        return "".join(
            ("{'", str(moves), "' cannot be a move, 'Yz0' inserted.}Yz0")
        )
    if not moves:
        return "{'' is not a move, 'Yz0' inserted. Rest '' ignored.}Yz0"
    tagtext = fen.join(FEN_CONTEXT)
    match_end = add_token_to_game(tagtext, game)
    match_end = add_token_to_game(tagtext, game, pos=match_end)
    if not game.set_initial_position():
        return "".join(
            (
                "{'Forsyth-Edwards Notation sets an illegal position. ",
                "Move 'Yz0' inserted.}Yz0",
            )
        )
    for count, move in enumerate(moves):
        g = re_move.match(move)
        if not g:
            text.append(
                "".join(
                    (
                        "{'",
                        str(move),
                        "' cannot be a move, 'Yz0' inserted. Rest '",
                        " ".join(moves[count + 1 :]),
                        "' ignored.}Yz0",
                    )
                )
            )
            break
        from_square, to_square, promote_to = g.groups()

        # from_square must contain a piece belonging to side with the move.
        if from_square not in piece_placement_data:
            text.append(
                "".join(
                    (
                        "{'",
                        str(move),
                        "' does not refer to a piece of the active side, ",
                        "'Yz0' inserted. Rest '",
                        " ".join(moves[count + 1 :]),
                        "' ignored.}Yz0",
                    )
                )
            )
            break
        piece = piece_placement_data[from_square].name
        if piece not in _ACTIVE_PIECES[game._active_color]:
            text.append(
                "".join(
                    (
                        "{'",
                        str(move),
                        "' does not refer to a piece of the active side, ",
                        "'Yz0' inserted. Rest '",
                        " ".join(moves[count + 1 :]),
                        "' ignored.}Yz0",
                    )
                )
            )
            break

        # to_square must not contain a piece belonging to side with the move.
        if to_square in piece_placement_data:
            destination_piece = piece_placement_data[to_square].name
            if destination_piece in _ACTIVE_PIECES[game._active_color]:
                text.append(
                    "".join(
                        (
                            "{'",
                            str(move),
                            "' cannot be a move, 'Yz0' inserted. Rest '",
                            " ".join(moves[count + 1 :]),
                            "' ignored.}Yz0",
                        )
                    )
                )
                break

        # Maybe the _PIECE_TO_PGN mapping should be replaced by an attribute
        # in the Piece class.
        piece = _PIECE_TO_PGN[piece]

        promote_to = _PROMOTE[promote_to]

        # What about illegal moves specified in e2f5 format where the
        # constructed PGN move happens to be legal.

        # Castles is treated as a king move of two squares, otherwise illegal.
        if move in _CASTLES and piece_placement_data[
            from_square
        ].name == _CASTLEKEY.get(move):
            pgn_movetext = _CASTLES[move]

        # Pawn moves are given in a mixture of short algebraic notation and
        # long algebraic notation to fit the expectations of pgn_read's Game
        # class (at time of writing).  The move text returned by the chess
        # engine, <source square><destination square>, is used directly as
        # long algebraic notation passed to the PGN parser because it fits
        # the processing of, for example, 'g7g8' when a black pawn is on 'g7'.
        # Promotions and captures fit processing as short algebraic notation.
        # Short algebraic notation is generated by the GameMove class.
        elif piece == PGN_PAWN:

            # The distinction between normal captures, to_square occupied, and
            # en-passant captures, to_square empty, is left to the PGN parser.
            if from_square[0] == to_square[0]:
                if promote_to:
                    pgn_movetext = to_square + promote_to
                else:
                    pgn_movetext = from_square + to_square
            else:
                pgn_movetext = "".join(
                    (from_square[0], PGN_CAPTURE_MOVE, to_square, promote_to)
                )

            # Pawn must not be promoted to ranks othen than 1 or 8.
            if promote_to:
                if to_square[1] not in "18":
                    text.append(
                        "".join(
                            (
                                "{'",
                                str(move),
                                "' cannot be a move, 'Yz0' inserted. Rest '",
                                " ".join(moves[count + 1 :]),
                                "' ignored.}Yz0",
                            )
                        )
                    )
                    break

        # Piece moves are given in long algebraic notation, relying on the
        # GameMove class to produce short algebraic notation if possible.
        elif to_square not in piece_placement_data:
            pgn_movetext = "".join((piece, from_square, to_square))
        else:
            pgn_movetext = "".join(
                (piece, from_square, PGN_CAPTURE_MOVE, to_square)
            )

        # Generally the 'if matchend ...' should be 'while matchend ...', but
        # pgn_movetext is a single move so two calls to add_token_to_game are
        # needed, at most, to handle moves expressed as 'Qe3c6' for example.
        # This function does not have to figure which of 'Qe3c6', 'Q3c6',
        # 'Qec6', and 'Qc6', is the appropriate PGN movetext in the position.
        matchend = add_token_to_game(pgn_movetext, game)
        if matchend != len(pgn_movetext):
            add_token_to_game(pgn_movetext, game, pos=matchend)

        if game.state is not None:
            text.append(
                "".join(
                    (
                        "{'",
                        str(move),
                        "' cannot be a move, 'Yz0' inserted. Rest '",
                        " ".join(moves[count + 1 :]),
                        "' ignored.}Yz0",
                    )
                )
            )
            break
        text.append(game._text[-1])
    return " ".join(text)
