# fullposition.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for full position index.

Methods which do not need to know the particular engine used are defined here.

A superclass will include a base class for particular database engines.
"""

from ..core.filespec import POSITIONS_FIELD_DEF


class FullPosition:
    """Represent subset of games on file that match a position."""

    def __init__(self, dbhome, dbset, dbname, newrow=None):
        """Extend to provide placeholder for position used to select games."""
        super().__init__(dbhome, dbset, dbname, newrow=newrow)

        # Position used as key to select games
        self._fullposition = None

    @property
    def fullposition(self):
        """Return FEN representation of a game position."""
        return self._fullposition

    @fullposition.setter
    def fullposition(self, value):
        """Set fullposition to value which should be a FEN string or None."""
        assert isinstance(value, str) or value is None
        self._fullposition = value


class _FullPosition:
    """Methods shared by basecore and dpt subclasses of FullPosition."""

    def get_full_position_games(self, fullposition):
        """Find game records matching full position."""
        if not fullposition:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return None

        recordset = self.dbhome.recordlist_key(
            self.dbset,
            POSITIONS_FIELD_DEF,
            self.dbhome.encode_record_selector(fullposition),
        )

        self.set_recordset(recordset)
        return fullposition
