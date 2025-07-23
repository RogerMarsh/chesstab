# cqlcontainer.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate a CQL statement with chesstab internal evaluator."""
import chessql.core.parser
import chessql.core.querycontainer

from . import cqlevaluator


class CQLContainer(chessql.core.querycontainer.QueryContainer):
    """Lex and parse the ChessQL statement and prepare evaluation tree."""

    def __init__(self, **kwargs):
        """Set details for root of node tree."""
        super().__init__(**kwargs)
        self._evaluator = None
        self._message = None

    @property
    def evaluator(self):
        """Return evaluator."""
        return self._evaluator

    @property
    def message(self):
        """Return error message or None."""
        return self._message

    def prepare_statement(self, statement, text):
        """Prepare evaluation tree for ChessQL statement."""
        title_end = statement.split_statement(text)
        chessql.core.parser.populate_container(self, text, title_end)
        tree = []
        self.parse_tree_node(trace=tree)
        level = 0
        node = None
        if tree:
            level, node = tree.pop(0)
        if node is self:
            mapkey = chessql.core.querycontainer.QueryContainer
        else:
            mapkey = node.__class__
        self._evaluator = cqlevaluator.CQLEvaluator(
            mapkey=mapkey, node=node, level=level
        )
        cursor = self._evaluator
        for level, node in tree:
            if node is self:
                mapkey = chessql.core.querycontainer.QueryContainer
            else:
                mapkey = node.__class__
            if level > cursor.level + 2:
                self._message = "".join(
                    (
                        node.class__.__name__.join("''"),
                        " is level ",
                        str(level).join("''"),
                        " but level ",
                        str(cursor.level + 1).join("''"),
                        " or less is expected",
                    )
                )
                return
            if level == cursor.level + 2:
                if not cursor.has_children():
                    self._message = "".join(
                        (
                            node.class__.__name__.join("''"),
                            " is level ",
                            str(level).join("''"),
                            " but level ",
                            str(cursor.level + 1).join("''"),
                            " has no children",
                        )
                    )
                    return
                cursor = cursor.last_child()
                cursor.append_child(
                    cqlevaluator.CQLEvaluator(
                        mapkey=mapkey, node=node, level=level, parent=cursor
                    )
                )
                continue
            if level == cursor.level + 1:
                cursor.append_child(
                    cqlevaluator.CQLEvaluator(
                        mapkey=mapkey, node=node, level=level, parent=cursor
                    )
                )
                continue
            while cursor and level <= cursor.level:
                cursor = cursor.parent
            cursor.append_child(
                cqlevaluator.CQLEvaluator(
                    mapkey=mapkey, node=node, level=level, parent=cursor
                )
            )
