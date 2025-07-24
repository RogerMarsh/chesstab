# not_.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate 'not' filter."""

import chessql.core.filters

from . import symbol


class Not(symbol.Symbol):
    """Evaluate 'not' filter."""

    def __init__(self, *args):
        """Initialise a Not instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Not)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Delegate to child symbols then do own evaluation.

        Arguments are passed to superclass method.

        This method gives the complement of the result for the child filter.

        """
        super().evaluate_symbol(
            cqlfinder, movenumber, cache, constraint=constraint
        )
        move_answer = cqlfinder.db.recordlist_ebm(cqlfinder.dbset)
        move_answer.remove_recordset(self.master.children[0].node.data)
        self._data = move_answer
