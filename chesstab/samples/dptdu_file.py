# dptdu_file.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with dpt.database_du module."""


if __name__ == "__main__":
    from .file_widget import FileWidget
    from ..dpt.database_du import Database

    FileWidget(Database, "dpt")
