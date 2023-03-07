# dbdu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The Dbdu class for methods shared by Berkeley DB interface modules.

This module is relevant to the berkeleydb, bsddb3, and tcl, interfaces to
Berkeley DB.

"""
import os
import zipfile

from solentware_base.core.constants import (
    SUBFILE_DELIMITER,
    EXISTENCE_BITMAP_SUFFIX,
    SEGMENT_SUFFIX,
)

from ..core.filespec import (
    SECONDARY,
    DB_ENVIRONMENT_GIGABYTES,
    DB_ENVIRONMENT_BYTES,
    DB_ENVIRONMENT_MAXLOCKS,
)
from .archivedu import _delete_archive, _archive
from .alldu import get_filespec
from .dptcompatdu import DptCompatdu


class Dbdu(DptCompatdu):
    """Provide deferred update methods shared by the Berkeley DB interfaces.

    The methods provided by DptCompatdu are shared with engines other than
    Berkeley DB.

    The whole database can be put in a single file, or each table (called a
    database in Berkeley DB terminology) in the database can be put in a
    file of it's own.
    """

    def __init__(self, databasefile, exception_class, flags, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        assert issubclass(exception_class, Exception)
        environment = {
            "flags": flags,
            "gbytes": DB_ENVIRONMENT_GIGABYTES,
            "bytes": DB_ENVIRONMENT_BYTES,
            "maxlocks": DB_ENVIRONMENT_MAXLOCKS,
        }

        try:
            names = get_filespec(**kargs)
        except Exception as error:
            if __name__ == "__main__":
                raise
            raise exception_class("DB description invalid") from error

        try:
            super().__init__(names, databasefile, environment, **kargs)
        except Exception as error:
            if __name__ == "__main__":
                raise
            raise exception_class("DB description invalid") from error

    @staticmethod
    def open_context_prepare_import():
        """Return True.

        No preparation actions thet need database open for Berkeley DB.

        """
        return True

    def get_archive_names(self, files=()):
        """Return specified files and existing operating system files."""
        if self.home_directory is None:
            return None, []
        if self._file_per_database:
            names = dict()
            for key in self.specification:
                if key not in files:
                    continue
                name_list = []
                names[os.path.join(self.home_directory, key)] = name_list
                for item in self.specification[key][SECONDARY]:
                    name_list.append(
                        os.path.join(
                            self.home_directory,
                            SUBFILE_DELIMITER.join((key, item)),
                        )
                    )
                name_list.append(
                    os.path.join(
                        self.home_directory,
                        SUBFILE_DELIMITER.join((key, EXISTENCE_BITMAP_SUFFIX)),
                    )
                )
                name_list.append(
                    os.path.join(
                        self.home_directory,
                        SUBFILE_DELIMITER.join((key, SEGMENT_SUFFIX)),
                    )
                )
            exists = [
                os.path.basename(n)
                for n in names
                if os.path.exists(".".join((n, "zip")))
            ]
            return names, exists
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
            if self._file_per_database:
                for name in names:
                    archiveguard = ".".join((name, "grd"))
                    archivename = ".".join((name, "zip"))
                    with zipfile.ZipFile(
                        archivename,
                        mode="w",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                    ) as zip_archive:
                        for source in names[name]:
                            zip_archive.write(
                                source, arcname=os.path.basename(source)
                            )
                    with open(archiveguard, "wb"):
                        pass
            else:
                _archive(names)
        return True

    def delete_archive(self, flag=None, names=None):
        """Delete a zip backup of files containing games."""
        if self.home_directory is None:
            return None
        if names is None:
            return False
        if flag:
            if self._file_per_database:
                not_backups = []
                for name in names:
                    archiveguard = ".".join((name, "grd"))
                    archivename = ".".join((name, "zip"))
                    if not os.path.exists(archivename):
                        try:
                            os.remove(archiveguard)
                        except FileNotFoundError:
                            pass
                        continue
                    with zipfile.ZipFile(
                        archivename,
                        mode="r",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                    ) as zip_archive:
                        namelist = zip_archive.namelist()
                        extract = [
                            e
                            for e in namelist
                            if os.path.join(self.home_directory, e)
                            in names[name]
                        ]
                        if len(extract) != len(namelist):
                            not_backups.append(os.path.basename(archivename))
                            continue
                    try:
                        os.remove(archiveguard)
                    except FileNotFoundError:
                        pass
                    try:
                        os.remove(archivename)
                    except FileNotFoundError:
                        pass
                if not_backups:
                    return None
            else:
                _delete_archive(names)
        return True
