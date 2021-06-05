# topleveltext.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide methods shared by all classes which display games, repertoires,
selection rules, CQL statements, and run engine commands in Toplevels.

"""


class ToplevelText:

    """Mixin providing methods shared by all classes which display selection
    rules, CQL statements, and run engine commands in Toplevels.

    """

    binding_labels = ()

    # Without this, right-click, Shift F10, and Ctrl F10, in CQL* and Query*
    # toplevels cause AttributeError exceptions.  This just causes a null
    # popup menu to be posted: perhaps difficult to notice.  Maybe a reason to
    # show something is needed.
    # The Engine* classes do not have this problem, perhaps because of the
    # 'Run Engine' option or the absence of the 'main display' options.
    # The Game* and Repertoire* classes have reason for a popup here.
    def create_widget_navigation_submenu_for_popup(self, popup):
        pass


class _ToplevelText:

    """Mixin providing methods shared by at least two of the DeleteText,
    EditText, and ShowText, classes.

    """

    def initialize(self):
        oldview = self.oldview
        self.ui_items_in_toplevels.add(oldview)
        self.parent.wm_title(self.get_title_for_object(self.object))
        self.initialize_item_bindings(oldview)
        self.set_item(oldview, self.object)

    def initialize_item_bindings(self, item):
        self.bind_buttons_to_widget(item.score)
        # item.set_score_pointer_to_score_bindings(False)

    def tidy_on_destroy(self):
        """Clear up after Toplevel destruction."""
        self.ui_items_in_toplevels.discard(self.oldview)
        self.ui_base_table.selection.clear()


class ShowText(_ToplevelText):
    def dialog_ok(self):
        """Close the show record toplevel."""
        if self.ui.database is None:
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super().dialog_ok()


class DeleteText(_ToplevelText):
    def dialog_ok(self):
        """Delete record and return delete action response (True for deleted).

        Check that database is open and is same one as deletion action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text="Cannot delete because not connected to a database"
            )
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super().dialog_ok()


class EditText(_ToplevelText):
    def initialize(self):
        if self.oldview:
            self.ui_items_in_toplevels.add(self.oldview)
            self.set_item(self.oldview, self.oldobject)
        newview = self.newview
        self.ui_items_in_toplevels.add(newview)
        self.set_item(newview, self.newobject)
        self.parent.wm_title(self.get_title_for_object(self.newobject))
        self.initialize_item_bindings(newview)

    def dialog_ok(self):
        """Update record and return update action response (True for updated).

        Check that database is open and is same one as update action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text="Cannot update because not connected to a database"
            )
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super().dialog_ok()

    def tidy_on_destroy(self):
        """Clear up after Toplevel destruction."""
        self.ui_items_in_toplevels.discard(self.oldview)
        self.ui_items_in_toplevels.discard(self.newview)
        self.ui_base_table.selection.clear()
