# datarow.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Add solentware_misc bindings and exception handling to DataRow."""

from solentware_grid.gui import datarow

from solentware_bind.gui.bindings import Bindings


class DataRow(Bindings, datarow.DataRow):
    """Bindings and ExceptionHandler methods added to DataRow class."""
