# fullposition.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for full position index providing methods which
do not need to know the particular engine used.

A superclass will include a base class for particular database engines.
"""

from ..core.filespec import POSITIONS_FIELD_DEF


class FullPosition:

    """Represent subset of games on file that match a postion."""

    def __init__(self, dbhome, dbset, dbname, newrow=None):
        """Extend to provide placeholder for position used to select games."""
        super().__init__(dbhome, dbset, dbname, newrow=newrow)

        # Position used as key to select games
        self.fullposition = None

    def get_full_position_games(self, fullposition):
        """Find game records matching full position."""
        self.fullposition = None
        if not fullposition:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return

        recordset = self.dbhome.recordlist_key(
            self.dbset,
            POSITIONS_FIELD_DEF,
            self.dbhome.encode_record_selector(fullposition),
        )

        self.set_recordset(recordset)
        self.fullposition = fullposition
