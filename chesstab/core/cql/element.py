# element.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide base class for evaluating elements of CQL statements."""

from ast import literal_eval

from solentware_base.core.where import Where

from ..constants import MOVE_NUMBER_KEYS


class Element:
    """Base class for evaluating CQL filters.

    The _token attribute is an instance of a subclass of ChessQL class
    chessql.core.basenode.BaseNode from the chessql.core.filters module.

    The _master attribute is the CQLEvaluator instance which references
    this Symbol instance in it's _node attribute.  The parameter and
    argument Symbol instances are referenced via the _children attribute
    of the _master attribute instance.

    The _where attribute holds the database query which evaluates the
    token for a move number.

    The _data attribute holds the recordset found for the database query
    for a move number.
    """

    def __init__(self):
        """Delegate then initialise child filter definitions."""
        self._data = None
        self._where = None

    @property
    def data(self):
        """Return self._data."""
        return self._data

    @property
    def where(self):
        """Return self._where."""
        return self._where

    @staticmethod
    def move_number_in_key_range(key):
        """Yield the move number keys in a range one-by-one.

        Used in CQLParameters subclass but with modification may serve
        the 'path' filter's class too when implemented.

        """
        yield from range(0, literal_eval("0x" + key[1 : int(key[0]) + 1]) + 1)

    @staticmethod
    def move_number_str(movenumber):
        """Return hex(movenumber) values prefixed with string length.

        A '0x' prefix is removed first.

        """
        # Adapted from module pgn_read.core.parser method add_move_to_game().
        try:
            return MOVE_NUMBER_KEYS[movenumber]
        except IndexError:
            base16 = hex(movenumber)
            return str(len(base16) - 2) + base16[2:]

    def evaluate_statement(self, cqlfinder):
        """Return foundset calcualted from statement."""
        wqs = Where(self._where)
        wqs.lex()
        wqs.parse()
        wqs.validate(cqlfinder.db, cqlfinder.dbset)
        wqs.evaluate(cqlfinder)
        self._data = wqs.get_node_result_answer()
