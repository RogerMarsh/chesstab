# querytoplevel.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Toplevel widgets to display and edit game selection rules.

These two classes display game selection rules in their own Toplevel widget:
they are used in the querydbdelete, querydbedit, and querydbshow, modules.

"""

from .query import Query
from .queryedit import QueryEdit
from .topleveltext import ToplevelText


class QueryToplevel(ToplevelText, Query):

    """Customize Query to be the single instance in a Toplevel widget."""


class QueryToplevelEdit(ToplevelText, QueryEdit):

    """Customize QueryEdit to be the single instance in a Toplevel widget."""

    # A method like GameToplevelEdit.create_primary_activity_popup is not
    # needed because the standard edit operations of Text widget are
    # sufficient.
