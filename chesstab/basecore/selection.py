# selection.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Interface to chess database for selection rules index providing methods
which do not need to know the particular engine used.

A superclass will include a base class for particular database engines.
"""


class Selection:

    """Represent subset of games on file that match a selection rule."""

    def __init__(self, dbhome, dbset, dbname, newrow=None):
        super().__init__(dbhome, dbset, dbname, newrow=newrow)

    def get_selection_rule_games(self, fullposition):
        """Find game records matching selection rule."""
        if not fullposition:
            self.set_recordset(self.dbhome.recordlist_nil(self.dbset))
            return
        self.set_recordset(fullposition)
