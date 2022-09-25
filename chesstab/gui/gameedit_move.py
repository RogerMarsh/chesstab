# gameedit_move.py
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

from pgn_read.core.constants import (
    FEN_WHITE_ACTIVE,
)

from ..core.constants import (
    START_RAV,
    END_RAV,
)
from . import gameedit_nonmove
from .constants import (
    EDIT_RESULT,
    EDIT_MOVE,
    INSERT_RAV,
    MOVE_EDITED,
    NAVIGATE_MOVE,  # absence matters if no EDIT_... exists
    NAVIGATE_TOKEN,
    TOKEN,
    RAV_SEP,
    RAV_TAG,
    ALL_CHOICES,
    LINE_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    START_EDIT_MARK,
    END_EDIT_MARK,
    MOVES_PLAYED_IN_GAME_FONT,
    RAV_END_TAG,
    SPACE_SEP,
    RAV_START_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    FORCED_NEWLINE_TAG,
    FORCE_NEWLINE_AFTER_FULLMOVES,
    FORCED_INDENT_TAG,
)


class GameEdit(gameedit_nonmove.GameEdit):
    """Display a game with editing allowed."""

    def insert_empty_move_after_currentmove(self, event_char):
        """Insert empty NAVIGATE_MOVE range after current move.

        The empty NAVIGATE_MOVE range becomes the current move but because
        the move is not there yet, or is at best valid but incomplete, the
        position displayed on board is for the old current move.

        """
        widget = self.score
        if not self.is_currentmove_in_edit_move():
            # Likely will not happen as insert RAV is allowed in this case.
            return
        # Methods used to get variation and start designed for other, more
        # general, cases.  Extra return values ignored.
        current = self.current
        if self.current is None:
            # Assume that no moves, including incomplete or illegal, exist.
            # In other words bindings prevent getting here if they do exist.
            p_q = widget.tag_ranges(EDIT_RESULT)
            if p_q:
                widget.mark_set(
                    tkinter.INSERT, widget.index(p_q[0]) + "-1 lines lineend"
                )
                if widget.tag_prevrange(
                    NAVIGATE_TOKEN, p_q[0], widget.index(START_SCORE_MARK)
                ):
                    self.insert_forced_newline_into_text()
            else:
                widget.mark_set(tkinter.INSERT, tkinter.END)
            vartag = self.get_variation_tag_name()
            self.gamevartag = vartag
        else:
            start_current, end_current = widget.tag_ranges(self.current)
            insert_point = self.get_insertion_point_at_end_of_rav(end_current)
            if not insert_point:
                return
            vartag = self.get_variation_tag_of_index(start_current)
            widget.mark_set(tkinter.INSERT, insert_point)

        self.get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self.get_current_tag_and_mark_names()
        tpm = self.tagpositionmap
        tpm[positiontag] = tpm[self.current]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        if tpmpt[1] == FEN_WHITE_ACTIVE:
            tpr = widget.tag_prevrange(FORCED_NEWLINE_TAG, tkinter.INSERT)
            if not tpr:
                tpr = [widget.index(START_SCORE_MARK)]
            tpr = tpr[0]
            tr_q = widget.tag_ranges(NAVIGATE_MOVE)
            tri = 0
            for ti_q in tr_q:
                if widget.compare(ti_q, ">=", tkinter.INSERT):
                    break
                if widget.compare(ti_q, ">", tpr):
                    tri += 1
            if tri >= FORCE_NEWLINE_AFTER_FULLMOVES * 4:
                self.insert_forced_newline_into_text()
            start, end, sepend = self.insert_token_into_text(
                str(tpmpt[5]) + ".", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        for tag in (
            positiontag,
            vartag,
            NAVIGATE_MOVE,
            NAVIGATE_TOKEN,
            MOVE_EDITED,
            FORCED_INDENT_TAG,
        ):
            widget.tag_add(tag, start, end)
        if self.current is not None:
            widget.tag_remove(EDIT_MOVE, start_current, end_current)
            widget.tag_add(INSERT_RAV, start_current, end_current)
        if vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        if widget.tag_ranges(LINE_TAG):
            widget.tag_remove(LINE_END_TAG, end_current, start)
            widget.tag_add(LINE_END_TAG, end, sepend)
            widget.tag_add(LINE_TAG, start, sepend)
        self.previousmovetags[positiontag] = (current, vartag, vartag)
        self.nextmovetags[current] = [positiontag, []]

    def insert_empty_rav_after_next_move(self, event_char):
        """Insert "(<event_char>)" after move after current move.

        Both the current move and the move after may already have RAVs which
        are their alternatives.  The insert is before any RAVs which are
        alternatives for the move after current move.

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        current = self.current
        choice = None
        if self.current is None:
            # Insert RAV after first move of game
            prior = None
            choice, range_ = self.get_choice_tag_and_range_of_first_move()
            if not choice:
                choice = self.get_choice_tag_name()
            variation = self.get_variation_tag_of_index(range_[0])
            nextmove = widget.tag_nextrange(variation, range_[0])
        else:
            # Insert RAV after move after current move
            prior, range_ = self.get_prior_tag_and_range_of_move(self.current)
            if prior:
                choice = self.get_choice_tag_for_prior(prior)
            else:
                choice = self.get_choice_tag_name()
                prior = self.get_prior_tag_for_choice(choice)
            variation = self.get_variation_tag_of_index(range_[0])
            nextmove = widget.tag_nextrange(variation, range_[-1])

        # Figure point where the new empty RAV should be inserted.
        ctr = widget.tag_ranges(choice)
        if ctr:
            point = widget.tag_ranges(
                self.get_rav_tag_for_rav_moves(
                    self.get_rav_moves_of_index(ctr[2])
                )
            )[0]
        else:
            # No existing RAVs for the next move.
            for tn_q in variation, RAV_END_TAG, EDIT_RESULT:
                tr_q = widget.tag_nextrange(tn_q, nextmove[1])
                if tr_q:
                    point = tr_q[0]
            # pylint message useless-else-on-loop not resolved lest a crash
            # is introduced to replace presumed, but unnoticed, incorrect
            # behaviour.
            else:
                # Can keep going, but both raise exception and issue warning
                # dialogue are better options here.
                point = widget.index(nextmove[1] + "+1char")
        colourvariation = "".join((RAV_SEP, variation))

        # Apply choice tags to next move if not already done, implied by
        # absence of existing RAVs for move.
        if prior is None:
            # no prior move for initial position of game.
            # Seems ok to just set these tags even if already set.
            widget.tag_add(ALL_CHOICES, *nextmove)
            widget.tag_add(choice, *nextmove)
        # Why not just test 'ctr' which is already set?
        elif not ctr:  # widget.tag_nextrange(prior, '1.0'):
            assert bool(ctr) == bool(widget.tag_nextrange(prior, "1.0"))
            # no variations exist immediately after current move so set up
            # variation choice structures.  map_insert_rav cannot do this as
            # it assumes variation structure exists, if at all, for preceding
            # moves only.
            if self.current:
                widget.tag_add(prior, *widget.tag_ranges(self.current))
            widget.tag_add(ALL_CHOICES, *nextmove)
            widget.tag_add(choice, *nextmove)

        widget.mark_set(tkinter.INSERT, point)
        # Existence of choice implies the prior forced newline is in place.
        if not ctr:
            self.insert_forced_newline_into_text()
        start, end, sepend = self.insert_token_into_text("(", SPACE_SEP)

        tpm = self.tagpositionmap
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        vartag = self.get_variation_tag_name()
        ravtag = self.get_rav_tag_name()
        if prior:
            tpm[positiontag] = tpm[self.current]
        else:
            tpm[positiontag] = tpm[None]
        widget.tag_add(tokentag, start, sepend)
        for tag in (
            ravtag,
            positiontag,
            NAVIGATE_TOKEN,
            RAV_START_TAG,
        ):
            widget.tag_add(tag, start, end)
        if prior:
            widget.tag_add(prior, start, end)
        # Insert is surrounded by tagged colourvariation text unlike add at
        # end.  This breaks the sequence so rest of inserts in this method
        # do not get tagged by colourvariation as well as ravtag.
        widget.tag_remove(colourvariation, start, sepend)
        try:
            self.previousmovetags[positiontag] = (
                self.previousmovetags[current][0],
                variation,
                variation,
            )
        except KeyError:
            self.previousmovetags[positiontag] = (None, variation, variation)

        newmovetag = self.get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self.get_current_tag_and_mark_names()
        tpm[positiontag] = tpm[self.current]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        start, end, sepend = self.insert_token_into_text(
            str(tpmpt[5]) + ("." if tpmpt[1] == FEN_WHITE_ACTIVE else "..."),
            SPACE_SEP,
        )
        widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        # FORCED_INDENT_TAG is not needed, compared with
        # insert_empty_move_after_currentmove(), because this token can only
        # be first on a line due to word wrap.
        for tag in (
            positiontag,
            vartag,
            NAVIGATE_MOVE,
            ALL_CHOICES,
            self.get_selection_tag_for_choice(choice),
            choice,
            NAVIGATE_TOKEN,
            MOVE_EDITED,
        ):
            widget.tag_add(tag, start, end)

        if vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
            LINE_TAG,
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        self.previousmovetags[positiontag] = (current, vartag, variation)
        self.nextmovetags[current][1].append(positiontag)

        start, end, sepend = self.insert_token_into_text(")", SPACE_SEP)
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        tpm[positiontag] = tpm[self.nextmovetags[current][0]]
        for tag in (
            ravtag,
            positiontag,
            NAVIGATE_TOKEN,
            RAV_END_TAG,
        ):
            widget.tag_add(tag, start, end)
        if prior:
            widget.tag_add(prior, start, end)
        widget.tag_add(tokentag, start, sepend)
        self.previousmovetags[positiontag] = (current, variation, variation)
        nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, end)
        if nttnr and NAVIGATE_MOVE in widget.tag_names(nttnr[0]):
            self.insert_forced_newline_into_text()

        return newmovetag

    def insert_empty_rav_after_rav_start(self, event_char):
        """Insert "(<event_char>)" before first move or "(..)" in current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        tr_q = widget.tag_ranges(self.current)
        tn_q = widget.tag_names(tr_q[0])
        for n_q in tn_q:
            if n_q.startswith(TOKEN):
                insert_point = widget.tag_ranges(n_q)[-1]
                break
        return self.insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self.find_choice_prior_move_variation_main_move(tn_q),
            newline_before_rav=False
        )

    def insert_empty_rav_after_rav_start_move_or_rav(self, event_char):
        """Insert "(<event_char>)" after first move or "(..)" in current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        insert_point = None
        tr_q = widget.tag_ranges(self.current)
        tn_q = widget.tag_names(tr_q[0])
        nmtnr = widget.tag_nextrange(NAVIGATE_MOVE, tr_q[-1])
        rstnr = widget.tag_nextrange(RAV_START_TAG, tr_q[-1])
        if rstnr and widget.compare(nmtnr[0], ">", rstnr[0]):
            insert_after = False
            for n_q in widget.tag_names(rstnr[0]):
                if n_q.startswith(RAV_TAG):
                    for en_q in widget.tag_names(widget.tag_ranges(n_q)[-1]):
                        if en_q.startswith(TOKEN):
                            insert_point = widget.tag_ranges(en_q)[-1]
                            break
                    break
        else:
            for n_q in widget.tag_names(nmtnr[0]):
                if n_q.startswith(TOKEN):
                    insert_point = widget.tag_ranges(n_q)[-1]
                    break
            insert_after = widget.tag_nextrange(NAVIGATE_TOKEN, insert_point)
        if insert_after:
            for n_q in widget.tag_names(insert_after[0]):
                if n_q.startswith(RAV_END_TAG):
                    insert_after = False
                    break
        return self.insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self.find_choice_prior_move_variation_main_move(tn_q),
            newline_after_rav=bool(insert_after)
        )

    def insert_empty_rav_after_rav_end(self, event_char):
        """Insert "(<event_char>)" after ")" for current "(".

        The new NAVIGATE_MOVE range becomes the current move, but because
        the move is at best valid but incomplete, the position displayed on
        board is for the move from which the variation is entered (the old
        current move).

        """
        widget = self.score
        tn_q = widget.tag_names(widget.tag_ranges(self.current)[0])
        insert_point = None
        for n_q in tn_q:
            if n_q.startswith(RAV_TAG):
                for en_q in widget.tag_names(widget.tag_ranges(n_q)[-1]):
                    if en_q.startswith(TOKEN):
                        insert_point = widget.tag_ranges(en_q)[-1]
                        break
                break
        return self.insert_rav_at_insert_point(
            event_char,
            insert_point,
            *self.find_choice_prior_move_variation_main_move(tn_q),
            newline_after_rav=False
        )

    def delete_empty_move(self):
        """Delete empty move from PGN movetext and RAV if it is empty too."""
        widget = self.score
        if widget.count(START_EDIT_MARK, END_EDIT_MARK)[0] > 1:
            return
        tr_q = widget.tag_ranges(self.get_token_tag_for_position(self.current))
        if not tr_q:
            return
        if self.is_currentmove_in_main_line():
            current = self.select_prev_move_in_line()
            delete_rav = False
        elif self.is_currentmove_start_of_variation():
            choice = self.get_choice_tag_of_index(tr_q[0])
            prior = self.get_prior_tag_for_choice(choice)
            try:
                current = self.get_position_tag_of_index(
                    widget.tag_ranges(prior)[0]
                )
            except IndexError:
                current = None

            # First range in choice is a move in main line relative to RAV.
            # For first move do not highlight main line when no RAVs exist
            # after deletion of this one.
            # At other moves main line does not get highlighted when any RAV
            # is deleted, because there is a move to make current before the
            # move choices.
            if current or len(widget.tag_ranges(choice)) > 4:
                self.step_one_variation_select(current)
                selection = self.get_selection_tag_for_prior(prior)
                sr_q = widget.tag_nextrange(
                    choice, widget.tag_ranges(selection)[1]
                )
                if sr_q:
                    widget.tag_add(selection, *sr_q)
                else:
                    widget.tag_add(
                        selection, *widget.tag_nextrange(choice, "1.0")[:2]
                    )
            delete_rav = True
        else:
            current = self.select_prev_move_in_line()
            delete_rav = False
        move_number_indicator = widget.tag_prevrange(
            MOVETEXT_MOVENUMBER_TAG,
            tr_q[0],
            widget.tag_ranges(current)[-1] if current else "1.0",
        )
        if delete_rav:
            ravtag = self.get_rav_tag_for_rav_moves(
                self.get_variation_tag_of_index(tr_q[0])
            )
            # Tkinter.Text.delete does not support multiple ranges at
            # Python 2.7.1 so call delete for each range from highest to
            # lowest.  Perhaps put a hack in workarounds?
            widget.delete(
                *widget.tag_ranges(
                    self.get_token_tag_of_index(
                        widget.tag_nextrange(
                            RAV_END_TAG,
                            widget.tag_prevrange(ravtag, tkinter.END)[0],
                        )[0]
                    )
                )
            )
            widget.delete(tr_q[0], tr_q[1])
            if move_number_indicator:
                widget.delete(*move_number_indicator)
            widget.delete(
                *widget.tag_ranges(
                    self.get_token_tag_of_index(
                        widget.tag_nextrange(ravtag, "1.0")[0]
                    )
                )
            )

            # This should be a method for newlines before and after RAV,
            # perhaps called before the two preceding deletes.
            self.delete_forced_newlines_adjacent_to_rav(tr_q)

        else:
            widget.delete(tr_q[0], tr_q[1])
            if move_number_indicator:
                widget.delete(*move_number_indicator)
            self.delete_forced_newline_token_prefix(NAVIGATE_MOVE, tr_q)
        del self.edit_move_context[self.current]
        del self.tagpositionmap[self.current]
        self.current = current
        if delete_rav:
            ci_q = widget.tag_nextrange(choice, "1.0")[0]
            if widget.compare(
                ci_q, "==", widget.tag_prevrange(choice, tkinter.END)[0]
            ):
                widget.tag_remove(
                    ALL_CHOICES, *widget.tag_nextrange(ALL_CHOICES, ci_q)
                )
                widget.tag_delete(
                    choice, prior, self.get_selection_tag_for_prior(prior)
                )
            self.clear_choice_colouring_tag()
            self.set_current()
            if self.current is not None and widget.tag_ranges(self.current):
                self.apply_colouring_to_variation_back_to_main_line()
        elif self.current is None:
            nttpr = widget.tag_prevrange(
                NAVIGATE_TOKEN, tkinter.END, widget.index(START_SCORE_MARK)
            )
            if nttpr:
                fnltpr = widget.tag_prevrange(
                    FORCED_NEWLINE_TAG,
                    tkinter.END,
                    widget.index(START_SCORE_MARK),
                )
                if fnltpr and widget.compare(fnltpr[0], ">", nttpr[-1]):
                    widget.delete(*fnltpr)
            self.set_current()
        else:
            start, end = widget.tag_ranges(self.current)
            widget.tag_add(EDIT_MOVE, start, end)
            widget.tag_remove(INSERT_RAV, start, end)
            if widget.tag_ranges(LINE_TAG):
                widget.tag_add(LINE_END_TAG, end, end)
            self.set_current()
        self.set_game_board()

    def insert_rav_at_insert_point(
        self,
        event_char,
        insert_point,
        choice,
        prior_move,
        variation_containing_choice,
        main_line_move,
        newline_before_rav=True,
        newline_after_rav=True,
    ):
        """Insert RAV at insert_point with event_char as first character.

        event_char is a charcter valid in a move in movetext.
        insert_point is the index at which the RAV is to be inserted.
        choice is the tag which tags the alternative moves, including the
        main line move, at this point.  The index range of event_char is
        added to choice.
        prior_move is the tag which tags the main line move and all the
        start and end RAV markers for the alternative replies to the main
        line move.
        variation_containing_choice is the tag which tags all the moves in
        the line containing the RAV.  It can be a RAV itself.
        main_line_move tags 'm1' in '.. m1 m2 (m3 ..) (m4 ..) ..', a PGN-like
        sequence.
        newline_before_rav indicates whether to insert a newline before RAV.
        newline_after_rav indicates whether to insert a newline after RAV.

        The newline flags are intended to control newlines in sequences of
        start RAV or end RAV markers not interrupted by other tokens.

        It is assumed the choice, prior_move, variation_containing_choice,
        and main_line_move, arguments have been calculated by
        find_choice_prior_move_variation_main_move().

        """
        # If choice is not a tag name there is something wrong: do nothing.
        if not choice:
            return None

        widget = self.score

        # Move insert_point over any non-move and non-RAV marker tokens
        # before nearest of next move and RAV marker tokens.
        nttpr = widget.tag_prevrange(
            NAVIGATE_TOKEN,
            self.get_nearest_in_tags_between_point_and_end(
                insert_point,
                (
                    NAVIGATE_MOVE,
                    MOVETEXT_MOVENUMBER_TAG,
                    RAV_START_TAG,
                    RAV_END_TAG,
                    EDIT_RESULT,
                ),
            ),
            insert_point,
        )
        if nttpr:
            for n_q in widget.tag_names(nttpr[-1]):
                if n_q.startswith(TOKEN):
                    insert_point = widget.tag_ranges(n_q)[-1]
                    break
            else:
                insert_point = nttpr[-1]

        widget.mark_set(tkinter.INSERT, insert_point)
        if newline_before_rav:
            self.insert_forced_newline_into_text()
        start, end, sepend = self.insert_token_into_text("(", SPACE_SEP)
        tpm = self.tagpositionmap
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        vartag = self.get_variation_tag_name()
        ravtag = self.get_rav_tag_name()
        tpm[positiontag] = tpm[main_line_move if prior_move else None]
        widget.tag_add(tokentag, start, sepend)
        for tag in (ravtag, positiontag, NAVIGATE_TOKEN, RAV_START_TAG):
            widget.tag_add(tag, start, end)
        if prior_move:
            widget.tag_add(prior_move, start, end)
        # Is colourvariation wrong in insert_empty_rav_after_next_move()?
        # There is no 'rsrmN' tag so colourvariation is not propogated.
        # The colourvariation stuff is missing compared with
        # insert_empty_rav_after_next_move().
        self.previousmovetags[positiontag] = (
            self.previousmovetags[main_line_move][0] if prior_move else None,
            variation_containing_choice,
            variation_containing_choice,
        )
        newmovetag = self.get_next_positiontag_name()
        (
            positiontag,
            tokentag,
            tokenmark,
        ) = self.get_current_tag_and_mark_names()
        tpm[positiontag] = tpm[main_line_move if prior_move else None]
        self.edit_move_context[positiontag] = self.create_edit_move_context(
            positiontag
        )
        tpmpt = tpm[positiontag]
        start, end, sepend = self.insert_token_into_text(
            str(tpmpt[5]) + ("." if tpmpt[1] == FEN_WHITE_ACTIVE else "..."),
            SPACE_SEP,
        )
        widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
        widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(event_char, SPACE_SEP)

        # event_char and separator will have been tagged for elide by enclosure
        # if it is a black move.  The indentation tag too, but that is needed.
        widget.tag_remove(MOVETEXT_MOVENUMBER_TAG, start, sepend)

        # FORCED_INDENT_TAG is not needed, compared with
        # insert_empty_move_after_currentmove(), because this token can only
        # be first on a line due to word wrap.
        for tag in (
            positiontag,
            vartag,
            NAVIGATE_MOVE,
            ALL_CHOICES,
            self.get_selection_tag_for_choice(choice),
            choice,
            NAVIGATE_TOKEN,
            MOVE_EDITED,
        ):
            widget.tag_add(tag, start, end)

        if vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        for tag in (
            tokentag,
            "".join((RAV_SEP, vartag)),
            LINE_TAG,
        ):
            widget.tag_add(tag, start, sepend)
        widget.mark_set(tokenmark, end)
        self.previousmovetags[positiontag] = (
            main_line_move,
            vartag,
            variation_containing_choice,
        )
        self.nextmovetags[main_line_move][1].append(positiontag)
        start, end, sepend = self.insert_token_into_text(")", SPACE_SEP)
        positiontag, tokentag, tokenmark = self.get_tag_and_mark_names()
        tpm[positiontag] = tpm[self.nextmovetags[main_line_move][0]]
        for tag in (
            ravtag,
            self.get_rav_tag_for_rav_moves(variation_containing_choice),
            positiontag,
            NAVIGATE_TOKEN,
            RAV_END_TAG,
        ):
            widget.tag_add(tag, start, end)
        if prior_move:
            widget.tag_add(prior_move, start, end)
        widget.tag_add(tokentag, start, sepend)
        self.previousmovetags[positiontag] = (
            main_line_move,
            variation_containing_choice,
            variation_containing_choice,
        )
        if newline_after_rav:
            self.insert_forced_newline_into_text()

        return newmovetag

    def get_insertion_point_at_end_of_rav(self, insert_point_limit):
        """Return insertion point for new move at end of RAV.

        insert_point_limit is the earliest point in the score at which the
        new move can be inserted and will usually be the index of the last
        character of the move before the new move.

        The possible situations before the new move is inserted are:

        ... move )
        ... move ( moves ) )
        ... move comment )
        ... move <ravs and comments in any order> )

        The final ) can be 1-0, 0-1, 1/2-1/2, or * instead: one of the
        termination symbols.

        The sequence ( moves ) is the simplest example of a RAV.

        The insertion point for the new move is just before the final ).

        """
        widget = self.score
        end_rav = widget.tag_nextrange(RAV_END_TAG, insert_point_limit)
        next_move = widget.tag_nextrange(NAVIGATE_MOVE, insert_point_limit)
        if not end_rav:
            point = widget.tag_nextrange(EDIT_RESULT, insert_point_limit)
            if not point:
                return widget.index(tkinter.END)
            nttpr = widget.tag_prevrange(NAVIGATE_TOKEN, point[0])
            widget.mark_set(
                tkinter.INSERT, widget.index(point[0]) + "-1 lines lineend"
            )
            if NAVIGATE_MOVE not in widget.tag_names(nttpr[0]):
                self.insert_forced_newline_into_text()
            return widget.index(tkinter.INSERT)
        if not next_move:
            return end_rav[0]
        if widget.compare(next_move[0], ">", end_rav[0]):
            return end_rav[0]

        # In 'd4 d5 ( e5 Nf3 ) *' with current position after d5 an attempt to
        # insert a move by 'c4', say, gives 'd4 d5 ( e5 c4 Nf3 ) *' not the
        # correct 'd4 d5 ( e5 Nf3 ) c4 *'.  The position is correct but the
        # generated PGN text is wrong.
        # Fixed by stepping through adjacent variations.
        # The potential use of end_rav before binding is allowed because a next
        # range relative to self.current should exist.
        # Bug 2013-06-19 note.
        # This method had some code which attempted to solve RAV insertion
        # problem until insert_empty_rav_after_next_move() method was
        # amended with correct code on 2015-09-05.
        depth = 0
        nr_q = widget.tag_ranges(self.current)
        while True:
            nr_q = widget.tag_nextrange(NAVIGATE_TOKEN, nr_q[-1])
            if not nr_q:
                if widget.get(*end_rav) == END_RAV:
                    return widget.index(end_rav[1] + "+1char")
                widget.mark_set(tkinter.INSERT, widget.index(end_rav[1]))
                self.insert_forced_newline_into_text()
                return widget.index(tkinter.INSERT)
            end_rav = nr_q
            token = widget.get(*nr_q)
            if token == START_RAV:
                depth += 1
            elif token == END_RAV:
                depth -= 1
                if depth < 0:
                    return widget.index(end_rav[1] + "-1char")

    def delete_forced_newlines_adjacent_to_rav(self, range_):
        """Delete newlines adjacent to RAV markers to fit layout rules.

        There will be at least one move token before the RAV being deleted,
        and possibly some other tokens, including RAV start and end markers,
        too.

        """
        widget = self.score
        nttpr = widget.tag_prevrange(NAVIGATE_TOKEN, range_[0])
        for n_q in widget.tag_names(nttpr[0]):
            if n_q == RAV_START_TAG:
                nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, range_[-1])
                nltnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, range_[-1])
                if nttnr and nltnr and widget.compare(nttnr[0], ">", nltnr[0]):
                    widget.delete(*nltnr)
                break
            if n_q == RAV_END_TAG:
                nttnr = widget.tag_nextrange(NAVIGATE_TOKEN, range_[-1])
                nltnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, range_[-1])
                if nttnr:
                    while nltnr:
                        nltnnr = widget.tag_nextrange(
                            FORCED_NEWLINE_TAG, nltnr[-1]
                        )
                        if nltnnr and widget.compare(nttnr[0], ">", nltnnr[0]):
                            widget.delete(*nltnr)
                            nltnr = nltnnr
                            continue
                        break
                else:
                    while nltnr:
                        nltnnr = widget.tag_nextrange(
                            FORCED_NEWLINE_TAG, nltnr[-1]
                        )
                        if nltnnr:
                            widget.delete(*nltnr)
                        nltnr = nltnnr
                    break
        else:
            nltnr = widget.tag_nextrange(
                FORCED_NEWLINE_TAG, nttpr[-1], widget.index(tkinter.INSERT)
            )
            while nltnr:
                nltnnr = widget.tag_nextrange(FORCED_NEWLINE_TAG, nltnr[-1])
                widget.delete(nltnr[0], widget.index(tkinter.INSERT))
                nltnr = nltnnr
                continue
            nttpr = widget.tag_prevrange(
                NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
            )
            if nttpr:
                nltpr = widget.tag_prevrange(
                    FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
                )
                while nltpr:
                    nltppr = widget.tag_prevrange(
                        FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
                    )
                    if widget.compare(nttpr[0], "<", nltppr[0]):
                        widget.delete(*nltpr)
                        nltpr = nltppr
                        continue
                    break

        # If the RAV deletion has left a sequence of less than 20 fullmoves,
        # without any non-move tokens interrupting the sequence, delete any
        # forced newlines left over from the deletion.
        nttppr = widget.tag_prevrange(
            NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
        )
        if nttppr:
            for n_q in widget.tag_names(nttppr[0]):
                if n_q == NAVIGATE_MOVE:
                    break
            else:
                if widget.tag_nextrange(NAVIGATE_TOKEN, nttppr[-1]):
                    return
                self.delete_forced_newlines_adjacent_to_rav_and_termination(
                    nttppr[0]
                )
                return
        else:
            return
        nttnnr = widget.tag_nextrange(
            NAVIGATE_TOKEN, widget.index(tkinter.INSERT)
        )
        if nttnnr:
            for n_q in widget.tag_names(nttnnr[0]):
                if n_q == NAVIGATE_MOVE:
                    break
            else:
                if widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[-1]):
                    return
                self.delete_forced_newlines_adjacent_to_rav_and_termination(
                    widget.tag_prevrange(FORCED_NEWLINE_TAG, nttnnr[0])[0]
                )
                return
        else:
            return
        nltpr = widget.tag_prevrange(
            FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
        )
        if nltpr and widget.compare(nttppr[0], "<", nltpr[0]):
            nttppr = widget.tag_prevrange(NAVIGATE_TOKEN, nltppr[0])
        if not nttppr:
            return
        nltnr = widget.tag_nextrange(
            FORCED_NEWLINE_TAG, widget.index(tkinter.INSERT)
        )
        if nltnr and widget.compare(nttnnr[0], ">", nltnr[0]):
            nttnnr = widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[0])
        if not nttnnr:
            return
        count = 0
        nttpr = nttppr
        while nttppr:
            for n_q in widget.tag_names(nttppr[0]):
                if n_q == FORCED_NEWLINE_TAG:
                    break
                if n_q == NAVIGATE_MOVE:
                    count += 1
                    break
            else:
                break
            nttppr = widget.tag_prevrange(NAVIGATE_TOKEN, nttppr[0])
        nttnr = nttnnr
        while nttnnr:
            for n_q in widget.tag_names(nttnnr[0]):
                if n_q == FORCED_NEWLINE_TAG:
                    break
                if n_q == NAVIGATE_MOVE:
                    count += 1
                    break
            else:
                break
            nttnnr = widget.tag_nextrange(NAVIGATE_TOKEN, nttnnr[-1])
        if count < FORCE_NEWLINE_AFTER_FULLMOVES:
            dfnl = widget.tag_nextrange(
                FORCED_NEWLINE_TAG, nttpr[-1], nttnr[0]
            )
            if dfnl:
                widget.delete(*dfnl)

    def delete_forced_newlines_adjacent_to_rav_and_termination(self, index):
        """Delete newlines adjacent to RAV markers to fit layout rules.

        This method is called by delete_forced_newlines_adjacent_to_rav which
        is assumed to have set range_ to the final RAV end marker, ')', in a
        RAV which contained RAVs before deletion started.

        """
        widget = self.score
        while True:
            fnl = widget.tag_nextrange(FORCED_NEWLINE_TAG, index)
            if not fnl:
                break
            widget.delete(*fnl)
