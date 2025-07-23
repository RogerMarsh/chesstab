# cqlgrid.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Grids for lists of Chess Query Language (ChessQL) statements on database."""

from . import _cqlgrid
from .cqlrow import ChessDBrowCQL
from .cqlupdate import CQLUpdate
from .cqldelete import CQLDelete


class CQLListGrid(_cqlgrid.CQLListGrid):
    """A DataGrid for lists of ChessQL statements.

    Subclasses provide navigation and extra methods appropriate to list use.
    """

    def make_display_widget(self, sourceobject):
        """Return a CQLDelete instance."""
        selection = CQLDelete(
            master=self.ui.view_partials_pw,
            ui=self.ui,
            items_manager=self.ui.partial_items,
            itemgrid=self.ui.partial_games,
            sourceobject=sourceobject,
        )
        selection.cql_statement.prepare_cql_statement(
            sourceobject.get_srvalue()
        )
        return selection

    def make_edit_widget(self, sourceobject):
        """Return a ..gui.cqlinsert.CQLUpdate instance."""
        selection = CQLUpdate(
            master=self.ui.view_partials_pw,
            ui=self.ui,
            items_manager=self.ui.partial_items,
            itemgrid=self.ui.partial_games,
            sourceobject=sourceobject,
        )
        selection.cql_statement.prepare_cql_statement(
            sourceobject.get_srvalue()
        )
        return selection


class CQLGrid(_cqlgrid.CQLGrid, CQLListGrid):
    """Customized CQLListGrid for list of ChessQL statements."""

    def __init__(self, ui):
        """Extend with definition and bindings for ChessQL statements on grid.

        ui - container for user interface widgets and methods.

        """
        super().__init__(ui.partials_pw, ui)
        self.make_header(ChessDBrowCQL.header_specification)
        self.__bind_on()
        self._set_initial_bindings()

    def bind_off(self):
        """Disable all bindings."""
        super().bind_off()
        self._set_bindings_in_cqlgrid_bind_off()

    def bind_on(self):
        """Enable all bindings."""
        super().bind_on()
        self.__bind_on()

    def __bind_on(self):
        """Enable all bindings."""
        self._set_bindings_in_cqlgrid___bind_on()
