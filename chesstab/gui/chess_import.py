# chess_import.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define menu of database import functions.

Add options to import chess games and related data to the menu bar.

"""

import os
import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog

from solentware_base import do_deferred_updates

from ..core.filespec import GAMES_FILE_DEF
from . import chess_database


class Chess(chess_database.Chess):
    """Allow import to a chess database."""

    def _database_import(self):
        """Import games to open database."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Import",
                message="No chess database open to receive import",
            )
            return
        if self._database_class is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Import",
                message="Database interface not defined",
            )
            return
        if sum(
            [
                len(i.stack)
                for i in (
                    self.ui.game_items,
                    self.ui.repertoire_items,
                    self.ui.partial_items,
                    self.ui.selection_items,
                )
            ]
        ):
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Import",
                message="".join(
                    (
                        "All game, repertoire, selection, and partial ",
                        "position, items must be closed before starting ",
                        "an import.",
                    )
                ),
            )
            return
        # Use askopenfilenames rather than askopenfilename with
        # multiple=Tkinter.TRUE because in freebsd port of Tkinter a tuple
        # is returned while at least some versions of the Microsoft Windows
        # port return a space separated string (which looks a lot like a
        # TCL list - curly brackets around path names containing spaces).
        # Then only the dialogues intercept of askopenfilenames needs
        # changing as askopenfilename with default multiple argument
        # returns a string containg one path name in all cases.
        #
        # Under Wine multiple=Tkinter.TRUE has no effect at Python 2.6.2 so
        # the dialogue supports selection of a single file only.
        gamefile = tkinter.filedialog.askopenfilenames(
            parent=self.get_toplevel(),
            title="Select file containing games to import",
            initialdir="~",
            filetypes=[("Portable Game Notation (chess)", ".pgn")],
        )
        if gamefile:
            self.statusbar.set_status_text(
                text="Please wait while importing PGN file"
            )
            # gives time for destruction of dialogue and widget refresh
            # does nothing for obscuring and revealing application later
            self.root.after_idle(
                self.try_command(self._import_pgnfiles, self.root), gamefile
            )

    def _import_repertoires(self):
        """Import repertoires from PGN-like file."""
        if self.is_import_subprocess_active():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Import Repertoires",
                message="An import of PGN data is in progress",
            )
            return
        tkinter.messagebox.showinfo(
            parent=self.get_toplevel(),
            title="Import Repertoires",
            message="Not implemented",
        )

    def _import_positions(self):
        """Import positions from text file."""
        if self.is_import_subprocess_active():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Import Positions",
                message="An import of PGN data is in progress",
            )
            return
        tkinter.messagebox.showinfo(
            parent=self.get_toplevel(),
            title="Import Positions",
            message="Not implemented",
        )

    def _import_pgnfiles(self, pgnfiles):
        """Import games to open database."""
        self.ui.set_import_subprocess()  # raises exception if already active
        self._pgnfiles = pgnfiles
        usedu = self.opendatabase.use_deferred_update_process(
            dptmultistepdu=self._dptmultistepdu,
            dptchunksize=self._dptchunksize,
        )
        if usedu is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Import",
                message="".join(
                    (
                        "Import\n\n",
                        "\n".join([os.path.basename(p) for p in pgnfiles]),
                        "\n\ncancelled",
                    )
                ),
            )
            self.statusbar.set_status_text(text="")
            return
        self.opendatabase.close_database_contexts()
        self.ui.set_import_subprocess(
            subprocess_id=do_deferred_updates.do_deferred_updates(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), usedu
                ),
                self.opendatabase.home_directory,
                pgnfiles,
            )
        )
        self._wait_deferred_updates(pgnfiles)
        return

    def _wait_deferred_updates(self, pgnfiles):
        """Wait until subprocess doing deferred updates completes.

        pgnfiles - the PGN files being imported

        Wait for import subprocess to finish in a thread then do restart
        User Interface actions after idletasks.

        """
        del pgnfiles

        def completed():
            self.ui.get_import_subprocess().wait()

            # See comment near end of class definition ChessDeferredUpdate in
            # sibling module chessdu for explanation of this change.
            # self.root.after_idle(
            #     self.try_command(after_completion, self.root))
            self.reportqueue.put(
                (
                    self._try_command_after_idle,
                    (after_completion, self.root),
                    dict(),
                )
            )

        def after_completion():
            returncode = self.ui.get_import_subprocess().returncode
            names, archives, guards = self.opendatabase.get_archive_names(
                files=(GAMES_FILE_DEF,)
            )
            if len(guards) != len(archives):
                # Failed or cancelled while taking backups
                if returncode == 0:
                    msg = "was cancelled "
                else:
                    msg = "failed "
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    title="Import",
                    message="".join(
                        (
                            "The import ",
                            msg,
                            "before completion of backups.",
                            "\n\nThe database has not been changed and will ",
                            "be opened after deleting these backups.",
                        )
                    ),
                )
                self._tidy_up_after_import(tidy_backups, names)
                return
            if len(archives) == 0:
                # Succeeded, or failed with no backups
                if returncode != 0:
                    # Failed with no backups
                    tkinter.messagebox.showinfo(
                        parent=self.get_toplevel(),
                        title="Import",
                        message="".join(
                            (
                                "The import failed.\n\nBackups were not ",
                                "taken so the database cannot be restored ",
                                "and may not be usable.",
                            )
                        ),
                    )
                    self._tidy_up_after_import(dump_database, names)
                    return
                oaiwb = self.opendatabase.open_after_import_without_backups
                try:
                    action = oaiwb(files=(GAMES_FILE_DEF,))
                except self.opendatabase.__class__.SegmentSizeError:
                    action = oaiwb(files=(GAMES_FILE_DEF,))
                if action is None:
                    # Database full
                    self.statusbar.set_status_text(text="Database full")
                elif action is False:
                    # Unable to open database files
                    self._tidy_up_after_import(dump_database, names)
                elif action is True:
                    # Succeeded
                    self.ui.set_import_subprocess()
                    self._refresh_grids_after_import()
                    self.statusbar.set_status_text(text="")
                else:
                    # Failed
                    self.statusbar.set_status_text(text=action)
                return
            # Succeeded, or failed with backups
            try:
                action = self.opendatabase.open_after_import_with_backups()
            except self.opendatabase.__class__.SegmentSizeError:
                action = self.opendatabase.open_after_import_with_backups()
            if action is None:
                # Database full
                self.opendatabase.save_broken_database_details(
                    files=(GAMES_FILE_DEF,)
                )
                self.opendatabase.close_database_contexts()
                self._tidy_up_after_import(
                    restore_backups_and_retry_imports, names, (GAMES_FILE_DEF,)
                )
            elif action is False:
                # Unable to open database files
                self._tidy_up_after_import(
                    save_broken_and_restore_backups, names
                )
            elif action is True:
                # Succeeded
                self.ui.set_import_subprocess()
                self._refresh_grids_after_import()
                self.statusbar.set_status_text(text="")
            else:
                # Failed
                self._tidy_up_after_import(restore_backups, names)
            return

        def dump_database(names):
            # prompt to move existing dump first, and where to do this?
            self.statusbar.set_status_text(
                text="Please wait while saving copy of broken database"
            )
            self.opendatabase.dump_database(names=names)
            self.ui.set_import_subprocess()
            self._refresh_grids_after_import()
            self.statusbar.set_status_text(text="Broken database")

        def restore_backups(names):
            self.statusbar.set_status_text(
                text="Please wait while restoring database from backups"
            )
            self.opendatabase.restore_backups(names=names)
            self.statusbar.set_status_text(
                text="Please wait while deleting backups"
            )
            self.opendatabase.delete_backups(names=names)
            self.ui.set_import_subprocess()
            self._refresh_grids_after_import()
            self.statusbar.set_status_text(text="")

        def restore_backups_and_retry_imports(names, files):
            self.statusbar.set_status_text(
                text="Please wait while restoring database from backups"
            )
            self.opendatabase.restore_backups(names=names)
            self.statusbar.set_status_text(
                text="Please wait while deleting backups"
            )
            self.opendatabase.delete_backups(names=names)
            self._retry_import(files)

        def save_broken_and_restore_backups(names):
            self.statusbar.set_status_text(
                text="Please wait while saving copy of broken database"
            )
            self.opendatabase.dump_database(names=names)
            self.statusbar.set_status_text(
                text="Please wait while restoring database from backups"
            )
            self.opendatabase.restore_backups(names=names)
            self.statusbar.set_status_text(
                text="Please wait while deleting backups"
            )
            self.opendatabase.delete_backups(names=names)
            self.ui.set_import_subprocess()
            self._refresh_grids_after_import()
            self.statusbar.set_status_text(text="")

        def tidy_backups(names):
            self.statusbar.set_status_text(
                text="Please wait while deleting backups"
            )
            self.opendatabase.delete_backups(names=names)
            self.ui.set_import_subprocess()
            self._refresh_grids_after_import()
            self.statusbar.set_status_text(text="")

        self.queue.put_method(self.try_thread(completed, self.root))

    def _tidy_up_after_import(self, tidy_up_method, *a):
        """Create a Toplevel to report actions of tidy_up_method.

        Run tidy_up_method in a thread and wait for completion.

        """
        self.queue.put_method(self.try_thread(tidy_up_method, self.root), a)

    def _refresh_grids_after_import(self):
        """Repopulate grid from database after import."""
        # See _wait_deferred_update comment at call to this method.
        # Gets stuck in on_data_change.
        self.ui.base_games.on_data_change(None)
        if self.ui.game_items.count_items_in_stack():
            self.ui.game_games.set_partial_key()
            self.ui.game_items.active_item.set_game_list()
        if self.ui.partial_items.count_items_in_stack():
            self.ui.partial_games.set_partial_key()
            self.ui.partial_items.active_item.refresh_game_list()

    def _try_command_after_idle(self, method, widget):
        """Run command in main thread after idle."""
        self.root.after_idle(self.try_command(method, widget))

    def _retry_import(self, files):
        """Open database and retry import with increased file sizes.

        DPT does not increase file sizes automatically as needed.
        The action still makes sense in Berkeley DB if other files had to be
        deleted to allow the automatic increase to occur.

        """
        self.opendatabase.open_database_contexts(files=files)
        self.opendatabase.adjust_database_for_retry_import(files)
        self.opendatabase.close_database_contexts()
        if self._pgnfiles:
            self.statusbar.set_status_text(
                text="Please wait while importing PGN file"
            )
            self.root.after_idle(
                self.try_command(self._import_pgnfiles, self.root),
                self._pgnfiles,
            )
