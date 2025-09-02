# enginecommands.py
# Copyright 2025 Roger Marsh
# License: See LICENSE.TXT (BSD license)
"""Read and write file of available chess and pattern engines for a database.

Stockfish is a chess engine and CQL is a pattern engine.

The file name will be the name of the file containing the database with
'-engines' suffix.
"""

import os
from ast import literal_eval

_ENGINE_SUFFIX = "-engines"
_PATTERN_ENGINES = "pattern_engines"


class EngineCommands:
    """Provide read and write methods for file of engine commands.

    The file is a sibling of the database file named <database>-engines.

    opendatabase is an instance of an open chess database.
    """

    def __init__(self, database_file):
        """Create the engine command file accessor."""
        self._home_directory = os.path.dirname(database_file)
        self._database_file = database_file

    @property
    def filename(self):
        """Return pattern engine commands filename."""
        return os.path.join(
            self._home_directory,
            "".join(
                (
                    os.path.basename(self._database_file),
                    _ENGINE_SUFFIX,
                )
            ),
        )

    def read_pattern_engines(self):
        """Return the pattern engine commands."""
        with open(self.filename, encoding="utf8") as file:
            filedata = file.read()
        return literal_eval(filedata)[_PATTERN_ENGINES]

    def write_pattern_engines(self, entries):
        """Merge edited pattern engine commands into file."""
        try:
            with open(self.filename, encoding="utf8") as file:
                filedict = literal_eval(file.read())
        except FileNotFoundError:
            filedict = {}
        filedict[_PATTERN_ENGINES] = entries
        with open(self.filename, mode="w", encoding="utf8") as file:
            file.write(repr(filedict))
