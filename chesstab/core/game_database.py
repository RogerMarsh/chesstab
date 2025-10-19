# game_database.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Subclass of pgn_read.core.game.GameData for games in database records.

Each record should have exactly one game.  The game may have PGN errors
which were found by the PGN parser from pgn-read when importing, inserting,
or editing, the game.

Moves are in SAN (Standard Algebraic Notation) format delimited by a
SAN-like sequence indicating the piece location before the move.

It may be too difficult to implement the decision when this parser or one
from pgn-read should be used.  The module exists here so it is in the
repository.

"""
import pgn_read.core.gamedata
from pgn_read.core.constants import (
    FILE_NAMES,
    RANK_NAMES,
    FEN_WHITE_ACTIVE,
    FEN_NULL,
    PGN_CAPTURE_MOVE,
    PGN_O_O,
    OTHER_SIDE,
    PROMOTED_PIECE_NAME,
)
from pgn_read.core.squares import en_passant_target_squares

DFG_TAG_NAME = 1
DFG_TAG_VALUE = 2
DFG_END_TAG = 3  # The lastindex value for tags.
DFG_PIECE_FROM = 4
DFG_SAN = 5  # The lastindex value for moves except castling.
DFG_FULL_DISAMBIGUATION = 6
DFG_PIECE_MOVE = 7
DFG_PAWN_MOVE = 8
DFG_PAWN_PROMOTE = 9
DFG_CASTLING_SIDE = 10
DFG_CASTLES_SAN = 11  # The lastindex value for castling moves.
DFG_CASTLES = 12
DFG_GAME_TERMINATION = 13  # The lastindex value for game termination marker.
DFG_COMMENT_TO_EOL = 14  # The lastindex value for comment to end of line.
DFG_COMMENT = 15  # The lastindex value for braced comment.
DFG_START_RAV = 16  # The lastindex value for start variation.
DFG_END_RAV = 17  # The lastindex value for end variation.
DFG_NUMERIC_ANNOTATION_GLYPH = 18  # The lastindex value for NAG.
DFG_RESERVED = 19  # The lastindex value for reserved <>.
DFG_ESCAPE = 20  # The lastindex value for '%any\n' where '%' starts line.
DFG_TEXT = 21  # The lastindex value for anything else (an error).


class GameDatabase(pgn_read.core.gamedata.GameData):
    """Data structure of game positions derived from a PGN game score.

    Comparison operators implement the PGN collating sequence, except in
    ascending str order rather than ascending ASCII order.
    """

    def append_start_tag(self, match):
        """Append tag token to game score and update game tags.

        Put game in error state if a duplicate tag name is found.

        """
        if self._state is not None or self._movetext_offset is not None:
            self._append_token_and_set_error(match)
            return
        group = match.group
        tag_name = group(DFG_TAG_NAME)
        tag_value = group(DFG_TAG_VALUE)
        self._text.append("".join(("[", tag_name, '"', tag_value, '"]')))
        self.add_board_state_none()

        # Tag names must not be duplicated.
        if tag_name in self._tags:
            if self._state is None:
                self._state = len(self._tags) - 1
                self._state_stack[-1] = self._state
            return

        self._tags[tag_name] = tag_value
        return

    def append_game_termination(self, match):
        """Append game termination token to game score and update game state.

        Put game in error state if no moves exists in game score and the
        initial position is not valid.  Validation includes piece counts and
        some piece placement: pawns on ranks 2 to 7 only and king of active
        color not in check for example.  Verification that the initial position
        declared in a PGN FEN tag is reachable from the standard starting
        position is not attempted.

        """
        if self._movetext_offset is None:
            if not self.set_initial_position():
                self._append_token_and_set_error(match)
                return
            self._movetext_offset = len(self._text)
        self._text.append(match.group(DFG_GAME_TERMINATION))
        self.add_board_state_none()

    def append_comment_to_eol(self, match):
        r"""Append ';...\n' token from gamescore.

        The '\n' termination for the comment is not captured because it may
        start an escaped line, '\n%...\n', and is explicitly added to the
        token.

        The game position for this token is the same as for the adjacent token,
        and the game state is adjusted to fit.

        """
        self._text.append(match.group(DFG_COMMENT_TO_EOL) + "\n")
        try:
            self.repeat_board_state()
        except IndexError:
            self.add_board_state_none()

    def append_comment(self, match):
        """Append valid comment token from game score.

        The game position for this token is the same as for the adjacent token,
        and the game state is adjusted to fit.

        """
        self._text.append(match.group(DFG_COMMENT))
        try:
            self.repeat_board_state()
        except IndexError:
            self.add_board_state_none()

    def append_start_rav(self, match):
        """Append start recursive annotation variation token to game score."""
        if not self._reset_after_start_rav(match):
            return
        self._text.append(match.group(DFG_START_RAV))

    def append_end_rav(self, match):
        """Append end recursive annotation variation token to game score."""
        if not self._reset_after_end_rav(match):
            return
        self._reset_position_after_end_rav(match)
        self._text.append(match.group(DFG_END_RAV))

    def append_nag(self, match):
        """Append valid numeric annotation glyph token from game score.

        The game position for this token is the same as for the adjacent token,
        and the game state is adjusted to fit.

        """
        self._text.append(match.group(DFG_NUMERIC_ANNOTATION_GLYPH))
        try:
            self.repeat_board_state()
        except IndexError:
            self.add_board_state_none()

    def append_reserved(self, match):
        """Append valid reserved token from game score.

        The game position for this token is the same as for the adjacent token,
        and the game state is adjusted to fit.

        """
        self._text.append(match.group(DFG_RESERVED))
        try:
            self.repeat_board_state()
        except IndexError:
            self.add_board_state_none()

    def ignore_escape(self, match):
        r"""Ignore escape token and rest of line containing the token.

        The '\n' termination for the escaped line is not captured because it
        may start an escaped line.

        The '\n' must be appended to the token in subclasses which capture
        the escaped line.

        """

    def append_text(self, match):
        """Append any other token from game score as an error.

        These are all errors so call append_token_and_set_error.

        """
        self._append_token_and_set_error(match, index=DFG_TEXT)

    def append_token_and_set_error(self, match):
        """Append first unexpected match.lastindex to game score."""
        self._append_token_and_set_error(match)

    def append_castles(self, match):
        """Append castling move token to game score and update board state.

        Put game in error state if the token represents an illegal move.

        The game is assumed to be from a database record where only legal
        moves are represented.

        """
        if self._movetext_offset is None:
            if not self.set_initial_position():
                self._append_token_and_set_error(match, index=DFG_CASTLES_SAN)
                return
            self._ravstack.append([0])
            self._movetext_offset = len(self._text)
        if self._active_color == FEN_WHITE_ACTIVE:
            king_square = FILE_NAMES[4] + RANK_NAMES[-1]
            fullmove_number_for_next_halfmove = self._fullmove_number
        else:
            king_square = FILE_NAMES[4] + RANK_NAMES[0]
            fullmove_number_for_next_halfmove = self._fullmove_number + 1
        # Game is from database: assume the king is on the expected square
        # and the castling move is still available.

        if match.group(DFG_CASTLES) == PGN_O_O:
            if self._active_color == FEN_WHITE_ACTIVE:
                rook_square = FILE_NAMES[7] + RANK_NAMES[-1]
                king_destination = FILE_NAMES[6] + RANK_NAMES[-1]
                rook_destination = FILE_NAMES[5] + RANK_NAMES[-1]
            else:
                rook_square = FILE_NAMES[7] + RANK_NAMES[0]
                king_destination = FILE_NAMES[6] + RANK_NAMES[0]
                rook_destination = FILE_NAMES[5] + RANK_NAMES[0]
        elif self._active_color == FEN_WHITE_ACTIVE:
            rook_square = FILE_NAMES[0] + RANK_NAMES[-1]
            king_destination = FILE_NAMES[2] + RANK_NAMES[-1]
            rook_destination = FILE_NAMES[3] + RANK_NAMES[-1]
        else:
            rook_square = FILE_NAMES[0] + RANK_NAMES[0]
            king_destination = FILE_NAMES[2] + RANK_NAMES[0]
            rook_destination = FILE_NAMES[3] + RANK_NAMES[0]
        # Game is from database: assume squares between the king and rook
        # are empty and the rook is on the expected square.

        # Game is from database: assume the three relevant squares are not
        # attacked by side without the move, so castling is legal.

        king = self._piece_placement_data[king_square]
        rook = self._piece_placement_data[rook_square]
        self._modify_game_state_castles(
            ((king_square, king), (rook_square, rook)),
            ((king_destination, king), (rook_destination, rook)),
            fullmove_number_for_next_halfmove,
        )
        self._append_decorated_castles_text(match.group(DFG_CASTLES))

    def append_move(self, match):
        """Append non-castling move to game score and update board state."""
        groups = match.groups()
        if groups(DFG_PIECE_MOVE) is not None:
            self._append_piece_move(match, groups)
        elif groups(DFG_PAWN_MOVE) is not None:
            self._append_pawn_move(match, groups)
        elif groups(DFG_PAWN_PROMOTE) is not None:
            self._append_pawn_promote(match, groups)
        elif groups(DFG_FULL_DISAMBIGUATION) is not None:
            self._append_full_disambiguation(match, groups)
        else:
            self.append_token_and_set_error(match)

    def _append_piece_move(self, match, groups):
        """Append piece move to game score and update board state.

        Pawn moves and fully disambiguated queen, bishop, or knight, moves
        are handled elsewhere.

        """
        if self._movetext_offset is None:
            if not self.set_initial_position():
                self._append_token_and_set_error(match)
                return
            self._ravstack.append([0])
            self._movetext_offset = len(self._text)
        if self._active_color == FEN_WHITE_ACTIVE:
            fullmove_number_for_next_halfmove = self._fullmove_number
        else:
            fullmove_number_for_next_halfmove = self._fullmove_number + 1
        move = groups[DFG_PIECE_MOVE]
        source = groups[DFG_PIECE_FROM]
        destination = move[-2:]
        piece = self._piece_placement_data[source[1] + source[0]]
        if PGN_CAPTURE_MOVE in move:
            self._modify_game_state_piece_capture(
                (
                    (destination, self._piece_placement_data[destination]),
                    (piece.square.name, piece),
                ),
                ((destination, piece),),
                fullmove_number_for_next_halfmove,
            )
        else:
            self._modify_game_state_piece_move(
                ((piece.square.name, piece),),
                ((destination, piece),),
                fullmove_number_for_next_halfmove,
            )
        self._append_decorated_text(move)

    def _append_pawn_move(self, match, groups):
        """Append pawn move to game score and update board state.

        Piece moves, pawn promotion, and fully disambiguated queen, bishop,
        or knight, moves are handled elsewhere.

        """
        if self._movetext_offset is None:
            if not self.set_initial_position():
                self._append_token_and_set_error(match)
                return
            self._ravstack.append([0])
            self._movetext_offset = len(self._text)
        if self._active_color == FEN_WHITE_ACTIVE:
            fullmove_number_for_next_halfmove = self._fullmove_number
        else:
            fullmove_number_for_next_halfmove = self._fullmove_number + 1
        move = groups[DFG_PAWN_MOVE]
        source = groups[DFG_PIECE_FROM]
        destination = move[-2:]
        piece = self._piece_placement_data[source[1] + source[0]]
        if PGN_CAPTURE_MOVE in move:
            if destination not in self._piece_placement_data:
                capture = en_passant_target_squares.get(move)
            else:
                capture = destination
            self._modify_game_state_pawn_capture(
                (
                    (capture, self._piece_placement_data[capture]),
                    (piece.square.name, piece),
                ),
                ((destination, piece),),
                fullmove_number_for_next_halfmove,
            )
        else:
            self._modify_game_state_pawn_move(
                ((piece.square.name, piece),),
                ((destination, piece),),
                fullmove_number_for_next_halfmove,
                en_passant_target_squares[OTHER_SIDE[self._active_color]].get(
                    (destination, piece.square.name), FEN_NULL
                ),
            )
        self._append_decorated_text(move)

    def _append_pawn_promote(self, match, groups):
        """Append pawn promotion move to game score and update board state.

        Pawn moves and fully disambiguated queen, bishop, or knight, moves
        are handled elsewhere.

        """
        if self._movetext_offset is None:
            if not self.set_initial_position():
                self._append_token_and_set_error(match)
                return
            self._ravstack.append([0])
            self._movetext_offset = len(self._text)
        if self._active_color == FEN_WHITE_ACTIVE:
            fullmove_number_for_next_halfmove = self._fullmove_number
        else:
            fullmove_number_for_next_halfmove = self._fullmove_number + 1
        move = groups[DFG_PAWN_PROMOTE]
        source = groups[DFG_PIECE_FROM]
        destination = move[-2:]
        piece = self._piece_placement_data[source[1] + source[0]]
        promoted_pawn = piece.promoted_pawn(
            PROMOTED_PIECE_NAME[self._active_color][move[-1]],
            destination,
        )
        if PGN_CAPTURE_MOVE in move:
            self._modify_game_state_pawn_promote_capture(
                (
                    (destination, self._piece_placement_data[destination]),
                    (piece.square.name, piece),
                ),
                ((destination, promoted_pawn),),
                fullmove_number_for_next_halfmove,
            )
        else:
            self._modify_game_state_pawn_promote(
                ((piece.square.name, piece),),
                ((destination, promoted_pawn),),
                fullmove_number_for_next_halfmove,
            )
        self._append_decorated_text(move)

    def _append_full_disambiguation(self, match, groups):
        """Append fully disambiguated move to game and update board state.

        Pawn moves and other piece moves are handled elsewhere.

        These are rare and only queen, bishop, or knight, moves may need to
        be fully disambiguated.

        """
        if self._movetext_offset is None:
            if not self.set_initial_position():
                self._append_token_and_set_error(match)
                return
            self._ravstack.append([0])
            self._movetext_offset = len(self._text)
        if self._active_color == FEN_WHITE_ACTIVE:
            fullmove_number_for_next_halfmove = self._fullmove_number
        else:
            fullmove_number_for_next_halfmove = self._fullmove_number + 1
        move = groups[DFG_FULL_DISAMBIGUATION]
        source = groups[DFG_PIECE_FROM]
        destination = move[-2:]
        piece = self._piece_placement_data[source[1] + source[0]]
        if PGN_CAPTURE_MOVE in move:
            self._modify_game_state_piece_capture(
                (
                    (destination, self._piece_placement_data[destination]),
                    (piece.square.name, piece),
                ),
                ((destination, piece),),
                fullmove_number_for_next_halfmove,
            )
        else:
            self._modify_game_state_piece_move(
                ((piece.square.name, piece),),
                ((destination, piece),),
                fullmove_number_for_next_halfmove,
            )
        self._append_decorated_text(move)
