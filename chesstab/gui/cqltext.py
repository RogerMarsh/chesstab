# cqltext.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to display a Chess Query Language (ChessQL) statement.

ChessQL statements obey the syntax published for CQL version 6.0.1 (by Gady
Costeff).

"""
# The previous CQL syntax partially supported was version 5.1 found at:
# https://web.archive.org/web/20140130143815/http://www.rbnn.com/cql/
# (www.rbnn.com is no longer availabable).

import tkinter
import tkinter.messagebox

from ..core.cqlstatement import CQLStatement
from .blanktext import NonTagBind, BlankText
from .sharedtext import SharedText, SharedTextEngineText, SharedTextScore


class CQLTextListGamesError(Exception):
    """Exception class for display of lists of games."""


class CQLText(SharedText, SharedTextEngineText, SharedTextScore, BlankText):
    """ChessQL statement widget.

    panel is used as the panel argument for the super().__init__ call.

    ui is the user interface manager for an instance of CQLText, usually an
    instance of ChessUI.

    items_manager is used as the items_manager argument for the
    super().__init__ call.

    itemgrid is the ui reference to the DataGrid from which the record was
    selected.

    Subclasses are responsible for providing a geometry manager.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.
    """

    def __init__(
        self,
        panel,
        ui=None,
        items_manager=None,
        itemgrid=None,
        **ka,
    ):
        """Create widgets to display ChessQL statement."""
        super().__init__(panel, items_manager=items_manager, **ka)
        self.ui = ui
        self.itemgrid = itemgrid
        self.score.tag_configure(self.ERROR_TAG, background=self.ERROR_COLOR)
        self.score.tag_configure(self.CURSOR_TAG, background=self.CURSOR_COLOR)

        # Selection rule parser instance to process text.
        self.cql_statement = CQLStatement()
        self.cql_statement.dbset = ui.base_games.datasource.dbset
        self.cql_statement.set_database(database=ui.database)

    def set_and_tag_item_text(self, reset_undo=False):
        """Display the ChessQL statement as text.

        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a ChessQL statement for editing so that repeated
        Ctrl-Z in text editing mode recovers the original ChessQL statement.

        """
        if not self._is_text_editable:
            self.score.configure(state=tkinter.NORMAL)
        self._map_cql_statement()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self._bind_for_primary_activity()
        if not self._is_text_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()

    def set_statusbar_text(self):
        """Set status bar to display ChessQL statement name."""
        self.ui.statusbar.set_status_text(self.cql_statement.get_name_text())

    def get_name_cql_statement_text(self):
        """Return text from CQL statement Text widget."""
        return self.get_newline_delimited_title_and_text()

    def _map_cql_statement(self):
        """Convert tokens to text and show in CQL statement Text widget."""
        # No mapping of tokens to text in widget (yet).
        self._populate_query_widget(
            self.cql_statement.get_name_text(),
            self.cql_statement.get_statement_text_display(),
        )

    def _get_partial_key_cql_statement(self):
        """Return ChessQL statement for use as partial key."""
        if self.cql_statement.is_statement():
            # Things must be arranged so a tuple, not a list, can be returned.
            # return tuple(self.cql_statement.position)
            return self.cql_statement.get_statement_text()  # Maybe!

        return False

    def refresh_game_list(self, key_recno=None):
        """Display games with position matching selected ChessQL statement."""
        grid = self.itemgrid
        # Should this complain also if the grid is not visible?
        # Which can be fixed by the 'Position | Show' menu option.
        if grid is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="ChessQL Statement",
                message="No grid to display list of games",
            )
            return
        if grid.get_database() is None:
            tkinter.messagebox.showinfo(
                parent=self.ui.get_toplevel(),
                title="ChessQL Statement",
                message="No database open from which to select games",
            )
            return
        cqls = self.cql_statement
        if cqls.cql_error:
            grid.datasource.get_cql_statement_games(None, None)
        else:
            try:
                grid.datasource.get_cql_statement_games(cqls, key_recno)
            except AttributeError as exc:
                if str(exc) == "'NoneType' object has no attribute 'answer'":
                    msg = "".join(
                        (
                            "Unable to list games for ChessQL statement, ",
                            "probably because an 'empty square' is in the ",
                            "query (eg '.a2-3'):\n\n",
                            "The reported  error is:\n\n",
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
                grid.datasource.get_cql_statement_games(None, None)
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="ChessQL Statement",
                    message=msg,
                )
        grid.partial = self._get_partial_key_cql_statement()
        # grid.rows = 1
        grid.load_new_index()

        # Get rid of the 'Please wait ...' status text.
        self.ui.statusbar.set_status_text()

        if cqls.cql_error:
            if self.ui.is_database_access_inhibited():
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="ChessQL Statement Error",
                    message=cqls.cql_error.get_error_report(),
                )
            else:
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="ChessQL Statement Error",
                    message=cqls.cql_error.add_error_report_to_message(
                        ("An empty game list will be displayed.")
                    ),
                )

    def _tag_match_text(self, match_, tag):
        """Add match_.text in self.score to tag.

        The tag will have an associated colour, often pointing to errors.

        """
        if match_ is None:
            return
        # The span for match is converted to Tk 'line.column' form, taking
        # account of lines before those tagged TEXT_DATA.
        # The first line of query, line 4, starts with an elided character.
        tag_ranges = self.score.tag_ranges(self.TEXT_DATA)
        if not tag_ranges or len(tag_ranges) > 2:
            return
        start, end = match_.span()
        nl_count = (
            match_.string[:end].count("\n")
            + int(self.score.index(tag_ranges[0]).split(".", maxsplit=1)[0])
            - 1
        )
        nl_pos = match_.string[:end].rfind("\n")
        tag_start = ".".join(
            (str(nl_count), str(start - nl_pos - (0 if nl_count == 4 else 1)))
        )
        tag_end = self.score.index(tag_start) + "+" + str(end - start) + "c"

        self.score.tag_add(tag, tag_start, tag_end)

    def _report_statement_error(self, statement, error):
        """Display dialogue reporting error in statement."""
        msg = "".join(
            (
                "Unable to process ChessQL statement: ",
                "the reported problem is:\n\n",
                str(error),
            )
        )
        match_ = statement.query_container.cursor.match_
        if match_ is None:
            msg += "\n\nPerhaps 'cql()' should be on new line after title"
        self._tag_match_text(match_, self.CURSOR_TAG)
        self._tag_match_text(
            statement.query_container.current_token, self.ERROR_TAG
        )
        tkinter.messagebox.showinfo(
            parent=self.ui.get_toplevel(),
            title="ChessQL Statement",
            message=msg,
        )

    def _clear_statement_tags(self):
        """Cleat tags highlighting error in statement."""
        self.score.tag_remove(self.ERROR_TAG, "1.0", tkinter.END)
        self.score.tag_remove(self.CURSOR_TAG, "1.0", tkinter.END)
