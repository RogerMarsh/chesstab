# scorepgn.py
# Copyright 2021 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide classes which define methods shared by classes in the displaypgn
and toplevelpgn modules which display Portable Game Notation (PGN) text.

The displaypgn module has classes used as superclasses in the gamedisplay and
repertoiredisplay modules.

The toplevelpgn module has classes used as superclasses in the gamedbdelete,
gamedbdisplay, gamedbedit, gamedbshow, repertoiredbdelete, repertoiredbdisplay,
repertoiredbedit, and repertoiredbshow, classes.

All methods in the classes in this module existed as multiple copies in various
classes in the modules named above.  They are now deleted from those modules.

The classes in this module represnt the different sets of classes with methods
in common.

The ScorePGN class has methods identical in _GameDisplay, _RepertoireDisplay,
GameDialogue, and RepertoireDialogue, now removed from those classes.

"""


class ScorePGN:

    """Mixin providing methods shared by the displaypgn.ShowPGN and
    toplevelpgn.ToplevelPGN classes.

    These methods display the game or repertoire PGN score, or the engine
    analysis for the PGN score.

    """

    # The methods identical except for docstrings.  Here 'PGN score' replaces
    # 'game' and 'repertoire'.  The method names already had 'item' rather
    # than 'game' or 'repertoire'.  Perhaps 'pgn_score' is better, except
    # sometimes the method name should be compatible with the 'CQL' and
    # 'Select' classes.

    def analysis_current_item(self, event=None):
        """Select current PGN score analysis."""
        if self.game_position_analysis:
            self.analysis.apply_colouring_to_variation_back_to_main_line()
        else:
            self.analysis.clear_current_range()
            self.analysis.clear_moves_played_in_variation_colouring_tag()
            self.analysis.current = None
        self.analysis.set_current()
        self.analysis.set_game_board()
        self.set_board_pointer_move_bindings(False)
        self.analysis.set_board_pointer_move_bindings(True)
        self.set_score_pointer_item_navigation_bindings(False)
        self.analysis.set_score_pointer_item_navigation_bindings(True)
        self.set_score_pointer_to_score_bindings(True)
        self.set_analysis_score_pointer_to_analysis_score_bindings(False)
        self.set_toggle_game_analysis_bindings(True)
        self.analysis.score.focus_set()
        self.game_position_analysis = True
        self.takefocus_widget = self.analysis.score

    def current_pgn_score(self, cuiai):
        """Select current PGN score on display.

        Argument name follows history of separate functionally identical
        methods, all called current_item, originally present in gamedisplay
        and repertoiredisplay modules.

        """

        # cuiai should be referencing self given use of current_item() method,
        # but style of sibling *_item() methods is followed.
        # cuiai was cuigs in gamedisplay, and cuirs in repertoiredisplay,
        # modules originally.
        self.analysis.clear_current_range()
        self.analysis.clear_moves_played_in_variation_colouring_tag()
        if self.current is None:
            cuiai.board.set_board(cuiai.fen_tag_square_piece_map())
        else:
            cuiai.board.set_board(cuiai.tagpositionmap[self.current][0])
        cuiai.set_game_list()
        cuiai.analysis.set_board_pointer_move_bindings(False)
        cuiai.set_board_pointer_move_bindings(True)
        cuiai.analysis.set_score_pointer_item_navigation_bindings(False)
        cuiai.set_score_pointer_item_navigation_bindings(True)
        cuiai.set_score_pointer_to_score_bindings(False)
        cuiai.set_analysis_score_pointer_to_analysis_score_bindings(True)
        cuiai.set_toggle_game_analysis_bindings(True)
        self.takefocus_widget = self.score
        cuiai.takefocus_widget.focus_set()
