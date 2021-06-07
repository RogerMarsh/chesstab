# cqldisplay.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widgets to display and edit Chess Query Language (ChessQL) statements.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

These four classes display ChessQL statements in the main window: they are used
in the cqlgrid module.

The _CQLDisplay class provides attributes and behaviour shared by the
CQLDisplay, CQLDisplayInsert, and CQLDisplayEdit, classes.  It also provides
properties to support implementation of behaviour shared with the Game*,
Repertoire*, and Query*, classes.

The CQLDisplay, CQLDisplayInsert, and CQLDisplayEdit, classes are subclasses
of the relevant ShowText, InsertText, EditText, DisplayText, and ListGamesText,
classes from the displaytext module; to implement behaviour shared with all
Text widgets in the main display (that includes widgets displaying PGN text).

"""

import tkinter
import tkinter.messagebox

from solentware_grid.gui.dataedit import RecordEdit
from solentware_grid.gui.datadelete import RecordDelete
from solentware_grid.core.dataclient import DataNotify

from solentware_misc.gui.exceptionhandler import ExceptionHandler

from .cql import CQL
from .cqledit import CQLEdit
from ..core.chessrecord import ChessDBrecordPartial
from ..core.cqlstatement import CQLStatement
from .eventspec import EventSpec
from .display import Display
from .displaytext import (
    ShowText,
    InsertText,
    EditText,
    DisplayText,
    ListGamesText,
)


class _CQLDisplay(ExceptionHandler, Display):

    """Extend and link ChessQL statement to database.

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
        EventSpec.partialdisplay_to_previous_partial,
        EventSpec.partialdisplay_to_next_partial,
        EventSpec.navigate_to_partial_game_grid,
        EventSpec.navigate_to_selection_rule_grid,
        EventSpec.navigate_to_active_selection_rule,
        EventSpec.tab_traverse_backward,
        EventSpec.tab_traverse_forward,
    )

    def __init__(self, sourceobject=None, **ka):
        """Extend and link ChessQL statement to database."""
        super().__init__(**ka)
        self.blockchange = False
        if self.ui.base_partials.datasource:
            self.set_data_source(self.ui.base_partials.get_data_source())
        self.sourceobject = sourceobject
        self.insertonly = sourceobject is None
        self.recalculate_after_edit = sourceobject

    @property
    def ui_displayed_items(self):
        return self.ui.partial_items

    @property
    def ui_configure_item_list_grid(self):
        return self.ui.configure_partial_grid

    @property
    def ui_set_item_name(self):
        return self.ui._set_partial_name

    @property
    def ui_set_find_item_games(self):
        return self.ui._set_find_partial_name_games

    def get_navigation_events(self):
        """Return event description tuple for navigation from selection rule
        statement."""
        return (
            (EventSpec.navigate_to_partial_grid, self.set_focus_partial_grid),
            (EventSpec.partialdisplay_to_previous_partial, self.prior_item),
            (EventSpec.partialdisplay_to_next_partial, self.next_item),
            (
                EventSpec.navigate_to_partial_game_grid,
                self.set_focus_partial_game_grid,
            ),
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
            (
                EventSpec.navigate_to_position_grid,
                self.set_focus_position_grid,
            ),
            (EventSpec.navigate_to_active_game, self.set_focus_gamepanel_item),
            (
                EventSpec.navigate_to_selection_rule_grid,
                self.set_focus_selection_rule_grid,
            ),
            (
                EventSpec.navigate_to_active_selection_rule,
                self.set_focus_selectionpanel_item,
            ),
            (EventSpec.navigate_to_game_grid, self.set_focus_game_grid),
            (EventSpec.export_from_partialdisplay, self.export_partial),
            (EventSpec.tab_traverse_forward, self.traverse_forward),
            (EventSpec.tab_traverse_backward, self.traverse_backward),
            (EventSpec.tab_traverse_round, self.traverse_round),
        )

    def delete_item_view(self, event=None):
        """Remove ChessQL statement item from screen."""
        self.ui.delete_position_view(self)

    def insert_item_database(self, event=None):
        """Add ChessQL statement to database."""
        if self.ui.partial_items.active_item is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert ChessQL Statement",
                message="No active ChessQL statement to insert into database.",
            )
            return

        # This should see if ChessQL statement with same name already exists,
        # after checking for database open, and offer option to insert anyway.
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert ChessQL Statement",
                message="Cannot add ChessQL statement:\n\nNo database open.",
            )
            return

        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Insert ChessQL Statement",
                message="".join(
                    (
                        "Cannot add ChessQL statement:\n\n",
                        "Partial position list hidden.",
                    )
                ),
            )
            return
        updater = ChessDBrecordPartial()
        updater.value.process_statement(self.get_name_cql_statement_text())
        title = "Insert ChessQL Statement"
        tname = title.replace("Insert ", "").replace("S", "s")
        if not len(updater.value.get_name_text()):
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "The '",
                        tname,
                        " has no name.\n\nPlease enter it's ",
                        "name as the first line of text.'",
                    )
                ),
            )
            return
        message = [
            "".join(
                (
                    "Confirm request to add ",
                    tname,
                    " named:\n\n",
                    updater.value.get_name_text(),
                    "\n\nto database.\n\n",
                )
            )
        ]
        if not updater.value.cql_error:
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(message),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title=title,
                    message=tname.join(("Add ", " to database abandonned.")),
                )
                return
        else:
            message.append(updater.value.cql_error.get_error_report())
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(message),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title=title,
                    message=tname.join(("Add ", " to database abandonned.")),
                )
                return
        editor = RecordEdit(updater, None)
        editor.set_data_source(datasource, editor.on_data_change)
        updater.set_database(editor.get_data_source().dbhome)
        updater.key.recno = None  # 0
        editor.put()
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title=title,
            message="".join(
                (
                    tname,
                    ' "',
                    updater.value.get_name_text(),
                    '" added to database.',
                )
            ),
        )

    def on_game_change(self, instance):
        """Recalculate list of games for ChessQL statement after game update.

        instance is ignored: it is assumed a recalculation is needed.

        """
        if self.sourceobject is not None:
            self._get_cql_statement_games_to_grid(
                self.cql_statement
            )  # .match)

    def generate_popup_navigation_maps(self):
        navigation_map = {k: v for k, v in self.get_navigation_events()}
        local_map = {}
        return navigation_map, local_map

    def create_primary_activity_popup(self):
        popup = super().create_primary_activity_popup()
        self.add_close_item_entry_to_popup(popup)
        return popup

    def on_partial_change(self, instance):
        """Prevent update from self if instance refers to same record."""
        if instance.newrecord:

            # Editing an existing record.
            value = instance.newrecord.value
            key = instance.newrecord.key

        else:

            # Inserting a new record or deleting an existing record.
            value = instance.value
            key = instance.key

        if self.sourceobject is not None:
            if (
                key == self.sourceobject.key
                and self.datasource.dbname == self.sourceobject.dbname
                and self.datasource.dbset == self.sourceobject.dbset
            ):
                self.blockchange = True

        pds = self.ui.partial_games.datasource
        if self.sourceobject is not None and key != self.sourceobject.key:
            pass
        elif self is not self.ui.partial_items.active_item:
            pass
        elif instance.newrecord is None:
            pds.forget_cql_statement_games(instance)
        elif instance.newrecord is False:
            try:
                pds.update_cql_statement_games(instance)
            except AttributeError as exc:
                if str(exc) == "'NoneType' object has no attribute 'answer'":
                    msg = "".join(
                        (
                            "Unable to add ChessQL statement to database, ",
                            "probably because an 'empty square' is in the query ",
                            "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                            str(exc),
                        )
                    )
                else:
                    msg = "".join(
                        (
                            "Unable to add ChessQL statement to database:\n\n",
                            "The reported error is:\n\n",
                            str(exc),
                        )
                    )
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Insert ChessQL Statement",
                    message=msg,
                )
                return
            except Exception as exc:
                msg = "".join(
                    (
                        "Unable to add ChessQL statement to database:\n\n",
                        "The reported error is:\n\n",
                        str(exc),
                    )
                )
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Insert ChessQL Statement",
                    message=msg,
                )
                return
        else:

            # Unfortunatly the existing list will have to be recalculated if
            # one of the caught exceptions occurs.
            pds.forget_cql_statement_games(instance)
            try:
                pds.update_cql_statement_games(instance.newrecord)
            except AttributeError as exc:
                if str(exc) == "'NoneType' object has no attribute 'answer'":
                    msg = "".join(
                        (
                            "Unable to edit ChessQL statement on database, ",
                            "probably because an 'empty square' is in the query ",
                            "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                            str(exc),
                        )
                    )
                else:
                    msg = "".join(
                        (
                            "Unable to edit ChessQL statement on database:\n\n",
                            "The reported error is:\n\n",
                            str(exc),
                        )
                    )
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Insert ChessQL Statement",
                    message=msg,
                )
                return
            except Exception as exc:
                msg = "".join(
                    (
                        "Unable to edit ChessQL statement on database:\n\n",
                        "The reported error is:\n\n",
                        str(exc),
                    )
                )
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Insert ChessQL Statement",
                    message=msg,
                )
                return

        if self is self.ui.partial_items.active_item:
            if self.sourceobject is not None and key == self.sourceobject.key:

                # Maybe should create a new CQLStatement instance.
                # self.cql_statement is a CQLStatement instance.
                # value is a ChessDBvaluePartial instance.
                self.cql_statement = value
                self.set_and_tag_item_text()
                self._get_cql_statement_games_to_grid(value)

    def get_text_for_statusbar(self):
        """ """
        return "".join(
            (
                "Please wait while finding games for ChessQL statement ",
                self.cql_statement.get_name_text(),
            )
        )

    def get_selection_text_for_statusbar(self):
        """ """
        return self.cql_statement.get_name_text()

    def set_game_list(self):
        """Delegate to refresh_game_list via 'after(...) call."""
        self.panel.after(
            0, func=self.try_command(self.ui._set_partial_name, self.panel)
        )
        self.panel.after(
            0, func=self.try_command(self.refresh_game_list, self.panel)
        )

    def _get_cql_statement_games_to_grid(self, statement):  # match):
        """Populate Partial Position games grid with games selected by match.

        "match" is named for the CQL version-1.0 keyword which started a CQL
        statement.  Usage is "(match ..." which become "cql(" no later than
        version 5.0 of CQL.  Thus "cql" is now a better name for the argument.

        """
        p = self.ui.partial_games
        if len(p.keys):
            key = p.keys[0]
        else:
            key = None
        p.close_client_cursor()
        try:
            p.datasource.get_cql_statement_games(statement, self.sourceobject)
        except AttributeError as exc:
            if str(exc) == "'NoneType' object has no attribute 'answer'":
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement, ",
                        "probably because an 'empty square' is in the query ",
                        "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                        str(exc),
                    )
                )
            else:
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement:\n\n",
                        "The reported error is:\n\n",
                        str(exc),
                    )
                )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message=msg,
            )
        except Exception as exc:
            msg = "".join(
                (
                    "Unable to list games for ChessQL statement:\n\n",
                    "The reported error is:\n\n",
                    str(exc),
                )
            )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message=msg,
            )
        p.fill_view(currentkey=key, exclude=False)
        if p.datasource.not_implemented:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="ChessQL Statement Not Implemented",
                message="".join(
                    (
                        "These filters are not implemented and ",
                        "are ignored:\n\n",
                        "\n".join(sorted(grid.datasource.not_implemented)),
                    )
                ),
            )


