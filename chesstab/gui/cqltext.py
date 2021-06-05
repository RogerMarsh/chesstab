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
from .eventspec import EventSpec
from .blanktext import NonTagBind, BlankText
from .sharedtext import SharedText, SharedTextEngineText, SharedTextScore


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
        self, panel, ui=None, items_manager=None, itemgrid=None, **ka
    ):
        """Create widgets to display ChessQL statement."""
        super().__init__(panel, items_manager=items_manager, **ka)
        self.ui = ui
        self.itemgrid = itemgrid

        # The popup menus for the ChessQL statement.
        self.primary_activity_popup = None

        # Selection rule parser instance to process text.
        self.cql_statement = CQLStatement()
        # Not sure this is needed or wanted.
        # self.cql_statement.dbset = ui.base_games.datasource.dbset

    def set_and_tag_item_text(self, reset_undo=False):
        """Display the ChessQL statement as text.

        reset_undo causes the undo redo stack to be cleared if True.  Set True
        on first display of a ChessQL statement for editing so that repeated
        Ctrl-Z in text editing mode recovers the original ChessQL statement.

        """
        if not self._is_text_editable:
            self.score.configure(state=tkinter.NORMAL)
        self.score.delete("1.0", tkinter.END)
        self.map_cql_statement()
        if self._most_recent_bindings != NonTagBind.NO_EDITABLE_TAGS:
            self.bind_for_primary_activity()
        if not self._is_text_editable:
            self.score.configure(state=tkinter.DISABLED)
        if reset_undo:
            self.score.edit_reset()

    def set_statusbar_text(self):
        """Set status bar to display ChessQL statement name."""
        self.ui.statusbar.set_status_text(self.cql_statement.get_name_text())

    def get_name_cql_statement_text(self):
        """ """
        text = self.score.get("1.0", tkinter.END).strip()
        return text

    def map_cql_statement(self):
        """ """
        # No mapping of tokens to text in widget (yet).
        self.score.insert(
            tkinter.INSERT, self.cql_statement.get_name_statement_text()
        )

    def get_partial_key_cql_statement(self):
        """Return ChessQL statement for use as partial key."""
        if self.cql_statement.is_statement():

            # Things must be arranged so a tuple, not a list, can be returned.
            # return tuple(self.cql_statement.position)
            return self.cql_statement.get_statement_text()  # Maybe!

        else:
            return False

    def refresh_game_list(self):
        """Display games with position matching selected ChessQL statement."""
        grid = self.itemgrid
        if grid is None:
            return
        if grid.get_database() is None:
            return
        cqls = self.cql_statement
        if cqls.cql_error:
            grid.datasource.get_cql_statement_games(None, None)
        else:
            try:
                if self._is_text_editable:
                    grid.datasource.get_cql_statement_games(cqls, None)
                else:
                    grid.datasource.get_cql_statement_games(
                        cqls, self.recalculate_after_edit
                    )
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
                grid.datasource.get_cql_statement_games(None, None)
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
                grid.datasource.get_cql_statement_games(None, None)
                tkinter.messagebox.showinfo(
                    parent=self.ui.get_toplevel(),
                    title="ChessQL Statement",
                    message=msg,
                )
        grid.partial = self.get_partial_key_cql_statement()
        # grid.rows = 1
        grid.load_new_index()

        # Get rid of the 'Please wait ...' status text.
        self.ui.statusbar.set_status_text()

        if cqls.cql_error:
            if self.ui.database is None:
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
        elif grid.datasource.not_implemented:
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
