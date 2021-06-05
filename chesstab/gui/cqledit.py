# cqledit.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a Chess Query Language (ChessQL) statement.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

The CQLEdit class extends the cql.CQL class to allow editing.

An instance of this class fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

from .cql import CQL


class CQLEdit(CQL):

    """Display a ChessQL statement with editing allowed.

    Attribute _is_text_editable is True meaning the statement can be
    edited.

    """

    # True means ChessQL statement can be edited
    _is_text_editable = True

    # Remove if this is all it is left doing.
    def __init__(self, **ka):
        """Extend ChessQL statement widget as editor."""
        super().__init__(**ka)