class CQLDisplay(_CQLDisplay, DisplayText, ShowText, CQL, DataNotify):

    """Display ChessQL statement from database and allow delete and insert.

    Method delete_item_database allows records to be deleted from a database.

    """

    def delete_item_database(self, event=None):
        """Remove ChessQL statement from database."""
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="".join(
                    (
                        "Cannot delete ChessQL statement:\n\n",
                        "No database open.",
                    )
                ),
            )
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="".join(
                    (
                        "Cannot delete ChessQL statement:\n\n",
                        "ChessQL statement list hidden.",
                    )
                ),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Delete ChessQL Statement",
                message="".join(
                    (
                        "The ChessQL statement to delete has not ",
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
                title="Delete ChessQL Statement",
                message="\n".join(
                    (
                        "Cannot delete ChessQL statement.",
                        "Record has been amended since this copy displayed.",
                    )
                ),
            )
            return
        if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
            parent=self.ui.get_toplevel(),
            title="Delete ChessQL Statement",
            message="Confirm request to delete ChessQL statement.",
        ):
            return
        s = self.cql_statement

        # Consider changing this since the call no longer ever returns None.
        if s.is_statement() is not None:

            v = self.sourceobject.value
            if (
                s.get_name_text() != v.get_name_text()
                or s.is_statement() != v.is_statement()
                or s.get_statement_text() != v.get_statement_text()
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="Delete ChessQL Statement",
                    message="\n".join(
                        (
                            "Cannot delete ChessQL statement.",
                            " ".join(
                                (
                                    "ChessQL statement on display is not same as",
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
            title="Delete ChessQL Statement",
            message="".join(
                (
                    'ChessQL statement "',
                    self.sourceobject.value.get_name_text(),
                    '" deleted from database.',
                )
            ),
        )


class CQLDisplayInsert(
    _CQLDisplay, ListGamesText, InsertText, ShowText, CQLEdit, DataNotify
):

    """Display ChessQL statement from database allowing insert.

    CQLEdit provides the widget and _CQLDisplay the database interface.

    Listing games for ChessQL statements is different to selection rule
    statements because selection rules share the listing area with the Game
    and Index options to the Select menu.  Index opens up the 'Move to' and
    Filter options too.  A definite user action is always required to generate
    game lists for selection rules, in addition to navigating to (giving focus
    to) the selection rule.  The area where ChessQL game lists are shown is
    dedicated to ChessQL statements.

    """

    def get_list_games_events(self):
        """Return tuple of event bindings to list games for ChessQL rule."""
        return (
            (EventSpec.display_list, self.process_and_set_cql_statement_list),
        )

    def add_list_games_entry_to_popup(self, popup):
        """Add option to list games for selection rule to popup."""
        self.set_popup_bindings(popup, self.get_list_games_events())

    def set_database_navigation_close_item_bindings(self, switch=True):
        super().set_database_navigation_close_item_bindings(switch=switch)
        self.set_event_bindings_score(
            self.get_list_games_events(), switch=switch
        )

    def process_and_set_cql_statement_list(self, event=None):
        """Display games with position matching edited ChessQL statement."""
        s = CQLStatement()
        # Not sure this is needed or wanted.
        # s.dbset = self.ui.base_games.datasource.dbset
        s.process_statement(self.get_name_cql_statement_text())
        self.cql_statement = s
        try:
            self.refresh_game_list()
        except AttributeError as exc:
            if str(exc) == "'NoneType' object has no attribute 'answer'":
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement, probably ",
                        "because an 'empty square' is in the query ",
                        "(eg '.a2-3'):\n\nThe reported  error is:\n\n",
                        str(exc),
                    )
                )
            else:
                msg = "".join(
                    (
                        "Unable to list games for ChessQL statement:\n\n",
                        "The reported error is:\n\n",
                        str(exc),
                    )
                )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="ChessQL Statement",
                message=msg,
            )
        except Exception as exc:
            msg = "".join(
                (
                    "Unable to list games for ChessQL statement:\n\n",
                    "The reported error is:\n\n",
                    str(exc),
                )
            )
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="ChessQL Statement",
                message=msg,
            )
        return "break"


