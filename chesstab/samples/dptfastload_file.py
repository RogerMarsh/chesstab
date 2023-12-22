# dptfastload_file.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import PGN file with dpt.chessdptfastload module."""


if __name__ == "__main__":
    from .file_widget_fastload import FileWidget
    from .chessdptfastload import Database

    FileWidget(Database, "dpt fastload")
