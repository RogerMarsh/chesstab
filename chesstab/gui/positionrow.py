# positionrow.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets to display tag roster details of games matching position."""
# Put transposition moves in column 0 rather than column 4.
# Display just the moves played in, and to reach, the position.

import tkinter
from ast import literal_eval

from solentware_grid.gui.datarow import (
    DataRow,
    GRID_COLUMNCONFIGURE,
    GRID_CONFIGURE,
    WIDGET_CONFIGURE,
    WIDGET,
    ROW,
)

from . import constants
from ..core.chessrecord import ChessDBrecordGamePosition
from .positionscore import PositionScore
from ..shared.allrow import AllRow
from ..shared.game_position import GamePosition


class ChessDBrowPosition(
    GamePosition, AllRow, ChessDBrecordGamePosition, DataRow
):
    """Define row in list of games for given position.

    Add row methods to the chess game record definition.

    """

    header_specification = [
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text="Transposition",
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="move"),
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
        self.score = None
        self.row_specification = [
            {
                WIDGET: tkinter.Text,
                WIDGET_CONFIGURE: dict(
                    height=0,
                    relief=tkinter.FLAT,
                    font=constants.LISTS_OF_GAMES_FONT,
                    wrap=tkinter.NONE,
                    borderwidth=2,  # fill cell to row height from labels
                ),
                GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
                ROW: 0,
            },
        ]

    def grid_row(self, textitems=(), **kargs):
        """Delegate to __grid_row and reurn response."""
        return self.__grid_row(textitems=textitems, **kargs)

    def __grid_row(
        self, textitems=(), position=None, context=(None, None, None), **kargs
    ):
        """Set textitems to record value, delegate, return response.

        Create textitems argument for ChessDBrowPosition instance.

        The record value is expected to contain transposition details.

        textitems arguments is ignored and is present for compatibility.

        """
        del textitems
        del position
        self.row_specification[0][WIDGET_CONFIGURE]["context"] = context
        return super().grid_row(
            textitems=(literal_eval(self.srvalue),), **kargs
        )

    def set_background(self, widgets, background):
        """Set background colour of widgets.

        widgets - list((widget, specification), ...).
        background - the background colour.

        Each element of widgets will have been created by make_row_widgets()
        or DataHeader.make_header_widgets() and reused by DataGrid instance
        in a data row.

        """
        for widget, rowspec in zip(widgets, self.row_specification):
            if "background" not in rowspec[WIDGET_CONFIGURE]:
                widget[0].configure(background=background)

    def populate_widget(self, widget, cnf=None, text=None, **kw):
        """Delegate to __populate_widget."""
        self.__populate_widget(widget, cnf=cnf, text=text, **kw)

    def __populate_widget(
        self, widget, cnf=None, text=None, context=None, **kw
    ):
        """Delegate for tkinter.Label widget, put text in a PositionScore.

        The context argument is only relevant for the PositionScore.

        """
        if isinstance(widget, tkinter.Label):
            super().populate_widget(widget, cnf=cnf, text=text, **kw)
            return
        # This is the place to implement a pool of pre-processed PositionScore
        # instances which only need to call the colour_score() method rather
        # than the process_score() method.
        # Goal is to speed up populating widget showing games containing
        # current position of active game when the widget is able to list more
        # than a few (<5 say) games.
        if text:
            if self.score is None:
                self.score = PositionScore(widget, ui=self.ui, **kw)
            self.score.process_score(text=text, context=context)
        kw["width"] = self.score.score.count("1.0", tkinter.END, "chars")[0]
        widget.configure(cnf=cnf, **kw)


def chess_db_row_position(chessui):
    """Return function that returns ChessDBrowPosition instance for chessui.

    chessui is a chess_ui.ChessUI instance.

    The returned function takes a ChessDatabase instance as it's argument.
    """

    def make_position(database=None):
        return ChessDBrowPosition(database=database, ui=chessui)

    return make_position
