# lmdbdu.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The Lmdbdu class for methods shared by Symas LMMD interface modules.

This module is relevant to the lmdb interface to Symas LMMD.

"""
import os
import zipfile

from solentware_base.core.constants import (
    SUBFILE_DELIMITER,
    EXISTENCE_BITMAP_SUFFIX,
    SEGMENT_SUFFIX,
)

from .archivedu import _delete_archive, _archive
from .alldu import get_filespec
from .dptcompatdu import DptCompatdu


class Lmdbdu(DptCompatdu):
    """Provide deferred update methods shared by the Symas LMMD interfaces.

    The methods provided by DptCompatdu are shared with engines other than
    Berkeley DB.

    The whole database can be put in a single file, or each table (called a
    database in Berkeley DB terminology) in the database can be put in a
    file of it's own.
    """

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
            raise exception_class("DB description invalid") from error

        try:
            super().__init__(names, databasefile, **kargs)
        except Exception as error:
            if __name__ == "__main__":
                raise
            raise exception_class("DB description invalid") from error

    @staticmethod
    def open_context_prepare_import():
        """Return True.

        No preparation actions thet need database open for Symas LMMD.

        """
        return True

    def get_archive_names(self, files=()):
        """Return specified files and existing operating system files."""
        if self.home_directory is None:
            return None, []
        names = [self.database_file]
        exists = [
            os.path.basename(n)
            for n in names
            if os.path.exists(".".join((n, "bz2")))
        ]
        return names, exists

    def archive(self, flag=None, names=None):
        """Write a bz2 or zip backup of files containing games.

        Intended to be a backup in case import fails.

        """
        if self.home_directory is None:
            return None
        if names is None:
            return False
        if not self.delete_archive(flag=flag, names=names):
            return None
        if flag:
            _archive(names)
        return True

    def delete_archive(self, flag=None, names=None):
        """Delete a zip backup of files containing games."""
        if self.home_directory is None:
            return None
        if names is None:
            return False
        if flag:
            _delete_archive(names)
        return True
