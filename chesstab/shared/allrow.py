# allrow.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions, and AllRow class for methods, used by all *Row classes.

'All' means ChessDBrowCQL, ChessDBrowEngine, ChessDBrowGame,
ChessDBrowPosition, ChessDBrowQuery, and ChessDBrowRepertoire, classes.
"""

ON_DISPLAY_COLOUR = "#eba610"  # a pale orange


class AllRow:
    """Provide methods with default implementation for *Row classes.

    Subclasses should override methods as needed.

    """

    def grid_row_on_display(self, **kargs):
        """Return grid_row() object with ON_DISPLAY_COLOUR background."""
        self._init_current_row_background()
        return self.grid_row(background=ON_DISPLAY_COLOUR, **kargs)

    def set_background_on_display(self, widgets):
        """Set background to ON_DISPLAY_COLOUR on all widgets."""
        self._init_current_row_background()
        self.set_background(widgets, self._current_row_background)

    def _init_current_row_background(self):
        """Initialize _current_row_background to ON_DISPLAY_COLOUR.

        This method exists to be added to the defining-attr-methods list
        in pylint configuration.
        """
        assert hasattr(self, "_current_row_background")
        self._current_row_background = ON_DISPLAY_COLOUR
