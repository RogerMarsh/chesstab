# chess_database.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define menu of database functions excluding data import and export.

The database engine used by a run of ChessTab is chosen when a database is
first opened or created.

An existing database can be opened only if the database engine with which it
was created is available.

A new database is created using the first database engine interface available
from the list in order:

dptdb    DPT (an emulation of Model 204 on MS Windows) via SWIG interface
bsddb3   Berkeley DB
apsw     Sqlite3
sqlite3  Sqlite3

"""

import os
import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import gc

from solentware_grid.core.dataclient import DataSource

from solentware_base import modulequery

from .gamerow import chess_db_row_game
from .querydisplay import QueryDisplayInsert
from . import options
from .. import APPLICATION_DATABASE_MODULE, APPLICATION_NAME
from .. import (
    PARTIAL_POSITION_MODULE,
    FULL_POSITION_MODULE,
    ANALYSIS_MODULE,
    SELECTION_MODULE,
)
from ..core.filespec import (
    FileSpec,
    GAMES_FILE_DEF,
)
from . import chess_widget


class ChessError(Exception):
    """Exception class fo chess module."""


# Convert module constants _FullPositionDS and others to class attribute
# names because the default class-attribute-naming-style is 'any'.
class _Import:
    """Names of classes imported by import_module from alternative modules.

    For runtime "from <db|dpt>results import ChessDatabase" and similar.
    """

    ChessDatabase = "ChessDatabase"
    FullPositionDS = "FullPositionDS"
    ChessQueryLanguageDS = "ChessQueryLanguageDS"
    AnalysisDS = "AnalysisDS"
    SelectionDS = "SelectionDS"


class Chess(chess_widget.Chess):
    """Connect a chess database with User Interface."""

    def database_open(self):
        """Open chess database."""
        if self.opendatabase is not None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="A chess database is already open",
                title="Open",
            )
            return

        chessfolder = tkinter.filedialog.askdirectory(
            parent=self.get_toplevel(),
            title="Select folder containing a chess database",
            initialdir="~",
            mustexist=tkinter.TRUE,
        )
        if not chessfolder:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="Open chess database cancelled",
                title="Open",
            )
            return

        # Set the error file in top folder of chess database
        self._set_error_file_name(directory=chessfolder)

        interface_modules = modulequery.modules_for_existing_databases(
            chessfolder, FileSpec()
        )
        # A database module is chosen when creating the database
        # so there should be either only one entry in edt or None
        if not interface_modules:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "Chess database in ",
                        os.path.basename(chessfolder),
                        " cannot be opened, or there isn't one.\n\n",
                        "(Is correct database engine available?)",
                    )
                ),
                title="Open",
            )
            return
        if len(interface_modules) > 1:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "There is more than one chess database in folder\n\n",
                        os.path.basename(chessfolder),
                        "\n\nMove the databases to separate folders and try ",
                        "again.  (Use the platform tools for moving files to ",
                        "relocate the database files.)",
                    )
                ),
                title="Open",
            )
            return

        idm = modulequery.installed_database_modules()
        _enginename = None
        for key, value in idm.items():
            if value in interface_modules[0]:
                if _enginename:
                    tkinter.messagebox.showinfo(
                        parent=self.get_toplevel(),
                        message="".join(
                            (
                                "Several modules able to open database in\n\n",
                                os.path.basename(chessfolder),
                                "\n\navailable.  Unable to choose.",
                            )
                        ),
                        title="Open",
                    )
                    return
                _enginename = key
        if _enginename is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "No modules able to open database in\n\n",
                        os.path.basename(chessfolder),
                        "\n\navailable.",
                    )
                ),
                title="Open",
            )
            return
        _modulename = APPLICATION_DATABASE_MODULE[_enginename]
        if self._database_modulename != _modulename:
            if self._database_modulename is not None:
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    message="".join(
                        (
                            "The database engine needed for this database ",
                            "is not the one already in use.\n\nYou will ",
                            "have to Quit and start the application again ",
                            "to open this database.",
                        )
                    ),
                    title="Open",
                )
                return
            self._database_enginename = _enginename
            self._database_modulename = _modulename

            def import_name(modulename, name):
                try:
                    module = __import__(
                        modulename, globals(), locals(), [name]
                    )
                except ImportError:
                    return None
                return getattr(module, name)

            self._database_class = import_name(
                _modulename, _Import.ChessDatabase
            )
            self._fullposition_class = import_name(
                FULL_POSITION_MODULE[_enginename], _Import.FullPositionDS
            )
            self._partialposition_class = import_name(
                PARTIAL_POSITION_MODULE[_enginename],
                _Import.ChessQueryLanguageDS,
            )
            self._engineanalysis_class = import_name(
                ANALYSIS_MODULE[_enginename], _Import.AnalysisDS
            )
            self._selection_class = import_name(
                SELECTION_MODULE[_enginename], _Import.SelectionDS
            )

        try:
            self._database_open(chessfolder)
        except Exception as exc:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "Unable to open database\n\n",
                        str(chessfolder),
                        "\n\nThe reported reason is:\n\n",
                        str(exc),
                    )
                ),
                title="Open",
            )
            self._database_close()
            self.opendatabase = None
            # pylint message broad-except.
            # Can keep going for some exceptions.
            raise ChessError(
                " database in ".join(("Unable to open", APPLICATION_NAME))
            ) from exc

    def database_new(self):
        """Create and open a new chess database."""
        if self.opendatabase is not None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="A chess database is already open",
                title="New",
            )
            return

        chessfolder = tkinter.filedialog.askdirectory(
            parent=self.get_toplevel(),
            title="Select folder for new chess database",
            initialdir="~",
        )
        if not chessfolder:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="Create new chess database cancelled",
                title="New",
            )
            return

        if os.path.exists(chessfolder):
            if modulequery.modules_for_existing_databases(
                chessfolder, FileSpec()
            ):
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    message="".join(
                        (
                            "A chess database already exists in ",
                            os.path.basename(chessfolder),
                        )
                    ),
                    title="New",
                )
                return
        else:
            try:
                os.makedirs(chessfolder)
            except OSError:
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    message="".join(
                        (
                            "Folder ",
                            os.path.basename(chessfolder),
                            " already exists",
                        )
                    ),
                    title="New",
                )
                return

        # Set the error file in top folder of chess database
        self._set_error_file_name(directory=chessfolder)

        # the default preference order is used rather than ask the user or
        # an order specific to this application.  An earlier version of this
        # module implements a dialogue to pick a database engine if there is
        # a choice.
        idm = modulequery.installed_database_modules()
        if len(idm) == 0:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "No modules able to create database in\n\n",
                        os.path.basename(chessfolder),
                        "\n\navailable.",
                    )
                ),
                title="New",
            )
            return
        _modulename = None
        _enginename = None
        for ename in modulequery.DATABASE_MODULES_IN_DEFAULT_PREFERENCE_ORDER:
            if ename in idm:
                if ename in APPLICATION_DATABASE_MODULE:
                    _enginename = ename
                    _modulename = APPLICATION_DATABASE_MODULE[ename]
                    break
        if _modulename is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "None of the available database engines can be ",
                        "used to create a database.",
                    )
                ),
                title="New",
            )
            return
        if self._database_modulename != _modulename:
            if self._database_modulename is not None:
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    message="".join(
                        (
                            "The database engine needed for this database ",
                            "is not the one already in use.\n\nYou will ",
                            "have to Quit and start the application again ",
                            "to create this database.",
                        )
                    ),
                    title="New",
                )
                return
            self._database_enginename = _enginename
            self._database_modulename = _modulename

            def import_name(modulename, name):
                try:
                    module = __import__(
                        modulename, globals(), locals(), [name]
                    )
                except ImportError:
                    return None
                return getattr(module, name)

            self._database_class = import_name(
                _modulename, _Import.ChessDatabase
            )
            self._fullposition_class = import_name(
                FULL_POSITION_MODULE[_enginename], _Import.FullPositionDS
            )
            self._partialposition_class = import_name(
                PARTIAL_POSITION_MODULE[_enginename],
                _Import.ChessQueryLanguageDS,
            )
            self._engineanalysis_class = import_name(
                ANALYSIS_MODULE[_enginename], _Import.AnalysisDS
            )
            self._selection_class = import_name(
                SELECTION_MODULE[_enginename], _Import.SelectionDS
            )

        try:
            self._database_open(chessfolder)
        except Exception as exc:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                message="".join(
                    (
                        "Unable to create database\n\n",
                        str(chessfolder),
                        "\n\nThe reported reason is:\n\n",
                        str(exc),
                    )
                ),
                title="New",
            )
            self._database_close()
            # self.database = None  # Should be 'self.opendatabase = None'?
            # pylint message broad-except.
            # Can keep going for some exceptions.
            raise ChessError(
                " database in ".join(("Unable to create", APPLICATION_NAME))
            ) from exc

    def database_close(self):
        """Close chess database."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Close",
                message="No chess database open",
            )
        elif self._database_class is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Close",
                message="Database interface not defined",
            )
        elif self.is_import_subprocess_active():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Close",
                message="An import of PGN data is in progress",
            )
        else:
            dlg = tkinter.messagebox.askquestion(
                parent=self.get_toplevel(),
                title="Close",
                message="Close chess database",
            )
            if dlg == tkinter.messagebox.YES:
                if self.opendatabase:
                    self._database_close()
                    self.opendatabase = None

    def database_delete(self):
        """Delete chess database."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Delete",
                message="".join(
                    (
                        "Delete will not delete a database unless it can be ",
                        "opened.\n\nOpen the database and then Delete it.",
                    )
                ),
            )
            return
        dlg = tkinter.messagebox.askquestion(
            parent=self.get_toplevel(),
            title="Delete",
            message="".join(
                (
                    "Please confirm that the chess database in\n\n",
                    self.opendatabase.home_directory,
                    "\n\nis to be deleted.",
                )
            ),
        )
        if dlg == tkinter.messagebox.YES:

            # Replicate _database_close replacing close_database() call with
            # delete_database() call.  The close_database() call just before
            # setting opendatabase to None is removed.
            self._close_recordsets()
            message = self.opendatabase.delete_database()
            if message:
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(), title="Delete", message=message
                )
            self.root.wm_title(APPLICATION_NAME)
            self.ui.set_open_database_and_engine_classes()
            self.ui.hide_game_grid()
            self._set_error_file_name(directory=None)

            message = "".join(
                (
                    "The chess database in\n\n",
                    self.opendatabase.home_directory,
                    "\n\nhas been deleted.",
                )
            )
            self.opendatabase = None
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(), title="Delete", message=message
            )
        else:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Delete",
                message="The chess database has not been deleted",
            )

    def index_select(self):
        """Enter a new index seletion (callback for Menu option)."""
        self.new_index_selection()

    def new_index_selection(self):
        """Enter a new index selection."""
        selection = QueryDisplayInsert(
            master=self.ui.view_selection_rules_pw,
            ui=self.ui,
            items_manager=self.ui.selection_items,
            itemgrid=self.ui.base_games,
        )  # probably main list of games
        selection.query_statement.process_query_statement("")
        selection.set_and_tag_item_text(reset_undo=True)
        self.ui.add_selection_rule_to_display(selection)
        try:
            # Is new window only one available for user interaction?
            if self.root.focus_displayof() != self.root:
                return
        except KeyError:
            # Launch; Database Open; Database Close; Position Partial
            pass

        # Wrap to take account of self.ui.single_view
        self.ui.selection_items.active_item.takefocus_widget.focus_set()

    def index_show(self):
        """Show list of stored stored selection rules."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Show",
                message="No chess database open",
            )
        elif self.ui.base_selections.is_visible():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Show",
                message="Selection rules already shown",
            )
        else:
            self.ui.show_selection_rules_grid(self.opendatabase)

    def index_hide(self):
        """Hide list of stored selection rules."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Hide",
                message="No chess database open",
            )
        elif not self.ui.base_selections.is_visible():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Hide",
                message="Selection rules already hidden",
            )
        else:
            self.ui.hide_selection_rules_grid()

    def create_options_index_callback(self, index):
        """Return callback to bind to index selection menu buttons."""

        def index_changed():
            """Set the index used to display list of games."""
            if self.opendatabase is None:
                tkinter.messagebox.showinfo(
                    parent=self.get_toplevel(),
                    title="Select Index for games database",
                    message="No chess database open",
                )
                return

            ui = self.ui
            self._index = index
            ui.base_games.set_data_source(
                DataSource(
                    self.opendatabase,
                    GAMES_FILE_DEF,
                    self._index,
                    chess_db_row_game(ui),
                ),
                ui.base_games.on_data_change,
            )
            if ui.base_games.datasource.recno:
                ui.base_games.set_partial_key()
            ui.base_games.load_new_index()
            if ui.base_games.datasource.dbname in ui.allow_filter:
                ui.set_toolbarframe_normal(ui.move_to_game, ui.filter_game)
            else:
                ui.set_toolbarframe_disabled()

        return index_changed

    def position_show(self):
        """Show list of stored partial positions."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Show",
                message="No chess database open",
            )
        elif self.ui.base_partials.is_visible():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Show",
                message="Partial positions already shown",
            )
        else:
            self.ui.show_partial_position_grid(self.opendatabase)

    def position_hide(self):
        """Hide list of stored partial positions."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Hide",
                message="No chess database open",
            )
        elif not self.ui.base_partials.is_visible():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Hide",
                message="Partial positions already hidden",
            )
        else:
            self.ui.hide_partial_position_grid()

    def repertoire_show(self):
        """Show list of stored repertoire games (opening variations)."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Show",
                message="No chess database open",
            )
        elif self.ui.base_repertoires.is_visible():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Show",
                message="Opening variations already shown",
            )
        else:
            self.ui.show_repertoire_grid(self.opendatabase)

    def repertoire_hide(self):
        """Hide list of stored repertoire games (opening variations)."""
        if self.opendatabase is None:
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Hide",
                message="No chess database open",
            )
        elif not self.ui.base_repertoires.is_visible():
            tkinter.messagebox.showinfo(
                parent=self.get_toplevel(),
                title="Hide",
                message="Opening variations already hidden",
            )
        else:
            self.ui.hide_repertoire_grid()

    def _database_open(self, chessfolder):
        """Open chess database after creating it if necessary."""
        self.opendatabase = self._database_class(
            chessfolder, **self._chessdbkargs
        )
        self.opendatabase.open_database()
        self.ui.set_board_colours_from_options(
            options.get_saved_options(chessfolder)
        )
        # start code also used in _retry_import
        self.root.wm_title(
            " - ".join(
                (
                    APPLICATION_NAME,
                    os.path.join(
                        os.path.basename(os.path.dirname(chessfolder)),
                        os.path.basename(chessfolder),
                    ),
                )
            )
        )
        self.ui.set_open_database_and_engine_classes(
            database=self.opendatabase,
            fullpositionclass=self._fullposition_class,
            partialpositionclass=self._partialposition_class,
            engineanalysisclass=self._engineanalysis_class,
            selectionclass=self._selection_class,
        )
        self.ui.base_games.set_data_source(
            DataSource(
                self.opendatabase,
                GAMES_FILE_DEF,
                self._index,
                chess_db_row_game(self.ui),
            )
        )
        self.ui.show_game_grid(self.opendatabase)
        # end code also used in _retry_import

    def _database_close(self):
        """Close database and hide database display widgets."""
        self._close_recordsets()
        self.opendatabase.close_database()
        self.root.wm_title(APPLICATION_NAME)

        # Order matters after changes to solentware-base first implemented as
        # solentware-bitbases in March 2019.
        # Conjecture is timing may still lead to exception in calls, driven by
        # timer, to find_engine_analysis().  None seen yet.
        self.ui.set_open_database_and_engine_classes()
        self.ui.hide_game_grid()

        self._set_error_file_name(directory=None)

    # Close recordsets which do not have a defined lifetime.
    # Typically a recordset representing a scrollable list of records where
    # the records on the list vary with the state of a controlling widget.
    # Called just before opendatabase.close_database() to prevent the recordset
    # close() method being called on 'del recordset' after close_database() has
    # deleted the recordsets.
    # (The _dpt module needs this, but _db and _sqlite could get by without.)
    def _close_recordsets(self):
        ui = self.ui

        # If base_games is populated from a selection rule the datasource will
        # have a recordset which must be destroyed before the database is
        # closed.
        # This only affects DPT databases (_dpt module) but the _sqlite and _db
        # modules have 'do-nothing' methods to fit.
        data_source = ui.base_games.datasource
        if (
            data_source
            and hasattr(data_source, "recordset")
            and data_source.recordset is not None
        ):
            data_source.recordset.close()

        for grid in ui.game_games, ui.repertoire_games, ui.partial_games:
            data_source = grid.datasource
            if data_source:
                if data_source.recordset:
                    data_source.recordset.close()

        # This closes one of the five _DPTRecordSet instances which cause a
        # RuntimeError, because of an APIDatabaseContext.DestroyRecordSets()
        # call done earlier in close database sequence, in __del__ after doing
        # the sample CQL query 'cql() Pg7'.  Adding, say, pb3, to the query
        # raises the RuntimeError count to five, from four, while doing just
        # 'cql()' gets rid of all the RuntimeError exceptions.
        # Quit after close database otherwise finishes normally, but open drops
        # into MicroSoft Window's 'Not Responding' stuff sometimes.  Or perhaps
        # I have not seen it happen for quit yet.
        # The origin of the other four _DPTRecordSet instances has not been
        # traced yet.
        if ui.partial_games.datasource:
            ui.partial_games.datasource.cqlfinder = None

        # Not sure why these need an undefined lifetime.
        for item in ui.game_items, ui.repertoire_items:
            for widget in item.order:
                data_source = widget.analysis_data_source
                if data_source:
                    if data_source.recordset:
                        data_source.recordset.close()
        for widget in ui.selection_items.order:

            # widget.query_statement.where.node.result.answer is an example
            # instance that must be closed when query answer is displayed.
            # If query is typed in, not read from database, the DPT message
            # 'Bug: this context has no such record set object (any more?)'
            # is reported in a RuntimeError exception.  _DPTRecordList.__del__
            # raises this, and the problem is the DestroyAllRecordSets() call
            # done by close_database before the _DPTRecordList instance is
            # deleted.
            # Attribute widget.query_statement.where.node.result.answer is an
            # example. Closing the instance here clears the problem.
            # If query is read from database, a 'Python has stopped working'
            # dialogue is presented and Windows tries to find a solution!
            # I assume the cause is the lingering _DPTRecordList.
            # May need to add this to get rid of constraints in the Where tree.
            # if widget.datasource:
            #    widget.datasource.where = None
            pass

        for widget in ui.partial_items.order:

            # Same as selection_items, just above, for a typed CQL query but I
            # have not tracked down an example.
            # No problem for CQL query read from database.
            pass

        # Used print() to trace what was going on.
        # Gave each _DPTRecordList and _DPTFoundSet __init__ call a serial
        # number, defined as _DPTRecordSet.serial and held as self._serial,
        # which was printed for the instances which got a RuntimeError.
        # It was the same serials each time for the same query.
        # A traceback.print_stack() in __init__ showed the same profile for
        # each of these instances when created.
        # print() statements on entry to each method mentioned in the traceback
        # showed nothing unusual about these cases compared with all the others
        # which 'behaved properly' for deletion.
        # So tried forcing garbage collection, which seemed to work and does
        # not break the _db or _sqlite cases.
        gc.collect()
