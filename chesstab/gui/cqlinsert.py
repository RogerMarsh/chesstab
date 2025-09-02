# cqlinsert.py
# Copyright 2025 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to insert Chess Query Language (ChessQL) statements."""

from solentware_grid.core.dataclient import DataNotify

from . import displaytext
from . import cqledit
from . import cqlinsertbase
from . import cqldisplay


class CQLInsert(
    cqlinsertbase.CQLInsertBase,
    displaytext.ListGamesText,
    displaytext.InsertText,
    cqldisplay.CQLDisplay,
    cqledit.CQLEdit,
    DataNotify,
):
    """Display ChessQL statement from database allowing insert."""
