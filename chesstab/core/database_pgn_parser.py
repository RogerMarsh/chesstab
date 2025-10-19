# database_pgn_parser.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Portable Game Notation (PGN) parser for games in database records.

The PGN class provides the read_games method which splits text into tokens and
by default passes them to an instance of the game.Game class to build a data
structure representing a game.

The add_token_to_game function searches for the next token in the text
argument and adds it to the instance of game.Game class, or subclass, in the
game argument.

It may be too difficult to implement the decision when this parser or one
from pgn-read should be used.  The module exists here so it is in the
repository.

"""
import re

import pgn_read.core.constants

from . import game_database

MOVETEXT = r"".join(
    (
        r"(?#Piece location)([1-8][a-h][KQRBNPkqrbnp])",
        r"(?#SAN)(",
        r"(?#Moves)(?:",
        r"(?#Full disambiguation)([QBN][a-h][1-8]x?[a-h][1-8])|",
        r"(?#Pieces)([KQRBN](?:[a-h1-8]?x?)?[a-h][1-8])|",
        r"(?#Pawns)([a-h](?:x[a-h])?[2-7])|",
        r"(?#Promotions)([a-h](?:x[a-h])?[18]=[QRBN])",
        r"(?#End Moves))",
        r"(?#End SAN)[+#]?)",
    )
)
CASTLES = r"".join(
    (
        r"(?#Side)([Oo])",
        r"(?#Castles)(",
        r"(O-O(?:-O)?)",
        r"(?#End Castles)[+#]?)",
    )
)

# The pattern in pgn_read.core.constants is wrong here.
ESCAPED = r"(?#Escaped)((?:\A|(?<=\n))%[^\n]*)(?=\n)"

# Optional leading [{[<]? to catch incomplete [] {} and <> sequences.
TEXT = r"(?#Text)([{[<]?[^[;{<10*\n]+)"

DATABASE_FORMAT = r"|".join(
    (
        pgn_read.core.constants.TAG_PAIR,
        MOVETEXT,
        CASTLES,
        pgn_read.core.constants.GAME_TERMINATION,
        pgn_read.core.constants.EOL_COMMENT,
        pgn_read.core.constants.COMMENT,
        pgn_read.core.constants.START_RAV,
        pgn_read.core.constants.END_RAV,
        pgn_read.core.constants.NAG,
        pgn_read.core.constants.RESERVED,
        ESCAPED,
        TEXT,
    )
).join(
    (
        r"(?:\s*)(?:",
        r")",
    )
)

database_format = re.compile(DATABASE_FORMAT)


class DatabasePGN:
    """Extract tokens from database record text in PGN-like format.

    Each record has exactly one game in a PGN-like format where formatting
    has been removed.  This means all whitespace between PGN tags and all
    whitespace between movetext.  No move number indicators are present but
    check indicators are present.

    Each SAN token is prefixed by a sequence indicating the piece that is
    moving and the square it moves from.  For castling the prefix is an 'o'
    or an 'O'.  For other moves it is like '1fB' or 8fb' to be visually
    distinct from SAN movetext like 'Qc2'.  These reversed SAN tokens can
    serve as movetext delimiters like space and newline.
    """

    def __init__(self, game_class=game_database.GameDatabase):
        """Initialise switches to call game_class methods."""
        super().__init__()
        self._rules = database_format
        self._game_class = game_class

        # Table is set for indexing by match.lastindex which is 1-based.
        # When using a match.groups() index which is 0-based, subtract 1 from
        # the group() index.
        # So despatch[0] is set to None so both sources can use the lookup
        # table.
        self.despatch_table = (
            None,
            game_class.append_token_and_set_error,
            game_class.append_token_and_set_error,
            game_class.append_start_tag,
            game_class.append_token_and_set_error,
            game_class.append_move,
            game_class.append_token_and_set_error,
            game_class.append_token_and_set_error,
            game_class.append_token_and_set_error,
            game_class.append_token_and_set_error,
            game_class.append_token_and_set_error,
            game_class.append_castles,
            game_class.append_game_termination,
            game_class.append_comment_to_eol,
            game_class.append_comment,
            game_class.append_start_rav,
            game_class.append_end_rav,
            game_class.append_nag,
            game_class.append_reserved,
            game_class.ignore_escape,
            game_class.append_text,
        )
        self.error_despatch_table = (
            None,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_token_after_error,
            game_class.append_game_termination_after_error,
            game_class.append_comment_to_eol_after_error,
            game_class.append_comment_after_error,
            game_class.append_start_rav_after_error,
            game_class.append_end_rav_after_error,
            game_class.append_token_after_error,
            game_class.append_reserved_after_error,
            game_class.append_escape_after_error,
            game_class.append_token_after_error,
        )

    def read_game(self, source):
        """Extract games from source string.

        Yield Game, or subclass, instance when match is game termination token.
        The final yield is the instance as it is when source exhausted.

        source - file-like object from which to read pgn text
        size - number of characters to read in each read() call

        """
        despatch_table = self.despatch_table
        error_despatch_table = self.error_despatch_table
        dfg_game_termination = game_database.DFG_GAME_TERMINATION

        game = self._game_class()
        for match in self._rules.finditer(source):
            if game.state is not None:
                if match.lastindex == dfg_game_termination:
                    error_despatch_table[dfg_game_termination](game, match)
                    if game.len_ravstack() > 1:
                        game.set_game_error()
                    return game
                error_despatch_table[match.lastindex](game, match)
            elif match.lastindex == dfg_game_termination:
                despatch_table[dfg_game_termination](game, match)
                if game.len_ravstack() > 1:
                    game.set_game_error()
                return game
            else:
                despatch_table[match.lastindex](game, match)

        # The game in source has an error, or has no error but no game
        # termination marker either.
        if game.pgn_text:
            game.set_game_error()
        return game


def add_token_to_game(text, game, pos=0):
    """Apply first match in text after pos to game and return match.end().

    Return None if no match found.

    """
    dfg = game_database
    match = database_format.search(text, pos)
    if not match:
        game.set_game_error()
        return None
    lastindex = match.lastindex
    if game.state is not None:
        if lastindex == dfg.DFG_GAME_TERMINATION:
            game.append_game_termination_after_error(match)
        elif lastindex == dfg.DFG_COMMENT_TO_EOL:
            game.append_comment_to_eol_after_error(match)
        elif lastindex == dfg.DFG_START_RAV:
            game.append_start_rav_after_error(match)
        elif lastindex == dfg.DFG_END_RAV:
            game.append_end_rav_after_error(match)
        elif lastindex == dfg.DFG_ESCAPE:
            game.append_escape_after_error(match)
        elif lastindex == dfg.DFG_END_TAG:
            game.append_bad_tag_after_error(match)
        elif lastindex == dfg.DFG_COMMENT:
            game.append_comment_after_error(match)
        elif lastindex == dfg.DFG_RESERVED:
            game.append_token_after_error_without_separator(match)
        elif lastindex == dfg.DFG_TEXT:
            game.append_token_after_error_without_separator(match)
        else:
            game.append_token_after_error(match)
        return match.end()
    if lastindex == dfg.DFG_END_TAG:
        game.append_start_tag(match)
    elif lastindex == dfg.DFG_SAN:
        game.append_move(match)
    elif lastindex == dfg.DFG_CASTLES_SAN:
        game.append_castles(match)
    elif lastindex == dfg.DFG_GAME_TERMINATION:
        game.append_game_termination(match)
    elif lastindex == dfg.DFG_COMMENT_TO_EOL:
        game.append_comment_to_eol(match)
    elif lastindex == dfg.DFG_COMMENT:
        game.append_comment(match)
    elif lastindex == dfg.DFG_START_RAV:
        game.append_start_rav(match)
    elif lastindex == dfg.DFG_END_RAV:
        game.append_end_rav(match)
    elif lastindex == dfg.DFG_NUMERIC_ANNOTATION_GLYPH:
        game.append_nag(match)
    elif lastindex == dfg.DFG_RESERVED:
        game.append_reserved(match)
    elif lastindex == dfg.DFG_ESCAPE:
        game.ignore_escape(match)
    elif lastindex == dfg.DFG_TEXT:
        game.append_text(match)
    else:
        game.append_token_and_set_error(match)
    return match.end()
