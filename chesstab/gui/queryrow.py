# queryrow.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display details of game selection rules on database.
"""

import tkinter

from solentware_grid.gui.datarow import (
    GRID_COLUMNCONFIGURE,
    GRID_CONFIGURE,
    WIDGET_CONFIGURE,
    WIDGET,
    ROW,
)

from .datarow import DataRow
from ..core.chessrecord import ChessDBrecordQuery
from .querydbedit import QueryDbEdit
from .querydbdelete import QueryDbDelete
from .querydbshow import QueryDbShow
from . import constants

ON_DISPLAY_COLOUR = "#eba610"  # a pale orange


class ChessDBrowQuery(ChessDBrecordQuery, DataRow):

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
        return QueryDbShow(dialog, oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a QueryDbDelete dialog for oldobject.

        dialog - a Toplevel
        oldobject - a ChessDBrecordQuery containing original data

        """
        return QueryDbDelete(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a QueryDbEdit dialog for oldobject.

        dialog - a Toplevel
        newobject - a ChessDBrecordQuery containing original data to be
                    edited
        oldobject - a ChessDBrecordQuery containing original data
        showintial == True - show both original and edited data

        """
        return QueryDbEdit(
            newobject, dialog, oldobject, showinitial=showinitial, ui=self.ui
        )

    def grid_row(self, **kargs):
        """Return super().grid_row(textitems=(...), **kargs).

        Create textitems argument for ChessDBrowQuery instance.

        """
        return super().grid_row(
            textitems=(
                self.value.get_name_text(),
                # self.value.get_selection_rule_text(),
            ),
            **kargs
        )

    def grid_row_on_display(self, **kargs):
        self._current_row_background = ON_DISPLAY_COLOUR
        return self.grid_row(background=ON_DISPLAY_COLOUR, **kargs)

    def set_background_on_display(self, widgets):
        self._current_row_background = ON_DISPLAY_COLOUR
        self.set_background(widgets, self._current_row_background)


def make_ChessDBrowQuery(chessui):
    """Make ChessDBrowQuery with reference to ChessUI instance"""

    def make_selection(database=None):
        return ChessDBrowQuery(database=database, ui=chessui)

    return make_selection
