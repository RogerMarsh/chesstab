# pgn.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Subclasses of pgn_read.core.game.Game class used by ChessTab.

Game* classes replace PGN* classes in ChessTab version 4.3.

"""
from pgn_read.core.game import Game, GameIndicateCheck
from pgn_read.core.movetext_parser import MoveText
from pgn_read.core.squares import Squares
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
    FEN_WHITE_ACTIVE,
)

from chessql.core.constants import ANY_WHITE_PIECE_NAME, ANY_BLACK_PIECE_NAME

from .constants import (
    TAG_OPENING,
    REPERTOIRE_TAG_ORDER,
    REPERTOIRE_GAME_TAGS,
    MOVE_NUMBER_KEYS,
    START_COMMENT,
    ERROR_START_COMMENT,
    ESCAPE_END_COMMENT,
    HIDE_END_COMMENT,
    END_COMMENT,
)

MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE = {
    FEN_WHITE_KING: ANY_WHITE_PIECE_NAME,
    FEN_WHITE_QUEEN: ANY_WHITE_PIECE_NAME,
    FEN_WHITE_ROOK: ANY_WHITE_PIECE_NAME,
    FEN_WHITE_BISHOP: ANY_WHITE_PIECE_NAME,
    FEN_WHITE_KNIGHT: ANY_WHITE_PIECE_NAME,
    FEN_WHITE_PAWN: ANY_WHITE_PIECE_NAME,
    FEN_BLACK_KING: ANY_BLACK_PIECE_NAME,
    FEN_BLACK_QUEEN: ANY_BLACK_PIECE_NAME,
    FEN_BLACK_ROOK: ANY_BLACK_PIECE_NAME,
    FEN_BLACK_BISHOP: ANY_BLACK_PIECE_NAME,
    FEN_BLACK_KNIGHT: ANY_BLACK_PIECE_NAME,
    FEN_BLACK_PAWN: ANY_BLACK_PIECE_NAME,
}


class GameDisplayMoves(GameIndicateCheck):
    """Add structures to support display of PGN moves."""

    def __init__(self):
        """Delegate then initialize moves to empty list."""
        super().__init__()
        self.moves = []

    # Replaces self.set_position_fen(self, fen=None)
    def set_initial_board_state(self, position_delta):
        """Initialize PGN score parser with Forsyth Edwards Notation position.

        fen defaults to the starting position for a game of chess.

        """
        super().set_initial_board_state(position_delta)
        if self._ravstack:
            self.moves = [(None, self._ravstack[-1][-1])]

    def modify_board_state(self, position_delta):
        """Delegate to superclass then append entry to moves."""
        super().modify_board_state(position_delta)
        self.moves.append((self._text[-1], self._ravstack[-1][-1]))


class _Game(Game):
    """Override the PGN error notification and recovery methods.

    Errors detected in PGN movetext are hidden by wrapping all tokens to end
    of variation, which may be rest of game if error is in main line, in a
    comment which starts and ends with a presumed unlikely character sequence.
    The '}' in any '{}' comments which happen to get wrapped a changed to a
    distinct presumed unlikely character sequence so the wrapped '}' tokens do
    not terminate the wrapping comment.

    """

    def __init__(self):
        """Delegate then set 'errors_hidden_in_comments' to None."""
        super().__init__()
        self.errors_hidden_in_comments = None

    def pgn_error_notification(self):
        """Insert error '{' before movetext token which causes PGN error."""
        if self._movetext_offset is not None:
            self._text.append(START_COMMENT + ERROR_START_COMMENT)
            self.errors_hidden_in_comments = True

    def pgn_error_recovery(self):
        """Insert error '}' before token which ends the scope of a PGN error.

        This token will be a ')' or one of the game termination markers.

        """
        if self._movetext_offset is not None:
            self._text.append(ESCAPE_END_COMMENT + END_COMMENT)

    def pgn_mark_comment_in_error(self, comment):
        """Return comment with '}' replaced by a presumed unlikely sequence.

        One possibility is to wrap the error in a '{...}' comment.  The '}'
        token in any wrapped commment would end the comment wrapping the error
        prematurely, so replace with HIDE_END_COMMENT.

        """
        return comment.replace(END_COMMENT, HIDE_END_COMMENT)


class GameMove(Game):
    """Generate data structures to verify moves returned from Chess Engines.

    set_initial_position() is not called in Game until the first movetext
    token is processed, but conversion of moves returned from chess engines
    to PGN needs the data structures set by the set_initial_position() call.

    GameMove allows this call to be done before processing the first movetext
    and supresses the call usually done with first movetext.

    """

    def __init__(self):
        """Delegate then set 'set initial position state' to None."""
        super().__init__()
        self._set_initial_position_state = None

    def set_initial_position(self):
        """Return 'set initial position state' after delegate to initialize."""
        if self._set_initial_position_state is None:
            self._set_initial_position_state = super().set_initial_position()
        return self._set_initial_position_state


class GameAnalysis(GameDisplayMoves):
    """Generate data to display Chess Engine analysis without ability to edit.

    The notion of mandatory PGN tags, like the 'seven tag roster', is removed
    from the GameDisplayMoves class.  Section 8.1.1: Seven Tag Roster of the
    PGN specification starts: 'There is a set of tags defined for mandatory
    use for archival storage of PGN data.  This is the STR (Seven Tag Roster)'.
    Thus the absence of all the STR tags does not prevent data from being
    called PGN data.  In particular the Result tag is not present fitting the
    Game Termination Marker '*' assigned to all analysis.

    Subclasses may use the PGN tag structure to manage analysis, but exactly
    what tags are defined is up to them.

    A single main move is required; to which chess engine analysis is attached
    as a sequence of RAVs, each RAV corresponding to one PV in a PV or multiPV
    response from a chess engine.

    """

    def is_tag_roster_valid(self):
        """Return True if the game's tag roster is valid."""
        tags = self._tags
        for value in tags.values():
            if len(value) == 0:
                # Tag value must not be null
                return False
        return True


