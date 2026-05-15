# dptfastload_dir.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Import directory of PGN files with dpt.chessdptfastload module."""


if __name__ == "__main__":
    from .directory_widget_fastload import DirectoryWidget
    from .chessdptfastload import Database

    DirectoryWidget(Database, "dpt fastload")
