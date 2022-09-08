# topleveltext.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which initialize and close record or filter rule displays.

The records are games, repertoires, and rule lists.  The rules are selection
rules, CQL statements, and run engine commands in Toplevels.

"""


class ToplevelText:
    """Provide default popup menu initialisation methods for record display."""

    binding_labels = ()

    # Without this, right-click, Shift F10, and Ctrl F10, in CQL* and Query*
    # toplevels cause AttributeError exceptions.  This just causes a null
    # popup menu to be posted: perhaps difficult to notice.  Maybe a reason to
    # show something is needed.
    # The Engine* classes do not have this problem, perhaps because of the
    # 'Run Engine' option or the absence of the 'main display' options.
    # The Game* and Repertoire* classes have reason for a popup here.
    def create_widget_navigation_submenu_for_popup(self, popup):
        """Do nothing.

        Most ToplevelText subclasses require a handler for right-click,
        Shift F10, and Ctrl F10, events.

        A null popup menu is posted unless the subclass has a reason to
        implement a useful popup menu.
        """


class _ToplevelText:
    """Provide methods shared by this module's public _ToplevelText subclasses.

    The subclasses are DeleteText, EditText, and ShowText.
    """

    def initialize(self):
        """Initialize the widgets and event bindings in Toplevel widget."""
        oldview = self.oldview
        self.ui_items_in_toplevels.add(oldview)
        self.parent.wm_title(self.get_title_for_object(self.object))
        self.initialize_item_bindings(oldview)
        self.set_item(oldview, self.object)

    def initialize_item_bindings(self, item):
        """Initialize keypress and buttonpress bindings for item."""
        self.bind_buttons_to_widget(item.score)
        # item.set_score_pointer_to_score_bindings(False)

    def tidy_on_destroy(self):
        """Clear up after Toplevel destruction."""
        self.ui_items_in_toplevels.discard(self.oldview)
        self.ui_base_table.selection.clear()


class ShowText(_ToplevelText):
    """Show original text."""

    def dialog_ok(self):
        """Close the show record toplevel."""
        if self.ui.database is None:
            # pylint message access-member-before-definition.
            # ok defined in solentware_grid superclass of a sibling class.
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super().dialog_ok()


class DeleteText(_ToplevelText):
    """Show original text for record deletion."""

    def dialog_ok(self):
        """Delete record and return delete action response (True for deleted).

        Check that database is open and is same one as deletion action was
        started.

        """
        if self.ui.database is None:
            self.status.configure(
                text="Cannot delete because not connected to a database"
            )
            # pylint message access-member-before-definition.
            # ok defined in solentware_grid superclass of a sibling class.
            if self.ok:
                self.ok.destroy()
                self.ok = None
            self.blockchange = True
            return False
        return super().dialog_ok()


class EditText(_ToplevelText):
    """Show original and editable text versions for record editing."""

    def initialize(self):
        """Create widgets for the original and editable versions of text."""
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
            # pylint message access-member-before-definition.
            # ok defined in solentware_grid superclass of a sibling class.
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
