# queryedit.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a game selection rule and change main list of games to fit.

The QueryEdit class extends the query.Query class to allow editing.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

from .query import Query
from .eventspec import EventSpec


class QueryEdit(Query):

    """Display a game selection rule with editing allowed.

    Attribute _is_text_editable is True means the statement can be edited.

    """

    # True means selection selection can be edited
    _is_text_editable = True

    # Remove if this is all it is left doing.
    def __init__(self, **ka):
        """Extend game selection rule widget as editor."""
        super().__init__(**ka)
