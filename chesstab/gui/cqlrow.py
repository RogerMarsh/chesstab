# cqlrow.py
# Copyright 2016, 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets to display Chess Query Language (ChessQL) statement.

Adapt chesstab.gui._cqlrow.ChessDBrowCQL class to use chesstab version
of CQLDbEdit class.
"""

import tkinter

from solentware_grid.gui.datarow import (
    GRID_COLUMNCONFIGURE,
    GRID_CONFIGURE,
    WIDGET_CONFIGURE,
    WIDGET,
    ROW,
    DataRow,
)

from ..core.chessrecord import ChessDBrecordPartial
from .cqldbdelete import CQLDbDelete
from .cqldbshow import CQLDbShow
from . import constants
from ..shared.allrow import AllRow
from .cqldbedit import CQLDbEdit


class ChessDBrowCQL(AllRow, ChessDBrecordPartial, DataRow):
    """Define row in list of ChessQL statements.

    Add row methods to the ChessQL statement record definition.

    """

    header_specification = [
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: {
                "text": "Description",
                "anchor": tkinter.W,
                "padx": 0,
                "pady": 1,
                "font": "TkDefaultFont",
            },
            GRID_CONFIGURE: {"column": 0, "sticky": tkinter.EW},
            GRID_COLUMNCONFIGURE: {"weight": 1, "uniform": "pp"},
            ROW: 0,
        },
    ]

    def __init__(self, database=None, ui=None):
        """Extend and associate record definition with database.

        database - the open database that is source of row data
        ui - the ChessUI instamce

        """
        super().__init__()
        self.ui = ui
        self.set_database(database)
        self.row_specification = [
            {
                WIDGET: tkinter.Label,
                WIDGET_CONFIGURE: {
                    "anchor": tkinter.W,
                    "font": constants.LISTS_OF_GAMES_FONT,
                    "pady": 1,
                    "padx": 0,
                },
                GRID_CONFIGURE: {"column": 0, "sticky": tkinter.EW},
                ROW: 0,
            },
        ]

    def show_row(self, dialog, oldobject):
        """Return a CQLDbShow dialog for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordPartial containing original data

        """
        return CQLDbShow(parent=dialog, oldobject=oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a CQLDbDelete dialog for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordPartial containing original data

        """
        return CQLDbDelete(parent=dialog, oldobject=oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a CQLDbEdit dialog for instance.

        dialog - a Toplevel
        newobject - a ChessDBrecordPartial containing original data to be
                    edited
        oldobject - a ChessDBrecordPartial containing original data
        showintial == True - show both original and edited data

        """
        return CQLDbEdit(
            newobject=newobject,
            parent=dialog,
            oldobject=oldobject,
            showinitial=showinitial,
            ui=self.ui,
        )

    def grid_row(self, textitems=(), **kargs):
        """Set textitems to CQL query name, delegate, return response.

        Create textitems argument for ChessDBrowCQL instance.

        textitems arguments is ignored and is present for compatibility.

        """
        return super().grid_row(
            textitems=(self.value.get_name_text(),), **kargs
        )


def chess_db_row_cql(chessui):
    """Return function that returns ChessDBrowCQL instance for chessui.

    chessui is a chess_ui.ChessUI instance.

    The returned function takes a Database instance as it's argument.
    """

    def make_selection(database=None):
        return ChessDBrowCQL(database=database, ui=chessui)

    return make_selection
