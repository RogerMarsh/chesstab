# cqlparameters.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class to evaluate CQL top-level parameters."""

import chessql.core.cql

from . import symbol
from .. import filespec


class CQLParameters(symbol.Symbol):
    """Evaluate parameters given in 'cql(...)' phrase."""

    def __init__(self, *args):
        """Initialise the top-level parameters for the CQL statement."""
        super().__init__(*args)
        self._verify_token_is(chessql.core.cql.CQL)

    def evaluate_symbol(self, cqlfinder, *args, commit=True, **kwargs):
        """Eveluate child symbols for each move."""
        del args, kwargs
        if commit:
            cqlfinder.db.start_read_only_transaction()
        query_answer = cqlfinder.db.recordlist_nil(cqlfinder.dbset)
        move_initial = cqlfinder.db.recordlist_ebm(cqlfinder.dbset)
        highkey = self._get_high_move_number(cqlfinder.db, cqlfinder.dbset)
        if highkey is not None:
            for key in self.move_number_in_key_range(highkey):
                self.evaluate_child_symbols(
                    cqlfinder, self.move_number_str(key), {}, constraint=None
                )
                move_answer = cqlfinder.db.recordlist_nil(cqlfinder.dbset)
                move_answer |= move_initial
                for child in self.master.children:
                    move_answer &= child.node.data
                query_answer |= move_answer
            self._data = query_answer
        if commit:
            cqlfinder.db.end_read_only_transaction()

    def _get_high_move_number(self, dbhome, dbset):
        """Return high move number key on database (dbhome, dbset).

        The value could be taken from several indicies apart from the
        one chosen.

        """
        cursor = dbhome.database_cursor(
            dbset, filespec.PIECESQUAREMOVE_FIELD_DEF
        )
        try:
            return cursor.last()[0]
        except TypeError:
            return None
        finally:
            cursor.close()
            del cursor
