# indexentry.py
# Copyright 2026 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Tk ttk.Entry widget with user state added.

The extended ttk.Entry widget is shared between many widgets which show
sorted lists of records.  The added state retains the context of each
list as focus is switched between lists.
"""

import tkinter


class IndexEntry(tkinter.ttk.Entry):
    """Customize ttk.Entry widget.

    Initially the context is the string to display in the Entry widget
    for the associated list of records.
    """

    def __init__(self, *args, **kwargs):
        """Extend with a context dict."""
        super().__init__(*args, **kwargs)
        for name in ("index_context", "apply_index_context"):
            if hasattr(super(), name):
                raise RuntimeError(
                    "tkinter.ttk.Entry superclass defines " + name
                )
        self.index_context = {}
        self.index_context_key = None

    def apply_index_context(self, key):
        """Update widget with context for key.

        Expected to be done when the associated list gets focus.

        """
        if self.index_context_key is not None:
            self.index_context[self.index_context_key] = self.get()
        self.delete("0", tkinter.END)
        self.insert(tkinter.END, self.index_context.get(key, ""))
        self.index_context_key = key
