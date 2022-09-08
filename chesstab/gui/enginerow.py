# enginerow.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets to display details of chess engines emabled for database."""

import tkinter

from solentware_grid.gui.datarow import (
    GRID_COLUMNCONFIGURE,
    GRID_CONFIGURE,
    WIDGET_CONFIGURE,
    WIDGET,
    ROW,
)

from .datarow import DataRow
from ..core.chessrecord import ChessDBrecordEngine
from .enginedbedit import EngineDbEdit
from .enginedbdelete import EngineDbDelete
from .enginedbshow import EngineDbShow
from . import constants
from ..shared.allrow import AllRow


class ChessDBrowEngine(AllRow, ChessDBrecordEngine, DataRow):
    """Define row in list of chess engines.

    Add row methods to the chess engine record definition.

    """

    header_specification = [
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text="Description",
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="pp"),
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
                WIDGET_CONFIGURE: dict(
                    anchor=tkinter.W,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=0,
                ),
                GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
                ROW: 0,
            },
        ]

    def show_row(self, dialog, oldobject):
        """Return a EngineDbShow toplevel for oldobject.

        dialog - a Toplevel
        oldobject - a ChessDBrecordEngine containing original data

        """
        return EngineDbShow(dialog, oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a EngineDbDelete toplevel for oldobject.

        dialog - a Toplevel
        oldobject - a ChessDBrecordEngine containing original data

        """
        return EngineDbDelete(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a EngineDbEdit toplevel for oldobject.

        dialog - a Toplevel
        newobject - a ChessDBrecordEngine containing original data to be
                    edited
        oldobject - a ChessDBrecordEngine containing original data
        showintial == True - show both original and edited data

        """
        return EngineDbEdit(
            newobject, dialog, oldobject, showinitial=showinitial, ui=self.ui
        )

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    def grid_row(self, **kargs):
        """Return ChessDBrowEngine() with text set to engine name."""
        return super().grid_row(
            textitems=(
                self.value.get_name_text(),
                # self.value.get_selection_rule_text(),
            ),
            **kargs
        )


def make_ChessDBrowEngine(chessui):
    """Make ChessDBrowEngine with reference to ChessUI instance."""

    def make_engine(database=None):
        return ChessDBrowEngine(database=database, ui=chessui)

    return make_engine
