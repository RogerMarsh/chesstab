# cqldbshow.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Delete dialogue for Chess Query Language (ChessQL) statement record.
"""

from solentware_grid.gui.datashow import DataShow

from .chessexception import ChessException
from .cqldisplay import DialogueCQLDisplay


class ChessDBshowCQL(ChessException, DataShow):
    """Dialog to show a ChessQL statement from database.

    The ChessQL statement is in it's own Toplevel widget.

    """

    def __init__(self, parent, instance, ui=None):
        """Extend and create dialogue widget for deleting ChessQL statement."""
        oldview = DialogueCQLDisplay(master=parent, ui=ui)
        if ui is not None:
            ui.partials_in_toplevels.add(oldview)
        oldview.cql_statement.process_statement(instance.get_srvalue())
        oldview.set_cql_statement(instance.value)
        super().__init__(
            instance,
            parent,
            oldview,
            ':  '.join((
                'Show ChessQL statement',
                instance.value.get_name_text())),
            )
        self.bind_buttons_to_widget(oldview.score)
        self.ui = ui
       
    def dialog_ok(self):
        """Delete record and return delete action response (True for deleted).

        Check that database is open and is same one as deletion action was
        started.

        """
        if self.ui.database is None:
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super().dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.partials_in_toplevels.discard(self.oldview)
        self.ui.base_partials.selection.clear()
