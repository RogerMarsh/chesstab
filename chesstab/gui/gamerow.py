# gamerow.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display tag roster details of games on database.
"""

import tkinter

from solentware_grid.gui.datarow import DataRow
from solentware_grid.gui.datarow import GRID_COLUMNCONFIGURE, GRID_CONFIGURE
from solentware_grid.gui.datarow import WIDGET_CONFIGURE, WIDGET, ROW

from pgn_read.core.constants import (
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
    TAG_EVENT,
    TAG_DATE,
    IFG_TAG_SYMBOL,
    IFG_TAG_STRING_VALUE,
    )

from ..core.chessrecord import ChessDBrecordGameTags
from .gamedbedit import ChessDBeditGame
from .gamedbdelete import ChessDBdeleteGame
from .gamedbshow import ChessDBshowGame
from . import constants

ON_DISPLAY_COLOUR = '#eba610' # a pale orange


class ChessDBrowGame(ChessDBrecordGameTags, DataRow):
    """Define row in list of games.

    Add row methods to the chess game record definition.

    """
    header_specification = [
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_WHITE, anchor=tkinter.W),
         GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='player'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_RESULT, anchor=tkinter.CENTER),
         GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='score'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_BLACK, anchor=tkinter.W),
         GRID_CONFIGURE: dict(column=2, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='player'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_EVENT, anchor=tkinter.W),
         GRID_CONFIGURE: dict(column=3, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='event'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_DATE, anchor=tkinter.W),
         GRID_CONFIGURE: dict(column=4, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='date'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text='Tags'),
         GRID_CONFIGURE: dict(column=5, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=4, uniform='tags', minsize=160),
         ROW: 0,
         },
        ]

    def __init__(self, database=None, ui=None):
        """Extend and associate record definition with database.

        database - the open database that is source of row data
        ui - the ChessUI instamce

        """
        super(ChessDBrowGame, self).__init__()
        self.ui = ui
        self.set_database(database)
        self.row_specification = [
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(
                 anchor=tkinter.W,
                 font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(
                 anchor=tkinter.CENTER,
                 font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(
                 anchor=tkinter.W,
                 font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=2, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(
                 anchor=tkinter.W,
                 font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=3, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Label,
             WIDGET_CONFIGURE: dict(
                 anchor=tkinter.W,
                 font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=4, sticky=tkinter.EW),
             ROW: 0,
             },
            {WIDGET: tkinter.Text,
             WIDGET_CONFIGURE: dict(
                 height=0,
                 relief=tkinter.FLAT,
                 font=constants.LISTS_OF_GAMES_FONT,
                 wrap=tkinter.NONE,
                 borderwidth=2, # hack to fill cell to row height from labels
                 ),
             GRID_CONFIGURE: dict(column=5, sticky=tkinter.EW),
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

    def grid_row(self, **kargs):
        """Return super(ChessDBrowGame,).grid_row(textitems=(...), **kargs).

        Create textitems argument for ChessDBrowGame instance.

        """
        tags = self.value.collected_game[1]
        return super(ChessDBrowGame, self).grid_row(
            textitems=(
                tags.get(TAG_WHITE, '?'),
                tags.get(TAG_RESULT, '?'),
                tags.get(TAG_BLACK, '?'),
                tags.get(TAG_EVENT, '?'),
                tags.get(TAG_DATE, '????.??.??'),
                self.value,
                ),
            **kargs)

    def populate_widget(self, widget, cnf=None, text=None, context=None, **kw):
        """Wrapper for Tkinter.Text configure method for score attribute"""
        if isinstance(widget, tkinter.Label):
            super(ChessDBrowGame, self).populate_widget(widget, text=text, **kw)
            return
        widget.configure(cnf=cnf, **kw)
        widget.configure(state=tkinter.NORMAL)
        widget.delete('1.0', tkinter.END)
        widget.insert(
            tkinter.END,
            '  '.join([''.join((tag, ' "', value, '"'))
                       for tag, value in self.get_tags_display_order(text)]))
        widget.configure(state=tkinter.DISABLED)
        
    def get_tags_display_order(self, pgn):
        str_tags = []
        other_tags = []
        for t in pgn.collected_game[0]:
            tn = t.group(IFG_TAG_SYMBOL)
            if tn not in constants.SEVEN_TAG_ROSTER_EXPORT_ORDER:
                other_tags.append((tn, t.group(IFG_TAG_STRING_VALUE)))
            elif tn not in constants.GRID_HEADER_SEVEN_TAG_ROSTER:
                str_tags.append((tn, t.group(IFG_TAG_STRING_VALUE)))
        return str_tags + other_tags

    def set_background_on_display(self, widgets):
        self._current_row_background = ON_DISPLAY_COLOUR
        self.set_background(widgets, self._current_row_background)

    def grid_row_on_display(self, **kargs):
        self._current_row_background = ON_DISPLAY_COLOUR
        return self.grid_row(background=ON_DISPLAY_COLOUR, **kargs)


def make_ChessDBrowGame(chessui):
    """Make ChessDBrowGame with reference to ChessUI instance"""
    def make_position(database=None):
        return ChessDBrowGame(database=database, ui=chessui)
    return make_position
