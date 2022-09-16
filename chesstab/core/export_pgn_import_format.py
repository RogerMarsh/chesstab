# export_pgn_import_format.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Generate game or repertoire text in a form allowed by PGN import format.

The default argument values were chosen to fit what a sample of two other
non-commercial open source chess database products accept as PGN import
format.

The function is renamed export_pgn_import_format but the replaced name,
get_game_pgn_import_format, is kept as an alias which will be removed
without notice at some future time.

"""


# Derived from get_all_movetext_in_pgn_export_format method in
# pgn_read.core.game module.
# At 13 Jan 2021 on a sample of two other non-commercial open source chess
# database products both require a restricted line length to allow extraction
# of the game score.  One of them looks like it needs '\n' as tag_separator.
# The other finds all games and tags with both name_value_separator and
# tag_separator as ' ', but finds nothing with both as ''.  Both accept '\n'
# as block_separator rather than '\n\n' which puts a blank line at significant
# points. Neither accepts '', no whitespace, between movetext tokens.  Neither
# needs move numbers or black move indicators.
# Hence the choice of default values.
def export_pgn_import_format(
    collected_game,
    name_value_separator=" ",
    tag_separator=" ",
    movetext_separator=" ",
    block_separator="\n",
    line_length=79,
):
    """Construct game score in a PGN import format.

    This method cannot generate text which is identical to internal format
    because the movetext tokens have check and checkmate indicator suffixes
    where appropriate.

    """
    if not isinstance(line_length, int):
        return "".join(
            (
                tag_separator.join(
                    collected_game.get_tags(
                        name_value_separator=name_value_separator
                    )
                ),
                block_separator,
                movetext_separator.join(collected_game.get_movetext()),
                block_separator,
            )
        )
    _attt = _add_token_to_text
    text = []
    length = 0
    for token in collected_game.get_tags(
        name_value_separator=name_value_separator
    ):
        length = _add_token_to_text(
            token, text, line_length, tag_separator, length
        )
    text.append(block_separator)
    length = len(block_separator.split("\n")[-1])
    for token in collected_game.get_movetext():
        if token.startswith("{"):
            comment = token.split()
            length = _add_token_to_text(
                comment.pop(0), text, line_length, movetext_separator, length
            )
            for word in comment:
                length = _add_token_to_text(
                    word, text, line_length, " ", length
                )
        elif token.startswith("$"):
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
        elif token.startswith(";"):
            if len(token) + length >= line_length:
                text.append("\n")
            else:
                text.append(movetext_separator)
            text.append(token)
            length = 0
        elif token == "(":
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
        elif token == ")":
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
        else:
            length = _add_token_to_text(
                token, text, line_length, movetext_separator, length
            )
    text.append(block_separator)
    return "".join(text)


get_game_pgn_import_format = export_pgn_import_format


# Derived from _add_token_to_movetext method in pgn_read.core.game module
# (before that was moved to chesstab.core.pgn).
def _add_token_to_text(token, text, line_length, token_separator, length):
    if not length:
        text.append(token)
        return len(token)
    if len(token) + length >= line_length:
        text.append("\n")
        text.append(token)
        return len(token)
    text.append(token_separator)
    text.append(token)
    return len(token) + length + len(token_separator)
