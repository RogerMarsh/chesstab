# chessdpt.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess games database using DPT database via dptdb.dptapi."""

import os
import tkinter.messagebox

# pylint will always give import-error message on non-Microsoft Windows
# systems.
# Wine counts as a Microsft Windows system.
# It is reasonable to not install 'dptdb.dptapi'.
# The importlib module is used to import chessdpt if needed.
from dptdb.dptapi import (
    FIFLAGS_FULL_TABLEB,
    FIFLAGS_FULL_TABLED,
)

from .. import APPLICATION_NAME
from . import chessdptnofistat


class ChessDatabase(chessdptnofistat.ChessDatabase):
    """Provide access to a database of games of chess.

    The open_database() method is extended in a number of ways, all but
    one with a new name.  These methods take the FISTAT flags into
    account when attempting to open the database.
    """

    def __init__(self, *args, **kwargs):
        """Define chess database.

        See superclass for argument descriptions.

        """
        super().__init__(*args, **kwargs)
        self._broken_sizes = {}

    def adjust_database_for_retry_import(self, files):
        """Increase file sizes taking file full into account."""
        # Increase the size of files allowing for the file full condition
        # which occurred while doing a deferred update for import.
        for dbn, broken_sizes in self._broken_sizes.items():
            self.table[dbn].increase_size_of_full_file(
                self.dbenv,
                self.table[dbn].get_file_parameters(self.dbenv),
                broken_sizes,
            )

    def open_database(self, files=None):
        """Return True if all files are opened in Normal mode (FISTAT == 0)."""
        super().open_database(files=files)
        fistat = {}
        for dbo in self.table.values():
            fistat[dbo] = dbo.get_file_parameters(self.dbenv)["FISTAT"]
        for dbo in self.table.values():
            if fistat[dbo][0] != 0:
                break
        else:
            self.increase_database_size(files=None)
            return True

        # At least one file is not in Normal state
        report = "\n".join(
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
                    report,
                    "\n\n",
                    APPLICATION_NAME,
                    " will close the database on dismissing this ",
                    "dialogue.\n\nRestore the database from backups, or ",
                    "source data, before trying again.",
                )
            ),
        )
        self.close_database()

    def _delete_database_names(self):
        """Override and return tuple of filenames to delete."""
        names = [self.sysfolder]
        for value in self.table.values():
            names.append(value.file)
        return tuple(names)

    def get_archive_names(self, file=None):
        """Return names and operating system files for archives and guards."""
        names = [v.file for k, v in self.table.items() if k == file]
        archives = {}
        guards = {}
        for name in names:
            archiveguard = ".".join((name, "grd"))
            archivefile = ".".join((name, "bz2"))
            for box, arch in ((archives, archivefile), (guards, archiveguard)):
                if os.path.exists(arch):
                    box[name] = arch
        return (names, archives, guards)

    def open_after_import(self, files=()):
        """Return open context after doing database engine specific actions.

        For DPT clear the file sizes before import area if the database was
        opened successfully as there is no need to retry the import.

        """
        super().open_database()
        fistat = {}
        file_sizes_for_import = {}
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
        for file_sizes in file_sizes_for_import.values():
            # pylint message unused variable.
            # Document what seemed to matter at some point.
            # status = file_sizes["FISTAT"][0]
            flags = file_sizes["FIFLAGS"]
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
                        " has opened the database but some of the files are ",
                        "full.  The database may not be usable.",
                    )
                ),
            )
            # self.close_database()
            return None
        # At least one file is not in Normal state.
        # None of these files had deferred updates for Import or the state does
        # not imply a file full condition where deferred updates occured.
        report = "\n".join(
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
                    report,
                    "\n\nAt least one of these files is neither just ",
                    "marked Deferred Update nor marked Full.  The ",
                    "database may not be usable.",
                )
            ),
        )
        # self.close_database()
        return True

    def save_broken_database_details(self, files=()):
        """Save database engine specific detail of broken files to be restored.

        It is assumed that the Database Services object exists.

        """
        self._broken_sizes.clear()
        broken = self._broken_sizes
        for file in files:
            broken[file] = self.table[file].get_file_parameters(self.dbenv)
