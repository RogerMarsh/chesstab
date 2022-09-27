# scorewidget.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class with methods to display the score of a game of chess.

The ScoreWidget class displays text derived from PGN and highlights moves.

ScoreShow is a subclass of ScoreWidget.

The score of the game is extracted, by default, from a GameDisplayMoves
instance.  That class is defined in the core.pgn module.

"""

import tkinter

from pgn_read.core.constants import (
    SEVEN_TAG_ROSTER,
    FEN_WHITE_ACTIVE,
)

from ..core.pgn import GameDisplayMoves
from .constants import (
    LINE_COLOR,
    MOVE_COLOR,
    ALTERNATIVE_MOVE_COLOR,
    VARIATION_COLOR,
    MOVES_PLAYED_IN_GAME_FONT,
    TAGS_VARIATIONS_COMMENTS_FONT,
    NAVIGATE_MOVE,
    RAV_MOVES,
    CHOICE,
    PRIOR_MOVE,
    RAV_SEP,
    ALL_CHOICES,
    POSITION,
    MOVE_TAG,
    SELECTION,
    ALTERNATIVE_MOVE_TAG,
    LINE_TAG,
    VARIATION_TAG,
    LINE_END_TAG,
    START_SCORE_MARK,
    BUILD_TAG,
    SPACE_SEP,
    NEWLINE_SEP,
    FORCE_NEWLINE_AFTER_FULLMOVES,
    FORCED_INDENT_TAG,
    MOVETEXT_MOVENUMBER_TAG,
    FORCED_NEWLINE_TAG,
)
from .blanktext import BlankText, NonTagBind
from ._score_scaffold import _ScoreScaffold


class ScoreNoInitialPositionException(Exception):
    """Raise to indicate non-PGN text after Game Termination Marker.

    The ScoreNoInitialPositionException is intended to catch cases where a
    file claiming to be a PGN file contains text with little resemblance to
    the PGN standard between a Game Termination Marker and a PGN Tag or
    a move description like Ba4.  For example 'anytext*anytextBa4anytext'
    or 'anytext0-1anytext[tagname"tagvalue"]anytext'.

    """


class ScoreMapToBoardException(Exception):
    """Raise to indicate display of chess engine analysis for illegal move.

    In particular in the GameEdit class when the move played is the last in
    game or variation, but is being edited at the time and not complete.  It
    is caught in the AnalysisScore class but should be treated as a real
    error in the Score class.

    """


class ScoreRAVNoPriorMoveException(Exception):
    """Raise to indicate a start RAV marker does not have a prior move."""


class ScoreWidget(BlankText):
    """Areas for game score and a board for current position.

    panel is used as the panel argument for the super().__init__ call.

    board is the board.Board instance where the current position in this
    ScoreWidget instance is shown.

    tags_variations_comments_font is the font used for non-move PGN tokens,
    the default font is in class attribute tags_variations_comments_font.

    moves_played_in_game_font is the font used for non-move PGN tokens, the
    default font is in class attribute moves_played_in_game_font.

    ui is the user interface manager for an instance of ScoreWidget, usually
    an instance of ChessUI.  It is ignored and ScoreWidget instances refer
    to the board for the ui.

    items_manager is used as the items_manager argument for the
    super().__init__ call.

    itemgrid is the ui reference to the DataGrid from which the record was
    selected.

    Subclasses are responsible for providing a geometry manager.

    Attribute l_color is the background colour for a variation when it has
    the current move.

    Attribute m_color is the background colour for moves in a variation when
    it has the current move, which are before the current move.

    Attribute am_color is the background colour for moves which start other
    variations when selecting a variation.  The current choice has the colour
    specified by l_color.

    Attribute v_color is the background colour for the game move preceding
    the first move in the variation.

    Attribute tags_displayed_last is the PGN tags, in order, to be displayed
    immediately before the movetext.  It exists so Game*, Repertoire*, and
    AnalysisScore*, instances can use identical code to display PGN tags.  It
    is the PGN Seven Tag Roster.

    Attribute pgn_export_type is a tuple with the name of the type of data and
    the class used to generate export PGN.  It exists so Game*, Repertoire*,
    and AnalysisScore*, instances can use identical code to display PGN tags.
    It is ('Game', GameDisplayMoves).

    Attribute _most_recent_bindings is set to indicate the initial set of
    event bindings.  Instances will override this as required.

    """

    l_color = LINE_COLOR
    m_color = MOVE_COLOR
    am_color = ALTERNATIVE_MOVE_COLOR
    v_color = VARIATION_COLOR
    tags_variations_comments_font = TAGS_VARIATIONS_COMMENTS_FONT
    moves_played_in_game_font = MOVES_PLAYED_IN_GAME_FONT

    tags_displayed_last = SEVEN_TAG_ROSTER
    pgn_export_type = "Game", GameDisplayMoves

    # Indicate the most recent set of bindings applied to score attribute.
    # There will be some implied bindings to the board attribute, but board
    # may  be shared by more than one Score instance.  The analysis.score and
    # score attributes of a Game instance for example.
    # Values are Tk tag names or members of NonTagBind enumeration.
    _most_recent_bindings = NonTagBind.INITIAL_BINDINGS

    # Maybe do not need pgn_export_type for 'export_..' methods if repertoire
    # subclasses use gameclass=GameRepertoireDisplayMoves.
    def __init__(
        self,
        panel,
        board,
        tags_variations_comments_font=None,
        moves_played_in_game_font=None,
        gameclass=GameDisplayMoves,
        items_manager=None,
        itemgrid=None,
        **ka
    ):
        """Create widgets to display game score."""
        super().__init__(panel, items_manager=items_manager, **ka)
        self.itemgrid = itemgrid
        if tags_variations_comments_font:
            self.tags_variations_comments_font = tags_variations_comments_font
        if moves_played_in_game_font:
            self.moves_played_in_game_font = moves_played_in_game_font
        self.board = board
        self.score.configure(
            font=self.tags_variations_comments_font,
            selectbackground=self.score.cget("background"),
            inactiveselectbackground="",
        )
        self.score.tag_configure(
            MOVES_PLAYED_IN_GAME_FONT, font=self.moves_played_in_game_font
        )

        # Order is ALTERNATIVE_MOVE_TAG LINE_TAG VARIATION_TAG LINE_END_TAG
        # MOVE_TAG so that correct colour has highest priority as moves are
        # added to and removed from tags.
        self.score.tag_configure(
            ALTERNATIVE_MOVE_TAG, background=self.am_color
        )
        self.score.tag_configure(LINE_TAG, background=self.l_color)
        self.score.tag_configure(VARIATION_TAG, background=self.v_color)
        self.score.tag_configure(
            LINE_END_TAG, background=self.score.cget("background")
        )
        self.score.tag_configure(MOVE_TAG, background=self.m_color)

        # The popup menus for the game score.
        self.select_move_popup = None

        # None implies initial position and is deliberately not a valid Tk tag.
        self.current = None  # Tk tag of current move

        # These attributes replace the structure used with wxWidgets controls.
        # Record the structure by tagging text in the Tk Text widget.
        self.variation_number = 0
        self.varstack = []
        self.choice_number = 0
        self.choicestack = []
        self.position_number = 0
        self.tagpositionmap = dict()
        self.previousmovetags = dict()
        self.nextmovetags = dict()

        # PGN parser creates a gameclass instance for game data structure and
        # binds it to collected_game attribute.
        self.gameclass = gameclass
        self.collected_game = None

        self.gamevartag = None
        self._game_scaffold = None

    def fen_tag_square_piece_map(self):
        """Return square to piece mapping for position in game's FEN tag.

        The position was assumed to be the standard initial position of a game
        if there was no FEN tag.

        """
        try:
            return {
                square: piece
                for piece, square in self.collected_game._initial_position[0]
            }
        except TypeError as error:
            raise ScoreNoInitialPositionException(
                "No initial position: probably text has no PGN elements"
            ) from error

    def fen_tag_tuple_square_piece_map(self):
        """Return FEN tag as tuple with pieces in square to piece mapping."""
        cgip = self.collected_game._initial_position
        return (
            self.fen_tag_square_piece_map(),
            cgip[1],
            cgip[2],
            cgip[3],
            cgip[4],
            cgip[5],
        )

    def add_pgntag_to_map(self, name, value):
        r"""Add a PGN Tag, a name and value, to the game score.

        The PGN Tag consists of two editable tokens: the Tag name and the Tag
        value.  These are inserted and deleted together, never separately,
        formatted as [ <name> "<value>" ]\n.

        """
        widget = self.score
        widget.insert(tkinter.INSERT, "[")
        name_tag = self.add_text_pgntag_or_pgnvalue(
            "".join((" ", name)),
            tagset=(TAGS_VARIATIONS_COMMENTS_FONT,),
        )
        name_suffix = self.position_number
        value_tag = self.add_text_pgntag_or_pgnvalue(
            "".join(('"', value)),
            tagset=(TAGS_VARIATIONS_COMMENTS_FONT,),
            separator='"',
        )
        value_suffix = self.position_number
        widget.insert(tkinter.INSERT, " ]\n")
        widget.mark_set(START_SCORE_MARK, tkinter.INSERT)
        return ((name_suffix, name_tag), (value_suffix, value_tag))

    def add_text_pgntag_or_pgnvalue(self, token, separator=" ", **k):
        """Insert token and separator text. Return start and end indicies.

        token is ' 'text or '"'text.  The trailing ' ' or '"' required in the
        PGN specification is provided as separator.  The markers surrounding
        text are not editable.

        """
        del k
        return self.insert_token_into_text(token, separator)

    def build_nextmovetags(self):
        """Create next move references for all tags."""
        widget = self.score
        for this, value in self.previousmovetags.items():
            if widget.tag_nextrange(NAVIGATE_MOVE, *widget.tag_ranges(this)):
                previous, thisrav, previousrav = value
                nmt = self.nextmovetags.setdefault(previous, [None, []])
                if thisrav == previousrav:
                    nmt[0] = this
                else:
                    nmt[1].append(this)

    def get_range_of_prior_move(self, start):
        """Return range of PRIOR_MOVE tag before start.

        This method exists for use by create_previousmovetag() method so
        it can be overridden in GameEdit class.  The Score class does not
        tag '(' with a PRIOR_MOVE tag, but a route to this tag exists via
        the CHOICE tag of the nearest move before the '('.

        The GameEdit class tags '('s with a PRIOR_MOVE tag in it's extended
        map_start_rav() method, which happens to break the algorithm in
        Score.get_range_of_prior_move() {this method}.

        """
        widget = self.score
        for name in widget.tag_names(
            self.get_range_for_prior_move_before_insert()[0]
        ):
            if name.startswith(CHOICE):
                return widget.tag_prevrange(
                    self.get_prior_tag_for_choice(name), start
                )
        raise ScoreRAVNoPriorMoveException("Unable to find prior move for RAV")

    def create_previousmovetag(self, positiontag, start):
        """Create previous move tag reference for positiontag."""
        # Add code similar to this which sets up self.previousmovetags a method
        # of same name in positionscore.py to link prev-current-next positions.
        # Use these positions as starting point for colouring tags in score
        # displayed by positionscore.py

        widget = self.score
        vartag = self._game_scaffold.vartag
        tag_range = widget.tag_prevrange(vartag, start)
        if tag_range:
            self.previousmovetags[positiontag] = (
                self.get_position_tag_of_index(tag_range[0]),
                vartag,
                vartag,
            )
        else:
            varstack = list(self.varstack)
            while varstack:
                var = varstack.pop()[0]
                tag_range = widget.tag_prevrange(var, start)
                if tag_range:
                    tag_range = widget.tag_prevrange(var, tag_range[0])

                # Assume it is a '((' sequence.
                # The text for var has not been put in the widget yet since
                # it is after the RAV being processed, not before.
                # get_range_for_prior_move_before_insert returns the inserted
                # move range in this case, and prior is found relative to
                # choice.
                else:
                    tag_range = self.get_range_of_prior_move(start)

                if tag_range:
                    self.previousmovetags[positiontag] = (
                        self.get_position_tag_of_index(tag_range[0]),
                        vartag,
                        var,
                    )
                    break
            else:
                if vartag == self.gamevartag:
                    self.previousmovetags[positiontag] = (None, None, None)
                else:
                    self.previousmovetags[positiontag] = (None, False, None)

    def get_range_for_prior_move_before_insert(self):
        """Return range for move token preceding INSERT to be prior move.

        The prior move is the one played to reach the current position at the
        insertion point.  For RAV start and end markers it is the move before
        the move preceding the start of the RAV.  The nearest move to a move
        is itself.

        """
        # This algorithm is intended for use when building the Text widget
        # content from a PGN score.  INSERT is assumed to be at END and the
        # BUILD_TAG tag to still exist tagging the tokens relevant to the
        # search.
        skip_move_before_rav = True
        widget = self.score
        tpr = widget.tag_prevrange(BUILD_TAG, widget.index(tkinter.INSERT))
        while tpr:
            wtn = widget.tag_names(tpr[0])
            for tag_name in wtn:
                if tag_name.startswith(RAV_MOVES):
                    if skip_move_before_rav:
                        skip_move_before_rav = False
                        start_search = tpr[0]
                        break
                    for position_tag_name in wtn:
                        if position_tag_name.startswith(POSITION):
                            return tpr
                    return None

                # Commented rather than removed because it may be an attempt
                # to deal with ...<move1><move2>((<move3>)<move4>... style
                # RAVs.  However these break in create_previousmovetag at
                # line 958 when processing <move3> before getting here.
                # (See code in commit to which this change was made.)
                # The other RAV styles do not get here, using the 'RAV_MOVES'
                # path instead.  This is only use of RAV_TAG in Score.
                # So RAV_TAG is converted to mark the insertion point for a
                # new RAV after an existing one, like <move4> in:
                # ...<move1><move2>(<move3>)(<move4>)<move5>... from
                # ...<move1><move2>(<move3>)<move5>... for example.
                # RAV_TAG was used in GameEdit to spot the '(' tokens which
                # start a RAV, and was thus only interested in a tag's first
                # range.
                # The RAV_TAGs did not always have the ranges as described in
                # .constants: 'rt1' has ranges for ')' only, and most RAV_TAG
                # tags refer to a '(' range only, for example.  'rt2' has the
                # '(' for 'rt1'.
                # Basically the RAV_TAG structure was rubbish.
                # if tag_name.startswith(RAV_TAG):
                #    start_search = widget.tag_ranges(tag_name)[0]
                #    skip_move_before_rav = True
                #    break

            else:
                start_search = tpr[0]
            tpr = widget.tag_prevrange(BUILD_TAG, start_search)
            if not tpr:
                return None

    def get_position_tag_of_index(self, index):
        """Return Tk tag name if index is in a position tag."""
        for tag_name in self.score.tag_names(index):
            if tag_name.startswith(POSITION):
                return tag_name
        return None

    def get_tags_display_order(self):
        """Return tags in alphabetic order except any chosen to be last.

        last=None means do not display the tags: assume tags will be displayed
        in the order they appear in the PGN text.

        Return None if last is None, and list of '(tag, value)'s otherwise.

        last modifies the order PGN tags are displayed.  Normally the Seven
        Tag Roster appears first in a PGN game score followed by other tags
        in alphabetic order.  Tags not in last are displayed in alphabetic
        order followed by the tags in last.  If last is None the PGN tags are
        displayed in the order they appear in the PGN game score.

        The intention is to display the important tags adjacent to the game
        score.  Thus if last is the Seven Tag Roster these tags are displayed
        after the other tags, rather than appearing before the other tags as
        in a PGN file.
        """
        last = self.tags_displayed_last
        if last is None:
            return None
        tag_values = []
        tags = self.collected_game.pgn_tags
        for pgn_tag in sorted(tags.items()):
            if pgn_tag[0] not in last:
                tag_values.append(pgn_tag)
        for pgn_tag_name in last:
            if pgn_tag_name in tags:
                tag_values.append((pgn_tag_name, tags[pgn_tag_name]))
        return tag_values

    def get_choice_tag_name(self):
        """Return suffixed CHOICE tag name.

        The suffix is arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.choice_number += 1
        suffix = str(self.choice_number)
        return "".join((CHOICE, suffix))

    def get_variation_tag_name(self):
        """Return suffixed RAV_MOVES tag name.

        The suffixes are arbitrary so increment then generate suffix would be
        just as acceptable but generate then increment uses all numbers
        starting at 0.

        """
        self.variation_number += 1
        return "".join((RAV_MOVES, str(self.variation_number)))

    def get_next_positiontag_name(self):
        """Return suffixed POSITION tag name."""
        self.position_number += 1
        return "".join((POSITION, str(self.position_number)))

    @staticmethod
    def get_prior_tag_for_choice(choice):
        """Return Tk tag name for prior move with same suffix as choice."""
        return "".join((PRIOR_MOVE, choice[len(CHOICE) :]))

    def insert_token_into_text(self, token, separator):
        """Insert token and separator in widget.  Return boundary indicies.

        Indicies for start and end of token text are noted primarily to control
        editing and highlight significant text.  The end of separator index is
        used to generate contiguous regions for related tokens and act as a
        placeholder when there is no text between start and end.

        """
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token)
        end = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, separator)
        return start, end, widget.index(tkinter.INSERT)

    def insert_forced_newline_into_text(self):
        """Insert newline and tag it if widget is editable.

        A newline is added after FORCE_NEWLINE_AFTER_FULLMOVES fullmoves
        without a newline, or before various non-move tokens.  It is tagged
        if the widget is editable so deletion of the token can force deletion
        of the newline.

        """
        if self._is_text_editable:
            widget = self.score
            start = widget.index(tkinter.INSERT)
            widget.insert(tkinter.INSERT, NEWLINE_SEP)
            widget.tag_add(
                FORCED_NEWLINE_TAG, start, widget.index(tkinter.INSERT)
            )
        else:
            self.score.insert(tkinter.INSERT, NEWLINE_SEP)

    # Attempt to re-design map_game method to fit new pgn_read package.
    def map_game(self):
        """Tag and mark the displayed text of game score.

        The tags and marks are used for colouring and navigating the score.

        """
        self._game_scaffold = _ScoreScaffold(
            self.get_variation_tag_name(), self.get_choice_tag_name()
        )
        self.gamevartag = self._game_scaffold.vartag
        self.score.mark_set(START_SCORE_MARK, "1.0")
        self.score.mark_gravity(START_SCORE_MARK, tkinter.LEFT)
        game = self.collected_game
        spm = self._game_scaffold.square_piece_map
        try:
            for piece, square in game._initial_position[0]:
                spm[square] = piece
        except TypeError as error:
            raise ScoreMapToBoardException(
                "Unable to map text to board"
            ) from error
        assert len(game._text) == len(game._position_deltas)
        tags_displayed = self.map_tags_display_order()
        for text, position in zip(game._text, game._position_deltas):
            first_char = text[0]
            if first_char in "abcdefghKQRBNkqrnO":
                self.map_move_text(text, position)
            elif first_char == "[":
                if not tags_displayed:
                    self.map_tag(text)
            elif first_char == "{":
                self.map_start_comment(text)
            elif first_char == "(":
                self.map_start_rav(text, position)
            elif first_char == ")":
                self.map_end_rav(text, position)
            elif first_char in "10*":
                self.map_termination(text)
            elif first_char == ";":
                self.map_comment_to_eol(text)
            elif first_char == "$":
                self.map_glyph(text)

            # Currently ignored if present in PGN input.
            elif first_char == "%":
                self.map_escape_to_eol(text)

            # Currently not ignored if present in PGN input.
            elif first_char == "<":
                self.map_start_reserved(text)

            else:
                self.map_non_move(text)

        self.build_nextmovetags()

        # BUILD_TAG used to track moves and RAV markers during construction of
        # text.  Subclasses setup and use NAVIGATE_TOKEN for post-construction
        # comparisons of this, and other, kinds if necessary.  This class, and
        # subclasses, do not need this information after construction.
        # self.nextmovetags tracks the things BUILD_TAG is used for.  Maybe
        # change technique to use it rather than BUILD_TAG.
        self.score.tag_delete(BUILD_TAG)

        # Delete the attributes used to build the self.score Text widget.
        self._game_scaffold = None

    def map_move_text(self, token, position):
        """Add token to game text. Set navigation tags. Return token range.

        self._start_latest_move and self._end_latest_move are set to range
        occupied by token text so that variation tags can be constructed as
        more moves are processed.

        """
        scaffold = self._game_scaffold
        self._modify_square_piece_map(position)
        widget = self.score
        positiontag = self.get_next_positiontag_name()
        next_position = position[1]
        self.tagpositionmap[positiontag] = (
            scaffold.square_piece_map.copy(),
        ) + next_position[1:]
        fwa = next_position[1] == FEN_WHITE_ACTIVE
        if not fwa:
            scaffold.force_newline += 1
        if scaffold.force_newline > FORCE_NEWLINE_AFTER_FULLMOVES:
            self.insert_forced_newline_into_text()
            scaffold.force_newline = 1
        if not fwa:
            start, end, sepend = self.insert_token_into_text(
                str(next_position[5]) + ".", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            if self._is_text_editable or scaffold.force_newline == 1:
                widget.tag_add(FORCED_INDENT_TAG, start, end)
        elif scaffold.next_move_is_choice:
            start, end, sepend = self.insert_token_into_text(
                str(position[0][5]) + "...", SPACE_SEP
            )
            widget.tag_add(MOVETEXT_MOVENUMBER_TAG, start, sepend)
            if self._is_text_editable or scaffold.force_newline == 1:
                widget.tag_add(FORCED_INDENT_TAG, start, end)
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        if self._is_text_editable or scaffold.force_newline == 1:
            widget.tag_add(FORCED_INDENT_TAG, start, end)
        for tag in positiontag, scaffold.vartag, NAVIGATE_MOVE, BUILD_TAG:
            widget.tag_add(tag, start, end)
        if scaffold.vartag == self.gamevartag:
            widget.tag_add(MOVES_PLAYED_IN_GAME_FONT, start, end)
        widget.tag_add("".join((RAV_SEP, scaffold.vartag)), start, sepend)
        if scaffold.next_move_is_choice:
            widget.tag_add(ALL_CHOICES, start, end)

            # A START_RAV is needed to define and set choicetag and set
            # next_move_is_choice True.  There cannot be a START_RAV
            # until a MOVE_TEXT has occured: from PGN grammar.
            # So define and set choicetag then increment choice_number
            # in 'type_ is START_RAV' processing rather than other way
            # round, with initialization, to avoid tag name clutter.
            widget.tag_add(scaffold.choicetag, start, end)
            scaffold.next_move_is_choice = False
            scaffold.unresolved_choice_count -= 1

        scaffold.start_latest_move = start
        scaffold.end_latest_move = end
        self.create_previousmovetag(positiontag, start)
        return start, end, sepend

    def map_start_rav(self, token, position):
        """Add token to game text.  Return range and prior.

        Variation tags are set for guiding move navigation. self._vartag
        self._token_position and self._choicetag are placed on a stack for
        restoration at the end of the variation.
        self._next_move_is_choice is set True indicating that the next move
        is the default selection when choosing a variation.

        The _square_piece_map is reset from position.

        """
        scaffold = self._game_scaffold
        self._set_square_piece_map(position)
        widget = self.score
        if not widget.tag_nextrange(
            ALL_CHOICES, scaffold.start_latest_move, scaffold.end_latest_move
        ):

            # start_latest_move will be the second move, at earliest,
            # in current variation except if it is the first move in
            # the game.  Thus the move before start_latest_move using
            # tag_prevrange() can be tagged as the move creating the
            # position in which the choice of moves occurs.
            scaffold.choicetag = self.get_choice_tag_name()
            widget.tag_add(
                "".join((SELECTION, str(self.choice_number))),
                scaffold.start_latest_move,
                scaffold.end_latest_move,
            )
            prior = self.get_range_for_prior_move_before_insert()
            if prior:
                widget.tag_add(
                    "".join((PRIOR_MOVE, str(self.choice_number))), *prior
                )

        widget.tag_add(
            ALL_CHOICES, scaffold.start_latest_move, scaffold.end_latest_move
        )
        widget.tag_add(
            scaffold.choicetag,
            scaffold.start_latest_move,
            scaffold.end_latest_move,
        )
        self.varstack.append((scaffold.vartag, scaffold.token_position))
        self.choicestack.append(scaffold.choicetag)
        scaffold.vartag = self.get_variation_tag_name()
        nttpr = widget.tag_prevrange(BUILD_TAG, widget.index(tkinter.END))
        if nttpr:
            if widget.get(*nttpr) != "(":
                self.insert_forced_newline_into_text()
                scaffold.force_newline = 0
        else:
            self.insert_forced_newline_into_text()
            scaffold.force_newline = 0
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        widget.tag_add(BUILD_TAG, start, end)
        scaffold.next_move_is_choice = True
        scaffold.unresolved_choice_count += 1
        return start, end, sepend

    def map_end_rav(self, token, position):
        """Add token to game text.  Return token range.

        Variation tags are set for guiding move navigation. scaffold.vartag
        scaffold.token_position and scaffold.choicetag are restored from the
        stack for restoration at the end of the variation.
        (scaffold.start_latest_move, scaffold.end_latest_move) is set to the
        range of the move which the first move of the variation replaced.

        The _square_piece_map is reset from position.

        """
        scaffold = self._game_scaffold
        if scaffold.unresolved_choice_count:
            scaffold.next_move_is_choice = True

        # ValueError exception has happened if and only if opening an invalid
        # game generated from an arbitrary text file completely unlike a PGN
        # file.  Probably no valid PGN tokens at all must be in the file to
        # cause this exception.
        try:
            (
                scaffold.start_latest_move,
                scaffold.end_latest_move,
            ) = self.score.tag_prevrange(ALL_CHOICES, tkinter.END)
        except ValueError:
            return tkinter.END, tkinter.END, tkinter.END

        self._set_square_piece_map(position)
        start, end, sepend = self.insert_token_into_text(token, SPACE_SEP)
        self.score.tag_add(BUILD_TAG, start, end)
        scaffold.vartag, scaffold.token_position = self.varstack.pop()
        scaffold.choicetag = self.choicestack.pop()
        scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return start, end, sepend

    def map_tag(self, token):
        """Add PGN Tag to game text."""
        tag_name, tag_value = token[1:-1].split('"', 1)
        tag_value = tag_value[:-1]
        self.add_pgntag_to_map(tag_name, tag_value)

    def map_tags_display_order(self):
        """Add PGN Tags to game text."""
        tag_values = self.get_tags_display_order()
        self.tagpositionmap[None] = self.fen_tag_tuple_square_piece_map()
        if tag_values is None:
            return False
        for pgn_tag in tag_values:
            self.add_pgntag_to_map(*pgn_tag)
        return True

    def map_termination(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self.score.insert(tkinter.INSERT, NEWLINE_SEP)
        return self.insert_token_into_text(token, NEWLINE_SEP)

    def map_start_comment(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_forced_newline_into_text()
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return self.insert_token_into_text(token, SPACE_SEP)

    # force_newline is not set by gameedit.GameEdit.add_comment_to_eol().
    def _map_comment_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token[:-1])  # token)
        end = widget.index(tkinter.INSERT)  # + ' -1 chars')
        # widget.insert(tkinter.INSERT, NULL_SEP)
        return start, end, widget.index(tkinter.INSERT)

    def map_comment_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_forced_newline_into_text()
        token_indicies = self._map_comment_to_eol(token)
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return token_indicies

    # force_newline is not set by gameedit.GameEdit.add_escape_to_eol().
    def _map_escape_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        widget = self.score
        start = widget.index(tkinter.INSERT)
        widget.insert(tkinter.INSERT, token[:-1])
        end = widget.index(tkinter.INSERT)  # + ' -1 chars')

        # First character of this token is the newline to be tagged.
        # If necessary it is probably safe to use the commented version
        # because a forced newline will appear after the escaped line's EOL.
        # widget.tag_add(
        #     FORCED_NEWLINE_TAG, start, widget.index(tkinter.INSERT)
        # )
        widget.tag_add(FORCED_NEWLINE_TAG, start)

        # widget.insert(tkinter.INSERT, NULL_SEP)
        return start, end, widget.index(tkinter.INSERT)

    def map_escape_to_eol(self, token):
        """Add token to game text. position is ignored. Return token range."""
        token_indicies = self._map_comment_to_eol(token)
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return token_indicies

    def map_integer(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        del position
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_glyph(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_period(self, token, position):
        """Add token to game text. position is ignored. Return token range."""
        del position
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_start_reserved(self, token):
        """Add token to game text. position is ignored. Return token range."""
        self.insert_forced_newline_into_text()
        self._game_scaffold.force_newline = FORCE_NEWLINE_AFTER_FULLMOVES + 1
        return self.insert_token_into_text(token, SPACE_SEP)

    def map_non_move(self, token):
        """Add token to game text. position is ignored. Return token range."""
        return self.insert_token_into_text(token, SPACE_SEP)

    def _set_square_piece_map(self, position):
        assert len(position) == 1
        spm = self._game_scaffold.square_piece_map
        spm.clear()
        for piece, square in position[0][0]:
            spm[square] = piece

    def _modify_square_piece_map(self, position):
        assert len(position) == 2
        spm = self._game_scaffold.square_piece_map
        for square, piece in position[0][0]:
            del spm[square]
        for square, piece in position[1][0]:
            spm[square] = piece