def get_position_string(
    board,
    active_color,
    castling_availability,
    en_passant_target_square,
    halfmove_clock,
    fullmove_number,
):
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
    for similar positions, specifically for castling and en passant
    differences, near each other.  En passant is before castling because the
    meaning of 'b', 'Q', and 'q', can be decided without using the 8 byte bit
    pattern: piece name or en passant or castling or whose move.

    """
    del halfmove_clock, fullmove_number
    squares = Squares.squares
    for square, piece in board.items():
        piece.set_square(square)
    return (
        sum(squares[s].bit for s in board)
        .to_bytes(8, "big")
        .decode("iso-8859-1")
        + "".join(p.name for p in sorted(board.values()))
        + active_color
        + en_passant_target_square
        + castling_availability
    )


# The classes and functions above this comment are used in, or via, the Game,
# GameEdit, and Score, classes.  Those below this comment are used in, or via,
# the Repertoire, RepertoireEdit, and database update, classes only.  The
# order has been changed to ease a potential split in ChessTab to provide a
# 'ChessView' subset capable of viewing PGN files without the database update
# options.


class GameRepertoireDisplayMoves(GameDisplayMoves):
    """Generate data to display a repertoire without ability to edit.

    The Seven Tag Roster is ignored, except for the Result tag, and a private
    Opening tag is mandatory instead.

    Export methods are provided for repertoires.

    """

    def is_tag_roster_valid(self):
        """Return True if the game's tag roster is valid."""
        tags = self._tags
        for value in tags.values():
            if len(value) == 0:
                # Tag value must not be null
                return False
        if TAG_OPENING not in tags:
            # A mandatory tag is missing
            return False
        return True

    def get_repertoire_pgn(self):
        """Return export format PGN for repertoire."""
        tags = self._tags
        tokens = []
        for tag in REPERTOIRE_TAG_ORDER:
            tokens.extend(
                [
                    "[",
                    tag,
                    ' "',
                    tags.get(tag, REPERTOIRE_GAME_TAGS[tag]),
                    '"]\n',
                ]
            )
        for tag, value in sorted(
            [tv for tv in tags.items() if tv[0] not in REPERTOIRE_GAME_TAGS]
        ):
            tokens.extend(["[", tag, ' "', value, '"]\n'])
        tokens.append(self.get_all_movetext_in_pgn_export_format())
        return "".join(tokens)

    def get_repertoire_pgn_no_comments(self):
        """Return export format PGN for repertoire excluding comments."""
        tags = self._tags
        tokens = []
        for tag in REPERTOIRE_TAG_ORDER:
            tokens.extend(
                [
                    "[",
                    tag,
                    ' "',
                    tags.get(tag, REPERTOIRE_GAME_TAGS[tag]),
                    '"]\n',
                ]
            )
        for tag, value in sorted(
            [tv for tv in tags.items() if tv[0] not in REPERTOIRE_GAME_TAGS]
        ):
            tokens.extend(["[", tag, ' "', value, '"]\n'])
        tokens.append(
            self.get_movetext_without_comments_in_pgn_export_format()
        )
        return "".join(tokens)


