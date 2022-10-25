# gamerow.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display tag roster details of games on database."""

import tkinter

from solentware_grid.gui.datarow import (
    DataRow,
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

from ..core.chessrecord import ChessDBrecordGameTags
from . import constants
from ..shared.allrow import AllRow
from ..shared.game_position import GamePosition


class ChessDBrowGame(GamePosition, AllRow, ChessDBrecordGameTags, DataRow):
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

    def grid_row(self, textitems=(), **kargs):
        """Set textitems to selected PGN tags, delegate, return response.

        Create textitems argument for ChessDBrowGame instance.

        textitems arguments is ignored and is present for compatibility.

        """
        tags = self.value.collected_game.pgn_tags
        return super().grid_row(
            textitems=(
                tags.get(TAG_WHITE, DEFAULT_TAG_VALUE),
                tags.get(TAG_RESULT, DEFAULT_TAG_RESULT_VALUE),
                tags.get(TAG_BLACK, DEFAULT_TAG_VALUE),
                tags.get(TAG_EVENT, DEFAULT_TAG_VALUE),
                tags.get(TAG_DATE, DEFAULT_TAG_DATE_VALUE),
                "  ".join(
                    [
                        "".join((tag, ' "', value, '"'))
                        for tag, value in self._get_tags_display_order(
                            self.value
                        )
                    ]
                ),
            ),
            **kargs
        )

    def _get_tags_display_order(self, pgn):
        """Return Tags not given their own column in display order."""
        del pgn
        str_tags = []
        other_tags = []
        tags = self.value.collected_game.pgn_tags
        for tag in SEVEN_TAG_ROSTER:
            if tag not in constants.GRID_HEADER_SEVEN_TAG_ROSTER:
                str_tags.append((tag, tags.get(tag, DEFAULT_TAG_VALUE)))
        for key, value in sorted(tags.items()):
            if key not in SEVEN_TAG_ROSTER:
                other_tags.append((key, value))
        return str_tags + other_tags


def chess_db_row_game(chessui):
    """Return function that returns ChessDBrowGame instance for chessui.

    chessui is a chess_ui.ChessUI instance.

    The returned function takes a ChessDatabase instance as it's argument.
    """

    def make_position(database=None):
        return ChessDBrowGame(database=database, ui=chessui)

    return make_position
