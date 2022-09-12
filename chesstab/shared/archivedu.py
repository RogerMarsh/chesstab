# archivedu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The Archivedu class for interfaces to single file databases.

Most of the interface modules that can use the Litedu module have 'lite' in
their name.

This module is relevant to the apsw and sqlite3 interfaces to Sqlite3, and
to the gnu, ndbm, unqlite, and vedis, interfaces to their respective
'key:value' databases.

"""

import os
import bz2


class Archivedu:
    """Provide deferred update archive methods shared by various interfaces.

    All the supported engines put the whole database in a single file so
    can use the same methods to manage temporary backups which may exist
    while opening and checking the database.
    """

    def archive(self, flag=None, names=None):
        """Write a bz2 backup of file containing games.

        Intended to be a backup in case import fails.

        """
        if names is None:
            return False
        if not self.delete_archive(flag=flag, names=names):
            return None
        if flag:
            _archive(names)
        return True

    @staticmethod
    def delete_archive(flag=None, names=None):
        """Delete a bz2 backup of file containing games."""
        if names is None:
            return False
        if flag:
            _delete_archive(names)
        return True


# Snippet needed in dbdu.Dbdu.archive() method too.
def _archive(names):
    for name in names:
        compressor = bz2.BZ2Compressor()
        archiveguard = ".".join((name, "grd"))
        archivename = ".".join((name, "bz2"))
        with open(name, "rb") as file_in, open(archivename, "wb") as file_out:
            inp = file_in.read(10000000)
            while inp:
                compressed = compressor.compress(inp)
                if compressed:
                    file_out.write(compressed)
                inp = file_in.read(10000000)
            compressed = compressor.flush()
            if compressed:
                file_out.write(compressed)
        with open(archiveguard, "wb"):
            pass


# Snippet needed in dbdu.Dbdu.delete_archive() method too.
def _delete_archive(names):
    for name in names:
        archiveguard = ".".join((name, "grd"))
        archivename = ".".join((name, "bz2"))
        try:
            os.remove(archiveguard)
        except FileNotFoundError:
            pass
        try:
            os.remove(archivename)
        except FileNotFoundError:
            pass