class GameRepertoireUpdate(Game):
    """Generate data structures to Update a repertoire on a database."""

    def is_tag_roster_valid(self):
        """Return True if the repertoire's tag roster is valid."""
        tags = self._tags
        for value in tags.values():
            if len(value) == 0:
                # Tag value must not be null
                return False
        if TAG_OPENING not in tags:
            # A mandatory tag is missing
            return False
        return True


class GameTags(Game):
    """Generate data structures to display the PGN Tags of a game.

    Comments on two methods are worth making:

    _disambiguate_move is defined but the only way it should be reached has
    been disabled by overriding _collecting_movetext.  The definition ensures
    PGN._disambiguate_move is never called.

    PGN._collecting_non_whitespace_while_searching is correct in this class
    too.

    """

    def append_piece_move(self, match):
        """Ignore piece move token and update board state with null.

        Tokens are assumed to represent legal moves.

        """
        if self._movetext_offset is None:
            self._ravstack.append(None)
            self._movetext_offset = len(self._text)
            self._text.append("")

    def append_pawn_move(self, match):
        """Ignore pawn move token and update board state with null.

        Pawn promotion moves are handled by append_pawn_promote_move.

        Tokens are assumed to represent legal moves.

        """
        if self._movetext_offset is None:
            self._ravstack.append(None)
            self._movetext_offset = len(self._text)
            self._text.append("")

    def append_pawn_promote_move(self, match):
        """Ignore pawn promotion move token and update board state with null.

        Tokens are assumed to represent legal moves.

        """
        if self._movetext_offset is None:
            self._ravstack.append(None)
            self._movetext_offset = len(self._text)
            self._text.append("")

    def append_castles(self, match):
        """Ignore castling move token and update board state with null.

        Tokens are assumed to represent legal moves.

        """
        if self._movetext_offset is None:
            self._ravstack.append(None)
            self._movetext_offset = len(self._text)
            self._text.append("")

    def append_game_termination(self, match):
        """Append game termination token to game score and update game state.

        Tokens are assumed to represent legal moves.

        """
        if self._movetext_offset is None:
            self._movetext_offset = len(self._text)
        self._text.append(match.group())
        try:
            self.repeat_board_state(self._position_deltas[-1])
        except IndexError:
            self.add_board_state_none(None)

    def append_token(self, match):
        """Ignore valid non-tag token which does not change board state.

        The game position for this token is the same as for the adjacent token,
        and the game state is adjusted to fit.

        """
        try:
            self.repeat_board_state(self._position_deltas[-1])
        except IndexError:
            self.add_board_state_none(None)

    append_reserved = append_token

    def append_start_rav(self, match):
        """Append start RAV token to game score and update board state.

        Put game in error state if a variation cannot be put at current place
        in game score.

        """
        if self._movetext_offset is None:
            self.append_token_and_set_error(match)
            return
        self.reset_board_state(None)
        self._ravstack.append(None)
        self._text.append(match.group())
        self._state_stack.append(self._state)

    def append_end_rav(self, match):
        """Append end RAV token to game score and update board state.

        Put game in error state if a variation cannot be finished at current
        place in game score.

        """
        if self._state is not None or self._movetext_offset is None:
            self.append_token_and_set_error(match)
            return None

        if self._movetext_offset is None:
            self.append_token_and_set_error(match)
            return None
        if len(self._ravstack) == 1:
            self.append_token_and_set_error(match)
            return None
        del self._ravstack[-1]
        del self._state_stack[-1]
        self._state = self._state_stack[-1]

        self.set_board_state(None)
        self._text.append(match.group())
        return True

    def append_other_or_disambiguation_pgn(self, match):
        """Ignore token.

        'Qb3c2' can mean move the queen on b3 to c2 when all whitespace is
        removed from PGN movetext.  This method processes the 'c2' when it is
        consumed from the input: 'c2' is processed by peeking at the input when
        processing the 'Qb3'.

        """

    def append_token_after_error(self, match):
        """Ignore token after an error has been found."""

    def append_game_termination_after_error(self, match):
        """Append game termination token to game score.

        Tokens are assumed to represent legal moves.

        """
        self._text.append(match.group())

    def append_start_rav_after_error(self, match):
        """Append start RAV marker to game score and prepare error recovery.

        Rest of RAV is assumed to be in error, but after next matching end
        RAV marker it is worth assuming it possible to pick up from the
        valid position just before this start RAV marker.

        """
        self._text.append(match.group())
        self._state_stack.append(self._state)

    def append_end_rav_after_error(self, match):
        """Append end RAV marker to game score and reset position to pre-RAV.

        It is assumed the pre-RAV position is valid (otherwise the error
        state would have begun earlier).

        """
        if len(self._state_stack) > 1:
            if self._state_stack[-2] == self._state_stack[-1]:
                self._text.append(match.group())
                del self._state_stack[-1]
                self._state = self._state_stack[-1]
            else:
                # Cannot call append_end_rav() method because it tests some
                # conditions that should be true when errors are absent.
                if self._movetext_offset is None:
                    self.append_token_and_set_error(match)
                    return
                if len(self._ravstack) == 1:
                    self.append_token_and_set_error(match)
                    return
                del self._ravstack[-1]
                del self._state_stack[-1]
                self._state = self._state_stack[-1]
                self.set_board_state(None)
                self._text.append(match.group())

        else:
            self._text.append(match.group())


