# cqldbedit.py
# Copyright 2016, 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit toplevel to edit or insert ChessQL statement record.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""
from . import _cqldbedit


class CQLDbEdit(_cqldbedit.CQLDbEditBase):
    """Edit ChessQL statement on database, or insert a new record.

    Customise the CQLDbEditBase edit and put methods for chesstab
    internal evaluation of CQL statements.
    """

    def prepare_cql_statement(self):
        """Fit CQLStatement class to CQLDbEdit class."""
        value = self.newobject.value
        value.prepare_cql_statement(value.get_name_statement_text())
