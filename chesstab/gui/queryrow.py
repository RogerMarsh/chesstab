# queryrow.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display details of game selection rules."""

import tkinter

from solentware_grid.gui.datarow import (
    DataRow,
    GRID_COLUMNCONFIGURE,
    GRID_CONFIGURE,
    WIDGET_CONFIGURE,
    WIDGET,
    ROW,
)

from ..core.chessrecord import ChessDBrecordQuery
from .querydbedit import QueryDbEdit
from .querydbdelete import QueryDbDelete
from .querydbshow import QueryDbShow
from . import constants
from ..shared.allrow import AllRow


class ChessDBrowQuery(AllRow, ChessDBrecordQuery, DataRow):
    """Define row in list of game selection rules.

    Add row methods to the game selection rule record definition.

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
        """Return a QueryDbShow toplevel for oldobject.

        dialog - a Toplevel
        oldobject - a ChessDBrecordQuery containing original data

        """
        return QueryDbShow(parent=dialog, oldobject=oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a QueryDbDelete dialog for oldobject.

        dialog - a Toplevel
        oldobject - a ChessDBrecordQuery containing original data

        """
        return QueryDbDelete(parent=dialog, oldobject=oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a QueryDbEdit dialog for oldobject.

        dialog - a Toplevel
        newobject - a ChessDBrecordQuery containing original data to be
                    edited
        oldobject - a ChessDBrecordQuery containing original data
        showintial == True - show both original and edited data

        """
        return QueryDbEdit(
            newobject=newobject,
            parent=dialog,
            oldobject=oldobject,
            showinitial=showinitial,
            ui=self.ui,
        )

    def grid_row(self, textitems=(), **kargs):
        """Set textitems to selection query name, delegate, return response.

        Create textitems argument for ChessDBrowQuery instance.

        textitems arguments is ignored and is present for compatibility.

        """
        return super().grid_row(
            textitems=(self.value.get_name_text(),), **kargs
        )


def chess_db_row_query(chessui):
    """Return function which returns ChessDBrowQuery instance for chessui.

    The returned function takes an instance of a subclass of Database as
    it's argument.
    """

    def make_selection(database=None):
        return ChessDBrowQuery(database=database, ui=chessui)

    return make_selection
