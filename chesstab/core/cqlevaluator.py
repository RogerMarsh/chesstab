# cqlevaluator.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate a CQL filter in tree created by chessql parser."""
from . import filtermap


class CQLEvaluatorError(Exception):
    """Exception class for cqlevaluator module."""


class CQLEvaluator:
    """Evaluate element of query defined in node.

    The level and parent arguments guide construction of evaluation tree.
    """

    def __init__(self, mapkey=None, node=None, level=0, parent=None):
        """Initialise evaluator for node at level with parent node."""
        self._node = filtermap.filter_map[mapkey](node, self)
        self._level = level
        self._parent = parent
        self._answer = None
        self._children = []

    @property
    def node(self):
        """Return self._node."""
        return self._node

    @property
    def level(self):
        """Return self._level."""
        return self._level

    @property
    def parent(self):
        """Return self._parent."""
        return self._parent

    @property
    def children(self):
        """Return self._children."""
        return self._children

    @property
    def answer(self):
        """Return self._answer."""
        return self._answer

    def append_child(self, node):
        """Append node to children."""
        self._children.append(node)

    def has_children(self):
        """Return true if node has children."""
        return len(self._children) > 0

    def last_child(self):
        """Return last item in children."""
        return self._children[-1]

    def evaluator_tree_trace(self, trace=None):
        """Populate trace with evaluator tree for node in a print format.

        Trace should be a list.  On exit it will contain a str for each node
        indicating the number of ancestors and node type in CQL statement
        represented by the node.

        """
        if trace is None:
            trace = []
        depth = 0
        node = self
        while node:
            depth += 1
            node = node.parent
        # pylint C0209 consider-using-f-string.  f"{depth:>3}" not used
        # because 'depth' gets coloured as a "string" (typically green)
        # rather than as a local attribute (typically black).
        # The f-string documentation colours it 'right':
        # docs.python.org/3.10/reference/lexical_analysis.html#f-strings
        # but the Idle I have colours everything within the quotes green.
        # Ah! See github.com/python/cpython/issues/73473.
        trace.append(
            " ".join(
                (
                    "{:>3}".format(depth),
                    " " * depth,
                    self._node.__class__.__name__,
                    "evaluator",
                )
            )
        )
        for node in self._children:
            node.evaluator_tree_trace(trace=trace)

    def print_evaluator_tree_trace(self):
        """Print the evaluator tree rooted at self.

        Convenient for print debugging just before a raise statement.

        """
        tree_trace = []
        self.evaluator_tree_trace(trace=tree_trace)
        print("\n".join(tree_trace))
