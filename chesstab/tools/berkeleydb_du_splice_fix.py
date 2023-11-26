# berkeleydb_du_splice_fix.py
# Copyright 2023 Roger Marsh
# Licence: See LICENSE.txt (BSD licence)

"""Delete index references kept, not replaced, in deferred update runs."""
import solentware_base.tools.berkeleydb_du_splice_fix

from ..core import filespec


def berkeleydb_du_splice_fix(home=None):
    """Delete index references which seem not deleted in deferred update.

    home is name of a directory or file containing instances of the
    database defined in specification.  It can be specified as the last
    argument on the command line.  Default is current working directory.

    """
    solentware_base.tools.berkeleydb_du_splice_fix.berkeleydb_du_splice_fix(
        home=home, specification=filespec.FileSpec()
    )


if __name__ == "__main__":
    berkeleydb_du_splice_fix()
