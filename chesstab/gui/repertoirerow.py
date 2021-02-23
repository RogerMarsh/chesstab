# repertoirerow.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display tag roster details of repertoire.
"""

import tkinter

from solentware_grid.gui.datarow import DataRow
from solentware_grid.gui.datarow import GRID_COLUMNCONFIGURE, GRID_CONFIGURE
from solentware_grid.gui.datarow import WIDGET_CONFIGURE, WIDGET, ROW

from pgn_read.core.constants import (
    TAG_OPENING,
    TAG_RESULT,
    REPERTOIRE_GAME_TAGS,
    IFG_TAG_SYMBOL,
    IFG_TAG_STRING_VALUE,
    )

from ..core.chessrecord import ChessDBrecordRepertoireTags
from .repertoiredbedit import ChessDBeditRepertoire
from .repertoiredbdelete import ChessDBdeleteRepertoire
from .repertoiredbshow import ChessDBshowRepertoire
from . import constants

ON_DISPLAY_COLOUR = '#eba610' # a pale orange


class ChessDBrowRepertoire(ChessDBrecordRepertoireTags, DataRow):
    """Define row in list of repertoires.

    Add row methods to the chess game record definition.

    """
    header_specification = [
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_OPENING, anchor=tkinter.W),
         GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='player'),
         ROW: 0,
         },
        {WIDGET: tkinter.Label,
         WIDGET_CONFIGURE: dict(text=TAG_RESULT, anchor=tkinter.W),
         GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
         GRID_COLUMNCONFIGURE: dict(weight=1, uniform='result'),
         ROW: 0,
         },
        ]

    def __init__(self, database=None, ui=None):
        """Extend and associate record definition with database.

        database - the open database that is source of row data
        ui - the ChessUI instamce

        """
        super(ChessDBrowRepertoire, self).__init__()
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
                 anchor=tkinter.W,
                 font=constants.LISTS_OF_GAMES_FONT),
             GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
             ROW: 0,
             },
            ]
        
    def show_row(self, dialog, oldobject):
        """Return a ChessDBshowRepertoire dialog for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return ChessDBshowRepertoire(dialog, oldobject, ui=self.ui)
        
    def delete_row(self, dialog, oldobject):
        """Return a ChessDBdeleteRepertoire dialog for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return ChessDBdeleteRepertoire(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a ChessDBeditRepertoire dialog for instance.

        dialog - a Toplevel
        newobject - a ChessDBrecordGame containing original data to be edited
        oldobject - a ChessDBrecordGame containing original data
        showintial == True - show both original and edited data

        """
        return ChessDBeditRepertoire(
            newobject,
            dialog,
            oldobject,
            showinitial=showinitial,
            ui=self.ui)

    def grid_row(self, **kargs):
        """Return customized super(ChessDBrowRepertoire, self).grid_row(...).

        Create textitems argument for ChessDBrowRepertoire instance.

        """
        tags = self.value.collected_game[1]
        return super(ChessDBrowRepertoire, self).grid_row(
            textitems=(
                tags.get(TAG_OPENING, '?'),
                tags.get(TAG_RESULT, '?'),
                ),
            **kargs)

    def populate_widget(self, widget, cnf=None, text=None, context=None, **kw):
        """Wrapper for Tkinter.Text configure method for score attribute"""
        if isinstance(widget, tkinter.Label):
            super(ChessDBrowRepertoire, self).populate_widget(
                widget, text=text, **kw)
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
        """Return Tags not given their own column in display order"""
        str_tags = []
        for t in pgn.collected_game[0]:
            tn = t.group(IFG_TAG_SYMBOL)
            if tn not in REPERTOIRE_GAME_TAGS:
                str_tags.append((tn, t.group(IFG_TAG_STRING_VALUE)))
        return str_tags

    def set_background_on_display(self, widgets):
        self._current_row_background = ON_DISPLAY_COLOUR
        self.set_background(widgets, self._current_row_background)

    def grid_row_on_display(self, **kargs):
        self._current_row_background = ON_DISPLAY_COLOUR
        return self.grid_row(background=ON_DISPLAY_COLOUR, **kargs)


def make_ChessDBrowRepertoire(chessui):
    """Make ChessDBrowRepertoire with reference to ChessUI instance"""
    def make_position(database=None):
        return ChessDBrowRepertoire(database=database, ui=chessui)
    return make_position
