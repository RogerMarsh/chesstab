# positionrow.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets to display tag roster details of games matching a position.
"""

import tkinter

from solentware_grid.gui.datarow import DataRow, NULL_COLOUR
from solentware_grid.gui.datarow import GRID_COLUMNCONFIGURE, GRID_CONFIGURE
from solentware_grid.gui.datarow import WIDGET_CONFIGURE, WIDGET, ROW

from pgn_read.core.constants import (
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
    )

from . import constants
from ..core.chessrecord import ChessDBrecordGamePosition
from .positionscore import PositionScore
from .gamedbedit import ChessDBeditGame
from .gamedbdelete import ChessDBdeleteGame
from .gamedbshow import ChessDBshowGame

ON_DISPLAY_COLOUR = '#eba610' # a pale orange


class ChessDBrowPosition(ChessDBrecordGamePosition, DataRow):
    
    """Define row in list of games for given position.

    Add row methods to the chess game record definition.
    
    """
    header_specification = [
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=''),
         GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='name'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text='Players'),
         GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=0, uniform='result', minsize=80),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=''),
         GRID_CONFIGURE: dict(column=2, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='name'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text='Score'),
         GRID_CONFIGURE: dict(column=3, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=4, uniform='move', minsize=160),
         ROW: 0,
         },
        ]

    def __init__(self, database=None, ui=None):
        """Extend and associate record definition with database.

        database - the open database that is source of row data
        ui - the ChessUI instamce

        """
        super(ChessDBrowPosition, self).__init__()
        self.ui = ui
        self.set_database(database)
        self.score = None
        self.row_specification = [
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=2, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Text,
             WIDGET_CONFIGURE: dict(
                 height=0,
                 relief=tkinter.FLAT,
                 font=constants.LISTS_OF_GAMES_FONT,
                 background=NULL_COLOUR,
                 wrap=tkinter.NONE,
                 borderwidth=2, # hack to fill cell to row height from labels
                 ),
             GRID_CONFIGURE: dict(column=3, sticky=tkinter.EW),
             ROW: 0,
             },
            ]
        
    def show_row(self, dialog, oldobject):
        """Return a ChessDBshowGame dialog for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return ChessDBshowGame(dialog, oldobject, ui=self.ui)
        
    def delete_row(self, dialog, oldobject):
        """Return a ChessDBdeleteGame dialog for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return ChessDBdeleteGame(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a ChessDBeditGame dialog for instance.

        dialog - a Toplevel
        newobject - a ChessDBrecordGame containing original data to be edited
        oldobject - a ChessDBrecordGame containing original data
        showintial == True - show both original and edited data

        """
        return ChessDBeditGame(newobject,
                               dialog,
                               oldobject,
                               showinitial=showinitial,
                               ui=self.ui)

    def grid_row(self, position=None, context=(None, None, None), **kargs):
        """Return super().grid_row(textitems=(...), **kargs).

        Create textitems argument for ChessDBrowPosition instance.

        """
        self.row_specification[3][WIDGET_CONFIGURE]['context'] = context
        tags = self.value.collected_game[1]
        lasttag = self.value.collected_game[0][-1]
        return super(ChessDBrowPosition, self).grid_row(
            textitems=(
                tags.get(TAG_WHITE, '?'),
                tags.get(TAG_RESULT, '?'),
                tags.get(TAG_BLACK, '?'),
                lasttag.string[lasttag.end():],
                ),
            **kargs)

    def grid_row_on_display(self, **kargs):
        self._current_row_background = ON_DISPLAY_COLOUR
        return self.grid_row(background=ON_DISPLAY_COLOUR, **kargs)

    def set_background(self, widgets, background):
        """Set background colour of widgets.

        widgets - list((widget, specification), ...).
        background - the background colour.

        Each element of widgets will have been created by make_row_widgets()
        or DataHeader.make_header_widgets() and reused by DataGrid instance
        in a data row.

        """
        for w, rs in zip(widgets, self.row_specification):
            if 'background' not in rs[WIDGET_CONFIGURE]:
                w[0].configure(background=background)

    def set_background_on_display(self, widgets):
        self._current_row_background = ON_DISPLAY_COLOUR
        self.set_background(widgets, self._current_row_background)

    def populate_widget(self, widget, cnf=None, text=None, context=None, **kw):
        """Wrapper for Tkinter.Text configure method for score attribute"""
        if isinstance(widget, tkinter.Label):
            super(ChessDBrowPosition, self).populate_widget(
                widget, text=text, **kw)
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
        widget.configure(cnf=cnf, **kw)


def make_ChessDBrowPosition(chessui):
    """Make ChessDBrowPosition with reference to ChessUI instance"""
    def make_position(database=None):
        return ChessDBrowPosition(database=database, ui=chessui)
    return make_position
