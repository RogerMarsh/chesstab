# database.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess games database using DPT database via dpt_dbms.dptapi."""

import os
import tkinter.messagebox

# pylint always gives import-error message, E0401, on non-Microsoft Windows
# systems; or if dpt_dbms is not installed.
# Wine counts as a Microsft Windows system.
# It is reasonable to not install dpt_dbms.
# The importlib module is used elsewhere to import dpt_dbms if needed.
from dpt_dbms.dptapi import (
    FIFLAGS_FULL_TABLEB,
    FIFLAGS_FULL_TABLED,
)

from .. import APPLICATION_NAME
from . import dptnofistat


class Database(dptnofistat.Database):
    """Provide access to a DPT database of games of chess.

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

    def open_database(self, files=None):
        """Return True if all files are opened in Normal mode (FISTAT == 0)."""
        super().open_database(files=files)
        fistat = []
        for dbo in self.table.values():
            parameters = dbo.get_file_parameters(self.dbenv)
            fistat.extend(
                [(k, v) for k, v in parameters.items() if k[1] == "FISTAT"]
            )
        fistat_errors = []
        for item in fistat:
            if item[1][0] != 0:
                fistat_errors.append("\t".join((item[0][0], item[1][1])))
        if not fistat_errors:
            self.increase_database_size(files=None)
            return True

        # At least one file is not in Normal state
        report = "\n".join(fistat_errors)
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
            fistat[dbo] = gfp[os.path.basename(dbo.file), "FISTAT"]
            if dbn in files:
                file_sizes_for_import[dbn] = gfp[
                    os.path.basename(dbo.file), "FIFLAGS"
                ]
        for dbo in self.table.values():
            if fistat[dbo][0] != 0:
                break
        else:
            # Assume all is well as file status is 0
            # Or just do nothing (as file_sizes_for_import may be removed)
            self.increase_database_size(files=None)
            # self.mark_all_cql_statements_for_evaluation()
            return True
        # At least one file is not in Normal state after Import.
        # Check the files that had imports applied
        for flags in file_sizes_for_import.values():
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
