# queryedit.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Edit a game selection rule and change main list of games to fit.

The QueryEdit class displays a game selection rule and allows editing.

This class has the query.Query class as a superclass.

This class does not allow deletion of game selection rules from a database.

An instance of these classes fits into the user interface in two ways: as an
item in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

from ..core.querystatement import QueryStatement
from .query import Query
from .eventspec import EventSpec


class QueryEdit(Query):
    
    """Display a game selection rule with editing allowed.
    """

    # True means selection selection can be edited
    _is_query_editable = True

    def __init__(self, **ka):
        """Extend game selection rule widget as editor."""
        super(QueryEdit, self).__init__(**ka)
        self.bind_pointer()
        # Context is same for each location so do not need dictionary of
        # QueryStatement instances.
        self.selection_token_checker = QueryStatement()
        # Not needed or set selection_token_checker (.querytext module sets
        # query_statement's attribute.
        #self.query_statement.dbset = self.ui.base_games.datasource.dbset
        if self.ui.base_games.datasource:
            self.selection_token_checker.dbset = self.ui.base_games.datasource.dbset

    def bind_for_viewmode(self):
        """Set keyboard bindings for game selection rule display."""
        super(QueryEdit, self).bind_for_viewmode()
        for sequence, function in (
            ):
            if function:
                function = self.try_event(function)
            self.score.bind(sequence[0], function)

    def bind_pointer(self):
        """Set pointer button-1 binding."""
        for sequence, function in (
            ('<Control-ButtonPress-1>', ''),
            ('<ButtonPress-1>', ''), # go_to_token
            ('<ButtonPress-3>', ''),
            ):
            self.score.bind(sequence, function)
        
    def set_query_statement(self, **kargs):
        """Display the game selection rule as search creteria text."""
        super().set_query_statement(**kargs)
        self.bind_for_viewmode()

    def disable_keyboard(self):
        """Override and do nothing."""
