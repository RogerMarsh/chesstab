# and_.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate 'and' filter."""

import chessql.core.filters

from . import symbol


class And(symbol.Symbol):
    """Evaluate 'and' filter."""

    def __init__(self, *args):
        """Initialise an And instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.And)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Delegate to child symbols then do own evaluation.

        Arguments are passed to superclass method.

        The 'and' filter combines the results for it's two child filters and
        it's result is the elements in both children.

        """
        super().evaluate_symbol(
            cqlfinder, movenumber, cache, constraint=constraint
        )
        children = self.master.children
        self._data = children[0].node.data & children[1].node.data
