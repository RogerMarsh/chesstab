# cql_example.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Investigate converting CQL statements to ChessTab structure."""

import os
import tkinter.filedialog
import sys

from .. import cqlstatement


if __name__ == "__main__":

    class Statement(cqlstatement.CQLStatement):
        """Add access to protected attributes."""

        @property
        def query_evaluator(self):
            """Return the query evaluator."""
            return self._query_evaluator

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[-1]):
        query = sys.argv[-1]
    elif len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]):
        query = tkinter.filedialog.askopenfilename(
            title="CQL file", initialdir=os.path.expanduser(sys.argv[-1])
        )
    else:
        query = tkinter.filedialog.askopenfilename(
            title="CQL file", initialdir=os.path.expanduser("~")
        )
    if query:
        statement = Statement()
        with open(query, mode="r", encoding="utf-8") as queryfile:
            statement.prepare_cql_statement(queryfile.read())
        print()
        print(repr(statement.get_statement_text()))
        print()
        statement.query_container.print_parse_tree_trace()
        print()
        statement.query_evaluator.print_evaluator_tree_trace()
        print()
