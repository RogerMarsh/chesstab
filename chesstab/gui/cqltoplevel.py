# cqltoplevel.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Toplevel widgets to display and edit Chess Query Language (ChessQL)
statements.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

These two classes display ChessQL statements in their own Toplevel widget:
they are used in the cqldbdelete, cqldbedit, and cqldbshow, modules.

"""

from .cql import CQL
from .cqledit import CQLEdit
from .topleveltext import ToplevelText


class CQLToplevel(ToplevelText, CQL):

    """Customize CQL to be the single instance in a Toplevel widget."""


class CQLToplevelEdit(ToplevelText, CQLEdit):

    """Customize CQLEdit to be the single instance in a Toplevel widget."""

    # A method like GameToplevelEdit.create_primary_activity_popup is not
    # needed because the standard edit operations of Text widget are
    # sufficient.