class GameRepertoireTags(GameTags):
    """Generate data structures to display the PGN Tags of a repertoire.

    The notion of mandatory PGN tags, like the 'seven tag roster', means the
    TAG_OPENING tag.

    """

    def is_tag_roster_valid(self):
        """Return True if the game's tag roster is valid."""
        tags = self._tags
        for value in tags.values():
            if len(value) == 0:
                # Tag value must not be null
                return False
        if TAG_OPENING not in tags:
            # A mandatory tag is missing
            return False
        return True


class GameUpdate(_Game):
    """Prepare indicies after each token has been processed."""

    # self.positions, and the three similar, renamed to self.positionkeys.
    # self.movenumber is changed to self.halfmovenumber.
    def __init__(self):
        """Delegate then prepare to collect positions and piece locations."""
        super().__init__()
        self.positionkeys = []
        self.piecesquaremovekeys = []
        self.piecemovekeys = []
        self.squaremovekeys = []
        self.halfmovenumber = None
        self.variationnumber = None
        self.currentvariation = None
        self._variation = None

    # Replaces self.set_position_fen(self, fen=None)
    def set_initial_board_state(self, position_delta):
        """Initialize PGN score parser with Forsyth Edwards Notation position.

        fen defaults to the starting position for a game of chess.

        """
        super().set_initial_board_state(position_delta)
        if self._active_color == FEN_WHITE_ACTIVE:
            self.halfmovenumber = [(self._fullmove_number - 1) * 2]
        else:
            self.halfmovenumber = [self._fullmove_number * 2 - 1]
        self.variationnumber = [0]
        self._variation = "".join(
            _convert_integer_to_length_hex(i) for i in self.variationnumber
        )

    def reset_board_state(self, position_delta):
        """Delegate then append variation number to fit ravstack level."""
        super().reset_board_state(position_delta)
        if len(self._ravstack) > len(self.variationnumber):
            self.variationnumber.append(0)

    # Why '[len(self._ravstack)-1]' rather than '[-1]'?  The '[len()]' version
    # came from PGNUpdate in chesstab, without the -1 adjustment, and seems to
    # work.
    def set_board_state(self, position_delta):
        """Delegate then increment variation number.

        Both numeric and string variation numbers are kept in step in case
        there is another variation at this level.  For example:
        '... Ba7 ) ( Nf4 ...'.
        """
        super().set_board_state(position_delta)
        self.variationnumber[len(self._ravstack) - 1] += 1
        self._variation = "".join(
            _convert_integer_to_length_hex(i) for i in self.variationnumber
        )

    def modify_board_state(self, position_delta):
        """Delegate then modify board state and add index entries."""
        super().modify_board_state(position_delta)
        if len(self._ravstack) != len(self.halfmovenumber):
            while len(self._ravstack) < len(self.halfmovenumber):
                self.halfmovenumber.pop()
                self.variationnumber.pop()
            while len(self._ravstack) > len(self.halfmovenumber):
                self.halfmovenumber.append(self.halfmovenumber[-1])
                self.variationnumber.append(0)
            self._variation = "".join(
                _convert_integer_to_length_hex(i) for i in self.variationnumber
            )
        self.halfmovenumber[-1] += 1
        movenumber = _convert_integer_to_length_hex(self.halfmovenumber[-1])
        piecesquaremovekeys = self.piecesquaremovekeys
        piecemovekeys = self.piecemovekeys
        squaremovekeys = self.squaremovekeys
        pieces = [""] * 64
        bits = 0
        mnv = movenumber + self._variation
        for piece in self._piece_placement_data.values():
            piece_name = piece.name
            piece_square = piece.square
            square_name = piece_square.name
            pieces[piece_square.number] = piece_name
            bits += piece_square.bit

            # piecesquaremovekeys.append(mnv + piece_name + square_name)
            # squaremovekeys.append(mnv + mp[piece_name] + square_name)

            # If 'square piece' is better order than 'piece square'
            piecesquaremovekeys.append(mnv + square_name + piece_name)
            squaremovekeys.append(
                (
                    mnv
                    + square_name
                    + MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE[piece_name]
                )
            )

        pieces = "".join(pieces)
        for piece_name in set(pieces):
            piecemovekeys.append(mnv + piece_name)
        delta_after = position_delta[1]
        self.positionkeys.append(
            bits.to_bytes(8, "big").decode("iso-8859-1")
            + pieces
            + delta_after[1]
            + delta_after[3]
            + delta_after[2]
        )


