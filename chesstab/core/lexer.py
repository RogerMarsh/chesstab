# lexer.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Game record lexer.

Games are stored one per record in a format derived from PGN by removing
all whitespace separators, all move number indicators, and all sequences
of dots.  Fully disambiguated piece moves are stored with a hyphen between
the square moved from and the square moved to.

"""
import re

from pgn_read.core.constants import (
    PGN_TAG,
    GAME_TERMINATION,
    START_RAV,
    END_RAV,
    NAG,
    EOL_COMMENT,
    COMMENT,
    RESERVED,
)

PAWN_MOVE = r"(?#Pawn move)([a-h](?:x[a-h])?[1-8](?:=[QRBN])?(?:[+#])?)"
CASTLES = r"(?#Castles)((?:O-O-O|O-O)(?:[+#])?)"
PIECE_MOVE_FULL = "".join(
    (r"(?#Piece move full)", r"([QBN][a-h][1-8][x-][a-h][1-8](?:[+#])?)")
)
PIECE_MOVE = r"(?#Piece move)([QRBN][a-h1-8]?x?[a-h][1-8](?:[+#])?)"
KING_MOVE = r"(?#King move)(Kx?[a-h][1-8](?:[+#])?)"
MATCH_STARTER = r"(?#Match starter)([KQRBNa-h10O[{<;$])"
ANYTHING_ELSE = r"(?#Anything else)([^KQRBNa-h10*O[{<;()$]+)"
GAME_PATTERN = r"|".join(
    (
        PGN_TAG.join(r"()"),
        PAWN_MOVE,
        PIECE_MOVE_FULL,
        PIECE_MOVE,
        KING_MOVE,
        CASTLES,
        GAME_TERMINATION,
        START_RAV,
        END_RAV,
        NAG,
        COMMENT,
        EOL_COMMENT,
        RESERVED,
        MATCH_STARTER,
        ANYTHING_ELSE,
    )
)


class Lexer:
    """Extract tokens from game records on chesstab database."""

    def __init__(self, action):
        """Initialise switches to call action instance methods."""
        self.pattern = re.compile(GAME_PATTERN)
        self.tagpair_actions = (
            None,
            action.tagpair_pgn_tag,
            action.tagpair_pawn_move,
            action.tagpair_piece_move_full,
            action.tagpair_piece_move,
            action.tagpair_king_move,
            action.tagpair_castles,
            action.tagpair_game_termination,
            action.tagpair_start_rav,
            action.tagpair_end_rav,
            action.tagpair_nag,
            action.tagpair_comment,
            action.tagpair_eol_comment,
            action.tagpair_reserved,
            action.tagpair_match_starter,
            action.tagpair_anything_else,
        )
        self.movetext_actions = (
            None,
            action.movetext_pgn_tag,
            action.movetext_pawn_move,
            action.movetext_piece_move_full,
            action.movetext_piece_move,
            action.movetext_king_move,
            action.movetext_castles,
            action.movetext_game_termination,
            action.movetext_start_rav,
            action.movetext_end_rav,
            action.movetext_nag,
            action.movetext_comment,
            action.movetext_eol_comment,
            action.movetext_reserved,
            action.movetext_match_starter,
            action.movetext_anything_else,
        )
        self._actions = self.tagpair_actions

    def set_actions(self, actions):
        """Set the actions switch."""
        self._actions = actions

    def generate_tokens(self, text):
        """Generate tokens from text."""
        for item in self.pattern.finditer(text):
            self._actions[item.lastindex](item.group())
