# datarow.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Add solentware_misc exception handling to solentware_grid DataRow class for
ChessTab.
"""

from solentware_grid.gui.datarow import DataRow

from solentware_misc.gui.exceptionhandler import ExceptionHandler


class DataRow(ExceptionHandler, DataRow):

    """Override solentware_grid.gui.datarow.DataRow methods, from the subclass
    CallbackException, with those in ExceptionHandler.
    """
