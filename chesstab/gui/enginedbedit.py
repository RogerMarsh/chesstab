# enginedbedit.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customise edit dialogue to edit or insert chess engine definition record.
"""
from urllib.parse import urlsplit, parse_qs

from solentware_misc.workarounds import dialogues

from solentware_grid.gui.dataedit import DataEdit

from .chessexception import ChessException
from .enginedisplay import DialogueEngineDisplay, DialogueEngineEdit


class ChessDBeditEngine(ChessException, DataEdit):
    """Dialog to edit or insert a chess engine definition on database.

    The chess engine definition is in it's own Toplevel widget.

    """

    def __init__(self, newobject, parent, oldobject, showinitial=True, ui=None):
        """Create dialogue to edit or insert chess engine definition."""
        if oldobject:
            title = ':  '.join((
                'Edit Engine Definition',
                oldobject.value._description_string))
        else:
            title = 'Insert Engine Definition'
            showinitial = False
        self.__title = title.split(':')[0]
        if showinitial:
            showinitial = DialogueEngineDisplay(master=parent, ui=ui)
            if ui is not None:
                ui.engines_in_toplevels.add(showinitial)
            showinitial.definition.extract_engine_definition(
                oldobject.get_srvalue())
            showinitial.set_engine_definition()
        newview = DialogueEngineEdit(master=parent, ui=ui)
        if ui is not None:
            ui.engines_in_toplevels.add(newview)
        newview.definition.extract_engine_definition(newobject.get_srvalue())
        newview.set_engine_definition()
        super(ChessDBeditEngine, self).__init__(
            newobject,
            parent,
            oldobject,
            newview,
            title,
            oldview=showinitial,
            )

        # Bind only to newview.score because it alone takes focus.
        self.bind_buttons_to_widget(newview.score)

        self.ui = ui
        
    def dialog_ok(self):
        """Update record and return update action response (True for updated).

        Check that database is open and is same one as update action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text='Cannot update because not connected to a database')
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        ed = self.newview.get_name_engine_definition_dict()
        if not ed:
            dialogues.showerror(
                title=self.__title,
                message=''.join(('No chess engine definition given.\n\n',
                                 'Name of chess engine definition must be ',
                                 'first line, and subsequent lines the ',
                                 'command to run the engine.',
                                 )))
            return False
        self.newobject.value.load(repr(ed))
        if not self.newobject.value.get_engine_command_text():
            dialogues.showerror(
                title=self.__title,
                message=''.join(('No chess engine definition given.\n\n',
                                 'Name of chess engine definition must be ',
                                 'first line, and subsequent lines the ',
                                 'command to run the engine.',
                                 )))
            return False
        url = urlsplit(self.newobject.value.get_engine_command_text())
        try:
            url.port
        except ValueError as exc:
            dialogues.showerror(
                title=self.__title,
                message=''.join(('Invalid chess engine definition given.\n\n',
                                 'The reported error for the port is:\n\n',
                                 str(exc),
                                 )))
            return False
        if url.hostname or url.port:
            if url.path and url.query:
                dialogues.showerror(
                    title=self.__title,
                    message=''.join(
                        ('Give engine as query with hostname or port.\n\n',
                         "Path is: '", url.path, "'.\n\n",
                         "Query is: '", url.query, "'.\n",
                         )))
                return False
            elif url.path:
                dialogues.showerror(
                    title=self.__title,
                    message=''.join(
                        ('Give engine as query with hostname or port.\n\n',
                         "Path is: '", url.path, "'.\n",
                         )))
                return False
            elif not url.query:
                dialogues.showerror(
                    title=self.__title,
                    message='Give engine as query with hostname or port.\n\n')
                return False
            else:
                try:
                    query = parse_qs(url.query, strict_parsing=True)
                except ValueError as exc:
                    dialogues.showerror(
                        title=self.__title,
                        message=''.join(
                            ("Problem specifying chess engine.  The reported ",
                             "error is:\n\n'",
                             str(exc), "'.\n",
                             )))
                    return False
                if len(query) > 1:
                    dialogues.showerror(
                        title=self.__title,
                        message=''.join(
                            ("Give engine as single 'key=value' or ",
                             "'value'.\n\n",
                             "Query is: '", url.query, "'.\n",
                             )))
                    return False
                elif len(query) == 1:
                    for k, v in query.items():
                        if k != 'name':
                            dialogues.showerror(
                                title=self.__title,
                                message=''.join(
                                    ("Give engine as single 'key=value' or ",
                                     "'value'.\n\n",
                                     "Query is: '", url.query, "'\n\nand use ",
                                     "'name' as key.\n",
                                     )))
                            return False
                        elif len(v) > 1:
                            dialogues.showerror(
                                title=self.__title,
                                message=''.join(
                                    ("Give engine as single 'key=value' or ",
                                     "'value'.\n\n",
                                     "Query is: '", url.query, "' with more ",
                                     "than one 'value'\n",
                                     )))
                            return False
        elif url.path and url.query:
            dialogues.showerror(
                title=self.__title,
                message=''.join(
                    ('Give engine as path without hostname or port.\n\n',
                     "Path is: '", url.path, "'.\n\n",
                     "Query is: '", url.query, "'.\n",
                     )))
            return False
        elif url.query:
            dialogues.showerror(
                title=self.__title,
                message=''.join(
                    ('Give engine as path without hostname or port.\n\n',
                     "Query is: '", url.query, "'.\n",
                     )))
            return False
        elif not url.path:
            dialogues.showerror(
                title=self.__title,
                message='Give engine as path without hostname or port.\n')
            return False
        return super(ChessDBeditEngine, self).dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after dialogue destruction."""
        self.ui.engines_in_toplevels.discard(self.oldview)
        self.ui.engines_in_toplevels.discard(self.newview)

        # base_engines is None when this happens on Quit.
        try:
            self.ui.base_engines.selection.clear()
        except AttributeError:
            if self.ui.base_engines is not None:
                raise