class GameUpdatePosition(_Game):
    """Prepare position index after each token has been processed."""

    def __init__(self):
        """Delegate then prepare to collect positions."""
        super().__init__()
        self.positionkeys = []

    def modify_board_state(self, position_delta):
        """Delegate then modify board state and add index entries."""
        super().modify_board_state(position_delta)
        pieces = [""] * 64
        bits = 0
        for piece in self._piece_placement_data.values():
            piece_name = piece.name
            piece_square = piece.square
            pieces[piece_square.number] = piece_name
            bits += piece_square.bit
        delta_after = position_delta[1]
        self.positionkeys.append(
            bits.to_bytes(8, "big").decode("iso-8859-1")
            + "".join(pieces)
            + delta_after[1]
            + delta_after[3]
            + delta_after[2]
        )


class GameUpdatePieceLocation(_Game):
    """Prepare piece location indicies after each token has been processed."""

    def __init__(self):
        """Delegate then prepare to collect piece locations."""
        super().__init__()
        self.piecesquaremovekeys = []
        self.piecemovekeys = []
        self.squaremovekeys = []
        self.halfmovenumber = None
        self.variationnumber = None
        self.currentvariation = None
        self._variation = None

    # Replaces self.set_position_fen(self, fen=None)
    def set_initial_board_state(self, position_delta):
        """Initialize PGN score parser with Forsyth Edwards Notation position.

        fen defaults to the starting position for a game of chess.

        """
        super().set_initial_board_state(position_delta)
        if self._active_color == FEN_WHITE_ACTIVE:
            self.halfmovenumber = [(self._fullmove_number - 1) * 2]
        else:
            self.halfmovenumber = [self._fullmove_number * 2 - 1]
        self.variationnumber = [0]
        self._variation = "".join(
            _convert_integer_to_length_hex(i) for i in self.variationnumber
        )

    def reset_board_state(self, position_delta):
        """Delegate then append variation number to fit ravstack level."""
        super().reset_board_state(position_delta)
        if len(self._ravstack) > len(self.variationnumber):
            self.variationnumber.append(0)

    # Why '[len(self._ravstack)-1]' rather than '[-1]'?  The '[len()]' version
    # came from PGNUpdate in chesstab, without the -1 adjustment, and seems to
    # work.
    def set_board_state(self, position_delta):
        """Delegate then increment variation number.

        Both numeric and string variation numbers are kept in step in case
        there is another variation at this level.  For example:
        '... Ba7 ) ( Nf4 ...'.
        """
        super().set_board_state(position_delta)
        self.variationnumber[len(self._ravstack) - 1] += 1
        self._variation = "".join(
            _convert_integer_to_length_hex(i) for i in self.variationnumber
        )

    def modify_board_state(self, position_delta):
        """Delegate then modify board state and add index entries."""
        super().modify_board_state(position_delta)
        if len(self._ravstack) != len(self.halfmovenumber):
            while len(self._ravstack) < len(self.halfmovenumber):
                self.halfmovenumber.pop()
                self.variationnumber.pop()
            while len(self._ravstack) > len(self.halfmovenumber):
                self.halfmovenumber.append(self.halfmovenumber[-1])
                self.variationnumber.append(0)
            self._variation = "".join(
                _convert_integer_to_length_hex(i) for i in self.variationnumber
            )
        self.halfmovenumber[-1] += 1
        movenumber = _convert_integer_to_length_hex(self.halfmovenumber[-1])
        piecesquaremovekeys = self.piecesquaremovekeys
        piecemovekeys = self.piecemovekeys
        squaremovekeys = self.squaremovekeys
        pieces = [""] * 64
        mnv = movenumber + self._variation
        for piece in self._piece_placement_data.values():
            piece_name = piece.name
            piece_square = piece.square
            square_name = piece_square.name
            pieces[piece_square.number] = piece_name

            # piecesquaremovekeys.append(mnv + piece_name + square_name)
            # squaremovekeys.append(mnv + mp[piece_name] + square_name)

            # If 'square piece' is better order than 'piece square'
            piecesquaremovekeys.append(mnv + square_name + piece_name)
            squaremovekeys.append(
                (
                    mnv
                    + square_name
                    + MAP_PGN_PIECE_TO_CQL_COMPOSITE_PIECE[piece_name]
                )
            )
        for piece_name in set("".join(pieces)):
            piecemovekeys.append(mnv + piece_name)
        # delta_after = position_delta[1]


