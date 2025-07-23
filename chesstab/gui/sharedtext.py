# sharedtext.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define navigation methods and bindings.

The classes are SharedText, SharedTextEngineText, and SharedTextScore.
"""

import tkinter

from .eventspec import EventSpec

# The event.state value if a single key is pressed.
# Thus '\r' gets 16, Shift-'\r' gets 17, and Control-'\r' gets 20, as
# expected from tkinter.__init__.Event.__repr__() method.
_NO_MODIFIERS = 16


class SharedText:
    """Provide navigation bindings for subclasses.

    Methods with the same name are used in one or both enginetext.EngineText
    and score.Score, but the internals are different.

    """

    def _set_primary_activity_bindings(self, switch=True):
        """Switch bindings for traversing query statement on or off."""
        self.set_event_bindings_score(
            self.get_f10_popup_events(
                self._post_active_menu_at_top_left, self._post_active_menu
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_button_events(buttonpress3=self._post_active_menu),
            switch=switch,
        )

    def set_score_pointer_item_navigation_bindings(self, switch):
        """Set or unset pointer bindings for game navigation."""
        self.set_event_bindings_score(
            self._get_button_events(buttonpress3=self._post_active_menu),
            switch=switch,
        )

    @staticmethod
    def get_primary_activity_events():
        """Return null tuple of navigation keypresses and callbacks."""
        return ()


class SharedTextEngineText:
    """Provide keypress and pointer navigation methods for subclasses.

    This is a separate hierarchy from SharedTextScore because the engine
    stuff is in a Toplevel instance not the main application widget.
    """

    EDIT_TAG = "edittag"
    TITLE_TAG = "titletag"
    TITLE_DATA = "titledata"
    TITLE_COLOR = "thistle"
    TEXT_TAG = "texttag"
    TEXT_DATA = "textdata"
    TEXT_COLOR = "wheat"
    ELIDE_SPLIT = "elidesplit"
    ELIDE_NAME = "elidename"
    ERROR_TAG = "errortag"
    ERROR_COLOR = "#eb3010"
    CURSOR_TAG = "cursortag"
    CURSOR_COLOR = "#76d9d9"
    _title_tags = [TITLE_DATA, TITLE_TAG, EDIT_TAG]
    _text_tags = [TEXT_DATA, TEXT_TAG, EDIT_TAG]

    def __init__(self, *a, **ka):
        """Initialize Text widget tags."""
        super().__init__(*a, **ka)
        score = self.score
        edit_tag = self.EDIT_TAG
        score.tag_configure(self.TITLE_TAG, background=self.TITLE_COLOR)
        score.tag_configure(self.TEXT_TAG, background=self.TEXT_COLOR)
        score.tag_configure(self.ELIDE_SPLIT, elide=tkinter.TRUE)
        score.tag_configure(self.ELIDE_NAME, elide=tkinter.TRUE)

        self.tag_bind(score, edit_tag, "<Return>", self._insert_newline)
        self.tag_bind(score, edit_tag, "<KP_Enter>", self._insert_newline)
        self.tag_bind(score, edit_tag, "<Escape>", self._suppress_char)
        self.tag_bind(score, edit_tag, "<Tab>", self._suppress_char)
        self.tag_bind(score, edit_tag, "<Up>", self._up_char)
        self.tag_bind(score, edit_tag, "<Down>", self._down_char)
        self.tag_bind(score, edit_tag, "<Left>", self._left_char)
        self.tag_bind(score, edit_tag, "<Right>", self._right_char)
        self.tag_bind(score, edit_tag, "<Home>", self._home_char)
        self.tag_bind(score, edit_tag, "<End>", self._end_char)
        self.tag_bind(score, edit_tag, "<BackSpace>", self._backspace_char)
        self.tag_bind(score, edit_tag, "<Delete>", self._delete_char)
        self.tag_bind(score, edit_tag, "<KeyPress>", self._insert_char)
        self.tag_bind(score, edit_tag, "<Alt-KeyPress>", self._ignore_char)

        self.bind(score, "<Up>", self._up_char_text)
        self.bind(score, "<Down>", self._down_char_text)

        # Suppress the standard keypresses provided by Text widget.
        self.bind(score, "<Return>", self._suppress_char)
        self.bind(score, "<Delete>", self._suppress_char)
        self.bind(score, "<BackSpace>", self._suppress_char)
        self.bind(score, "<KeyPress>", self._suppress_char)
        self.bind(score, "<Alt-KeyPress>", self._ignore_char)

    def get_tagged_text(self, tag):
        """Return text tagged with 'tag'."""
        tagranges = self.score.tag_ranges(tag)
        if not tagranges:
            return ""
        return self.score.get(*tagranges)

    def get_newline_delimited_title_and_text(self):
        """Return title and text joined by newline.

        Everything before the first newline is the title.

        """
        return "\n".join(
            (
                self.get_tagged_text(self.TITLE_DATA).strip(),
                self.get_tagged_text(self.TEXT_DATA),
            )
        )

    def toggle_entry_area_names(self):
        """Toggle display of entry area names in selection widgets."""
        widget = self.score
        if int(widget.tag_cget(self.ELIDE_NAME, "elide")):
            widget.tag_configure(self.ELIDE_NAME, elide=tkinter.FALSE)
        else:
            widget.tag_configure(self.ELIDE_NAME, elide=tkinter.TRUE)
        widget.see(tkinter.INSERT)

    def _suppress_char(self, event):
        """Ignore character and suppress other events."""
        del event
        return "break"

    def _ignore_char(self, event):
        """Ignore character and continue to other events."""
        del event
        return "continue"

    # Often this method allows the Insert cursor to be put back in an
    # edit area without pointer action.  See description of 'tag bind'
    # command in Text manual page of Tcl/Tk.
    def _up_char_text(self, event):
        """Navigate up when Insert cursor is outside edit area.

        This method moves the Insert cursor into a nearby edit area,
        usually the one before, when it is not in an edit area.  The
        pointer sometimes needs to be moved out of it's current area
        to enable further keyboard actions if the entry area names
        are visible.

        """
        del event
        score = self.score
        tag_names = score.tag_names(tkinter.INSERT)
        if self.EDIT_TAG in tag_names:
            return "break"
        for tag in (tkinter.INSERT, tkinter.END):
            prevrange = score.tag_prevrange(self.TEXT_DATA, tag)
            if prevrange:
                score.mark_set(tkinter.INSERT, prevrange[0])
                return "break"
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.END)
        if prevrange:
            score.mark_set(tkinter.INSERT, prevrange[-1] + "-1c")
        return "break"

    # Often this method allows the Insert cursor to be put back in an
    # edit area without pointer action.  See description of 'tag bind'
    # command in Text manual page of Tcl/Tk.
    def _down_char_text(self, event):
        """Navigate down when Insert cursor is outside edit area.

        This method moves the Insert cursor into a nearby edit area,
        usually the one before, when it is not in an edit area.  The
        pointer sometimes needs to be moved out of it's current area
        to enable further keyboard actions if the entry area names
        are visible.

        """
        del event
        score = self.score
        tag_names = score.tag_names(tkinter.INSERT)
        if self.EDIT_TAG in tag_names:
            return "break"
        for tag in (tkinter.INSERT, "1.0"):
            nextrange = score.tag_nextrange(self.TEXT_DATA, tag)
            if nextrange:
                score.mark_set(tkinter.INSERT, nextrange[0])
                return "break"
        nextrange = score.tag_nextrange(self.EDIT_TAG, "1.0")
        if nextrange:
            score.mark_set(tkinter.INSERT, nextrange[-1] + "-1c")
        return "break"

    def _insert_newline(self, event):
        """Insert newline if event.keysym is plain 'Return'."""
        if event.keysym != "Return" or event.state != _NO_MODIFIERS:
            return
        score = self.score
        if not score.tag_prevrange(self.TEXT_TAG, tkinter.INSERT):
            return
        self.score.insert(tkinter.INSERT, "\n", self._text_tags)

    def _insert_char(self, event):
        """Insert character."""
        if not event.char:
            return
        score = self.score
        if score.tag_prevrange(self.TEXT_TAG, tkinter.INSERT):
            self.score.insert(tkinter.INSERT, event.char, self._text_tags)
            return
        if score.tag_prevrange(self.TITLE_TAG, tkinter.INSERT):
            self.score.insert(tkinter.INSERT, event.char, self._title_tags)

    def _backspace_char(self, event):
        """Delete character to left of insert point."""
        del event
        score = self.score
        prevchar = score.index(tkinter.INSERT + "-1c")
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(tkinter.INSERT, "<=", prevrange[-1]):
            score.delete(prevchar)

    def _delete_char(self, event):
        """Delete character to right of insert point."""
        del event
        score = self.score
        nextchar = score.index(tkinter.INSERT + "+1c")
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(nextchar, "<", prevrange[-1]):
            score.delete(tkinter.INSERT)
            return
        nextrange = score.tag_nextrange(self.EDIT_TAG, tkinter.INSERT)
        if (
            nextrange
            and score.compare(score.index(tkinter.INSERT), "==", nextrange[0])
            and score.compare(nextchar, "<", nextrange[-1])
        ):
            score.delete(tkinter.INSERT)

    def _up_char(self, event):
        """Navigate up."""
        del event
        score = self.score
        prevline = score.index(tkinter.INSERT + "-1 display lines")
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(prevline, ">=", prevrange[0]):
            if score.compare(prevline, "<", prevrange[-1]):
                score.mark_set(tkinter.INSERT, prevline)
                return
            score.mark_set(tkinter.INSERT, score.index(prevline + "-1c"))
            return
        if prevrange:
            eliderange = score.tag_prevrange(self.ELIDE_SPLIT, prevrange[0])
            if eliderange:
                score.mark_set(tkinter.INSERT, prevrange[0])
                return

    def _down_char(self, event):
        """Navigate down."""
        del event
        score = self.score
        nextline = score.index(tkinter.INSERT + "+1 display lines")
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange:
            if score.compare(nextline, "<", prevrange[-1]):
                score.mark_set(tkinter.INSERT, nextline)
                return
            if score.compare(nextline, "<", prevrange[0]):
                score.mark_set(
                    tkinter.INSERT, score.index(prevrange[-1] + "-1c")
                )
                return
            nextrange = score.tag_nextrange(self.EDIT_TAG, tkinter.INSERT)
            if (
                nextrange
                and score.compare(nextline, ">", nextrange[0])
                and score.compare(nextline, "<", nextrange[-1])
            ):
                score.mark_set(tkinter.INSERT, nextline)
                return
        else:
            nextrange = score.tag_nextrange(self.EDIT_TAG, nextline)
        # This handles Down from after first character in TITLE_TAG area
        # when the first line of TEXT_TAG area has no characters.
        if nextrange:
            score.mark_set(tkinter.INSERT, nextrange[0])

    def _left_char(self, event):
        """Navigate left."""
        del event
        score = self.score
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(tkinter.INSERT, "<=", prevrange[-1]):
            score.mark_set(tkinter.INSERT, score.index(tkinter.INSERT + "-1c"))

    def _right_char(self, event):
        """Navigate right."""
        del event
        score = self.score
        nextchar = score.index(tkinter.INSERT + "+1c")
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(nextchar, "<", prevrange[-1]):
            score.mark_set(tkinter.INSERT, nextchar)
            return
        nextrange = score.tag_nextrange(self.EDIT_TAG, tkinter.INSERT)
        if (
            nextrange
            and score.compare(score.index(tkinter.INSERT), "==", nextrange[0])
            and score.compare(nextchar, "<", nextrange[-1])
        ):
            score.mark_set(tkinter.INSERT, nextchar)

    def _home_char(self, event):
        """Navigate home title."""
        del event
        score = self.score
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(tkinter.INSERT, "<=", prevrange[-1]):
            score.mark_set(tkinter.INSERT, prevrange[0])

    def _end_char(self, event):
        """Navigate end."""
        del event
        score = self.score
        prevrange = score.tag_prevrange(self.EDIT_TAG, tkinter.INSERT)
        if prevrange and score.compare(tkinter.INSERT, "<", prevrange[-1]):
            score.mark_set(tkinter.INSERT, score.index(prevrange[-1] + "-1c"))
            return
        nextrange = score.tag_nextrange(self.EDIT_TAG, tkinter.INSERT)
        if nextrange and score.compare(
            score.index(tkinter.INSERT), "==", nextrange[0]
        ):
            score.mark_set(tkinter.INSERT, score.index(nextrange[-1] + "-1c"))
            return

    def _populate_query_widget(self, name, query):
        """Populate widget with name and text of query."""
        score = self.score
        score.delete("1.0", tkinter.END)
        score.insert(tkinter.INSERT, "Description\n", [self.ELIDE_NAME])
        score.insert(tkinter.INSERT, " ", [self.ELIDE_SPLIT, self.TITLE_TAG])
        score.insert(tkinter.INSERT, name, self._title_tags)
        score.insert(tkinter.INSERT, "\n", [self.TITLE_TAG, self.EDIT_TAG])
        score.insert(tkinter.INSERT, " ", [self.ELIDE_SPLIT, self.TITLE_TAG])
        score.insert(tkinter.INSERT, "Text\n", [self.ELIDE_NAME])
        score.insert(tkinter.INSERT, " ", [self.ELIDE_SPLIT, self.TEXT_TAG])
        score.insert(tkinter.INSERT, query, self._text_tags)
        score.insert(tkinter.INSERT, "\n", [self.TEXT_TAG, self.EDIT_TAG])
        score.insert(tkinter.INSERT, " ", [self.ELIDE_SPLIT, self.TEXT_TAG])
        score.insert(tkinter.INSERT, "End", [self.ELIDE_NAME])
        nextrange = score.tag_nextrange(self.EDIT_TAG, "1.0")
        if nextrange:
            score.mark_set(tkinter.INSERT, nextrange[0])

    @staticmethod
    def _get_modifier_buttonpress_suppression_events():
        """Return empty tuple of event binding definitions.

        These events suppress buttonpress with Control, Shift, or Alt.

        """
        return ()

    def _post_active_menu(self, event=None):
        """Show the popup menu for chess engine definition navigation."""
        return self._post_menu(
            self.primary_activity_popup,
            self._create_primary_activity_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )

    def _post_active_menu_at_top_left(self, event=None):
        """Show the popup menu for chess engine definition navigation."""
        return self.post_menu_at_top_left(
            self.primary_activity_popup,
            self._create_primary_activity_popup,
            allowed=self._is_active_item_mapped(),
            event=event,
        )


class SharedTextScore:
    """Provide keypress and pointer navigation methods for subclasses.

    This is a separate hierarchy from SharedTextEngineText because the
    engine stuff is in a Toplevel instance not the main application
    widget.
    """

    def _add_cascade_menu_to_popup(
        self, label, popup, bindings=None, order=None, index=tkinter.END
    ):
        """Add cascade_menu, and bindings, to popup if not already present.

        The index is used as the label on the popup menu when visible.

        The bindings are not applied if cascade_menu is alreay in popup menu.

        """
        # Cannot see a way of asking 'Does entry exist?' other than:
        try:
            popup.index(label)
        except tkinter.TclError:
            cascade_menu = tkinter.Menu(master=popup, tearoff=False)
            popup.insert_cascade(label=label, menu=cascade_menu, index=index)
            if order is None:
                order = ()
            if bindings is None:
                bindings = {}
            for definition in order:
                function = bindings.get(definition)
                if function is not None:
                    cascade_menu.add_command(
                        label=definition[1],
                        command=self.try_command(function, cascade_menu),
                        accelerator=definition[2],
                    )

    # Subclasses which need widget navigation in their popup menus should
    # call this method.
    def _create_widget_navigation_submenu_for_popup(self, popup):
        """Create and populate a submenu of popup for widget navigation.

        The commands in the submenu should switch focus to another widget.

        Subclasses should define a generate_popup_navigation_maps method and
        binding_labels iterable suitable for allowed navigation.

        """
        navigation_map, local_map = self.generate_popup_navigation_maps()
        local_map.update(navigation_map)
        self._add_cascade_menu_to_popup(
            "Navigation", popup, bindings=local_map, order=self.binding_labels
        )

    # Subclasses which need dismiss widget in a menu should call this method.
    def _add_close_item_entry_to_popup(self, popup):
        """Add option to dismiss widget entry to popup.

        Subclasses must provide a delete_item_view method.

        """
        self._set_popup_bindings(popup, self._get_close_item_events())

    def _create_inactive_popup(self):
        """Create popup menu for an inactive widget."""
        assert self.inactive_popup is None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self._set_popup_bindings(popup, self._get_inactive_events())
        self._init_inactive_popup(popup)
        return popup

    def _get_inactive_button_events(self):
        """Return pointer event specifications for an inactive widget."""
        return self._get_modifier_buttonpress_suppression_events() + (
            (EventSpec.buttonpress_1, self.give_focus_to_widget),
            (EventSpec.buttonpress_3, self.post_inactive_menu),
        )

    def post_inactive_menu(self, event=None):
        """Show the popup menu for a game score in an inactive item."""
        return self._post_menu(
            self.inactive_popup, self._create_inactive_popup, event=event
        )

    def post_inactive_menu_at_top_left(self, event=None):
        """Show the popup menu for a game score in an inactive item."""
        return self.post_menu_at_top_left(
            self.inactive_popup, self._create_inactive_popup, event=event
        )

    def _get_inactive_events(self):
        """Return keypress event specifications for an inactive widget."""
        return (
            (EventSpec.display_make_active, self.set_focus_panel_item_command),
            (EventSpec.display_dismiss_inactive, self.delete_item_view),
        )
