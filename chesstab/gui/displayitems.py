# displayitems.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Panel manager for sets of displayed items.

The classes for individual games, and so forth, expect their widgets to be
displayed in some container (panel).  In some circumstances it is convenient
to use the DisplayItemsStub class to give appropriate answers: when the
container is not used.

There are four kinds of item: game, repertoire, partial position, and selection
rule.

"""

import tkinter

# To support workaround for:
# _tkinter.TclError: window id "<number>" doesn't exist in this application
# which occurs on 64-bit Windows 7 Home Edition running 64-bit Python 3.4.3
# but not on 32-bit Windows XP.
# Not yet known if 64-bit OSes in general are affected.
# The problem code is: widget.winfo_pathname(widget.winfo_id())
import sys

_win32_platform = sys.platform == "win32"
del sys
import os

_amd64 = (
    os.getenv("PROCESSOR_ARCHITECTURE") == "AMD64"
    or os.getenv("PROCESSOR_ARCHITEW6432") == "AMD64"
)
del os


class DisplayItemsError(Exception):
    pass


class DisplayItems(object):

    """Manage set of displayed widgets."""

    def __init__(self):
        """Create control data structures for  widgets."""
        self.order = []  # items in top to bottom display order.
        self.stack = []  # items in most recent visit order.
        self.panel_object_map = {}  # map panel identity to object displayed
        self.object_panel_count = {}  # count panels displaying an object

    def add_item_to_display(self, item):
        """Add item widget to GUI."""
        stack = self.stack
        order = self.order
        if len(order):
            order.insert(order.index(stack[-1]) + 1, item)
            stack.insert(0, item)
        else:
            stack.append(item)
            order.append(item)

    def contains_one_item(self):
        """Return True if order contains one element."""
        return len(self.order) == 1

    def get_active_item_top_widget(self):
        """Return top widget of item."""
        return self.stack[-1].get_top_widget()

    def is_item_panel_active(self, item):
        """Return True if itempanel's item is the active item."""
        if item.panel in self.panel_object_map:
            if item is self.stack[-1]:
                return True

    def is_mapped_panel(self, panel):
        """Return True if panel is in self.panel_object_map."""
        return panel in self.panel_object_map

    def is_visible(self):
        """Return True if active item exists."""
        return bool(self.stack)

    def count_items_in_stack(self):
        """Return number of items in stack.

        May be not equal count of items in panel_object_map or objects if item
        has been created but add_item_to_display() has not yet been called.

        """
        return len(self.stack)

    @property
    def active_item(self):
        try:
            return self.stack[-1]
        except IndexError:
            if self.stack:
                raise
            return None

    def get_stack_item(self, index):
        """Return self.stack[index]."""
        return self.stack[index]

    def cycle_active_item(self, prior=False):
        """Make active an item adjacent to current active item."""
        stack = self.stack
        order = self.order
        if prior:
            i = order.index(stack[-1]) - 1
            if i < 0:
                i = len(order) - 1
        else:
            i = order.index(stack[-1]) + 1
            if i >= len(order):
                i = 0
        stack.append(stack.pop(stack.index(order[i])))

    def any_items_displayed_of_type(self, class_=None):
        """Return True if instances of class_ displayed, default any class."""
        if class_ is None:
            return bool(len(self.stack))
        for i in self.stack:
            if isinstance(i, class_):
                return True
        return False

    def delete_item(self, item):
        """Delete item and return True if it was the active item."""
        stack = self.stack
        index = stack.index(item)
        stack[index].ui.set_game_change_notifications(stack[index])
        stack[index].destroy_widget()
        del self.order[self.order.index(stack[index])]
        del stack[index]

        # stack[-1] is always the active item.
        return index == len(stack)

    def delete_item_counters(self, item):
        """Delete panel, decrement counters, and return grid key for reset."""
        s = self.panel_object_map.get(item.panel, None)
        if s:
            del self.panel_object_map[item.panel]
        if s in self.object_panel_count:
            self.object_panel_count[s] -= 1
            if self.object_panel_count[s] == 0:
                del self.object_panel_count[s]
                return s

    def set_itemmap(self, item, objectkey):
        """Set panel_object_map to map item.panel to objectkey (database key).

        Panel is a surrogate for item in this map because item cannot be key
        in a dictionary,  Each item has one panel which contains everything.

        """
        self.panel_object_map[item.panel] = objectkey

    def increment_object_count(self, key):
        """Increment objects[key] to count widgets displaying object."""
        self.object_panel_count[key] = self.object_panel_count.get(key, 0) + 1

    def decrement_object_count(self, key):
        """Decrement objects[key] to count widgets displaying object."""
        self.object_panel_count[key] = self.object_panel_count.get(key, 0) - 1
        if self.object_panel_count[key] < 1:
            del self.object_panel_count[key]

    def adjust_edited_item(self, updater):
        """Fit self and active item state to database edit from updater values.

        It is assumed caller has checked it is the active item, or that only
        the active item gets to a point where it call this method.

        """
        item = self.stack[-1]
        if not (item.blockchange is True):
            return False
        panel = item.panel
        pom = self.panel_object_map
        if panel not in pom:
            return False
        oldkey = pom[panel]
        recno = updater.key.recno
        if oldkey[0] != recno:
            return False
        opc = self.object_panel_count
        opc[oldkey] -= 1
        if opc[oldkey] <= 0:
            del opc[oldkey]
        newkey = recno, updater.srvalue
        opc[newkey] = opc.get(newkey, 0) + 1
        pom[panel] = newkey
        item.sourceobject.srvalue = updater.srvalue
        item.blockchange = False
        return newkey

    def give_focus_to_widget(self, widget):
        """Give focus to widget and return (lose focus, gain focus) widgets."""
        stack = self.stack
        losefocus = stack[-1]

        # win32 amd64 workaround. See comment at top of module.
        # Code in except clause is semantically closer to try clause than
        # a str(widget) version.
        try:
            gain = widget.winfo_pathname(widget.winfo_id())
        except tkinter.TclError:
            if not _win32_platform or not _amd64:
                raise
            gain = ".".join((widget.winfo_parent(), widget.winfo_name()))

        for s in stack:
            sw = s.get_top_widget()

            # win32 amd64 workaround. See comment at top of module.
            # Code in except clause is semantically closer to try clause than
            # a str(widget) version.
            try:
                if gain.startswith(sw.winfo_pathname(sw.winfo_id())):
                    gainfocus = s
                    break
            except tkinter.TclError:
                if not _win32_platform or not _amd64:
                    raise
                if gain.startswith(
                    ".".join((sw.winfo_parent(), sw.winfo_name()))
                ):
                    gainfocus = s
                    break

        else:
            gainfocus = losefocus
        self.stack[-1].ui.set_toolbarframe_disabled()
        if losefocus is not gainfocus:
            stack.append(stack.pop(stack.index(gainfocus)))
            losefocus.bind_for_widget_navigation()
        gainfocus.bind_for_item_navigation()
        gainfocus.takefocus_widget.focus_set()
        if gainfocus.ui.single_view:
            gainfocus.ui.show_just_panedwindow_with_focus(
                gainfocus.get_top_widget()
            )
        return losefocus, gainfocus

    def set_focus(self):
        """Give focus to active widget."""
        if self.active_item:
            self.give_focus_to_widget(self.active_item.panel)
            self.active_item.set_statusbar_text()

    def configure_items_grid(self, panel, active_weight=None):
        """Adjust items panel grid row sizes after navigate add or delete."""
        if active_weight is None:
            active_weight = max(2, len(self.order) - 1)
        for e, g in enumerate(self.order):
            g.get_top_widget().grid(row=e, column=0, sticky=tkinter.NSEW)
            panel.grid_columnconfigure(0, weight=1, uniform="c")

            # next line may do as alternative to line above
            # panel.grid_columnconfigure(0, weight=1)

            if g is self.active_item:
                panel.grid_rowconfigure(e, weight=active_weight, uniform="v")
            else:
                panel.grid_rowconfigure(
                    e, weight=0 if g.ui.single_view else 1, uniform="v"
                )

    def object_display_count(self, key):
        """Return count of widgets which display object of key."""
        return self.object_panel_count.get(key)

    def set_insert_or_delete_on_all_items(self):
        """Call instance.set_insert_or_delete() for all items."""
        for g in self.stack:
            g.set_insert_or_delete()

    def forget_payload(self, parent):
        """Do nothing: compatibility with instances of Display subclasses."""

    def insert_payload(self, parent):
        """Do nothing: compatibility with instances of Display subclasses."""

    def is_payload_available(self):
        """Return True if items displayed: implies active item exists."""
        return bool(self.stack)

    def bind_for_widget_without_focus(self):
        """Return True if this item has the focus about to be lost."""
        if self.active_item is None:
            return False
        if not self.active_item.has_focus():
            return False
        self.active_item.bind_for_widget_navigation()
        return True


class DisplayItemsStub(object):

    """Stub manager for set of displayed widgets.

    Tk Frames, each containing an item and usually called a panel in ChessTab,
    can be displayed in a container with the convention the active item is the
    [-1] element of self.stack.  self.panel_object_map maps panel to item.

    The item can be displayed in a tk Toplevel with no other items.  The
    is_mapped_panel method and active_item property return values meaning the
    item is always the active item and no other item can be available to be
    active.

    """

    def __init__(self):
        """Create control data structures for  widgets."""

        # Only stack and panel_object_map are referenced when module written.
        # self.order = ()
        self.stack = (None,)
        self.panel_object_map = frozenset()
        # self.object_panel_count = frozenset()

    @property
    def active_item(self):
        return self.stack[-1]

    def is_mapped_panel(self, panel):
        """Return True if panel is in self.panel_object_map."""
        return panel in self.panel_object_map
