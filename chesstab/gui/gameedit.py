# gameedit.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Widget to edit a chess game score and put current position on a board.

The GameEdit class displays a game of chess and allows editing.  It is a
subclass of game.Game.

This class does not allow deletion of games from a database.

An instance of GameEdit fits into the user interface in two ways: as an item
in a panedwindow of the main widget, or as the only item in a new toplevel
widget.

"""

import tkinter
import tkinter.messagebox

from . import gameedit_handlers
from .score import NonTagBind
from .game import Game
from .eventspec import EventSpec
from . import constants


class GameEdit(gameedit_handlers.GameEdit):
    """Display a game with editing allowed."""

    def _set_primary_activity_bindings(self, switch=True):
        """Delegate then set bindings for primary activity.

        The primary activity is inserting moves and traversing all tokens.

        Moves, including RAVs can only be inserted if the game termination
        marker is present.

        """
        super()._set_primary_activity_bindings(switch=switch)
        if self.score.tag_ranges(constants.EDIT_RESULT):
            self._set_keypress_binding(
                function=self._insert_rav,
                bindings=(EventSpec.gameedit_insert_rav,),
                switch=switch,
            )
            function = self._insert_rav_castle_queenside  # Line count.
            self.set_event_bindings_score(
                ((EventSpec.gameedit_insert_castle_queenside, function),),
                switch=switch,
            )
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    def _set_select_variation_bindings(self, switch=True):
        """Switch bindings for selecting a variation on or off."""
        super()._set_select_variation_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=False
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=False
        )

    def _set_edit_symbol_mode_bindings(
        self,
        switch=True,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        popup_top_left=None,
        popup_pointer=None,
    ):
        """Set or unset bindings for editing symbols depending on switch.

        Defaults for include_ooo, include_tags, and include_movetext, are for
        non-move tokens in the movetext area of the PGN game score.

        include_ooo refers to the popup menu option and Ctrl-o option to insert
        O-O-O in the game score when both O-O and O-O-O are legal moves.

        include_tags refers to the popup menu options, and keystrokes, to add
        or delete empty PGN tags in the PGN tag area.

        include_movetext refers to the popup menu options, and keystrokes, to
        add empty non-move constructs in the movetext area.

        popup_top_left is expected to be a function to post a popup menu at
        top left of widget with focus by Shift F10.  Default is no popup which
        causes menubar to activate.

        popup_pointer is expected to be a function to post a popup menu at the
        pointer location by Control F10 or right click.  Default is no popup
        which means Control F10 causes menubar to activate.

        """
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )
        if include_movetext:
            self.set_event_bindings_score(
                self._get_insert_pgn_in_movetext_events(), switch=switch
            )
        if include_tags:
            self.set_event_bindings_score(
                self._get_insert_pgn_in_tags_events(), switch=switch
            )
        self.set_event_bindings_score(
            self._get_set_insert_in_token_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_delete_char_in_token_events(), switch=switch
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self._add_char_to_token),),
            switch=switch,
        )
        if include_ooo:
            function = self._insert_castle_queenside_command  # Line count.
            self.set_event_bindings_score(
                ((EventSpec.gameedit_insert_castle_queenside, function),),
                switch=switch,
            )
        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self._go_to_token, buttonpress3=popup_pointer
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self.get_f10_popup_events(popup_top_left, popup_pointer),
            switch=switch,
        )
        # Allowed characters defined in _set_token_context() call

    def _bind_for_edit_glyph(self, switch=True):
        """Set bindings for EDIT_GLYPH state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_GLYPH
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_nag_menu_at_top_left,
            popup_pointer=self._post_nag_menu,
        )

    def _bind_for_edit_game_termination(self, switch=True):
        """Set bindings for EDIT_RESULT state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_RESULT
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            include_movetext=False,
            popup_top_left=self._post_game_termination_menu_at_top_left,
            popup_pointer=self._post_game_termination_menu,
        )

    def _bind_for_edit_pgn_tag_name(self, switch=True):
        """Set bindings for EDIT_PGN_TAG_NAME state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_PGN_TAG_NAME
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            include_tags=True,
            include_movetext=False,
            popup_top_left=self._post_pgn_tag_menu_at_top_left,
            popup_pointer=self._post_pgn_tag_menu,
        )

    def _bind_for_edit_pgn_tag_value(self, switch=True):
        """Set bindings for EDIT_PGN_TAG_VALUE state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_PGN_TAG_VALUE
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            include_tags=True,
            include_movetext=False,
            popup_top_left=self._post_pgn_tag_menu_at_top_left,
            popup_pointer=self._post_pgn_tag_menu,
        )

    def _bind_for_edit_comment(self, switch=True):
        """Set bindings for EDIT_COMMENT state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_COMMENT
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_comment_menu_at_top_left,
            popup_pointer=self._post_comment_menu,
        )

    def _bind_for_edit_reserved(self, switch=True):
        """Set bindings for EDIT_RESERVED state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_RESERVED
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_reserved_menu_at_top_left,
            popup_pointer=self._post_reserved_menu,
        )

    def _bind_for_edit_comment_eol(self, switch=True):
        """Set bindings for EDIT_COMMENT_EOL state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_COMMENT_EOL
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_comment_to_end_of_line_menu_at_top_left,
            popup_pointer=self._post_comment_to_end_of_line_menu,
        )

    def _bind_for_edit_escape_eol(self, switch=True):
        """Set bindings for EDIT_ESCAPE_EOL state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_ESCAPE_EOL
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_escape_whole_line_menu_at_top_left,
            popup_pointer=self._post_escape_whole_line_menu,
        )

    def _bind_for_edit_move_error(self, switch=True):
        """Set bindings for EDIT_MOVE_ERROR state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_MOVE_ERROR
        self._set_edit_symbol_mode_bindings(switch=switch)

    def _bind_for_edit_move(self, switch=True):
        """Set bindings for EDIT_MOVE state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.EDIT_MOVE
        super()._set_primary_activity_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )
        function = self._insert_move_castle_queenside  # Line count.
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_insert_move, self._insert_move),
                (EventSpec.gameedit_edit_move, self._edit_move),
                (EventSpec.gameedit_insert_castle_queenside, function),
            ),
            switch=switch,
        )

    def _bind_for_insert_rav(self, switch=True):
        """Set bindings for INSERT_RAV state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.INSERT_RAV
        self._set_primary_activity_bindings(switch=switch)

    def _bind_for_move_edited(self, switch=True):
        """Set bindings for MOVE_EDITED state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.MOVE_EDITED
        super()._set_primary_activity_bindings(switch=switch)
        self.set_event_bindings_score(
            self._get_insert_pgn_in_movetext_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_delete_char_in_move_events(), switch=switch
        )
        function = self._add_move_char_to_token  # Line count.
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_move_char_to_token, function),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self._go_to_token,
                buttonpress3=self._post_move_menu,
            ),
            switch=switch,
        )

    # Should self._set_edit_symbol_mode_bindings() be used?
    def _bind_for_rav_start(self, switch=True):
        """Set bindings for RAV_START_TAG state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.RAV_START_TAG
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_start_rav_menu_at_top_left,
            popup_pointer=self._post_start_rav_menu,
        )
        # self.set_event_bindings_score((
        #    (EventSpec.gameedit_add_char_to_token,
        #     self.press_break),
        #    ), switch=switch)
        self._set_keypress_binding(
            function=self._insert_rav_after_rav_start,
            bindings=(EventSpec.gameedit_insert_rav_after_rav_start,),
            switch=switch,
        )
        self._set_keypress_binding(
            function=self._insert_rav_after_rav_start_move_or_rav,
            bindings=(
                EventSpec.gameedit_insert_rav_after_rav_start_move_or_rav,
            ),
            switch=switch,
        )
        self._set_keypress_binding(
            function=self._insert_rav_after_rav_end,
            bindings=(EventSpec.gameedit_insert_rav_after_rav_end,),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    # Should self._set_edit_symbol_mode_bindings() be used?
    def _bind_for_rav_end(self, switch=True):
        """Set bindings for RAV_END_TAG state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = constants.RAV_END_TAG
        self._set_edit_symbol_mode_bindings(
            switch=switch,
            popup_top_left=self._post_end_rav_menu_at_top_left,
            popup_pointer=self._post_end_rav_menu,
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.press_break),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    def _bind_for_no_current_token(self, switch=True):
        """Set bindings for NO_CURRENT_TOKEN state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.NO_CURRENT_TOKEN
        self.set_event_bindings_score(
            self._get_button_events(
                buttonpress1=self._go_to_token,
                buttonpress3=self._post_comment_menu,
            ),
            switch=switch,
        )

    def _bind_for_unrecognised_edit_token(self, switch=True):
        """Set bindings for DEFAULT_BINDINGS state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.DEFAULT_BINDINGS
        self.set_event_bindings_score(
            (
                (EventSpec.alt_buttonpress_1, ""),
                (EventSpec.buttonpress_1, ""),
                (EventSpec.buttonpress_3, self._post_comment_menu),
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            ((EventSpec.gameedit_add_char_to_token, self.press_break),),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_primary_activity_from_non_move_events(), switch=switch
        )
        self.set_event_bindings_score(
            self._get_navigate_score_events(), switch=switch
        )

    def bind_for_initial_state(self, switch=True):
        """Set bindings for INITIAL_BINDINGS state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    def _bind_for_no_editable_tags(self, switch=True):
        """Do nothing.

        Set bindings for NO_EDITABLE_TAGS state.
        """

    def _bind_for_current_without_tags(self, switch=True):
        """Set bindings for CURRENT_NO_TAGS state."""
        if switch:
            self.token_bind_method[self._most_recent_bindings](self, False)
            self._most_recent_bindings = NonTagBind.CURRENT_NO_TAGS
        self.set_event_bindings_score(
            (
                (EventSpec.gameedit_add_move_char_to_token, self.press_break),
                (EventSpec.gameedit_insert_castle_queenside, self.press_break),
            ),
            switch=switch,
        )
        self.set_event_bindings_score(
            self._get_delete_char_in_move_events(), False
        )

    # Dispatch dictionary for token binding selection.
    # Keys are the possible values of self._most_recent_bindings.
    token_bind_method = {
        constants.EDIT_GLYPH: _bind_for_edit_glyph,
        constants.EDIT_RESULT: _bind_for_edit_game_termination,
        constants.EDIT_PGN_TAG_NAME: _bind_for_edit_pgn_tag_name,
        constants.EDIT_PGN_TAG_VALUE: _bind_for_edit_pgn_tag_value,
        constants.EDIT_COMMENT: _bind_for_edit_comment,
        constants.EDIT_RESERVED: _bind_for_edit_reserved,
        constants.EDIT_COMMENT_EOL: _bind_for_edit_comment_eol,
        constants.EDIT_ESCAPE_EOL: _bind_for_edit_escape_eol,
        constants.EDIT_MOVE_ERROR: _bind_for_edit_move_error,
        constants.EDIT_MOVE: _bind_for_edit_move,
        constants.INSERT_RAV: _bind_for_insert_rav,
        constants.MOVE_EDITED: _bind_for_move_edited,
        constants.RAV_END_TAG: _bind_for_rav_end,
        constants.RAV_START_TAG: _bind_for_rav_start,
        NonTagBind.NO_CURRENT_TOKEN: _bind_for_no_current_token,
        NonTagBind.DEFAULT_BINDINGS: _bind_for_unrecognised_edit_token,
        NonTagBind.INITIAL_BINDINGS: bind_for_initial_state,
        NonTagBind.NO_EDITABLE_TAGS: _bind_for_no_editable_tags,
        NonTagBind.CURRENT_NO_TAGS: _bind_for_current_without_tags,
        NonTagBind.SELECT_VARIATION: Game.bind_for_select_variation,
    }

    def _set_edit_bindings_and_to_prev_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at previous PGN tag."""
        del event
        return self._to_prev_pgn_tag()

    def _set_edit_bindings_and_to_next_pgn_tag(self, event=None):
        """Remove bindings for editing and put cursor at next PGN tag."""
        del event
        return self._to_prev_pgn_tag()  # to start of PGN tag if in one.

    def _create_popup(self, popup, move_navigation=None):
        """Create and return popup menu with optional move navigation.

        This method is called by all the create_*_popup methods.

        """
        assert popup is None
        assert move_navigation is not None
        popup = tkinter.Menu(master=self.score, tearoff=False)
        self._set_popup_bindings(popup, move_navigation())
        export_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_export_submenu(export_submenu)
        popup.add_cascade(label="Export", menu=export_submenu)
        # pylint message assignment-from-none is false positive.
        # However it is sensible to do an isinstance test.
        database_submenu = self._create_database_submenu(popup)
        if isinstance(database_submenu, tkinter.Menu):
            popup.add_cascade(label="Database", menu=database_submenu)
        return popup

    # Most popups are same except for binding the popup menu attribute.
    # This does the work for the ones with identical processing.
    def _create_non_move_popup(self, popup):
        """Create and return popup menu for PGN non-move tokens.

        This method is called by the create_*_popup methods for each
        non-move token.

        """
        popup = self._create_popup(
            popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        return popup

    def _create_pgn_tag_popup(self):
        """Create and return popup menu for PGN Tag token."""
        popup = self._create_popup(
            self.pgn_tag_popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup,
            include_tags=True,
            include_movetext=False,
            index=self.export_popup_label,
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        self.pgn_tag_popup = popup
        return popup

    def _post_pgn_tag_menu(self, event=None):
        """Post popup menu when a PGN tag is current token."""
        return self._post_menu(
            self.pgn_tag_popup, self._create_pgn_tag_popup, event=event
        )

    def _post_pgn_tag_menu_at_top_left(self, event=None):
        """Post popup menu when a PGN tag is current token."""
        return self.post_menu_at_top_left(
            self.pgn_tag_popup, self._create_pgn_tag_popup, event=event
        )

    def _create_game_termination_popup(self):
        """Create and return popup menu for PGN game termination token."""
        popup = self._create_popup(
            self.game_termination_popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        self.game_termination_popup = popup
        return popup

    def _post_game_termination_menu(self, event=None):
        """Post popup menu when game termination is current token."""
        return self._post_menu(
            self.game_termination_popup,
            self._create_game_termination_popup,
            event=event,
        )

    def _post_game_termination_menu_at_top_left(self, event=None):
        """Post popup menu when game termination is current token."""
        return self.post_menu_at_top_left(
            self.game_termination_popup,
            self._create_game_termination_popup,
            event=event,
        )

    def _create_comment_popup(self):
        """Create and return popup menu for PGN comment, {...}, token."""
        popup = self._create_non_move_popup(self.comment_popup)
        self.comment_popup = popup
        return popup

    def _post_comment_menu(self, event=None):
        """Post popup menu when a comment is current token."""
        return self._post_menu(
            self.comment_popup, self._create_comment_popup, event=event
        )

    def _post_comment_menu_at_top_left(self, event=None):
        """Post popup menu when a comment is current token."""
        return self.post_menu_at_top_left(
            self.comment_popup, self._create_comment_popup, event=event
        )

    def _create_nag_popup(self):
        """Create and return popup menu for PGN numeric annotation glyph."""
        popup = self._create_non_move_popup(self.nag_popup)
        self.nag_popup = popup
        return popup

    def _post_nag_menu(self, event=None):
        """Post popup menu when a NAG is current token."""
        return self._post_menu(
            self.nag_popup, self._create_nag_popup, event=event
        )

    def _post_nag_menu_at_top_left(self, event=None):
        """Post popup menu when a NAG is current token."""
        return self.post_menu_at_top_left(
            self.nag_popup, self._create_nag_popup, event=event
        )

    def _create_start_rav_popup(self):
        """Create and return popup menu for PGN start RAV token."""
        popup = self._create_popup(
            self.start_rav_popup,
            move_navigation=self._get_primary_activity_from_non_move_events,
        )
        self._add_pgn_navigation_to_submenu_of_popup(
            popup, index=self.export_popup_label
        )
        self._add_pgn_insert_to_submenu_of_popup(
            popup, include_rav_start_rav=True, index=self.export_popup_label
        )
        self._create_widget_navigation_submenu_for_popup(popup)
        self.start_rav_popup = popup
        return popup

    def _post_start_rav_menu(self, event=None):
        """Post popup menu when a '(', start RAV, is current token."""
        return self._post_menu(
            self.start_rav_popup, self._create_start_rav_popup, event=event
        )

    def _post_start_rav_menu_at_top_left(self, event=None):
        """Post popup menu when a '(', start RAV, is current token."""
        return self.post_menu_at_top_left(
            self.start_rav_popup, self._create_start_rav_popup, event=event
        )

    def _create_end_rav_popup(self):
        """Create and return popup menu for PGN end RAV token."""
        popup = self._create_non_move_popup(self.end_rav_popup)
        self.end_rav_popup = popup
        return popup

    def _post_end_rav_menu(self, event=None):
        """Post popup menu when a ')', end RAV, is current token."""
        return self._post_menu(
            self.end_rav_popup, self._create_end_rav_popup, event=event
        )

    def _post_end_rav_menu_at_top_left(self, event=None):
        """Post popup menu when a ')', end RAV, is current token."""
        return self.post_menu_at_top_left(
            self.end_rav_popup, self._create_end_rav_popup, event=event
        )

    def _create_comment_to_end_of_line_popup(self):
        """Create and return popup menu for PGN comment to end line token."""
        popup = self._create_non_move_popup(self.comment_to_end_of_line_popup)
        self.comment_to_end_of_line_popup = popup
        return popup

    def _post_comment_to_end_of_line_menu(self, event=None):
        r"""Post popup menu when a ';...\n' comment is current token."""
        return self._post_menu(
            self.comment_to_end_of_line_popup,
            self._create_comment_to_end_of_line_popup,
            event=event,
        )

    def _post_comment_to_end_of_line_menu_at_top_left(self, event=None):
        r"""Post popup menu when a ';...\n' comment is current token."""
        return self.post_menu_at_top_left(
            self.comment_to_end_of_line_popup,
            self._create_comment_to_end_of_line_popup,
            event=event,
        )

    def _create_escape_whole_line_popup(self):
        """Create and return popup menu for PGN escaped line token."""
        popup = self._create_non_move_popup(self.escape_whole_line_popup)
        self.escape_whole_line_popup = popup
        return popup

    def _post_escape_whole_line_menu(self, event=None):
        r"""Post popup menu when a '\n%...\n' escape is current token."""
        return self._post_menu(
            self.escape_whole_line_popup,
            self._create_escape_whole_line_popup,
            event=event,
        )

    def _post_escape_whole_line_menu_at_top_left(self, event=None):
        r"""Post popup menu when a '\n%...\n' escape is current token."""
        return self.post_menu_at_top_left(
            self.escape_whole_line_popup,
            self._create_escape_whole_line_popup,
            event=event,
        )

    def _create_reserved_popup(self):
        """Create and return popup menu for PGN reserved tokens."""
        popup = self._create_non_move_popup(self.reserved_popup)
        self.reserved_popup = popup
        return popup

    def _post_reserved_menu(self, event=None):
        """Post popup menu when a '<...>, reserved, is current token."""
        return self._post_menu(
            self.reserved_popup, self._create_reserved_popup, event=event
        )

    def _post_reserved_menu_at_top_left(self, event=None):
        """Post popup menu when a '<...>, reserved, is current token."""
        return self.post_menu_at_top_left(
            self.reserved_popup, self._create_reserved_popup, event=event
        )

    def _populate_navigate_score_submenu(self, submenu):
        """Populate popup menu with commands for navigating PGN."""
        self._set_popup_bindings(submenu, self._get_navigate_score_events())

    # O-O-O is available to avoid ambiguity if both O-O and O-O-O are legal
    # when typing moves in.  When move editing is not allowed the O-O-O menu
    # option must be suppressed.
    # The addition of include_tags and include_movetext arguments gets the
    # method close to precipice of too complicated.
    def _populate_pgn_submenu(
        self,
        submenu,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        include_rav_start_rav=False,
        include_move_rav=False,
    ):
        """Populate popup menu with commands for inserting PGN."""
        assert not (include_rav_start_rav and include_move_rav)
        if include_movetext:
            self._set_popup_bindings(
                submenu, self._get_insert_pgn_in_movetext_events()
            )
        if include_rav_start_rav:
            self._set_popup_bindings(
                submenu, self._get_insert_pgn_rav_in_movetext_events()
            )
        if include_move_rav:
            self._set_popup_bindings(
                submenu, self._get_insert_rav_in_movetext_events()
            )
        if include_tags:
            self._set_popup_bindings(
                submenu, self._get_insert_pgn_in_tags_events()
            )
        if not include_ooo:
            return
        function = self._insert_castle_queenside_command  # Line count.
        self._set_popup_bindings(
            submenu,
            ((EventSpec.gameedit_insert_castle_queenside, function),),
        )

    # This method should be in GameEdit, the nearest subclass of Score which
    # supports editing games.
    # Subclasses which need non-move PGN navigation should call this method.
    # Intended for editors.
    def _add_pgn_insert_to_submenu_of_popup(
        self,
        popup,
        include_ooo=False,
        include_tags=False,
        include_movetext=True,
        include_rav_start_rav=False,
        include_move_rav=False,
        index=tkinter.END,
    ):
        """Add non-move PGN insertion to a submenu of popup.

        Subclasses must provide the methods named.

        Moves, including RAVs, are inserted at current by starting to type.

        Other items, such as comments, are inserted with the options on this
        menu.

        """
        pgn_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_pgn_submenu(
            pgn_submenu,
            include_ooo=include_ooo,
            include_tags=include_tags,
            include_movetext=include_movetext,
            include_rav_start_rav=include_rav_start_rav,
            include_move_rav=include_move_rav,
        )
        popup.insert_cascade(index=index, label="PGN", menu=pgn_submenu)

    def _get_navigate_score_events(self):
        """Return tuple of event definitions for navigating PGN.

        Going to next and previous token, comment, or PGN tag; and first and
        last token and comment is supported.

        See Score.get_primary_activity_events for next and previous moves.

        """
        return (
            (
                EventSpec.gameedit_show_previous_rav_start,
                self._show_prev_rav_start,
            ),
            (
                EventSpec.gameedit_show_next_rav_start,
                self._show_next_rav_start,
            ),
            (EventSpec.gameedit_show_previous_token, self._show_prev_token),
            (EventSpec.gameedit_show_next_token, self._show_next_token),
            (EventSpec.gameedit_show_first_token, self._show_first_token),
            (EventSpec.gameedit_show_last_token, self._show_last_token),
            (EventSpec.gameedit_show_first_comment, self._show_first_comment),
            (EventSpec.gameedit_show_last_comment, self._show_last_comment),
            (
                EventSpec.gameedit_show_previous_comment,
                self._show_prev_comment,
            ),
            (EventSpec.gameedit_show_next_comment, self._show_next_comment),
            (EventSpec.gameedit_to_previous_pgn_tag, self._to_prev_pgn_tag),
            (EventSpec.gameedit_to_next_pgn_tag, self._to_next_pgn_tag),
        )

    def _get_insert_pgn_in_movetext_events(self):
        """Return tuple of event definitions for inserting PGN constructs.

        Inserting RAVs and adding of moves at end of game is allowed only when
        the current token is a move or a RAV start token.  The relevant
        characters are defined elsewhere, including the O-O-O shortcut
        convenient when both O-O-O and O-O are legal moves.

        The bindings for inserting RAVs are defined in other methods.

        """
        return (
            (EventSpec.gameedit_insert_comment, self._insert_comment),
            (EventSpec.gameedit_insert_reserved, self._insert_reserved),
            (
                EventSpec.gameedit_insert_comment_to_eol,
                self._insert_comment_to_eol,
            ),
            (
                EventSpec.gameedit_insert_escape_to_eol,
                self._insert_escape_to_eol,
            ),
            (EventSpec.gameedit_insert_glyph, self._insert_glyph),
            (EventSpec.gameedit_insert_white_win, self._insert_result_win),
            (EventSpec.gameedit_insert_draw, self._insert_result_draw),
            (EventSpec.gameedit_insert_black_win, self._insert_result_loss),
            (
                EventSpec.gameedit_insert_other_result,
                self._insert_result_termination,
            ),
        )

    # Use in creating popup menus only, where the entries exist to
    # advertise the options.
    def _get_insert_pgn_rav_in_movetext_events(self):
        """Return tuple of event definitions for inserting RAVs."""
        function = self._insert_rav_command  # Line count.
        return (
            (EventSpec.gameedit_insert_rav_after_rav_end, function),
            (
                EventSpec.gameedit_insert_rav_after_rav_start_move_or_rav,
                function,
            ),
            (EventSpec.gameedit_insert_rav_after_rav_start, function),
        )

    # Use in creating popup menus only, where the entries exist to
    # advertise the options.
    def _get_insert_rav_in_movetext_events(self):
        """Return tuple of event definitions for inserting text."""
        return ((EventSpec.gameedit_insert_rav, self._insert_rav_command),)

    def _get_insert_pgn_in_tags_events(self):
        """Return tuple of event definitions for inserting PGN constructs.

        Inserting and deleting PGN tags is allowed only when the current token
        is a PGN tag.

        """
        return (
            (EventSpec.gameedit_insert_pgn_tag, self._insert_pgn_tag),
            (
                EventSpec.gameedit_insert_pgn_seven_tag_roster,
                self._insert_pgn_seven_tag_roster,
            ),
            (
                EventSpec.gameedit_delete_empty_pgn_tag,
                self._delete_empty_pgn_tag,
            ),
        )

    def _get_set_insert_in_token_events(self):
        """Return tuple of event definitions for inserting text."""
        return (
            (
                EventSpec.gameedit_set_insert_previous_line_in_token,
                self._set_insert_prev_line_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_previous_char_in_token,
                self._set_insert_prev_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_next_char_in_token,
                self._set_insert_next_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_next_line_in_token,
                self._set_insert_next_line_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_first_char_in_token,
                self._set_insert_first_char_in_token,
            ),
            (
                EventSpec.gameedit_set_insert_last_char_in_token,
                self._set_insert_last_char_in_token,
            ),
        )

    def _get_delete_char_in_token_events(self):
        """Return event specification tuple for text deletion."""
        return (
            (
                EventSpec.gameedit_delete_token_char_left,
                self._delete_token_char_left,
            ),
            (
                EventSpec.gameedit_delete_token_char_right,
                self._delete_token_char_right,
            ),
            (EventSpec.gameedit_delete_char_left, self._delete_char_left),
            (EventSpec.gameedit_delete_char_right, self._delete_char_right),
        )

    def _get_delete_char_in_move_events(self):
        """Return event specification tuple for move deletion."""
        return (
            (
                EventSpec.gameedit_delete_move_char_left_shift,
                self._delete_move_char_left,
            ),
            (
                EventSpec.gameedit_delete_move_char_right_shift,
                self._delete_move_char_right,
            ),
            (
                EventSpec.gameedit_delete_move_char_left,
                self._delete_move_char_left,
            ),
            (
                EventSpec.gameedit_delete_move_char_right,
                self._delete_move_char_right,
            ),
        )

    def _get_primary_activity_from_non_move_events(self):
        """Return event specification tuple for game score navigation."""
        return (
            (
                EventSpec.gameedit_non_move_show_previous_in_variation,
                self._show_prev_in_variation_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_previous_in_line,
                self._show_prev_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_next_in_line,
                self._show_next_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_next_in_variation,
                self._show_next_in_variation_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_first_in_line,
                self._show_first_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_last_in_line,
                self._show_last_in_line_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_first_in_game,
                self._show_first_in_game_from_non_move_token,
            ),
            (
                EventSpec.gameedit_non_move_show_last_in_game,
                self._show_last_in_game_from_non_move_token,
            ),
        )

    def _add_pgn_navigation_to_submenu_of_popup(
        self, popup, index=tkinter.END
    ):
        """Add non-move PGN navigation to a submenu of popup."""
        navigate_score_submenu = tkinter.Menu(master=popup, tearoff=False)
        self._populate_navigate_score_submenu(navigate_score_submenu)
        popup.insert_cascade(
            index=index, label="Navigate Score", menu=navigate_score_submenu
        )
