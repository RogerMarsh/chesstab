# eventbinding.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide class which defines shared event binding methods.

The CQL, Game, and Query classes have a number of sets of event bindings
expressed identically in method calls.

The EventBinding class allows these method calls to be covered by an entry
in the ignored-classes list of a pylint configuration file without also
catching all the other members of the CQL, Game, and Query, classes.

The Game class has some event bindings which take account of the presence of
both the game score and analysis of positions within the game.

The AnalysisEventBinding class allows these to be covered by an entry in the
ignored-classes list of a pylint configuration file too.
"""
# The scorepgn module, and several others, were introduced to bundle shared
# methods on a fairly large scale.  It turned out the classes in these
# modules needed to be on the ignored-classes list for pylint.  It was not
# obvious which, if any, event binding methods needed to be treated in the
# same way until most of the initial set of no-member messages from pylint
# had been resolved.
from .eventspec import EventSpec


class EventBinding:
    """A collection of event binding methods shared by various classes.

    At present the classes are CQL, Game, and Query.
    """

    def set_database_navigation_close_item_bindings(self, switch=True):
        """Unset navigation bindings when query is closed."""
        self.set_event_bindings_score(
            self.get_database_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_navigation_events(), switch=switch
        )
        self.set_event_bindings_score(
            self.get_close_item_events(), switch=switch
        )


class AnalysisEventBinding:
    """The event binding methods which allow for analysis in Game."""

    def set_toggle_game_analysis_bindings(self, switch):
        """Set keystoke bindings to switch between game and analysis."""
        del switch
        self.set_event_bindings_score(
            ((EventSpec.scoresheet_to_analysis, self.analysis_current_item),)
        )
        self.analysis.set_event_bindings_score(
            ((EventSpec.analysis_to_scoresheet, self.current_item),)
        )

    def set_score_pointer_to_score_bindings(self, switch):
        """Set score pointer bindings to go to game."""
        self.set_event_bindings_score(
            ((EventSpec.alt_buttonpress_1, self.current_item),), switch=switch
        )

    def set_analysis_score_pointer_to_analysis_score_bindings(self, switch):
        """Set analysis score pointer bindings to go to analysis score."""
        self.analysis.set_event_bindings_score(
            ((EventSpec.alt_buttonpress_1, self.analysis_current_item),),
            switch=switch,
        )

    def set_analysis_event_bindings_score(self, switch=True):
        """Enable or disable bindings for navigation and database selection."""
        self.analysis.set_event_bindings_score(
            self.get_navigation_events(), switch=switch
        )
