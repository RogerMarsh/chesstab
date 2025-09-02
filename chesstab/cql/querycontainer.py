# querycontainer.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Run CQL program against games on database.

This module defines the QueryContainer class.  An instance of this class
runs the CQL program using the *.cql file and *.pgn file associated with
a database.  Both files are generated from the database as needed.
"""
import os

from ..core import constants
from . import queryevaluator

_ENCODING = "utf-8"


class QueryContainer:
    """The top level node for a CQL statement."""

    def __init__(self):
        """Set details for root of node tree."""
        self._evaluator = queryevaluator.QueryEvaluator()
        self._message = None

    @property
    def evaluator(self):
        """Return evaluator."""
        return self._evaluator

    @property
    def message(self):
        """Return error message or None."""
        return self._message

    def prepare_statement(self, statement, text):
        """Verify CQL statement is accepted by CQL program.

        A null game is output to a PGN file to be the input parameter to
        the 'cql -parse' command for a CQL query.  It is deleted after
        parsing the CQL query.

        """
        title_end = statement.split_statement(text)
        del title_end
        evaluator = self.evaluator
        evaluator.find_command(statement.database_file)
        if evaluator.message:
            self._message = evaluator.message
            return
        evaluator.verify_command_is_cql()
        if evaluator.message:
            self._message = evaluator.message
            return
        pgn_file = "".join(
            (
                statement.database_file,
                "-",
                os.path.basename(statement.database_file),
                "-parse",
                ".pgn",
            )
        )
        with open(pgn_file, "w", encoding=_ENCODING) as gamesout:
            gamesout.write(constants.NULL_GAME_TEXT)
        try:
            evaluator.verify_cql_pqn_input_is_present(pgn_file)
            if evaluator.message:
                self._message = evaluator.message
                return
            evaluator.write_cql_statement_file(
                statement.get_statement_text(), statement
            )
            if evaluator.message:
                self._message = evaluator.message
                return
            evaluator.parse_statement(statement, pgn_file)
            if evaluator.message:
                self._message = evaluator.message
                return
        finally:
            try:
                os.remove(pgn_file)
            except FileNotFoundError:
                pass
