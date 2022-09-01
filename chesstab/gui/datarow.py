# datarow.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide DataRow class which uses solentware_misc exception handling."""

from solentware_grid.gui.datarow import DataRow

from solentware_misc.gui.exceptionhandler import ExceptionHandler


class DataRow(ExceptionHandler, DataRow):
    """Override DataRow methods with those available in ExceptionHandler."""
