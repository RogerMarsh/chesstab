# braces.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate {} filter."""

import chessql.core.filters

from . import symbol


class Braces(symbol.Symbol):
    """Evaluate {} filter."""

    def __init__(self, *args):
        """Initialise a BraceLeft instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.BraceLeft)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Delegate to child symbols then do own evaluation.

        Arguments are passed to superclass method.  This method combines
        the results found by child filters evaluated via super().

        """
        super().evaluate_symbol(
            cqlfinder, movenumber, cache, constraint=constraint
        )
        move_answer = cqlfinder.db.recordlist_ebm(cqlfinder.dbset)
        for child in self.master.children:
            move_answer &= child.node.data
        self._data = move_answer
