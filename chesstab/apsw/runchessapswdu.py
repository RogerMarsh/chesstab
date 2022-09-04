# runchessapswdu.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for sqlite3.

Run as a new process from the chess GUI.

The customisation is null, and will remain so unless the journals enabling
transaction rollback can be disabled (well then it will not be a customisation
but use of an sqlite3 feature).  DPT deferred update requires that it's
rollback journals are disabled.

"""

if __name__ == "__main__":

    import os
    import sys

    # When run in a py2exe generated executable the module will not have
    # the __file__ attribute.
    # But the siblings can be assumed to be in the right place.
    # (Comment above at least 10 years old in 2022.)
    # sys.path[-1] is assumed to be '/usr/.../site-packages'.
    if "__file__" in dir():
        packageroot = os.path.dirname(os.path.dirname(__file__))
        if sys.path[-1].replace("\\\\", "\\") != packageroot:
            sys.path.insert(0, os.path.dirname(packageroot))
        assert os.path.basename(packageroot) == "chesstab"

    from chesstab.shared import rundu

    rundu.rundu("chesstab.gui.chessdu", "chesstab.apsw.chessapswdu")
