# engine.py
# Copyright 2016 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess engine program definition.
"""
import os.path

from .constants import  NAME_DELIMITER

_error = 1


class Engine(object):
    """Chess engine program definition.

    Maintain command line details for running a chess engine.

    The definition has a name: typically the chess engine name and version.

    The definition has a command line used to run the chess engine.
    
    """

    def __init__(self):
        """"""
        super().__init__()
        self._description_string = ''
        self._run_engine_string = ''

    def update_engine_definition(self, attributes):
        """Update existing self.__dict__ keys from dict attributes"""
        for a in self.__dict__.keys():
            if a in attributes:
                self.__dict__[a] = attributes[a]

    def extract_engine_definition(self, text):
        """Return True if definition contains a command line and optional name.

        The command line starts with a path.  The last element of the path is
        used as the name if a separate name is not present.

        The definition contains at most two lines: the first line may be the
        optional name.

        """
        if isinstance(text, dict):
            self._description_string = text['_description_string']
            self._run_engine_string = text['_run_engine_string']
            return True
        definition = [t.strip() for t in text.split(NAME_DELIMITER)]
        if not len(definition[0]) or not len(definition[-1]):
            return False
        if len(definition) > 2:
            return False
        self._run_engine_string = definition[-1]
        if len(definition) == 1:
            self._description_string = os.path.splitext(os.path.basename(
                definition[0].split()[0]))[0]
        else:
            self._description_string = definition[0]
        return True

    def get_name_text(self):
        """Return name text."""
        return self._description_string

    def get_name_engine_command_text(self):
        """Return name and command text."""
        return '\n'.join(
            (self._description_string,
             self._run_engine_string,
             ))

    def get_engine_command_text(self):
        """Return command line to run engine."""
        return self._run_engine_string

    def is_run_engine_command(self):
        """Return True if run engine command line starts with existing file."""
        if not self._run_engine_string:
            return False
        return os.path.isfile(self._run_engine_string)
