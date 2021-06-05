# database.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""ChessTab database methods common to all database engine interfaces.
"""

import os
import bz2
import shutil

from ..core.filespec import (
    NEWGAMES_FIELD_DEF,
    NEWGAMES_FIELD_VALUE,
    PARTIAL_FILE_DEF,
)
from .. import APPLICATION_NAME, ERROR_LOG


class Database:

    """ """

    def use_deferred_update_process(self, **kargs):
        """Return path to deferred update module.

        **kargs - soak up any arguments other database engines need.

        """
        return self._deferred_update_process

    def open_database(self, files=None):
        """Return True to fit behaviour of dpt version of this method."""
        super().open_database(files=files)
        return True

    def dump_database(self, names=()):
        """Dump database in compressed files."""
        for n in names:
            c = bz2.BZ2Compressor()
            archivename = ".".join((n, "broken", "bz2"))
            fi = open(n, "rb")
            fo = open(archivename, "wb")
            try:
                inp = fi.read(10000000)
                while inp:
                    co = c.compress(inp)
                    if co:
                        fo.write(co)
                    inp = fi.read(10000000)
                co = c.flush()
                if co:
                    fo.write(co)
            finally:
                fo.close()
                fi.close()

    def delete_backups(self, names=()):
        """Delete backup files."""
        for n in names:
            archiveguard = ".".join((n, "grd"))
            archivename = ".".join((n, "bz2"))
            try:
                os.remove(archiveguard)
            except:
                pass
            try:
                os.remove(archivename)
            except:
                pass

    def restore_backups(self, names=()):
        """Restore database from backup files."""
        for n in names:
            c = bz2.BZ2Decompressor()
            archivename = ".".join((n, "bz2"))
            fi = open(archivename, "rb")
            fo = open(n, "wb")
            try:
                inp = fi.read(1000000)
                while inp:
                    co = c.decompress(inp)
                    if co:
                        fo.write(co)
                    inp = fi.read(1000000)
            finally:
                fo.close()
                fi.close()
        return True

    def delete_database(self, names):
        """Close and delete the open chess database."""
        listnames = set(n for n in os.listdir(self.home_directory))
        homenames = set(n for n in names if os.path.basename(n) in listnames)
        if ERROR_LOG in listnames:
            homenames.add(os.path.join(self.home_directory, ERROR_LOG))
        if len(listnames - set(os.path.basename(h) for h in homenames)):
            message = "".join(
                (
                    "There is at least one file or folder in\n\n",
                    self.home_directory,
                    "\n\nwhich may not be part of the database.  These items ",
                    "have not been deleted by ",
                    APPLICATION_NAME,
                    ".",
                )
            )
        else:
            message = None
        self.close_database()
        for h in homenames:
            if os.path.isdir(h):
                shutil.rmtree(h, ignore_errors=True)
            else:
                os.remove(h)
        try:
            os.rmdir(self.home_directory)
        except:
            pass
        return message

    def get_archive_names(self, files=()):
        """Return names and operating system files for archives and guards"""
        names = (self.database_file,)
        archives = dict()
        guards = dict()
        for n in names:
            archiveguard = ".".join((n, "grd"))
            archivefile = ".".join((n, "bz2"))
            for d, f in ((archives, archivefile), (guards, archiveguard)):
                if os.path.exists(f):
                    d[n] = f
        return (names, archives, guards)

    def open_after_import_without_backups(self, **ka):
        """Return True after doing database engine specific open actions.

        For SQLite3 and Berkeley DB just call open_database.

        """
        super().open_database()

        # Return True to fit behaviour of chessdpt module version of method.
        return True

    def open_after_import_with_backups(self, files=()):
        """Return True after doing database engine specific open actions.

        For SQLite3 and Berkeley DB just call open_database.

        """
        super().open_database()

        # Return True to fit behaviour of chessdpt module version of method.
        return True

    def save_broken_database_details(self, files=()):
        """Save database engine specific detail of broken files to be restored.

        It is assumed that the Database Services object exists.

        """
        pass

    def adjust_database_for_retry_import(self, files):
        """Database engine specific actions to do before re-trying an import"""
        pass

    def mark_partial_positions_to_be_recalculated(self):
        """File all partial positions to be recalculated."""
        self.start_transaction()
        allrecords = self.recordlist_ebm(PARTIAL_FILE_DEF)
        self.file_records_under(
            PARTIAL_FILE_DEF,
            NEWGAMES_FIELD_DEF,
            allrecords,
            self.encode_record_selector(NEWGAMES_FIELD_VALUE),
        )
        allrecords.close()
        self.commit()
