# dptdu_file_713.py
# Copyright 2026 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with dpt.database_one_step_du module.

The import algorithm is from ChessTab-7.1.3 but applied to the modified
database structure.
"""

if __name__ == "__main__":
    from .file_widget_du_713 import FileWidget
    from ..dpt.database_one_step_du import Database

    FileWidget(Database, "dpt")
