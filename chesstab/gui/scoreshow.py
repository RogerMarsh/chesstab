# scoreshow.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class with methods to support event handlers defined in Score class.

Score is a subclass of ScoreShow.

"""

import tkinter

from .constants import (
    NAVIGATE_MOVE,
    TOKEN,
    RAV_MOVES,
    CHOICE,
    PRIOR_MOVE,
    RAV_SEP,
    POSITION,
    MOVE_TAG,
    SELECTION,
    ALTERNATIVE_MOVE_TAG,
    LINE_TAG,
    VARIATION_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    TOKEN_MARK,
)
from ..core.pgn import get_position_string
from .scorewidget import ScoreWidget


class ScoreNoGameException(Exception):
    """Raise to indicate non-PGN text after Game Termination Marker.

    The ScoreNoGameException is intended to catch cases where a file
    claiming to be a PGN file contains text with little resemblance to
    the PGN standard between a Game Termination Marker and a PGN Tag or
    a move description like Ba4.  For example 'anytext*anytextBa4anytext'
    or 'anytext0-1anytext[tagname"tagvalue"]anytext'.

    """


class ScoreShow(ScoreWidget):
    """Methods to adjust game display in response to events."""

    def see_first_move(self):
        """Make first move visible on navigation to initial position.

        Current move is always made visible but no current move defined
        for initial position.
        """
        self.score.see(START_SCORE_MARK)

    def set_game_board(self):
        """Show position after highlighted move and return True if it exists.

        True means further processing appropriate to a game score can be done,
        while None means a problem occurred and the first position in score
        is displayed as a default.

        The setup_game_board() in AnalysisScore always returns False.

        """
        if self.current is None:
            try:
                self.board.set_board(self.fen_tag_square_piece_map())
            except ScoreNoGameException:
                return False
            self.see_first_move()
        else:
            try:
                self.board.set_board(self.tagpositionmap[self.current][0])
            except TypeError:
                self.board.set_board(self.fen_tag_square_piece_map())
                self.score.see(self.score.tag_ranges(self.current)[0])
                return None
            self.score.see(self.score.tag_ranges(self.current)[0])
        self.set_game_list()
        return True

    def clear_current_range(self):
        """Remove existing MOVE_TAG ranges."""
        tag_range = self.score.tag_ranges(MOVE_TAG)
        if tag_range:
            self.score.tag_remove(MOVE_TAG, tag_range[0], tag_range[1])

    def clear_moves_played_in_variation_colouring_tag(self):
        """Clear the colouring tag for moves played in variation."""
        self.score.tag_remove(VARIATION_TAG, "1.0", tkinter.END)

    def clear_choice_colouring_tag(self):
        """Clear the colouring tag for variation choice."""
        self.score.tag_remove(ALTERNATIVE_MOVE_TAG, "1.0", tkinter.END)

    def clear_variation_colouring_tag(self):
        """Clear the colouring tag for moves in variation."""
        self.score.tag_remove(LINE_TAG, "1.0", tkinter.END)
        self.score.tag_remove(LINE_END_TAG, "1.0", tkinter.END)

    def get_position_for_current(self):
        """Return position associated with the current range."""
        if self.current is None:
            return self.tagpositionmap[None]
        return self.get_position_for_text_index(
            self.score.tag_ranges(self.current)[0]
        )

    def get_position_for_text_index(self, index):
        """Return position associated with index in game score text widget."""
        tagpositionmap = self.tagpositionmap
        for tag in self.score.tag_names(index):
            if tag in tagpositionmap:
                return tagpositionmap[tag]
        return None

    def get_position_key(self):
        """Return position key string for position associated with current."""
        try:

            # Hack.  get_position_for_current returns None on next/prev token
            # navigation at end of imported game with errors when editing.
            return get_position_string(*self.get_position_for_current())

        except TypeError:
            return False

    def set_current(self):
        """Remove existing MOVE_TAG ranges and add self.currentmove ranges.

        Subclasses may adjust the MOVE_TAG range if the required colouring
        range of the item is different.  For example just <text> in {<text>}
        which is a PGN comment where <text> may be null after editing.

        The adjusted range must be a subset of self.currentmove range.

        """
        # Superclass set_current method may adjust bindings so do not call
        # context independent binding setup methods after this method for
        # an event.
        tag_range = self.set_current_range()
        if tag_range:
            self.set_move_tag(tag_range[0], tag_range[1])
            return tag_range
        return None

    def set_current_range(self):
        """Remove existing MOVE_TAG ranges and add self.currentmove ranges.

        Subclasses may adjust the MOVE_TAG range if the required colouring
        range of the item is different.  For example just <text> in {<text>}
        which is a PGN comment where <text> may be null after editing.

        The adjusted range must be a subset of self.currentmove range.

        """
        self.clear_current_range()
        if self.current is None:
            return None
        tag_range = self.score.tag_ranges(self.current)
        if not tag_range:
            return None
        return tag_range

    def set_move_tag(self, start, end):
        """Add range start to end to MOVE_TAG (which is expected to be empty).

        Assumption is that set_current_range has been called and MOVE_TAG is
        still empty following that call.

        """
        self.score.tag_add(MOVE_TAG, start, end)

    def show_new_current(self, new_current=None):
        """Set current to new item and adjust display."""
        self.clear_moves_played_in_variation_colouring_tag()
        self.clear_choice_colouring_tag()
        self.clear_variation_colouring_tag()
        self.current = new_current
        self.set_current()
        self.set_game_board()
        return "break"

    def show_item(self, new_item=None):
        """Display new item if not None."""
        if not new_item:
            return "break"
        return self.show_new_current(new_current=new_item)

    def set_game_list(self):
        """Display list of records in grid.

        Called after each navigation event on a game including switching from
        one game to another.

        """
        grid = self.itemgrid
        if grid is None:
            return
        if grid.get_database() is not None:
            newpartialkey = self.get_position_key()
            if grid.partial != newpartialkey:
                grid.partial = newpartialkey
                grid.rows = 1
                grid.close_client_cursor()
                grid.datasource.get_full_position_games(newpartialkey)
                grid.load_new_index()

    def add_move_to_moves_played_colouring_tag(self, move):
        """Add move to colouring tag for moves played in variation."""
        widget = self.score
        tag_range = widget.tag_nextrange(move, "1.0")
        widget.tag_add(VARIATION_TAG, tag_range[0], tag_range[1])

    def is_index_in_main_line(self, index):
        """Return True if index is in the main line tag."""
        return bool(
            self.score.tag_nextrange(
                self.gamevartag, index, "".join((str(index), "+1 chars"))
            )
        )

    def is_move_in_main_line(self, move):
        """Return True if move is in the main line."""
        return self.is_index_in_main_line(self.score.tag_ranges(move)[0])

    def add_variation_before_move_to_colouring_tag(self, move):
        """Add variation before current move to moves played colouring tag."""
        widget = self.score
        index = widget.tag_nextrange(move, "1.0")[0]
        for ctn in widget.tag_names(index):
            if ctn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(ctn, "1.0", index)
                while tag_range:
                    widget.tag_add(VARIATION_TAG, tag_range[0], tag_range[1])
                    tag_range = widget.tag_nextrange(ctn, tag_range[1], index)
                return

    def select_first_move_in_line(self, move):
        """Return tag name for first move in rav containing move."""
        widget = self.score
        tag_range = widget.tag_ranges(move)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(oldtn, "1.0")
                break
        else:
            return None
        if not tag_range:
            return move
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def get_choice_tag_of_index(self, index):
        """Return Tk tag name if index is in a choice tag."""
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(CHOICE):
                return tag_name
        return None

    def get_choice_tag_of_move(self, move):
        """Return Tk tag name if move is first move of a variation choice."""
        if move:
            return self.get_choice_tag_of_index(self.score.tag_ranges(move)[0])
        return None

    @staticmethod
    def get_selection_tag_for_choice(choice):
        """Return Tk tag name for selection with same suffix as choice."""
        return "".join((SELECTION, choice[len(CHOICE) :]))

    def _add_tag_ranges_to_color_tag(self, tag, colortag):
        """Add the index ranges in tag to colortag.

        Tkinter Text.tag_add() takes two indicies as arguments rather than
        the list of 2n indicies, for n ranges, accepted by Tk tag_add.
        So do it a long way.

        """
        add = self.score.tag_add
        tag_range = list(self.score.tag_ranges(tag))
        while tag_range:
            start = tag_range.pop(0)
            end = tag_range.pop(0)
            add(colortag, start, end)

    def add_currentmove_variation_to_colouring_tag(self):
        """Add current move variation to selected variation colouring tag."""
        widget = self.score
        for tag_name in widget.tag_names(
            widget.tag_nextrange(self.current, "1.0")[0]
        ):
            if tag_name.startswith(RAV_SEP):
                self._add_tag_ranges_to_color_tag(tag_name, LINE_TAG)
                widget.tag_add(
                    LINE_END_TAG,
                    "".join(
                        (
                            str(
                                widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]
                            ),
                            "-1 chars",
                        )
                    ),
                )
                return

    def apply_colouring_to_variation_back_to_main_line(self):
        """Apply colouring as if move navigation used to reach current move.

        Used in point and click navigation and when exiting token navigation
        to resume move navigation.  It is assumed that no colouring is applied
        to moves (compare with move navigation where incremental colouring
        occurs).

        """
        if self.current is None:
            return
        move = self.current
        if not self.is_move_in_main_line(move):
            self.add_currentmove_variation_to_colouring_tag()
        while not self.is_move_in_main_line(move):
            self.add_move_to_moves_played_colouring_tag(move)
            self.add_variation_before_move_to_colouring_tag(move)
            first_move_of_variation = self.select_first_move_in_line(move)
            choice = self.get_choice_tag_of_move(first_move_of_variation)
            prior = self.score.tag_ranges(
                self.get_prior_tag_for_choice(choice)
            )
            if not prior:
                move = None
                break
            move = self.get_position_tag_of_index(prior[0])
            selection = self.get_selection_tag_for_choice(choice)
            if selection:
                self.score.tag_remove(selection, "1.0", tkinter.END)
                self.score.tag_add(
                    selection, *self.score.tag_ranges(first_move_of_variation)
                )
        if self.score.tag_nextrange(VARIATION_TAG, "1.0"):
            if move:
                self.add_move_to_moves_played_colouring_tag(move)

    # If pointer click location is between last PGN Tag and first move in
    # movetext, it would be reasonable to allow the call to reposition at
    # start of game.  Then there is a pointer click option equivalent to
    # the popup menu and keypress ways of getting to start of game.
    def go_to_move(self, index):
        """Show position for move text at index."""
        widget = self.score
        move = widget.tag_nextrange(NAVIGATE_MOVE, index)
        if not move:
            move = widget.tag_prevrange(NAVIGATE_MOVE, index)
            if not move:
                return None
            if widget.compare(move[1], "<", index):
                return None
        elif widget.compare(move[0], ">", index):
            move = widget.tag_prevrange(NAVIGATE_MOVE, move[0])
            if not move:
                return None
            if widget.compare(move[1], "<", index):
                return None
        selected_move = self.get_position_tag_of_index(index)
        if selected_move:
            self.clear_moves_played_in_variation_colouring_tag()
            self.clear_choice_colouring_tag()
            self.clear_variation_colouring_tag()
            self.current = selected_move
            self.set_current()
            self.apply_colouring_to_variation_back_to_main_line()
            self.set_game_board()
            return True
        return None

    def go_to_token(self, event=None):
        """Highlight token at pointer in active item, and set position."""
        if self.items.is_mapped_panel(self.panel):
            if self is not self.items.active_item:
                return "break"
        return self.go_to_move(
            self.score.index("".join(("@", str(event.x), ",", str(event.y))))
        )

    def is_game_in_text_edit_mode(self):
        """Return True if current state of score widget is 'normal'."""
        return self.score.cget("state") == tkinter.NORMAL

    def cycle_selection_tag(self, choice, selection):
        """Cycle selection one range round the choice ranges if coloured.

        The choice ranges are coloured if they are on ALTERNATIVE_MOVE_TAG.

        """
        if choice is None:
            return
        if selection is None:
            return
        widget = self.score
        choice_tnr = widget.tag_nextrange(choice, "1.0")
        if not choice_tnr:
            return
        if not widget.tag_nextrange(ALTERNATIVE_MOVE_TAG, choice_tnr[0]):
            return
        selection_tnr = widget.tag_nextrange(
            choice, widget.tag_nextrange(selection, "1.0")[1]
        )
        widget.tag_remove(selection, "1.0", tkinter.END)
        if selection_tnr:
            widget.tag_add(selection, selection_tnr[0], selection_tnr[1])
        else:
            widget.tag_add(selection, choice_tnr[0], choice_tnr[1])

    def get_prior_to_variation_tag_of_index(self, index):
        """Return Tk tag name if index is in a prior to variation tag."""
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(PRIOR_MOVE):
                return tag_name
        return None

    def get_colouring_variation_tag_of_index(self, index):
        """Return Tk tag name if index is in a varsep tag.

        RAV_SEP for colouring (RAV_MOVES for editing).

        """
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(RAV_SEP):
                return tag_name
        return None

    @staticmethod
    def get_choice_tag_for_prior(prior):
        """Return Tk tag name for choice with same suffix as prior."""
        return "".join((CHOICE, prior[len(PRIOR_MOVE) :]))

    @staticmethod
    def get_selection_tag_for_prior(prior):
        """Return Tk tag name for selection with same suffix as prior."""
        return "".join((SELECTION, prior[len(PRIOR_MOVE) :]))

    def is_variation_entered(self):
        """Return True if currentmove is, or about to be, in variation.

        Colour tag LINE_TAG will contain at least one range if a variation
        has been entered; in particular when self.currentmove is about to
        be set to the first move of the variation at which point no other
        way of determining this is easy.  In fact LINE_TAG is populated
        ahead of time in this case to enable the test.

        """
        if self.score.tag_nextrange(LINE_TAG, "1.0"):
            return True
        return False

    def get_position_tag_of_previous_move(self):
        """Return name of tag of move played prior to current move in line.

        Assumes self.currentmove has been removed from VARIATION_TAG.

        """
        widget = self.score
        tag_range = widget.tag_prevrange(VARIATION_TAG, tkinter.END)
        if not tag_range:

            # Should be so just for variations on the first move of game
            return None

        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def set_next_variation_move_played_colouring_tag(self, move):
        """Add range from selected variation for move to moves played tag.

        Used at start of game when no move has been played.

        Find the range in the selected variation (RAV_SEP) corresponding to
        the range of move (usually the current move except at start of game)
        and add it to the colouring tag (VARIATION_TAG) for moves played in
        the selected variation leading to the current move.  It is assumed
        self.set_current() will be called to change the current move,
        including the colouring tag (MOVE_TAG), exposing this setting.

        self.set_current uses the existence of a range in VARIATION_TAG
        to decide if the current move is in the main line of the game.

        """
        widget = self.score
        for vtn in widget.tag_names(widget.tag_nextrange(move, "1.0")[0]):
            if vtn.startswith(RAV_SEP):
                tag_range = widget.tag_nextrange(
                    NAVIGATE_MOVE, widget.tag_nextrange(vtn, "1.0")[0]
                )
                widget.tag_add(VARIATION_TAG, tag_range[0], tag_range[1])
                break

    def _remove_tag_ranges_from_color_tag(self, tag, colortag):
        """Remove the index ranges in tag from colortag.

        Tkinter Text.tag_add() takes two indicies as arguments rather than
        the list of 2n indicies, for n ranges, accepted by Tk tag_remove.
        So do it a long way.

        """
        remove = self.score.tag_remove
        tag_range = list(self.score.tag_ranges(tag))
        while tag_range:
            start = tag_range.pop(0)
            end = tag_range.pop(0)
            remove(colortag, start, end)

    def select_move_for_start_of_analysis(self, movetag=MOVE_TAG):
        """Return name of tag for move to which analysis will be attached.

        Differs from select_next_move_in_line() by returning None if at last
        position in line or game, rather than self.current.

        """
        widget = self.score
        tag_range = widget.tag_ranges(movetag)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(
                    oldtn, "".join((str(tag_range[0]), "+1 chars"))
                )
                break
        else:
            return None
        if not tag_range:
            return None
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def colour_variation(self, move):
        """Colour variation and display its initial position.

        The current move is coloured to indicate it is a move played to reach
        the position in the variation.  Colour is removed from any moves to
        enter alternative variations.  The move played to enter the variation
        becomes the current move and is coloured to indicate that it is in a
        variation.

        """
        if move is None:

            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self.get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            selection = self.get_selection_tag_for_choice(choice)

        else:
            prior = self.get_prior_to_variation_tag_of_move(move)
            choice = self.get_choice_tag_for_prior(prior)
            selection = self.get_selection_tag_for_prior(prior)
        self.clear_variation_choice_colouring_tag(choice)
        selected_first_move = self.select_first_move_of_selected_line(
            selection
        )
        if self.is_move_in_main_line(selected_first_move):
            self.clear_moves_played_in_variation_colouring_tag()
            self.clear_variation_colouring_tag()
        elif move is None:
            self.set_next_variation_move_played_colouring_tag(selection)
        else:
            self.add_move_to_moves_played_colouring_tag(move)
        self.current = selected_first_move
        self.set_current()
        self.set_game_board()

    def see_current_move(self):
        """Make current move visible and default to first move."""
        if self.current:
            self.score.see(self.score.tag_ranges(self.current)[0])
        else:
            self.see_first_move()

    def step_one_variation(self, move):
        """Highlight next variation in choices at current position."""
        if move is None:

            # No prior to variation tag exists: no move to attach it to.
            prior = None
            choice = self.get_choice_tag_of_move(
                self.select_first_move_of_game()
            )
            selection = self.get_selection_tag_for_choice(choice)

        else:
            prior = self.get_prior_to_variation_tag_of_move(move)
            choice = self.get_choice_tag_for_prior(prior)
            selection = self.get_selection_tag_for_prior(prior)

        # if choices are already on ALTERNATIVE_MOVE_TAG cycle selection one
        # place round choices before getting colouring variation tag.
        self.cycle_selection_tag(choice, selection)

        variation = self.get_colouring_variation_tag_for_selection(selection)
        self.set_variation_selection_tags(prior, choice, selection, variation)
        return variation

    def clear_variation_choice_colouring_tag(self, first_moves_in_variations):
        """Remove ranges in first_moves_in_variations from colour tag.

        The colour tag is ALTERNATIVE_MOVE_TAG which should contain just the
        ranges that exist in first_moves_in_variation.  However do what the
        headline says rather than delete everything in an attempt to ensure
        correctness.

        """
        self._remove_tag_ranges_from_color_tag(
            first_moves_in_variations, ALTERNATIVE_MOVE_TAG
        )

    def get_range_next_move_in_variation(self):
        """Return range of move after current move in variation."""
        if self.current is None:
            tnr = self.score.tag_nextrange(NAVIGATE_MOVE, "1.0")
            if tnr:
                return tnr
            return None
        return self._get_range_next_move_in_variation()

    def get_current_move_context(self):
        """Return the previous current and next positions in line.

        Alternative next moves in sub-variations are not included.

        """
        # This method gets called once for each game listed in the games
        # containing the current position.  An alternative is to pass these
        # values in the 'set partial key' route for the the grid which is
        # one call.
        try:
            prevpos = self.tagpositionmap[
                self.previousmovetags[self.current][0]
            ]
        except KeyError:

            # The result at the end of an editable game score for example
            prevpos = None

        currpos = self.tagpositionmap[self.current]
        npc = self.nextmovetags.get(self.current)
        if npc is None:
            nextpos = None
        else:
            try:
                nextpos = self.tagpositionmap[npc[0]]
            except KeyError:
                nextpos = None
        return (prevpos, currpos, nextpos)

    def get_prior_to_variation_tag_of_move(self, move):
        """Return Tk tag name if currentmove is prior to a variation."""
        return self.get_prior_to_variation_tag_of_index(
            self.score.tag_ranges(move)[0]
        )

    def get_colouring_variation_tag_for_selection(self, selection):
        """Return Tk tag name for variation associated with selection."""
        return self.get_colouring_variation_tag_of_index(
            self.score.tag_ranges(selection)[0]
        )

    def get_current_tag_and_mark_names(self):
        """Return suffixed POSITION and TOKEN tag and TOKEN_MARK mark names."""
        suffix = str(self.position_number)
        return ["".join((t, suffix)) for t in (POSITION, TOKEN, TOKEN_MARK)]

    def get_tag_and_mark_names(self):
        """Return suffixed POSITION and TOKEN tag and TOKEN_MARK mark names.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        A TOKEN_MARK name is generated for each token but the mark will be
        created only for editable tokens.

        """
        self.position_number += 1
        suffix = str(self.position_number)
        return ["".join((t, suffix)) for t in (POSITION, TOKEN, TOKEN_MARK)]

    def is_currentmove_in_main_line(self):
        """Return True if currentmove is in the main line tag."""
        return self.is_index_in_main_line(
            self.score.tag_ranges(self.current)[0]
        )

    def is_currentmove_start_of_variation(self):
        """Return True if currentmove is at start of a variation tag."""
        widget = self.score
        index = widget.tag_ranges(self.current)[0]
        for tag_name in widget.tag_names(index):
            if tag_name.startswith(RAV_SEP):
                return not bool(self.score.tag_prevrange(tag_name, index))
        return None

    def is_index_of_variation_next_move_in_choice(self):
        """Return True if index is in a choice of variations tag."""
        tag_range = self.get_range_next_move_in_variation()
        if not tag_range:
            return False
        for tag_name in self.score.tag_names(tag_range[0]):
            if tag_name.startswith(CHOICE):
                return True
        return False

    def remove_currentmove_from_moves_played_in_variation(self):
        """Remove current move from moves played in variation colouring tag."""
        widget = self.score
        tag_range = widget.tag_nextrange(self.current, "1.0")
        widget.tag_remove(VARIATION_TAG, tag_range[0], tag_range[1])

    def select_first_move_of_game(self):
        """Return name of tag associated with first move of game."""
        widget = self.score
        try:
            index = widget.tag_nextrange(self.gamevartag, "1.0")[0]
        except IndexError:
            return None
        for tag_name in widget.tag_names(index):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_first_move_of_selected_line(self, selection):
        """Return name of tag associated with first move of line."""
        widget = self.score
        for tag_name in widget.tag_names(widget.tag_ranges(selection)[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_last_move_of_selected_line(self, selection):
        """Return name of tag associated with last move of line."""
        widget = self.score
        for tag_name in widget.tag_names(widget.tag_ranges(selection)[-2]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_last_move_played_in_game(self):
        """Return name of tag associated with last move played in game."""
        widget = self.score
        try:
            index = widget.tag_prevrange(self.gamevartag, tkinter.END)[0]
        except IndexError:
            return None
        for tag_name in widget.tag_names(index):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_last_move_in_line(self):
        """Return name of tag associated with last move in line."""
        widget = self.score
        tag_range = widget.tag_ranges(MOVE_TAG)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_prevrange(oldtn, tkinter.END)
                break
        else:
            return None
        if not tag_range:
            return self.current
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_next_move_in_line(self, movetag=MOVE_TAG):
        """Return name of tag associated with next move in line."""
        widget = self.score
        tag_range = widget.tag_ranges(movetag)
        if not tag_range:
            return None
        for oldtn in widget.tag_names(tag_range[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(
                    oldtn, "".join((str(tag_range[0]), "+1 chars"))
                )
                break
        else:
            return None
        if not tag_range:
            return self.current
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def select_prev_move_in_line(self):
        """Return name of tag associated with previous move in line."""
        widget = self.score
        oldtr = widget.tag_ranges(MOVE_TAG)
        if not oldtr:
            return None
        for oldtn in widget.tag_names(oldtr[0]):
            if oldtn.startswith(RAV_MOVES):
                tag_range = widget.tag_prevrange(oldtn, oldtr[0])
                break
        else:
            return None
        if not tag_range:
            if widget.tag_prevrange(NAVIGATE_MOVE, oldtr[0]):
                return self.current
            return None
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def set_variation_selection_tags(
        self,
        move_prior_to_choice,
        first_moves_in_variations,
        selected_first_move,
        moves_in_variation,
    ):
        """Replace existing ranges on color tags with ranges in arguments.

        The replacement is applied to the right of move_prior_to_choice,
        which is usually the same as current move.  In practice this only
        effects moves_in_variation because the moves to left of current move
        are not present unless the variation is the main line.

        """
        # ####### warning ######
        #
        # VARIATION_COLOR is the colour applied to moves up to the current
        # move in a RAV.
        # LINE_COLOR is the colour applied to moves after the selected move
        # where a choice of next moves exists.
        #
        # RAV_SEP<suffix> is the Tk tag for a set of moves to which the
        # colour LINE_COLOR may be applied.
        # VARIATION_TAG is the Tk tag for the set of moves to which the
        # colour VARIATION_COLOR may be applied.
        # RAV_MOVES<suffix> is the Tk tag for the editable characters in a
        # set of moves for which RAV_SEP<suffix> is the colouring tag.
        #
        # ######################
        #
        # Now it may be possible to use START_SCORE_MARK rather than '1.0'
        #
        # ######################

        del selected_first_move
        widget = self.score
        if move_prior_to_choice is None:
            index = "1.0"
        else:
            index = widget.tag_ranges(move_prior_to_choice)[0]

        # Remove current move from VARIATION_TAG (for show_prev_in_variation)
        if move_prior_to_choice:
            widget.tag_remove(VARIATION_TAG, index, tkinter.END)

        widget.tag_remove(ALTERNATIVE_MOVE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_END_TAG, index, tkinter.END)
        self._add_tag_ranges_to_color_tag(
            first_moves_in_variations, ALTERNATIVE_MOVE_TAG
        )
        self._add_tag_ranges_to_color_tag(moves_in_variation, LINE_TAG)

        # In all cases but one there is nothing to remove.  But if the choice
        # includes a move played in the game LINE_TAG contains all these moves
        # when the move played is the selection.
        widget.tag_remove(
            LINE_TAG,
            "1.0",
            widget.tag_nextrange(first_moves_in_variations, "1.0")[0],
        )

        widget.tag_add(
            LINE_END_TAG,
            "".join(
                (
                    str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                    "-1 chars",
                )
            ),
        )

    def set_variation_tags_from_currentmove(self):
        """Replace existing color tags ranges with those current move.

        Assumes colour tags are already set correctly for moves prior to
        current move in variation.

        """
        widget = self.score
        index = widget.tag_ranges(self.current)[0]
        widget.tag_remove(VARIATION_TAG, index, tkinter.END)
        widget.tag_remove(LINE_TAG, index, tkinter.END)
        widget.tag_remove(LINE_END_TAG, index, tkinter.END)
        self._add_tag_ranges_to_color_tag(
            self.get_colouring_variation_tag_of_index(index), LINE_TAG
        )
        widget.tag_add(
            LINE_END_TAG,
            "".join(
                (
                    str(widget.tag_prevrange(LINE_TAG, tkinter.END)[-1]),
                    "-1 chars",
                )
            ),
        )

    def _get_range_next_move_in_variation(self):
        """Return range of move after current move in variation."""
        widget = self.score
        tag_range = widget.tag_ranges(self.current)
        for tag_name in widget.tag_names(tag_range[0]):
            if tag_name.startswith(RAV_MOVES):
                tag_range = widget.tag_nextrange(
                    tag_name, "".join((str(tag_range[0]), "+1 chars"))
                )
                break
        else:
            return None
        if not tag_range:
            return None
        return tag_range

    def get_move_for_start_of_analysis(self):
        """Return PGN text of move to which analysis will be RAVs.

        Default to first move played in game, or '' if no moves played, or ''
        if current position is last in line or game.

        """
        if self.current is None:
            tag = self.select_first_move_of_game()
        else:
            tag = self.select_move_for_start_of_analysis()
        if tag is None:
            return ""
        tag_range = self.score.tag_ranges(tag)
        if not tag_range:
            return ""
        return self.score.get(*tag_range)
