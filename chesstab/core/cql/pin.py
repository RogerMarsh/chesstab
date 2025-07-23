# pin.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate CQL pin filter."""

import chessql.core.filters

from . import symbol
from . import parameters


class Pin(symbol.Symbol):
    """Evaluate CQL pin filter."""

    def __init__(self, *args):
        """Initialise a Pin instance for filter_."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.filters.Pin)
        self._pin_set = None
        self._from = None
        self._through = None
        self._to = None

    def expand_symbol(self):
        """Delegate to child symbols then do own expanding.

        Note the 'through', 'from', and 'to', filter arguments and note
        the first argument as providing the 'pin' filter set value.

        """
        super().expand_symbol()
        self._pin_set = self.master.children[0].children[0].node
        for child in self.master.children:
            if isinstance(child.node, parameters.FromParameter):
                self._from = child.children[0].node
            elif isinstance(child.node, parameters.Through):
                self._through = child.children[0].node
            elif isinstance(child.node, parameters.ToParameter):
                self._to = child.children[0].node
