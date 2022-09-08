# dbdu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The DbDu class for methods shared by Berkeley DB interface modules.

This module is relevant to the berkeleydb and bsddb3 interfaces to Berkeley
DB.

"""
import os
import bz2
import zipfile

from bsddb3.db import (
    DB_CREATE,
    DB_RECOVER,
    DB_INIT_MPOOL,
    DB_INIT_LOCK,
    DB_INIT_LOG,
    DB_INIT_TXN,
    DB_PRIVATE,
)

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

    The whole database can be put in a single file, or each table (called a
    database in Berkeley DB terminology) in the database can be put in a
    file of it's own.  The litedu.Litedu class cannot be used with the
    Berkeley DB interfaces because this choice exists.
    """

    def __init__(self, databasefile, exception_class, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        assert issubclass(exception_class, Exception)
        environment = {
            "flags": (
                DB_CREATE
                | DB_RECOVER
                | DB_INIT_MPOOL
                | DB_INIT_LOCK
                | DB_INIT_LOG
                | DB_INIT_TXN
                | DB_PRIVATE
            ),
            "gbytes": DB_ENVIRONMENT_GIGABYTES,
            "bytes": DB_ENVIRONMENT_BYTES,
            "maxlocks": DB_ENVIRONMENT_MAXLOCKS,
        }

        try:
            names = get_filespec(**kargs)
        except Exception:
            if __name__ == "__main__":
                raise
            raise exception_class("DB description invalid")

        try:
            super().__init__(names, databasefile, environment)
        except Exception:
            if __name__ == "__main__":
                raise
            raise exception_class("DB description invalid")

    def open_context_prepare_import(self):
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
            for k in self.specification:
                if k not in files:
                    continue
                ns = []
                names[os.path.join(self.home_directory, k)] = ns
                for i in self.specification[k][SECONDARY]:
                    ns.append(
                        os.path.join(
                            self.home_directory, SUBFILE_DELIMITER.join((k, i))
                        )
                    )
                ns.append(
                    os.path.join(
                        self.home_directory,
                        SUBFILE_DELIMITER.join((k, EXISTENCE_BITMAP_SUFFIX)),
                    )
                )
                ns.append(
                    os.path.join(
                        self.home_directory,
                        SUBFILE_DELIMITER.join((k, SEGMENT_SUFFIX)),
                    )
                )
            exists = [
                os.path.basename(n)
                for n in names
                if os.path.exists(".".join((n, "zip")))
            ]
            return names, exists
        else:
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
            return
        if names is None:
            return False
        if not self.delete_archive(flag=flag, names=names):
            return
        if flag:
            if self._file_per_database:
                for n in names:
                    archiveguard = ".".join((n, "grd"))
                    archivename = ".".join((n, "zip"))
                    c = zipfile.ZipFile(
                        archivename,
                        mode="w",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                    )
                    for s in names[n]:
                        c.write(s, arcname=os.path.basename(s))
                    c.close()
                    c = open(archiveguard, "wb")
                    c.close()
            else:
                _archive(names)
        return True

    def delete_archive(self, flag=None, names=None):
        """Delete a zip backup of files containing games."""
        if self.home_directory is None:
            return
        if names is None:
            return False
        if flag:
            if self._file_per_database:
                not_backups = []
                for n in names:
                    archiveguard = ".".join((n, "grd"))
                    archivename = ".".join((n, "zip"))
                    if not os.path.exists(archivename):
                        try:
                            os.remove(archiveguard)
                        except FileNotFoundError:
                            pass
                        continue
                    c = zipfile.ZipFile(
                        archivename,
                        mode="r",
                        compression=zipfile.ZIP_DEFLATED,
                        allowZip64=True,
                    )
                    namelist = c.namelist()
                    extract = [
                        e
                        for e in namelist
                        if os.path.join(self.home_directory, e) in names[n]
                    ]
                    if len(extract) != len(namelist):
                        not_backups.append(os.path.basename(archivename))
                        c.close()
                        continue
                    c.close()
                    try:
                        os.remove(archiveguard)
                    except FileNotFoundError:
                        pass
                    try:
                        os.remove(archivename)
                    except FileNotFoundError:
                        pass
                if not_backups:
                    return
            else:
                _delete_archive(names)
        return True
