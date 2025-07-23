# container.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate CQL query top-level filter."""

import chessql.core.querycontainer

from . import symbol


class Container(symbol.Symbol):
    """Evaluate query in container children."""

    def __init__(self, *args):
        """Initialise a Container instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.querycontainer.QueryContainer)

    def evaluate_symbol(self, cqlfinder, *args, commit=True, **kwargs):
        """Delegate to child symbols then do own evaluation."""
        del args, kwargs
        self.evaluate_child_symbols(cqlfinder, commit=commit)
        children = self.master.children
        if not children:
            self._data = cqlfinder.db.recordlist_nil(cqlfinder.dbset)
        else:
            self._data = children[-1].node.data
