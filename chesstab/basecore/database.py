# database.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""ChessTab database methods common to all database engine interfaces."""

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
    """Define methods which are common to all database engine interfaces."""

    def use_deferred_update_process(self, **kargs):
        """Return path to deferred update module.

        **kargs - soak up any arguments other database engines need.

        """
        del kargs
        return self._deferred_update_process

    def open_database(self, files=None):
        """Return True to fit behaviour of dpt version of this method."""
        super().open_database(files=files)
        return True

    @staticmethod
    def dump_database(names=()):
        """Dump database in compressed files."""
        for name in names:
            compressor = bz2.BZ2Compressor()
            archivename = ".".join((name, "broken", "bz2"))
            with open(name, "rb") as file_in, open(
                archivename, "wb"
            ) as file_out:
                inp = file_in.read(10000000)
                while inp:
                    compressed = compressor.compress(inp)
                    if compressed:
                        file_out.write(compressed)
                    inp = file_in.read(10000000)
                compressed = compressor.flush()
                if compressed:
                    file_out.write(compressed)

    @staticmethod
    def delete_backups(names=()):
        """Delete backup files."""
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

    @staticmethod
    def restore_backups(names=()):
        """Restore database from backup files."""
        for name in names:
            decompressor = bz2.BZ2Decompressor()
            archivename = ".".join((name, "bz2"))
            with open(archivename, "rb") as file_in, open(
                name, "wb"
            ) as file_out:
                inp = file_in.read(1000000)
                while inp:
                    decompressed = decompressor.decompress(inp)
                    if decompressed:
                        file_out.write(decompressed)
                    inp = file_in.read(1000000)
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
        for pathname in homenames:
            if os.path.isdir(pathname):
                shutil.rmtree(pathname, ignore_errors=True)
            else:
                os.remove(pathname)
        try:
            os.rmdir(self.home_directory)
        except FileNotFoundError:
            pass
        return message

    def get_archive_names(self, files=()):
        """Return names and operating system files for archives and guards."""
        del files
        names = (self.database_file,)
        archives = dict()
        guards = dict()
        for name in names:
            archiveguard = ".".join((name, "grd"))
            archivefile = ".".join((name, "bz2"))
            for box, file in ((archives, archivefile), (guards, archiveguard)):
                if os.path.exists(file):
                    box[name] = file
        return (names, archives, guards)

    def open_after_import_without_backups(self, files=()):
        """Return True after doing database engine specific open actions.

        For SQLite3 and Berkeley DB just call open_database.

        """
        del files
        super().open_database()

        # Return True to fit behaviour of chessdpt module version of method.
        return True

    def open_after_import_with_backups(self, files=()):
        """Return True after doing database engine specific open actions.

        For SQLite3 and Berkeley DB just call open_database.

        """
        del files
        super().open_database()

        # Return True to fit behaviour of chessdpt module version of method.
        return True

    def save_broken_database_details(self, files=()):
        """Save database engine specific detail of broken files to be restored.

        It is assumed that the Database Services object exists.

        """

    def adjust_database_for_retry_import(self, files):
        """Database engine specific actions done before re-trying an import."""

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
