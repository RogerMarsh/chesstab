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

    # Defining a property current_row_background, in solentware_grid's
    # DataRow class, does not suppress the attribute-defined-outside-init
    # message from pylint, so a method is provided instead.

    def grid_row_on_display(self, **kargs):
        """Return grid_row() object with ON_DISPLAY_COLOUR background."""
        self.set_current_row_background(ON_DISPLAY_COLOUR)
        return self.grid_row(background=ON_DISPLAY_COLOUR, **kargs)

    def set_background_on_display(self, widgets):
        """Set background to ON_DISPLAY_COLOUR on all widgets."""
        self.set_current_row_background(ON_DISPLAY_COLOUR)
        self.set_background(widgets, self._current_row_background)
