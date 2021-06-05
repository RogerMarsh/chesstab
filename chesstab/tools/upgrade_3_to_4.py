# upgrade_3_to_4.py
# Copyright 2019 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Upgrade a ChessTab database from version 3 to version 4.

Table names are changed and extra tables introduced in segment support.

"""


if __name__ == "__main__":

    import os

    from solentware_base.tools import ui_base_3_to_4

    from ..core.filespec import FileSpec

    ui_base_3_to_4.UIBase_3_to_4(FileSpec()).root.mainloop()