class GameUpdateEstimate(GameUpdate):
    """Count characters and tokens to estimate time for import run."""

    start_char = 0
    end_char = 0

    def append_start_tag(self, match):
        """Set self.start_char if no PGN Tags found and delegate."""
        if not self._tags:
            self.start_char = match.start()
        super().append_start_tag(match)

    def append_game_termination_after_error(self, match):
        """Set self.end_char and delegate."""
        self.end_char = match.end()
        super().append_game_termination_after_error(match)

    def append_game_termination(self, match):
        """Set self.end_char and delegate."""
        self.end_char = match.end()
        super().append_game_termination(match)

    def append_bad_tag_and_set_error(self, match):
        """Set self.start_char if no PGN Tags found and delegate."""
        if not self._tags:
            self.start_char = match.start()
        super().append_bad_tag_and_set_error(match)


def _convert_integer_to_length_hex(integer):
    """Return hexadecimal representation of integer without '0x' prefix."""
    try:
        return MOVE_NUMBER_KEYS[integer]
    except IndexError:
        base16 = hex(integer)
        return str(len(base16) - 2) + base16[2:]


class GameMoveText(MoveText):
    """Customize methods of MoveText."""

    def is_pgn_valid(self):
        """Return True if the tags in the game are valid.

        Override because the tag values matter rather than their existence.

        """
        return self.is_tag_roster_valid()
