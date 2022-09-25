# _score_scaffold.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Class with attributes to construct text and tag content of ScoreWidget.

Instances of this class should be discarded after construction is completed.
"""


class _ScoreScaffold:
    """Attributes used by map_game to build a ScoreWidget instance."""

    def __init__(self, vartag, choicetag):
        """Initialize the scaffold."""
        self._start_latest_move = ""
        self._end_latest_move = ""
        self._next_move_is_choice = False
        self._unresolved_choice_count = 0
        self._token_position = None
        self._square_piece_map = {}

        # Used to force a newline before a white move in large games after a
        # non-move token or after FORCE_NEWLINE_AFTER_FULLMOVES black moves
        # have been added to a line.
        # map_game uses self._force_newline as a fullmove number clock which
        # is reset after comments, the start or end of recursive annotation
        # variations, escaped lines '\n%...\n', and reserved '<...>'
        # sequences.  In each case a newline is added before the next token.
        # The AnalysisScore subclass of Score makes its own arrangements
        # because the Score technique does not work, forced newlines are not
        # needed, and only the first move gets numbered.
        self._force_newline = 0

        self._vartag = vartag
        self._choicetag = choicetag

        # PositionScore class uses _force_movenumber to insert movenumber
        # before black moves after start and end of recursive annotation
        # variation markers.  The show and hide move number menu options are
        # ignored.
        # The ScoreWidget based classes ignore _force_movenumber.
        self._force_movenumber = True

    @property
    def start_latest_move(self):
        """Return tkinter.Text widget index of start latest move token."""
        return self._start_latest_move

    @start_latest_move.setter
    def start_latest_move(self, value):
        """Set tkinter.Text widget index of start latest move token."""
        self._start_latest_move = value

    @property
    def end_latest_move(self):
        """Return tkinter.Text widget index of end latest move token."""
        return self._end_latest_move

    @end_latest_move.setter
    def end_latest_move(self, value):
        """Set tkinter.Text widget index of end latest move token."""
        self._end_latest_move = value

    @property
    def next_move_is_choice(self):
        """Return True if next move is chosen from more than one line."""
        return self._next_move_is_choice

    @next_move_is_choice.setter
    def next_move_is_choice(self, value):
        """Set _next_move_is_choice to True or False."""
        assert isinstance(value, bool)
        self._next_move_is_choice = value

    @property
    def unresolved_choice_count(self):
        """Return count of choices for next move."""
        return self._unresolved_choice_count

    @unresolved_choice_count.setter
    def unresolved_choice_count(self, value):
        """Set _unresolved_choice_count to 0 or a positive integer."""
        assert isinstance(value, int) and not value < 0
        self._unresolved_choice_count = value

    @property
    def token_position(self):
        """Return position description associated with current move."""
        return self._token_position

    @token_position.setter
    def token_position(self, value):
        """Set _token_position to value."""
        self._token_position = value

    @property
    def square_piece_map(self):
        """Return dict mapping squares to pieces."""
        return self._square_piece_map

    @property
    def force_newline(self):
        """Return suggested count of newlines to be inserted.

        A return greater than 0 is often interpreted as insert one newline.

        """
        return self._force_newline

    @force_newline.setter
    def force_newline(self, value):
        """Set _force_newline to 0 or a positive integer."""
        assert isinstance(value, int) and not value < 0
        self._force_newline = value

    @property
    def vartag(self):
        """Return tkinter.Text tag of current variation."""
        return self._vartag

    @vartag.setter
    def vartag(self, value):
        """Set _vartag to value which should be a tkinter.Text tag name."""
        assert isinstance(value, str)
        self._vartag = value

    @property
    def choicetag(self):
        """Return tkinter.Text tag of current set of move choices."""
        return self._choicetag

    @choicetag.setter
    def choicetag(self, value):
        """Set _choicetag to value which should be a tkinter.Text tag name."""
        assert isinstance(value, str)
        self._choicetag = value

    @property
    def force_movenumber(self):
        """Return True if next move is chosen from more than one line."""
        return self._force_movenumber

    @force_movenumber.setter
    def force_movenumber(self, value):
        """Set _next_move_is_choice to True or False."""
        assert isinstance(value, bool)
        self._force_movenumber = value
