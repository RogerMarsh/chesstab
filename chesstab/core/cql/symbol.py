# symbol.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide base class for evaluating tokens in CQL statements.

Tokens are mostly filters; but some represent parameters to filters
which are not, strictly speaking, filters themselves.
"""

from . import element


class SymbolError(Exception):
    """Exception raised for problems in Symbols."""


class Symbol(element.Element):
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

    def __init__(self, token, master):
        """Delegate then initialise child filter definitions."""
        super().__init__()
        self._token = token
        self._master = master
        self._orbit_index = None

    @property
    def token(self):
        """Return self._token."""
        return self._token

    @property
    def master(self):
        """Return self._master."""
        return self._master

    def _verify_token_is(self, token_class):
        """Raise SymbolError if self._token is not a token_class instance."""
        if isinstance(self._token, token_class):
            return
        raise SymbolError("Node's filter is not a " + repr(token_class))

    def expand_symbol(self):
        """Expand child symbols.

        Most subclasses will use this method.  Some, such as the subclass
        for piece designators, will extend it.

        """
        for child in self.master.children:
            child.node.expand_symbol()

    def prepare_to_evaluate_symbol(self):
        """Call prepare_to_evaluate_symbol for all children.

        Many subclasses will override this method.

        """
        for child in self.master.children:
            child.node.prepare_to_evaluate_symbol()

    def collect_transform_targets(self, targets):
        """Call collect_transform_targets for all children.

        Some subclasses will override this method.

        """
        for child in self.master.children:
            child.node.collect_transform_targets(targets)

    def evaluate_child_symbols(self, *args, **kwargs):
        """Process filter arguments for movenumber.

        Most subclasses will use this method.

        """
        for child in self.master.children:
            child.node.evaluate_symbol(*args, **kwargs)

    def evaluate_symbol(self, cqlfinder, movenumber, cache, constraint=None):
        """Process filter for movenumber.

        Most subclasses will override this method.

        """
        self.evaluate_child_symbols(
            cqlfinder, movenumber, cache, constraint=constraint
        )
