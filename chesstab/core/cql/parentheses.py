# parentheses.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate () filter."""

import chessql.core.filters

from . import symbol


class Parentheses(symbol.Symbol):
    """Evaluate () filter."""

    def __init__(self, *args):
        """Initialise a ParenthesisLeft instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.ParenthesisLeft)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Delegate to child symbols then do own evaluation.

        Arguments are passed to superclass method.

        Filters within parentheses resolve to a single child filter so the
        result is that found for the only child filter.

        """
        super().evaluate_symbol(
            cqlfinder, movenumber, cache, constraint=constraint
        )
        self._data = self.master.children[0].node.data
