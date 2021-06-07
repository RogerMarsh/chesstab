# querydisplay.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit game selection rules.

These four classes display game selection rules in the main window: they are
used in the querygrid module.

The _QueryDisplay class provides attributes and behaviour shared by the
QueryDisplay, QueryDisplayInsert, and QueryDisplayEdit, classes.  It also
provides properties to support implementation of behaviour shared with the
Game*, Repertoire*, and CQL*, classes.

The QueryDisplay, QueryDisplayInsert, and QueryDisplayEdit, classes are
subclasses of the relevant ShowText, InsertText, EditText, DisplayText, and
ListGamesText, classes from the displaytext module; to implement behaviour
shared with all Text widgets in the main display (that includes widgets
displaying PGN text).

"""

import tkinter
import tkinter.messagebox

from solentware_base.core.where import WhereError

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from ..core.querystatement import QueryStatement
from .query import Query
from .queryedit import QueryEdit
from ..core.chessrecord import ChessDBrecordQuery
from .eventspec import EventSpec
from .display import Display
from .displaytext import (
    ShowText,
    InsertText,
    EditText,
    DisplayText,
    ListGamesText,
)


class _QueryDisplay(ExceptionHandler, Display):

    """Extend and link game selection rule to database.

    sourceobject - link to database.

    Attribute binding_labels specifies the order navigation bindings appear
    in popup menus.

    Method insert_item_database allows records to be inserted into a database
    from any CQL widget.

    """

    binding_labels = (
        EventSpec.navigate_to_position_grid,
        EventSpec.navigate_to_active_game,
        EventSpec.navigate_to_game_grid,
        EventSpec.navigate_to_repertoire_grid,
        EventSpec.navigate_to_active_repertoire,
        EventSpec.navigate_to_repertoire_game_grid,
        EventSpec.navigate_to_partial_grid,
        EventSpec.navigate_to_active_partial,
        EventSpec.navigate_to_selection_rule_grid,
        EventSpec.selectiondisplay_to_previous_selection,
        EventSpec.selectiondisplay_to_next_selection,
        EventSpec.navigate_to_partial_game_grid,
        EventSpec.tab_traverse_backward,
        EventSpec.tab_traverse_forward,
    )

    def __init__(self, sourceobject=None, **ka):
        """Extend and link game selection rule to database."""
        super().__init__(**ka)
        self.blockchange = False
        if self.ui.base_selections.datasource:
            self.set_data_source(self.ui.base_selections.get_data_source())
        self.sourceobject = sourceobject
        self.insertonly = sourceobject is None
        self.recalculate_after_edit = sourceobject

    @property
    def ui_displayed_items(self):
        return self.ui.selection_items

    @property
    def ui_configure_item_list_grid(self):
        return self.ui.configure_selection_grid

    @property
    def ui_set_item_name(self):
        return self.ui._set_selection_name

    @property
    def ui_set_find_item_games(self):
        return self.ui._set_find_selection_name_games

    def get_navigation_events(self):
        """Return event description tuple for navigation from selection rule
        statement."""
        return (
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (EventSpec.navigate_to_active_game, self.set_focus_gamepanel_item),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (
                EventSpec.navigate_to_repertoire_grid,
                self.set_focus_repertoire_grid,
            ),
            (
                EventSpec.navigate_to_active_repertoire,
                self.set_focus_repertoirepanel_item,
            ),
            (
                EventSpec.navigate_to_repertoire_game_grid,
                self.set_focus_repertoire_game_grid,
            ),
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item,
            ),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.selectiondisplay_to_previous_selection,
                self.prior_item,
            ),
            (EventSpec.selectiondisplay_to_next_selection, self.next_item),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_round, self.traverse_round),
        )

    def delete_item_view(self, event=None):
        """Remove game selection rule item from screen."""
        self.ui.delete_selection_rule_view(self)

    def insert_item_database(self, event=None):
        """Add game selection rule to database."""
        if self.ui.selection_items.active_item is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert Game Selection Rule",
                message="No active game selection rule to insert into database.",
            )
            return

        # This should see if game selection rule with same name already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert Game Selection Rule",
                message="Cannot add game selection rule:\n\nNo database open.",
            )
            return

        datasource = self.ui.base_selections.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert Game Selection Rule",
                message="Cannot add game selection rule:\n\nRule list hidden.",
            )
            return
        updater = ChessDBrecordQuery()
        updater.value.set_database(datasource.dbhome)
        updater.value.dbset = self.ui.base_games.datasource.dbset
        uvpqs = updater.value.process_query_statement(
            self.get_name_query_statement_text()
        )
        if not len(updater.value.get_name_text()):
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title="Insert Game Selection Rule",
                message="".join(
                    (
                        "The selection rule has no name.\n\nPlease enter it's ",
                        "name as the first line of text.'",
                    )
                ),
            )
            return
        if not uvpqs:
            if not updater.value.where_error:
                if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                    parent=self.ui.get_toplevel(),
                    title="Insert Game Selection Rule",
                    message="".join(
                        (
                            "Confirm request to add game selection rule named:\n\n",
                            updater.value.get_name_text(),
                            "\n\nto database.\n\n",
                            "Note validation of the statement failed but no ",
                            "information is available.",
                        )
                    ),
                ):
                    tkinter.messagebox.showinfo(
                        parent=self.ui.get_toplevel(),
                        title="Insert Game Selection Rule",
                        message="".join(
                            (
                                "Add game selection rule to ",
                                "database abandonned.",
                            )
                        ),
                    )
                    return
            elif tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title="Insert Game Selection Rule",
                message="".join(
                    (
                        "Confirm request to add game selection rule named:\n\n",
                        updater.value.get_name_text(),
                        "\n\nto database.\n\n",
                        updater.value.where_error.get_error_report(
                            self.ui.base_games.get_data_source()
                        ),
                    )
                ),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Insert Game Selection Rule",
                    message="".join(
                        ("Add game selection rule to ", "database abandonned.")
                    ),
                )
                return
        elif tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title="Insert Game Selection Rule",
            message="".join(
                (
                    "Confirm request to add game selection rule named:\n\n",
                    updater.value.get_name_text(),
                    "\n\nto database.",
                )
            ),
        ):
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert Game Selection Rule",
                message="Add game selection rule to database abandonned.",
            )
            return
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        updater.key.recno = None  # 0
        editor.put()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title="Insert Game Selection Rule",
            message="".join(
                (
                    'Game selection rule "',
                    updater.value.get_name_text(),
                    '" added to database.',
                )
            ),
        )

    # on_game_change() is not called, but do nothing if it is.
    def on_game_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if self.sourceobject is not None:
            pass

    def get_list_games_events(self):
        """Return tuple of event bindings to list games for selection rule."""
        return (
            (EventSpec.display_list, self.process_and_set_selection_rule_list),
        )

    def set_database_navigation_close_item_bindings(self, switch=True):
        super().set_database_navigation_close_item_bindings(switch=switch)
        self.set_event_bindings_score(
            self.get_list_games_events(), switch=switch
        )

    def add_list_games_entry_to_popup(self, popup, index=tkinter.END):
        """Add option to list games for selection rule to popup."""
        self.set_popup_bindings(
            popup, self.get_list_games_events(), index=index
        )

    def generate_popup_navigation_maps(self):
        navigation_map = {k: v for k, v in self.get_navigation_events()}
        local_map = {}
        return navigation_map, local_map

    def create_primary_activity_popup(self):
        popup = super().create_primary_activity_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def on_selection_change(self, instance):
        """Prevent update from self if instance refers to same record.

        The list of games is updated by the 'List Games' popup menu option,
        but not as a consequence of updating the database.
        """
        if instance.newrecord:

            # Editing an existing record.
            value = instance.newrecord.value
            key = instance.newrecord.key

        else:

            # Inserting a new record.
            value = instance.value
            key = instance.key

        if self.sourceobject is not None:
            if (
                key == self.sourceobject.key
                and self.datasource.dbname == self.sourceobject.dbname
                and self.datasource.dbset == self.sourceobject.dbset
            ):
                self.blockchange = True

    def get_text_for_statusbar(self):
        """ """
        return "".join(
            (
                "Please wait while finding games for game selection rule ",
                self.query_statement.get_name_text(),
            )
        )

    def get_selection_text_for_statusbar(self):
        """ """
        return self.query_statement.get_name_text()

    # This method added so it can be used in _cycle_items which then becomes
    # identical to definitions in other classes.  There may be a case for
    # following what cqldisplay does in it's set_game_list method.
    def set_game_list(self):
        """Delegate to refresh_game_list.

        Enables 'after(refresh_game_list, ...)' in give_focus_to_widget()
        without affecting set_game_list() call in _cycle_items method.

        """
        self.refresh_game_list()

    def process_and_set_selection_rule_list(self, event=None):
        """Display games matching edited game selection rule."""
        if self.ui.base_games.datasource:
            self.query_statement.set_database(
                self.ui.base_games.datasource.dbhome
            )
        try:
            self.query_statement.process_query_statement(
                self.score.get("1.0", tkinter.END)
            )
        except WhereError as exc:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title=" ".join(("Game Selection Rule Error")),
                message=str(exc),
            )
            return "break"
        finally:
            self.query_statement.set_database()
        self.refresh_game_list()
        return "break"


class QueryDisplay(_QueryDisplay, DisplayText, ShowText, Query, DataNotify):

    """Display game selection rule from database and allow delete and insert.

    Method delete_item_database allows records to be deleted from a database.

    """

    # QueryDisplay has this method, but CQLDisplay does not, because the game
    # list area is shared with the main game list and the index lists.
    # Generating the game list on demand may be necessary at any time.
    def create_primary_activity_popup(self):
        popup = super().create_primary_activity_popup()
        self.add_list_games_entry_to_popup(popup, index="Close Item")
        return popup

    def delete_item_database(self, event=None):
        """Remove game selection rule from database."""
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete Game Selection Rule",
                message="".join(
                    (
                        "Cannot delete game selection rule:\n\n",
                        "No database open.",
                    )
                ),
            )
            return
        datasource = self.ui.base_selections.get_data_source()
        if datasource is None:
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title="Delete Game Selection Rule",
                message="".join(
                    (
                        "Cannot delete game selection rule:\n\n",
                        "Rule list hidden.",
                    )
                ),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete Game Selection Rule",
                message="".join(
                    (
                        "The game selection rule to delete has not ",
                        "been given.\n\nProbably because database ",
                        "has been closed and opened since this copy ",
                        "was displayed.",
                    )
                ),
            )
            return
        if self.blockchange:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete Game Selection Rule",
                message="\n".join(
                    (
                        "Cannot delete game selection rule.",
                        "Record has been amended since this copy displayed.",
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title="Delete Game Selection Rule",
            message="Confirm request to delete game selection rule.",
        ):
            return
        s = self.query_statement
        if s.where_error is not None:
            v = self.sourceobject.value
            if (
                s.get_name_text() != v.get_name_text()
                or s.where_error != v.where_error
                or s.get_query_statement_text() != v.get_query_statement_text()
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Delete Game Selection Rule",
                    message="\n".join(
                        (
                            "Cannot delete game selection rule.",
                            " ".join(
                                (
                                    "Rule on display is not same as",
                                    "rule from record.",
                                )
                            ),
                        )
                    ),
                )
                return
        editor = RecordDelete(self.sourceobject)
        editor.set_data_source(datasource, editor.on_data_change)
        editor.delete()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title="Delete Game Selection Rule",
            message="".join(
                (
                    'Game selection rule "',
                    self.sourceobject.value.get_name_text(),
                    '" deleted from database.',
                )
            ),
        )


class QueryDisplayInsert(
    _QueryDisplay, ListGamesText, InsertText, ShowText, QueryEdit, DataNotify
):

    """Display game selection rule from database allowing insert.

    QueryEdit provides the widget and _QueryDisplay the database interface.

    Listing games for ChessQL statements is different to selection rule
    statements because selection rules share the listing area with the Game
    and Index options to the Select menu.  Index opens up the 'Move to' and
    Filter options too.  A definite user action is always required to generate
    game lists for selection rules, in addition to navigating to (giving focus
    to) the selection rule.  The area where ChessQL game lists are shown is
    dedicated to ChessQL statements.

    """


class QueryDisplayEdit(EditText, QueryDisplayInsert):

    """Display game selection rule from database allowing edit and insert.

    Method update_item_database allows records on the database to be amended.

    """

    def update_item_database(self, event=None):
        """Modify existing game selection rule record."""
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="Cannot edit repertoire:\n\nNo database open.",
            )
            return
        datasource = self.ui.base_selections.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="Cannot edit game selection rule:\n\nRule list hidden.",
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="".join(
                    (
                        "The game selection rule to edit has not ",
                        "been given.\n\nProbably because database ",
                        "has been closed and opened since this copy ",
                        "was displayed.",
                    )
                ),
            )
            return
        if self.blockchange:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="\n".join(
                    (
                        "Cannot edit game selection rule.",
                        "Rule has been amended since this copy was displayed.",
                    )
                ),
            )
            return
        original = ChessDBrecordQuery()
        original.set_database(datasource.dbhome)
        original.load_record(
            (self.sourceobject.key.recno, self.sourceobject.srvalue)
        )

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        updater = ChessDBrecordQuery()
        updater.value.set_database(datasource.dbhome)
        updater.value.dbset = self.ui.base_games.datasource.dbset
        uvpqs = updater.value.process_query_statement(
            self.get_name_query_statement_text()
        )
        if not len(updater.value.get_name_text()):
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="".join(
                    (
                        "The selection rule has no name.\n\nPlease enter it's ",
                        "name as the first line of text.'",
                    )
                ),
            )
            return
        if not uvpqs:
            if not updater.value.where_error:
                if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                    parent=self.ui.get_toplevel(),
                    title="Edit Game Selection Rule",
                    message="".join(
                        (
                            "Confirm request to edit game selection rule ",
                            "named:\n\n",
                            updater.value.get_name_text(),
                            "\n\nto database.\n\n",
                            "Note validation of the statement failed but no ",
                            "information is available.",
                        )
                    ),
                ):
                    tkinter.messagebox.showinfo(
                        parent=self.ui.get_toplevel(),
                        title="Edit Game Selection Rule",
                        message="".join(
                            (
                                "Edit game selection rule to ",
                                "database abandonned.",
                            )
                        ),
                    )
                    return
            elif tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="".join(
                    (
                        "Confirm request to edit game selection rule named:\n\n",
                        updater.value.get_name_text(),
                        "\n\nto database.\n\n",
                        updater.value.where_error.get_error_report(
                            self.ui.base_games.get_data_source()
                        ),
                    )
                ),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Edit Game Selection Rule",
                    message="".join(
                        (
                            "Edit game selection rule to ",
                            "database abandonned.",
                        )
                    ),
                )
                return
        elif tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title="Edit Game Selection Rule",
            message="".join(
                (
                    "Confirm request to edit game selection rule named:\n\n",
                    updater.value.get_name_text(),
                    "\n\non database.",
                )
            ),
        ):
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit Game Selection Rule",
                message="Edit game selection rule to database abandonned.",
            )
            return
        editor = RecordEdit(updater, original)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        original.set_database(editor.get_data_source().dbhome)
        updater.key.recno = original.key.recno
        editor.edit()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title="Edit Game Selection Rule",
            message="".join(
                (
                    'Game selection rule "',
                    updater.value.get_name_text(),
                    '" amended on database.',
                )
            ),
        )