class CQLDisplayEdit(EditText, CQLDisplayInsert):

    """Display ChessQL statement from database allowing edit and insert.

    Method update_item_database allows records on the database to be amended.

    """

    def update_item_database(self, event=None):
        """Modify existing ChessQL statement record."""
        if self.ui.database is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit ChessQL Statement",
                message="Cannot edit ChessQL statement:\n\nNo database open.",
            )
            return
        datasource = self.ui.base_partials.get_data_source()
        if datasource is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit ChessQL Statement",
                message="".join(
                    (
                        "Cannot edit ChessQL statement:\n\n",
                        "Partial position list hidden.",
                    )
                ),
            )
            return
        if self.sourceobject is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="Edit ChessQL Statement",
                message="".join(
                    (
                        "The ChessQL statement to edit has not ",
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
                title="Edit ChessQL Statement",
                message="\n".join(
                    (
                        "Cannot edit ChessQL statement.",
                        "It has been amended since this copy was displayed.",
                    )
                ),
            )
            return
        original = ChessDBrecordPartial()
        original.load_record(
            (self.sourceobject.key.recno, self.sourceobject.srvalue)
        )

        # is it better to use DataClient directly?
        # Then original would not be used. Instead DataSource.new_row
        # gets record keyed by sourceobject and update is used to edit this.
        updater = ChessDBrecordPartial()
        updater.value.process_statement(self.get_name_cql_statement_text())
        title = "Edit ChessQL Statement"
        tname = title.replace("Edit ", "").replace("S", "s")
        if not len(updater.value.get_name_text()):
            tkinter.messagebox.showerror(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(
                    (
                        "The '",
                        tname,
                        " has no name.\n\nPlease enter it's ",
                        "name as the first line of text.'",
                    )
                ),
            )
            return
        message = [
            "".join(
                (
                    "Confirm request to edit ",
                    tname,
                    " named:\n\n",
                    updater.value.get_name_text(),
                    "\n\non database.\n\n",
                )
            )
        ]
        if not updater.value.cql_error:
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(message),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title=title,
                    message=tname.join(("Edit ", " on database abandonned.")),
                )
                return
        else:
            message.append(updater.value.cql_error.get_error_report())
            if tkinter.messagebox.YES != tkinter.messagebox.askquestion(
                parent=self.ui.get_toplevel(),
                title=title,
                message="".join(message),
            ):
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title=title,
                    message=tname.join(("Edit ", " on database abandonned.")),
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
            title=title,
            message="".join(
                (
                    tname,
                    ' "',
                    updater.value.get_name_text(),
                    '" amended on database.',
                )
            ),
        )
