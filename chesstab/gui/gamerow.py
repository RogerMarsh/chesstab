# gamerow.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display tag roster details of games on database.
"""

import tkinter

from solentware_grid.gui.datarow import (
    GRID_COLUMNCONFIGURE,
    GRID_CONFIGURE,
    WIDGET_CONFIGURE,
    WIDGET,
    ROW,
)

from pgn_read.core.constants import (
    TAG_WHITE,
    TAG_BLACK,
    TAG_RESULT,
    TAG_EVENT,
    TAG_DATE,
    SEVEN_TAG_ROSTER,
    DEFAULT_TAG_VALUE,
    DEFAULT_TAG_DATE_VALUE,
    DEFAULT_TAG_RESULT_VALUE,
)

from .datarow import DataRow
from ..core.chessrecord import ChessDBrecordGameTags
from .gamedbedit import GameDbEdit
from .gamedbdelete import GameDbDelete
from .gamedbshow import GameDbShow
from . import constants

ON_DISPLAY_COLOUR = "#eba610"  # a pale orange


class ChessDBrowGame(ChessDBrecordGameTags, DataRow):
    """Define row in list of games.

    Add row methods to the chess game record definition.

    """

    header_specification = [
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text=TAG_WHITE,
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=0, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="player"),
            ROW: 0,
        },
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text=TAG_RESULT,
                anchor=tkinter.CENTER,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="score"),
            ROW: 0,
        },
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text=TAG_BLACK,
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=2, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="player"),
            ROW: 0,
        },
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text=TAG_EVENT,
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=3, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="event"),
            ROW: 0,
        },
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text=TAG_DATE,
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=4, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="date"),
            ROW: 0,
        },
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text="Tags",
                anchor=tkinter.W,
                padx=10,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=5, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=4, uniform="tags"),
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
            {
                WIDGET: tkinter.Label,
                WIDGET_CONFIGURE: dict(
                    anchor=tkinter.CENTER,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=0,
                ),
                GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
                ROW: 0,
            },
            {
                WIDGET: tkinter.Label,
                WIDGET_CONFIGURE: dict(
                    anchor=tkinter.W,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=0,
                ),
                GRID_CONFIGURE: dict(column=2, sticky=tkinter.EW),
                ROW: 0,
            },
            {
                WIDGET: tkinter.Label,
                WIDGET_CONFIGURE: dict(
                    anchor=tkinter.W,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=0,
                ),
                GRID_CONFIGURE: dict(column=3, sticky=tkinter.EW),
                ROW: 0,
            },
            {
                WIDGET: tkinter.Label,
                WIDGET_CONFIGURE: dict(
                    anchor=tkinter.W,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=0,
                ),
                GRID_CONFIGURE: dict(column=4, sticky=tkinter.EW),
                ROW: 0,
            },
            {
                WIDGET: tkinter.Label,
                WIDGET_CONFIGURE: dict(
                    anchor=tkinter.W,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=10,
                ),
                GRID_CONFIGURE: dict(column=5, sticky=tkinter.EW),
                ROW: 0,
            },
        ]

    def show_row(self, dialog, oldobject):
        """Return a GameDbShow toplevel for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return GameDbShow(dialog, oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a GameDbDelete toplevel for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return GameDbDelete(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a GameDbEdit toplevel for instance.

        dialog - a Toplevel
        newobject - a ChessDBrecordGame containing original data to be edited
        oldobject - a ChessDBrecordGame containing original data
        showintial == True - show both original and edited data

        """
        return GameDbEdit(
            newobject, dialog, oldobject, showinitial=showinitial, ui=self.ui
        )

    def grid_row(self, **kargs):
        """Return super(ChessDBrowGame,).grid_row(textitems=(...), **kargs).

        Create textitems argument for ChessDBrowGame instance.

        """
        tags = self.value.collected_game._tags
        return super(ChessDBrowGame, self).grid_row(
            textitems=(
                tags.get(TAG_WHITE, DEFAULT_TAG_VALUE),
                tags.get(TAG_RESULT, DEFAULT_TAG_RESULT_VALUE),
                tags.get(TAG_BLACK, DEFAULT_TAG_VALUE),
                tags.get(TAG_EVENT, DEFAULT_TAG_VALUE),
                tags.get(TAG_DATE, DEFAULT_TAG_DATE_VALUE),
                "  ".join(
                    [
                        "".join((tag, ' "', value, '"'))
                        for tag, value in self.get_tags_display_order(
                            self.value
                        )
                    ]
                ),
            ),
            **kargs
        )

    def get_tags_display_order(self, pgn):
        str_tags = []
        other_tags = []
        tags = self.value.collected_game._tags
        for t in SEVEN_TAG_ROSTER:
            if t not in constants.GRID_HEADER_SEVEN_TAG_ROSTER:
                str_tags.append((t, tags.get(t, DEFAULT_TAG_VALUE)))
        for t, v in sorted(tags.items()):
            if t not in SEVEN_TAG_ROSTER:
                other_tags.append((t, v))
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
