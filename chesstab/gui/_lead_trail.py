# _lead_trail.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class with attributes to number of leading and trailing spaces."""


class _LeadTrail:
    """Attributes for number of leading and trailing spaces."""

    def __init__(self, lead, trail):
        """Initialize the description."""
        self._lead = lead
        self._trail = trail

    @property
    def lead(self):
        """Return number of leading spaces."""
        return self._lead

    @lead.setter
    def lead(self, value):
        """Set self._lead to value."""
        self._lead = value

    @property
    def trail(self):
        """Return number of trailing spaces."""
        return self._trail

    @trail.setter
    def trail(self, value):
        """Set self._trail to value."""
        self._trail = value

    @property
    def header_length(self):
        """Return number of packing spaces associated with token."""
        return self._lead + self._trail
