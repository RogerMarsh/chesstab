# runchessndbmdu.py
# Copyright 2020 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess database update using custom deferred update for dbm.ndbm.

Run as a new process from the chess GUI.

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

    rundu.rundu("chesstab.gui.chessdu", "chesstab.ndbm.chessndbmdu")
