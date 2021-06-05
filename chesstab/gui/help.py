# help.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to create Help widgets for ChessTab.
"""

import tkinter

import solentware_misc.gui.textreadonly
from solentware_misc.gui.help import help_widget

from .. import help as help_


def help_about(master):
    """Display About document"""

    help_widget(master, help_.ABOUT, help_)


def help_file_size(master):
    """Display File Size document"""

    help_widget(master, help_.FILESIZE, help_)


def help_guide(master):
    """Display About document"""

    help_widget(master, help_.GUIDE, help_)


def help_selection(master):
    """Display Selection Rules document"""

    help_widget(master, help_.SELECTION, help_)


def help_notes(master):
    """Display Notes document"""

    help_widget(master, help_.NOTES, help_)


if __name__ == "__main__":
    # Display all help documents without running ChessTab application

    root = tkinter.Tk()
    help_about(root)
    help_file_size(root)
    help_guide(root)
    help_notes(root)
    help_selection(root)
    root.mainloop()
