# dbdutcl.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The DbduTcl class for TCL interface to Berkeley DB.

This module uses the solentware_base.core._db_tkinter Database class.

"""
# Nominally this module does not belong in the shared sub-package because
# there is only one TCL interface.  It is an alternative to the dbdudu
# module which does belong, and that relationship is more important.
# Perhaps 'shared' is the wrong name for the sub-package.

from solentware_base.core._db_tkinter import Database

from .dptcompatdu import DptCompatdu


class DbduTcl(DptCompatdu, Database):
    """Provide deferred update methods shared by Berkeley DB interfaces."""
