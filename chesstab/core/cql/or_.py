# or_.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate 'or' filter."""

import chessql.core.filters

from . import symbol


class Or(symbol.Symbol):
    """Evaluate 'or' filter."""

    def __init__(self, *args):
        """Initialise an Or instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Or)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Delegate to child symbols then do own evaluation.

        Arguments are passed to superclass method.

        The 'or' filter combines the results for it's two child filters and
        it's result is the elements in at least one of the children.

        """
        super().evaluate_symbol(
            cqlfinder, movenumber, cache, constraint=constraint
        )
        children = self.master.children
        self._data = children[0].node.data | children[1].node.data
