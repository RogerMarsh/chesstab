# cqledit.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a Chess Query Language (ChessQL) statement.

The CQLEdit class displays a ChessQL statement and allows editing.

This class has the cql.CQL class as a superclass.

This class does not allow deletion of ChessQL statements from a database.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

from .cql import CQL


class CQLEdit(CQL):
    
    """Display a ChessQL statement with editing allowed.
    """

    # True means ChessQL statement can be edited
    _is_cql_query_editable = True

    def __init__(self, **ka):
        """Extend ChessQL statement widget as editor."""
        super().__init__(**ka)
        self.bind_pointer()

    def bind_pointer(self):
        """Set pointer button-1 binding."""
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', ''), # go_to_token
            ('<ButtonPress-3>', ''),
            ):
            self.score.bind(sequence, function)

    def disable_keyboard(self):
        """Override and do nothing."""
