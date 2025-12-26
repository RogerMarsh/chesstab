# cqlpgnify.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Generate input format PGN for CQL scan from tokens produced by lexer.

CQL 6.2 is known to fail processing PGN files containing '{' within '{}'
comments.  For example a number of games from 2003 in the download at

https://4ncl.co.uk/download/All_4NCL_1996_2010.pgn

have the '{{=}' comment (assumed to indicate a draw offer recorded on
the scoresheet).
"""

from . import pgnify
from .constants import START_COMMENT


class CQLPGNify(pgnify.PGNify):
    """Output input format PGN, with '{' in '{}' removed, to open file."""

    def tagpair_comment(self, token):
        """Override, append comment when tagpair expected."""
        self.file.write(START_COMMENT)
        self.file.write(token.replace(START_COMMENT, ""))
        self.file.write(self.newline)

    def movetext_comment(self, token):
        """Override, append comment when movetext expected."""
        self.file.write(START_COMMENT)
        self.file.write(token.replace(START_COMMENT, ""))
        self.file.write(self.space)
