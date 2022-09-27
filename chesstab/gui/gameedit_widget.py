# gameedit_widget.py
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

from ..core.pgn import GameDisplayMoves
from .score import NonTagBind
from .game import Game
from .constants import (
    EDIT_GLYPH,
    EDIT_RESULT,
    EDIT_COMMENT,
    EDIT_RESERVED,
    EDIT_COMMENT_EOL,
    EDIT_ESCAPE_EOL,
    EDIT_MOVE,
    INSERT_RAV,
    NAVIGATE_MOVE,  # absence matters if no EDIT_... exists
    NAVIGATE_TOKEN,
    RAV_MOVES,
    RAV_TAG,
    START_SCORE_MARK,
    NAVIGATE_COMMENT,
    RAV_END_TAG,
    SPACE_SEP,
    RAV_START_TAG,
    FORCE_NEWLINE_AFTER_FULLMOVES,
)


class GameEditException(Exception):
    """Exception class for gameedit module."""


class GameEdit(Game):
    """Display a game with editing allowed.

    gameclass is passed to the superclass as the gameclass argument.  It
    defaults to GameDisplayMoves.

    Two PGN objects are available to a GameEdit instance: one provided
    by the creator of the instance used to display the game (from Game
    a base class of GameDisplay); the other inherited directly from PGN
    which is used for editing. This class provides methods to handle single
    moves complementing the game facing methods in PGN.

    Attribute _is_text_editable is True meaning the statement can be edited.

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    """

    # get_first_game() does not care whether self.score.get() returns
    # string or unicode but self.set_and_tag_item_text() does a
    # string.translate() so the get_first_game(x) calls must be
    # get_first_game(x.encode()).
    # ( encode() was introduced for compatibility with Python 2.5 but )
    # ( as this app now uses the hide attribute of paned windows from )
    # ( Tk 8.5 which is not available on Python 2.5 maybe convert to  )
    # ( unicode for Python 3.n compatibility and drop encode().       )

    # True means game score can be edited.
    _is_text_editable = True

    # Indicate the most recent set of bindings applied to score attribute.
    # There will be some implied bindings to the board attribute, but board is
    # shared with the analysis.score attribute so this indicator does not
    # imply anything about the board bindings.  Assumed that switching between
    # game and analysis will put the binding right.
    # Values are Tk tag names or members of NonTagBind enumeration.
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    # Indicate number of leading and trailing spaces for a token.
    _lead_trail = None

    def __init__(self, gameclass=GameDisplayMoves, **ka):
        """Extend with bindings to edit game score."""
        super().__init__(gameclass=gameclass, **ka)
        self.ravstack = []

        self._allowed_chars_in_token = ""  # or an iterable of characters.
        self.edit_move_context = dict()

        # Define popup menu for comment tokens.
        self.comment_popup = None

        # Define popup menu for PGN tag tokens.
        self.pgn_tag_popup = None

        # Define popup menu for Game Termination token.
        self.game_termination_popup = None

        # Define popup menu for '(' start RAV (recursive annotation variation)
        # tokens.
        self.start_rav_popup = None

        # Define popup menu for ')' end RAV (recursive annotation variation)
        # tokens.
        self.end_rav_popup = None

        # Define popup menu for '$' NAG (numeric annotation glyph) tokens.
        self.nag_popup = None

        # Define popup menu for ';...\n' comment to end of line tokens.
        self.comment_to_end_of_line_popup = None

        # Define popup menu for '\n%...\n' escape whole line tokens.
        self.escape_whole_line_popup = None

        # Define popup menu for '<...>' reserved tokens.
        self.reserved_popup = None

    def map_game(self):
        """Extend to set insertion cursor at start of moves."""
        super().map_game()
        # Is INSERT_TOKEN_MARK redundant now?  Let's see.
        self.score.mark_set(tkinter.INSERT, START_SCORE_MARK)

    # Unwanted tags can be inherited from surrounding characters.
    def map_move_text(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_move_text(token, position),
            self.get_current_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, INSERT_RAV),
            tag_position=False,  # already tagged by superclass method
        )
        self._game_scaffold.token_position = self.tagpositionmap[positiontag]
        return token_indicies

    # Unwanted tags can be inherited from surrounding characters.
    def map_start_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing.

        ravtag is placed on a stack so it can be recovered when the
        matching RAV end appears for tagging.  The tag marks two of the
        places where new variations may be inserted.

        """
        scaffold = self._game_scaffold
        token_indicies = super().map_start_rav(token, position)
        ravtag = self.get_rav_tag_name()
        self.ravstack.append(ravtag)
        prior = self.get_prior_tag_for_choice(scaffold.choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            scaffold.token_position = self.tagpositionmap[
                self.get_position_tag_of_index(prior_range[0])
            ]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_START_TAG, prior)
        else:
            scaffold.token_position = self.tagpositionmap[None]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_START_TAG)
        positiontag, token_indicies = self.tag_token_for_editing(
            token_indicies,
            self.get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_end_rav(self, token, position):
        """Extend to tag token for single-step navigation and game editing.

        ravtag is recovered from the stack to tag the end of RAV, one
        of the points where new variations can be inserted.

        """
        # last move in rav is editable
        scaffold = self._game_scaffold
        self.add_move_to_editable_moves(scaffold.vartag)
        token_indicies = super().map_end_rav(token, position)
        ravtag = self.ravstack.pop()
        prior = self.get_prior_tag_for_choice(scaffold.choicetag)
        prior_range = self.score.tag_ranges(prior)
        if prior_range:
            scaffold.token_position = self.tagpositionmap[
                self.get_position_tag_of_index(
                    self.get_range_of_main_move_for_rav(prior_range[0])[0]
                )
            ]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_END_TAG, prior)
        else:
            scaffold.token_position = self.tagpositionmap[None]
            tags = (ravtag, NAVIGATE_TOKEN, RAV_END_TAG)
        positiontag, token_indicies = self.tag_token_for_editing(
            token_indicies,
            self.get_tag_and_mark_names,
            tag_start_to_end=tags,
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_termination(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # last move in game is editable
        self.add_move_to_editable_moves(self._game_scaffold.vartag)
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_termination(token),
            self.get_tag_and_mark_names,
            # tag_start_to_end=(EDIT_RESULT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
            tag_start_to_end=(EDIT_RESULT,),
        )
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        return token_indicies

    def _map_start_comment(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            self.insert_token_into_text(token, SPACE_SEP),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_COMMENT, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )

    def map_start_comment(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_start_comment(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    def _map_comment_to_eol(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            super()._map_comment_to_eol(token, newline_prefix),
            self.get_tag_and_mark_names,
            tag_start_to_end=(
                EDIT_COMMENT_EOL,
                NAVIGATE_TOKEN,
                NAVIGATE_COMMENT,
            ),
        )

    def map_comment_to_eol(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_comment_to_eol(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    # Resolve pylint message arguments-differ deferred.
    # Depends on detail of planned naming of methods as private if possible.
    def _map_escape_to_eol(self, token, newline_prefix):
        """Extend to tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            super()._map_escape_to_eol(token, newline_prefix),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_ESCAPE_EOL, NAVIGATE_TOKEN),
        )

    # The EDIT_ESCAPE_EOL entry in _TOKEN_LEAD_TRAIL has been changed from
    # (2, 0) to (1, 0) to fit the add_escape_to_eol() case.  Not sure yet
    # if this breaks the map_escape_to_eol() case, which currently cannot
    # happen because '\n%\n' tokens are not put on database even if present
    # in the PGN movetext.
    def map_escape_to_eol(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_escape_to_eol(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_integer(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_integer(token, position),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN,),
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_glyph(self, token, newline_prefix):
        """Tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            self.insert_token_into_text(token, SPACE_SEP),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_GLYPH, NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )

    def map_glyph(self, token):
        """Override to tag token for single-step navigation and editing."""
        # At present NAGs are not put on a line of their own when following
        # a move.  They would be if the NAG translations were shown too.
        # before = self.tokens_exist_between_movetext_start_and_insert_point()
        before = self.score.tag_prevrange(
            NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
        )
        if before:
            before = NAVIGATE_MOVE not in self.score.tag_names(before[0])
        else:
            before = False

        positiontag, token_indicies = self._map_glyph(token, before)
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_period(self, token, position):
        """Extend to tag token for single-step navigation and game editing."""
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_period(token, position),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN,),
            mark_for_edit=False,
        )
        self.tagpositionmap[positiontag] = self.tagpositionmap[None]
        return token_indicies

    def _map_start_reserved(self, token, newline_prefix):
        """Tag token for single-step navigation and game editing."""
        if newline_prefix:
            self.insert_forced_newline_into_text()
        return self.tag_token_for_editing(
            self.insert_token_into_text(token, SPACE_SEP),
            self.get_tag_and_mark_names,
            tag_start_to_end=(EDIT_RESERVED, NAVIGATE_TOKEN),
        )

    def map_start_reserved(self, token):
        """Override to tag token for single-step navigation and editing."""
        positiontag, token_indicies = self._map_start_reserved(
            token, self.tokens_exist_between_movetext_start_and_insert_point()
        )
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        self.tagpositionmap[positiontag] = self._game_scaffold.token_position
        self.create_previousmovetag(positiontag, token_indicies[0])
        return token_indicies

    def map_non_move(self, token):
        """Extend to tag token for single-step navigation and game editing."""
        # mark_for_edit is True while no EDIT_... tag is done?
        positiontag, token_indicies = self.tag_token_for_editing(
            super().map_non_move(token),
            self.get_tag_and_mark_names,
            tag_start_to_end=(NAVIGATE_TOKEN, NAVIGATE_COMMENT),
        )
        self.tagpositionmap[positiontag] = None
        return token_indicies

    def tag_token_for_editing(
        self,
        token_indicies,
        tag_and_mark_names,
        tag_start_to_end=(),
        tag_start_to_sepend=(),
        mark_for_edit=True,
        tag_position=True,  # assume superclass caller method has not done tag
    ):
        """Tag token for single-step navigation and game editing.

        token_indicies - the start end and separator end indicies of the token
        tag_and_mark_names - method which returns tag and mark names for token
        tag_start_to_end - state tags appropriate for editable text of token
        tag_start_to_sepend - state tags appropriate for token
        mark_for_edit - True if tokenmark returned by tag_and_mark_names is
        to be made the insert point for editing the token
        tag_position - True if POSITION tag returned by tag_and_mark_names
        needs to be tagged. (There should be no harm doing this if not needed.)

        tag_and_mark_names is a method name because in some cases the current
        names are needed and in others new names should be generated first:
        pass the appropriate method.

        """
        # may yet do tag_and_mark_names as a flag (only two known cases).
        # tokenmark should remain between start and end, and may be further
        # restricted depending on the state tags.
        start, end, sepend = token_indicies
        positiontag, tokentag, tokenmark = tag_and_mark_names()
        tag_add = self.score.tag_add
        for tag in tag_start_to_end:
            tag_add(tag, start, end)
        for tag in tag_start_to_sepend:
            tag_add(tag, start, sepend)
        tag_add(tokentag, start, sepend)
        if mark_for_edit:
            self.score.mark_set(tokenmark, end)
        if tag_position:
            tag_add(positiontag, start, end)
        return positiontag, token_indicies

    def get_range_of_main_move_for_rav(self, start):
        """Return range of move for which start index ends a RAV."""
        widget = self.score
        for n_q in widget.tag_names(start):
            if n_q.startswith(RAV_MOVES):
                return widget.tag_nextrange(
                    n_q, widget.tag_nextrange(n_q, start)[1]
                )
        raise GameEditException("Unable to find position for end RAV")

    # This method may be removed because it is used in only two places, and
    # one of those needs the 'tr_q' value too.
    def add_move_to_editable_moves(self, variation):
        """Mark last move in variation for editing rather than insert RAV.

        This method should be called when it is known there are no more moves
        in the game or a RAV, which is at end of RAV or game termination.

        """
        widget = self.score
        tr_q = widget.tag_prevrange(variation, tkinter.END)

        # Is it a game score with no moves?
        if not tr_q:
            return

        widget.tag_add(EDIT_MOVE, *tr_q)
        widget.tag_remove(INSERT_RAV, *tr_q)

    def tokens_exist_between_movetext_start_and_insert_point(self):
        """Return True if tokens exist from movetext start to insert point."""
        return bool(
            self.score.tag_prevrange(
                NAVIGATE_TOKEN, tkinter.INSERT, START_SCORE_MARK
            )
        )

    def get_rav_tag_name(self):
        """Return suffixed RAV_TAG tag name.

        The Score.get_variation_tag_name() is assumed to have been called
        to increment self.variation_number and set the name of the
        corresponding RAV_MOVES tag.

        """
        return "".join((RAV_TAG, str(self.variation_number)))
