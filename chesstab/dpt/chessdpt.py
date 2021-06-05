# chessdpt.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess games database using DPT database via dptdb.dptapi.
"""

import os
import shutil
import tkinter.messagebox

from dptdb.dptapi import (
    FILEDISP_OLD,
    FIFLAGS_FULL_TABLEB,
    FIFLAGS_FULL_TABLED,
    FISTAT_DEFERRED_UPDATES,
    APIContextSpecification,
    APIFieldValue,
)

from solentware_base import dpt_database
from solentware_base.core.constants import (
    FILEDESC,
    BRECPPG,
    BSIZE,
    DSIZE,
    DPT_DEFER_FOLDER,
    DPT_SYS_FOLDER,
    SECONDARY,
)

from ..core.filespec import (
    FileSpec,
    PARTIAL_FILE_DEF,
    PARTIAL_FIELD_DEF,
    NEWGAMES_FIELD_DEF,
    NEWGAMES_FIELD_VALUE,
)
from ..basecore import database
from .. import APPLICATION_NAME


class ChessdptError(Exception):
    pass


class ChessDatabase(database.Database, dpt_database.Database):

    """Provide access to a database of games of chess."""

    # The default for DPT.  See use_deferred_update_process method for cases
    # where this is not used: normally delegated to superclass to pick the
    # default.
    _deferred_update_process = os.path.join(
        os.path.basename(os.path.dirname(__file__)), "runchessdptdu.py"
    )

    def __init__(self, databasefolder, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        try:
            sysprint = kargs.pop("sysprint")
        except KeyError:
            sysprint = "CONSOLE"
        ddnames = FileSpec(**kargs)

        if not kargs.get("allowcreate", False):
            try:
                for dd in ddnames:
                    if FILEDESC in ddnames[dd]:
                        del ddnames[dd][FILEDESC]
            except:
                if __name__ == "__main__":
                    raise
                else:
                    raise ChessdptError("DPT description invalid")

        try:
            super(ChessDatabase, self).__init__(
                ddnames, databasefolder, sysprint=sysprint, **kargs
            )
        except ChessdptError:
            if __name__ == "__main__":
                raise
            else:
                raise ChessdptError("DPT description invalid")

        self._broken_sizes = dict()

    def use_deferred_update_process(
        self, dptmultistepdu=False, dptchunksize=None, **kargs
    ):
        """Return module name or None

        dptmultistepdu is ignored if dptchunksize is not None.
        dptmultistepdu is True: use multi-step deferred update
        otherwise use single-step deferred update.

        dptchunksize is None: dptmultistepdu determines deferred update module
        otherwise use single-step deferred update with the chunk size (assumed
        to be a valid chunk size)

        **kargs - soak up any arguments other database engines need.

        On non-Microsoft operating systems single-step update may not work.
        First encountered on upgrade to FreeBSD7.2 wine-1.1.23,1 dptv2r19.
        But single-step works on FreeBSD7.2 wine-1.1.0,1 dptv2r19.
        Wine source code comments state that memory-use calls do not return
        correct values. Evidently the incorrectness can vary by version
        making the DPT workarounds liable to fail also.

        runchessdptdu.py does DPT's single-step deferred update process.
        runchessdptduchunk.py does DPT's single-step deferred update process
        but splits the task into fixed size chunks, a number of games, which
        it is hoped are small enough to finish before all memory is used.
        runchessdptdumulti.py does DPT's multi-step deferred update process.

        Multi-step is about half an order of magnitude slower than single-step.

        """
        if dptchunksize is not None:
            return os.path.join(
                os.path.basename(os.path.dirname(__file__)),
                "runchessdptduchunk.py",
            )
        if dptmultistepdu is True:
            return os.path.join(
                os.path.basename(os.path.dirname(__file__)),
                "runchessdptdumulti.py",
            )
        else:
            return super().use_deferred_update_process(**kargs)

    def adjust_database_for_retry_import(self, files):
        """Increase file sizes taking file full into account"""
        # Increase the size of files allowing for the file full condition
        # which occurred while doing a deferred update for import.
        for dbn in self._broken_sizes.keys():
            self.table[dbn].increase_size_of_full_file(
                self.dbenv,
                self.table[dbn].get_file_parameters(self.dbenv),
                self._broken_sizes[dbn],
            )
        return

    def open_database(self, files=None):
        """Return True if all files are opened in Normal mode (FISTAT == 0)."""
        super().open_database(files=files)
        fistat = dict()
        for dbo in self.table.values():
            fistat[dbo] = dbo.get_file_parameters(self.dbenv)["FISTAT"]
        for dbo in self.table.values():
            if fistat[dbo][0] != 0:
                break
        else:
            self.increase_database_size(files=None)
            return True

        # At least one file is not in Normal state
        r = "\n".join(
            [
                "\t".join((os.path.basename(dbo.file), fistat[dbo][1]))
                for dbo in self.table.values()
            ]
        )
        tkinter.messagebox.showinfo(
            title="Open",
            message="".join(
                (
                    APPLICATION_NAME,
                    " has opened the database but some of the files are ",
                    "not in the Normal state.\n\n",
                    r,
                    "\n\n",
                    APPLICATION_NAME,
                    " will close the database on dismissing this ",
                    "dialogue.\n\nRestore the database from backups, or source ",
                    "data, before trying again.",
                )
            ),
        )
        self.close_database()

    def delete_database(self):
        """Close and delete the open chess database."""
        names = [self.sysfolder]
        for k, v in self.table.items():
            names.append(v.file)
        return super().delete_database(names)

    def get_archive_names(self, files=()):
        """Return names and operating system files for archives and guards"""
        specs = {f for f in files if f in self.table}
        names = [v.file for k, v in self.table.items() if k in specs]
        archives = dict()
        guards = dict()
        for n in names:
            archiveguard = ".".join((n, "grd"))
            archivefile = ".".join((n, "bz2"))
            for d, f in ((archives, archivefile), (guards, archiveguard)):
                if os.path.exists(f):
                    d[n] = f
        return (names, archives, guards)

    def open_after_import_without_backups(self, files=()):
        """Return open context after doing database engine specific actions.

        For DPT clear the file sizes before import area if the database was
        opened successfully as there is no need to retry the import.

        """
        super().open_database()
        fistat = dict()
        file_sizes_for_import = dict()
        for dbn, dbo in self.table.items():
            gfp = dbo.get_file_parameters(self.dbenv)
            fistat[dbo] = gfp["FISTAT"]
            if dbn in files:
                file_sizes_for_import[dbn] = gfp
        for dbo in self.table.values():
            if fistat[dbo][0] != 0:
                break
        else:
            # Assume all is well as file status is 0
            # Or just do nothing (as file_sizes_for_import may be removed)
            self.increase_database_size(files=None)
            self.mark_partial_positions_to_be_recalculated()
            return True
        # At least one file is not in Normal state after Import.
        # Check the files that had imports applied
        for dbn in file_sizes_for_import:
            status = file_sizes_for_import[dbn]["FISTAT"][0]
            flags = file_sizes_for_import[dbn]["FIFLAGS"]
            if not (
                (flags & FIFLAGS_FULL_TABLEB) or (flags & FIFLAGS_FULL_TABLED)
            ):
                break
        else:
            # The file states are consistent with the possibility that the
            # import failed because at least one file was too small.
            # The file size information is kept for calculating an increase
            # in file size before trying the import again.
            tkinter.messagebox.showinfo(
                title="Open",
                message="".join(
                    (
                        "The import failed.\n\n",
                        APPLICATION_NAME,
                        " has opened the database but some of the files are full ",
                        "and backups were not taken, so cannot offer ",
                        "the option of retrying the import with a larger file, ",
                        "and cannot restore the database.  The database may not ",
                        "be usable.",
                    )
                ),
            )
            self.close_database()
            return None
        # At least one file is not in Normal state.
        # None of these files had deferred updates for Import or the state does
        # not imply a file full condition where deferred updates occured.
        r = "\n".join(
            [
                "\t".join((os.path.basename(dbo.file), fistat[dbo][1]))
                for dbo in self.table.values()
            ]
        )
        action = tkinter.messagebox.askyesno(
            title="Open",
            message="".join(
                (
                    APPLICATION_NAME,
                    " has opened the database but some of the files are ",
                    "not in the Normal state.\n\n",
                    r,
                    "\n\nAt least one of these files is neither just ",
                    "marked Deferred Update nor marked Full, and backups were ",
                    "not taken, so ",
                    APPLICATION_NAME,
                    " is not offering the option of ",
                    "retrying the import with a larger file.\n\nDo you want to ",
                    "save a copy of the broken database?",
                )
            ),
        )
        self.close_database()
        if not action:
            return "Import failed"
        return False

    def open_after_import_with_backups(self, files=()):
        """Return open context after doing database engine specific actions.

        For DPT clear the file sizes before import area if the database was
        opened successfully as there is no need to retry the import.

        """
        super().open_database()

        # open_database() call after completion of Import sequence
        fistat = dict()
        file_sizes_for_import = dict()
        for dbn, dbo in self.table.items():
            gfp = dbo.get_file_parameters(self.dbenv)
            fistat[dbo] = gfp["FISTAT"]
            if dbn in files:
                file_sizes_for_import[dbn] = gfp
        for dbo in self.table.values():
            if fistat[dbo][0] != 0:
                break
        else:
            self.increase_database_size(files=None)
            self.mark_partial_positions_to_be_recalculated()
            return True
        # At least one file is not in Normal state after Import.
        # Check the files that had imports applied
        for dbn in file_sizes_for_import:
            status = file_sizes_for_import[dbn]["FISTAT"][0]
            flags = file_sizes_for_import[dbn]["FIFLAGS"]
            if not (
                (status == 0)
                or (status == FISTAT_DEFERRED_UPDATES)
                or (flags & FIFLAGS_FULL_TABLEB)
                or (flags & FIFLAGS_FULL_TABLED)
            ):
                break
        else:
            # The file states are consistent with the possibility that the
            # import failed because at least one file was too small.
            # The file size information is kept for calculating an increase
            # in file size before trying the import again.
            if tkinter.messagebox.askyesno(
                title="Retry Import",
                message="".join(
                    (
                        "The import failed because the games file was filled.\n\n",
                        "The file will be restored from backups.\n\nDo ",
                        "you want to retry the import with more space (20%) ",
                        "allocated to the games file?",
                    )
                ),
            ):
                return None
            else:
                self.close_database()
                return "Restore without retry"
        # At least one file is not in Normal state.
        # None of these files had deferred updates for Import or the state does
        # not imply a file full condition where deferred updates occured.
        r = "\n".join(
            [
                "\t".join((os.path.basename(dbo.file), fistat[dbo][1]))
                for dbo in self.table.values()
            ]
        )
        action = tkinter.messagebox.askyesno(
            title="Open",
            message="".join(
                (
                    APPLICATION_NAME,
                    " has opened the database but some of the files are ",
                    "not in the Normal state.\n\n",
                    r,
                    "\n\nAt least one of these files is neither just ",
                    "marked Deferred Update nor marked Full so ",
                    APPLICATION_NAME,
                    " is not offering the option of retrying ",
                    "the import with a larger file.\n\nDo you want to save a ",
                    "copy of the broken database before restoring from backups?",
                )
            ),
        )
        self.close_database()
        if not action:
            return "Import failed"
        return False

    def save_broken_database_details(self, files=()):
        """Save database engine specific detail of broken files to be restored.

        It is assumed that the Database Services object exists.

        """
        self._broken_sizes.clear()
        bs = self._broken_sizes
        for f in files:
            bs[f] = self.table[f].get_file_parameters(self.dbenv)
