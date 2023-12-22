# dptdu_dir.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with dpt.database_du to database."""


if __name__ == "__main__":
    from .directory_widget import DirectoryWidget
    from ..dpt.database_du import database_du

    DirectoryWidget(database_du, "dpt")
