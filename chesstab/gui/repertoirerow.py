# repertoirerow.py
# Copyright 2013 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display tag roster details of repertoire.
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
    TAG_RESULT,
    IFG_TAG_NAME,
    IFG_TAG_VALUE,
)

from .datarow import DataRow
from ..core.chessrecord import ChessDBrecordRepertoireTags
from .repertoiredbedit import RepertoireDbEdit
from .repertoiredbdelete import RepertoireDbDelete
from .repertoiredbshow import RepertoireDbShow
from . import constants
from ..core.constants import TAG_OPENING, REPERTOIRE_GAME_TAGS

ON_DISPLAY_COLOUR = "#eba610"  # a pale orange


class ChessDBrowRepertoire(ChessDBrecordRepertoireTags, DataRow):
    """Define row in list of repertoires.

    Add row methods to the chess game record definition.

    """

    header_specification = [
        {
            WIDGET: tkinter.Label,
            WIDGET_CONFIGURE: dict(
                text=TAG_OPENING,
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
                anchor=tkinter.W,
                padx=0,
                pady=1,
                font="TkDefaultFont",
            ),
            GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
            GRID_COLUMNCONFIGURE: dict(weight=1, uniform="result"),
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
                    anchor=tkinter.W,
                    font=constants.LISTS_OF_GAMES_FONT,
                    pady=1,
                    padx=0,
                ),
                GRID_CONFIGURE: dict(column=1, sticky=tkinter.EW),
                ROW: 0,
            },
        ]

    def show_row(self, dialog, oldobject):
        """Return a RepertoireDbShow toplevel for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return RepertoireDbShow(dialog, oldobject, ui=self.ui)

    def delete_row(self, dialog, oldobject):
        """Return a RepertoireDbDelete toplevel for instance.

        dialog - a Toplevel
        oldobject - a ChessDBrecordGame containing original data

        """
        return RepertoireDbDelete(dialog, oldobject, ui=self.ui)

    def edit_row(self, dialog, newobject, oldobject, showinitial=True):
        """Return a RepertoireDbEdit toplevel for instance.

        dialog - a Toplevel
        newobject - a ChessDBrecordGame containing original data to be edited
        oldobject - a ChessDBrecordGame containing original data
        showintial == True - show both original and edited data

        """
        return RepertoireDbEdit(
            newobject, dialog, oldobject, showinitial=showinitial, ui=self.ui
        )

    def grid_row(self, **kargs):
        """Return customized super(ChessDBrowRepertoire, self).grid_row(...).

        Create textitems argument for ChessDBrowRepertoire instance.

        """
        tags = self.value.collected_game._tags
        return super(ChessDBrowRepertoire, self).grid_row(
            textitems=(
                tags.get(TAG_OPENING, "?"),
                tags.get(TAG_RESULT, "?"),
            ),
            **kargs
        )

    def get_tags_display_order(self, pgn):
        """Return Tags not given their own column in display order"""
        tag_values = []
        tags = self.collected_game._tags
        for tv in sorted(tags.items()):
            if tv[0] not in REPERTOIRE_GAME_TAGS:
                tag_values.append(tv)
        return tag_values

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
