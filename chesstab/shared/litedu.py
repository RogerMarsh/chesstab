# litedu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide PGN import estimating and backup for non-DPT interface modules.

These other modules, except Symas LMMD, take space as needed so methods
which 'do nothing' are provided.

For Symas LMMD it is possible to set an arbitrarly large size and then
reclaim any unused space by setting an arbitrarly low size.  The size
determines how large the database can get before giving a 'full' error.

"""
from solentware_base.core.archivedu import Archivedu

from .alldu import get_filespec


class Litedu(Archivedu):
    """Provide methods for compatibility with DPT interface.

    The methods have their DPT-specific code removed.
    """

    # Fix pylint no-member message E1101.
    # Class usage is 'class C(..., Litedu, ...) where '...' classes give
    # mro 'C, ..., Litedu, ..., <class defining database_file>, ..., object'.
    # Each C has a different <class defining database_file> with various
    # rules for generating the value.
    database_file = None  # Put this in core._database.Database if anywhere.

    def __init__(self, databasefile, exception_class, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        assert issubclass(exception_class, Exception)
        try:
            names = get_filespec(**kargs)
        except Exception as error:
            if __name__ == "__main__":
                raise
            raise exception_class("database description invalid") from error

        try:
            super().__init__(names, databasefile, **kargs)
        except Exception as error:
            if __name__ == "__main__":
                raise
            raise exception_class(
                "unable to initialize database object"
            ) from error

    @staticmethod
    def get_file_sizes():
        """Return an empty dictionary.

        No sizes needed.  Method exists for DPT compatibility.

        """
        return {}

    def report_plans_for_estimate(self, estimates, reporter, increases):
        """Remind user to check estimated time to do import.

        No planning needed.  Method exists for DPT compatibility.

        """
        del estimates, increases
        reporter.append_text_only("")
        reporter.append_text("Ready to start import.")

    @staticmethod
    def open_context_prepare_import():
        """Return True.

        No preparation actions that need database open for non-DPT databases.

        """
        return True
